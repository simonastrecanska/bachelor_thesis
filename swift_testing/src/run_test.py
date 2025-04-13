#!/usr/bin/env python3
"""
SWIFT Testing Framework Test Runner

This script runs the SWIFT Message Routing testing framework with the specified parameters.
It handles the initialization of the framework and executes a complete test run.
"""

import argparse
import sys
import os
import json
from pathlib import Path
import logging
from datetime import datetime
import time
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.testing_framework import create_testing_framework

def run_test(config_path, test_name, description, num_messages=None, train_model=False, output_file=None, use_existing=False):
    """
    Run a complete test using the SWIFT testing framework.
    
    Args:
        config_path: Path to the configuration YAML file
        test_name: Name of the test
        description: Description of the test
        num_messages: Number of test messages to generate (default from config if None)
                      If set to 0, uses existing messages without generating new ones
        train_model: Whether to train the model before testing
        output_file: Optional file path to save the results as JSON
        use_existing: Whether to use existing messages instead of generating new ones
        
    Returns:
        Test results as a dictionary
    """
    try:
        logger.info(f"Creating testing framework using config: {config_path}")
        framework = create_testing_framework(config_path)
        
        logger.info(f"Running test: {test_name}")
        
        if num_messages == 0:
            logger.info("Using existing messages (no new message generation)")
            
            param_id = framework.db_manager.create_parameter(
                test_name=test_name,
                description=description
            )
            logger.info(f"Created test parameters with ID: {param_id}")
            
            messages = []
            
            template_query = text("SELECT id, expected_routing_label, template_content FROM templates")
            templates = {}
            training_texts = []
            training_labels = []
            
            with framework.db_manager.engine.connect() as conn:
                try:
                    for row in conn.execute(template_query):
                        template_id = row[0]
                        routing_label = row[1]
                        template_content = row[2]
                        
                        templates[template_id] = routing_label
                        
                        if template_content and routing_label:
                            training_texts.append(template_content)
                            training_labels.append(routing_label)
                            
                    logger.info(f"Found {len(templates)} templates: {templates}")
                    
                    message_query = text("SELECT message_id, generated_text, template_id FROM messages LIMIT 50")
                    result = conn.execute(message_query)
                    
                    for row in result:
                        message_id = row[0]
                        generated_text = row[1]
                        template_id = row[2]
                        
                        expected_routing_label = templates.get(template_id)
                        
                        messages.append({
                            'message_id': message_id,
                            'generated_text': generated_text,
                            'expected_label': expected_routing_label
                        })
                        
                except Exception as e:
                    logger.error(f"Error fetching messages: {e}")
                    conn.rollback()
                    
                    try:
                        all_messages = framework.db_manager.get_all_messages()
                        logger.info(f"Retrieved {len(all_messages)} messages using built-in method")
                        
                        for msg in all_messages:
                            template_id = msg.get('template_id')
                            messages.append({
                                'message_id': msg.get('id') or msg.get('message_id'),
                                'generated_text': msg.get('generated_text') or msg.get('text'),
                                'expected_label': templates.get(template_id) if template_id else None
                            })
                    except Exception as e2:
                        logger.error(f"Error using framework methods: {e2}")
                        logger.warning("No existing messages found. Will generate new messages.")
                        num_messages = framework.config.message_generation.num_messages
                        test_name = f"{test_name} (fallback)"
                        description = f"{description} (fallback after error)"
            
            if not messages and num_messages == 0:
                logger.warning("No existing messages found. Will generate new messages.")
                num_messages = framework.config.message_generation.num_messages
            
            if not messages:
                results = framework.run_complete_test(
                    test_name=test_name,
                    description=description,
                    num_messages=num_messages or framework.config.message_generation.num_messages,
                    train_model=train_model
                )
            else:
                logger.info(f"Found {len(messages)} existing messages")
                
                logger.info("Training model directly on template content...")
                if training_texts and training_labels:
                    logger.info(f"Training model with {len(training_texts)} templates")
                    for message in messages:
                        if message.get('generated_text') and message.get('expected_label'):
                            training_texts.append(message['generated_text'])
                            training_labels.append(message['expected_label']) 
                            
                    try:
                        framework.router.train(training_texts, training_labels)
                        logger.info("Model trained successfully")
                    except Exception as e:
                        logger.error(f"Error training model: {e}")
                        return {"error": f"Failed to train model: {str(e)}"}
                else:
                    logger.error("No training data available")
                    return {"error": "No training data available for the model"}
                
                for i, message in enumerate(messages):
                    logger.info(f"Processing message {i+1}/{len(messages)}")
                    if not message.get('generated_text'):
                        logger.warning(f"Missing generated_text for message {message.get('message_id')}, skipping")
                        continue
                        
                    predicted_label, confidence = framework.router.predict(message['generated_text'])
                    logger.info(f"Prediction for message {message.get('message_id')}: {predicted_label} (confidence: {confidence})")
                    
                    framework.db_manager.create_actual_result(
                        message['message_id'], 
                        framework.router.version, 
                        predicted_label, 
                        confidence
                    )
                
                valid_messages = [m for m in messages if m.get('expected_label') and m.get('generated_text')]
                true_labels = [m['expected_label'] for m in valid_messages]
                predicted_labels = []
                confidences = []
                
                for message in valid_messages:
                    results_for_message = framework.db_manager.get_test_results(message['message_id'])
                    if results_for_message and len(results_for_message) > 0:
                        latest_result = results_for_message[-1]
                        predicted_labels.append(latest_result['predicted_label'])
                        confidences.append(latest_result['confidence'])
                    else:
                        predicted_labels.append(None)
                        confidences.append(0.0)
                
                output_dir = os.path.join(
                    framework.config.paths.output_dir,
                    f"test_{param_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                os.makedirs(output_dir, exist_ok=True)
                
                start_time = time.time()
                
                valid_indices = [i for i, (true, pred) in enumerate(zip(true_labels, predicted_labels)) 
                                if true is not None and pred is not None]
                
                filtered_true_labels = [true_labels[i] for i in valid_indices]
                filtered_predicted_labels = [predicted_labels[i] for i in valid_indices]
                filtered_confidences = [confidences[i] for i in valid_indices]
                
                logger.info(f"Evaluating {len(filtered_true_labels)} valid message results after filtering out None values")
                
                evaluation_metrics = framework.evaluator.evaluate(
                    filtered_true_labels, filtered_predicted_labels, filtered_confidences, output_dir
                )
                
                results = {
                    "parameter": {
                        "param_id": param_id,
                        "test_name": test_name,
                        "description": description
                    },
                    "num_messages": len(valid_messages),
                    "evaluation": evaluation_metrics,
                    "output_dir": output_dir,
                    "execution_time": time.time() - start_time
                }
        else:
            results = framework.run_complete_test(
                test_name=test_name,
                description=description,
                num_messages=num_messages,
                train_model=train_model
            )
            
        if "error" in results:
            logger.error(f"Test failed with error: {results['error']}")
            return results
            
        logger.info("\n=== TEST RESULTS ===")
        logger.info(f"Test ID: {results['parameter']['param_id']}")
        logger.info(f"Test Name: {results['parameter']['test_name']}")
        if "execution_time" in results:
            logger.info(f"Execution Time: {results['execution_time']:.2f} seconds")
        logger.info(f"Messages Tested: {results['num_messages']}")
        
        if "evaluation" in results and "metrics" in results["evaluation"]:
            metrics = results["evaluation"]["metrics"]
            logger.info("\n=== METRICS ===")
            logger.info(f"Accuracy: {metrics.get('accuracy', 'N/A')}")
            logger.info(f"Precision: {metrics.get('precision', 'N/A')}")
            logger.info(f"Recall: {metrics.get('recall', 'N/A')}")
            logger.info(f"F1 Score: {metrics.get('f1', 'N/A')}")
            
            if "correct_count" in metrics and "total_count" in metrics:
                logger.info(f"Correct: {metrics['correct_count']}/{metrics['total_count']}")
        
        if "output_dir" in results:
            logger.info(f"\nOutputs saved to: {results['output_dir']}")
        
        if output_file:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error running test: {str(e)}")
        logger.exception("Exception details:")
        return {"error": str(e)}

def main():
    """Main function for CLI entry point"""
    parser = argparse.ArgumentParser(description="Run SWIFT message routing tests")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")
    parser.add_argument("--name", required=True, help="Name of the test")
    parser.add_argument("--description", "--desc", default="SWIFT message routing test", help="Description of the test")
    parser.add_argument("--messages", type=int, help="Number of test messages to generate (default from config if not specified, 0 to use existing messages)")
    parser.add_argument("--train", action="store_true", help="Train the model before testing")
    parser.add_argument("--output", help="Path to save the results as JSON")
    parser.add_argument("--use-existing", action="store_true", help="Use existing messages instead of generating new ones (currently not supported)")
    
    args = parser.parse_args()
    
    run_test(
        config_path=args.config,
        test_name=args.name,
        description=args.description,
        num_messages=args.messages,
        train_model=args.train,
        output_file=args.output,
        use_existing=args.use_existing
    )

if __name__ == "__main__":
    main() 