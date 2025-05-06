"""
Message Generator Module

This module provides functionality to generate SWIFT message variations
based on templates. It creates artificial test data that simulates
real-world SWIFT messages to test message routing services.
"""

import random
import re
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class MessageGenerator:
    """
    Generates variations of SWIFT messages for testing purposes.
    
    This class is used to create test messages by taking templates and
    applying various modifications to generate a diverse set of inputs
    for testing message routing systems.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the MessageGenerator with the provided configuration.
        
        Args:
            config: Configuration dictionary that may be either the full config with
                   a message_generation key or just the message_generation config directly
        """
        if isinstance(config, dict):
            message_config = config.get('message_generation', config)
            self.perturbation_degree = message_config.get('perturbation_degree', 0.2)
            self.seed = message_config.get('seed', 42)
            self.max_variations = message_config.get('max_variations_per_template', 5)
            self.field_substitution_rate = message_config.get('field_substitution_rate', 0.3)
            
            if 'database' in config:
                self.db_uri = config.get('database', {}).get('connection_string')
            elif 'database_uri' in message_config:
                self.db_uri = message_config.get('database_uri')
            else:
                raise ValueError("Database connection string not found in configuration")
        else:
            raise ValueError("Configuration must be a dictionary")
            
        random.seed(self.seed)
        
        self.currencies = []
        self.bank_prefixes = []
        self.bank_suffixes = []
        
        self.load_data_from_database()
        
    def load_data_from_database(self) -> None:
        """Load variator data from the database."""
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT data_value FROM variator_data WHERE data_type = 'currencies'"))
                self.currencies = [row[0] for row in result]
                
                result = conn.execute(text("SELECT data_value FROM variator_data WHERE data_type = 'bank_prefixes'"))
                self.bank_prefixes = [row[0] for row in result]
                
                result = conn.execute(text("SELECT data_value FROM variator_data WHERE data_type = 'bank_suffixes'"))
                self.bank_suffixes = [row[0] for row in result]
                
                logger.info(f"Loaded data from database: {len(self.currencies)} currencies, " 
                           f"{len(self.bank_prefixes)} bank prefixes, {len(self.bank_suffixes)} bank suffixes")
                
                if not self.currencies or not self.bank_prefixes:
                    logger.warning("Missing essential data in database. Please run populate_variator_data.py script.")
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            raise RuntimeError(f"Failed to load variator data from database: {str(e)}")
        
    def parse_template(self, template: str) -> Dict[str, List[Tuple[str, int]]]:
        """
        Parse a SWIFT message template and identify key fields.
        
        Args:
            template: SWIFT message template string
            
        Returns:
            Dictionary mapping field types to lists of (field content, position) tuples
        """
        parsed = {}
        
        references = re.finditer(r':20:([A-Z0-9]+)', template)
        parsed['reference'] = [(m.group(1), m.start()) for m in references]
        
        date_amounts = re.finditer(r':32A:(\d{6})([A-Z]{3})([0-9,.]+)', template)
        parsed['date_amount'] = [(m.groups(), m.start()) for m in date_amounts]
        
        accounts = re.finditer(r'/([0-9]+)', template)
        parsed['account'] = [(m.group(1), m.start()) for m in accounts]
        
        banks = re.finditer(r':[0-9]{2}A:([A-Z]+)', template)
        parsed['bank'] = [(m.group(1), m.start()) for m in banks]
        
        return parsed
    
    def generate_message(self, template: str) -> str:
        """
        Generate a single SWIFT message by modifying the template.
        
        Args:
            template: The SWIFT message template to modify
            
        Returns:
            Modified SWIFT message string
        """
        parsed = self.parse_template(template)
        
        modified = template
        
        for field_type, fields in parsed.items():
            for field_content, position in fields:
                if random.random() < self.field_substitution_rate:
                    modified = self.modify_field(field_type, field_content, modified, position)
                    
        return modified
    
    def modify_field(self, field_type: str, field_content: str, 
                    message: str = None, position: int = None) -> str:
        """
        Modify a specific field in the message.
        
        Args:
            field_type: Type of field to modify (reference, date_amount, account, bank)
            field_content: Current content of the field
            message: Full message string (if modifying in place)
            position: Position of field in message (if modifying in place)
            
        Returns:
            Modified field content or full message if message and position are provided
        """
        modified_content = field_content
        
        if field_type == 'reference':
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            modified_content = ''.join(random.choices(chars, k=len(field_content)))
            
        elif field_type == 'date_amount':
            date, currency, amount = field_content
            day = int(date[0:2])
            month = int(date[2:4])
            year = int(date[4:6])
            
            day = max(1, min(28, day + random.randint(-5, 5)))
            
            month_change = random.randint(-1, 1)
            month += month_change
            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1
                
            new_date = f"{day:02d}{month:02d}{year:02d}"
            
            if self.currencies and random.random() < 0.3:
                currency = random.choice(self.currencies)
                
            amount_value = float(amount.replace(',', '.').replace(' ', ''))
            amount_value *= random.uniform(0.7, 1.3)
            
            new_amount = f"{amount_value:.2f}".replace('.', ',')
            
            modified_content = (new_date, currency, new_amount)
            
        elif field_type == 'account':
            modified_content = ''.join(random.choices('0123456789', k=len(field_content)))
            
        elif field_type == 'bank':
            if self.bank_prefixes:
                prefix = random.choice(self.bank_prefixes)
                suffix_length = len(field_content) - len(prefix)
                
                if suffix_length > 0:
                    if self.bank_suffixes and random.random() < 0.5:
                        available_suffixes = [s for s in self.bank_suffixes if len(s) <= suffix_length]
                        if available_suffixes:
                            suffix = random.choice(available_suffixes)
                            padding_length = suffix_length - len(suffix)
                            padding = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=padding_length)) if padding_length > 0 else ''
                            modified_content = prefix + padding + suffix
                        else:
                            modified_content = prefix + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=suffix_length))
                    else:
                        modified_content = prefix + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=suffix_length))
                else:
                    modified_content = field_content
            else:
                modified_content = field_content
        
        if message and position is not None:
            if field_type == 'date_amount':
                date, currency, amount = modified_content
                
                field_match = re.search(r':32A:(\d{6})([A-Z]{3})([0-9,.]+)', message[position:position+30])
                if field_match:
                    start, end = field_match.span()
                    start += position
                    end += position
                    
                    new_field = f":32A:{date}{currency}{amount}"
                    return message[:start] + new_field + message[end:]
            else:
                field_pattern = re.escape(field_content)
                position_end = position + 50
                
                field_match = re.search(field_pattern, message[position:position_end])
                if field_match:
                    start, end = field_match.span()
                    start += position
                    end += position
                    
                    return message[:start] + modified_content + message[end:]
            
            return message
        
        if field_type == 'date_amount':
            date, currency, amount = modified_content
            return f"{date}{currency}{amount}"
        
        return modified_content
    
    def generate_variations(self, template: str, count: int = None) -> List[str]:
        """
        Generate multiple variations of a SWIFT message template.
        
        Args:
            template: SWIFT message template string
            count: Number of variations to generate (default is self.max_variations)
            
        Returns:
            List of generated SWIFT message strings
        """
        if count is None:
            count = self.max_variations
            
        variations = []
        for _ in range(count):
            variation = self.generate_message(template)
            variations.append(variation)
            
        return variations


def create_message_generator(config: Dict[str, Any]) -> MessageGenerator:
    """
    Factory function to create a MessageGenerator instance.
    
    Args:
        config: Configuration dictionary for the message generator
        
    Returns:
        A configured MessageGenerator instance
    """
    return MessageGenerator(config)