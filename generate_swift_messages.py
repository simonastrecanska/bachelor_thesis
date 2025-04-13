#!/usr/bin/env python3
"""
Generate SWIFT Messages

This script:
1. Loads configuration from swift_testing/config/config.yaml
2. Connects to the database
3. Retrieves message templates from the database
4. Generates SWIFT messages using each template
5. Saves the generated messages back to the database

It supports two generation modes:
- Standard mode: Uses the TemplateVariator
- AI mode: Uses Ollama to generate messages with AI
"""

import argparse
import logging
import os
import yaml
import sys
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swift_testing.src.database.db_manager import create_database_manager
from swift_testing.src.message_generator.template_variator import create_template_variator
from swift_testing.src.message_generator.ai_generator import create_ollama_generator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    logger.info(f"Loading configuration from: {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def get_db_connection_string(config: Dict[str, Any]) -> str:
    """Extract database connection string from config."""
    if 'database' in config and 'connection_string' in config['database']:
        return config['database']['connection_string']
    
    db_config = config.get('database', {})
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 5432)
    username = db_config.get('username', '')
    password = db_config.get('password', '')
    dbname = db_config.get('dbname', '')
    sslmode = db_config.get('sslmode', 'prefer')
    
    return f"postgresql://{username}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate SWIFT messages using templates')
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--count', type=int, default=10, help='Number of messages per template')
    parser.add_argument('--type', help='Template type to use (e.g., MT103)')
    parser.add_argument('--ai', action='store_true', help='Use AI (Ollama) for generation')
    parser.add_argument('--model', default='llama3', help='Ollama model to use (with --ai)')
    parser.add_argument('--temperature', type=float, default=0.7, help='AI temperature (with --ai)')
    args = parser.parse_args()

    config = load_config(args.config)
    
    db_uri = get_db_connection_string(config)
    logger.info(f"Using database: {db_uri}")
    
    db_manager = create_database_manager(db_uri)
    
    logger.info("Retrieving message templates from database")
    templates = db_manager.get_all_templates()
    if not templates:
        logger.error("No templates found in the database")
        return
    
    if args.type:
        logger.info(f"Filtering templates for type: {args.type}")
        filtered_templates = []
        for template in templates:
            template_type = template.get('template_type', template.get('template_name', ''))
            if template_type.upper() == args.type.upper():
                filtered_templates.append(template)
        
        if not filtered_templates:
            logger.error(f"No templates found with type: {args.type}")
            logger.info(f"Available template types: {', '.join(set(t.get('template_type', t.get('template_name', '')) for t in templates))}")
            return
        
        templates = filtered_templates
    
    logger.info(f"Found {len(templates)} templates to process")
    
    generation_method = "AI (Ollama)" if args.ai else "Template Variator"
    param_id = db_manager.create_parameter(
        test_name=f"Message generation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        description=f"Generated with {generation_method}"
    )
    
    if args.ai:
        logger.info(f"Using AI generation with model: {args.model}")
        ai_config = config.get('message_generation', {}).get('ai_generation_config', {})
        model_name = args.model or ai_config.get('model', 'llama3')
        temperature = args.temperature or ai_config.get('temperature', 0.7)
        api_base = ai_config.get('api_base', 'http://localhost:11434/api')
        system_prompt = ai_config.get('system_prompt')
        
        generator = create_ollama_generator(
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_prompt,
            api_base=api_base
        )
        generation_method = "generate_variation"
    else:
        logger.info(f"Using template variator")
        variator = create_template_variator(db_uri=db_uri)
        generation_method = "add_variations"
    
    total_messages = 0
    
    for template in templates:
        template_id = template.get('id', template.get('template_id'))
        template_type = template.get('template_type', template.get('template_name', 'Unknown'))
        template_content = template.get('template_content', template.get('template_text', ''))
        
        if not template_id or not template_content:
            logger.warning(f"Skipping template {template_type}: missing ID or content")
            continue
            
        logger.info(f"Processing template {template_type} (ID: {template_id})")
        
        for i in range(args.count):
            try:
                if args.ai:
                    generated_message = generator.generate_variation(template_content)
                else:
                    generated_message = variator.add_variations(template_content)
                
                expected_routing_label = template.get('expected_routing_label', '')
                message_id = db_manager.create_message(
                    template_id=template_id,
                    param_id=param_id,
                    generated_text=generated_message,
                    expected_routing_label=expected_routing_label
                )
                
                if message_id:
                    total_messages += 1
                    logger.info(f"Generated message {i+1}/{args.count} for template {template_type}")
                else:
                    logger.warning(f"Failed to save message {i+1}/{args.count} for template {template_type}")
            
            except Exception as e:
                logger.error(f"Error generating message {i+1} for template {template_type}: {e}")
    
    logger.info(f"Generation complete. Created {total_messages} messages.")


if __name__ == "__main__":
    main() 