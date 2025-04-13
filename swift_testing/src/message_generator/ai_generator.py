"""
AI Message Generator

This module uses Ollama to generate variations of SWIFT messages based on templates.
"""

import logging
import json
import re
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class OllamaGenerator:
    """
    SWIFT message generator that uses Ollama models to create variations.
    """
    
    def __init__(
        self, 
        model_name: str = "llama3", 
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        api_base: str = "http://localhost:11434/api"
    ):
        """
        Initialize the Ollama generator.
        
        Args:
            model_name: Name of the Ollama model to use
            temperature: Controls randomness in generation (0.0-1.0)
            system_prompt: Optional system prompt to guide generation
            api_base: Base URL for Ollama API
        """
        self.model_name = model_name
        self.temperature = temperature
        self.api_base = api_base
        
        self.system_prompt = system_prompt or (
            "You are a banking system that creates realistic SWIFT financial messages. "
            "Your task is to fill in the placeholder values in SWIFT message templates "
            "with realistic but fictional data. Keep the same message structure and format, "
            "but replace placeholder values with realistic information."
        )
        
        logger.info(f"Initialized Ollama generator using model: {model_name}")
    
    def generate_variation(self, template: str) -> str:
        """
        Generate a variation of a SWIFT message template using Ollama.
        
        Args:
            template: SWIFT message template text
        
        Returns:
            Generated SWIFT message with variations
        """
        prompt = self._create_prompt(template)
        
        try:
            logger.info(f"Generating variation using Ollama model {self.model_name}")
            response = self._call_ollama_api(prompt)
            
            generated_message = self._clean_response(response, template)
            return generated_message
            
        except Exception as e:
            logger.error(f"Error generating message variation: {e}")
            return template
    
    def _create_prompt(self, template: str) -> str:
        """
        Create a prompt for the Ollama model.
        
        Args:
            template: SWIFT message template
        
        Returns:
            Prompt string for Ollama
        """
        return (
            f"Create a realistic SWIFT message based on this template:\n\n"
            f"{template}\n\n"
            f"Replace all placeholder values with realistic but fictional data. "
            f"Keep the exact same SWIFT message structure and format, including all tags. "
            f"Only output the resulting message, nothing else."
        )
    
    def _call_ollama_api(self, prompt: str) -> str:
        """
        Call the Ollama API to generate text.
        
        Args:
            prompt: The prompt to send to Ollama
        
        Returns:
            Generated text response
        
        Raises:
            Exception: If the API call fails
        """
        try:
            response = requests.post(
                f"{self.api_base}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": self.system_prompt,
                    "temperature": self.temperature,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                raise Exception(f"API error: {response.status_code}")
        except requests.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def _clean_response(self, response: str, original_template: str) -> str:
        """
        Clean the API response to extract just the SWIFT message.
        
        Args:
            response: Raw response from the API
            original_template: Original template for reference
        
        Returns:
            Cleaned SWIFT message
        """
        response = re.sub(r'```swift|```SWIFT|```|```\n', '', response)
        
        lines = []
        for line in response.strip().split('\n'):
            if re.search(r'[{}]|:[\d\w]+:', line) or line.strip():
                lines.append(line)
                
        return '\n'.join(lines)


def create_ollama_generator(**kwargs) -> OllamaGenerator:
    """
    Create a new OllamaGenerator instance.
    
    Args:
        **kwargs: Arguments to pass to the OllamaGenerator constructor
    
    Returns:
        New OllamaGenerator instance
    """
    return OllamaGenerator(**kwargs) 