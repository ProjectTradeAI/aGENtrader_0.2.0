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
                            "You are a cryptocurrency market sentiment expert providing detailed, specific analysis. "
                            "IMPORTANT: Avoid generic observations like 'the text is factual in nature.' "
                            "Be specific, decisive, and reference actual content in your analysis.\n\n"
                            
                            "ANALYZE THE PROVIDED TEXT AND DELIVER THE FOLLOWING:\n"
                            "1. A rating from 1 to 5 (1=very bearish, 3=neutral, 5=very bullish)\n"
                            "2. A confidence score between 0 and 1 based on the specificity and relevance of the data\n"
                            "3. A clear sentiment classification as 'bullish', 'neutral', or 'bearish'\n"
                            "4. A detailed reasoning that references specific indicators, metrics, or statements\n\n"
                            
                            "GUIDELINES:\n"
                            "- Identify any contradictions between price action and sentiment indicators\n"
                            "- Explicitly note when technical factors contradict fundamental factors\n"
                            "- Prioritize specificity over generalization in your analysis\n"
                            "- If the data shows mixed signals, explain the contradiction\n"
                            "- Include specific data points that influenced your conclusion\n\n"
                            
                            "Respond with JSON in this format: "
                            "{ 'rating': number, 'confidence': number, 'sentiment': string, 'reasoning': string, "
                            "'key_factors': [string, string], 'contradictions': string }"
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
                            "You are a crypto market sentiment expert providing detailed, specific analysis. "
                            "IMPORTANT: Avoid generic observations like 'the text is factual in nature.' Be specific and decisive.\n\n"
                            
                            "ANALYZE THE NEWS ITEMS AND PROVIDE:\n"
                            "1. An overall market sentiment (bullish, neutral, or bearish) with specific justification\n"
                            "2. A confidence score from 0-1 based on the quality and consistency of the data\n"
                            "3. Individual sentiment analysis for each news item (bullish, neutral, or bearish)\n"
                            "4. A rating from 1-5 for each item (1=very bearish, 3=neutral, 5=very bullish)\n"
                            "5. A specific summary that references actual content, not generic observations\n\n"
                            
                            "GUIDELINES:\n"
                            "- Identify any contradictions between different news items\n"
                            "- Note when news is suggesting a trend change or continuation\n"
                            "- Consider market impact beyond just the factual content\n"
                            "- Be critical and interpretive, not just descriptive\n\n"
                            
                            "Respond with JSON formatted as: "
                            "{ 'overall_sentiment': string, 'confidence': number, 'summary': string, "
                            "'items': [{ 'text': string, 'sentiment': string, 'rating': number, 'reasoning': string }] }"
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
            Dictionary with signal, confidence, reasoning, and additional metadata fields
        """
        # Extract data from sentiment result
        if "overall_sentiment" in sentiment_result:
            # This is from analyze_market_news
            sentiment = sentiment_result.get("overall_sentiment", "neutral").lower()
            confidence = sentiment_result.get("confidence", 0.5)
            reasoning = sentiment_result.get("summary", "No summary provided")
            
            # Extract additional metadata if available
            items = sentiment_result.get("items", [])
            total_ratings = sum(item.get("rating", 3) for item in items) if items else 0
            avg_rating = total_ratings / len(items) if items else 3
            
            # Collect key signals from news items
            key_signals = []
            for item in items[:3]:  # Use top 3 items
                if "text" in item and "sentiment" in item:
                    key_signals.append(f"{item['text'][:50]}... ({item['sentiment']})")
        else:
            # This is from analyze_sentiment
            sentiment = sentiment_result.get("sentiment", "neutral").lower()
            confidence = sentiment_result.get("confidence", 0.5)
            reasoning = sentiment_result.get("reasoning", "No reasoning provided")
            avg_rating = sentiment_result.get("rating", 3)
            
            # Collect key factors if available
            key_signals = sentiment_result.get("key_factors", [])
            
            # Get contradictions if available
            contradictions = sentiment_result.get("contradictions", "")
            if contradictions and len(contradictions) > 5:
                if "reasoning" in sentiment_result:
                    reasoning += f" Contradictions: {contradictions}"
            
        # Convert sentiment to signal based on updated sentiment naming
        signal_mapping = {
            "positive": "BUY",
            "bullish": "BUY",
            "neutral": "NEUTRAL",  # Changed from HOLD to NEUTRAL for consistency
            "bearish": "SELL",
            "negative": "SELL"
        }
        
        # Map sentiment to signal, defaulting to NEUTRAL
        signal = signal_mapping.get(sentiment.lower(), "NEUTRAL")
        
        # Scale confidence to percentage (0-100)
        confidence_pct = int(confidence * 100)
        
        # Create result with enhanced information
        result = {
            "signal": signal,
            "confidence": confidence_pct,
            "reasoning": reasoning,
            "rating": avg_rating  # Include the numerical rating
        }
        
        # Add key signals if we have them
        if key_signals:
            result["key_signals"] = key_signals
        
        # Add timestamp and request_id for traceability
        result["timestamp"] = datetime.now().isoformat()
        result["request_id"] = str(uuid.uuid4())
        
        # Add actual_temperature if available
        if "actual_temperature" in sentiment_result:
            result["actual_temperature"] = sentiment_result["actual_temperature"]
        
        # Add source information for debugging
        source_type = "market_news" if "overall_sentiment" in sentiment_result else "text_sentiment"
        result["source_type"] = source_type
        
        return result