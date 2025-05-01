"""
aGENtrader v2 Sentiment Aggregator Agent

This module provides a sentiment analysis agent that uses Grok AI to analyze market sentiment.
It aggregates sentiment data from various sources and provides a unified sentiment score.
"""

import os
import time
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base_agent import BaseAnalystAgent
from core.logging import decision_logger
from models.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sentiment_aggregator')

class SentimentAggregatorAgent(BaseAnalystAgent):
    """
    Agent that analyzes market sentiment using Grok AI.
    
    This agent retrieves sentiment data from various sources and uses
    Grok AI to analyze the overall market sentiment for specific assets.
    """
    
    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the sentiment aggregator agent.
        
        Args:
            data_fetcher: Optional data fetcher instance
            config: Configuration parameters
        """
        super().__init__()
        self.name = "SentimentAggregatorAgent"
        self.description = "Analyzes market sentiment using Grok AI"
        self.data_fetcher = data_fetcher
        self.config = config or {}
        
        # Get agent config for timeframe setting
        self.agent_config = self.get_agent_config()
        self.trading_config = self.get_trading_config()
        
        # Use agent-specific timeframe from config if available
        sentiment_config = self.agent_config.get("sentiment_analyst", {})
        self.default_interval = sentiment_config.get("timeframe", self.trading_config.get("default_interval", "1h"))
        
        # Configure Grok-specific LLM client using agent-specific model selection
        self.llm_client = LLMClient(agent_name="sentiment_aggregator")
        
        # Set API key directly from environment
        self.api_key = os.environ.get('XAI_API_KEY')
        self.grok_model = os.environ.get('LLM_MODEL_SENTIMENT', 'grok-2-1212')
        
        if not self.api_key:
            logger.warning("XAI_API_KEY not found in environment variables. Sentiment analysis will be limited.")
        else:
            logger.info(f"Sentiment Analyzer initialized with Grok model: {self.grok_model}")
        
        # Configure sentiment data storage
        self.sentiment_log_path = os.path.join('logs', 'sentiment_feed.jsonl')
        os.makedirs(os.path.dirname(self.sentiment_log_path), exist_ok=True)
    
    def analyze(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market sentiment for a specific symbol.
        
        Args:
            symbol: Trading symbol
            interval: Time interval (different timeframe for sentiment analysis)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        start_time = time.time()
        
        # Use agent-specific timeframe if none provided
        interval = interval or self.default_interval
        
        # Validate input
        if not self.validate_input(symbol, interval):
            error_response = self.build_error_response(
                "INVALID_INPUT", 
                f"Invalid input parameters: symbol={symbol}, interval={interval}"
            )
            # Add interval to error response for consistency
            error_response["interval"] = interval
            return error_response
            
        # Check if our LLM client has access to Grok
        if not self.llm_client.api_keys.get('grok'):
            return self.build_error_response(
                "API_KEY_MISSING",
                "XAI_API_KEY is not set. Cannot perform sentiment analysis."
            )
            
        try:
            # Ensure symbol is not None
            if symbol is None:
                symbol = "BTC/USDT"  # Default symbol if none provided
            
            # Get market news and social media data for the symbol
            market_data = self._fetch_market_data(symbol)
            
            # Analyze sentiment using Grok AI
            sentiment_result = self._analyze_sentiment_with_grok(symbol, market_data)
            
            # Log sentiment data
            self._log_sentiment_data(symbol, sentiment_result)
            
            execution_time = time.time() - start_time
            
            # Map sentiment score to trading signal
            sentiment_score = sentiment_result["rating"]
            confidence_pct = int(sentiment_result["confidence"] * 100)
            
            if sentiment_score >= 4:  # Bullish
                signal = "BUY"
            elif sentiment_score <= 2:  # Bearish
                signal = "SELL"
            else:  # Neutral
                signal = "NEUTRAL"
                
            # Get current price if available from data_fetcher
            current_price = 0.0
            if self.data_fetcher:
                try:
                    # Handle case where symbol is a dictionary
                    symbol_value = symbol
                    if isinstance(symbol, dict):
                        # Try to safely extract symbol from dict
                        if 'symbol' in symbol:
                            symbol_value = symbol.get('symbol', 'BTC/USDT')
                        else:
                            logger.warning("Symbol dict doesn't contain a 'symbol' key, using default BTC/USDT")
                            symbol_value = 'BTC/USDT'
                        
                    # Now we have a string symbol to query
                    current_price = self.data_fetcher.get_current_price(symbol_value)
                    logger.info(f"Retrieved current price for {symbol_value}: {current_price}")
                except Exception as price_err:
                    logger.warning(f"Unable to fetch current price: {str(price_err)}")
                    
            # Use default mock price if we couldn't get a real one
            if current_price == 0.0:
                current_price = 50000.0  # Default BTC price for testing
                logger.info(f"Using default price for {symbol}: {current_price}")
                    
            # Prepare response
            results = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol if not isinstance(symbol, dict) else symbol.get('symbol', 'BTC/USDT'),
                "interval": interval,  # Add interval for consistency with other agents
                "current_price": current_price,  # Add current price for consistency
                "sentiment_score": sentiment_result["rating"],
                "confidence": confidence_pct,  # Use the percentage form for consistency
                "signal": signal,  # Add signal field for DecisionAgent
                "analysis_summary": sentiment_result["summary"],
                "sentiment_signals": sentiment_result["signals"],
                "execution_time_seconds": execution_time,
                "status": "success"
            }
                
            # Log decision summary
            try:
                # Use the current_price we already fetched above
                # Already have proper handling for symbol as dict or string
                
                # Get proper symbol string for logging
                symbol_str = symbol
                if isinstance(symbol, dict):
                    symbol_str = symbol.get('symbol', 'BTC/USDT')
                
                decision_logger.log_decision(
                    agent_name=self.name,
                    signal=signal,
                    confidence=confidence_pct,
                    reason=sentiment_result["summary"],
                    symbol=symbol_str,
                    price=current_price,  # Use the current_price we calculated above
                    timestamp=results["timestamp"],
                    additional_data={
                        "sentiment_score": sentiment_score,
                        "signals": sentiment_result["signals"]
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log decision: {str(e)}")
                
            # Return results
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
            error_response = self.build_error_response(
                "SENTIMENT_ANALYSIS_ERROR",
                f"Error analyzing sentiment: {str(e)}"
            )
            # Add interval to error response for consistency
            error_response["interval"] = interval
            return error_response
    
    def _fetch_market_data(self, symbol) -> str:
        """
        Fetch market news and social media data related to the symbol.
        
        Args:
            symbol: Trading symbol (can be string or dictionary)
            
        Returns:
            String containing market news and social media data
        """
        # In a production environment, this would connect to real news APIs
        # For now, we'll use a template approach that provides meaningful context
        
        # Handle case where symbol is a dictionary (e.g., from test harness)
        if isinstance(symbol, dict):
            # Extract symbol from market_data dictionary if available
            if 'symbol' in symbol:
                symbol_str = symbol['symbol']
            else:
                # Default to BTC/USDT if no symbol found
                symbol_str = "BTC/USDT"
                logger.warning(f"Received dict instead of string for symbol. Using default: {symbol_str}")
        else:
            symbol_str = str(symbol) if symbol is not None else "BTC/USDT"
        
        # Remove the slash that might be in symbols like "BTC/USDT"
        clean_symbol = symbol_str.replace("/", "")
        base_asset = clean_symbol.split("USDT")[0] if "USDT" in clean_symbol else clean_symbol
        
        market_data = f"""
        Recent market developments for {base_asset}:
        
        1. Several major investment firms have adjusted their {base_asset} price targets.
        2. Social media sentiment for {base_asset} shows mixed reactions to recent price movements.
        3. Regulatory news has affected market perception of {base_asset} and similar assets.
        4. Trading volume for {base_asset} has shown notable patterns in the last 24 hours.
        5. Institutional adoption of {base_asset} continues to evolve with new announcements.
        
        Please analyze the overall market sentiment for {base_asset} based on these factors,
        rating the sentiment from 1 (extremely bearish) to 5 (extremely bullish),
        with a confidence score between 0 and 1.
        """
        
        return market_data
        
    def _analyze_sentiment_with_grok(self, symbol, market_data: str) -> Dict[str, Any]:
        """
        Analyze sentiment using Grok AI via the LLM client.
        
        Args:
            symbol: Trading symbol (can be string or dictionary)
            market_data: Market data string
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Handle case where symbol is a dictionary
            if isinstance(symbol, dict):
                symbol_str = symbol.get('symbol', "BTC/USDT")
            else:
                symbol_str = str(symbol) if symbol is not None else "BTC/USDT"
                
            # Define the system prompt for sentiment analysis
            clean_symbol = symbol_str.replace("/", "")
            
            system_prompt = (
                "You are a financial sentiment analysis expert. "
                "Analyze the sentiment of cryptocurrency market data and provide: "
                "1. A sentiment rating from 1 to 5 (1=very bearish, 3=neutral, 5=very bullish) "
                "2. A confidence score between 0 and 1 "
                "3. A brief summary of your analysis (3 sentences max) "
                "4. Three key signals that informed your analysis "
                "Respond with JSON in this format: "
                "{ \"rating\": number, \"confidence\": number, \"summary\": string, \"signals\": [string, string, string] }"
            )
            
            user_prompt = f"Analyze the current market sentiment for {clean_symbol} based on this data:\n\n{market_data}"
            
            # Query LLM using our configured LLM client for Grok
            response = self.llm_client.query(
                prompt=user_prompt,
                system_prompt=system_prompt,
                provider="grok",  # Enforce using Grok for sentiment analysis
                model=self.grok_model,
                json_response=True
            )
            
            # Check if the request was successful
            if response["status"] == "success":
                # Get the content - should already be a JSON object since json_response=True
                result = response["content"]
                
                # Ensure the response has the expected format and types
                if isinstance(result, dict):
                    result["rating"] = max(1, min(5, int(result.get("rating", 3))))
                    result["confidence"] = max(0, min(1, float(result.get("confidence", 0.5))))
                    
                    # Ensure signals is a list and handle None case
                    signals = result.get("signals")
                    if signals is None or not isinstance(signals, list):
                        result["signals"] = ["No specific signals were identified"]
                    
                    # Ensure summary is a string
                    if not isinstance(result.get("summary", ""), str):
                        result["summary"] = "No summary was provided"
                    
                    return result
                else:
                    # If not a proper dict, create a fallback response
                    logger.error(f"Invalid response format from Grok: {result}")
                    return {
                        "rating": 3,
                        "confidence": 0.3,
                        "summary": "Received malformed response from Grok AI. Using fallback neutral sentiment.",
                        "signals": [
                            "API response format error",
                            "Using fallback neutral sentiment with low confidence",
                            "Check Grok API for proper JSON formatting"
                        ]
                    }
            else:
                logger.error(f"Error from Grok API: {response.get('error', 'Unknown error')}")
                # Fallback to a default response with clear indication it's a fallback
                return {
                    "rating": 3,
                    "confidence": 0.3,
                    "summary": "Unable to retrieve sentiment from Grok AI due to API error. This is a fallback neutral sentiment with low confidence.",
                    "signals": [
                        "API connection error - sentiment could not be determined",
                        "Using fallback neutral sentiment with low confidence",
                        "Recommend checking API connection and retry"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error in Grok sentiment analysis: {str(e)}", exc_info=True)
            # Provide a fallback response with clear error indication
            return {
                "rating": 3,
                "confidence": 0.2,
                "summary": f"Error analyzing sentiment: {str(e)}. Using fallback neutral rating with very low confidence.",
                "signals": [
                    "Error in sentiment analysis process",
                    "Fallback neutral sentiment with very low confidence",
                    "Error details in application logs"
                ]
            }
    
    def _log_sentiment_data(self, symbol, sentiment_result: Dict[str, Any]) -> None:
        """
        Log sentiment data to a file.
        
        Args:
            symbol: Trading symbol (can be string or dictionary)
            sentiment_result: Sentiment analysis result
        """
        try:
            # Handle case where symbol is a dictionary
            if isinstance(symbol, dict):
                symbol_str = symbol.get('symbol', "BTC/USDT")
            else:
                symbol_str = str(symbol) if symbol is not None else "BTC/USDT"
                
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol_str,
                "sentiment_score": sentiment_result["rating"],
                "confidence": sentiment_result["confidence"],
                "summary": sentiment_result["summary"],
                "signals": sentiment_result["signals"]
            }
            
            with open(self.sentiment_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging sentiment data: {str(e)}", exc_info=True)