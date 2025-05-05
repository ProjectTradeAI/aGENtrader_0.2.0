"""
aGENtrader v2 Mock Data Provider

This module provides mock data services for testing and development
when access to real data sources is not needed or available.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

class MockDataProvider:
    """
    Mock data provider that generates realistic-looking market data for testing.
    
    This class implements the same interface as BinanceDataProvider
    but returns generated data instead of making actual API calls.
    """
    
    def __init__(
        self,
        symbol: str = "BTC/USDT",
        base_price: float = 50000.0,
        volatility: float = 0.02,
        volume_factor: float = 100.0,
        trend: str = "neutral"  # "up", "down", or "neutral"
    ):
        """
        Initialize the mock data provider.
        
        Args:
            symbol: The trading symbol to simulate
            base_price: The base price for the data
            volatility: Price volatility factor
            volume_factor: Volume multiplier
            trend: Price trend direction ("up", "down", or "neutral")
        """
        self.symbol = symbol
        self.base_price = base_price
        self.volatility = volatility
        self.volume_factor = volume_factor
        self.trend = trend.lower()
        
        # Seed with symbol to get consistent results for same symbol
        self._seed = sum(ord(c) for c in symbol)
        random.seed(self._seed)
        
        # Initialize current price
        self._current_price = self.base_price
        
        # Cache for consistent data
        self._ohlcv_cache = {}
        self._depth_cache = {}
        
    def get_current_price(self, symbol: Optional[str] = None) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            
        Returns:
            Current price as float
        """
        symbol = symbol or self.symbol
        
        # If we've already generated data for this symbol, use the last close price
        if symbol in self._ohlcv_cache:
            last_candle = self._ohlcv_cache[symbol][-1]
            return last_candle["close"]
            
        # Otherwise, return the base price with some randomness
        return self.base_price * (1 + (random.random() - 0.5) * 0.01)
        
    def _generate_mock_price_series(
        self,
        interval: str,
        limit: int,
        start_timestamp: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a series of realistic-looking price data.
        
        Args:
            interval: Time interval for the data
            limit: Number of data points to generate
            start_timestamp: Starting timestamp for the data
            
        Returns:
            List of OHLCV dictionaries
        """
        # Set the trend coefficients
        trend_coefficients = {
            "up": 0.55,     # 55% chance of price increase
            "down": 0.45,   # 45% chance of price increase (i.e., 55% chance of decrease)
            "neutral": 0.5  # 50-50 chance
        }
        trend_coef = trend_coefficients.get(self.trend, 0.5)
        
        # Determine the interval in seconds
        interval_seconds = self._parse_interval_to_seconds(interval)
        
        # Set the starting timestamp
        if start_timestamp is None:
            # Default to now - (limit * interval)
            start_timestamp = int(time.time() * 1000) - (limit * interval_seconds * 1000)
            
        result = []
        current_price = self.base_price
        
        for i in range(limit):
            # Calculate timestamp for this candle
            timestamp = start_timestamp + (i * interval_seconds * 1000)
            
            # Generate a random price change
            price_change_pct = (random.random() - (1 - trend_coef)) * self.volatility
            
            # Add some mean reversion based on distance from base price
            mean_reversion = (self.base_price - current_price) / self.base_price * 0.1
            price_change_pct += mean_reversion
            
            # Apply the price change
            current_price *= (1 + price_change_pct)
            
            # Generate the candle data
            open_price = current_price
            
            # Add some intra-candle volatility
            high_price = open_price * (1 + random.random() * self.volatility * 0.5)
            low_price = open_price * (1 - random.random() * self.volatility * 0.5)
            
            # Ensure high is always the highest price
            high_price = max(high_price, open_price)
            
            # Ensure low is always the lowest price
            low_price = min(low_price, open_price)
            
            # Generate the close price with bias based on the trend
            if random.random() < trend_coef:
                # Trending up, close likely higher than open
                close_price = open_price * (1 + random.random() * self.volatility * 0.3)
            else:
                # Trending down, close likely lower than open
                close_price = open_price * (1 - random.random() * self.volatility * 0.3)
                
            # Apply some additional constraints to ensure realistic candle
            # Make sure high is higher than close
            high_price = max(high_price, close_price)
            
            # Make sure low is lower than close
            low_price = min(low_price, close_price)
            
            # Generate volume with some randomness
            volume = self.volume_factor * (1 + random.random())
            
            # Format the data similar to Binance API response
            candle_data = {
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp / 1000).isoformat(),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(volume, 2)
            }
            
            result.append(candle_data)
            
            # Update the current price for the next iteration
            current_price = close_price
            
        # Store the last generated price as current price
        self._current_price = result[-1]["close"] if result else self.base_price
        
        return result
        
    def _parse_interval_to_seconds(self, interval: str) -> int:
        """
        Convert an interval string to seconds.
        
        Args:
            interval: Time interval (e.g., "1h", "4h", "1d")
            
        Returns:
            Number of seconds
        """
        unit = interval[-1]
        value = int(interval[:-1])
        
        # Convert the interval to seconds
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 60 * 60
        elif unit == 'd':
            return value * 24 * 60 * 60
        elif unit == 'w':
            return value * 7 * 24 * 60 * 60
        elif unit == 'M':
            return value * 30 * 24 * 60 * 60
        else:
            # Default to seconds if unit is not recognized
            return value
        
    def fetch_ohlcv(
        self,
        symbol: Optional[str] = None,
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
        symbol = symbol or self.symbol
        
        # Normalize symbol format
        if '/' in symbol:
            cache_key = symbol
        else:
            # Convert BTCUSDT to BTC/USDT
            if len(symbol) > 6 and symbol.endswith(('USDT', 'BUSD', 'USDC')):
                base = symbol[:-4]
                quote = symbol[-4:]
                cache_key = f"{base}/{quote}"
            elif len(symbol) > 3 and symbol.endswith(('BTC', 'ETH')):
                base = symbol[:-3]
                quote = symbol[-3:]
                cache_key = f"{base}/{quote}"
            else:
                cache_key = symbol
        
        # Create a cache key including interval and start/end times
        cache_params = f"{interval}:{limit}:{start_time}:{end_time}"
        full_cache_key = f"{cache_key}:{cache_params}"
        
        # Check if we already have this data cached
        if full_cache_key in self._ohlcv_cache:
            return self._ohlcv_cache[full_cache_key]
        
        # Generate new data
        data = self._generate_mock_price_series(interval, limit, start_time)
        
        # Cache the data for consistency
        self._ohlcv_cache[full_cache_key] = data
        
        return data
        
    def fetch_market_depth(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, List[List[float]]]:
        """
        Fetch market depth (order book) data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            limit: Maximum number of price levels to return
            
        Returns:
            Dictionary containing bids and asks arrays
        """
        symbol = symbol or self.symbol
        
        # Check cache first
        cache_key = f"{symbol}:{limit}"
        if cache_key in self._depth_cache:
            return self._depth_cache[cache_key]
        
        # Get the current price
        current_price = self.get_current_price(symbol)
        
        # Generate bid and ask orders around the current price
        bids = []
        asks = []
        
        # Set the range for price deviations
        price_range_pct = 0.05  # 5% range
        
        # Generate bids (buy orders below current price)
        for i in range(limit):
            # Price decreases as we go down the order book
            price_decrease = (i / limit) * price_range_pct
            price = current_price * (1 - price_decrease)
            
            # Higher volume near the current price, decreasing as we go down
            volume = self.volume_factor * (1 - i/limit) * (0.5 + random.random())
            
            bids.append([round(price, 2), round(volume, 6)])
        
        # Generate asks (sell orders above current price)
        for i in range(limit):
            # Price increases as we go up the order book
            price_increase = (i / limit) * price_range_pct
            price = current_price * (1 + price_increase)
            
            # Higher volume near the current price, decreasing as we go up
            volume = self.volume_factor * (1 - i/limit) * (0.5 + random.random())
            
            asks.append([round(price, 2), round(volume, 6)])
        
        # Sort bids in descending order by price
        bids.sort(key=lambda x: x[0], reverse=True)
        
        # Sort asks in ascending order by price
        asks.sort(key=lambda x: x[0])
        
        result = {
            "bids": bids,
            "asks": asks
        }
        
        # Cache the result
        self._depth_cache[cache_key] = result
        
        return result
        
    def fetch_futures_open_interest(
        self,
        symbol: Optional[str] = None,
        interval: str = "4h",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch futures open interest data.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "4h", "1d")
            limit: Maximum number of records to return
            
        Returns:
            List of open interest records
        """
        symbol = symbol or self.symbol
        
        # Convert to standardized format
        if '/' in symbol:
            # Convert BTC/USDT to BTCUSDT
            symbol = symbol.replace('/', '')
        
        # Generate mock open interest data based on price trends
        interval_seconds = self._parse_interval_to_seconds(interval)
        
        # Get price data to correlate with open interest
        price_data = self.fetch_ohlcv(symbol, interval, limit)
        
        result = []
        base_open_interest = 1000000.0  # $1,000,000 base value
        
        for i, candle in enumerate(price_data):
            timestamp = candle["timestamp"]
            
            # Calculate open interest with some correlation to price changes
            # and some random variance
            price = candle["close"]
            price_change = 0.0
            
            if i > 0:
                prev_price = price_data[i-1]["close"]
                price_change = (price - prev_price) / prev_price
            
            # Open interest often follows price trend with some lag and variance
            oi_change = price_change * 0.7 + (random.random() - 0.5) * 0.05
            
            # Add trend bias
            if self.trend == "up":
                oi_change += 0.01  # Small increase in OI for uptrend
            elif self.trend == "down":
                oi_change -= 0.01  # Small decrease in OI for downtrend
                
            open_interest = base_open_interest * (1 + oi_change)
            
            # Add some randomness to avoid perfectly correlated data
            open_interest *= (0.95 + 0.1 * random.random())
            
            record = {
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp / 1000).isoformat(),
                "open_interest": round(open_interest, 2),
                "open_interest_value": round(open_interest * price, 2),
                "symbol": symbol
            }
            
            result.append(record)
            
            # Update base for next iteration
            base_open_interest = open_interest
            
        return result
        
    def get_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current price ticker for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Current ticker data
        """
        symbol = symbol or self.symbol
        
        # Normalize symbol format
        if '/' in symbol:
            # Convert BTC/USDT to BTCUSDT
            symbol_formatted = symbol.replace('/', '')
        else:
            symbol_formatted = symbol
            
        # Get current price
        price = self.get_current_price(symbol)
        
        # Generate mock 24h data
        price_change = price * (random.random() - 0.5) * 0.05
        price_change_percent = (price_change / price) * 100
        
        # 24h high and low around current price
        high_24h = price * (1 + random.random() * 0.03)
        low_24h = price * (1 - random.random() * 0.03)
        
        # Ensure high is higher than current price and low is lower
        high_24h = max(high_24h, price)
        low_24h = min(low_24h, price)
        
        # Generate volume
        volume_24h = self.volume_factor * 24 * (0.8 + 0.4 * random.random())
        
        return {
            "symbol": symbol_formatted,
            "price": str(round(price, 2)),
            "priceChange": str(round(price_change, 2)),
            "priceChangePercent": str(round(price_change_percent, 2)),
            "highPrice": str(round(high_24h, 2)),
            "lowPrice": str(round(low_24h, 2)),
            "volume": str(round(volume_24h, 2)),
            "quoteVolume": str(round(volume_24h * price, 2)),
            "lastPrice": str(round(price, 2)),
            "lastQty": str(round(random.random() * 10, 6)),
            "openPrice": str(round(price - price_change, 2)),
            "prevClosePrice": str(round(price - price_change, 2)),
            "bidPrice": str(round(price * 0.999, 2)),
            "bidQty": str(round(random.random() * 10, 6)),
            "askPrice": str(round(price * 1.001, 2)),
            "askQty": str(round(random.random() * 10, 6)),
            "openTime": int(time.time() * 1000) - 24 * 60 * 60 * 1000,
            "closeTime": int(time.time() * 1000),
            "count": int(10000 * random.random())
        }
        
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including trading pairs and rules.
        
        Returns:
            Exchange information
        """
        # Generate basic exchange info similar to Binance
        return {
            "timezone": "UTC",
            "serverTime": int(time.time() * 1000),
            "rateLimits": [
                {
                    "rateLimitType": "REQUEST_WEIGHT",
                    "interval": "MINUTE",
                    "intervalNum": 1,
                    "limit": 1200
                },
                {
                    "rateLimitType": "ORDERS",
                    "interval": "SECOND",
                    "intervalNum": 10,
                    "limit": 50
                },
                {
                    "rateLimitType": "ORDERS",
                    "interval": "DAY",
                    "intervalNum": 1,
                    "limit": 160000
                }
            ],
            "exchangeFilters": [],
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "baseAssetPrecision": 8,
                    "quoteAsset": "USDT",
                    "quotePrecision": 8,
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01",
                            "maxPrice": "1000000.0",
                            "tickSize": "0.01"
                        },
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00001000",
                            "maxQty": "9000.00000000",
                            "stepSize": "0.00001000"
                        }
                    ]
                },
                {
                    "symbol": "ETHUSDT",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "baseAssetPrecision": 8,
                    "quoteAsset": "USDT",
                    "quotePrecision": 8,
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01",
                            "maxPrice": "100000.0",
                            "tickSize": "0.01"
                        },
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.0001000",
                            "maxQty": "9000.00000000",
                            "stepSize": "0.0001000"
                        }
                    ]
                }
            ]
        }
        
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information (authenticated endpoint).
        
        Returns:
            Account information
        """
        # Mock account info with some random balances
        balances = [
            {
                "asset": "BTC",
                "free": str(round(random.random() * 2, 8)),
                "locked": "0.00000000"
            },
            {
                "asset": "ETH",
                "free": str(round(random.random() * 20, 8)),
                "locked": "0.00000000"
            },
            {
                "asset": "USDT",
                "free": str(round(random.random() * 10000 + 1000, 2)),
                "locked": "0.00"
            }
        ]
        
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": balances,
            "permissions": ["SPOT"]
        }