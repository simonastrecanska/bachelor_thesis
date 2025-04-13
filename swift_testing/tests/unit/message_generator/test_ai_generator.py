"""
Unit tests for the AI-based message generator component.

Tests the functionality of the AI generator that uses Ollama
for generating SWIFT messages.
"""

import pytest
from unittest.mock import patch, MagicMock

from swift_testing.src.message_generator.ai_generator import (
    OllamaGenerator, create_ollama_generator
)


class TestOllamaMessageGenerator:
    """Test suite for the OllamaMessageGenerator class."""
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_creation(self, mock_post):
        """Test that the Ollama generator can be created successfully."""
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        assert generator is not None
        assert isinstance(generator, OllamaGenerator)
        assert generator.model_name == "llama2"
        assert generator.temperature == 0.7
        
        mock_post.assert_not_called()
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_generate_message(self, mock_post):
        """Test generating a single message."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:AITEST123
:23B:CRED
:32A:210615USD1000,00
:50K:AI GENERATED CUSTOMER
123 AI STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:PAYMENT FOR AI SERVICES
:71A:SHA
-}"""
        }
        mock_post.return_value = mock_response
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        template = "MT103 SWIFT message template"
        message = generator.generate_variation(template)
        
        assert message is not None
        assert "{1:F01BANKDEFMAXXX0000000000}" in message
        assert ":20:AITEST123" in message
        assert ":50K:AI GENERATED CUSTOMER" in message
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "llama2"
        assert "MT103 SWIFT message template" in kwargs["json"]["prompt"]
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_generate_messages_batch(self, mock_post):
        """Test generating a batch of messages."""
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:AITEST123
:23B:CRED
:32A:210615USD1000,00
:50K:AI GENERATED CUSTOMER
123 AI STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:PAYMENT FOR AI SERVICES
:71A:SHA
-}"""
        }
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I202BANKABCMXXXXN}{4:
:20:AITEST456
:21:RELATED123
:32A:210616EUR5000,00
:52A:ORDERING INSTITUTION
:58A:BENEFICIARY INSTITUTION
:72:/BNF/AI PAYMENT DETAILS
-}"""
        }
        
        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:AITEST789
:23B:CRED
:32A:210617GBP3000,00
:50K:ANOTHER AI CUSTOMER
456 AI AVENUE
:59:ANOTHER BENEFICIARY
789 BENEFICIARY ROAD
:70:ANOTHER AI PAYMENT
:71A:SHA
-}"""
        }
        
        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        templates = ["MT103 template", "MT202 template", "MT103 template"]
        messages = []
        for template in templates:
            messages.append(generator.generate_variation(template))
        
        assert len(messages) == 3
        
        assert ":20:AITEST123" in messages[0]
        assert ":20:AITEST456" in messages[1]
        assert ":20:AITEST789" in messages[2]
        
        assert mock_post.call_count == 3
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_error_handling(self, mock_post):
        """Test handling of errors during message generation."""
        mock_post.side_effect = Exception("API error")
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        template = "MT103 template"
        message = generator.generate_variation(template)
        
        assert message == template
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_invalid_response_handling(self, mock_post):
        """Test handling of invalid responses from the API."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        template = "MT103 template"
        message = generator.generate_variation(template)
        
        assert message == template
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_different_message_types(self, mock_post):
        """Test generating messages of different types."""
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:AITEST103
:23B:CRED
:32A:210615USD1000,00
:50K:MT103 CUSTOMER
123 SENDER STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:MT103 PAYMENT
:71A:SHA
-}"""
        }
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I202BANKABCMXXXXN}{4:
:20:AITEST202
:21:RELATED123
:32A:210616EUR5000,00
:52A:MT202 INSTITUTION
:58A:MT202 BENEFICIARY
:72:/BNF/MT202 DETAILS
-}"""
        }
        
        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I760BANKABCMXXXXN}{4:
:20:AITEST760
:27:1/1
:31C:210617
:77C:GUARANTEE DETAILS
MT760 SPECIFIC CONTENT
-}"""
        }
        
        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        mt103 = generator.generate_variation("MT103 template")
        mt202 = generator.generate_variation("MT202 template")
        mt760 = generator.generate_variation("MT760 template")
        
        assert ":20:AITEST103" in mt103
        assert ":23B:CRED" in mt103
        
        assert ":20:AITEST202" in mt202
        assert ":21:RELATED123" in mt202
        
        assert ":20:AITEST760" in mt760
        assert ":77C:GUARANTEE DETAILS" in mt760
    

class TestOllamaMessageGeneratorIntegration:
    """Integration tests for the OllamaMessageGenerator with real templates."""
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_full_generation_workflow(self, mock_post):
        """Test the full workflow of template loading and message generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:AITEST103
:23B:CRED
:32A:210615USD1000,00
:50K:MT103 CUSTOMER
123 SENDER STREET
:59:BENEFICIARY CUSTOMER
456 BENEFICIARY STREET
:70:MT103 PAYMENT
:71A:SHA
-}"""
        }
        mock_post.return_value = mock_response
        
        template = """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
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
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7
        )
        
        generated = generator.generate_variation(template)
        
        assert generated is not None
        assert ":20:AITEST103" in generated
        assert ":23B:CRED" in generated
        assert ":50K:MT103 CUSTOMER" in generated
    
    @patch('swift_testing.src.message_generator.ai_generator.requests.post')
    def test_custom_prompt(self, mock_post):
        """Test using a custom system prompt for generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": """{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:CUSTOM123
:23B:CRED
:32A:210615USD1000,00
:50K:CUSTOM CUSTOMER
123 CUSTOM STREET
:59:CUSTOM BENEFICIARY
456 CUSTOM STREET
:70:CUSTOM PAYMENT
:71A:SHA
-}"""
        }
        mock_post.return_value = mock_response
        
        custom_prompt = "You are a SWIFT message generator that creates test messages with 'CUSTOM' in all fields."
        
        generator = create_ollama_generator(
            model_name="llama2",
            temperature=0.7,
            system_prompt=custom_prompt
        )
        
        template = "MT103 template"
        message = generator.generate_variation(template)
        
        assert message is not None
        assert "CUSTOM" in message
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["system"] == custom_prompt 