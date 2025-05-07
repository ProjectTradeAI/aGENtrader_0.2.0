"""
aGENtrader v0.2.2 - Grok Sentiment Client Module

This module provides specialized sentiment analysis functionality using the 
Grok model, extending the base GrokClient with sentiment-specific methods.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import time

# Import the base GrokClient
from models.grok_client import GrokClient

# Configure logging
logger = logging.getLogger("grok_sentiment_client")

class GrokSentimentClient:
    """
    Specialized client for sentiment analysis using xAI's Grok models.
    Extends GrokClient with specific sentiment analysis capabilities.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-2-1212",
        temperature: float = 0.5
    ):
        """
        Initialize the Grok sentiment client.
        
        Args:
            api_key: xAI API key (defaults to XAI_API_KEY environment variable)
            model: Grok model to use (default: grok-2-1212)
            temperature: Sampling temperature (default: 0.5, lower for more consistent results)
        """
        # Initialize the base Grok client
        self.client = GrokClient(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=2048  # Larger context for sentiment analysis
        )
        
        self.model = model
        self.temperature = temperature
        
        # Add an enabled flag that sentiment_analyst_agent.py checks
        self.enabled = True
        
        # Record initialization status
        self.initialized = self.client.initialized
        
        if self.initialized:
            logger.info(f"GrokSentimentClient initialized with model {model}")
        else:
            logger.warning("GrokSentimentClient initialization failed. Check API key and client.")
    
    def analyze_sentiment(
        self, 
        text: str,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment in the provided text.
        
        Args:
            text: Text to analyze for sentiment
            temperature: Optional temperature override
            
        Returns:
            Dictionary with sentiment analysis results
        """
        return self.client.analyze_sentiment(text, temperature)
    
    def convert_sentiment_to_signal(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a sentiment analysis result to a trading signal format.
        
        Args:
            sentiment_data: Dictionary with sentiment analysis results
            
        Returns:
            Dictionary with trading signal format
        """
        if not sentiment_data:
            return {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": "No sentiment data available"
            }
            
        # Extract sentiment score and label
        sentiment_score = sentiment_data.get("sentiment_score", 50)
        sentiment_label = sentiment_data.get("sentiment_label", "neutral").lower()
        confidence = sentiment_data.get("confidence", 60)
        reasoning = sentiment_data.get("reasoning", "")
        
        # Map sentiment to trading signal
        signal = "NEUTRAL"
        if sentiment_label == "bullish" or sentiment_score >= 65:
            signal = "BUY"
        elif sentiment_label == "bearish" or sentiment_score <= 35:
            signal = "SELL"
            
        # If sentiment is close to neutral but has high confidence, still use NEUTRAL
        if sentiment_score > 40 and sentiment_score < 60:
            signal = "NEUTRAL"
            
        # If very close to neutral (45-55), reduce confidence
        if 45 <= sentiment_score <= 55:
            confidence = min(confidence, 70)
            
        # Scale confidence based on how extreme the sentiment is
        if signal != "NEUTRAL":
            # Stronger sentiment should have higher confidence
            sentiment_strength = abs(sentiment_score - 50) / 50  # 0.0 to 1.0
            # Blend original confidence with sentiment strength
            confidence = (confidence * 0.7) + (sentiment_strength * 100 * 0.3)
            # Ensure within bounds
            confidence = max(min(confidence, 100), 0)
            
        return {
            "signal": signal,
            "confidence": round(confidence),
            "reasoning": reasoning,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "source": "grok_sentiment"
        }
    
    def analyze_market_news(
        self,
        news_items: List[str],
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment from a list of news headlines or articles.
        
        Args:
            news_items: List of news headlines or articles
            temperature: Optional temperature override
            
        Returns:
            Dictionary with market news sentiment analysis
        """
        # Ensure temperature is valid (must be positive for Grok API)
        if temperature is not None and temperature < 0:
            # Handle negative temperature specially
            import random
            temperature = 0.6 + (random.random() * 0.3)  # Random between 0.6-0.9
            logger.info(f"Converting negative temperature to valid value: {temperature:.2f}")
            
        # Combine news items into a single context
        context = "\n".join([f"- {item}" for item in news_items])
        
        prompt = f"""
        Analyze the market sentiment in these news items:
        
        {context}
        
        As a market sentiment analyst, evaluate the overall tone of these news items and determine:
        1. The general market sentiment (bullish, bearish, or neutral)
        2. The strength of that sentiment (on a scale of 0-100)
        3. The key points supporting your analysis
        4. Your confidence in this assessment (0-100%)
        
        Return ONLY a valid JSON object with this structure:
        {{
            "sentiment_label": "bullish"/"bearish"/"neutral",
            "sentiment_score": [0-100],
            "key_points": [list of main points affecting sentiment],
            "confidence": [0-100],
            "reasoning": "explanation of your analysis"
        }}
        """
        
        try:
            # Use lower temperature for more consistent results
            actual_temp = temperature if temperature is not None else 0.5
            response_str = self.client.generate(prompt, temperature=actual_temp, json_response=True)
            
            # Parse JSON response
            try:
                result = json.loads(response_str)
                
                # Validate required fields
                required_fields = ["sentiment_label", "sentiment_score", "confidence", "reasoning"]
                for field in required_fields:
                    if field not in result:
                        result[field] = "unknown" if field != "sentiment_score" and field != "confidence" else 50
                
                # Convert sentiment analysis to a tradable signal
                signal_result = self.convert_sentiment_to_signal(result)
                
                # Return the complete result
                return signal_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding market news sentiment JSON: {str(e)}")
                return {
                    "signal": "NEUTRAL",
                    "confidence": 50,
                    "reasoning": f"Error parsing market news sentiment: {str(e)}",
                    "error": True
                }
                
        except Exception as e:
            logger.error(f"Error analyzing market news sentiment: {str(e)}")
            return {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": f"Error analyzing market news: {str(e)}",
                "error": True
            }
    
    def analyze_and_get_signal(
        self, 
        text: str,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment and convert directly to a trading signal.
        
        Args:
            text: Text to analyze for sentiment
            temperature: Optional temperature override
            
        Returns:
            Dictionary with trading signal format
        """
        try:
            # First analyze sentiment
            sentiment_result = self.analyze_sentiment(text, temperature)
            
            # Then convert to signal format
            return self.convert_sentiment_to_signal(sentiment_result)
            
        except Exception as e:
            logger.error(f"Error in analyze_and_get_signal: {str(e)}")
            return {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": f"Error analyzing sentiment: {str(e)}",
                "error": True
            }

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test sentiment client
    client = GrokSentimentClient()
    
    test_texts = [
        "Bitcoin has surged 15% over the past week, with on-chain metrics showing strong accumulation from institutional investors. Exchange outflows have reached yearly highs.",
        "Market sentiment for cryptocurrencies remains mixed as Bitcoin consolidates around the $48,000 level. Volume has been declining and the RSI shows neutral momentum.",
        "Analysts are increasingly bearish on Bitcoin following the break of critical support at $42,000. Rising interest rates and regulatory concerns have dampened investor enthusiasm."
    ]
    
    for i, text in enumerate(test_texts):
        try:
            print(f"\nTest {i+1}:")
            print(f"Text: {text[:50]}...")
            
            # Get signal
            result = client.analyze_and_get_signal(text)
            print(f"Signal: {result['signal']}")
            print(f"Confidence: {result['confidence']}%")
            print(f"Reasoning: {result['reasoning'][:100]}...")
            
        except Exception as e:
            print(f"Error: {e}")