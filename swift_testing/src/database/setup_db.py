#!/usr/bin/env python3
"""
Database Setup Script

This script sets up the PostgreSQL database tables needed for the SWIFT testing framework.
It uses the DatabaseManager's create_tables method to create all tables defined in models.py.
"""

import argparse
import sys
import os
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import load_config
from src.database.db_manager import create_database_manager

def setup_database(config_path, drop_existing=False):
    """
    Set up database tables based on the configuration.
    
    Args:
        config_path: Path to the configuration YAML file
        drop_existing: Whether to drop existing tables before creating new ones
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        logger.info(f"Loading configuration from {config_path}")
        config = load_config(config_path)
        
        db_config = config.database
        
        if hasattr(db_config, 'connection_string'):
            db_uri = db_config.connection_string
        else:
            db_uri = f"postgresql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.dbname}"
            if hasattr(db_config, 'sslmode'):
                db_uri += f"?sslmode={db_config.sslmode}"
        
        logger.info(f"Using database URI: {db_uri}")
        
        logger.info("Creating database manager")
        db_manager = create_database_manager(db_uri)
        
        if drop_existing:
            logger.info("Dropping existing tables")
            db_manager.drop_tables()
            logger.info("Tables dropped successfully")
        
        logger.info("Creating database tables")
        db_manager.create_tables()
        
        if db_manager.ensure_tables_exist():
            logger.info("All required tables have been created successfully")
            return True
        else:
            logger.error("Failed to verify table creation")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

def main():
    """Main function for CLI entry point"""
    parser = argparse.ArgumentParser(description="Setup the database for SWIFT testing framework")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing tables before creating new ones")
    
    args = parser.parse_args()
    
    if setup_database(args.config, args.drop_existing):
        logger.info("Database setup completed successfully. The database is ready to use.")
    else:
        logger.error("Database setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 