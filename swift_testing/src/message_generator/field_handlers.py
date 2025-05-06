"""
Field Handlers Module

This module provides a system for handling various SWIFT message
fields and their substitution during message generation.

All handlers are dynamically registered in a global registry so that new field handlers
can be added or modified without changing the core message generator code.
"""

import re
import random
import string
import logging
from typing import List, Dict, Any, Match
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

FIELD_HANDLER_REGISTRY: Dict[str, 'FieldHandler'] = {}

class FieldHandler(ABC):
    """
    Abstract base class for field handlers.

    Each field handler must implement the substitute() method to generate a new value
    for a matched field from a SWIFT message template.
    """
    def __init__(self, substitutions: Dict[str, List[str]]) -> None:
        """
        Initialize the field handler with substitution lists.

        Args:
            substitutions: A dictionary mapping field names to lists of possible substitute values.
        """
        self.substitutions = substitutions
    
    @abstractmethod
    def substitute(self, match: Match) -> str:
        """
        Substitute the matched field with a new value.

        Args:
            match: The regex match object containing the field parts.

        Returns:
            The substituted field as a string.
        """
        pass

class ReferenceFieldHandler(FieldHandler):
    """Handler for SWIFT reference fields (e.g., :20:REFERENCE)."""
    def substitute(self, match: Match) -> str:
        field_tag = match.group(1)
        try:
            new_value = random.choice(self.substitutions.get("reference", []))
        except IndexError:
            new_value = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{field_tag}{new_value}"

class DateAmountCurrencyFieldHandler(FieldHandler):
    """
    Handler for SWIFT date, currency, and amount fields

    Expects the regex to capture four groups:
      1. Field tag (e.g., ":32A:")
      2. Date (YYMMDD)
      3. Currency (3 letters)
      4. Amount (numeric, may contain commas)
    """
    def substitute(self, match: Match) -> str:
        field_tag = match.group(1)
        new_date = random.choice(self.substitutions.get("dates", ["".join(random.choices("0123456789", k=6))]))
        new_currency = random.choice(self.substitutions.get("currencies", ["".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))]))
        new_amount = random.choice(self.substitutions.get("amounts", [f"{random.randint(1000, 10000000)},00"]))
        return f"{field_tag}{new_date}{new_currency}{new_amount}"

class AccountNumberFieldHandler(FieldHandler):
    """Handler for account number fields (e.g., /12345678)."""
    def substitute(self, match: Match) -> str:
        prefix = match.group(1)
        new_account = random.choice(self.substitutions.get("account_numbers", [
            "".join(random.choices("0123456789", k=random.randint(8, 12)))
        ]))
        return f"{prefix}{new_account}"

class BankCodeFieldHandler(FieldHandler):
    """Handler for bank code fields (e.g., :BANKUS33)."""
    def substitute(self, match: Match) -> str:
        prefix = match.group(1)
        new_code = random.choice(self.substitutions.get("bank_codes", [
            "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=random.randint(8, 11)))
        ]))
        return f"{prefix}{new_code}"

class SenderBlockFieldHandler(FieldHandler):
    """
    Handler for multi-line sender blocks.

    Expected regex capture groups:
      1. The sender field tag line
      2. The sender name (line 2)
      3. The sender address (line 3)
      4. Trailing newline or end-of-string
    """
    def substitute(self, match: Match) -> str:
        prefix = match.group(1)
        try:
            new_name = random.choice(self.substitutions.get("sender_names", ["DEFAULT SENDER"]))
            new_address = random.choice(self.substitutions.get("sender_addresses", ["DEFAULT SENDER ADDRESS"]))
        except Exception as e:
            logger.error(f"Error in SenderBlockFieldHandler: {e}")
            new_name, new_address = "DEFAULT SENDER", "DEFAULT SENDER ADDRESS"
        trailing = match.group(4)
        return f"{prefix}{new_name}\n{new_address}{trailing}"

class BeneficiaryBlockFieldHandler(FieldHandler):
    """
    Handler for multi-line beneficiary blocks.

    Expected regex capture groups:
      1. The beneficiary field tag line
      2. The beneficiary name (line 2)
      3. The beneficiary address (line 3)
      4. Trailing newline or end-of-string
    """
    def substitute(self, match: Match) -> str:
        prefix = match.group(1)
        try:
            new_name = random.choice(self.substitutions.get("beneficiary_names", ["DEFAULT BENEFICIARY"]))
            new_address = random.choice(self.substitutions.get("beneficiary_addresses", ["DEFAULT BENEFICIARY ADDRESS"]))
        except Exception as e:
            logger.error(f"Error in BeneficiaryBlockFieldHandler: {e}")
            new_name, new_address = "DEFAULT BENEFICIARY", "DEFAULT BENEFICIARY ADDRESS"
        trailing = match.group(4)
        return f"{prefix}{new_name}\n{new_address}{trailing}"

class DefaultFieldHandler(FieldHandler):
    """Default handler for any unrecognized field type."""
    def substitute(self, match: Match) -> str:
        original = match.group(0)
        length = len(original)
        prefix = original[0] if length > 0 else ""
        if length > 1:
            random_str = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length-1))
            return f"{prefix}{random_str}"
        return original

def register_field_handler(field_type: str, handler: FieldHandler) -> None:
    """
    Register a field handler in the global registry.

    Args:
        field_type: A unique identifier for the field type.
        handler: An instance of a FieldHandler.
    """
    FIELD_HANDLER_REGISTRY[field_type] = handler
    logger.debug(f"Registered handler for field '{field_type}'.")

def initialize_field_handlers(config: Any) -> None:
    """
    Initialize and register field handlers based on the provided configuration.

    This function reads the 'field_patterns' from the configuration and registers dedicated handlers for each
    field type using their associated substitution lists.

    Args:
        config: A validated configuration object (Pydantic model) for message generation.
    """
    FIELD_HANDLER_REGISTRY.clear()
    
    if isinstance(config, dict):
        substitutions = config.get("message_generation", {}).get("substitutions", {})
        field_patterns = config.get("message_generation", {}).get("field_patterns", {})
    else:
        substitutions = config.message_generation.substitutions
        field_patterns = config.message_generation.field_patterns

    for field_type in field_patterns:
        if field_type == "reference":
            register_field_handler(field_type, ReferenceFieldHandler(substitutions))
        elif field_type == "date_amount_currency":
            register_field_handler(field_type, DateAmountCurrencyFieldHandler(substitutions))
        elif field_type == "account_number":
            register_field_handler(field_type, AccountNumberFieldHandler(substitutions))
        elif field_type == "bank_code":
            register_field_handler(field_type, BankCodeFieldHandler(substitutions))
        elif field_type == "sender_block":
            register_field_handler(field_type, SenderBlockFieldHandler(substitutions))
        elif field_type == "beneficiary_block":
            register_field_handler(field_type, BeneficiaryBlockFieldHandler(substitutions))
        else:
            # For any unknown field type, use the default handler.
            register_field_handler(field_type, DefaultFieldHandler(substitutions))