"""
aGENtrader v2 LLM Client

This module provides a client for interacting with large language models.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_client')

class LLMClient:
    """
    Client for interacting with large language models.
    
    This client supports multiple LLM providers and handles API requests,
    prompt formatting, and response parsing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM client.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        
        # Default to Grok if available
        self.default_provider = self.config.get('default_provider', 'grok')
        
        # Configure API keys
        self.api_keys = {
            'grok': os.environ.get('XAI_API_KEY'),
            'openai': os.environ.get('OPENAI_API_KEY')
        }
        
        # Configure API endpoints
        self.api_endpoints = {
            'grok': 'https://api.x.ai/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions'
        }
        
        # Configure models
        self.models = {
            'grok': 'grok-2-1212',
            'openai': 'gpt-4-turbo'
        }
        
        # Log available providers
        available_providers = [p for p, key in self.api_keys.items() if key]
        if available_providers:
            logger.info(f"LLM client initialized with providers: {', '.join(available_providers)}")
        else:
            logger.warning("No LLM providers are configured. Set XAI_API_KEY or OPENAI_API_KEY environment variables.")
            
    def query(self, 
              prompt: str, 
              provider: Optional[str] = None,
              system_prompt: Optional[str] = None,
              model: Optional[str] = None,
              json_response: bool = False,
              max_tokens: int = 1000
             ) -> Dict[str, Any]:
        """
        Send a query to a language model.
        
        Args:
            prompt: User prompt
            provider: Provider to use (grok, openai)
            system_prompt: Optional system prompt
            model: Specific model to use
            json_response: Whether to request a JSON response
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary containing response and metadata
        """
        # Select provider
        provider = provider or self.default_provider
        
        # Check if provider is available
        if not self.api_keys.get(provider):
            available = [p for p, key in self.api_keys.items() if key]
            if not available:
                return {
                    "error": "No LLM providers available",
                    "message": "Set XAI_API_KEY or OPENAI_API_KEY environment variables",
                    "status": "error"
                }
            
            logger.warning(f"Provider {provider} not available. Falling back to {available[0]}")
            provider = available[0]
            
        try:
            # Select model
            model = model or self.models.get(provider)
            
            # Create messages
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
                
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Create API payload
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens
            }
            
            # Add JSON response format if requested
            if json_response:
                payload["response_format"] = {"type": "json_object"}
                
            # Create headers
            headers = {
                "Authorization": f"Bearer {self.api_keys[provider]}",
                "Content-Type": "application/json"
            }
            
            # Send request
            response = requests.post(
                self.api_endpoints[provider],
                headers=headers,
                json=payload
            )
            
            # Parse response
            if response.status_code == 200:
                data = response.json()
                
                # Extract content based on provider
                if provider == 'grok':
                    content = data["choices"][0]["message"]["content"]
                elif provider == 'openai':
                    content = data["choices"][0]["message"]["content"]
                else:
                    content = "Unsupported provider"
                    
                # Parse JSON if requested
                if json_response:
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Error parsing JSON response: {content}")
                        return {
                            "error": "JSON parsing error",
                            "message": "The model did not return valid JSON",
                            "status": "error"
                        }
                
                # Return response
                return {
                    "content": content,
                    "model": data.get("model", model),
                    "provider": provider,
                    "status": "success"
                }
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {
                    "error": f"API error ({response.status_code})",
                    "message": response.text,
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}", exc_info=True)
            return {
                "error": "LLM query error",
                "message": str(e),
                "status": "error"
            }