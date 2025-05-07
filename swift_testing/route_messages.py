#!/usr/bin/env python3
"""
SWIFT Message Router

This script loads a trained model and routes SWIFT messages.
It can process a single message or a batch of messages from the database.
"""

import argparse
import logging
import os
import json
import sys
from pathlib import Path

# Add the project root to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from swift_testing.src.testing_framework import TestingFramework
    from swift_testing.src.config_loader import load_config
except ImportError:
    # Try relative import if package is not installed
    from src.testing_framework import TestingFramework
    from src.config_loader import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def route_message(config_path, message_text=None, message_id=None, model_path=None):
    """
    Route a SWIFT message using the trained model.
    
    Args:
        config_path: Path to the configuration file
        message_text: The text of the message to route (optional)
        message_id: ID of a message in the database to route (optional)
        model_path: Path to a saved model file (optional)
        
    Returns:
        Dictionary with routing result
    """
    try:
        config = load_config(config_path)
        
        framework = TestingFramework(config)
        
        if model_path and os.path.exists(model_path):
            logger.info(f"Loading model from {model_path}")
            framework.load_model(model_path)
    
        if message_text:
            result = framework.router.predict(message_text)
            return {
                "predicted_label": result[0],
                "confidence": result[1],
                "message": message_text[:100] + "..." if len(message_text) > 100 else message_text
            }
        elif message_id:
            message = framework.db_manager.get_message(message_id)
            if not message:
                return {"error": f"Message with ID {message_id} not found"}
            
            message_content = None
            if "content" in message:
                message_content = message["content"]
            elif "generated_text" in message:
                message_content = message["generated_text"]
            
            if not message_content:
                return {"error": f"Message with ID {message_id} has no content"}
                
            result = framework.router.predict(message_content)
            return {
                "message_id": message_id,
                "message_type": message.get("message_type"),
                "predicted_label": result[0],
                "confidence": result[1],
                "expected_label": message.get("expected_routing_label")
            }
        else:
            return {"error": "Either message_text or message_id must be provided"}
            
    except Exception as e:
        logger.error(f"Error routing message: {e}")
        return {"error": f"Failed to route message: {str(e)}"}

def route_batch(config_path, limit=10, model_path=None):
    """
    Route a batch of messages from the database.
    
    Args:
        config_path: Path to the configuration file
        limit: Maximum number of messages to route
        model_path: Path to a saved model file (optional)
        
    Returns:
        List of routing results
    """
    try:
        config = load_config(config_path)
        
        framework = TestingFramework(config)
        
        if model_path and os.path.exists(model_path):
            logger.info(f"Loading model from {model_path}")
            framework.load_model(model_path)
        
        messages = framework.db_manager.get_messages(limit=limit)
        
        results = []
        for message in messages:
            message_content = None
            if "content" in message:
                message_content = message["content"]
            elif "generated_text" in message:
                message_content = message["generated_text"]
            
            if not message_content:
                logger.warning(f"Message with ID {message.get('message_id')} has no content field. Skipping.")
                continue
                
            result = framework.router.predict(message_content)
            results.append({
                "message_id": message.get("message_id"),
                "message_type": message.get("message_type"),
                "predicted_label": result[0],
                "confidence": result[1],
                "expected_label": message.get("expected_routing_label")
            })
        
        return results
            
    except Exception as e:
        logger.error(f"Error routing batch: {e}")
        return {"error": f"Failed to route batch: {str(e)}"}

def main():
    """Main function to route SWIFT messages."""
    parser = argparse.ArgumentParser(description='Route SWIFT messages using a trained model')
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--model', help='Path to saved model file')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--message', help='Text of message to route')
    group.add_argument('--message-id', type=int, help='ID of message in database to route')
    group.add_argument('--batch', action='store_true', help='Route a batch of messages from database')
    
    parser.add_argument('--batch-size', type=int, default=10, help='Number of messages to route in batch mode')
    
    parser.add_argument('--output', help='Path to save routing results (JSON)')
    args = parser.parse_args()
    
    if args.message:
        result = route_message(args.config, message_text=args.message, model_path=args.model)
        print(json.dumps(result, indent=2))
    elif args.message_id:
        result = route_message(args.config, message_id=args.message_id, model_path=args.model)
        print(json.dumps(result, indent=2))
    elif args.batch:
        results = route_batch(args.config, limit=args.batch_size, model_path=args.model)
        
        if isinstance(results, list):
            print(f"Routed {len(results)} messages")
            correct = sum(1 for r in results if r.get("predicted_label") == r.get("expected_label") 
                           and r.get("expected_label") is not None)
            total = sum(1 for r in results if r.get("expected_label") is not None)
            if total > 0:
                print(f"Accuracy: {correct/total:.2%} ({correct}/{total})")
    
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 