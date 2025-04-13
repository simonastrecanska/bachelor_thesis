"""
Unit tests for the template variator component.

Tests the functionality of the template variator which is responsible
for extracting and applying variations to templates.
"""

import pytest
from unittest.mock import patch, MagicMock

from swift_testing.src.message_generator.template_variator import (
    TemplateVariator, create_template_variator
)

@pytest.fixture
def mock_template_variator():
    """Fixture to patch TemplateVariator methods that access the database."""
    with patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db') as mock_load, \
         patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded') as mock_verify:
        mock_load.return_value = None
        mock_verify.return_value = None
        
        def add_essential_data(instance):
            instance.common_currencies = ["USD", "EUR", "GBP"]
            instance.bank_prefixes = ["BANK", "CORP"]
            instance.bank_suffixes = ["MAXXX", "MXXXX"]
            instance.first_names = ["JOHN", "JANE"]
            instance.last_names = ["DOE", "SMITH"]
            instance.company_prefixes = ["ACME", "GLOBAL"]
            instance.company_mids = ["INDUSTRIES", "TRADING"]
            instance.company_suffixes = ["INC", "LTD"]
            instance.street_names = ["MAIN", "PARK"]
            instance.street_types = ["STREET", "AVENUE"]
            instance.cities = ["NEW YORK", "LONDON"]
            instance.reference_prefixes = ["REF", "INV"]
            
        mock_load.side_effect = add_essential_data
        
        yield


class TestTemplateVariator:
    """Test suite for the TemplateVariator class."""
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    def test_creation(self, mock_verify, mock_load, in_memory_db):
        """Test that the template variator can be created successfully."""
        variator = create_template_variator(in_memory_db.db_uri)
        assert variator is not None
        assert isinstance(variator, TemplateVariator)
        mock_load.assert_called_once()
        mock_verify.assert_called_once()
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_templates')
    def test_get_templates(self, mock_get_templates, mock_verify, mock_load, in_memory_db):
        """Test retrieving templates from the database."""
        mock_templates = [
            {
                "template_id": 1,
                "template_type": "MT103",
                "template_content": "MT103 content",
                "expected_routing_label": "PAYMENTS",
                "description": "MT103 desc"
            },
            {
                "template_id": 2,
                "template_type": "MT202",
                "template_content": "MT202 content",
                "expected_routing_label": "TREASURY",
                "description": "MT202 desc"
            }
        ]
        mock_get_templates.return_value = mock_templates
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        templates = variator.get_templates()
        
        assert len(templates) == 2
        template_types = [t["template_type"] for t in templates]
        assert "MT103" in template_types
        assert "MT202" in template_types
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_template_by_type')
    def test_get_template_by_type(self, mock_get_template, mock_verify, mock_load, in_memory_db):
        """Test retrieving a specific template by type."""
        mock_template = {
            "template_id": 1,
            "template_type": "MT103",
            "template_content": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:210615USD1000,00
:50K:ORDERING CUSTOMER
123 SENDER STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:PAYMENT FOR SERVICES
:71A:SHA
-}""",
            "expected_routing_label": "PAYMENTS",
            "description": "MT103 desc"
        }
        mock_get_template.return_value = mock_template
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        template = variator.get_template_by_type("MT103")
        
        assert template is not None
        assert template["template_type"] == "MT103"
        assert ":20:REFERENCE123" in template["template_content"]
        assert ":50K:ORDERING CUSTOMER" in template["template_content"]
        mock_get_template.assert_called_once_with("MT103")
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_template_by_type')
    def test_get_nonexistent_template(self, mock_get_template, mock_verify, mock_load, in_memory_db):
        """Test attempting to retrieve a template that doesn't exist."""
        mock_get_template.return_value = None
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        template = variator.get_template_by_type("MT999")
        
        assert template is None
        mock_get_template.assert_called_once_with("MT999")
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_variator_data')
    def test_get_variator_data(self, mock_get_data, mock_verify, mock_load, in_memory_db):
        """Test retrieving variator data from the database."""
        mock_get_data.return_value = ["USD", "EUR", "GBP"]
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        currencies = variator.get_variator_data("currencies")
        
        assert len(currencies) == 3
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "GBP" in currencies
        mock_get_data.assert_called_once_with("currencies")
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_variator_data')
    def test_get_nonexistent_variator_data(self, mock_get_data, mock_verify, mock_load, in_memory_db):
        """Test attempting to retrieve variator data that doesn't exist."""
        mock_get_data.return_value = []
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        data = variator.get_variator_data("nonexistent_type")
        
        assert data == []
        mock_get_data.assert_called_once_with("nonexistent_type")
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.create_template')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_template_by_type')
    def test_create_template(self, mock_get_template, mock_create, mock_verify, mock_load, in_memory_db):
        """Test creating a new template."""
        template_id = 3
        mock_create.return_value = template_id
        
        template_type = "MT202COV"
        template_content = """{1:F01BANKABCDAXXX0000000000}{2:I202COVBANKEFGHXXXXN}{4:
:20:REFERENCE789
:21:RELATED456
:32A:210617GBP3000,00
-}"""
        description = "Test MT202COV template"
        expected_routing_label = "TREASURY"
        
        mock_template = {
            "template_id": template_id,
            "template_type": template_type,
            "template_content": template_content,
            "description": description,
            "expected_routing_label": expected_routing_label
        }
        mock_get_template.return_value = mock_template
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        result_id = variator.create_template(
            template_type, template_content, description, expected_routing_label
        )
        
        assert result_id == template_id
        mock_create.assert_called_once_with(template_type, template_content, description, expected_routing_label)
        
        template = variator.get_template_by_type(template_type)
        assert template is not None
        assert template["template_type"] == template_type
        assert template["template_content"] == template_content
        assert template["description"] == description
        assert template["expected_routing_label"] == expected_routing_label
        mock_get_template.assert_called_once_with(template_type)
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.update_template')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_template_by_type')
    def test_update_template(self, mock_get_template, mock_update, mock_verify, mock_load, in_memory_db):
        """Test updating an existing template."""
        template_id = 1
        initial_template = {
            "template_id": template_id,
            "template_type": "MT103",
            "template_content": "Initial content",
            "description": "Initial description",
            "expected_routing_label": "PAYMENTS"
        }
        mock_get_template.return_value = initial_template
        
        updated_content = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{3:{108:UPDATED}}{4:
:20:NEWREFERENCE
:23B:CRED
:32A:210615USD1000,00
:50K:UPDATED CUSTOMER
123 SENDER STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:UPDATED PAYMENT DETAILS
:71A:SHA
-}"""
        updated_description = "Updated MT103 template"
        
        updated_template = {
            "template_id": template_id,
            "template_type": "MT103",
            "template_content": updated_content,
            "description": updated_description,
            "expected_routing_label": "PAYMENTS"
        }
        
        mock_get_template.side_effect = [initial_template, updated_template]
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        template = variator.get_template_by_type("MT103")
        template_id = template["template_id"]
        
        variator.update_template(
            template_id, "MT103", updated_content, updated_description, "PAYMENTS"
        )
        mock_update.assert_called_once_with(template_id, "MT103", updated_content, updated_description, "PAYMENTS")
        
        updated_template = variator.get_template_by_type("MT103")
        
        assert updated_template["template_content"] == updated_content
        assert updated_template["description"] == updated_description
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.delete_template')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_template_by_type')
    def test_delete_template(self, mock_get_template, mock_delete, mock_verify, mock_load, in_memory_db):
        """Test deleting a template."""
        template_id = 2
        initial_template = {
            "template_id": template_id,
            "template_type": "MT202",
            "template_content": "MT202 content",
            "description": "MT202 description",
            "expected_routing_label": "TREASURY"
        }
        mock_get_template.side_effect = [initial_template, None]
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        template = variator.get_template_by_type("MT202")
        template_id = template["template_id"]
        
        variator.delete_template(template_id)
        mock_delete.assert_called_once_with(template_id)
        
        deleted_template = variator.get_template_by_type("MT202")
        
        assert deleted_template is None
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.delete_variator_data')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_variator_data')
    def test_delete_variator_data(self, mock_get_data, mock_delete_data, mock_verify, mock_load, in_memory_db):
        """Test deleting variator data."""
        mock_get_data.side_effect = [
            [
                {"data_type": "currencies", "data_value": "USD"},
                {"data_type": "currencies", "data_value": "EUR"},
                {"data_type": "currencies", "data_value": "GBP"}
            ],
            [
                {"data_type": "currencies", "data_value": "EUR"},
                {"data_type": "currencies", "data_value": "GBP"}
            ]
        ]
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        currencies = variator.get_variator_data("currencies")
        assert any(item["data_value"] == "USD" for item in currencies)
        
        variator.delete_variator_data("currencies", "USD")
        mock_delete_data.assert_called_once_with("currencies", "USD")
        
        updated_currencies = variator.get_variator_data("currencies")
        
        assert not any(item["data_value"] == "USD" for item in updated_currencies)
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.database.db_manager.DatabaseManager.execute_query')
    def test_database_error_handling(self, mock_execute, mock_verify, mock_load, in_memory_db):
        """Test that the variator handles database errors gracefully."""
        mock_execute.side_effect = Exception("Database error")
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        assert variator is not None
        assert isinstance(variator, TemplateVariator)
        mock_load.assert_called_once()


class TestTemplateVariatorIntegration:
    """Integration tests for the TemplateVariator that require a proper database setup."""
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_templates')
    def test_get_all_templates(self, mock_get_templates, mock_verify, mock_load, in_memory_db):
        """Test retrieving all templates from the database."""
        mock_templates = [
            {
                "template_id": 1,
                "template_type": "MT103",
                "template_content": "MT103 content",
                "expected_routing_label": "PAYMENTS",
                "description": "MT103 desc"
            },
            {
                "template_id": 2,
                "template_type": "MT202",
                "template_content": "MT202 content",
                "expected_routing_label": "TREASURY",
                "description": "MT202 desc"
            }
        ]
        mock_get_templates.return_value = mock_templates
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        templates = variator.get_templates()
        
        assert len(templates) >= 2
        
        template_types = [t["template_type"] for t in templates]
        assert "MT103" in template_types
        assert "MT202" in template_types
        
        for template in templates:
            assert "template_content" in template
            assert "expected_routing_label" in template
            assert template["template_content"] is not None
            assert template["expected_routing_label"] in ["PAYMENTS", "TREASURY"]
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.create_template')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_templates')
    def test_create_and_retrieve_template(self, mock_get_templates, mock_create, mock_verify, mock_load, in_memory_db):
        """Test creating and then retrieving a template."""
        template_id = 4
        mock_create.return_value = template_id
        
        template_type = "MT760"
        template_content = """{1:F01BANKABCDAXXX0000000000}{2:I760BANKEFGHXXXXN}{4:
:20:REFERENCE123
:77C:GUARANTEE DETAILS
-}"""
        description = "Test MT760 template"
        expected_routing_label = "TRADE"
        
        mock_templates = [{
            "template_id": template_id,
            "template_type": template_type,
            "template_content": template_content,
            "description": description,
            "expected_routing_label": expected_routing_label
        }]
        mock_get_templates.return_value = mock_templates
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        created_id = variator.create_template(
            template_type, 
            template_content,
            description,
            expected_routing_label
        )
        
        templates = variator.get_templates()
        
        assert len(templates) == 1
        assert templates[0]["template_id"] == template_id
        assert templates[0]["template_type"] == template_type
    
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._load_variator_data_from_db')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator._verify_data_loaded')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.add_variator_data')
    @patch('swift_testing.src.message_generator.template_variator.TemplateVariator.get_variator_data')
    def test_add_and_retrieve_variator_data(self, mock_get_data, mock_add_data, mock_verify, mock_load, in_memory_db):
        """Test adding and then retrieving variator data."""
        mock_get_data.side_effect = lambda data_type: {
            "product_codes": [
                {"data_type": "product_codes", "data_value": "PROD001"},
                {"data_type": "product_codes", "data_value": "PROD002"}
            ],
            "product_names": [
                {"data_type": "product_names", "data_value": "Product 1"},
                {"data_type": "product_names", "data_value": "Product 2"}
            ]
        }.get(data_type, [])
        
        variator = create_template_variator(in_memory_db.db_uri)
        
        variator.add_variator_data("product_codes", "PROD001")
        variator.add_variator_data("product_codes", "PROD002")
        variator.add_variator_data("product_names", "Product 1")
        variator.add_variator_data("product_names", "Product 2")
        
        assert mock_add_data.call_count == 4
        
        product_codes = variator.get_variator_data("product_codes")
        product_names = variator.get_variator_data("product_names")
        
        assert len(product_codes) == 2
        assert any(item["data_value"] == "PROD001" for item in product_codes)
        assert any(item["data_value"] == "PROD002" for item in product_codes)
        
        assert len(product_names) == 2
        assert any(item["data_value"] == "Product 1" for item in product_names)
        assert any(item["data_value"] == "Product 2" for item in product_names) 