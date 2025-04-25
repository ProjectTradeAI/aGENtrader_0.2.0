"""
LLM Client Abstraction Module

This module provides a unified interface for different LLM providers:
- Mock mode for fast development
- Ollama for local testing on EC2
- Optional OpenAI support (post-MVP)

The client handles formatting, token management, and serialization
to ensure consistent responses across different LLM backends.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

# Import centralized logger and configuration
from utils.logger import get_logger
from utils.config import get_config

# Get module logger and configuration
logger = get_logger("llm_client")
config = get_config()

# Base LLM Provider class
class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text based on prompt"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response based on chat messages"""
        pass

# Mock LLM Provider for fast development
class MockLLMProvider(LLMProvider):
    """Mock LLM provider for fast development and testing"""
    
    def __init__(self):
        self.logger = get_logger("mock_llm")
        self.logger.info("Initialized Mock LLM Provider")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response based on prompt type"""
        self.logger.info(f"Mock LLM received prompt: {prompt[:50]}...")
        
        # Detect the type of analysis being requested
        if "liquidity" in prompt.lower():
            return self._generate_liquidity_analysis()
        elif "market" in prompt.lower():
            return self._generate_market_analysis()
        elif "decision" in prompt.lower():
            return self._generate_trading_decision()
        else:
            return "I'm a mock LLM and I don't have a specific response for this prompt type."
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate mock response based on chat history"""
        self.logger.info(f"Mock LLM received chat with {len(messages)} messages")
        
        # Extract the last user message
        last_message = messages[-1]["content"] if messages and messages[-1]["role"] == "user" else ""
        
        # Use the generate method to create a response
        return self.generate(last_message, **kwargs)
    
    def _generate_liquidity_analysis(self) -> str:
        """Generate a mock liquidity analysis"""
        return json.dumps({
            "analysis": {
                "overall_liquidity": "high",
                "bid_ask_imbalance": "neutral",
                "volume_profile": "above average",
                "depth_analysis": "Large buy walls observed at key support levels",
                "funding_rate_impact": "neutral to slightly positive",
                "liquidity_score": 78
            },
            "interpretation": "Market shows strong liquidity with balanced order books. Volume concentration at key price levels suggests institutional interest.",
            "recommendation": "Current liquidity conditions are favorable for both entry and exit with minimal slippage."
        })
    
    def _generate_market_analysis(self) -> str:
        """Generate a mock market analysis"""
        return json.dumps({
            "analysis": {
                "trend": "bullish",
                "key_levels": {
                    "support": [45200, 44500, 43800],
                    "resistance": [46700, 47500, 48200]
                },
                "volatility": "moderate",
                "momentum": "positive",
                "market_structure": "higher highs and higher lows",
                "market_score": 72
            },
            "interpretation": "BTC is in an uptrend with strong momentum, forming a series of higher highs and higher lows.",
            "recommendation": "Look for pullbacks to key support levels for potential entries."
        })
    
    def _generate_trading_decision(self) -> str:
        """Generate a mock trading decision"""
        return json.dumps({
            "action": "BUY",
            "pair": "BTC/USDT",
            "confidence": 87,
            "reason": "Strong market structure + deep liquidity detected"
        })

# Ollama Provider for local model deployment
class OllamaLLMProvider(LLMProvider):
    """Ollama provider for local model deployment"""
    
    def __init__(self, model: str = "tiny-llama", endpoint: str = "http://localhost:11434"):
        self.logger = get_logger("ollama_llm")
        self.model = model
        self.endpoint = endpoint
        self.logger.info(f"Initialized Ollama LLM Provider with model: {model}")
        
        # Import requests here to avoid dependency if not using this provider
        try:
            import requests
            self.requests = requests
        except ImportError:
            self.logger.error("Requests library not found. Please install with 'pip install requests'")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama API"""
        self.logger.info(f"Generating with Ollama model {self.model}")
        
        try:
            response = self.requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: Failed to get response from Ollama. Status code: {response.status_code}"
                
        except Exception as e:
            self.logger.error(f"Error calling Ollama API: {e}")
            return f"Error: {str(e)}"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using Ollama API"""
        self.logger.info(f"Chat with Ollama model {self.model}")
        
        try:
            response = self.requests.post(
                f"{self.endpoint}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    **kwargs
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: Failed to get response from Ollama. Status code: {response.status_code}"
                
        except Exception as e:
            self.logger.error(f"Error calling Ollama API: {e}")
            return f"Error: {str(e)}"

# OpenAI Provider (optional, post-MVP)
class OpenAILLMProvider(LLMProvider):
    """OpenAI provider for remote API support"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        self.logger = get_logger("openai_llm")
        self.model = model
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.logger.warning("No OpenAI API key found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.logger.info(f"Initialized OpenAI LLM Provider with model: {model}")
        
        # Import openai here to avoid dependency if not using this provider
        try:
            import openai
            self.openai = openai
            self.openai.api_key = self.api_key
        except ImportError:
            self.logger.error("OpenAI library not found. Please install with 'pip install openai'")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API"""
        self.logger.info(f"Generating with OpenAI model {self.model}")
        
        if not self.api_key:
            return "Error: OpenAI API key is not set"
        
        try:
            response = self.openai.Completion.create(
                model=self.model,
                prompt=prompt,
                **kwargs
            )
            
            return response.choices[0].text.strip()
                
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            return f"Error: {str(e)}"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using OpenAI API"""
        self.logger.info(f"Chat with OpenAI model {self.model}")
        
        if not self.api_key:
            return "Error: OpenAI API key is not set"
        
        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            
            return response.choices[0].message.content.strip()
                
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            return f"Error: {str(e)}"

# Main LLM Client
class LLMClient:
    """
    Main LLM Client that provides a unified interface for different LLM providers.
    
    This class handles:
    - Provider selection based on configuration
    - Prompt formatting
    - Response parsing
    - Error handling
    """
    
    def __init__(self, provider: str = None, model: str = None):
        """
        Initialize the LLM client with specified provider and model.
        
        Args:
            provider: LLM provider (mock, ollama, or openai)
            model: Model name for the selected provider
        """
        self.logger = get_logger("llm_client")
        
        # Load configuration from central config module
        self.llm_config = config.get_llm_settings()
        
        # Set provider and model from args or config
        self.provider_name = provider or self.llm_config.get("provider", "mock")
        self.model_name = model or self.llm_config.get("model", "tinyllama")
        
        # Initialize the appropriate provider
        self._init_provider()
        
        self.logger.info(f"LLM Client initialized with provider: {self.provider_name}, model: {self.model_name}")
    
    def _init_provider(self):
        """Initialize the selected LLM provider"""
        if self.provider_name == "mock":
            self.provider = MockLLMProvider()
        elif self.provider_name == "ollama":
            self.provider = OllamaLLMProvider(model=self.model_name)
        elif self.provider_name == "openai":
            self.provider = OpenAILLMProvider(model=self.model_name)
        else:
            self.logger.warning(f"Unknown provider: {self.provider_name}. Using mock provider.")
            self.provider = MockLLMProvider()
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on prompt.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        return self.provider.generate(prompt, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate response based on chat messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated chat response
        """
        return self.provider.chat(messages, **kwargs)
    
    def analyze(self, data: Any, task: str, format_output: bool = True) -> Dict[str, Any]:
        """
        Analyze data for a specific task and return structured result.
        
        Args:
            data: Data to analyze
            task: Analysis task description
            format_output: Whether to format the output as JSON
            
        Returns:
            Analysis result as dictionary
        """
        # Format prompt based on task
        if isinstance(data, dict) or isinstance(data, list):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = str(data)
            
        prompt = f"""
        Task: {task}
        
        Data to analyze:
        {data_str}
        
        Please provide a detailed analysis of the data for the specified task.
        Return your analysis as a JSON object with clear reasoning and recommendations.
        """
        
        # Get response from provider
        response = self.generate(prompt)
        
        # Parse response if format_output is True
        if format_output:
            try:
                # Extract JSON if response contains other text
                response = self._extract_json(response)
                return json.loads(response)
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse response as JSON")
                return {"error": "Failed to parse response as JSON", "raw_response": response}
        
        return {"result": response}
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain other content"""
        import re
        
        # Try to find JSON objects in the text
        json_pattern = r'({[\s\S]*}|\[[\s\S]*\])'
        matches = re.findall(json_pattern, text)
        
        if matches:
            for match in matches:
                try:
                    # Validate that this is valid JSON
                    json.loads(match)
                    return match
                except:
                    continue
        
        # If no valid JSON found, return the original text
        return text


# Example usage (for demonstration)
if __name__ == "__main__":
    # Create client with default settings (mock provider)
    client = LLMClient()
    
    # Generate a simple response
    response = client.generate("Analyze the liquidity of BTC/USDT")
    print(f"Response: {response}")
    
    # Use chat interface
    chat_response = client.chat([
        {"role": "system", "content": "You are a helpful trading assistant."},
        {"role": "user", "content": "What do you think about the current market?"}
    ])
    print(f"Chat response: {chat_response}")