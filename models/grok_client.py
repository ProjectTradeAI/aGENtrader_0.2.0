"""
aGENtrader v0.2.2 - Grok Client Module

This module provides integration with xAI's Grok models for AI text generation,
following a similar pattern to OpenAI's API but using the xAI endpoints.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union
import time

# Import OpenAI for SDK compatibility
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logger = logging.getLogger("grok_client")

class GrokClient:
    """
    Client for interacting with xAI's Grok models.
    Uses OpenAI's Python SDK with xAI's base URL.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-2-1212",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60
    ):
        """
        Initialize the Grok client.
        
        Args:
            api_key: xAI API key (defaults to XAI_API_KEY environment variable)
            model: Grok model to use (default: grok-2-1212)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens in completion (default: 1024)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key or os.environ.get("XAI_API_KEY", "")
        if not self.api_key:
            logger.warning("No xAI API key provided. Set XAI_API_KEY environment variable or pass api_key parameter.")
            
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Initialize OpenAI client if available
        self.client = None
        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1"
            )
        else:
            logger.warning("OpenAI SDK not available. Install with 'pip install openai' or 'npm install openai'")
            
        # Record initialization status
        self.initialized = bool(self.api_key and (self.client or not OPENAI_AVAILABLE))
        logger.info(f"GrokClient initialized with model {model}, SDK available: {OPENAI_AVAILABLE}")
        
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_response: bool = False
    ) -> str:
        """
        Generate text using Grok model.
        
        Args:
            prompt: Text prompt to generate from
            model: Override default model if provided
            temperature: Override default temperature if provided
            max_tokens: Override default max_tokens if provided
            json_response: Whether to request and parse a JSON response
            
        Returns:
            Generated text string
        """
        if not self.initialized:
            raise ValueError("GrokClient not properly initialized. Check API key and dependencies.")
            
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        # SDK-based approach (preferred)
        if self.client:
            try:
                response_format = {"type": "json_object"} if json_response else None
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"Error using Grok via SDK: {str(e)}")
                raise ValueError(f"Grok API error: {str(e)}")
        
        # Fallback to direct API calls if SDK not available
        else:
            # Construct API URL and headers
            api_url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Construct request body
            request_body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if json_response:
                request_body["response_format"] = {"type": "json_object"}
                
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=request_body,
                    timeout=self.timeout
                )
                
                # Check for successful response
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError) as e:
                        logger.error(f"Error parsing Grok response: {str(e)}")
                        raise ValueError(f"Failed to parse Grok response: {str(e)}")
                else:
                    logger.error(f"Grok API error: {response.status_code}, {response.text}")
                    raise ValueError(f"Grok API returned error {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                logger.error(f"Request error using Grok API: {str(e)}")
                raise ValueError(f"Grok API request failed: {str(e)}")
    
    def analyze_sentiment(
        self,
        text: str,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment in provided text.
        
        Args:
            text: Text to analyze for sentiment
            temperature: Optional temperature override
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # Ensure temperature is valid (must be positive for Grok API)
        if temperature is not None and temperature < 0:
            # Handle negative temperature specially
            import random
            temperature = 0.6 + (random.random() * 0.3)  # Random between 0.6-0.9
            logger.info(f"Converting negative temperature to valid value: {temperature:.2f}")
        # Construct sentiment analysis prompt
        prompt = f"""
        Analyze the market sentiment in the following text.
        
        Text: {text}
        
        Provide a detailed analysis including:
        1. Overall sentiment score (0-100, where 0 is extremely bearish, 50 is neutral, 100 is extremely bullish)
        2. Key factors influencing the sentiment
        3. Confidence in your assessment (0-100%)
        4. Potential sentiment biases in the data
        
        Return your analysis as a JSON object with the following structure:
        {{
            "sentiment_score": [0-100],
            "sentiment_label": "bearish"/"neutral"/"bullish",
            "key_factors": [list of factors],
            "confidence": [0-100],
            "biases": [list of potential biases],
            "reasoning": "detailed explanation of sentiment assessment"
        }}
        
        Only return a valid JSON object, nothing else.
        """
        
        try:
            temperature = temperature if temperature is not None else 0.4  # Lower temperature for more consistent results
            response_str = self.generate(prompt, temperature=temperature, json_response=True)
            
            # Parse JSON response
            if isinstance(response_str, str):
                try:
                    result = json.loads(response_str)
                    
                    # Validate required fields
                    required_fields = ["sentiment_score", "sentiment_label", "confidence", "reasoning"]
                    for field in required_fields:
                        if field not in result:
                            raise ValueError(f"Missing required field '{field}' in sentiment analysis response")
                            
                    # Normalize response
                    result["sentiment_score"] = max(0, min(100, result["sentiment_score"]))
                    result["confidence"] = max(0, min(100, result["confidence"]))
                    
                    # Map sentiment_label to standard format if needed
                    if result["sentiment_label"].lower() not in ["bullish", "bearish", "neutral"]:
                        # Map other labels to our standard ones
                        score = result["sentiment_score"]
                        if score >= 60:
                            result["sentiment_label"] = "bullish"
                        elif score <= 40:
                            result["sentiment_label"] = "bearish"
                        else:
                            result["sentiment_label"] = "neutral"
                    
                    # Add timestamp
                    result["timestamp"] = time.time()
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding sentiment analysis JSON: {str(e)}")
                    raise ValueError(f"Invalid sentiment analysis response format: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {str(e)}")
            raise ValueError(f"Sentiment analysis failed: {str(e)}")
            
        # Default return in case all other paths fail
        return {
            "sentiment_score": 50,
            "sentiment_label": "neutral",
            "confidence": 0,
            "reasoning": "Failed to complete sentiment analysis",
            "error": "Processing error",
            "timestamp": time.time()
        }

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test Grok client
    client = GrokClient()
    
    # Test generation
    try:
        response = client.generate(
            "What factors are currently affecting Bitcoin price?"
        )
        print(f"Grok response: {response}")
    except Exception as e:
        print(f"Generation error: {e}")
    
    # Test sentiment analysis
    try:
        sentiment = client.analyze_sentiment(
            "Bitcoin has been showing strong signs of recovery amid institutional adoption, with positive on-chain metrics and decreasing selling pressure."
        )
        print(f"Sentiment analysis: {json.dumps(sentiment, indent=2)}")
    except Exception as e:
        print(f"Sentiment analysis error: {e}")