#!/usr/bin/env python3
"""
Generate SWIFT Messages

This script:
1. Loads configuration from swift_testing/config/config.yaml
2. Connects to the database
3. Retrieves ALL message templates from the database
4. Generates SWIFT messages using each template
5. Saves the generated messages back to the database
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
    parser.add_argument('--count', type=int, default=10, help='Number of messages to generate per template')
    parser.add_argument('--type', help='Template type to use (e.g., MT103)')
    parser.add_argument('--randomness', type=float, default=0.5, help='Randomness factor for message generation (0.0-1.0)')
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
    
    param_id = db_manager.create_parameter(
        test_name=f"Random message generation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        description=f"Generated with randomness factor {args.randomness}"
    )
    
    variator = create_template_variator(randomness=args.randomness, db_uri=db_uri)
    
    total_messages = 0
    
    for template in templates:
        template_id = template.get('id')
        template_type = template.get('template_type', template.get('template_name', 'Unknown'))
        template_content = template.get('template_content', template.get('template_text', ''))
        
        if not template_id or not template_content:
            logger.warning(f"Skipping template {template_type}: missing ID or content")
            continue
            
        logger.info(f"Processing template {template_type} (ID: {template_id})")
        
        for i in range(args.count):
            try:
                varied_template = variator.add_variations(template_content)
                
                message_id = db_manager.create_message(
                    template_id=template_id,
                    param_id=param_id,
                    generated_text=varied_template
                )
                
                if message_id:
                    total_messages += 1
                    logger.info(f"Generated message #{i+1} for template {template_type}, saved with ID: {message_id}")
                else:
                    logger.error(f"Failed to save message #{i+1} for template {template_type}")
            except Exception as e:
                logger.error(f"Error generating message for {template_type}: {e}")
    
    logger.info(f"Successfully generated and stored {total_messages} messages across all templates.")
    logger.info(f"Test parameter ID: {param_id}")

if __name__ == "__main__":
    main() 