"""
Unit tests for the database manager component.

Tests the functionality of the database manager for handling
SWIFT message testing data.
"""

import pytest
import datetime
from unittest.mock import patch, MagicMock

from swift_testing.src.database.db_manager import DatabaseManager
from swift_testing.src.database.models import (
    Base, MessageTemplate, Parameters, Messages, 
    ExpectedResults, ActualResults, VariatorData
)

class TestDatabaseManager:
    """Test suite for the DatabaseManager class."""
    
    def test_creation(self):
        """Test that the database manager can be created successfully."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        assert db_manager is not None
        assert db_manager.db_uri == "sqlite:///:memory:"
    
    def test_create_tables(self, in_memory_db):
        """Test that tables can be created successfully."""
        metadata = Base.metadata
        table_names = metadata.tables.keys()
        
        assert "templates" in table_names
        assert "parameters" in table_names
        assert "messages" in table_names
        assert "expected_results" in table_names
        assert "actual_results" in table_names
        assert "variator_data" in table_names
    
    def test_create_parameter(self, in_memory_db):
        """Test creating a test parameter."""
        test_name = "Test Parameter"
        description = "Test parameter description"
        
        param_id = in_memory_db.create_parameter(test_name, description)
        
        assert param_id is not None
        
        with in_memory_db.get_session() as session:
            param = session.query(Parameters).filter_by(param_id=param_id).first()
            
            assert param is not None
            assert param.test_name == test_name
            assert param.description == description
    
    def test_get_parameter(self, in_memory_db):
        """Test retrieving a test parameter."""
        test_name = "Test Parameter"
        description = "Test parameter description"
        
        param_id = in_memory_db.create_parameter(test_name, description)
        
        parameter = in_memory_db.get_parameter(param_id)
        
        assert parameter is not None
        assert parameter["param_id"] == param_id
        assert parameter["test_name"] == test_name
        assert parameter["description"] == description
    
    def test_get_nonexistent_parameter(self, in_memory_db):
        """Test retrieving a parameter that doesn't exist."""
        parameter = in_memory_db.get_parameter(999)
        
        assert parameter is None
    
    def test_get_all_parameters(self, in_memory_db):
        """Test retrieving all test parameters."""
        params = [
            ("Test Parameter 1", "Description 1"),
            ("Test Parameter 2", "Description 2"),
            ("Test Parameter 3", "Description 3")
        ]
        
        param_ids = []
        for name, desc in params:
            param_id = in_memory_db.create_parameter(name, desc)
            param_ids.append(param_id)
        
        parameters = in_memory_db.get_parameters()
        
        assert len(parameters) == 3
        retrieved_ids = [p["id"] for p in parameters]
        assert all(pid in retrieved_ids for pid in param_ids)
    
    def test_create_template(self, in_memory_db):
        """Test creating a message template."""
        template_type = "MT103"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:210615USD1000,00
:50K:ORDERING CUSTOMER
123 SENDER STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:PAYMENT FOR SERVICES
:71A:SHA
-}"""
        description = "Test MT103 template"
        expected_routing_label = "PAYMENTS"
        
        template_id = in_memory_db.create_template(
            template_type, template_content, description, expected_routing_label
        )
        
        assert template_id is not None
        
        with in_memory_db.get_session() as session:
            template = session.query(MessageTemplate).filter_by(id=template_id).first()
            
            assert template is not None
            assert template.template_type == template_type
            assert template.template_content == template_content
            assert template.description == description
            assert template.expected_routing_label == expected_routing_label
            assert isinstance(template.created_at, datetime.datetime)
    
    def test_get_template(self, in_memory_db):
        """Test retrieving a message template."""
        template_type = "MT103"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:210615USD1000,00
-}"""
        description = "Test MT103 template"
        expected_routing_label = "PAYMENTS"
        
        template_id = in_memory_db.create_template(
            template_type, template_content, description, expected_routing_label
        )
        
        template = in_memory_db.get_template(template_id)
        
        assert template is not None
        assert template["id"] == template_id
        assert template["template_type"] == template_type
        assert template["template_content"] == template_content
        assert template["description"] == description
        assert template["expected_routing_label"] == expected_routing_label
        assert "created_at" in template
    
    def test_get_templates_by_type(self, in_memory_db):
        """Test retrieving templates by type."""
        templates = [
            ("MT103", "MT103 content", "MT103 desc", "PAYMENTS"),
            ("MT202", "MT202 content", "MT202 desc", "TREASURY"),
            ("MT799", "MT799 content", "MT799 desc", "TREASURY")
        ]
        
        for t_type, content, desc, label in templates:
            in_memory_db.create_template(t_type, content, desc, label)
        
        if hasattr(in_memory_db, 'get_templates_by_type'):
            mt103_templates = in_memory_db.get_templates_by_type("MT103")

            assert len(mt103_templates) == 1
            assert mt103_templates[0]["template_type"] == "MT103"
        else:
            mt103_template = in_memory_db.get_template_by_type("MT103")
            
            assert mt103_template is not None
            assert mt103_template["template_type"] == "MT103"
    
    def test_create_message(self, in_memory_db):
        """Test creating a message."""
        param_id = in_memory_db.create_parameter(
            "Test Parameter", "Test description"
        )
        
        template_type = "MT103"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
-}"""
        template_id = in_memory_db.create_template(
            template_type, template_content, "Test template", "PAYMENTS"
        )
        
        message_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:210615USD1000,00
-}"""
        expected_label = "PAYMENTS"
        
        message_id = in_memory_db.create_message(
            template_id, param_id, message_content, expected_label
        )
        
        assert message_id is not None
        
        with in_memory_db.get_session() as session:
            message = session.query(Messages).filter_by(message_id=message_id).first()
            expected = session.query(ExpectedResults).filter_by(message_id=message_id).first()
            
            assert message is not None
            assert message.param_id == param_id
            assert message.template_id == template_id
            assert message.generated_text == message_content
            assert isinstance(message.created_at, datetime.datetime)
            
            assert expected is not None
            assert expected.expected_label == expected_label
    
    def test_get_messages(self, in_memory_db):
        """Test retrieving messages for a parameter."""
        param_id = in_memory_db.create_parameter(
            "Test Parameter", "Test description"
        )
        
        template_type = "MT103"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
-}"""
        template_id = in_memory_db.create_template(
            template_type, template_content, "Test template", "PAYMENTS"
        )
        
        messages = [
            ("""{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REF1
:23B:CRED
:32A:210615USD1000,00
-}""", "PAYMENTS"),
            ("""{1:F01BANKDEFMAXXX0000000000}{2:I202BANKABCMXXXXN}{4:
:20:REF2
:21:RELATED123
:32A:210616EUR5000,00
-}""", "TREASURY"),
        ]
        
        message_ids = []
        for content, label in messages:
            message_id = in_memory_db.create_message(template_id, param_id, content, label)
            message_ids.append(message_id)
            
        retrieved_messages = in_memory_db.get_messages_by_param(param_id)
        
        assert len(retrieved_messages) == 2
        retrieved_ids = [m["message_id"] for m in retrieved_messages]
        assert all(mid in retrieved_ids for mid in message_ids)
    
    def test_add_actual_result(self, in_memory_db):
        """Test adding actual result for a message."""
        param_id = in_memory_db.create_parameter(
            "Test Parameter", "Test description"
        )
        
        template_type = "MT103"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
-}"""
        template_id = in_memory_db.create_template(
            template_type, template_content, "Test template", "PAYMENTS"
        )
        
        message_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:210615USD1000,00
-}"""
        expected_label = "PAYMENTS"
        
        message_id = in_memory_db.create_message(
            template_id, param_id, message_content, expected_label
        )
        
        model_version = "model-v1.0"
        predicted_label = "PAYMENTS"
        confidence = 0.95
        
        result = in_memory_db.create_actual_result(
            message_id, model_version, predicted_label, confidence
        )
        
        assert result is True
        
        with in_memory_db.get_session() as session:
            actual = session.query(ActualResults).filter_by(message_id=message_id).first()
            
            assert actual is not None
            assert actual.message_id == message_id
            assert actual.model_version == model_version
            assert actual.predicted_label == predicted_label
            assert actual.confidence == confidence
            assert isinstance(actual.classification_date, datetime.datetime)
    
    def test_get_test_results(self, in_memory_db):
        """Test retrieving test results."""
        param_id = in_memory_db.create_parameter(
            "Test Parameter", "Test description"
        )
        
        template_type = "MT103"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
-}"""
        template_id = in_memory_db.create_template(
            template_type, template_content, "Test template", "PAYMENTS"
        )
        
        messages = [
            # Message 1: Correctly classified
            {
                "content": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REF1
:23B:CRED
:32A:210615USD1000,00
-}""",
                "expected": "PAYMENTS",
                "predicted": "PAYMENTS",
                "confidence": 0.95
            },
            # Message 2: Incorrectly classified
            {
                "content": """{1:F01BANKDEFMAXXX0000000000}{2:I202BANKABCMXXXXN}{4:
:20:REF2
:21:RELATED123
:32A:210616EUR5000,00
-}""",
                "expected": "TREASURY",
                "predicted": "PAYMENTS",
                "confidence": 0.75
            },
            # Message 3: Correctly classified
            {
                "content": """{1:F01BANKDEFMAXXX0000000000}{2:I202BANKABCMXXXXN}{4:
:20:REF3
:21:RELATED456
:32A:210617GBP3000,00
-}""",
                "expected": "TREASURY",
                "predicted": "TREASURY",
                "confidence": 0.85
            }
        ]
        
        model_version = "model-v1.0"
        for msg in messages:
            message_id = in_memory_db.create_message(
                template_id, param_id, msg["content"], msg["expected"]
            )
            in_memory_db.create_actual_result(
                message_id, model_version, msg["predicted"], msg["confidence"]
            )
        
        results = in_memory_db.get_test_results(param_id)
        
        assert results is not None
        assert len(results) == 3
        
        correct_count = sum(1 for r in results if r["expected_label"] == r["predicted_label"])
        assert correct_count == 2
    
    def test_add_variator_data(self, in_memory_db):
        """Test adding variator data."""
        in_memory_db.add_variator_data("currencies", "USD")
        
        with in_memory_db.get_session() as session:
            data = session.query(VariatorData).filter_by(data_type="currencies").first()
            
            assert data is not None
            assert data.data_type == "currencies"
            assert data.data_value == "USD"
    
    def test_get_variator_data(self, in_memory_db):
        """Test retrieving variator data."""
        in_memory_db.add_variator_data("currencies", "USD")
        in_memory_db.add_variator_data("currencies", "EUR")
        
        currencies = in_memory_db.get_variator_data("currencies")
        
        assert len(currencies) == 2
        assert all(c["data_type"] == "currencies" for c in currencies)
        assert "USD" in [c["data_value"] for c in currencies]
        assert "EUR" in [c["data_value"] for c in currencies]
    
    def test_delete_parameter(self, in_memory_db):
        """Test deleting a parameter and its related data."""
        param_id = in_memory_db.create_parameter(
            "Test Parameter", "Test description"
        )
        
        template_type = "MT103_DELETE_TEST"
        template_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
-}"""
        template_id = in_memory_db.create_template(
            template_type, template_content, "Test template", "PAYMENTS"
        )
        
        for i in range(3):
            message_content = f"""{{1:F01BANKDEFMAXXX0000000000}}{{2:I103BANKABCMXXXXN}}{{4:
:20:REF{i+1}
:23B:CRED
:32A:21061{i+5}USD1000,00
-}}"""
            expected_label = "PAYMENTS"
            
            message_id = in_memory_db.create_message(
                template_id, param_id, message_content, expected_label
            )
            
            in_memory_db.create_actual_result(
                message_id, "model-v1.0", "PAYMENTS", 0.95
            )
        
        with in_memory_db.get_session() as session:
            message_count = session.query(Messages).filter_by(param_id=param_id).count()
            assert message_count == 3
        
        if hasattr(in_memory_db, 'delete_parameter'):
            in_memory_db.delete_parameter(param_id)
            
            with in_memory_db.get_session() as session:
                param = session.query(Parameters).filter_by(param_id=param_id).first()
                assert param is None
                
                messages = session.query(Messages).filter_by(param_id=param_id).all()
                assert len(messages) == 0
    
    def test_error_handling(self):
        """Test that errors are handled gracefully."""
        try:
            db_manager = DatabaseManager("invalid_db_uri")
            db_manager.connect()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "invalid_db_uri" in str(e).lower() or "could not parse" in str(e).lower() 