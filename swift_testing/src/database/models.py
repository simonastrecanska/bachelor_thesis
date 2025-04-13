"""
Database models for the SWIFT testing framework.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()

class Parameters(Base):
    """Test parameters table."""
    __tablename__ = 'parameters'
    
    param_id = Column(Integer, primary_key=True)
    test_name = Column(String(100))
    description = Column(String(255))
    
    def __repr__(self):
        return f"<Parameters(param_id={self.param_id}, test_name='{self.test_name}')>"


class MessageTemplate(Base):
    """
    Models a SWIFT message template, which provides the base structure for generating SWIFT messages.
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    template_type = Column(String, unique=True, nullable=False)
    template_content = Column(Text, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    expected_routing_label = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, template_type='{self.template_type}')>"


class Messages(Base):
    """Generated messages table."""
    __tablename__ = 'messages'
    
    message_id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    param_id = Column(Integer, ForeignKey('parameters.param_id'))
    generated_text = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    template = relationship("MessageTemplate")
    parameters = relationship("Parameters")
    
    def __repr__(self):
        return f"<Messages(message_id={self.message_id}, template_id={self.template_id})>"


class ExpectedResults(Base):
    """Expected results table."""
    __tablename__ = 'expected_results'
    
    message_id = Column(Integer, ForeignKey('messages.message_id'), primary_key=True)
    expected_label = Column(String(100))
    
    message = relationship("Messages")
    
    def __repr__(self):
        return f"<ExpectedResults(message_id={self.message_id}, expected_label='{self.expected_label}')>"


class ActualResults(Base):
    """Model predictions table."""
    __tablename__ = 'actual_results'
    
    message_id = Column(Integer, ForeignKey('messages.message_id'), primary_key=True)
    model_version = Column(String(50))
    predicted_label = Column(String(100))
    confidence = Column(Float)
    classification_date = Column(DateTime, default=func.now())
    
    message = relationship("Messages")
    
    def __repr__(self):
        return f"<ActualResults(message_id={self.message_id}, model_version='{self.model_version}', predicted_label='{self.predicted_label}')>"


class VariatorData(Base):
    """Variator data table."""
    __tablename__ = 'variator_data'
    
    id = Column(Integer, primary_key=True)
    data_type = Column(String(100))
    data_value = Column(String(255))
    
    def __repr__(self):
        return f"<VariatorData(id={self.id}, data_type='{self.data_type}', data_value='{self.data_value}')>" 