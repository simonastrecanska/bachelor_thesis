
"""
Configuration Loader Module

This module handles loading and validating configuration from YAML files using PyYAML and Pydantic.
"""

import os
import yaml
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError, validator

logger = logging.getLogger(__name__)

class DatabaseConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    dbname: str
    add_sample_data: bool = False
    pool_size: int = 5
    connection_timeout: int = 30

    @validator("username", pre=True)
    def map_username(cls, v, values, **kwargs):
        if isinstance(v, str):
            return v
        elif "user" in values:
            return values["user"]
        return v

class PathsConfig(BaseModel):
    input_dir: str
    output_dir: str
    log_dir: str
    model_dir: str
    template_dir: str

class MessageGenerationConfig(BaseModel):
    seed: int = 42
    max_variations_per_template: int = 10
    field_substitution_rate: float = 0.3
    perturbation_degree: float = 0.2
    field_patterns: Dict[str, str] = Field(default_factory=dict)
    substitutions: Dict[str, List[str]] = Field(default_factory=dict)

class ModelConfig(BaseModel):
    version: str = "1.0.0"
    prediction_threshold: float = 0.5
    model_type: str = "random_forest"
    model_params: Dict[str, Any] = Field(default_factory=lambda: {"n_estimators": 100, "max_depth": 10, "random_state": 42})
    feature_extraction: Dict[str, Any] = Field(default_factory=lambda: {"vectorizer": "tfidf", "max_features": 1000, "ngram_range": [1, 3]})
    hyperparameter_tuning: Dict[str, Any] = Field(default_factory=dict)

class EvaluationConfig(BaseModel):
    metrics: List[str] = ["accuracy", "precision", "recall", "f1"]
    confusion_matrix: bool = True
    cross_validation: Dict[str, Any] = Field(default_factory=lambda: {"enabled": True, "n_splits": 5})
    output_format: List[str] = ["csv", "json", "plot"]
    plot: Dict[str, Any] = Field(default_factory=lambda: {"dpi": 300, "width": 10, "height": 8, "save_format": "png"})

class ConfigModel(BaseModel):
    database: DatabaseConfig
    paths: PathsConfig
    message_generation: MessageGenerationConfig
    model: ModelConfig
    evaluation: EvaluationConfig

    @validator("database", pre=True)
    def map_database_keys(cls, v):
        if "user" in v and "username" not in v:
            v["username"] = v.pop("user")
        if "name" in v and "dbname" not in v:
            v["dbname"] = v.pop("name")
        return v

def load_config(config_path: str) -> ConfigModel:
    if not os.path.exists(config_path):
        raise Exception(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    try:
        config = ConfigModel(**raw_config)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except ValidationError as e:
        logger.error("Configuration validation error: " + str(e))
        raise
