"""
Unit tests for the MessageGenerator component.

Tests the functionality of generating variations of SWIFT message templates.
"""

import pytest
from unittest.mock import patch, MagicMock
import re

from swift_testing.src.message_generator.generator import (
    MessageGenerator, create_message_generator
)
from swift_testing.src.message_generator.field_handlers import ReferenceFieldHandler


class TestMessageGenerator:
    """Test suite for the MessageGenerator class."""
    
    def test_creation(self, test_config):
        """Test that the message generator can be created successfully."""
        generator = create_message_generator(test_config.model_dump())
        assert isinstance(generator, MessageGenerator)
        
    def test_generate_variations(self, test_config, test_templates):
        """Test that the generator produces variations of a template."""
        generator = create_message_generator(test_config.model_dump())
        
        template = test_templates["MT103"]["template_content"]
        variations = generator.generate_variations(template, 3)
        
        assert len(variations) == 3
        
        assert all(v != template for v in variations)
    
    def test_substitution_applied(self, test_config, test_templates):
        """Test that field substitutions are applied in the generated variations."""
        generator = create_message_generator(test_config.model_dump())
        
        template = test_templates["MT103"]["template_content"]
        variations = generator.generate_variations(template, 1)
        
        assert len(variations) > 0
        
        original_ref = re.search(r':20:([A-Z0-9]+)', template)
        variation_ref = re.search(r':20:([A-Z0-9]+)', variations[0])
        
        if original_ref and variation_ref:
            assert variation_ref.group(1)
    
    def test_preserve_message_structure(self, test_config, test_templates):
        """Test that message structure is preserved in variations."""
        generator = create_message_generator(test_config.model_dump())
        
        template = test_templates["MT103"]["template_content"]
        variations = generator.generate_variations(template, 1)
        
        assert len(variations) > 0
        
        assert "{1:" in variations[0]  # Header block
        assert "{4:" in variations[0]  # Text block
        assert "-}" in variations[0]   # Trailer
    
    @patch('swift_testing.src.message_generator.field_handlers.ReferenceFieldHandler.substitute')
    def test_handler_called(self, mock_substitute, test_config, test_templates):
        """Test that the appropriate field handlers are called."""
        generator = create_message_generator(test_config.model_dump())
        template = test_templates["MT103"]["template_content"]
        
        generator.generate_variations(template, 1)
        
    def test_error_handling(self, test_config):
        """Test that the generator handles errors gracefully."""
        generator = create_message_generator(test_config.model_dump())
        
        invalid_template = "This is not a valid SWIFT message"
        variations = generator.generate_variations(invalid_template, 2)
        
        assert len(variations) == 2
    
    def test_substitution_rate(self, test_config, test_templates):
        """Test that the substitution rate parameter affects the number of substitutions."""
        config_low = test_config.model_dump()
        config_low["message_generation"]["field_substitution_rate"] = 0.1
        
        config_high = test_config.model_dump()
        config_high["message_generation"]["field_substitution_rate"] = 0.9
        
        generator_low = create_message_generator(config_low)
        generator_high = create_message_generator(config_high)
        
        template = test_templates["MT103"]["template_content"]
        
        variations_low = generator_low.generate_variations(template, 5)
        variations_high = generator_high.generate_variations(template, 5)
        
        assert len(variations_low) == 5
        assert len(variations_high) == 5


class TestMessageGeneratorIntegration:
    """Integration tests for the MessageGenerator with real templates."""
    
    def test_generate_multiple_templates(self, test_config, test_templates):
        """Test generating variations for multiple template types."""
        generator = create_message_generator(test_config.model_dump())
        
        mt103_template = test_templates["MT103"]["template_content"]
        mt202_template = test_templates["MT202"]["template_content"]
        
        mt103_variations = generator.generate_variations(mt103_template, 3)
        mt202_variations = generator.generate_variations(mt202_template, 3)
        
        assert len(mt103_variations) == 3
        assert len(mt202_variations) == 3
        
        assert all(":23B:" in v for v in mt103_variations)
        assert all(":21:" in v for v in mt202_variations)
    
    def test_process_message_batch(self, test_config, test_templates):
        """Test processing a batch of messages."""
        generator = create_message_generator(test_config.model_dump())
        
        templates = [
            test_templates["MT103"]["template_content"],
            test_templates["MT202"]["template_content"]
        ]
        
        variations = []
        for template in templates:
            variations.extend(generator.generate_variations(template, 2))
        
        assert len(variations) == 4
        
        mt103_vars = [v for v in variations if ":23B:" in v]
        mt202_vars = [v for v in variations if ":21:" in v]
        
        assert len(mt103_vars) == 2
        assert len(mt202_vars) == 2 