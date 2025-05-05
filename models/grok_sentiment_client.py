"""
aGENtrader v2 Grok Sentiment Analysis Client

This module interfaces with xAI's Grok API to provide sentiment analysis 
on market-related text content. It uses the same patterns and practices as 
the OpenAI API for easy integration.
"""
import os
import logging
import json
import random
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import time

# Try to import OpenAI client which is used for the xAI API
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available; Grok sentiment analysis will not function")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GrokSentimentClient")

class GrokSentimentClient:
    """
    Client for interfacing with xAI's Grok API for sentiment analysis.
    
    This class provides methods to analyze text for sentiment and extract
    key insights using Grok models.
    """
    
    def __init__(self):
        """Initialize the Grok sentiment client."""
        # Check API key availability
        self.api_key = os.environ.get("XAI_API_KEY")
        
        if not self.api_key:
            logger.warning("XAI_API_KEY not available in environment. Grok sentiment analysis disabled.")
            self.enabled = False
            return
            
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not installed. Grok sentiment analysis disabled.")
            self.enabled = False
            return
            
        # Initialize OpenAI client with the xAI base URL
        try:
            self.client = OpenAI(
                base_url="https://api.x.ai/v1",
                api_key=self.api_key
            )
            logger.info("Grok sentiment client initialized successfully")
            self.enabled = True
        except Exception as e:
            logger.error(f"Failed to initialize Grok client: {str(e)}")
            self.enabled = False
    
    def analyze_sentiment(self, text: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Analyze the sentiment of a text.
        
        Args:
            text: The text to analyze
            temperature: The temperature to use for generation (0.0 to 1.0)
            
        Returns:
            Dictionary containing sentiment analysis with keys:
            - rating: 1-5 star rating (5 being most positive)
            - confidence: 0-1 confidence score
            - sentiment: 'positive', 'neutral', or 'negative'
            - reasoning: Brief explanation of the sentiment
            - actual_temperature: The temperature that was actually used
        """
        if not self.enabled:
            logger.warning("Grok sentiment analysis is disabled. Returning neutral sentiment.")
            return {
                "rating": 3,
                "confidence": 0.5,
                "sentiment": "neutral",
                "reasoning": "Grok sentiment analysis is disabled.",
                "actual_temperature": 0.0
            }
            
        try:
            # Handle dynamic temperature (-1 means use random temperature between 0.6 and 0.9)
            actual_temperature = temperature
            if temperature == -1:
                actual_temperature = round(0.6 + 0.3 * random.random(), 2)  # Random between 0.6 and 0.9
                logger.info(f"Using dynamic temperature: {actual_temperature}")
            
            response = self.client.chat.completions.create(
                model="grok-2-1212",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial sentiment analysis expert. Analyze the sentiment of the "
                            "text and provide a rating from 1 to 5 stars (5 being most positive), a confidence "
                            "score between 0 and 1, and a brief explanation. Categorize the sentiment as "
                            "'positive', 'neutral', or 'negative'. Respond with JSON in this format: "
                            "{ 'rating': number, 'confidence': number, 'sentiment': string, 'reasoning': string }"
                        )
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                response_format={"type": "json_object"},
                temperature=actual_temperature
            )
            
            # Check for empty or invalid response
            if not response or not response.choices or not response.choices[0].message or not response.choices[0].message.content:
                raise ValueError("Empty or invalid response received from Grok API")
            
            content = response.choices[0].message.content
            
            # Check if content is valid before parsing JSON
            if not content or not content.strip():
                raise ValueError("Empty content received from Grok API")
                
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Grok API: {e}, Content: {content[:100]}...")
                raise ValueError(f"Invalid JSON format in API response: {str(e)}")
            
            # Validate response format and enforce constraints
            rating = int(max(1, min(5, round(result.get("rating", 3)))))
            confidence = float(max(0, min(1, result.get("confidence", 0.5))))
            sentiment = result.get("sentiment", "neutral").lower()
            
            # Ensure sentiment is one of the valid values
            if sentiment not in ["positive", "neutral", "negative"]:
                sentiment = "neutral"
                
            reasoning = result.get("reasoning", "No reasoning provided")
                
            return {
                "rating": rating,
                "confidence": confidence,
                "sentiment": sentiment,
                "reasoning": reasoning,
                "actual_temperature": actual_temperature
            }
                
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {str(e)}")
            # Return neutral sentiment on error with the actual_temperature
            return {
                "rating": 3,
                "confidence": 0.5,
                "sentiment": "neutral",
                "reasoning": f"Error during analysis: {str(e)}",
                "actual_temperature": temperature  # Use the requested temperature even if it failed
            }
    
    def analyze_market_news(self, news_items: List[str], temperature: float = 0.7) -> Dict[str, Any]:
        """
        Analyze sentiment from a list of market news items.
        
        Args:
            news_items: List of news headlines or short articles
            temperature: The temperature to use for generation (0.0 to 1.0 or -1 for dynamic)
            
        Returns:
            Dictionary with overall sentiment analysis and 
            individual sentiment for each news item
        """
        if not self.enabled:
            logger.warning("Grok sentiment analysis is disabled. Returning neutral sentiment.")
            return {
                "overall_sentiment": "neutral",
                "confidence": 0.5,
                "items": [{"text": item, "sentiment": "neutral", "rating": 3} for item in news_items]
            }
            
        try:
            # Combine news items into a single prompt
            combined_text = "\n".join([f"- {item}" for item in news_items])
            
            # Handle dynamic temperature (-1 means use random temperature between 0.6 and 0.9)
            actual_temperature = temperature
            if temperature == -1:
                actual_temperature = round(0.6 + 0.3 * random.random(), 2)  # Random between 0.6 and 0.9
                logger.info(f"Using dynamic temperature for news analysis: {actual_temperature}")
            
            response = self.client.chat.completions.create(
                model="grok-2-1212",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial market analyst specializing in crypto sentiment analysis. "
                            "Analyze the following news items and provide: "
                            "1. An overall market sentiment (positive, neutral, or negative) "
                            "2. A confidence score from 0-1 "
                            "3. Individual sentiment for each news item (positive, neutral, or negative) "
                            "4. A rating from 1-5 for each item "
                            "5. A brief summary of the overall sentiment implications "
                            "Respond with JSON formatted as: "
                            "{ 'overall_sentiment': string, 'confidence': number, 'summary': string, "
                            "'items': [{ 'text': string, 'sentiment': string, 'rating': number }] }"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these market news items:\n{combined_text}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=actual_temperature
            )
            
            # Check for empty or invalid response
            if not response or not response.choices or not response.choices[0].message or not response.choices[0].message.content:
                raise ValueError("Empty or invalid response received from Grok API")
            
            content = response.choices[0].message.content
            
            # Check if content is valid before parsing JSON
            if not content or not content.strip():
                raise ValueError("Empty content received from Grok API")
                
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Grok API: {e}, Content: {content[:100]}...")
                raise ValueError(f"Invalid JSON format in API response: {str(e)}")
            
            # Add actual temperature to the result for tracking
            result["actual_temperature"] = actual_temperature
            
            # Add unique request ID and timestamp
            result["request_id"] = str(uuid.uuid4())
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error during market news analysis: {str(e)}")
            # Return neutral sentiment on error
            error_result = {
                "overall_sentiment": "neutral",
                "confidence": 0.5,
                "summary": f"Error during analysis: {str(e)}",
                "items": [{"text": item, "sentiment": "neutral", "rating": 3} for item in news_items],
                "actual_temperature": temperature,  # Use the requested temperature value
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            return error_result
            
    def convert_sentiment_to_signal(self, sentiment_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert sentiment analysis result to a trading signal format.
        
        Args:
            sentiment_result: The result from analyze_sentiment or analyze_market_news
            
        Returns:
            Dictionary with signal, confidence, and reasoning fields
        """
        # Extract data from sentiment result
        if "overall_sentiment" in sentiment_result:
            # This is from analyze_market_news
            sentiment = sentiment_result.get("overall_sentiment", "neutral").lower()
            confidence = sentiment_result.get("confidence", 0.5)
            reasoning = sentiment_result.get("summary", "No summary provided")
        else:
            # This is from analyze_sentiment
            sentiment = sentiment_result.get("sentiment", "neutral").lower()
            confidence = sentiment_result.get("confidence", 0.5)
            reasoning = sentiment_result.get("reasoning", "No reasoning provided")
            
        # Convert sentiment to signal
        signal_mapping = {
            "positive": "BUY",
            "neutral": "HOLD",
            "negative": "SELL"
        }
        
        signal = signal_mapping.get(sentiment, "HOLD")
        
        # Scale confidence to percentage (0-100)
        confidence_pct = int(confidence * 100)
        
        # Include actual_temperature if it exists in the sentiment_result
        result = {
            "signal": signal,
            "confidence": confidence_pct,
            "reasoning": reasoning
        }
        
        # Add timestamp and request_id for traceability
        result["timestamp"] = datetime.now().isoformat()
        result["request_id"] = str(uuid.uuid4())
        
        # Add actual_temperature if available
        if "actual_temperature" in sentiment_result:
            result["actual_temperature"] = sentiment_result["actual_temperature"]
        
        return result