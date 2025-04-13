#!/usr/bin/env python3
"""
Populate Templates Script

This script populates the database with default SWIFT message templates.
It directly uses SQLAlchemy to interact with the database.
"""

import os
import sys
import yaml
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = {
    'MT103': {
        'content': """{1:F01BANKBEBBAXXX0000000000}{2:I103BANKDEFFXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:230101EUR10000,00
:50K:ORDERING CUSTOMER
123 MAIN STREET
NEW YORK
:52A:BANKBEBB
:57A:BANKDEFF
:59:BENEFICIARY CUSTOMER
456 OAK AVENUE
FRANKFURT
:70:PAYMENT FOR INVOICE 12345
:71A:SHA
-}""",
        'description': "Single Customer Credit Transfer",
        'expected_routing_label': "PAYMENTS"
    },

    'MT202': {
        'content': """{1:F01BANKBEBBAXXX0000000000}{2:I202BANKDEFFXXXXN}{4:
:20:REFERENCE456
:21:RELATED123
:32A:230101EUR20000,00
:52A:BANKBEBB
:57A:BANKDEFF
:58A:BENEFICIARY BANK
:72:/ACC/123456789
-}""",
        'description': "General Financial Institution Transfer",
        'expected_routing_label': "TREASURY"
    },

    'MT950': {
        'content': """{1:F01BANKBEBBAXXX0000000000}{2:I950BANKDEFFXXXXN}{4:
:20:STATEMENT123
:25:12345678901
:28C:123/1
:60F:C230101EUR50000,00
:61:2301010101C10000,00NCHK123456
:86:PAYMENT RECEIVED
:61:2301010102D5000,00NCHK654321
:86:PAYMENT SENT
:62F:C230101EUR55000,00
-}""",
        'description': "Statement Message",
        'expected_routing_label': "REPORTING"
    },  
}

def ensure_table_exists(engine):
    """Ensure the templates table exists."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'templates'
                )
            """)).fetchone()
            
            if not result or not result[0]:
                conn.execute(text("""
                    CREATE TABLE templates (
                        id SERIAL PRIMARY KEY,
                        template_type VARCHAR(100) UNIQUE NOT NULL,
                        template_content TEXT NOT NULL,
                        description TEXT,
                        expected_routing_label VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                logger.info("Created templates table")
                conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error ensuring table exists: {e}")
        return False

def save_template(engine, template_type, template_content, description=None, expected_routing_label=None):
    """
    Save or update a template in the database.
    
    Args:
        engine: SQLAlchemy engine
        template_type: Type of the template (e.g., 'MT103')
        template_content: The template content
        description: Optional description of the template
        expected_routing_label: Optional routing label for this template
    
    Returns:
        ID of the saved template or None if failed
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id FROM templates WHERE template_type = :template_type"),
                {"template_type": template_type}
            ).fetchone()
            
            if result:
                conn.execute(
                    text("""
                        UPDATE templates 
                        SET template_content = :template_content, 
                            description = :description,
                            expected_routing_label = :expected_routing_label,
                            updated_at = :updated_at
                        WHERE template_type = :template_type
                    """),
                    {
                        "template_type": template_type,
                        "template_content": template_content,
                        "description": description or f"Template for {template_type}",
                        "expected_routing_label": expected_routing_label,
                        "updated_at": datetime.now()
                    }
                )
                logger.info(f"Updated template {template_type}")
                conn.commit()
                return result[0]
            else:
                result = conn.execute(
                    text("""
                        INSERT INTO templates (
                            template_type, 
                            template_content, 
                            description, 
                            expected_routing_label,
                            created_at, 
                            updated_at
                        )
                        VALUES (
                            :template_type, 
                            :template_content, 
                            :description, 
                            :expected_routing_label,
                            :created_at, 
                            :updated_at
                        )
                        RETURNING id
                    """),
                    {
                        "template_type": template_type,
                        "template_content": template_content,
                        "description": description or f"Template for {template_type}",
                        "expected_routing_label": expected_routing_label,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                ).fetchone()
                logger.info(f"Inserted template {template_type}")
                conn.commit()
                return result[0]
    except Exception as e:
        logger.error(f"Error saving template {template_type}: {e}")
        return None

def get_all_templates(engine):
    """Get all templates from the database."""
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT template_type, template_content, expected_routing_label FROM templates")
            ).fetchall()
            
            templates = {}
            for row in results:
                templates[row[0]] = {
                    'content': row[1],
                    'expected_routing_label': row[2]
                }
            
            return templates
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return {}

def populate_templates(config_path: str, template_dir: str = None, default_routing: str = None, routing_map: Dict[str, str] = None) -> None:
    """
    Populate the database with default SWIFT message templates.
    
    Args:
        config_path: Path to the configuration file
        template_dir: Optional directory to load additional templates from
        default_routing: Default routing label to apply to all templates
        routing_map: Dictionary mapping template types to routing labels
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if 'database' not in config or 'connection_string' not in config['database']:
            logger.error("Database connection string not found in config")
            return
            
        db_uri = config['database']['connection_string']
        
        engine = create_engine(db_uri)
        logger.info("Database connection established")
        
        if not ensure_table_exists(engine):
            logger.error("Failed to ensure tables exist")
            return
    
        templates_from_dir = {}
        if template_dir:
            template_path = Path(template_dir)
            if template_path.exists() and template_path.is_dir():
                logger.info(f"Loading templates from directory: {template_dir}")
                for file_path in template_path.glob('*.swt'):
                    template_type = file_path.stem.upper()
                    try:
                        with open(file_path, 'r') as f:
                            template_content = f.read().strip()
                            
                        meta_path = file_path.with_suffix('.meta')
                        description = f"Template for {template_type}"
                        expected_routing_label = default_routing
                        
                        if routing_map and template_type in routing_map:
                            expected_routing_label = routing_map[template_type]
                            
                        if meta_path.exists():
                            try:
                                with open(meta_path, 'r') as f:
                                    meta_data = yaml.safe_load(f)
                                    if meta_data and isinstance(meta_data, dict):
                                        if 'description' in meta_data:
                                            description = meta_data['description']
                                        if 'routing' in meta_data:
                                            expected_routing_label = meta_data['routing']
                            except Exception as e:
                                logger.warning(f"Error reading metadata for {template_type}: {e}")
                                
                        templates_from_dir[template_type] = {
                            'content': template_content,
                            'description': description,
                            'expected_routing_label': expected_routing_label
                        }
                        logger.info(f"Loaded template {template_type} from {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error loading template {file_path}: {e}")
        
        all_templates = {**DEFAULT_TEMPLATES, **templates_from_dir}
        
        for template_type, template_data in all_templates.items():
            content = template_data['content'] if isinstance(template_data, dict) else template_data
            description = template_data.get('description') if isinstance(template_data, dict) else None
            
            expected_routing_label = None
            if isinstance(template_data, dict) and 'expected_routing_label' in template_data:
                expected_routing_label = template_data['expected_routing_label']
            elif routing_map and template_type in routing_map:
                expected_routing_label = routing_map[template_type]
            elif default_routing:
                expected_routing_label = default_routing
                
            template_id = save_template(
                engine, 
                template_type, 
                content, 
                description, 
                expected_routing_label
            )
            
            if template_id:
                logger.info(f"Saved template {template_type} with ID {template_id}")
            else:
                logger.error(f"Failed to save template {template_type}")
                
        all_db_templates = get_all_templates(engine)
        logger.info(f"Total templates in database: {len(all_db_templates)}")
        
    except Exception as e:
        logger.error(f"Error populating templates: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Populate database with SWIFT message templates")
    parser.add_argument("--config", "-c", default="config/config.yaml",
                        help="Path to configuration file")
    parser.add_argument("--templates", "-t", default=None,
                        help="Path to directory with additional templates")
    parser.add_argument("--default-routing", "-r", default=None,
                        help="Default routing label to apply to all templates (e.g., 'PAYMENT_PROCESSOR')")
    parser.add_argument("--routing-map", "-m", default=None,
                        help="Path to JSON file mapping template types to routing labels")
    args = parser.parse_args()
    
    routing_map = {}
    if args.routing_map and os.path.exists(args.routing_map):
        try:
            with open(args.routing_map, 'r') as f:
                routing_map = json.load(f)
            logger.info(f"Loaded routing map from {args.routing_map}")
        except Exception as e:
            logger.error(f"Error loading routing map: {e}")
    
    populate_templates(args.config, args.templates, args.default_routing, routing_map)

if __name__ == "__main__":
    main() 