"""
aGENtrader v2 LLM Client

This module provides a client for interacting with large language models.
It supports both API-based providers (Grok, OpenAI) and local Mixtral via Ollama.
"""

import os
import json
import logging
import requests
import time
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_client')

class LLMClient:
    """
    Client for interacting with large language models.
    
    This client supports multiple LLM providers including:
    - Local Mixtral via Ollama (preferred for cost efficiency and privacy)
    - Grok API (xAI)
    - OpenAI API
    
    It handles API requests, prompt formatting, and response parsing.
    """
    
    # Default providers and endpoints from environment or config
    DEFAULT_PROVIDER = os.environ.get('LLM_PROVIDER_DEFAULT', 'grok')  # Default to Grok for testing reliability
    DEFAULT_MODEL = os.environ.get('LLM_MODEL_DEFAULT', 'grok-2-1212')  # Using Grok for testing
    
    # Agent-specific model configuration
    AGENT_SPECIFIC_MODELS = {
        # All agents now use Grok as the primary provider for testing reliability
        'sentiment_analyst': {
            'provider': 'grok',
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        },
        'sentiment_aggregator': {
            'provider': 'grok',
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        },
        
        # Technical and market structure agents now use Grok directly for testing
        'technical_analyst': {
            'provider': 'grok',  # Using Grok directly instead of local Ollama
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        },
        'liquidity_analyst': {
            'provider': 'grok',  # Using Grok directly instead of local Ollama
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        },
        'funding_rate_analyst': {
            'provider': 'grok',  # Using Grok directly instead of local Ollama
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        },
        'open_interest_analyst': {
            'provider': 'grok',  # Using Grok directly instead of local Ollama
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        },
        
        # Decision agent also uses Grok directly for testing
        'decision_agent': {
            'provider': 'grok',  # Using Grok directly instead of local Ollama
            'model': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        }
    }
    
    # Try multiple potential Ollama endpoints based on deployment environment
    DEPLOY_ENV = os.environ.get('DEPLOY_ENV', 'dev').lower()
    
    # Define environment-specific endpoints
    if DEPLOY_ENV == 'ec2':
        # When running on EC2, try connections within the instance first, then other known locations
        # Prioritize 127.0.0.1 since that's where Ollama is currently listening
        DEFAULT_ENDPOINTS = [
            'http://127.0.0.1:11434',  # This is the address Ollama is actually using
            os.environ.get('LLM_ENDPOINT_DEFAULT', 'http://localhost:11434'),
            'http://localhost:11434',
            'http://0.0.0.0:11434',
            'http://172.31.16.22:11434'  # EC2 internal IP (might vary)
        ]
        logger.info(f"Running in EC2 environment, will use these Ollama endpoints: {DEFAULT_ENDPOINTS}")
    elif DEPLOY_ENV == 'docker':
        # When running in Docker, include Docker-specific hostnames
        DEFAULT_ENDPOINTS = [
            os.environ.get('LLM_ENDPOINT_DEFAULT', 'http://localhost:11434'),
            'http://localhost:11434', 
            'http://host.docker.internal:11434',  # Docker host access
            'http://ollama:11434'  # If running in a Docker network with ollama service
        ]
        logger.info(f"Running in Docker environment, will use these Ollama endpoints: {DEFAULT_ENDPOINTS}")
    else:
        # Default endpoints for local development
        DEFAULT_ENDPOINTS = [
            os.environ.get('LLM_ENDPOINT_DEFAULT', 'http://localhost:11434'),
            'http://localhost:11434',
            'http://127.0.0.1:11434'
        ]
        logger.info(f"Running in {DEPLOY_ENV} environment, will use these Ollama endpoints: {DEFAULT_ENDPOINTS}")
        
    DEFAULT_ENDPOINT = DEFAULT_ENDPOINTS[0]  # Use the first one as default
    
    def __init__(self, 
                 provider: Optional[str] = None, 
                 model: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 agent_name: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            provider: Provider to use ('local', 'grok', 'openai')
            model: Model name to use
            endpoint: API endpoint for local provider
            config: Additional configuration parameters
            agent_name: Name of the agent using this LLM client (for agent-specific configurations)
        """
        self.config = config or {}
        self.agent_name = agent_name
        
        # Check if we have an agent-specific configuration
        if agent_name:
            if agent_name.lower() in self.AGENT_SPECIFIC_MODELS:
                agent_config = self.AGENT_SPECIFIC_MODELS[agent_name.lower()]
                provider = provider or agent_config.get('provider')
                model = model or agent_config.get('model')
                logger.info(f"Using agent-specific LLM config for {agent_name}: {provider}:{model}")
            else:
                logger.info(f"No special LLM config for {agent_name}, using default provider: {self.DEFAULT_PROVIDER}, model: {self.DEFAULT_MODEL}")
        
        # Set provider and model from parameters or defaults
        self.provider = provider or self.config.get('provider', self.DEFAULT_PROVIDER)
        self.model = model or self.config.get('model', self.DEFAULT_MODEL)
        
        # Configure Ollama for local Mixtral
        self.ollama_enabled = self.provider == 'local'
        self.ollama_endpoint = endpoint or self.config.get('endpoint', self.DEFAULT_ENDPOINT)
        self.ollama_api_chat = f"{self.ollama_endpoint}/api/chat"
        self.ollama_api_generate = f"{self.ollama_endpoint}/api/generate"
        
        # Test Ollama connection if local provider is selected
        if self.ollama_enabled:
            ollama_available = self._test_ollama_connection()
            if not ollama_available:
                logger.warning(f"Ollama not available at {self.ollama_endpoint}. Will try fallback providers.")
                # Fallback to Grok if Ollama is not available
                self.provider = 'grok'
        
        # Configure API keys
        self.api_keys = {
            'local': None,  # Local Ollama doesn't need an API key
            'grok': os.environ.get('XAI_API_KEY'),
            'openai': os.environ.get('OPENAI_API_KEY')
        }
        
        # Configure API endpoints
        self.api_endpoints = {
            'local': self.ollama_api_chat,
            'grok': 'https://api.x.ai/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions'
        }
        
        # Configure default models for each provider
        self.default_models = {
            'local': 'mistral',  # Changed from mixtral to mistral for lower resource requirements
            'grok': os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212'),
            'openai': 'gpt-4-turbo'
        }
        
        # Set the model based on provider
        if not model:
            provider_key = self.provider or 'local'
            self.model = self.default_models.get(provider_key, 'mistral')  # Changed from mixtral to mistral
        
        # Log available providers
        available_providers = []
        if self.ollama_enabled and self._test_ollama_connection():
            available_providers.append('local')
        available_providers.extend([p for p, key in self.api_keys.items() if key and p != 'local'])
        
        if available_providers:
            logger.info(f"LLM client initialized with: {self.provider}:{self.model}")
        else:
            logger.warning("No LLM providers are available. Check Ollama setup or set API keys.")
    
    def _test_ollama_connection(self) -> bool:
        """
        Test if local Ollama server is running and responsive.
        Tries multiple possible endpoints if the default one fails.
        Provides more detailed diagnostics in EC2 environment.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        # First try the configured endpoint
        if self._try_ollama_endpoint(self.ollama_endpoint):
            return True
            
        # If that fails, try all the default endpoints
        for endpoint in self.DEFAULT_ENDPOINTS:
            if endpoint != self.ollama_endpoint:  # Skip the one we already tried
                if self._try_ollama_endpoint(endpoint):
                    # Update the endpoint to the working one
                    logger.info(f"Switching to working Ollama endpoint: {endpoint}")
                    self.ollama_endpoint = endpoint
                    self.ollama_api_chat = f"{self.ollama_endpoint}/api/chat"
                    self.ollama_api_generate = f"{self.ollama_endpoint}/api/generate"
                    return True
        
        # If all endpoints fail, provide environment-specific diagnostics
        if self.DEPLOY_ENV == 'ec2':
            logger.warning("""
            ===== EC2 OLLAMA CONNECTION FAILURE =====
            Unable to connect to Ollama server in the EC2 environment.
            
            Possible causes and solutions:
            1. Ollama service is not running - Run 'sudo systemctl start ollama' on the EC2 instance
            2. Ollama is running but only on localhost (127.0.0.1) - Run the following commands:
               sudo systemctl stop ollama
               sudo mkdir -p /etc/ollama
               sudo bash -c 'echo "host = \\"0.0.0.0\\"" > /etc/ollama/config'
               sudo systemctl start ollama
               sudo netstat -tulpn | grep ollama  # Should show 0.0.0.0:11434
            3. Firewall blocking connections - Check EC2 security group settings
            4. Mistral model is installed but service is stopped - Run 'sudo systemctl status ollama'
            
            Will fallback to using Grok API instead.
            ==========================================
            """)
        else:
            logger.warning(f"All Ollama endpoints failed to connect in {self.DEPLOY_ENV} environment")
            
        return False
        
    def _try_ollama_endpoint(self, endpoint: str) -> bool:
        """
        Try to connect to a specific Ollama endpoint.
        
        Args:
            endpoint: The endpoint URL to try
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple ping to Ollama API
            response = requests.get(endpoint, timeout=5)  # Add a timeout
            if response.status_code == 200:
                # Check if the model we need is available (for Mistral)
                try:
                    models_response = requests.get(f"{endpoint}/api/tags", timeout=5)
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        models = [model.get('name', '') for model in models_data.get('models', [])]
                        if 'mistral' in models or 'mistral:latest' in models:
                            logger.info(f"Ollama server is available at {endpoint} with Mistral model")
                        else:
                            logger.warning(f"Ollama is available at {endpoint} but Mistral model is not installed")
                            # We still return True as Ollama is available, but log a warning
                except Exception as model_e:
                    logger.warning(f"Could not check available models: {str(model_e)}")
                
                logger.info(f"Local Ollama server is available at {endpoint}")
                return True
            else:
                if self.DEPLOY_ENV == 'ec2':
                    logger.warning(f"Ollama server at {endpoint} returned error status: {response.status_code}")
                    logger.warning("Possible issue: Ollama service may need to be restarted with 'sudo systemctl restart ollama'")
                else:
                    logger.warning(f"Ollama server at {endpoint} returned error status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            
            if self.DEPLOY_ENV == 'ec2':
                if "Connection refused" in error_message:
                    logger.warning(f"Ollama server at {endpoint} connection refused: Service may not be running")
                    logger.warning("Start Ollama with: 'sudo systemctl start ollama' or 'ollama serve'")
                elif "Name or service not known" in error_message:
                    logger.warning(f"Ollama server at {endpoint} host not found: Check network configuration or hostname")
                elif "timed out" in error_message:
                    logger.warning(f"Connection timed out for {endpoint}: Check firewall settings or instance security group")
                else:
                    logger.warning(f"Ollama server at {endpoint} is not available: {error_message}")
            else:
                logger.warning(f"Ollama server at {endpoint} is not available: {error_message}")
                
            return False
            
    def query(self, 
              prompt: str, 
              provider: Optional[str] = None,
              system_prompt: Optional[str] = None,
              model: Optional[str] = None,
              json_response: bool = False,
              max_tokens: int = 1000,
              temperature: float = 0.7
             ) -> Dict[str, Any]:
        """
        Send a query to a language model.
        
        Args:
            prompt: User prompt
            provider: Provider to use ('local', 'grok', 'openai')
            system_prompt: Optional system prompt
            model: Specific model to use
            json_response: Whether to request a JSON response
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Dictionary containing response and metadata
        """
        # Select provider
        provider_to_use = provider or self.provider
        model_to_use = model or self.model or "mistral"  # Changed from mixtral to mistral
        
        # If local is requested but not available, fall back
        if provider_to_use == 'local' and not self._test_ollama_connection():
            fallbacks = [p for p, key in self.api_keys.items() if key and p != 'local']
            if fallbacks:
                logger.warning(f"Ollama not available, falling back to {fallbacks[0]}")
                provider_to_use = fallbacks[0]
                model_to_use = self.default_models.get(provider_to_use, "mistral")  # Changed from mixtral to mistral
            else:
                return {
                    "error": "Ollama not available and no fallback providers configured",
                    "message": "Check Ollama server or set API keys for Grok/OpenAI",
                    "status": "error"
                }
        
        # For non-local providers, check API keys
        if provider_to_use != 'local' and not self.api_keys.get(provider_to_use, None):
            available = ['local'] if self._test_ollama_connection() else []
            available.extend([p for p, key in self.api_keys.items() if key and p != 'local'])
            
            if not available:
                return {
                    "error": "No LLM providers available",
                    "message": "Check Ollama or set API keys for Grok/OpenAI",
                    "status": "error"
                }
            
            logger.warning(f"Provider {provider_to_use} not available. Falling back to {available[0]}")
            provider_to_use = available[0]
            model_to_use = self.default_models.get(provider_to_use, "mistral")  # Changed from mixtral to mistral
            
        try:
            # Ollama has a different API format
            if provider_to_use == 'local':
                return self._query_ollama(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model_to_use,
                    json_response=json_response,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                # For Grok and OpenAI
                return self._query_openai_compatible(
                    prompt=prompt,
                    provider=provider_to_use,
                    system_prompt=system_prompt,
                    model=model_to_use,
                    json_response=json_response,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                    
        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}", exc_info=True)
            
            # Try fallback providers
            if provider == 'local':
                fallbacks = [p for p, key in self.api_keys.items() if key and p != 'local']
                if fallbacks:
                    logger.warning(f"Ollama query failed, trying fallback: {fallbacks[0]}")
                    return self.query(
                        prompt=prompt,
                        provider=fallbacks[0],
                        system_prompt=system_prompt,
                        model=None,  # Use default model for fallback provider
                        json_response=json_response,
                        max_tokens=max_tokens
                    )
                    
            return {
                "error": "LLM query error",
                "message": str(e),
                "status": "error"
            }
    
    def _query_ollama(self,
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      model: Optional[str] = "mistral",  # Changed from mixtral to mistral for lower resource requirements
                      json_response: bool = False,
                      max_tokens: int = 1000,
                      temperature: float = 0.7) -> Dict[str, Any]:
        """
        Query the Ollama API for local inference.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model name in Ollama
            json_response: Whether to request a JSON response
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Dictionary containing response and metadata
        """
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
        
        # Add JSON formatting hint for structured responses
        if json_response:
            if system_prompt:
                messages[0]["content"] += "\n\nYour response must be valid JSON only, with no other text."
            else:
                messages.insert(0, {
                    "role": "system",
                    "content": "Your response must be valid JSON only, with no other text."
                })
        
        # Create API payload for Ollama
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        # Send request to Ollama
        logger.debug(f"Sending request to Ollama API for model {model}...")
        
        # Ollama API has a different response format
        response = requests.post(
            self.ollama_api_chat,
            json=payload,
            timeout=120  # Longer timeout for local inference
        )
        
        # Parse response
        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")
            
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
                "model": model,
                "provider": "local",
                "status": "success"
            }
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return {
                "error": f"Ollama API error ({response.status_code})",
                "message": response.text,
                "status": "error"
            }
    
    def _query_openai_compatible(self,
                               prompt: str,
                               provider: Optional[str] = "grok",
                               system_prompt: Optional[str] = None,
                               model: Optional[str] = None,
                               json_response: bool = False,
                               max_tokens: int = 1000,
                               temperature: float = 0.7) -> Dict[str, Any]:
        """
        Query OpenAI-compatible APIs (Grok, OpenAI).
        
        Args:
            prompt: User prompt
            provider: Provider name ('grok', 'openai')
            system_prompt: Optional system prompt
            model: Model name
            json_response: Whether to request a JSON response
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Dictionary containing response and metadata
        """
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
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add JSON response format if requested
        if json_response:
            payload["response_format"] = {"type": "json_object"}
            
        # Create headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authorization if provider is valid and has an API key
        if provider and provider in self.api_keys and self.api_keys[provider]:
            headers["Authorization"] = f"Bearer {self.api_keys[provider]}"
        
        # Get endpoint safely
        endpoint = self.api_endpoints.get(provider or "grok", self.api_endpoints["grok"])
        
        # Send request
        logger.debug(f"Sending request to {provider or 'default'} API...")
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # Parse response
        if response.status_code == 200:
            data = response.json()
            
            # Extract content from response
            content = data["choices"][0]["message"]["content"]
                
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
            
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM (simplified interface for DecisionAgent).
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters to pass to query()
            
        Returns:
            The generated text as a string
        """
        response = self.query(prompt, **kwargs)
        
        if response.get("status") == "success":
            content = response.get("content", "")
            if isinstance(content, dict):
                # If content is a dictionary (from JSON response), return it as a string
                return json.dumps(content)
            return content
        else:
            error_msg = response.get("message", "Unknown error")
            logger.error(f"Error generating response: {error_msg}")
            return f"Error: {error_msg}"
            
    def check_ollama_status(self) -> Dict[str, Any]:
        """
        Check the status of the local Ollama server.
        
        Returns:
            Dictionary with status information
        """
        if not self._test_ollama_connection():
            return {
                "status": "unavailable",
                "message": "Ollama server is not running or not accessible"
            }
            
        try:
            # List models
            response = requests.get(f"{self.ollama_endpoint}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "available",
                    "message": "Ollama server is running",
                    "models": data.get("models", [])
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama server returned status code {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error checking Ollama status: {str(e)}"
            }