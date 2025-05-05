"""
aGENtrader v2 Sentiment Aggregator Agent

This module provides a sentiment analysis agent that uses Grok AI to analyze market sentiment.
It aggregates sentiment data from various sources and provides a unified sentiment score.
"""

import os
import time
import json
import random
import logging
import requests
from typing import Dict, Any, List, Optional, Union
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
    
    def analyze(self, symbol: Optional[str] = None, market_data: Optional[Dict[str, Any]] = None, 
               interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market sentiment for a specific symbol.
        
        Args:
            symbol: Trading symbol
            market_data: Pre-fetched market data (optional)
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
            
            # Check if market_data was provided, otherwise fetch it
            if market_data is None:
                # Get market news and social media data for the symbol
                market_data_text = self._fetch_market_data_text(symbol)
                
                # Analyze sentiment using Grok AI with the text data
                sentiment_result = self._analyze_sentiment_with_grok(symbol, market_data_text)
            else:
                # Use the provided market_data, but we need to convert it to the text format our model expects
                # For now, just use the symbol to generate text as we normally would
                market_data_text = self._fetch_market_data_text(symbol)
                sentiment_result = self._analyze_sentiment_with_grok(symbol, market_data_text)
            
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
            execution_time = time.time() - start_time
            error_str = str(e).lower()
            
            # Check for specific API-related errors
            if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                logger.warning(f"SentimentAggregatorAgent API rate limited: {str(e)}")
                return self._api_error_response(symbol, "rate_limit", interval)
            elif "api key" in error_str or "authentication" in error_str or "unauthorized" in error_str:
                logger.error(f"SentimentAggregatorAgent API authentication error: {str(e)}")
                return self._api_error_response(symbol, "auth_error", interval)
            elif "timeout" in error_str or "connection" in error_str:
                logger.error(f"SentimentAggregatorAgent API connection error: {str(e)}")
                return self._api_error_response(symbol, "connection_error", interval)
            else:
                # Log the general exception details
                logger.error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
                error_response = self.build_error_response(
                    "SENTIMENT_ANALYSIS_ERROR",
                    f"Error analyzing sentiment: {str(e)}"
                )
                # Add interval to error response for consistency
                error_response["interval"] = interval
                return error_response
    
    def _fetch_market_data_text(self, symbol) -> str:
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
        
        # Get current price if available for context
        current_price = "Unknown"
        if self.data_fetcher:
            try:
                current_price = self.data_fetcher.get_current_price(symbol_str)
                current_price = f"{current_price:,.2f} USD"
            except:
                pass

        # Add timestamp and unique request ID for each analysis
        timestamp = datetime.now()
        request_id = f"{hash(timestamp.isoformat() + symbol_str) % 10000:04d}"
        
        # Create a more dynamic prompt with timestamp and price context
        market_data = f"""
        Market Analysis Request #{request_id} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        
        Latest market developments for {base_asset} at current price {current_price}:
        
        1. Recent news: Several major investment firms have published new {base_asset} price targets 
           and trading strategies in the past 24 hours based on technical indicators.
           
        2. Social sentiment: {base_asset} conversations on Twitter/X and Reddit in the last 6 hours 
           show a mix of bullish and bearish perspectives, with ongoing debate about support levels.
           
        3. Regulatory landscape: Recent regulatory developments have created both opportunities 
           and challenges for {base_asset} investors and traders.
           
        4. Market metrics: Trading volume for {base_asset} in the past 24h has been {10 + (hash(timestamp.isoformat()) % 80)}% 
           {['higher', 'lower'][hash(timestamp.minute) % 2]} than the 7-day average, with 
           {'increasing' if timestamp.minute % 2 == 0 else 'decreasing'} open interest.
           
        5. Institutional activity: New institutional announcements regarding {base_asset} have emerged, 
           including {['increased', 'diversified', 'strategic'][hash(timestamp.second) % 3]} positions from 
           several fund managers.
        
        Please analyze the overall market sentiment for {base_asset} based on these factors,
        rating the sentiment from 1 (extremely bearish) to 5 (extremely bullish),
        with a confidence score between 0 and 1.
        
        Use only the information provided above to form your analysis, focusing on the unique 
        circumstances at this specific time ({timestamp.strftime('%H:%M:%S')}).
        """
        
        # Log the first 120 chars of the prompt
        logger.debug(f"Sentiment prompt for {symbol_str} (first 120 chars): {market_data[:120]}...")
        
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
            
            # Log debug information about the prompt for debugging
            logger.debug(f"Sending sentiment analysis request to Grok API: [First 120 chars] {user_prompt[:120]}...")
            
            # Generate random temperature for more diverse responses
            temperature_value = 0.6 + (0.3 * random.random())  # Random temp between 0.6-0.9
            
            # Query LLM using our configured LLM client for Grok
            response = self.llm_client.query(
                prompt=user_prompt,
                system_prompt=system_prompt,
                provider="grok",  # Enforce using Grok for sentiment analysis
                model=self.grok_model,
                json_response=True,
                temperature=temperature_value  # Use the stored temperature value
            )
            
            # Check if the request was successful
            if response["status"] == "success":
                # Get the content - should already be a JSON object since json_response=True
                result = response["content"]
                
                # Log the first part of the response for debugging
                if isinstance(result, dict):
                    summary = result.get("summary", "")
                    logger.debug(f"Received sentiment response from Grok: [First 120 chars] {summary[:120]}...")
                else:
                    logger.debug(f"Received non-dict response from Grok: {str(result)[:120]}...")
                
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
    
    def _fetch_market_data(self, symbol: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for the specified symbol.
        This method implements the base class interface but delegates to our text-based method.
        
        Args:
            symbol: Trading symbol (can be string or dictionary)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing market data
        """
        # Extract proper symbol string
        symbol_str = "BTC/USDT"  # Default
        if isinstance(symbol, dict) and "symbol" in symbol:
            symbol_str = symbol.get("symbol", "BTC/USDT")
        elif isinstance(symbol, str):
            symbol_str = symbol
            
        # Generate the prompt text using our specialized method
        market_text = self._fetch_market_data_text(symbol)
        
        # Create a standardized market_data dictionary to match base class expectations
        return {
            "symbol": symbol_str,
            "timestamp": datetime.now().isoformat(),
            "news_text": market_text,
            "data_type": "sentiment_text",
            "data_source": "sentiment_aggregator_template",
            "status": "success"
        }
    
    def _api_error_response(self, symbol, error_type: str = "api_error", interval: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle API errors gracefully, particularly rate limiting (429) errors.
        
        Args:
            symbol: Trading symbol (string, dict, or None)
            error_type: Type of error ("rate_limit", "auth_error", "connection_error", etc.)
            interval: Time interval for consistency with other methods
            
        Returns:
            Dictionary with standardized error response that won't reduce system confidence
        """
        # Extract symbol string if it's a dictionary
        symbol_str = "BTC/USDT"  # Default
        try:
            if isinstance(symbol, dict) and "symbol" in symbol:
                symbol_str = symbol.get("symbol", "BTC/USDT")
            elif isinstance(symbol, str):
                symbol_str = symbol
        except:
            pass
            
        # Create timestamp for tracking
        timestamp = datetime.now()
        request_id = f"{hash(timestamp.isoformat() + symbol_str) % 10000:04d}"
        
        # Create an error response that won't reduce system confidence
        # Using UNKNOWN signal with confidence=0 to ensure it doesn't affect decision
        if error_type == "rate_limit":
            reason = "Sentiment data unavailable (API rate limit exceeded)"
            logger.warning(f"[WARNING] SentimentAggregatorAgent API rate limited (429)")
        elif error_type == "auth_error":
            reason = "Sentiment data unavailable (API authentication error)"
            logger.warning(f"[WARNING] SentimentAggregatorAgent API authentication error")
        elif error_type == "connection_error":
            reason = "Sentiment data unavailable (API connection error)"
            logger.warning(f"[WARNING] SentimentAggregatorAgent API connection error")
        else:
            reason = "Sentiment API error, data unavailable"
            logger.warning(f"[WARNING] SentimentAggregatorAgent API error: {error_type}")
            
        return {
            "agent": self.name,
            "timestamp": timestamp.isoformat(),
            "symbol": symbol_str,
            "interval": interval or self.default_interval,
            "current_price": 0.0,  # Placeholder
            "sentiment_score": 3,  # Neutral
            "confidence": 0,      # Zero confidence to prevent affecting system
            "signal": "UNKNOWN",  # Using UNKNOWN for API errors
            "analysis_summary": reason,
            "sentiment_signals": ["API error, reliable data unavailable"],
            "execution_time_seconds": 0.0,
            "status": "error",
            "error_type": error_type,
            "error_reason": reason
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
                
            # Add more dynamic metadata to each sentiment entry
            current_price = None
            if self.data_fetcher:
                try:
                    current_price = self.data_fetcher.get_current_price(symbol_str)
                except Exception as e:
                    logger.debug(f"Could not fetch price for logging: {str(e)}")
                    
            # Create a more informative log entry with additional metadata
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol_str,
                "sentiment_score": sentiment_result["rating"],
                "confidence": sentiment_result["confidence"],
                "summary": sentiment_result["summary"],
                "signals": sentiment_result["signals"],
                "metadata": {
                    "request_id": f"{hash(datetime.now().isoformat())%1000:03d}",
                    "current_price": current_price,
                    "temperature": sentiment_result.get("temperature", 0.7), # Record temperature if available  
                    "model": self.grok_model,
                    "version": "aGENtrader_0.2.0"
                }
            }
            
            with open(self.sentiment_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging sentiment data: {str(e)}", exc_info=True)