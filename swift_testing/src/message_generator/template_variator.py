"""
Template Variator Module

This module provides functionality to add random variations to SWIFT message templates
before they are processed by the message generator. The goal is to increase the diversity
of generated messages by modifying templates directly.
"""

import random
import string
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class TemplateVariator:
    """
    Adds random variations to SWIFT message templates.
    
    This class modifies SWIFT message templates by applying random variations to fields such as
    reference numbers, dates, amounts, bank codes, sender and beneficiary blocks, and payment details.
    All variations are applied with maximum randomness.
    """
    
    REFERENCE_TAGS = [':20:', ':21:']
    DATE_AMOUNT_TAGS = [':32A:']
    BANK_CODE_TAGS = [':52A:', ':57A:', ':58A:', ':53A:', ':54A:']
    PAYMENT_DETAIL_TAGS = [':70:']
    SENDER_TAGS = [':50K:']
    BENEFICIARY_TAGS = [':59:']
    
    BLOCK_END_MARKERS = [':', '{', '}']
    
    def __init__(self, db_uri: str = None) -> None:
        """
        Initialize the TemplateVariator.

        Args:
            db_uri: Database connection URI to load variator data (required)
        """
        if not db_uri:
            raise ValueError("Database URI is required - variator data is loaded exclusively from the database")
        
        self.db_uri = db_uri
        
        self._init_config()
        
        self._load_variator_data_from_db()
        
        self._verify_data_loaded()

    def _init_config(self) -> None:
        """Initialize configuration with default values that may be overridden later."""
        self.attribute_mapping = {
            'currencies': 'common_currencies',
        }
        
        self.essential_categories = [
            'currencies', 'bank_prefixes', 'bank_suffixes', 'first_names', 'last_names',
            'company_prefixes', 'company_mids', 'company_suffixes', 'street_names',
            'street_types', 'cities', 'reference_prefixes'
        ]
        
        self.payment_detail_templates = []
        self.instruction_templates = []

    def _verify_data_loaded(self) -> None:
        """Verify that essential data has been loaded from the database."""
        loaded_attributes = [attr for attr in dir(self) 
                            if not attr.startswith('_') and 
                            isinstance(getattr(self, attr), list) and
                            getattr(self, attr)]
        
        if not loaded_attributes:
            raise ValueError("No variator data was loaded from the database. "
                             "Please run the populate_variator_data.py script to populate the database.")
            
        logger.info(f"Loaded {len(loaded_attributes)} data types: {', '.join(loaded_attributes)}")

        missing = []
        
        for category in self.essential_categories:
            if category == 'currencies':
                if not hasattr(self, 'common_currencies') and not hasattr(self, 'currencies'):
                    missing.append(category)
            elif not hasattr(self, category) or not getattr(self, category, None):
                missing.append(category)
        
        if missing:
            raise ValueError(f"Missing essential data in database: {', '.join(missing)}. "
                            f"Please run the populate_variator_data.py script to populate the database.")

    def _load_variator_data_from_db(self) -> None:
        """Load variator data from the database."""
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT data_type, data_value FROM variator_data"))
                
                data_by_type = {}
                for row in result:
                    data_type, data_value = row
                    if data_type not in data_by_type:
                        data_by_type[data_type] = []
                    data_by_type[data_type].append(data_value)
                
                if 'config' in data_by_type:
                    self._apply_config_from_db(data_by_type['config'])
                    del data_by_type['config']
                
                for data_type, values in data_by_type.items():
                    if values:
                        attr_name = self.attribute_mapping.get(data_type, data_type)
                        setattr(self, attr_name, values)
                
                logger.info(f"Loaded variator data from database: {', '.join(data_by_type.keys())}")
        except Exception as e:
            logger.error(f"Error loading variator data from database: {str(e)}")
            raise ValueError(f"Failed to load variator data from database: {str(e)}")

    def _apply_config_from_db(self, config_values: List[str]) -> None:
        """
        Apply configuration from database values.
        
        Args:
            config_values: List of configuration entries in format key=value
        """
        for config_entry in config_values:
            if '=' in config_entry:
                key, value = config_entry.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key.endswith('_list') and ',' in value:
                    value_list = [v.strip() for v in value.split(',')]
                    
                    if key == 'essential_categories_list':
                        attr_name = 'essential_categories'
                    elif key == 'payment_detail_templates_list':
                        attr_name = 'payment_detail_templates'
                    elif key == 'instruction_templates_list':
                        attr_name = 'instruction_templates'
                    elif '_tags_list' in key:
                        attr_name = key.replace('_list', '').upper()
                    else:
                        attr_name = key.replace('_list', '')
                            
                    if hasattr(self, attr_name):
                        setattr(self, attr_name, value_list)

    def add_variations(self, template_text: str) -> str:
        """
        Add random variations to a SWIFT message template.

        Args:
            template_text: The original SWIFT message template as a string.

        Returns:
            A modified template string with random variations.
        """
        lines: List[str] = template_text.split('\n')
        modified_lines: List[str] = lines.copy()

        for j in range(len(lines)):
            current_line: str = lines[j]
            if not current_line.strip():
                continue

            try:
                processed = False
                
                for tag in self.REFERENCE_TAGS:
                    if tag in current_line:
                        modified_lines[j] = self._vary_reference_field(current_line, tag)
                        processed = True
                        break
                
                if processed:
                    continue
                        
                for tag in self.DATE_AMOUNT_TAGS:
                    if tag in current_line:
                        modified_lines[j] = self._vary_date_amount_currency(current_line)
                        processed = True
                        break
                
                if processed:
                    continue
                    
                if "/" in current_line and any(c.isdigit() for c in current_line):
                    modified_lines[j] = self._vary_account_numbers(current_line)
                    processed = True
                
                if processed:
                    continue
                    
                for tag in self.BANK_CODE_TAGS:
                    if tag in current_line:
                        modified_lines[j] = self._vary_bank_code(current_line, tag)
                        processed = True
                        break
                
                if processed:
                    continue
                
                for tag in self.PAYMENT_DETAIL_TAGS:
                    if tag in current_line:
                        start_idx = j
                        end_idx = j + 1
                        while end_idx < len(lines) and not any(marker in lines[end_idx] for marker in self.BLOCK_END_MARKERS):
                            end_idx += 1
                        for m in range(start_idx, end_idx):
                            modified_lines[m] = self._vary_payment_details(lines[m])
                        processed = True
                        break
                
                if processed:
                    continue
                        
                for tag in self.SENDER_TAGS:
                    if tag in current_line:
                        sender_start = j
                        end_idx = j + 1
                        while end_idx < len(lines) and not any(marker in lines[end_idx] for marker in self.BLOCK_END_MARKERS):
                            end_idx += 1
                        new_block = self._generate_new_sender_block()
                        modified_lines[sender_start] = tag
                        for offset, block_line in enumerate(new_block.split('\n')):
                            if sender_start + offset + 1 < len(modified_lines):
                                modified_lines[sender_start + offset + 1] = block_line
                        processed = True
                        break
                
                if processed:
                    continue
                        
                for tag in self.BENEFICIARY_TAGS:
                    if tag in current_line:
                        ben_start = j
                        end_idx = j + 1
                        while end_idx < len(lines) and not any(marker in lines[end_idx] for marker in self.BLOCK_END_MARKERS):
                            end_idx += 1
                        new_block = self._generate_new_beneficiary_block()
                        modified_lines[ben_start] = tag
                        for offset, block_line in enumerate(new_block.split('\n')):
                            if ben_start + offset + 1 < len(modified_lines):
                                modified_lines[ben_start + offset + 1] = block_line
                        processed = True
                        break
                        
            except Exception as e:
                logger.error(f"Error processing line {j}: {e}")
                modified_lines[j] = current_line

        for j in range(len(modified_lines)):
            for tag in self.PAYMENT_DETAIL_TAGS:
                if tag in modified_lines[j] and random.random() < 0.5:
                    details = self._generate_random_instructions()
                    insert_idx = j + 1
                    while insert_idx < len(modified_lines) and not any(marker in modified_lines[insert_idx] for marker in self.BLOCK_END_MARKERS):
                        insert_idx += 1
                    for offset, detail_line in enumerate(details.split('\n')):
                        modified_lines.insert(insert_idx + offset, detail_line)
                    break
        
        return '\n'.join(modified_lines)

    def _vary_reference_field(self, line: str, field_tag: str) -> str:
        """Apply variations to reference fields."""
        try:
            parts = line.split(field_tag)
            if len(parts) < 2:
                return line
            ref = parts[1].strip()
            
            prefix = random.choice(self.reference_prefixes) if hasattr(self, 'reference_prefixes') and self.reference_prefixes else ""
            digits = ''.join(random.choices(string.digits, k=random.randint(4, 8)))
            letters = ''.join(random.choices(string.ascii_uppercase, k=random.randint(1, 3)))
            new_ref = f"{prefix}{digits}{letters}"
            return line.replace(ref, new_ref)
        except Exception as e:
            logger.debug(f"Error varying reference field: {e}")
        return line

    def _vary_date_amount_currency(self, line: str) -> str:
        """Apply variations to date, currency, and amount fields."""
        try:
            date_part = line[5:11] if len(line) > 11 else ""
            if date_part.isdigit():
                today = datetime.now()
                days_back = random.randint(0, 730)
                new_date = (today - timedelta(days=days_back)).strftime('%y%m%d')
                line = line.replace(date_part, new_date)
            if len(line) > 14:
                curr_part = line[11:14]
                if curr_part.isalpha():
                    currencies = getattr(self, 'common_currencies', getattr(self, 'currencies'))
                    new_curr = random.choice(currencies)
                    line = line.replace(curr_part, new_curr)
            if "," in line:
                match = re.search(r'(\d+),(\d{2})', line)
                if match:
                    old_amount = f"{match.group(1)},{match.group(2)}"
                    new_whole = str(random.randint(100, 999999))
                    new_cents = f"{random.randint(0, 99):02d}"
                    new_amount = f"{new_whole},{new_cents}"
                    line = line.replace(old_amount, new_amount)
        except Exception as e:
            logger.debug(f"Error varying date/amount/currency: {e}")
        return line

    def _vary_account_numbers(self, line: str) -> str:
        """Apply variations to account numbers."""
        try:
            parts = line.split("/")
            for idx in range(1, len(parts)):
                digit_match = re.search(r'(\d{5,})', parts[idx])
                if digit_match:
                    digits = digit_match.group(1)
                    new_digits = ''.join(random.choices(string.digits, k=len(digits)))
                    parts[idx] = parts[idx].replace(digits, new_digits, 1)
            return "/".join(parts)
        except Exception as e:
            logger.debug(f"Error varying account numbers: {e}")
        return line

    def _vary_bank_code(self, line: str, tag: str) -> str:
        """Apply variations to bank code fields."""
        try:
            parts = line.split(tag)
            if len(parts) > 1:
                code_part = parts[1].strip()
                
                bank_part = random.choice(self.bank_prefixes)[:4]
                country_part = random.choice(self.bank_suffixes)
                location_part = random.choice(string.ascii_uppercase) + random.choice(string.digits)
                if random.random() < 0.5:
                    branch_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
                    new_code = f"{bank_part}{country_part}{location_part}{branch_part}"
                else:
                    new_code = f"{bank_part}{country_part}{location_part}"
                return line.replace(code_part, new_code, 1)
        except Exception as e:
            logger.debug(f"Error varying bank code: {e}")
        return line

    def _vary_payment_details(self, line: str) -> str:
        """Apply variations to payment details lines."""
        try:
            if len(line) > 10:
                template = random.choice(self.payment_detail_templates)
                return self._process_template(template)
        except Exception as e:
            logger.debug(f"Error varying payment details: {e}")
        return line

    def _process_template(self, template: str) -> str:
        """
        Process a template string by substituting variables.
        
        Handles patterns like:
        - {number:min:max} - Random number between min and max
        - {string:length} - Random string of specified length
        
        Args:
            template: Template string with variable patterns
            
        Returns:
            Processed string with variables replaced
        """
        result = template
        
        number_pattern = r'\{number:(\d+):(\d+)\}'
        for match in re.finditer(number_pattern, template):
            min_val = int(match.group(1))
            max_val = int(match.group(2))
            random_num = str(random.randint(min_val, max_val))
            result = result.replace(match.group(0), random_num, 1)
        
        string_pattern = r'\{string:(\d+)\}'
        for match in re.finditer(string_pattern, template):
            length = int(match.group(1))
            random_str = self._random_string(length)
            result = result.replace(match.group(0), random_str, 1)
            
        return result

    def _vary_sender_beneficiary_line(self, line: str) -> str:
        """
        Vary sender or beneficiary information lines.

        For names and addresses, generate new values if conditions meet.
        """
        try:
            if line.startswith(':'):
                return line
                
            if line.isupper() and not any(c.isdigit() for c in line):
                if any(sub in line for sub in self.company_suffixes):
                    return f"{random.choice(self.company_prefixes)} {random.choice(self.company_mids)} {random.choice(self.company_suffixes)}"
                else:
                    return f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
            elif any(c.isdigit() for c in line) and any(c.isalpha() for c in line):
                street_num = str(random.randint(1, 999))
                return f"{street_num} {random.choice(self.street_names)} {random.choice(self.street_types)}"
        except Exception as e:
            logger.debug(f"Error varying sender/beneficiary line: {e}")
        return line

    def _generate_new_sender_block(self) -> str:
        """Generate a completely new sender block."""
        try:
            if random.random() < 0.7:
                name = f"{random.choice(self.company_prefixes)} {random.choice(self.company_mids)} {random.choice(self.company_suffixes)}"
            else:
                name = f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
            
            street_num = str(random.randint(1, 999))
            address = f"{street_num} {random.choice(self.street_names)} {random.choice(self.street_types)}"
            
            if random.random() < 0.6:
                address += f"\n{random.choice(self.cities)}"
            
            return f"{name}\n{address}"
        except Exception as e:
            logger.error(f"Error generating new sender block: {e}")
            raise ValueError("Missing required data for sender block generation")

    def _generate_new_beneficiary_block(self) -> str:
        """Generate a completely new beneficiary block."""
        try:
            if random.random() < 0.5:
                name = f"{random.choice(self.company_prefixes)} {random.choice(self.company_mids)} {random.choice(self.company_suffixes)}"
            else:
                name = f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
            
            street_num = str(random.randint(1, 999))
            address = f"{street_num} {random.choice(self.street_names)} {random.choice(self.street_types)}"
            
            if random.random() < 0.7:
                address += f"\n{random.choice(self.cities)}"
            
            return f"{name}\n{address}"
        except Exception as e:
            logger.error(f"Error generating new beneficiary block: {e}")
            raise ValueError("Missing required data for beneficiary block generation")

    def _generate_random_instructions(self) -> str:
        """Generate random payment instructions or details."""
        template = random.choice(self.instruction_templates)
        return self._process_template(template)

    def _random_string(self, length: int, char_set: str = string.ascii_uppercase + string.digits) -> str:
        """Generate a random string of the specified length."""
        return ''.join(random.choices(char_set, k=length))

    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Retrieve all templates from the database.
        
        Returns:
            List of template dictionaries, each containing template_id, template_type,
            template_content, expected_routing_label, and description
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    SELECT id as template_id, template_type, template_content, 
                           expected_routing_label, description 
                    FROM templates
                """)
                result = conn.execute(query)
                
                templates = []
                for row in result:
                    template = {
                        "template_id": row.template_id,
                        "template_type": row.template_type,
                        "template_content": row.template_content,
                        "expected_routing_label": row.expected_routing_label,
                        "description": row.description
                    }
                    templates.append(template)
                
                return templates
        except Exception as e:
            logger.error(f"Error retrieving templates: {str(e)}")
            return []
    
    def get_template_by_type(self, template_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a template by its type.
        
        Args:
            template_type: The type of template to retrieve (e.g., "MT103")
            
        Returns:
            Template dictionary if found, None otherwise
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    SELECT id as template_id, template_type, template_content, 
                           expected_routing_label, description 
                    FROM templates
                    WHERE template_type = :template_type
                """)
                result = conn.execute(query, {"template_type": template_type})
                
                row = result.fetchone()
                if row:
                    template = {
                        "template_id": row.template_id,
                        "template_type": row.template_type,
                        "template_content": row.template_content,
                        "expected_routing_label": row.expected_routing_label,
                        "description": row.description
                    }
                    return template
                return None
        except Exception as e:
            logger.error(f"Error retrieving template by type {template_type}: {str(e)}")
            return None
    
    def create_template(self, template_type: str, template_content: str, 
                       description: str, expected_routing_label: str) -> int:
        """
        Create a new template in the database.
        
        Args:
            template_type: The type of template (e.g., "MT103")
            template_content: The content of the template
            description: Description of the template
            expected_routing_label: Expected routing label for messages from this template
            
        Returns:
            ID of the created template
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO templates (template_type, template_content, description, expected_routing_label)
                    VALUES (:template_type, :template_content, :description, :expected_routing_label)
                    RETURNING id
                """)
                result = conn.execute(query, {
                    "template_type": template_type,
                    "template_content": template_content,
                    "description": description,
                    "expected_routing_label": expected_routing_label
                })
                
                template_id = result.scalar()
                conn.commit()
                
                return template_id
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise ValueError(f"Failed to create template: {str(e)}")
    
    def update_template(self, template_id: int, template_type: str, template_content: str,
                       description: str, expected_routing_label: str) -> bool:
        """
        Update an existing template in the database.
        
        Args:
            template_id: ID of the template to update
            template_type: New type for the template
            template_content: New content for the template
            description: New description for the template
            expected_routing_label: New expected routing label
            
        Returns:
            True if successful, False otherwise
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    UPDATE templates
                    SET template_type = :template_type,
                        template_content = :template_content,
                        description = :description,
                        expected_routing_label = :expected_routing_label
                    WHERE id = :template_id
                """)
                result = conn.execute(query, {
                    "template_id": template_id,
                    "template_type": template_type,
                    "template_content": template_content,
                    "description": description,
                    "expected_routing_label": expected_routing_label
                })
                
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            return False
    
    def delete_template(self, template_id: int) -> bool:
        """
        Delete a template from the database.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    DELETE FROM templates
                    WHERE id = :template_id
                """)
                result = conn.execute(query, {"template_id": template_id})
                
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            return False
    
    def get_variator_data(self, data_type: str) -> List[str]:
        """
        Retrieve variator data of a specific type from the database.
        
        Args:
            data_type: The type of data to retrieve
            
        Returns:
            List of data values
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    SELECT data_value
                    FROM variator_data
                    WHERE data_type = :data_type
                """)
                result = conn.execute(query, {"data_type": data_type})
                
                data_values = [row.data_value for row in result]
                return data_values
        except Exception as e:
            logger.error(f"Error retrieving variator data for {data_type}: {str(e)}")
            return []
    
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
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                check_query = text("""
                    SELECT COUNT(*) as count
                    FROM variator_data
                    WHERE data_type = :data_type AND data_value = :data_value
                """)
                check_result = conn.execute(check_query, {
                    "data_type": data_type,
                    "data_value": data_value
                }).scalar()
                
                if check_result == 0:
                    query = text("""
                        INSERT INTO variator_data (data_type, data_value)
                        VALUES (:data_type, :data_value)
                    """)
                    conn.execute(query, {
                        "data_type": data_type,
                        "data_value": data_value
                    })
                    
                    conn.commit()
                
                return True
        except Exception as e:
            logger.error(f"Error adding variator data {data_type}={data_value}: {str(e)}")
            return False
    
    def delete_variator_data(self, data_type: str, data_value: str) -> bool:
        """
        Delete variator data from the database.
        
        Args:
            data_type: The type of data
            data_value: The value to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            engine = create_engine(self.db_uri)
            with engine.connect() as conn:
                query = text("""
                    DELETE FROM variator_data
                    WHERE data_type = :data_type AND data_value = :data_value
                """)
                result = conn.execute(query, {
                    "data_type": data_type,
                    "data_value": data_value
                })
                
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting variator data {data_type}={data_value}: {str(e)}")
            return False

def create_template_variator(db_uri: str = None) -> TemplateVariator:
    """
    Helper function to create a TemplateVariator instance.

    Args:
        db_uri: Database connection URI to load variator data (required)

    Returns:
        A TemplateVariator instance.
    """
    return TemplateVariator(db_uri)