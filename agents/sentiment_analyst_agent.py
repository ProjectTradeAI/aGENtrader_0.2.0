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
            symbol: Trading symbol (e.g., "BTC/USDT")
            interval: Time interval for analysis
            market_data: Dictionary containing market data including:
                - symbol: Trading symbol (e.g., "BTC/USDT")
                - news: List of news headlines (optional)
                - social_posts: List of social media posts (optional)
            **kwargs: Additional parameters
                
        Returns:
            Dictionary with sentiment analysis results:
                - signal: Trading signal (BUY, SELL, HOLD)
                - confidence: Confidence score (0-100)
                - reasoning: Reasoning behind the sentiment
                - details: Additional sentiment details
        """
        # Initialize market_data if it's None to avoid NoneType errors
        if market_data is None:
            market_data = {}
            
        # Handle the case where symbol is passed directly
        if symbol is not None:
            # Don't log potentially large data structures
            if isinstance(symbol, dict):
                if "symbol" in symbol:
                    logger.info(f"Using symbol from symbol parameter: {symbol['symbol']}")
                else:
                    logger.info("Using provided symbol parameter (dictionary without symbol key)")
            else:
                logger.info(f"Using provided symbol parameter: {symbol}")
        # Get trading symbol from market_data
        elif isinstance(market_data, str):
            symbol = market_data
            logger.info(f"Received string as market_data, using as symbol: {symbol}")
            # Construct empty market data with just the symbol
            market_data = {"symbol": symbol}
        elif isinstance(market_data, dict) and "symbol" in market_data:
            symbol = market_data["symbol"]
            logger.info(f"Extracting symbol from market_data: {symbol}")
            
            # Log OHLCV data sizes without printing the actual data
            if "ohlcv" in market_data:
                logger.info(f"Market data contains OHLCV with {len(market_data['ohlcv'])} data points")
        else:
            symbol = "BTC/USDT"  # Default
            logger.warning(f"No symbol found in any parameter, using default: {symbol}")
            
        # Ensure market_data is a dictionary
        if not isinstance(market_data, dict):
            logger.warning(f"market_data is not a dictionary, creating empty dict")
            market_data = {"symbol": symbol}
            
        # Check if GrokSentimentClient is available
        if not self.grok_client or not self.grok_client.enabled:
            logger.warning("Grok sentiment client not available. Using fallback.")
            return self._fallback_analysis(symbol)
            
        try:
            # Check if we received OHLCV data instead of sentiment data
            if "ohlcv" in market_data:
                # Only log that we received OHLCV data without dumping the data
                logger.warning("Received OHLCV data instead of sentiment data - this should be fixed in the data flow")
                logger.info("SentimentAnalystAgent should receive sentiment data directly, not OHLCV data")
                
                # If we have enough OHLCV data points, we can try to extract simple price trend
                ohlcv_data = market_data["ohlcv"]
                data_points = len(ohlcv_data) if ohlcv_data else 0
                
                if ohlcv_data and data_points > 1:
                    logger.info(f"Using {data_points} OHLCV data points as a proxy for sentiment")
                    
                    try:
                        # Extract closing prices as numbers only
                        closes = []
                        for candle in ohlcv_data:
                            if 'close' in candle:
                                closes.append(float(candle['close']))
                                
                        if len(closes) > 1:
                            # Simple trend analysis: compare latest close with first close
                            price_change_pct = (closes[-1] - closes[0]) / closes[0] * 100
                            first_price = closes[0]
                            last_price = closes[-1]
                            
                            logger.info(f"Price movement: {price_change_pct:.2f}% (from {first_price:.2f} to {last_price:.2f})")
                            
                            if price_change_pct > 5:
                                sentiment = {"signal": "BUY", "confidence": 70, 
                                          "reasoning": f"Price increased by {price_change_pct:.2f}% over the analyzed period"}
                            elif price_change_pct < -5:
                                sentiment = {"signal": "SELL", "confidence": 70,
                                          "reasoning": f"Price decreased by {abs(price_change_pct):.2f}% over the analyzed period"}
                            else:
                                sentiment = {"signal": "HOLD", "confidence": 60,
                                          "reasoning": f"Price relatively stable (changed by {price_change_pct:.2f}%) over the analyzed period"}
                                
                            logger.info(f"Generated simple sentiment from price trend: {sentiment['signal']} ({sentiment['confidence']}%)")
                            return sentiment
                    except Exception as e:
                        logger.error(f"Error processing OHLCV data: {str(e)}")
                        
                # If OHLCV data analysis didn't work, fall back to default neutral sentiment
                logger.info("Cannot extract meaningful sentiment from OHLCV data, using fallback")
                return self._fallback_analysis(symbol)
            
            # Normal processing for genuine sentiment data
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
                logger.info("No specific sentiment data provided, analyzing general market sentiment")
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
            
    def _fallback_analysis(self, symbol=None) -> Dict[str, Any]:
        """
        Provide fallback sentiment analysis when Grok is unavailable.
        
        Args:
            symbol: Trading symbol (string, dict, or None)
            
        Returns:
            Dictionary with basic sentiment analysis
        """
        # Extract symbol string if it's a dictionary
        symbol_str = "BTC/USDT"  # Default
        try:
            if isinstance(symbol, dict) and "symbol" in symbol:
                symbol_str = symbol["symbol"]
            elif isinstance(symbol, str):
                symbol_str = symbol
        except:
            pass
            
        logger.info(f"Using fallback sentiment analysis (neutral bias) for {symbol_str}")
        
        return {
            "signal": "HOLD",
            "confidence": 70,
            "reasoning": f"Neutral market sentiment detected for {symbol_str} with moderate confidence. " +
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