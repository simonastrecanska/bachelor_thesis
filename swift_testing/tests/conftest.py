"""
Pytest configuration file for SWIFT testing framework tests.

This file contains fixtures and configuration for running tests across
the SWIFT testing framework.
"""

import os
import sys
import pytest
import logging
import tempfile
import yaml
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from swift_testing.src.database.db_manager import DatabaseManager
from swift_testing.src.message_generator.generator import create_message_generator
from swift_testing.src.message_generator.template_variator import create_template_variator
from swift_testing.src.message_generator.ai_generator import create_ollama_generator, OllamaGenerator
from swift_testing.src.config_loader import load_config, ConfigModel
from swift_testing.src.testing_framework import create_testing_framework

logging.basicConfig(level=logging.WARNING)


@pytest.fixture
def test_config():
    """Return a test configuration."""
    config_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'test_config.yaml')
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    return ConfigModel(**config_dict)


@pytest.fixture
def in_memory_db():
    """Fixture that provides an in-memory SQLite database for testing."""
    # Create in-memory SQLite database
    db_uri = "sqlite:///:memory:"
    db_manager = DatabaseManager(db_uri)
    db_manager.create_tables()
    
    yield db_manager


@pytest.fixture
def temp_db_file():
    """Fixture that provides a temporary SQLite database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_uri = f"sqlite:///{path}"
    db_manager = DatabaseManager(db_uri)
    db_manager.create_tables()
    
    yield db_manager
    
    # Cleanup
    try:
        os.unlink(path)
    except Exception as e:
        print(f"Error cleaning up temp DB file: {e}")


@pytest.fixture
def message_generator(test_config):
    """Fixture that provides a configured message generator."""
    return create_message_generator(test_config.dict())


@pytest.fixture
def template_variator(in_memory_db):
    """Fixture that provides a configured template variator."""
    return create_template_variator(in_memory_db.db_uri)


@pytest.fixture
def testing_framework(test_config):
    """Fixture that provides a testing framework instance."""
    return create_testing_framework(test_config)


@pytest.fixture
def test_templates():
    """Return test templates for SWIFT messages."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'templates')
    templates = {}
    
    # MT103 template
    mt103_path = os.path.join(templates_dir, 'MT103.txt')
    with open(mt103_path, 'r') as f:
        mt103_content = f.read()
    
    templates["MT103"] = {
        "template_path": mt103_path,
        "template_content": mt103_content
    }
    
    # MT202 template
    mt202_path = os.path.join(templates_dir, 'MT202.txt')
    with open(mt202_path, 'r') as f:
        mt202_content = f.read()
    
    templates["MT202"] = {
        "template_path": mt202_path,
        "template_content": mt202_content
    }
    
    return templates


@pytest.fixture
def populate_test_db(in_memory_db, test_templates):
    """Fixture that populates the test database with templates and variator data."""
    for template_type, template_data in test_templates.items():
        in_memory_db.create_template(
            template_type=template_data["template_type"],
            template_content=template_data["template_content"],
            description=f"Test {template_type} template",
            expected_routing_label=template_data["expected_routing_label"]
        )
    
    variator_data = [
        ("currencies", "USD"),
        ("currencies", "EUR"),
        ("currencies", "GBP"),
        ("bank_prefixes", "BANK"),
        ("bank_prefixes", "CORP"),
        ("bank_suffixes", "MAXXX"),
        ("bank_suffixes", "MXXXX"),
        ("first_names", "JOHN"),
        ("first_names", "JANE"),
        ("last_names", "DOE"),
        ("last_names", "SMITH"),
        ("company_prefixes", "ACME"),
        ("company_prefixes", "GLOBAL"),
        ("company_mids", "INDUSTRIES"),
        ("company_mids", "TRADING"),
        ("company_suffixes", "INC"),
        ("company_suffixes", "LTD"),
        ("street_names", "MAIN"),
        ("street_names", "PARK"),
        ("street_types", "STREET"),
        ("street_types", "AVENUE"),
        ("cities", "NEW YORK"),
        ("cities", "LONDON"),
        ("reference_prefixes", "REF"),
        ("reference_prefixes", "INV")
    ]
    
    for data_type, data_value in variator_data:
        in_memory_db.execute_update(
            "INSERT INTO variator_data (data_type, data_value) VALUES (%s, %s)",
            [data_type, data_value]
        )
    
    return in_memory_db


def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers", "integration: mark a test as an integration test"
    ) 