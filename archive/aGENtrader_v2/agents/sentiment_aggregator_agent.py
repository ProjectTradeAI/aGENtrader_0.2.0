"""
aGENtrader v2.1 - SentimentAggregatorAgent

This module implements a specialized agent for retrieving sentiment data
using the Grok API via xAI.
"""
import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class SentimentAggregatorAgent:
    """
    Agent responsible for retrieving and analyzing sentiment data using Grok API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SentimentAggregatorAgent.
        
        Args:
            api_key: xAI (Grok) API key, defaults to XAI_API_KEY environment variable
        """
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.base_url = "https://api.x.ai/v1"
        
        if not self.api_key:
            logger.warning("No Grok API key provided. Sentiment analysis will be limited.")
    
    def analyze_sentiment(
        self, 
        symbol: str, 
        date: Optional[Union[str, datetime]] = None,
        lookback_days: int = 1,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a specific crypto asset on a given date.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            date: Date for sentiment analysis (defaults to today)
            lookback_days: Number of days to look back for sentiment analysis
            detailed: Whether to include detailed sentiment breakdown
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self.api_key:
            return self._build_error_response(
                "api_key_missing",
                "No Grok API key available. Please provide XAI_API_KEY."
            )
        
        # Normalize symbol format (remove /USDT if present)
        normalized_symbol = symbol.split('/')[0] if '/' in symbol else symbol
        
        # Parse date if string
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return self._build_error_response(
                    "invalid_date_format",
                    f"Invalid date format: {date}. Use YYYY-MM-DD format."
                )
        
        # Default to today if no date provided
        if date is None:
            date = datetime.now()
        
        # Calculate date range for analysis
        end_date = date
        start_date = end_date - timedelta(days=lookback_days)
        
        # Format dates for query
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        try:
            return self._query_grok_api(normalized_symbol, start_date_str, end_date_str, detailed)
        except Exception as e:
            logger.error(f"Error querying Grok API: {str(e)}", exc_info=True)
            return self._build_error_response(
                "api_error",
                f"Error querying Grok API: {str(e)}"
            )
    
    def _query_grok_api(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        detailed: bool
    ) -> Dict[str, Any]:
        """
        Query the Grok API for sentiment data.
        
        Args:
            symbol: Trading symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            detailed: Whether to include detailed sentiment breakdown
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare prompt for Grok API
        prompt = f"""Analyze the market sentiment for {symbol} cryptocurrency between {start_date} and {end_date}.
        Include relevant news, social media trends, and market events that may have influenced the sentiment.
        
        Respond with a JSON object containing the following fields:
        - asset: The cryptocurrency symbol
        - period: The analyzed time period
        - overall_sentiment: A score from -100 to 100, where -100 is extremely negative and 100 is extremely positive
        - sentiment_breakdown: Object with scores for news, social media, and market indicators
        - key_events: Array of significant events that influenced sentiment
        - sources: Array of data sources considered in the analysis
        - confidence: A score from 0 to 100 indicating the confidence in this sentiment analysis
        """
        
        # Call the Grok API
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": "grok-2-1212",
                    "messages": [
                        {"role": "system", "content": "You are a financial sentiment analysis expert."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
            )
            
            response.raise_for_status()
            data = response.json()
            sentiment_data = data["choices"][0]["message"]["content"]
            
            # Parse the JSON content
            parsed_sentiment = json.loads(sentiment_data)
            
            # Create the response
            result = {
                "asset": parsed_sentiment["asset"],
                "period": parsed_sentiment["period"],
                "overall_sentiment": parsed_sentiment["overall_sentiment"],
                "confidence": parsed_sentiment["confidence"],
                "status": "success"
            }
            
            # Include detailed data if requested
            if detailed:
                result["sentiment_breakdown"] = parsed_sentiment["sentiment_breakdown"]
                result["key_events"] = parsed_sentiment["key_events"]
                result["sources"] = parsed_sentiment["sources"]
                
            return result
            
        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}", exc_info=True)
            return self._build_error_response(
                "api_request_error",
                f"Error calling Grok API: {str(e)}"
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}", exc_info=True)
            return self._build_error_response(
                "json_decode_error",
                f"Error parsing API response: {str(e)}"
            )
        except KeyError as e:
            logger.error(f"Response structure error: {str(e)}", exc_info=True)
            return self._build_error_response(
                "response_structure_error",
                f"Unexpected API response structure: {str(e)}"
            )
    
    def _build_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_type: Type of error
            message: Error message
            
        Returns:
            Error response dictionary
        """
        return {
            "status": "error",
            "error": {
                "type": error_type,
                "message": message
            }
        }