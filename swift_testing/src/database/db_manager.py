"""
Database Manager Module

This module handles database connections and operations using SQLAlchemy.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Parameters, Template, Messages, ExpectedResults, ActualResults, VariatorData, MessageTemplate

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for PostgreSQL integration."""
    
    def __init__(self, db_uri: str):
        """
        Initialize database manager.
        
        Args:
            db_uri: Database connection URI
        """
        self.db_uri = db_uri
        self.engine = None
        self.Session = None
        self.connect()
        
    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.engine = create_engine(self.db_uri)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables defined in the models."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.Session()
    
    def create_parameter(self, test_name: str, description: str) -> int:
        """
        Create a new test parameter entry.
        
        Args:
            test_name: Name of the test
            description: Description of the test
            
        Returns:
            ID of the created parameter
        """
        session = self.get_session()
        try:
            parameter = Parameters(test_name=test_name, description=description)
            session.add(parameter)
            session.commit()
            param_id = parameter.param_id
            logger.info(f"Created parameter with ID {param_id}")
            return param_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create parameter: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_parameter(self, param_id: int) -> Optional[Dict[str, Any]]:
        """
        Get parameter by ID.
        
        Args:
            param_id: Parameter ID
            
        Returns:
            Parameter as dictionary or None if not found
        """
        session = self.get_session()
        try:
            parameter = session.query(Parameters).filter(Parameters.param_id == param_id).first()
            if parameter:
                return {
                    'param_id': parameter.param_id,
                    'test_name': parameter.test_name,
                    'description': parameter.description
                }
            return None
        finally:
            session.close()
    
    def get_parameters(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all parameters, limited by the specified amount.
        
        Args:
            limit: Maximum number of parameters to return
            
        Returns:
            List of parameters as dictionaries
        """
        session = self.get_session()
        try:
            parameters = session.query(Parameters).limit(limit).all()
            return [
                {
                    'id': param.param_id,
                    'name': param.test_name,
                    'description': param.description
                }
                for param in parameters
            ]
        finally:
            session.close()
    
    def create_template(self, template_name: str, template_text: str) -> int:
        """
        Create a new message template (legacy table).
        
        Args:
            template_name: Name of the template
            template_text: Template text content
            
        Returns:
            ID of the created template
        """
        session = self.get_session()
        try:
            template = Template(template_name=template_name, template_text=template_text)
            session.add(template)
            session.commit()
            template_id = template.template_id
            logger.info(f"Created template with ID {template_id}")
            return template_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create template: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_template(self, template_id_or_type: Any) -> Optional[Dict[str, Any]]:
        """
        Get template by ID or type.
        
        Args:
            template_id_or_type: Template ID (int) or template type (str)
            
        Returns:
            Template as dictionary or None if not found
        """
        session = self.get_session()
        try:
            if isinstance(template_id_or_type, int):
                template = session.query(Template).filter(Template.template_id == template_id_or_type).first()
                if template:
                    return {
                        'template_id': template.template_id,
                        'template_name': template.template_name,
                        'template_text': template.template_text
                    }
            else:
                template = session.query(MessageTemplate).filter(
                    MessageTemplate.template_type == template_id_or_type
                ).first()
                if template:
                    return {
                        'id': template.id,
                        'template_type': template.template_type,
                        'template_content': template.template_content,
                        'description': template.description,
                        'created_at': template.created_at,
                        'updated_at': template.updated_at
                    }
            return None
        finally:
            session.close()
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """
        Get all templates from both tables.
        
        Returns:
            List of templates as dictionaries
        """
        session = self.get_session()
        try:
            legacy_templates = session.query(Template).all()
            legacy_results = [
                {
                    'template_id': template.template_id,
                    'template_name': template.template_name,
                    'template_text': template.template_text
                }
                for template in legacy_templates
            ]
            
            new_templates = session.query(MessageTemplate).all()
            new_results = [
                {
                    'id': template.id,
                    'template_type': template.template_type,
                    'template_content': template.template_content,
                    'description': template.description
                }
                for template in new_templates
            ]
            
            return legacy_results + new_results
        finally:
            session.close()
    
    def save_template(self, template_type: str, template_content: str, description: str = None) -> Optional[int]:
        """
        Save a message template to the database.
        
        Args:
            template_type: Type of the template (e.g., 'MT103')
            template_content: The template content as a string
            description: Optional description of the template
            
        Returns:
            The ID of the saved template or None if failed
        """
        session = self.get_session()
        try:
            existing_template = session.query(MessageTemplate).filter_by(
                template_type=template_type
            ).first()
            
            if existing_template:
                existing_template.template_content = template_content
                if description is not None:
                    existing_template.description = description
                existing_template.updated_at = datetime.now()
                template = existing_template
                logger.info(f"Updated existing template for type: {template_type}")
            else:
                template = MessageTemplate(
                    template_type=template_type,
                    template_content=template_content,
                    description=description
                )
                session.add(template)
                logger.info(f"Added new template for type: {template_type}")
            
            session.commit()
            return template.id
            
        except Exception as e:
            logger.error(f"Error saving template {template_type}: {str(e)}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def delete_template(self, template_type: str) -> bool:
        """
        Delete a template from the database.
        
        Args:
            template_type: The type of template to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        session = self.get_session()
        try:
            template = session.query(MessageTemplate).filter_by(
                template_type=template_type
            ).first()
            
            if template:
                session.delete(template)
                session.commit()
                logger.info(f"Deleted template for type: {template_type}")
                return True
            else:
                logger.warning(f"No template found for type: {template_type}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting template {template_type}: {str(e)}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def create_message(self, template_id: int, param_id: int, generated_text: str) -> int:
        """
        Create a new generated message.
        
        Args:
            template_id: ID of the template used
            param_id: ID of the parameter used
            generated_text: Generated message text
            
        Returns:
            ID of the created message
        """
        session = self.get_session()
        try:
            message = Messages(
                template_id=template_id,
                param_id=param_id,
                generated_text=generated_text
            )
            session.add(message)
            session.commit()
            message_id = message.message_id
            logger.info(f"Created message with ID {message_id}")
            return message_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create message: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Get message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message as dictionary or None if not found
        """
        session = self.get_session()
        try:
            message = session.query(Messages).filter(Messages.message_id == message_id).first()
            if message:
                return {
                    'id': message.message_id,
                    'template_id': message.template_id,
                    'param_id': message.param_id,
                    'message_text': message.generated_text
                }
            return None
        finally:
            session.close()
    
    def get_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get messages, limited by the specified amount.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of messages as dictionaries
        """
        session = self.get_session()
        try:
            messages = session.query(Messages).order_by(Messages.message_id.desc()).limit(limit).all()
            return [
                {
                    'id': message.message_id,
                    'template_id': message.template_id,
                    'param_id': message.param_id,
                    'message_text': message.generated_text
                }
                for message in messages
            ]
        finally:
            session.close()
    
    def get_messages_by_template_id(self, template_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get messages by template ID.
        
        Args:
            template_id: Template ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages as dictionaries
        """
        session = self.get_session()
        try:
            messages = session.query(Messages).filter(
                Messages.template_id == template_id
            ).order_by(Messages.message_id.desc()).limit(limit).all()
            
            return [
                {
                    'id': message.message_id,
                    'template_id': message.template_id,
                    'param_id': message.param_id,
                    'message_text': message.generated_text
                }
                for message in messages
            ]
        finally:
            session.close()
    
    def get_messages_by_param(self, param_id: int) -> List[Dict[str, Any]]:
        """
        Get messages by parameter ID.
        
        Args:
            param_id: Parameter ID
            
        Returns:
            List of messages as dictionaries
        """
        session = self.get_session()
        try:
            messages = session.query(Messages).filter(Messages.param_id == param_id).all()
            return [
                {
                    'id': message.message_id,
                    'template_id': message.template_id,
                    'param_id': message.param_id,
                    'message_text': message.generated_text
                }
                for message in messages
            ]
        finally:
            session.close()
    
    def ensure_tables_exist(self):
        """
        Ensure all necessary tables exist in the database.
        
        Returns:
            bool: True if tables exist or were created successfully, False otherwise
        """
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            if 'message_templates' not in existing_tables or 'parameters' not in existing_tables:
                self.create_tables()
                logger.info("Created database tables")
            return True
        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {str(e)}")
            return False


def create_database_manager(config: Dict) -> DatabaseManager:
    """
    Create a database manager from a configuration dictionary.
    
    Args:
        config: Configuration dictionary with database settings
    
    Returns:
        DatabaseManager instance
    """
    db_config = config.get("database", {})
    
    username = db_config.get("username", "")
    password = db_config.get("password", "")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", "5432")
    dbname = db_config.get("dbname", "swift_db")
    
    db_uri = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"
    
    return DatabaseManager(db_uri) 