"""
aGENtrader v2 Sentiment Analyst Agent

This agent is responsible for analyzing market sentiment from news and social media sources
using Grok's advanced language understanding capabilities.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union
import time
import random
from datetime import datetime, timedelta

# Add parent directory to path to allow importing from sibling directories
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import base agent class and interfaces
try:
    from agents.base_agent import AgentInterface, AnalystAgentInterface, BaseAgent, BaseAnalystAgent
except ImportError:
    from base_agent import AgentInterface, AnalystAgentInterface, BaseAgent, BaseAnalystAgent

# Import Grok sentiment client
try:
    from models.grok_sentiment_client import GrokSentimentClient
except ImportError:
    GrokSentimentClient = None
    print("Warning: GrokSentimentClient not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SentimentAnalystAgent")

class SentimentAnalystAgent(BaseAnalystAgent):
    """
    Agent that analyzes market sentiment using Grok's language model.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Sentiment Analyst Agent.
        
        Args:
            config: Configuration dictionary with optional settings
        """
        super().__init__("SentimentAnalystAgent")
        self.description = "Analyzes market sentiment from various text sources"
        
        # Initialize Grok client if available
        self.grok_client = GrokSentimentClient() if GrokSentimentClient else None
        
        if self.grok_client and not self.grok_client.enabled:
            logger.warning("Grok client not enabled. Check XAI_API_KEY and OpenAI package.")
        
        # Agent-specific configuration
        self.config = config or {}
        self.data_sources = self.config.get("data_sources", ["news", "social"])
        
        logger.info(f"Sentiment Analyst Agent initialized with {len(self.data_sources)} data sources")
        
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent configuration.
        
        Returns:
            Dictionary with agent configuration
        """
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "data_sources": self.data_sources
        }
        
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data (required by abstract interface).
        
        For the sentiment analyst, we don't need traditional market data like OHLCV candles.
        Instead, this could be extended to fetch news and social media data in a real implementation.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            **kwargs: Additional parameters (interval, limit, etc.)
            
        Returns:
            Dictionary with market data
        """
        # Extract common parameters from kwargs
        interval = kwargs.get("interval", "1h")
        
        # For a real implementation, this would gather news and social media from APIs
        # Here we just return a skeleton structure
        return {
            "symbol": symbol,
            "interval": interval,
            "timestamp": int(time.time()),
            "news": [],
            "social_posts": []
        }
        
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute the sentiment analysis.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Dictionary with analysis results
        """
        # Extract market data from args or kwargs
        market_data = args[0] if args else kwargs.get("market_data", {})
        
        # Call analyze with the market data
        return self.analyze(symbol=None, interval=None, market_data=market_data)
        
    def analyze(self, symbol: Optional[str] = None, interval: Optional[str] = None, 
               market_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market sentiment from various sources.
        
        Args:
            market_data: Dictionary containing market data including:
                - symbol: Trading symbol (e.g., "BTC/USDT")
                - news: List of news headlines (optional)
                - social_posts: List of social media posts (optional)
                
        Returns:
            Dictionary with sentiment analysis results:
                - signal: Trading signal (BUY, SELL, HOLD)
                - confidence: Confidence score (0-100)
                - reasoning: Reasoning behind the sentiment
                - details: Additional sentiment details
        """
        # Get trading symbol
        if isinstance(market_data, str):
            symbol = market_data
            logger.info(f"Received string symbol: {symbol}")
            
            # Construct empty market data with just the symbol
            market_data = {"symbol": symbol}
        elif isinstance(market_data, dict) and "symbol" in market_data:
            symbol = market_data["symbol"]
            logger.info(f"Analyzing sentiment for {symbol}")
        else:
            symbol = "BTC/USDT"  # Default
            logger.warning(f"No symbol provided, using default: {symbol}")
            
        # Check if GrokSentimentClient is available
        if not self.grok_client or not self.grok_client.enabled:
            logger.warning("Grok sentiment client not available. Using fallback.")
            return self._fallback_analysis(symbol)
            
        try:
            # Collect sentiment data from different sources
            sentiments = []
            
            # Process news headlines if available
            if "news" in self.data_sources and "news" in market_data and market_data["news"]:
                news_items = market_data["news"]
                logger.info(f"Analyzing {len(news_items)} news items")
                news_sentiment = self.grok_client.analyze_market_news(news_items)
                sentiments.append(news_sentiment)
                
            # Process social media posts if available
            if "social" in self.data_sources and "social_posts" in market_data and market_data["social_posts"]:
                social_posts = market_data["social_posts"]
                logger.info(f"Analyzing {len(social_posts)} social media posts")
                social_sentiment = self.grok_client.analyze_market_news(social_posts)
                sentiments.append(social_sentiment)
                
            # If no data was provided, analyze the general market context
            if not sentiments:
                logger.info("No specific data provided, analyzing general market sentiment")
                context = f"Current market conditions for {symbol} as of {datetime.now().strftime('%Y-%m-%d')}"
                general_sentiment = self.grok_client.analyze_sentiment(context)
                
                # Convert to signal format
                return self.grok_client.convert_sentiment_to_signal(general_sentiment)
                
            # Aggregate sentiments from different sources
            # For simplicity, we'll use the first source if multiple are available
            # In a production system, you would implement a more sophisticated aggregation
            if sentiments:
                primary_sentiment = sentiments[0]
                signal_result = self.grok_client.convert_sentiment_to_signal(primary_sentiment)
                
                # Add details about other sources if available
                if len(sentiments) > 1:
                    signal_result["details"] = {
                        "sources_analyzed": len(sentiments),
                        "additional_sources": sentiments[1:]
                    }
                    
                return signal_result
            else:
                # Fallback in case sentiment analysis failed
                return self._fallback_analysis(symbol)
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return self._fallback_analysis(symbol)
            
    def _fallback_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Provide fallback sentiment analysis when Grok is unavailable.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with basic sentiment analysis
        """
        logger.info("Using fallback sentiment analysis (neutral bias)")
        
        return {
            "signal": "HOLD",
            "confidence": 70,
            "reasoning": "Neutral market sentiment detected with moderate confidence. " +
                        "Insufficient data for thorough sentiment analysis."
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert agent state to dictionary for serialization.
        
        Returns:
            Dictionary containing agent state
        """
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "data_sources": self.data_sources,
            "grok_available": self.grok_client is not None and self.grok_client.enabled
        }
        
    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> 'SentimentAnalystAgent':
        """
        Create agent instance from dictionary.
        
        Args:
            state_dict: Dictionary containing agent state
            
        Returns:
            New SentimentAnalystAgent instance
        """
        config = state_dict.get("config", {})
        return cls(config=config)

# For testing purposes
if __name__ == "__main__":
    # Create agent
    agent = SentimentAnalystAgent()
    
    # Test with some sample data
    test_data = {
        "symbol": "BTC/USDT",
        "news": [
            "Bitcoin reaches new all-time high above $100,000 as institutional adoption grows",
            "Major central bank announces interest rate hike to combat inflation pressures",
            "New cryptocurrency regulation framework proposed by financial authorities"
        ],
        "social_posts": [
            "Just bought more $BTC, feeling bullish for the next month! #Bitcoin #ToTheMoon",
            "Markets looking uncertain with these mixed economic signals, staying cautious",
            "Technical analysis shows strong support at $95k for Bitcoin, good entry point"
        ]
    }
    
    # Run analysis
    result = agent.analyze(test_data)
    
    # Print result
    print(json.dumps(result, indent=2))