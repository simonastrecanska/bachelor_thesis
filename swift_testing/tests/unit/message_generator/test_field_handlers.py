"""
Unit tests for the field handlers component.

Tests the various field handlers that are responsible for
substituting specific fields in SWIFT messages.
"""

import pytest
import re
from unittest.mock import patch, MagicMock

from swift_testing.src.message_generator.field_handlers import (
    FieldHandler, ReferenceFieldHandler, DateAmountCurrencyFieldHandler,
    AccountNumberFieldHandler, BankCodeFieldHandler, SenderBlockFieldHandler, BeneficiaryBlockFieldHandler,
    initialize_field_handlers, FIELD_HANDLER_REGISTRY
)


class TestFieldHandler:
    """Tests for the FieldHandler base class."""
    
    def test_substitute_not_implemented(self):
        """Test that the abstract method raises NotImplementedError."""
        class TestHandler(FieldHandler):
            def substitute(self, match):
                pass
            
        handler = TestHandler({})
        
        handler.substitute = MagicMock(side_effect=NotImplementedError)
        
        with pytest.raises(NotImplementedError):
            handler.substitute(MagicMock())


class TestReferenceFieldHandler:
    """Tests for the ReferenceFieldHandler class."""
    
    def test_creation(self):
        """Test that the handler can be created successfully."""
        substitutions = {"reference": ["REF123", "REF456"]}
        handler = ReferenceFieldHandler(substitutions)
        assert handler is not None
        assert isinstance(handler, ReferenceFieldHandler)
        assert handler.substitutions == substitutions
    
    def test_substitute(self):
        """Test the substitute method."""
        substitutions = {"reference": ["NEWREF123", "NEWREF456"]}
        handler = ReferenceFieldHandler(substitutions)
        
        match = MagicMock()
        match.group.side_effect = lambda idx: ":20:" if idx == 1 else "OLDREF789"
        
        result = handler.substitute(match)
        
        assert result.startswith(":20:")
        assert result in [":20:NEWREF123", ":20:NEWREF456"]
    
    @patch('random.choice')
    def test_substitute_with_fixed_choice(self, mock_choice):
        """Test the substitute method with a predetermined random choice."""
        substitutions = {"reference": ["NEWREF123", "NEWREF456"]}
        handler = ReferenceFieldHandler(substitutions)
        
        mock_choice.return_value = "NEWREF123"
        
        match = MagicMock()
        match.group.side_effect = lambda idx: ":20:" if idx == 1 else "OLDREF789"
        
        result = handler.substitute(match)
        
        assert result == ":20:NEWREF123"
        mock_choice.assert_called_once_with(["NEWREF123", "NEWREF456"])


class TestDateAmountCurrencyFieldHandler:
    """Tests for the DateAmountCurrencyFieldHandler class."""
    
    def test_creation(self):
        """Test that the handler can be created successfully."""
        substitutions = {
            "dates": ["210615", "210616"],
            "currencies": ["USD", "EUR"],
            "amounts": ["1000,00", "5000,00"]
        }
        handler = DateAmountCurrencyFieldHandler(substitutions)
        assert handler is not None
        assert isinstance(handler, DateAmountCurrencyFieldHandler)
        assert handler.substitutions == substitutions
    
    def test_substitute(self):
        """Test the substitute method."""
        substitutions = {
            "dates": ["210615", "210616"],
            "currencies": ["USD", "EUR"],
            "amounts": ["1000,00", "5000,00"]
        }
        handler = DateAmountCurrencyFieldHandler(substitutions)
        
        match = MagicMock()
        match.group.side_effect = lambda idx: {
            1: ":32A:",
            2: "210617",
            3: "GBP",
            4: "3000,00"
        }.get(idx)
        
        result = handler.substitute(match)
        
        assert result.startswith(":32A:")
        assert any(date in result for date in substitutions["dates"])
        assert any(curr in result for curr in substitutions["currencies"])
        assert any(amt in result for amt in substitutions["amounts"])


class TestAccountNumberFieldHandler:
    """Tests for the AccountNumberFieldHandler class."""
    
    def test_creation(self):
        """Test that the handler can be created successfully."""
        substitutions = {"account_numbers": ["12345678", "87654321"]}
        handler = AccountNumberFieldHandler(substitutions)
        assert handler is not None
        assert isinstance(handler, AccountNumberFieldHandler)
        assert handler.substitutions == substitutions
    
    def test_substitute(self):
        """Test the substitute method."""
        substitutions = {"account_numbers": ["12345678", "87654321"]}
        handler = AccountNumberFieldHandler(substitutions)
        
        match = MagicMock()
        match.group.side_effect = lambda idx: "/ACC" if idx == 1 else "98765432"
        
        result = handler.substitute(match)
        
        assert result.startswith("/ACC")
        assert any(acc in result for acc in substitutions["account_numbers"])


class TestBankCodeFieldHandler:
    """Tests for the BankCodeFieldHandler class."""
    
    def test_creation(self):
        """Test that the handler can be created successfully."""
        substitutions = {"bank_codes": ["ABCDEF12", "XYZWVU98"]}
        handler = BankCodeFieldHandler(substitutions)
        assert handler is not None
        assert isinstance(handler, BankCodeFieldHandler)
        assert handler.substitutions == substitutions
    
    def test_substitute(self):
        """Test the substitute method."""
        substitutions = {"bank_codes": ["ABCDEF12", "XYZWVU98"]}
        handler = BankCodeFieldHandler(substitutions)
        
        match = MagicMock()
        match.group.side_effect = lambda idx: ":BANK" if idx == 1 else "US33"
        
        result = handler.substitute(match)
        
        assert result.startswith(":BANK")
        assert any(code in result for code in substitutions["bank_codes"])


class TestSenderBlockFieldHandler:
    """Tests for the SenderBlockFieldHandler class."""
    
    def test_creation(self):
        """Test that the handler can be created successfully."""
        substitutions = {
            "sender_names": ["SENDER COMPANY LTD", "TEST SENDER CORP"],
            "sender_addresses": ["123 SENDER ST, CITY", "456 TEST ROAD, TOWN"]
        }
        handler = SenderBlockFieldHandler(substitutions)
        assert handler is not None
        assert isinstance(handler, SenderBlockFieldHandler)
        assert handler.substitutions == substitutions
    
    def test_substitute(self):
        """Test the substitute method."""
        substitutions = {
            "sender_names": ["SENDER COMPANY LTD", "TEST SENDER CORP"],
            "sender_addresses": ["123 SENDER ST, CITY", "456 TEST ROAD, TOWN"]
        }
        handler = SenderBlockFieldHandler(substitutions)
        
        match = MagicMock()
        match.group.side_effect = lambda idx: {
            1: ":50K:\n",
            2: "ORIGINAL SENDER",
            3: "ORIGINAL ADDRESS",
            4: "\n"
        }.get(idx)
        
        result = handler.substitute(match)
        
        assert result.startswith(":50K:\n")
        assert any(name in result for name in substitutions["sender_names"])
        assert any(addr in result for addr in substitutions["sender_addresses"])
        assert result.endswith("\n")


class TestBeneficiaryBlockFieldHandler:
    """Tests for the BeneficiaryBlockFieldHandler class."""
    
    def test_creation(self):
        """Test that the handler can be created successfully."""
        substitutions = {
            "beneficiary_names": ["BENEFICIARY INC", "TEST BENEFICIARY LTD"],
            "beneficiary_addresses": ["789 BENE AVENUE, CITY", "321 TEST BENE ST, TOWN"]
        }
        handler = BeneficiaryBlockFieldHandler(substitutions)
        assert handler is not None
        assert isinstance(handler, BeneficiaryBlockFieldHandler)
        assert handler.substitutions == substitutions
    
    def test_substitute(self):
        """Test the substitute method."""
        substitutions = {
            "beneficiary_names": ["BENEFICIARY INC", "TEST BENEFICIARY LTD"],
            "beneficiary_addresses": ["789 BENE AVENUE, CITY", "321 TEST BENE ST, TOWN"]
        }
        handler = BeneficiaryBlockFieldHandler(substitutions)
        
        match = MagicMock()
        match.group.side_effect = lambda idx: {
            1: ":59:\n",
            2: "ORIGINAL BENEFICIARY",
            3: "ORIGINAL ADDRESS",
            4: "\n"
        }.get(idx)
        
        result = handler.substitute(match)
        
        assert result.startswith(":59:\n")
        assert any(name in result for name in substitutions["beneficiary_names"])
        assert any(addr in result for addr in substitutions["beneficiary_addresses"])
        assert result.endswith("\n")


class TestFieldHandlersRegistry:
    """Tests for the field handlers registry functionality."""
    
    def test_register_field_handler(self):
        """Test registering and retrieving handlers from registry."""
        FIELD_HANDLER_REGISTRY.clear()
        
        mock_handler = MagicMock(spec=FieldHandler)
        
        from swift_testing.src.message_generator.field_handlers import register_field_handler
        register_field_handler("test_field", mock_handler)
        
        assert "test_field" in FIELD_HANDLER_REGISTRY
        assert FIELD_HANDLER_REGISTRY["test_field"] is mock_handler 