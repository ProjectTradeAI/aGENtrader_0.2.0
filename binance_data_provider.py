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
    
    # Separate URLs for futures API
    FUTURES_BASE_URL = "https://fapi.binance.com"
    FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"
    
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
        use_testnet: Optional[bool] = None  # Now determined by DEPLOY_ENV
    ):
        """
        Initialize the Binance API provider.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            use_testnet: Override environment setting for testnet (if provided)
            use_testnet: Whether to use Binance testnet (defaults to True to avoid geo restrictions)
        """
        # Use environment variables as fallback
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET")
        
        # Determine whether to use testnet based on environment if not explicitly provided
        if use_testnet is None:
            # Check DEPLOY_ENV first (ec2 = mainnet, replit/dev = testnet)
            deploy_env = os.environ.get("DEPLOY_ENV", "dev").lower()
            if deploy_env == "ec2":
                use_testnet = False
                logger.info("Using real Binance API for EC2 deployment")
            else:
                # Then check specific BINANCE_USE_TESTNET flag as fallback
                use_testnet_str = os.environ.get("BINANCE_USE_TESTNET", "true").lower()
                use_testnet = (use_testnet_str == "true")
        
        # Select base URL based on whether to use testnet
        self.base_url = self.TESTNET_URL if use_testnet else self.BASE_URL
        self.futures_url = self.FUTURES_TESTNET_URL if use_testnet else self.FUTURES_BASE_URL
        self.use_testnet = use_testnet
        
        # Set up rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # seconds between requests
        
        logger.info(f"Initialized Binance Data Provider using {'testnet' if use_testnet else 'mainnet'}")
        logger.info(f"Spot API: {self.base_url}")
        logger.info(f"Futures API: {self.futures_url}")
    
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
        signed: bool = False,
        use_futures_api: bool = False
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
        
        # Select appropriate base URL (futures or spot)
        base = self.futures_url if use_futures_api else self.base_url
        
        # Create full URL
        url = f"{base}{endpoint}"
        
        logger.debug(f"Making request to URL: {url} with params: {params}")
        
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
            
            # Handle 451 Geographic Restriction errors specially
            elif e.response.status_code == 451:
                logger.error(f"API access restricted due to geographic restrictions (451 error)")
                # This is a case where we should try a different API or proxy
                raise Exception("Geographic restriction (451) detected - Binance API not available in this region")
            
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
        
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker data for a symbol (alias for compatibility with other data providers).
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            
        Returns:
            Dictionary with ticker data including 'last' price
        """
        ticker_data = self.get_ticker(symbol)
        
        # Format to ensure compatibility with the expected interface
        formatted_ticker = {
            "symbol": symbol,
            "last": float(ticker_data.get("lastPrice", 0)),
            "bid": float(ticker_data.get("bidPrice", 0)),
            "ask": float(ticker_data.get("askPrice", 0)),
            "high": float(ticker_data.get("highPrice", 0)),
            "low": float(ticker_data.get("lowPrice", 0)),
            "volume": float(ticker_data.get("volume", 0)),
            "change": float(ticker_data.get("priceChange", 0)),
            "percentage": float(ticker_data.get("priceChangePercent", 0)),
            "timestamp": ticker_data.get("closeTime", int(time.time() * 1000))
        }
        
        return formatted_ticker
    
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
        
    def fetch_market_depth(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Fetch market depth (order book) data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            limit: Maximum number of price levels to return (max 5000)
            
        Returns:
            Dictionary containing bids and asks arrays
        """
        # Format symbol correctly (remove "/" if present)
        formatted_symbol = symbol.replace("/", "")
        
        # Limit must be one of: 5, 10, 20, 50, 100, 500, 1000, 5000
        valid_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
        if limit not in valid_limits:
            # Find the closest valid limit
            limit = min(valid_limits, key=lambda x: abs(x - limit))
            logger.info(f"Adjusted limit to nearest valid value: {limit}")
        
        params = {
            "symbol": formatted_symbol,
            "limit": limit
        }
        
        try:
            # Make request to the order book endpoint
            depth_data = self._make_request("/api/v3/depth", params=params)
            
            # Process the data
            result = {
                "timestamp": int(time.time() * 1000),  # Current timestamp in milliseconds
                "bids": [],
                "asks": [],
                "bid_total": 0.0,
                "ask_total": 0.0,
                "top_5_bid_volume": 0.0,
                "top_5_ask_volume": 0.0
            }
            
            # Format bids and calculate totals
            if "bids" in depth_data:
                # Bids are in format [price, quantity]
                result["bids"] = [[float(bid[0]), float(bid[1])] for bid in depth_data["bids"]]
                
                # Calculate total volume
                bid_total = sum(float(bid[0]) * float(bid[1]) for bid in depth_data["bids"])
                result["bid_total"] = bid_total
                
                # Calculate top 5 volume
                top_5_bid_volume = sum(float(bid[0]) * float(bid[1]) for bid in depth_data["bids"][:5])
                result["top_5_bid_volume"] = top_5_bid_volume
                
            # Format asks and calculate totals
            if "asks" in depth_data:
                # Asks are in format [price, quantity]
                result["asks"] = [[float(ask[0]), float(ask[1])] for ask in depth_data["asks"]]
                
                # Calculate total volume
                ask_total = sum(float(ask[0]) * float(ask[1]) for ask in depth_data["asks"])
                result["ask_total"] = ask_total
                
                # Calculate top 5 volume
                top_5_ask_volume = sum(float(ask[0]) * float(ask[1]) for ask in depth_data["asks"][:5])
                result["top_5_ask_volume"] = top_5_ask_volume
                
            # Calculate mid price and spread if possible
            if result["bids"] and result["asks"]:
                best_bid = float(result["bids"][0][0])
                best_ask = float(result["asks"][0][0])
                result["mid_price"] = (best_bid + best_ask) / 2
                result["spread"] = best_ask - best_bid
                result["spread_percent"] = (best_ask - best_bid) / best_bid * 100
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching market depth: {str(e)}")
            # Return empty structure
            return {
                "timestamp": int(time.time() * 1000),
                "bids": [],
                "asks": [],
                "bid_total": 0.0,
                "ask_total": 0.0
            }
            
    def fetch_funding_rates(
        self,
        symbol: Union[str, Dict[str, Any], None] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch funding rates for a futures symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT") or market data dictionary
            limit: Maximum number of records to return
            
        Returns:
            List of funding rate records
        """
        # Extract symbol string if market_data dictionary was passed
        if isinstance(symbol, dict):
            symbol_str = symbol.get('symbol', 'BTCUSDT')
        else:
            symbol_str = symbol or 'BTCUSDT'
        
        # Format symbol correctly (remove "/" if present)
        formatted_symbol = symbol_str.replace("/", "")
        
        try:
            # Prepare parameters
            params = {
                "symbol": formatted_symbol,
                "limit": limit
            }
            
            # Make request to the funding rate endpoint (futures API)
            funding_data = self._make_request(
                "/fapi/v1/fundingRate", 
                params=params,
                use_futures_api=True
            )
            
            # Format the response
            formatted_funding_data = []
            for item in funding_data:
                formatted_funding_data.append({
                    "symbol": formatted_symbol,
                    "rate": float(item["fundingRate"]),
                    "timestamp": int(item["fundingTime"]),
                    "time": int(item["fundingTime"])
                })
                
            return formatted_funding_data
            
        except Exception as e:
            logger.error(f"Error fetching funding rates: {str(e)}")
            # Return empty list on error
            return []
    
    def fetch_futures_open_interest(
        self,
        symbol: str,
        interval: str = "4h",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch futures open interest data from Binance.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "4h", "1d")
            limit: Maximum number of records to return
            
        Returns:
            List of open interest records
        """
        # Format symbol correctly - ensure it's in the right format for futures API
        formatted_symbol = symbol.replace("/", "")
        
        # Some pairs may need to be formatted differently, ensure proper format for futures
        if ":" not in formatted_symbol and "/" not in formatted_symbol:
            # If not already in proper format, try to parse and convert
            base_asset = formatted_symbol
            if "USDT" in formatted_symbol:
                base_asset = formatted_symbol.split("USDT")[0]
            
            # Ensure proper futures symbol format (usually just the base asset + USDT)
            formatted_symbol = f"{base_asset}USDT"
        
        # Log the symbol we're requesting
        logger.info(f"Requesting futures open interest for symbol: {formatted_symbol}")
        
        # Map interval to valid periods for openInterestHist endpoint
        period_map = {
            "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h",
            "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h", "1d": "1d"
        }
        period = period_map.get(interval, "4h")  # Default to 4h if invalid
        
        # Prepare parameters
        params = {
            "symbol": formatted_symbol,
            "period": period,
            "limit": limit
        }
        
        logger.info(f"Open interest params: {params}")
        
        # Try the appropriate endpoint with fallbacks to handle geographic restrictions
        futures_endpoints = []
        
        if self.use_testnet:
            # For testnet, use fapi endpoint first
            futures_endpoints.append({
                "endpoint": "/fapi/v1/openInterest",
                "is_historical": False,
                "description": "testnet current open interest"
            })
        else:
            # For mainnet, try multiple endpoints starting with the historical one
            futures_endpoints.extend([
                {
                    "endpoint": "/futures/data/openInterestHist", 
                    "is_historical": True,
                    "description": "mainnet historical open interest"
                },
                {
                    "endpoint": "/fapi/v1/openInterest", 
                    "is_historical": False,
                    "description": "mainnet current open interest"
                }
            ])
        
        # Try each endpoint in order until one works
        for endpoint_info in futures_endpoints:
            endpoint = endpoint_info["endpoint"]
            is_historical = endpoint_info["is_historical"]
            description = endpoint_info["description"]
            
            try:
                logger.info(f"Trying to fetch {description} from {endpoint}")
                
                if is_historical:
                    # For historical endpoints
                    data = self._make_request(endpoint, params=params, use_futures_api=True)
                    
                    # Ensure the response is a list
                    if not isinstance(data, list):
                        logger.warning(f"Unexpected response from {description}: {data}")
                        continue
                        
                    # Format the response
                    formatted_data = []
                    for item in data:
                        formatted_data.append({
                            "symbol": item.get("symbol", formatted_symbol),
                            "sumOpenInterest": float(item.get("sumOpenInterest", 0)),
                            "sumOpenInterestValue": float(item.get("sumOpenInterestValue", 0)),
                            "timestamp": item.get("timestamp", 0)
                        })
                    
                    logger.info(f"Successfully fetched {len(formatted_data)} futures open interest records from {description}")
                    return formatted_data
                else:
                    # For non-historical endpoints (current value only)
                    current_oi_data = self._make_request(endpoint, params={"symbol": formatted_symbol}, use_futures_api=True)
                    
                    # Create a historical-like structure with just the current data repeated
                    if isinstance(current_oi_data, dict) and "openInterest" in current_oi_data:
                        # Single current value, create a list of historical-like records
                        current_oi = float(current_oi_data.get("openInterest", 0))
                        current_time = int(time.time() * 1000)
                        current_price = self.get_current_price(formatted_symbol)
                        
                        # Create historical-like data with the current value
                        historical_data = []
                        for i in range(limit):
                            # Create timestamps going backward in time
                            timestamp = current_time - (i * self._get_interval_milliseconds(interval))
                            historical_data.append({
                                "symbol": formatted_symbol,
                                "sumOpenInterest": current_oi,
                                "sumOpenInterestValue": current_oi * current_price,
                                "timestamp": timestamp
                            })
                        
                        logger.info(f"Successfully created historical-like open interest data from current value ({current_oi}) via {description}")
                        return historical_data
                    else:
                        logger.warning(f"Unexpected response from {description}: {current_oi_data}")
                        continue
            except Exception as e:
                logger.warning(f"Error fetching from {description}: {str(e)}")
                continue  # Try the next endpoint
        
        # If all endpoints fail, return empty list
        logger.error("All Binance futures endpoints failed when trying to fetch open interest data")
        return []
    
    def _get_interval_milliseconds(self, interval: str) -> int:
        """
        Convert interval string to milliseconds.
        
        Args:
            interval: Time interval (e.g., "4h", "1d")
            
        Returns:
            Number of milliseconds
        """
        # Extract the number and unit
        if len(interval) < 2:
            return 3600000  # Default to 1h
            
        try:
            number = int(interval[:-1])
            unit = interval[-1].lower()
            
            if unit == 'm':
                return number * 60 * 1000
            elif unit == 'h':
                return number * 60 * 60 * 1000
            elif unit == 'd':
                return number * 24 * 60 * 60 * 1000
            elif unit == 'w':
                return number * 7 * 24 * 60 * 60 * 1000
            else:
                return 3600000  # Default to 1h
        except:
            return 3600000  # Default to 1h