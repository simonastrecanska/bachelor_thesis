"""
SWIFT Message Routing Testing Framework

This module integrates all components of the testing framework and provides
the main functionality for running tests on SWIFT message routing models.
It covers configuration management, database operations, message generation,
model testing, and result evaluation.
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import pytest

from src.config_loader import load_config

from src.database.db_manager import create_database_manager

from src.message_generator.generator import create_message_generator

from src.models.routing_model import create_router, load_router

from src.evaluation.evaluator import create_evaluator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.skip("Not a test class")

class TestingFramework:
    """
    Main testing framework for SWIFT message routing models.

    Integrates configuration management, database operations, message generation,
    model testing, and result evaluation.
    """
    __test__ = False
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the testing framework.

        Args:
            config: A validated configuration object (from Pydantic).
        """
        self.config = config
        self.db_manager = None
        self.message_generator = None
        self.router = None
        self.evaluator = None
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize and configure database, generator, model, and evaluator."""
        try:
            db_config = self.config.database
            
            db_uri = f"postgresql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.dbname}"
            
            if hasattr(db_config, 'sslmode'):
                db_uri += f"?sslmode={db_config.sslmode}"
                
            logger.info(f"Using database URI: {db_uri}")
            
            self.db_manager = create_database_manager(db_uri)
            logger.info("Database connection established.")

            message_gen_config = self.config.message_generation.dict()
            message_gen_config['database_uri'] = db_uri
            self.message_generator = create_message_generator(message_gen_config)
            logger.info("Message generator initialized.")

            model_config = self.config.model.dict()
            model_dir = self.config.paths.model_dir
            model_path = os.path.join(model_dir, f"model_v{model_config.get('version')}.pkl")
            if os.path.exists(model_path):
                self.router = load_router(model_path)
                logger.info(f"Loaded existing routing model from {model_path}.")
            else:
                self.router = create_router(model_config)
                logger.info("Created new routing model.")

            evaluation_config = self.config.evaluation.dict()
            self.evaluator = create_evaluator(evaluation_config)
            logger.info("Evaluator initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def create_test_parameters(self, test_name: str, description: str) -> int:
        """
        Create test parameters in the database and return the parameter ID.

        Args:
            test_name: Name of the test.
            description: Description of the test.

        Returns:
            The generated parameter ID.
        """
        try:
            param_id = self.db_manager.create_parameter(test_name, description)
            logger.info(f"Test parameters created with ID {param_id}.")
            return param_id
        except Exception as e:
            logger.error(f"Error creating test parameters: {e}")
            raise

    def generate_messages(self, param_id: int, num_messages: int = None) -> List[int]:
        """
        Generate test messages for each template and store them in the database.

        Args:
            param_id: Parameter ID to associate with these messages.
            num_messages: Total number of messages to generate; if not provided, use default.

        Returns:
            A list of generated message IDs.
        """
        try:
            if num_messages is None:
                num_messages = self.config.message_generation.dict().get("num_messages", 100)
            templates = self.db_manager.get_all_templates()
            if not templates:
                logger.warning("No templates found in the database.")
                return []

            message_ids = []
            messages_per_template = max(1, num_messages // len(templates))
            for template in templates:
                template_id = template.get('id')
                template_text = template.get('template_text') 
                if not template_text:
                    template_text = template.get('template_content')
                
                if not isinstance(template_text, str):
                    logger.warning(f"Template text is not a string, it's a {type(template_text)}. Using template_content instead.")
                    template_text = str(template.get('template_content', ''))
                
                if not template_text:
                    logger.warning(f"No usable template content found for template {template_id}. Skipping.")
                    continue
                
                expected_routing_label = template.get('expected_routing_label', 'Unknown')
                
                logger.info(f"Using template: ID={template_id}, Type={template.get('template_type')}, Expected Label={expected_routing_label}")
                
                variations = self.message_generator.generate_variations(template_text, messages_per_template)
                for variation in variations:
                    message_id = self.db_manager.create_message(template_id, param_id, variation)
                    message_ids.append(message_id)
                    self.db_manager.create_expected_result(message_id, expected_routing_label)
            logger.info(f"Generated {len(message_ids)} test messages for parameter ID {param_id}.")
            return message_ids
        except Exception as e:
            logger.error(f"Error generating messages: {e}")
            raise

    def test_model(self, param_id: int) -> Dict[str, Any]:
        """
        Run the routing model on generated messages and store predictions.

        Args:
            param_id: Parameter ID associated with the test.

        Returns:
            A dictionary containing test results and metrics.
        """
        try:
            messages = self.db_manager.get_messages_by_param(param_id)
            if not messages:
                logger.warning(f"No messages found for parameter ID {param_id}.")
                return {"error": "No messages found"}
            
            logger.info(f"Testing model on {len(messages)} messages.")
            for message_data in messages:
                message_id = message_data['message_id']
                message_text = message_data['generated_text']
                predicted_label, confidence = self.router.predict(message_text)
                self.db_manager.create_actual_result(message_id, self.router.version, predicted_label, confidence)
            logger.info(f"Model testing completed for parameter ID {param_id}.")
            return self.get_test_results(param_id)
        except Exception as e:
            logger.error(f"Error during model testing: {e}")
            return {"error": str(e)}

    def get_test_results(self, param_id: int) -> Dict[str, Any]:
        """
        Retrieve test results from the database and aggregate evaluation metrics.

        Args:
            param_id: Parameter ID for the test run.

        Returns:
            A dictionary with test parameters, evaluation metrics, and output directory.
        """
        try:
            param_info = self.db_manager.get_parameter(param_id)
            if not param_info:
                logger.warning(f"Parameter ID {param_id} not found.")
                return {"error": "Parameter not found"}
            results = self.db_manager.get_test_results(param_id)
            if not results:
                logger.warning(f"No test results found for parameter ID {param_id}.")
                return {"parameter": param_info, "error": "No test results found"}
            
            true_labels = [r["expected_label"] for r in results]
            predicted_labels = [r["predicted_label"] for r in results]
            confidences = [r["confidence"] for r in results]
            
            output_dir = os.path.join(
                self.config.paths.output_dir,
                f"test_{param_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            os.makedirs(output_dir, exist_ok=True)
            
            evaluation_metrics = self.evaluator.evaluate(true_labels, predicted_labels, confidences, output_dir)
            return {
                "parameter": param_info,
                "num_messages": len(results),
                "evaluation": evaluation_metrics,
                "output_dir": output_dir
            }
        except Exception as e:
            logger.error(f"Error retrieving test results for parameter ID {param_id}: {e}")
            return {"error": str(e)}

    def train_model(self, param_id: int = None) -> Dict[str, Any]:
        """
        Train the routing model using messages from the database.

        Args:
            param_id: Optional parameter ID to filter training data.

        Returns:
            A dictionary of training metrics.
        """
        try:
            messages = []
            labels = []
            if param_id:
                message_data = self.db_manager.get_messages_by_param(param_id)
                for message in message_data:
                    message_id = message["message_id"]
                    expected = self.db_manager.get_expected_result(message_id)
                    if expected:
                        messages.append(message["generated_text"])
                        labels.append(expected["expected_label"])
            else:
                templates = self.db_manager.get_all_templates()
                for template in templates:
                    template_text = template.get('template_text') 
                    if not template_text:
                        template_text = template.get('template_content')
                    
                    if not isinstance(template_text, str):
                        logger.warning(f"Template text is not a string, it's a {type(template_text)}. Using template_content instead.")
                        template_text = str(template.get('template_content', ''))
                    
                    if not template_text:
                        logger.warning(f"No usable template content found for template {template.get('id')}. Skipping.")
                        continue
                    
                    expected_routing_label = template.get('expected_routing_label', 'Unknown')
                    
                    logger.info(f"Training with template: Type={template.get('template_type')}, Expected Label={expected_routing_label}")
                    
                    variations = self.message_generator.generate_variations(template_text, 20)
                    for variation in variations:
                        messages.append(variation)
                        labels.append(expected_routing_label)
            
            if not messages:
                logger.warning("No messages available for training.")
                return {"error": "No training data"}
            
            logger.info(f"Training model with {len(messages)} messages.")
            training_metrics = self.router.train(messages, labels)
            model_dir = self.config.paths.model_dir
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, f"model_v{self.router.version}.pkl")
            self.router.save(model_path)
            logger.info(f"Model trained and saved to {model_path}.")
            return training_metrics
        except Exception as e:
            logger.error(f"Error during model training: {e}")
            return {"error": str(e)}

    def run_complete_test(self, test_name: str, description: str, num_messages: int = None, train_model: bool = False) -> Dict[str, Any]:
        """
        Execute a full test workflow:
        1. Create test parameters.
        2. Generate messages.
        3. Optionally train the model.
        4. Test the model.
        5. Evaluate results.

        Args:
            test_name: Name of the test run.
            description: Description of the test.
            num_messages: Number of messages to generate (default from config if None).
            train_model: Whether to train the model before testing.

        Returns:
            A dictionary containing test results and aggregated metrics.
        """
        start_time = time.time()
        try:
            param_id = self.create_test_parameters(test_name, description)
            logger.info(f"Test parameters created with ID {param_id}.")
            
            message_ids = self.generate_messages(param_id, num_messages)
            logger.info(f"Generated {len(message_ids)} messages.")
            
            if train_model:
                training_metrics = self.train_model(param_id)
                logger.info(f"Model training metrics: {training_metrics}")
            
            test_results = self.test_model(param_id)
            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            logger.info(f"Complete test run completed in {execution_time:.2f} seconds.")
            return test_results
        except Exception as e:
            logger.error(f"Complete test run failed: {e}")
            return {"error": str(e)}

def create_testing_framework(config_path: str) -> TestingFramework:
    """
    Helper function to create a TestingFramework instance.

    Args:
        config_path: Path to the configuration YAML file.

    Returns:
        An instance of TestingFramework.
    """
    from src.config_loader import load_config
    config = load_config(config_path)
    return TestingFramework(config)