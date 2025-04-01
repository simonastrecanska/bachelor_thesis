#!/usr/bin/env python3
"""
Database Setup Script

This script sets up the database schema for the SWIFT message testing framework.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config_loader import load_config
from src.database.db_manager import create_database_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_database(config_path):
    """
    Set up the database schema.
    
    Args:
        config_path: Path to configuration file
    """
    try:
        logger.info(f"Loading configuration from {config_path}")
        config = load_config(config_path)
        
        db_uri = config.get_database_uri()
        logger.info(f"Connecting to database at {db_uri}")
        db_manager = create_database_manager(db_uri)
        
        logger.info("Creating database tables")
        db_manager.create_tables()
        
        logger.info("Database schema setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Set up the database schema")
    parser.add_argument(
        "--config", 
        required=True,
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--drop-existing", 
        action="store_true",
        help="Drop existing tables before creating new ones"
    )
    args = parser.parse_args()
    
    if args.drop_existing:
        try:
            config = load_config(args.config)
            
            db_uri = config.get_database_uri()
            db_manager = create_database_manager(db_uri)
            
            logger.warning("Dropping existing database tables")
            db_manager.drop_tables()
            
        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
            sys.exit(1)
    
    setup_database(args.config)


if __name__ == "__main__":
    main() 