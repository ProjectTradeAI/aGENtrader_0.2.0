"""
aGENtrader v2 CoinAPI Fetcher

This module implements the CoinAPIFetcher class, which handles
retrieving market data from the CoinAPI service.
"""

import os
import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger('aGENtrader.data.coinapi')

class CoinAPIFetcher:
    """Class for fetching cryptocurrency market data from CoinAPI."""

    BASE_URL = "https://rest.coinapi.io/v1"
    OHLCV_ENDPOINT = "/ohlcv/{symbol}/latest"
    TICKER_ENDPOINT = "/quotes/current"
    
    # Map common intervals to CoinAPI format
    INTERVAL_MAP = {
        '1m': '1MIN',
        '3m': '3MIN',
        '5m': '5MIN',
        '15m': '15MIN',
        '30m': '30MIN',
        '1h': '1HRS',
        '2h': '2HRS',
        '4h': '4HRS',
        '6h': '6HRS',
        '12h': '12HRS',
        '1d': '1DAY',
        '3d': '3DAY',
        '1w': '1WEK',
        '1mo': '1MTH'
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CoinAPI fetcher.
        
        Args:
            api_key: CoinAPI key
        """
        self.api_key = api_key or os.environ.get('COINAPI_KEY')
        if not self.api_key:
            raise ValueError("CoinAPI key not provided")
        
        self.headers = {
            'X-CoinAPI-Key': self.api_key,
            'Accept': 'application/json'
        }
        
        self.logger = logger
        self.rate_limit_wait = 1.0  # Default wait time between requests
        self.logger.debug("CoinAPIFetcher initialized")

    def fetch_ohlcv(
        self, 
        symbol: str, 
        interval: str = "1d", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data.
        
        Args:
            symbol: Trading symbol (e.g., BITSTAMP_SPOT_BTC_USD)
            interval: Time interval (e.g., 1d, 4h, 1h, 15m)
            limit: Number of candles to retrieve
            
        Returns:
            List of OHLCV data dictionaries
        """
        try:
            # Format the URL
            url = f"{self.BASE_URL}{self.OHLCV_ENDPOINT.format(symbol=symbol)}"
            
            # Convert interval to CoinAPI format
            period_id = self._convert_interval_to_coinapi_format(interval)
            
            # Set up parameters
            params = {
                'period_id': period_id,
                'limit': limit
            }
            
            self.logger.debug(f"Fetching OHLCV data for {symbol} at {interval} interval")
            
            # Make the request
            response = self._make_request(url, params)
            
            # Standardize the data format
            standardized_data = self._standardize_ohlcv_data(response)
            
            self.logger.debug(f"Retrieved {len(standardized_data)} OHLCV records")
            return standardized_data
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data: {str(e)}")
            raise

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current ticker data.
        
        Args:
            symbol: Trading symbol (e.g., BITSTAMP_SPOT_BTC_USD)
            
        Returns:
            Ticker data dictionary
        """
        try:
            # Format the URL
            url = f"{self.BASE_URL}{self.TICKER_ENDPOINT}"
            
            # Set up parameters
            params = {
                'filter_symbol_id': symbol
            }
            
            self.logger.debug(f"Fetching ticker data for {symbol}")
            
            # Make the request
            response = self._make_request(url, params)
            
            # Check if we got any data
            if not response or len(response) == 0:
                self.logger.error(f"No ticker data returned for {symbol}")
                raise ValueError(f"No ticker data available for {symbol}")
            
            # Standardize the data format
            standardized_data = self._standardize_ticker_data(response[0])
            
            self.logger.debug(f"Retrieved ticker data for {symbol}")
            return standardized_data
            
        except Exception as e:
            self.logger.error(f"Error fetching ticker data: {str(e)}")
            raise

    def _make_request(self, url: str, params: Dict[str, Any]) -> Any:
        """
        Make a request to the CoinAPI service with rate limiting.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            Response data
        """
        try:
            # Make the request
            response = requests.get(url, headers=self.headers, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                self.logger.warning("Rate limit exceeded, increasing wait time")
                self.rate_limit_wait *= 2  # Exponential backoff
                time.sleep(self.rate_limit_wait)
                return self._make_request(url, params)  # Retry
            
            # Handle other errors
            if response.status_code != 200:
                error_msg = f"API request failed with status code {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
            
            # Reset rate limit wait time on successful request
            self.rate_limit_wait = 1.0
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {str(e)}")
            raise

    def _convert_interval_to_coinapi_format(self, interval: str) -> str:
        """
        Convert common interval format to CoinAPI format.
        
        Args:
            interval: Interval string (e.g., 1d, 4h, 30m)
            
        Returns:
            CoinAPI format period ID
        """
        if interval in self.INTERVAL_MAP:
            return self.INTERVAL_MAP[interval]
        
        self.logger.warning(f"Unknown interval format: {interval}, using 1DAY as default")
        return '1DAY'

    def _standardize_ohlcv_data(self, api_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert CoinAPI OHLCV data to standardized format.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            Standardized OHLCV data
        """
        standardized = []
        
        for item in api_data:
            standardized_item = {
                'time_period_start': item.get('time_period_start'),
                'time_period_end': item.get('time_period_end'),
                'time_open': item.get('time_open'),
                'time_close': item.get('time_close'),
                'price_open': item.get('price_open'),
                'price_high': item.get('price_high'),
                'price_low': item.get('price_low'),
                'price_close': item.get('price_close'),
                'volume_traded': item.get('volume_traded'),
                'trades_count': item.get('trades_count')
            }
            standardized.append(standardized_item)
        
        return standardized

    def _standardize_ticker_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert CoinAPI ticker data to standardized format.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            Standardized ticker data
        """
        return {
            'symbol': api_data.get('symbol_id'),
            'price': api_data.get('ask_price'),  # Use ask price as current price
            'price_bid': api_data.get('bid_price'),
            'price_ask': api_data.get('ask_price'),
            'volume_bid': api_data.get('bid_size'),
            'volume_ask': api_data.get('ask_size'),
            'timestamp': api_data.get('time_exchange'),
            'raw': api_data  # Include the raw data for reference
        }