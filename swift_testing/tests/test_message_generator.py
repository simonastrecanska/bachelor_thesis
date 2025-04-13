"""
Integration tests for the message generator component.

Tests the functionality of generating variations of SWIFT messages.
"""

import pytest
import os
from pathlib import Path

import unittest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.message_generator.generator import MessageGenerator, create_message_generator


class TestMessageGenerator(unittest.TestCase):
    """Tests for the MessageGenerator class."""
    
    def setUp(self):
        """Set up the test case."""
        self.config = {
            'message_generation': {
                'perturbation_degree': 0.2,
                'seed': 42,
                'max_variations_per_template': 5,
                'field_substitution_rate': 0.3
            }
        }
        self.generator = create_message_generator(self.config)
        
        self.template = """
        :20:REFERENCE123
        :23B:CRED
        :32A:220610USD1000,00
        :50K:/123456789
        ACME CORP
        123 MAIN ST
        :59:/987654321
        JOHN DOE
        456 OAK AVE
        :71A:SHA
        """
    
    def test_initialization(self):
        """Test if the generator initializes correctly."""
        self.assertEqual(self.generator.perturbation_degree, 0.2)
        self.assertEqual(self.generator.seed, 42)
        self.assertEqual(self.generator.max_variations, 5)
        self.assertEqual(self.generator.field_substitution_rate, 0.3)
    
    def test_generate_message(self):
        """Test message generation."""
        message = self.generator.generate_message(self.template)
        
        self.assertTrue(message)
        
        self.assertIsInstance(message, str)
        
        self.assertNotEqual(message, self.template)
    
    def test_generate_variations(self):
        """Test generating multiple variations."""
        variations = self.generator.generate_variations(self.template, 3)
        
        self.assertEqual(len(variations), 3)
        
        self.assertNotEqual(variations[0], variations[1])
        self.assertNotEqual(variations[0], variations[2])
        self.assertNotEqual(variations[1], variations[2])
    
    def test_parse_template(self):
        """Test template parsing."""
        parsed = self.generator.parse_template(self.template)
        
        self.assertIn('reference', parsed)
        
        reference_matches = [match[0] for match in parsed.get('reference', [])]
        self.assertIn('REFERENCE123', reference_matches)
    
    def test_field_modification(self):
        """Test field modification."""
        original_reference = "REFERENCE123"
        modified_reference = self.generator.modify_field('reference', original_reference)
        
        self.assertNotEqual(modified_reference, original_reference)
        self.assertIsInstance(modified_reference, str)


if __name__ == '__main__':
    unittest.main() 