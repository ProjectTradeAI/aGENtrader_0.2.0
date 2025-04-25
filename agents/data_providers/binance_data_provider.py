"""
aGENtrader v2 Binance Data Provider

This module provides a data fetcher for Binance cryptocurrency exchange API.
It serves as the primary market data provider with fallback to CoinAPI when needed.
"""
import os
import time
import hmac
import hashlib
import logging
import urllib.parse
from typing import Dict, List, Optional, Any, Union
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BinanceDataProvider")

class BinanceDataProvider:
    """
    Data provider for Binance cryptocurrency exchange API.
    
    This class handles fetching market data from Binance API with robust
    error handling and rate limiting compliance.
    """
    
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"
    
    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m", 
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M"
    }
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None,
        use_testnet: bool = False
    ):
        """
        Initialize the Binance API provider.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            use_testnet: Whether to use Binance testnet
        """
        # Use environment variables as fallback
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET")
        
        # Select base URL based on whether to use testnet
        self.base_url = self.TESTNET_URL if use_testnet else self.BASE_URL
        
        # Set up rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # seconds between requests
        
        logger.info("Initialized Binance Data Provider")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC SHA256 signature for authenticated requests.
        
        Args:
            params: Request parameters as dictionary
            
        Returns:
            HMAC signature as hex string
        """
        if not self.api_secret:
            raise ValueError("API secret is required for authenticated requests")
            
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _handle_rate_limiting(self):
        """Ensure we don't exceed rate limits by spacing requests"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Make a request to the Binance API with error handling.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Request parameters
            signed: Whether request requires authentication
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If API request fails
        """
        # Handle rate limiting
        self._handle_rate_limiting()
        
        # Initialize parameters if None
        params = params or {}
        
        # Create full URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = {}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        # Add signature for authenticated requests
        if signed and self.api_secret:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._generate_signature(params)
        
        try:
            # Make the request
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Special handling for common errors
            if e.response.status_code == 400:
                # Check if this is an invalid symbol error
                try:
                    error_data = e.response.json()
                    if "msg" in error_data and "symbol" in error_data["msg"].lower():
                        logger.error(f"Invalid symbol: {params.get('symbol')}")
                        # Return empty data instead of raising an exception
                        if endpoint == "/api/v3/klines":
                            return []  # Return empty list for klines
                        elif endpoint == "/api/v3/ticker/price":
                            return {"price": "0.0"}  # Return zero price
                        elif endpoint == "/api/v3/ticker/24hr":
                            return {}  # Return empty dict as appropriate for the endpoint
                except:
                    pass  # If we can't parse the error, continue with normal handling
            
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"Binance API request failed: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"Binance API request failed: {str(e)}")
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including trading pairs and rules.
        
        Returns:
            Exchange information
        """
        return self._make_request("/api/v3/exchangeInfo")
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        interval: str = "1h", 
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV (candlestick) data for a trading pair.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            limit: Maximum number of records to return
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            List of OHLCV records
        """
        # Map interval if needed
        mapped_interval = self.INTERVAL_MAP.get(interval, interval)
        
        # Format symbol correctly (remove "/" if present, e.g., "BTC/USDT" -> "BTCUSDT")
        formatted_symbol = symbol.replace("/", "")
        
        # Prepare parameters
        params = {
            "symbol": formatted_symbol,
            "interval": mapped_interval,
            "limit": limit
        }
        
        # Add optional parameters if provided
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
            
        # Make request
        candlesticks = self._make_request("/api/v3/klines", params=params)
        
        # Format the response
        formatted_candlesticks = []
        for candle in candlesticks:
            formatted_candlesticks.append({
                "timestamp": candle[0],  # Changed "time" to "timestamp" to match expected format
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": candle[6],
                "quote_asset_volume": float(candle[7]),
                "number_of_trades": int(candle[8]),
                "taker_buy_base_asset_volume": float(candle[9]),
                "taker_buy_quote_asset_volume": float(candle[10])
            })
            
        return formatted_candlesticks
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price ticker for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Current ticker data
        """
        # Format symbol correctly (remove "/" if present)
        formatted_symbol = symbol.replace("/", "")
        
        params = {"symbol": formatted_symbol}
        return self._make_request("/api/v3/ticker/24hr", params=params)
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Current price as float
        """
        # Format symbol correctly (remove "/" if present)
        formatted_symbol = symbol.replace("/", "")
        
        params = {"symbol": formatted_symbol}
        ticker = self._make_request("/api/v3/ticker/price", params=params)
        return float(ticker["price"])
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information (authenticated endpoint).
        
        Returns:
            Account information
        """
        return self._make_request("/api/v3/account", signed=True)