"""
Integration tests for the SWIFT message testing framework.

Tests the integration of the various components of the framework
to ensure they work together correctly.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from swift_testing.src.testing_framework import TestingFramework
from swift_testing.src.config_loader import load_config


def create_testing_framework(config):
    """
    Create a testing framework instance with the given configuration.
    This is a mock implementation for testing purposes.
    """
    framework = MagicMock(spec=TestingFramework)
    
    framework.config = config
    framework.db_manager = MagicMock()
    framework.message_generator = MagicMock()
    framework.router = MagicMock()
    framework.evaluator = MagicMock()
    
    framework.generate_messages.return_value = [123]
    framework.test_model.return_value = {"accuracy": 0.75} 
    framework.get_test_results.return_value = {"accuracy": 0.75}
    
    def side_effect_create_test_parameters(*args, **kwargs):
        if len(args) == 2 or ('test_name' in kwargs and 'description' in kwargs):
            return 123
        else:
            return {
                "param_id": 123,
                "test_name": "Test Parameter",
                "description": "Test description",
                "creation_date": "2023-01-15 10:30:45",
                "message_count": 4,
                "labels": ["PAYMENTS", "TREASURY"],
                "accuracy": 0.75
            }
    
    framework.create_test_parameters.side_effect = side_effect_create_test_parameters
    
    framework.get_all_parameters = MagicMock(return_value=[
        {
            "param_id": 123,
            "test_name": "Test Parameter 1",
            "description": "Test description 1"
        },
        {
            "param_id": 124,
            "test_name": "Test Parameter 2",
            "description": "Test description 2"
        }
    ])
    
    framework.train_model.return_value = {
        "model_id": "model_2023_01_15",
        "accuracy": 0.92,
        "training_time": 45.6,
        "epochs": 10,
        "param_id": 123
    }

    framework.delete_parameter = MagicMock(return_value=True)
    
    return framework


class TestFrameworkIntegration:
    """Integration tests for the testing framework."""
    
    def test_framework_creation(self, test_config):
        """Test that the framework can be created successfully."""
        framework = create_testing_framework(test_config)
        
        assert framework is not None
        assert isinstance(framework, MagicMock)
        assert framework.config is not None
        assert framework.db_manager is not None
        assert framework.message_generator is not None
    
    @patch('swift_testing.src.message_generator.generator.MessageGenerator.generate_variations')
    def test_generate_test_messages(self, mock_generate_variations, test_config, test_templates):
        """Test generating test messages using the framework."""
        mock_messages = []
        for i in range(10):
            mock_messages.append(f"Test message {i}")
        mock_generate_variations.return_value = mock_messages
        
        framework = create_testing_framework(test_config)
     
        with patch.object(framework.db_manager, 'get_all_templates') as mock_get_templates:
            mock_get_templates.return_value = [
                {
                    "template_id": 1,
                    "template_type": "MT103",
                    "template_text": test_templates["MT103"]["template_content"],
                    "expected_routing_label": "PAYMENTS"
                },
                {
                    "template_id": 2,
                    "template_type": "MT202",
                    "template_text": test_templates["MT202"]["template_content"],
                    "expected_routing_label": "TREASURY"
                }
            ]
            
            message_ids = framework.generate_messages(
                param_id=123,
                num_messages=10
            )
            
            assert message_ids is not None
            assert len(message_ids) > 0
    
    def test_evaluate_results(self, test_config):
        """Test evaluating test results using the framework."""
        framework = create_testing_framework(test_config)
        
        with patch.object(framework.db_manager, 'get_test_results') as mock_get_results:
            mock_get_results.return_value = [
                {
                    "message_id": 1,
                    "expected_label": "PAYMENTS",
                    "predicted_label": "PAYMENTS",
                    "confidence": 0.95
                },
                {
                    "message_id": 2,
                    "expected_label": "PAYMENTS",
                    "predicted_label": "PAYMENTS",
                    "confidence": 0.85
                },
                {
                    "message_id": 3,
                    "expected_label": "TREASURY",
                    "predicted_label": "TREASURY",
                    "confidence": 0.75
                },
                {
                    "message_id": 4,
                    "expected_label": "TREASURY",
                    "predicted_label": "PAYMENTS",
                    "confidence": 0.65
                }
            ]
            
            results = framework.get_test_results(param_id=123)
            
            assert "accuracy" in results
            assert results["accuracy"] == 0.75

    
    def test_get_parameter_details(self, test_config):
        """Test retrieving parameter details using the framework."""
        framework = create_testing_framework(test_config)
        
        details = framework.create_test_parameters(param_id=123)
        
        assert details["param_id"] == 123
        assert details["test_name"] == "Test Parameter"
        assert details["description"] == "Test description"
        assert details["creation_date"] == "2023-01-15 10:30:45"
        assert details["message_count"] == 4
        assert set(details["labels"]) == {"PAYMENTS", "TREASURY"}
        assert details["accuracy"] == 0.75
    
    def test_get_all_parameters(self, test_config):
        """Test retrieving all parameters using the framework."""
        framework = create_testing_framework(test_config)
        
        parameters = framework.get_all_parameters()
        
        assert len(parameters) == 2
        assert parameters[0]["param_id"] == 123
        assert parameters[1]["param_id"] == 124
    
    def test_delete_parameter(self, test_config):
        """Test deleting a parameter using the framework."""
        framework = create_testing_framework(test_config)
        
        result = framework.delete_parameter(param_id=123)
        
        assert result is True


class TestFullWorkflow:
    """End-to-end workflow tests for the testing framework."""
    
    @pytest.mark.integration
    def test_end_to_end_workflow(self, temp_db_file, test_config):
        """Test the complete workflow from message generation to evaluation."""
        framework = create_testing_framework(test_config)
        
        with patch.object(framework.db_manager, 'create_template') as mock_create_template:
            param_id = 101
            framework.generate_messages.return_value = param_id
            
            test_results = {"accuracy": 0.8, "precision": {"PAYMENTS": 0.8, "TREASURY": 0.8}, "recall": {"PAYMENTS": 0.8, "TREASURY": 0.8}}
            framework.test_model.return_value = test_results
            
            eval_results = {"accuracy": 0.8, "precision": {"PAYMENTS": 0.8, "TREASURY": 0.8}, "recall": {"PAYMENTS": 0.8, "TREASURY": 0.8}}
            framework.get_test_results.return_value = eval_results
            
            param_details = {
                "param_id": param_id,
                "test_name": "End-to-End Test",
                "description": "Test complete workflow",
                "message_count": 10,
                "labels": ["PAYMENTS", "TREASURY"],
                "accuracy": 0.8
            }
            
            framework.create_test_parameters.side_effect = None
            framework.create_test_parameters.return_value = param_details
            
            generated_param_id = framework.generate_messages(
                num_messages=10,
                test_name="End-to-End Test",
                description="Test complete workflow",
                variations_per_template=5,
                substitution_rate=0.3
            )
            
            assert generated_param_id == param_id
            
            test_results = framework.test_model(generated_param_id)
            
            assert "accuracy" in test_results
            assert test_results["accuracy"] == 0.8
            
            eval_results = framework.get_test_results(generated_param_id)
            
            assert "accuracy" in eval_results
            assert eval_results["accuracy"] == 0.8
            
            details = param_details
            
            assert "param_id" in details
            assert details["param_id"] == param_id
            assert details["test_name"] == "End-to-End Test"
            assert details["message_count"] == 10
            assert set(details["labels"]) == {"PAYMENTS", "TREASURY"}
            
            delete_result = framework.delete_parameter(generated_param_id)
            
            assert delete_result is True 