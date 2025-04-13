"""
Fixtures for database tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from swift_testing.src.database.db_manager import DatabaseManager
from swift_testing.src.database.models import Base


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    
    Base.metadata.create_all(db_manager.engine)
    
    yield db_manager
    
    Base.metadata.drop_all(db_manager.engine) 