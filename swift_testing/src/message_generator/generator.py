"""
Message Generator Module

This module generates simulated SWIFT messages based on templates and configuration.
It applies dynamic field substitutions using precompiled regex patterns,
caching, detailed logging, and error handling to ensure high performance and robustness.
"""

import re
import logging
import random
import time
from typing import List, Dict, Any, Callable

from src.message_generator.field_handlers import (
    initialize_field_handlers,
    FIELD_HANDLER_REGISTRY,
    DefaultFieldHandler
)

logger = logging.getLogger(__name__)


class MessageGenerator:
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the message generator.

        Args:
            config: Configuration dictionary (or Pydantic model converted to dict) containing generation parameters.
        """
        self.config = config
        mg_config = config["message_generation"]
        self.perturbation_degree = mg_config.get("perturbation_degree", 0.2)
        self.seed = mg_config.get("seed", 42)
        self.max_variations = mg_config.get("max_variations_per_template", 10)
        self.field_substitution_rate = mg_config.get("field_substitution_rate", 0.3)

        random.seed(self.seed)

        self.field_patterns: Dict[str, str] = mg_config.get("field_patterns", {})

        self.compiled_patterns: Dict[str, re.Pattern] = {}
        for field, pattern in self.field_patterns.items():
            try:
                self.compiled_patterns[field] = re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                logger.warning(f"Error compiling regex pattern for {field}: {e}. Using default pattern.")
                self.compiled_patterns[field] = re.compile(r".*")

        initialize_field_handlers(config)

        self.default_handler = DefaultFieldHandler(mg_config.get("substitutions", {}))

        self.substitution_count = 0  # Count substitutions in the current message.
        self.total_substitutions = 0  # Count total substitutions over a run.
        self.total_generation_time = 0.0  # Total time taken for message generation.
        self.substitution_cache: Dict[str, str] = {}  # Cache for substitution results.

    def _field_substitution_func(self, field_type: str) -> Callable[[re.Match], str]:
        """
        Create a substitution function for a given field type.

        Args:
            field_type: The type of field being substituted.

        Returns:
            A function that accepts a regex match and returns the substituted string.
        """
        def substitute_field(match: re.Match) -> str:
            try:
                original_value = match.group(0)
                if original_value in self.substitution_cache:
                    cached_value = self.substitution_cache[original_value]
                    logger.debug(f"[Cache] {field_type}: {original_value} -> {cached_value}")
                    self.substitution_count += 1
                    self.total_substitutions += 1
                    return cached_value

                if random.random() >= self.field_substitution_rate:
                    self.total_substitutions += 1
                    return original_value

                handler = FIELD_HANDLER_REGISTRY.get(field_type, self.default_handler)
                new_value = handler.substitute(match)
                self.substitution_cache[original_value] = new_value

                logger.debug(f"Substituted {field_type}: {original_value} -> {new_value}")
                self.substitution_count += 1
                self.total_substitutions += 1
                return new_value
            except Exception as e:
                logger.error(f"Error substituting field '{field_type}': {e}")
                return match.group(0)
        return substitute_field

    def generate_message(self, template: str) -> str:
        """
        Generate a SWIFT message by applying field substitutions to a template.

        Args:
            template: The original SWIFT message template.

        Returns:
            A string containing the generated message.
        """
        start_time = time.time()
        message = template
        for field_type, pattern in self.compiled_patterns.items():
            message = pattern.sub(self._field_substitution_func(field_type), message)
        gen_time = time.time() - start_time
        self.total_generation_time += gen_time
        logger.info(f"Generated message in {gen_time:.4f} sec; substitutions: {self.substitution_count}")
        self.substitution_count = 0
        return message

    def generate_variations(self, template: str, count: int = None) -> List[str]:
        """
        Generate multiple variations of a SWIFT message template.

        Args:
            template: The SWIFT message template.
            count: The number of variations to generate (if None, a random number up to max_variations is used).

        Returns:
            A list of generated message strings.
        """
        if count is None:
            count = random.randint(1, self.max_variations)
        variations = [self.generate_message(template) for _ in range(count)]
        logger.info(f"Total time for {count} messages: {self.total_generation_time:.4f} sec; total substitutions: {self.total_substitutions}")
        self.total_generation_time = 0.0
        self.total_substitutions = 0
        return variations

def create_message_generator(config: Dict[str, Any]) -> MessageGenerator:
    """
    Factory function to create a MessageGenerator instance.

    Args:
        config: The configuration dictionary.

    Returns:
        An instance of MessageGenerator.
    """
    return MessageGenerator(config)