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
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import text

from .models import Base, Parameters, Messages, ExpectedResults, ActualResults, VariatorData, MessageTemplate

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
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables defined in the models."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
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
        with self.get_session() as session:
            try:
                parameter = Parameters(test_name=test_name, description=description)
                session.add(parameter)
                session.commit()
                param_id = parameter.param_id
                logger.info(f"Created parameter with ID {param_id}")
                return param_id
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to create parameter '{test_name}': {str(e)}")
                raise
    
    def get_parameter(self, param_id: int) -> Optional[Dict[str, Any]]:
        """
        Get parameter by ID.
        
        Args:
            param_id: Parameter ID
            
        Returns:
            Parameter as dictionary or None if not found
        """
        with self.get_session() as session:
            try:
                parameter = session.query(Parameters).filter(Parameters.param_id == param_id).first()
                if parameter:
                    return {
                        'param_id': parameter.param_id,
                        'test_name': parameter.test_name,
                        'description': parameter.description
                    }
                logger.debug(f"Parameter with ID {param_id} not found")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving parameter ID {param_id}: {str(e)}")
                return None
    
    def get_parameters(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all parameters, limited by the specified amount.
        
        Args:
            limit: Maximum number of parameters to return
            
        Returns:
            List of parameters as dictionaries
        """
        with self.get_session() as session:
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
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving parameters (limit={limit}): {str(e)}")
                return []
    
    def create_template(
        self, 
        template_type: str, 
        template_content: str, 
        description: str = None,
        expected_routing_label: str = None
    ) -> int:
        """
        Create a new message template in the database.
        
        Args:
            template_type: Identifier for the template
            template_content: The content of the template
            description: Optional description of the template
            expected_routing_label: Optional routing label for messages of this template
            
        Returns:
            The ID of the newly created template
        """
        with self.get_session() as session:
            try:
                template = MessageTemplate(
                    template_type=template_type,
                    template_content=template_content,
                    description=description,
                    expected_routing_label=expected_routing_label
                )
                session.add(template)
                session.commit()
                template_id = template.id
                logger.info(f"Created template {template_type} with ID {template_id}")
                return template_id
            except IntegrityError:
                session.rollback()
                logger.error(f"Template {template_type} already exists (integrity error)")
                raise
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error creating template '{template_type}': {str(e)}")
                raise
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a message template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Dictionary with template details or None if not found
        """
        with self.get_session() as session:
            try:
                template = session.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
                if not template:
                    logger.debug(f"Template with ID {template_id} not found")
                    return None
                return {
                    "id": template.id,
                    "template_id": template.id,
                    "template_type": template.template_type,
                    "template_content": template.template_content,
                    "template_text": template.updated_at,
                    "description": template.description,
                    "expected_routing_label": template.expected_routing_label,
                    "created_at": template.created_at,
                    "updated_at": template.updated_at
                }
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving template ID {template_id}: {str(e)}")
                return None
    
    def get_template_by_type(self, template_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by its type.
        
        Args:
            template_type: Type of the template to retrieve
            
        Returns:
            Template dictionary or None if not found
        """
        with self.get_session() as session:
            try:
                template = session.query(MessageTemplate).filter(
                    MessageTemplate.template_type == template_type
                ).first()
                
                if not template:
                    logger.debug(f"Template with type '{template_type}' not found")
                    return None
                    
                return {
                    "id": template.id,
                    "template_id": template.id,
                    "template_type": template.template_type,
                    "template_content": template.template_content,
                    "template_text": template.updated_at,
                    "description": template.description,
                    "expected_routing_label": template.expected_routing_label,
                    "created_at": template.created_at,
                    "updated_at": template.updated_at
                }
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving template by type '{template_type}': {str(e)}")
                return None
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """
        Get all message templates.
        
        Returns:
            List of template dictionaries
        """
        with self.get_session() as session:
            try:
                templates = session.query(MessageTemplate).all()
                return [
                    {
                        "id": t.id,
                        "template_id": t.id,
                        "template_type": t.template_type,
                        "template_content": t.template_content,
                        "template_text": t.updated_at,
                        "description": t.description,
                        "expected_routing_label": t.expected_routing_label,
                        "created_at": t.created_at,
                        "updated_at": t.updated_at
                    }
                    for t in templates
                ]
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving all templates: {str(e)}")
                return []
    
    def get_template_id(self, template_type: str) -> Optional[int]:
        """
        Get template ID by template type.
        
        Args:
            template_type: Type of the template
            
        Returns:
            Template ID or None if not found
        """
        with self.get_session() as session:
            try:
                template = session.query(MessageTemplate).filter(
                    MessageTemplate.template_type == template_type
                ).first()
                
                if template:
                    return template.id
                logger.debug(f"No template ID found for type '{template_type}'")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving template ID for type '{template_type}': {str(e)}")
                return None
    
    def update_template_by_type(self, template_type: str, template_content: str, description: str = None, expected_routing_label: str = None) -> Optional[int]:
        """
        Update an existing template or create a new one if it doesn't exist.
        
        Args:
            template_type: Type of the template (e.g., 'MT103')
            template_content: The template content as a string
            description: Optional description of the template
            expected_routing_label: Optional routing label for this template
            
        Returns:
            The ID of the saved template or None if failed
        """
        with self.get_session() as session:
            try:
                existing_template = session.query(MessageTemplate).filter_by(
                    template_type=template_type
                ).first()
                
                if existing_template:
                    existing_template.template_content = template_content
                    if description is not None:
                        existing_template.description = description
                    if expected_routing_label is not None:
                        existing_template.expected_routing_label = expected_routing_label
                    existing_template.updated_at = datetime.now()
                    template = existing_template
                    logger.info(f"Updated existing template for type: {template_type}")
                else:
                    template = MessageTemplate(
                        template_type=template_type,
                        template_content=template_content,
                        description=description,
                        expected_routing_label=expected_routing_label
                    )
                    session.add(template)
                    logger.info(f"Added new template for type: {template_type}")
                
                session.commit()
                return template.id
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error updating/creating template '{template_type}': {str(e)}")
                return None
    
    def delete_template(self, template_type: str) -> bool:
        """
        Delete a template from the database.
        
        Args:
            template_type: The type of template to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        with self.get_session() as session:
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
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error deleting template '{template_type}': {str(e)}")
                return False
    
    def update_template(
        self, 
        template_id: int, 
        template_content: str = None, 
        template_type: str = None,
        description: str = None,
        expected_routing_label: str = None
    ) -> bool:
        """
        Update an existing message template by ID.
        
        Args:
            template_id: ID of the template to update
            template_content: New content for the template
            template_type: New type identifier for the template
            description: New description for the template
            expected_routing_label: New routing label for the template
            
        Returns:
            True if update was successful, False otherwise
        """
        with self.get_session() as session:
            try:
                template = session.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
                if not template:
                    logger.error(f"Template with ID {template_id} not found for update")
                    return False
                
                if template_content is not None:
                    template.template_content = template_content
                if template_type is not None:
                    template.template_type = template_type
                if description is not None:
                    template.description = description
                if expected_routing_label is not None:
                    template.expected_routing_label = expected_routing_label
                
                session.commit()
                logger.info(f"Updated template with ID {template_id}")
                return True
            except IntegrityError:
                session.rollback()
                logger.error(f"Integrity error updating template ID {template_id} (duplicate template type?)")
                return False
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error updating template ID {template_id}: {str(e)}")
                return False
    
    def create_message(self, template_id: int, param_id: int, generated_text: str, expected_routing_label: str = None) -> int:
        """
        Create a new generated message and its expected result if provided.
        
        Args:
            template_id: ID of the template used
            param_id: ID of the parameter used
            generated_text: Generated message text
            expected_routing_label: Optional expected routing label for evaluation
            
        Returns:
            ID of the created message
        """
        with self.get_session() as session:
            try:
                message = Messages(
                    template_id=template_id,
                    param_id=param_id,
                    generated_text=generated_text
                )
                session.add(message)
                session.flush()
                
                if expected_routing_label:
                    expected_result = ExpectedResults(
                        message_id=message.message_id,
                        expected_label=expected_routing_label
                    )
                    session.add(expected_result)
                
                session.commit()
                message_id = message.message_id
                logger.info(f"Created message with ID {message_id} for template ID {template_id}")
                if expected_routing_label:
                    logger.info(f"Added expected routing label '{expected_routing_label}' for message {message_id}")
                return message_id
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to create message for template ID {template_id}: {str(e)}")
                raise
    
    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Get message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message as dictionary or None if not found
        """
        with self.get_session() as session:
            try:
                message = session.query(Messages).filter(Messages.message_id == message_id).first()
                if message:
                    return {
                        'message_id': message.message_id,
                        'template_id': message.template_id,
                        'param_id': message.param_id,
                        'generated_text': message.generated_text,
                        'content': message.generated_text,
                        'created_at': message.created_at
                    }
                logger.debug(f"Message with ID {message_id} not found")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving message ID {message_id}: {str(e)}")
                return None
    
    def get_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get messages, limited by the specified amount.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of messages as dictionaries
        """
        with self.get_session() as session:
            try:
                messages = session.query(Messages).order_by(Messages.message_id.desc()).limit(limit).all()
                return [
                    {
                        'message_id': message.message_id,
                        'template_id': message.template_id,
                        'param_id': message.param_id,
                        'generated_text': message.generated_text,
                        'content': message.generated_text,
                        'created_at': message.created_at
                    }
                    for message in messages
                ]
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving messages (limit={limit}): {str(e)}")
                return []
    
    def get_messages_by_template_id(self, template_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get messages by template ID.
        
        Args:
            template_id: Template ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages as dictionaries
        """
        with self.get_session() as session:
            try:
                messages = session.query(Messages).filter(
                    Messages.template_id == template_id
                ).order_by(Messages.message_id.desc()).limit(limit).all()
                
                return [
                    {
                        'message_id': message.message_id,
                        'template_id': message.template_id,
                        'param_id': message.param_id,
                        'generated_text': message.generated_text,
                        'content': message.generated_text,
                        'created_at': message.created_at
                    }
                    for message in messages
                ]
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving messages for template ID {template_id}: {str(e)}")
                return []
    
    def get_messages_by_param(self, param_id: int) -> List[Dict[str, Any]]:
        """
        Get messages by parameter ID.
        
        Args:
            param_id: Parameter ID
            
        Returns:
            List of messages as dictionaries
        """
        with self.get_session() as session:
            try:
                messages = session.query(Messages).filter(Messages.param_id == param_id).all()
                return [
                    {
                        'message_id': message.message_id,
                        'template_id': message.template_id,
                        'param_id': message.param_id,
                        'generated_text': message.generated_text,
                        'content': message.generated_text,
                        'created_at': message.created_at
                    }
                    for message in messages
                ]
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving messages for parameter ID {param_id}: {str(e)}")
                return []
    
    def create_expected_result(self, message_id: int, expected_label: str) -> bool:
        """
        Create an expected result entry for a message.
        
        Args:
            message_id: ID of the message
            expected_label: Expected routing label
            
        Returns:
            True if successful, False otherwise
        """
        with self.get_session() as session:
            try:
                result = ExpectedResults(
                    message_id=message_id,
                    expected_label=expected_label
                )
                session.add(result)
                session.commit()
                logger.info(f"Created expected result for message ID {message_id}: {expected_label}")
                return True
            except IntegrityError:
                session.rollback()
                logger.error(f"Expected result for message ID {message_id} already exists")
                return False
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error creating expected result for message ID {message_id}: {str(e)}")
                return False
    
    def get_expected_result(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Get expected result for a message.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Dictionary with expected result or None if not found
        """
        with self.get_session() as session:
            try:
                result = session.query(ExpectedResults).filter(ExpectedResults.message_id == message_id).first()
                if result:
                    return {
                        'message_id': result.message_id,
                        'expected_label': result.expected_label
                    }
                logger.debug(f"No expected result found for message ID {message_id}")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving expected result for message ID {message_id}: {str(e)}")
                return None
    
    def create_actual_result(self, message_id: int, model_version: str, predicted_label: str, confidence: float) -> bool:
        """
        Create or update an actual result entry for a message.
        
        Args:
            message_id: ID of the message
            model_version: Version of the model used
            predicted_label: Predicted routing label
            confidence: Confidence score for the prediction
            
        Returns:
            True if successful, False otherwise
        """
        with self.get_session() as session:
            try:
                existing_result = session.query(ActualResults).filter(
                    ActualResults.message_id == message_id
                ).first()
                
                if existing_result:
                    existing_result.model_version = model_version
                    existing_result.predicted_label = predicted_label
                    existing_result.confidence = confidence
                    existing_result.classification_date = datetime.now()
                    logger.info(f"Updated actual result for message ID {message_id}")
                else:
                    result = ActualResults(
                        message_id=message_id,
                        model_version=model_version,
                        predicted_label=predicted_label,
                        confidence=confidence
                    )
                    session.add(result)
                    logger.info(f"Created actual result for message ID {message_id}")
                
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Error saving actual result for message ID {message_id}: {str(e)}")
                return False
    
    def get_test_results(self, param_id: int) -> List[Dict[str, Any]]:
        """
        Get all test results for a given parameter.
        
        Args:
            param_id: Parameter ID
            
        Returns:
            List of dictionaries with test results
        """
        with self.get_session() as session:
            try:
                query = session.query(
                    Messages, 
                    ExpectedResults.expected_label,
                    ActualResults.predicted_label,
                    ActualResults.confidence,
                    ActualResults.classification_date
                ).join(
                    ExpectedResults, 
                    Messages.message_id == ExpectedResults.message_id
                ).join(
                    ActualResults,
                    Messages.message_id == ActualResults.message_id
                ).filter(
                    Messages.param_id == param_id
                ).all()
                
                results = []
                for msg, expected, predicted, confidence, date in query:
                    results.append({
                        "message_id": msg.message_id,
                        "generated_text": msg.generated_text,
                        "expected_label": expected,
                        "predicted_label": predicted,
                        "confidence": confidence,
                        "classification_date": date
                    })
                
                return results
            except SQLAlchemyError as e:
                logger.error(f"Error retrieving test results for param_id {param_id}: {str(e)}")
                return []
    
    def execute_query(self, query: str, params: list = None) -> list:
        """
        Execute a custom query on the database.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            List of dictionaries representing the query results
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params)
                
                columns = result.keys()
                results = []
                for row in result:
                    results.append({col: getattr(row, col) for col in columns})
                
                return results
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return []
    
    def execute_update(self, query: str, params: list = None) -> int:
        """
        Execute a custom update query on the database.
        
        Args:
            query: SQL update query to execute
            params: Parameters for the query
            
        Returns:
            Number of rows affected
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params)
                session.commit()
                
                return result.rowcount
        except Exception as e:
            logger.error(f"Error executing update: {str(e)}")
            session.rollback()
            return 0
    
    def ensure_tables_exist(self) -> bool:
        """
        Ensure all necessary tables exist in the database.
        
        Returns:
            True if tables exist or were created successfully, False otherwise
        """
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = ['parameters', 'templates', 'messages', 'expected_results', 'actual_results', 'variator_data']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                self.create_tables()
                logger.info(f"Created missing database tables: {', '.join(missing_tables)}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to ensure tables exist: {str(e)}")
            return False
    
    def add_variator_data(self, data_type: str, data_value: str) -> bool:
        """
        Add variator data to the database.
        
        Args:
            data_type: The type of data (e.g., "currencies")
            data_value: The value to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                existing = session.query(VariatorData).filter_by(
                    data_type=data_type, data_value=data_value).first()
                
                if not existing:
                    variator_data = VariatorData(
                        data_type=data_type,
                        data_value=data_value
                    )
                    session.add(variator_data)
                    session.commit()
                
                return True
        except Exception as e:
            logger.error(f"Error adding variator data {data_type}={data_value}: {str(e)}")
            return False

    def get_variator_data(self, data_type: str) -> list:
        """
        Retrieve variator data of a specific type from the database.
        
        Args:
            data_type: The type of data to retrieve
            
        Returns:
            List of dictionaries with data_type and data_value keys
        """
        try:
            with self.get_session() as session:
                data = session.query(VariatorData).filter_by(data_type=data_type).all()
                
                return [{"data_type": item.data_type, "data_value": item.data_value} for item in data]
        except Exception as e:
            logger.error(f"Error retrieving variator data for {data_type}: {str(e)}")
            return []


def create_database_manager(config_or_uri) -> DatabaseManager:
    """
    Create a database manager from either a configuration dictionary or a direct database URI.
    
    Args:
        config_or_uri: Either a configuration dictionary with database settings 
                      or a direct database URI string
    
    Returns:
        DatabaseManager instance
    """
    if isinstance(config_or_uri, str):
        db_uri = config_or_uri
    
    else:
        db_config = config_or_uri.get("database", {})
        
        if "connection_string" in db_config:
            return DatabaseManager(db_config["connection_string"])
        
        username = db_config.get("username", "")
        password = db_config.get("password", "")
        host = db_config.get("host", "localhost")
        port = db_config.get("port", "5432")
        dbname = db_config.get("dbname", "swift_db")
        sslmode = db_config.get("sslmode", "prefer")
        
        db_uri = f"postgresql://{username}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    
    return DatabaseManager(db_uri) 