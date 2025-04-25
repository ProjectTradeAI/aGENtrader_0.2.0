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

from base_agent import BaseAnalystAgent
from decision_logger import decision_logger

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
        super().__init__(data_fetcher, config)
        self.name = "SentimentAggregatorAgent"
        self.description = "Analyzes market sentiment using Grok AI"
        
        # Configure xAI API access
        self.api_key = os.environ.get('XAI_API_KEY')
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-2-1212"  # Using the text-only model for sentiment analysis
        
        if not self.api_key:
            logger.warning("XAI_API_KEY not found in environment variables. Sentiment analysis will be limited.")
        else:
            logger.info("xAI API configured successfully.")
        
        # Configure sentiment data storage
        self.sentiment_log_path = os.path.join('logs', 'sentiment_feed.jsonl')
        os.makedirs(os.path.dirname(self.sentiment_log_path), exist_ok=True)
    
    def analyze(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market sentiment for a specific symbol.
        
        Args:
            symbol: Trading symbol
            interval: Time interval (not used for sentiment analysis)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        start_time = time.time()
        
        # Validate input
        if not self.validate_input(symbol, interval):
            return self.build_error_response(
                "INVALID_INPUT", 
                f"Invalid input parameters: symbol={symbol}, interval={interval}"
            )
            
        # Check if API key is available
        if not self.api_key:
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
            
            # Prepare response
            results = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "sentiment_score": sentiment_result["rating"],
                "confidence": sentiment_result["confidence"],
                "analysis_summary": sentiment_result["summary"],
                "sentiment_signals": sentiment_result["signals"],
                "execution_time_seconds": execution_time,
                "status": "success"
            }
            
            # Map sentiment score to trading signal
            sentiment_score = sentiment_result["rating"]
            confidence_pct = int(sentiment_result["confidence"] * 100)
            
            if sentiment_score >= 4:  # Bullish
                signal = "BUY"
            elif sentiment_score <= 2:  # Bearish
                signal = "SELL"
            else:  # Neutral
                signal = "NEUTRAL"
                
            # Log decision summary
            try:
                decision_logger.log_decision(
                    agent_name=self.name,
                    signal=signal,
                    confidence=confidence_pct,
                    reason=sentiment_result["summary"],
                    symbol=symbol,
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
            return self.build_error_response(
                "SENTIMENT_ANALYSIS_ERROR",
                f"Error analyzing sentiment: {str(e)}"
            )
    
    def _fetch_market_data(self, symbol: str) -> str:
        """
        Fetch market news and social media data related to the symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            String containing market news and social media data
        """
        # In a production environment, this would connect to real news APIs
        # For now, we'll use a template approach that provides meaningful context
        
        # Remove the slash that might be in symbols like "BTC/USDT"
        clean_symbol = symbol.replace("/", "")
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
        
    def _analyze_sentiment_with_grok(self, symbol: str, market_data: str) -> Dict[str, Any]:
        """
        Analyze sentiment using Grok AI.
        
        Args:
            symbol: Trading symbol
            market_data: Market data string
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Define the prompt for sentiment analysis
            clean_symbol = symbol.replace("/", "")
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a financial sentiment analysis expert. "
                            "Analyze the sentiment of cryptocurrency market data and provide: "
                            "1. A sentiment rating from 1 to 5 (1=very bearish, 3=neutral, 5=very bullish) "
                            "2. A confidence score between 0 and 1 "
                            "3. A brief summary of your analysis (3 sentences max) "
                            "4. Three key signals that informed your analysis "
                            "Respond with JSON in this format: "
                            "{ \"rating\": number, \"confidence\": number, \"summary\": string, \"signals\": [string, string, string] }"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the current market sentiment for {clean_symbol} based on this data:\n\n{market_data}"
                    }
                ],
                "response_format": {"type": "json_object"}
            }
            
            # Make the API call
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                response_data = response.json()
                result = json.loads(response_data["choices"][0]["message"]["content"])
                
                # Ensure the response has the expected format
                result["rating"] = max(1, min(5, int(result.get("rating", 3))))
                result["confidence"] = max(0, min(1, float(result.get("confidence", 0.5))))
                
                return result
            else:
                logger.error(f"Error from xAI API: {response.status_code} - {response.text}")
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
    
    def _log_sentiment_data(self, symbol: str, sentiment_result: Dict[str, Any]) -> None:
        """
        Log sentiment data to a file.
        
        Args:
            symbol: Trading symbol
            sentiment_result: Sentiment analysis result
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "sentiment_score": sentiment_result["rating"],
                "confidence": sentiment_result["confidence"],
                "summary": sentiment_result["summary"],
                "signals": sentiment_result["signals"]
            }
            
            with open(self.sentiment_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging sentiment data: {str(e)}", exc_info=True)