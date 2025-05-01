"""
Sentiment Analyst Agent Module

This agent analyzes market sentiment from various sources including:
- Social media trends
- News sentiment
- Market fear/greed indicators
- Community bullish/bearish sentiment

The agent provides sentiment signals with confidence scores that can be
integrated into the trading decision process.
"""

import os
import sys
import json
import logging
import random
import time
import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sentiment_analyst')

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import required modules
from models.llm_client import LLMClient
from data.database import DatabaseConnector
from utils.config import get_config
from agents.base_agent import BaseAnalystAgent

# Define sentiment states as enum for type safety
class SentimentState(Enum):
    """Enum representing possible sentiment states"""
    BULLISH = auto()
    NEUTRAL = auto()
    BEARISH = auto()
    UNKNOWN = auto()
    
    @classmethod
    def from_string(cls, sentiment_str: str) -> 'SentimentState':
        """Convert a string to a SentimentState enum value"""
        mapping = {
            "bullish": cls.BULLISH,
            "neutral": cls.NEUTRAL,
            "bearish": cls.BEARISH
        }
        return mapping.get(sentiment_str.lower(), cls.UNKNOWN)
    
    def to_action(self) -> str:
        """Convert sentiment state to trading action"""
        mapping = {
            self.BULLISH: "BUY",
            self.NEUTRAL: "HOLD",
            self.BEARISH: "SELL",
            self.UNKNOWN: "HOLD"
        }
        return mapping[self]
    
    def __str__(self) -> str:
        """String representation of the sentiment state"""
        return self.name.title()


class SentimentAnalystAgent(BaseAnalystAgent):
    """
    Sentiment Analyst Agent that analyzes market sentiment.
    
    This agent:
    - Fetches sentiment data from various configurable sources
    - Analyzes sentiment for specific assets
    - Provides structured sentiment signals with confidence scores
    - Supports multiple data sources and sentiment calculation methods
    """
    
    def __init__(self):
        """Initialize the Sentiment Analyst Agent."""
        # Initialize the base agent
        super().__init__(agent_name="sentiment_analyst")
        
        # Get agent and trading configuration
        self.agent_config = self.get_agent_config()
        self.trading_config = self.get_trading_config()
        
        # Initialize LLM client with agent-specific configuration
        self.llm_client = LLMClient(agent_name="sentiment_analyst")
        
        # Initialize database connector
        self.db = DatabaseConnector()
        
        # Helper method for timestamps
        self.format_timestamp = lambda: datetime.datetime.now().isoformat()
        
        # Set up sentiment source and mode
        self.data_mode = self.agent_config.get("data_mode", "mock")
        self.api_source = self.agent_config.get("api_source", "lunarcrush")
        
        # Load confidence mappings
        self.confidence_map = self.agent_config.get("confidence_map", {
            "Bullish": 0.7,
            "Neutral": 0.5,
            "Bearish": 0.6
        })
        
        # Set up storage for recent sentiment data
        self.sentiment_history = []
        self.sentiment_log_file = os.path.join(parent_dir, "logs/sentiment_feed.jsonl")
        self.max_history_size = 100
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.sentiment_log_file), exist_ok=True)
        
        # Load existing sentiment history if available
        self._load_sentiment_history()
        
        # Set default parameters
        self.default_symbol = self.trading_config.get("default_pair", "BTC/USDT").replace("/", "")
        self.default_interval = self.trading_config.get("default_interval", "1h")
        
        # Use the global logger defined at the top of the file
        logger.info(f"Sentiment Analyst Agent initialized with data mode: {self.data_mode}")
    
    def _load_sentiment_history(self) -> None:
        """Load sentiment history from the log file."""
        if not os.path.exists(self.sentiment_log_file):
            logger.info(f"No sentiment history found at {self.sentiment_log_file}")
            return
        
        try:
            with open(self.sentiment_log_file, 'r') as f:
                self.sentiment_history = [json.loads(line) for line in f.readlines()]
            
            # Keep only the most recent entries
            if len(self.sentiment_history) > self.max_history_size:
                self.sentiment_history = self.sentiment_history[-self.max_history_size:]
                
            logger.info(f"Loaded {len(self.sentiment_history)} sentiment history records")
        except Exception as e:
            logger.error(f"Error loading sentiment history: {e}")
    
    def _save_sentiment_data(self, data: Dict[str, Any]) -> None:
        """
        Save sentiment data to the history log file.
        
        Args:
            data: Sentiment data dictionary
        """
        try:
            # Add the data to the history
            self.sentiment_history.append(data)
            
            # Keep only the most recent entries
            if len(self.sentiment_history) > self.max_history_size:
                self.sentiment_history = self.sentiment_history[-self.max_history_size:]
            
            # Append to the log file
            with open(self.sentiment_log_file, 'a') as f:
                f.write(json.dumps(data) + '\n')
                
        except Exception as e:
            logger.error(f"Error saving sentiment data: {e}")
    
    def analyze(self, 
               symbol: Optional[Union[str, Dict[str, Any]]] = None, 
               market_data: Optional[Dict[str, Any]] = None,
               interval: Optional[str] = None,
               **kwargs) -> Dict[str, Any]:
        """
        Perform sentiment analysis for the given symbol and interval.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT') or market_data dictionary
            market_data: Pre-fetched market data (optional)
            interval: Time interval (e.g., '1h', '15m')
            **kwargs: Additional parameters specific to the agent
            
        Returns:
            Dictionary with sentiment analysis results
        """
        # Handle case where market_data is passed as first parameter (common in test harness)
        if isinstance(symbol, dict) and 'symbol' in symbol:
            # First parameter is actually market_data
            market_data = symbol
            symbol = market_data.get('symbol')
            if 'interval' in market_data and not interval:
                interval = market_data.get('interval')
                
        # Use default values if not provided
        symbol_str = symbol or self.default_symbol
        interval_str = interval or self.default_interval
        
        # Log analysis start
        logger.info(f"Starting sentiment analysis for {symbol_str} at {interval_str} interval")
        
        # Initialize result structure
        result = {
            "symbol": symbol_str,
            "interval": interval_str,
            "timestamp": self.format_timestamp(),
            "sentiment_source": self.data_mode,
            "sentiment_data": {},
            "analysis": {}
        }
        
        try:
            # Get sentiment data based on configured mode
            sentiment_data = self.get_sentiment_data(symbol_str, interval_str, **kwargs)
            result["sentiment_data"] = sentiment_data
            
            # Process sentiment data into a standardized analysis result
            analysis = self.process_sentiment_data(sentiment_data, symbol_str)
            result["analysis"] = analysis
            
            # Validate the result
            result = self.validate_result(result)
            
            # Save sentiment data to history
            self._save_sentiment_data(result)
            
            # Log successful analysis
            logger.info(f"Sentiment analysis completed for {symbol_str}: {analysis.get('sentiment', 'UNKNOWN')} (Confidence: {analysis.get('confidence', 0):.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing sentiment analysis: {e}")
            
            # Return a neutral result in case of error
            result["analysis"] = {
                "sentiment": "NEUTRAL",
                "confidence": 0.3,
                "action": "HOLD",
                "reason": f"Error in sentiment analysis: {str(e)}"
            }
            result["error"] = str(e)
            
            return result
    
    def get_sentiment_data(self, 
                         symbol: str,
                         interval: str,
                         **kwargs) -> Dict[str, Any]:
        """
        Get sentiment data from the configured source.
        
        This method will call the appropriate data source based on configuration.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with raw sentiment data
        """
        # Select the appropriate data source method based on configuration
        if self.data_mode == "mock":
            return self._get_mock_sentiment_data(symbol, interval, **kwargs)
        elif self.data_mode == "api" and self.api_source == "lunarcrush":
            return self._get_lunarcrush_sentiment_data(symbol, interval, **kwargs)
        elif self.data_mode == "scrape":
            return self._get_scraped_sentiment_data(symbol, interval, **kwargs)
        else:
            logger.warning(f"Unknown sentiment data mode: {self.data_mode}, falling back to mock data")
            return self._get_mock_sentiment_data(symbol, interval, **kwargs)
    
    def _get_mock_sentiment_data(self, 
                               symbol: str,
                               interval: str,
                               **kwargs) -> Dict[str, Any]:
        """
        Generate mock sentiment data for testing.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with mock sentiment data
        """
        # Check if we should use fixed rotation or random
        use_rotation = kwargs.get("use_rotation", True)
        
        # Use symbol and timestamp to create a deterministic pattern if rotating
        if use_rotation:
            # Create a simple deterministic pattern based on the symbol and current time
            hash_base = symbol + str(int(time.time() / (3600 * 24)))  # Changes daily
            hash_val = sum(ord(c) for c in hash_base) % 3
            
            # Map to sentiment states
            sentiment_map = {
                0: "Bullish",
                1: "Neutral",
                2: "Bearish"
            }
            
            sentiment = sentiment_map[hash_val]
            
            # Add slight randomness to the confidence
            base_confidence = self.confidence_map.get(sentiment, 0.5)
            confidence = base_confidence + (random.random() * 0.2 - 0.1)  # +/- 0.1
            confidence = round(max(0.1, min(0.95, confidence)), 2)  # Ensure in range [0.1, 0.95]
            
            sources = ["twitter_analysis", "reddit_sentiment", "news_headlines", "community_mood"]
            reason = f"Based on {random.choice(sources)} for {symbol}"
            
        else:
            # Completely random sentiment
            sentiment = random.choice(["Bullish", "Neutral", "Bearish"])
            confidence = round(random.uniform(0.3, 0.9), 2)
            reason = "Random sentiment generation for testing"
        
        # Create mock sources with varying sentiment
        mock_sources = {
            "social_media": {
                "twitter": {
                    "sentiment": sentiment,
                    "volume": random.randint(500, 5000),
                    "change_24h": random.uniform(-10, 10)
                },
                "reddit": {
                    "sentiment": random.choice(["Bullish", "Neutral", "Bearish"]),
                    "post_count": random.randint(10, 100),
                    "top_topics": ["price", "technology", "adoption"]
                }
            },
            "news": {
                "sentiment": random.choice(["Bullish", "Neutral", "Bearish"]),
                "article_count": random.randint(5, 30),
                "top_headlines": [
                    f"{symbol} sees increased adoption in {random.choice(['Asia', 'Europe', 'North America'])}",
                    f"Market analysts predict {random.choice(['bullish', 'bearish'])} trend for {symbol}",
                    f"New {symbol} development announced by team"
                ]
            },
            "market_indicators": {
                "fear_greed_index": random.randint(0, 100),
                "long_short_ratio": random.uniform(0.5, 2.0),
                "funding_rate": random.uniform(-0.01, 0.01)
            }
        }
        
        # Return comprehensive mock sentiment data
        return {
            "timestamp": self.format_timestamp(),
            "symbol": symbol,
            "interval": interval,
            "sentiment": sentiment,
            "confidence": confidence,
            "reason": reason,
            "sources": mock_sources,
            "data_mode": "mock"
        }
    
    def _get_lunarcrush_sentiment_data(self, 
                                     symbol: str,
                                     interval: str,
                                     **kwargs) -> Dict[str, Any]:
        """
        Get sentiment data from LunarCrush API.
        
        This is a placeholder method for future implementation.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with sentiment data from LunarCrush
        """
        # This is a placeholder for future implementation
        logger.warning("LunarCrush API integration not implemented yet, falling back to mock data")
        
        # Fall back to mock data with a warning
        mock_data = self._get_mock_sentiment_data(symbol, interval, **kwargs)
        mock_data["data_mode"] = "api_fallback"
        mock_data["api_source"] = "lunarcrush"
        mock_data["warning"] = "API integration not implemented yet"
        
        return mock_data
    
    def _get_scraped_sentiment_data(self, 
                                  symbol: str,
                                  interval: str,
                                  **kwargs) -> Dict[str, Any]:
        """
        Get sentiment data from web scraping sources.
        
        This is a placeholder method for future implementation.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with sentiment data from web scraping
        """
        # This is a placeholder for future implementation
        logger.warning("Web scraping integration not implemented yet, falling back to mock data")
        
        # Fall back to mock data with a warning
        mock_data = self._get_mock_sentiment_data(symbol, interval, **kwargs)
        mock_data["data_mode"] = "scrape_fallback"
        mock_data["warning"] = "Web scraping integration not implemented yet"
        
        return mock_data
    
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize the analysis result.
        
        Args:
            result: The analysis result to validate
            
        Returns:
            Validated result dictionary
        """
        # Ensure required fields exist
        if "analysis" not in result:
            result["analysis"] = {}
            
        if "sentiment" not in result["analysis"]:
            result["analysis"]["sentiment"] = "NEUTRAL"
            
        if "confidence" not in result["analysis"]:
            result["analysis"]["confidence"] = 50
            
        if "action" not in result["analysis"]:
            result["analysis"]["action"] = "HOLD"
            
        if "reason" not in result["analysis"]:
            result["analysis"]["reason"] = "No reason provided"
            
        # Ensure confidence is within bounds
        confidence = result["analysis"]["confidence"]
        if isinstance(confidence, float) and confidence <= 1.0:
            # Convert from 0-1 scale to 0-100
            result["analysis"]["confidence"] = int(confidence * 100)
        elif isinstance(confidence, (int, float)):
            # Ensure it's within 0-100 range
            result["analysis"]["confidence"] = max(0, min(100, int(confidence)))
        else:
            # Default if not a number
            result["analysis"]["confidence"] = 50
            
        # Map 'action' to 'signal' for consistent interface with test harness
        if "action" in result["analysis"] and "signal" not in result["analysis"]:
            result["analysis"]["signal"] = result["analysis"]["action"]
            
        # Ensure reasoning field is present for test harness
        if "reason" in result["analysis"] and "reasoning" not in result["analysis"]:
            result["analysis"]["reasoning"] = result["analysis"]["reason"]
            
        return result
        
    def process_sentiment_data(self, 
                             sentiment_data: Dict[str, Any],
                             symbol: str) -> Dict[str, Any]:
        """
        Process raw sentiment data into a standardized analysis result.
        
        Args:
            sentiment_data: Raw sentiment data from any source
            symbol: Trading symbol
            
        Returns:
            Dictionary with standardized analysis result
        """
        # Extract the sentiment state from the data
        sentiment_str = sentiment_data.get("sentiment", "NEUTRAL")
        
        # Convert to SentimentState enum
        sentiment_state = SentimentState.from_string(sentiment_str)
        
        # Map to trading action
        action = sentiment_state.to_action()
        
        # Get confidence score
        confidence = sentiment_data.get("confidence", 0.5)
        
        # Get reason if available
        reason = sentiment_data.get("reason", "No reason provided")
        
        # Scale confidence according to configured map
        base_confidence = self.confidence_map.get(str(sentiment_state), 0.5)
        scaled_confidence = int(base_confidence * confidence * 100)
        
        # Cap confidence to be within valid range
        scaled_confidence = max(1, min(99, scaled_confidence))
        
        # Generate additional insights if possible
        sources = sentiment_data.get("sources", {})
        insights = []
        
        if sources:
            # Extract insights from social media if available
            social = sources.get("social_media", {})
            if social:
                twitter = social.get("twitter", {})
                if twitter:
                    insights.append(f"Twitter sentiment: {twitter.get('sentiment', 'Unknown')} with volume {twitter.get('volume', 'N/A')}")
                
                reddit = social.get("reddit", {})
                if reddit:
                    insights.append(f"Reddit sentiment: {reddit.get('sentiment', 'Unknown')} with {reddit.get('post_count', 'N/A')} posts")
            
            # Extract insights from news if available
            news = sources.get("news", {})
            if news:
                insights.append(f"News sentiment: {news.get('sentiment', 'Unknown')} with {news.get('article_count', 'N/A')} articles")
            
            # Extract insights from market indicators if available
            indicators = sources.get("market_indicators", {})
            if indicators:
                fear_greed = indicators.get("fear_greed_index")
                if fear_greed is not None:
                    fear_greed_desc = "Extreme Fear" if fear_greed < 25 else "Fear" if fear_greed < 40 else "Neutral" if fear_greed < 60 else "Greed" if fear_greed < 75 else "Extreme Greed"
                    insights.append(f"Fear & Greed Index: {fear_greed} ({fear_greed_desc})")
        
        # Create the standardized analysis result
        analysis = {
            "sentiment": str(sentiment_state),
            "action": action,
            "signal": action,  # Direct mapping for test harness
            "confidence": scaled_confidence,
            "reason": reason,
            "reasoning": reason,  # Direct mapping for test harness
            "insights": insights
        }
        
        return analysis
    
    def get_recent_sentiment_history(self, 
                                   symbol: Optional[str] = None,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sentiment history for a symbol.
        
        Args:
            symbol: Trading symbol (optional, returns all symbols if None)
            limit: Maximum number of history items to return
            
        Returns:
            List of recent sentiment data dictionaries
        """
        if not self.sentiment_history:
            return []
        
        # Filter by symbol if specified
        if symbol:
            history = [item for item in self.sentiment_history if item.get("symbol") == symbol]
        else:
            history = self.sentiment_history.copy()
        
        # Sort by timestamp (newest first) and limit
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return history[:limit]
    
    def get_sentiment_trend(self, 
                          symbol: str,
                          days: int = 7) -> Dict[str, Any]:
        """
        Calculate sentiment trend over a period of time.
        
        Args:
            symbol: Trading symbol
            days: Number of days to look back
            
        Returns:
            Dictionary with sentiment trend analysis
        """
        # Get sentiment history for the symbol
        history = self.get_recent_sentiment_history(symbol)
        
        if not history:
            return {
                "symbol": symbol,
                "trend": "UNKNOWN",
                "confidence": 0,
                "data_points": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0
            }
        
        # Count sentiment occurrences
        sentiment_counts = {
            "BULLISH": 0,
            "BEARISH": 0,
            "NEUTRAL": 0
        }
        
        for item in history:
            sentiment = item.get("analysis", {}).get("sentiment", "NEUTRAL").upper()
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        # Calculate the dominant sentiment
        max_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])
        dominant_sentiment = max_sentiment[0]
        
        # Calculate confidence based on proportion
        data_points = sum(sentiment_counts.values())
        confidence = (max_sentiment[1] / data_points) * 100 if data_points > 0 else 0
        
        return {
            "symbol": symbol,
            "trend": dominant_sentiment,
            "confidence": confidence,
            "data_points": data_points,
            "bullish_count": sentiment_counts["BULLISH"],
            "bearish_count": sentiment_counts["BEARISH"],
            "neutral_count": sentiment_counts["NEUTRAL"]
        }


# Example usage (for demonstration)
if __name__ == "__main__":
    # Create agent
    agent = SentimentAnalystAgent()
    
    # Get sentiment analysis for Bitcoin
    result = agent.analyze("BTCUSDT", None, "1h")
    
    # Print result
    print(json.dumps(result, indent=2))
    
    # Get recent history
    history = agent.get_recent_sentiment_history("BTCUSDT", limit=5)
    print(f"\nRecent Sentiment History ({len(history)} entries):")
    for entry in history:
        sentiment = entry.get("analysis", {}).get("sentiment", "UNKNOWN")
        confidence = entry.get("analysis", {}).get("confidence", 0)
        timestamp = entry.get("timestamp", "")
        print(f"  {timestamp}: {sentiment} (Confidence: {confidence})")
    
    # Get sentiment trend
    trend = agent.get_sentiment_trend("BTCUSDT")
    print(f"\nSentiment Trend: {trend['trend']} (Confidence: {trend['confidence']:.1f}%)")
    print(f"Data Points: {trend['data_points']} (Bullish: {trend['bullish_count']}, Bearish: {trend['bearish_count']}, Neutral: {trend['neutral_count']})")