"""
aGENtrader v2 Mock Data Provider

This module provides a mock data provider for testing purposes.
It generates synthetic market data that closely resembles real market data
but is consistent and deterministic for reliable testing.
"""

import numpy as np
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class MockDataProvider:
    """
    Mock data provider for testing.
    
    This class generates synthetic market data for testing purposes,
    with configurable parameters to simulate different market conditions.
    """
    
    def __init__(
        self,
        symbol: str = "BTC/USDT",
        seed: int = 42,
        trend_bias: float = 0.0,  # -1.0 (down) to 1.0 (up)
        volatility: float = 0.02,  # 0.01 = 1% daily volatility
        liquidity: float = 1.0,  # 0.0 (low) to 1.0 (high)
        price_range: tuple = (10000, 80000),  # (min, max) price
    ):
        """
        Initialize the mock data provider.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            seed: Random seed for reproducibility
            trend_bias: Bias for trend direction (-1.0 to 1.0)
            volatility: Price volatility (0.01 = 1% daily)
            liquidity: Market liquidity (0.0 to 1.0)
            price_range: Price range (min, max)
        """
        self.symbol = symbol
        self.seed = seed
        self.trend_bias = trend_bias
        self.volatility = volatility
        self.liquidity = liquidity
        self.price_range = price_range
        
        # Set random seed for reproducibility
        np.random.seed(seed)
        random.seed(seed)
        
        # Initialize with a price in the middle of the range
        self._current_price = np.mean(price_range)
        self._price_history = []
        self._generate_price_history()
        
        logger.info(f"MockDataProvider initialized for {symbol}")
        
    def _generate_price_history(self, days: int = 30):
        """
        Generate synthetic price history.
        
        Args:
            days: Number of days of history to generate
        """
        # Generate daily returns with trend bias and volatility
        daily_returns = np.random.normal(
            self.trend_bias * 0.001,  # Convert bias to daily return
            self.volatility,
            days
        )
        
        # Convert to price series starting from current price
        price = self._current_price
        for ret in daily_returns:
            price *= (1 + ret)
            
            # Ensure price stays within range
            price = max(self.price_range[0], min(price, self.price_range[1]))
            
            self._price_history.append(price)
        
        # Last price becomes current price
        self._current_price = self._price_history[-1]
        
    def _generate_ohlcv(
        self,
        base_price: float,
        timestamp: int,
        interval_seconds: int
    ) -> Dict[str, Any]:
        """
        Generate a single OHLCV candle.
        
        Args:
            base_price: Base price for the candle
            timestamp: Timestamp in milliseconds
            interval_seconds: Interval in seconds
            
        Returns:
            Dictionary with OHLCV data
        """
        # Generate random price movement
        daily_volatility = self.volatility
        interval_volatility = daily_volatility * np.sqrt(interval_seconds / 86400)
        
        # Add slight bias based on trend
        bias = self.trend_bias * interval_volatility * 0.1
        
        # Generate OHLC prices
        price_range = base_price * interval_volatility * 2
        open_price = base_price
        high_price = base_price + abs(np.random.normal(0, price_range))
        low_price = base_price - abs(np.random.normal(0, price_range))
        close_price = base_price * (1 + np.random.normal(bias, interval_volatility))
        
        # Ensure high is highest and low is lowest
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Generate volume based on volatility and liquidity
        base_volume = base_price * 10 * self.liquidity
        volume_multiplier = 1 + abs(np.random.normal(0, interval_volatility * 3))
        volume = base_volume * volume_multiplier
        
        return {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        }
        
    def get_current_price(self, symbol: Optional[str] = None) -> float:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading symbol (defaults to self.symbol)
            
        Returns:
            Current price as float
        """
        # Add small random noise to current price
        noise = np.random.normal(0, self._current_price * 0.0005)
        return self._current_price + noise
        
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
            symbol: Trading symbol (defaults to self.symbol)
            interval: Time interval (e.g., "1h", "4h", "1d")
            limit: Maximum number of records to return
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            List of OHLCV records
        """
        symbol = symbol or self.symbol
        
        # Convert interval to seconds
        interval_map = {
            "1m": 60,
            "3m": 3 * 60,
            "5m": 5 * 60,
            "15m": 15 * 60,
            "30m": 30 * 60,
            "1h": 60 * 60,
            "2h": 2 * 60 * 60,
            "4h": 4 * 60 * 60,
            "6h": 6 * 60 * 60,
            "8h": 8 * 60 * 60,
            "12h": 12 * 60 * 60,
            "1d": 24 * 60 * 60,
            "3d": 3 * 24 * 60 * 60,
            "1w": 7 * 24 * 60 * 60,
            "1M": 30 * 24 * 60 * 60,
        }
        
        if interval not in interval_map:
            raise ValueError(f"Invalid interval: {interval}")
            
        interval_seconds = interval_map[interval]
        
        # Use current time as end time if not specified
        now = int(time.time() * 1000)
        end_time = end_time or now
        
        # Calculate start time if not specified
        if start_time is None:
            start_time = end_time - (interval_seconds * 1000 * limit)
            
        result = []
        current_ts = start_time
        
        # Generate candles from start to end time
        while current_ts < end_time and len(result) < limit:
            # Get the appropriate base price based on candle position
            candle_idx = len(result)
            if candle_idx < len(self._price_history):
                base_price = self._price_history[candle_idx]
            else:
                base_price = self._current_price
                
            candle = self._generate_ohlcv(base_price, current_ts, interval_seconds)
            result.append(candle)
            
            current_ts += interval_seconds * 1000
            
        return result
    
    def get_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current price ticker for a symbol.
        
        Args:
            symbol: Trading symbol (defaults to self.symbol)
            
        Returns:
            Current ticker data
        """
        symbol = symbol or self.symbol
        
        current_price = self.get_current_price(symbol)
        
        return {
            "symbol": symbol,
            "timestamp": int(time.time() * 1000),
            "datetime": datetime.now().isoformat(),
            "high": current_price * 1.01,
            "low": current_price * 0.99,
            "bid": current_price * 0.9998,
            "ask": current_price * 1.0002,
            "last": current_price,
            "volume": current_price * 5 * self.liquidity,
            "change": np.random.normal(self.trend_bias * 0.01, 0.005),
            "percentage": np.random.normal(self.trend_bias * 1.0, 0.5),
            "average": current_price * 0.9995,
            "baseVolume": current_price * 5 * self.liquidity / current_price,
            "quoteVolume": current_price * 5 * self.liquidity,
        }
    
    def fetch_market_depth(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch market depth (order book) data for a symbol.
        
        Args:
            symbol: Trading symbol (defaults to self.symbol)
            limit: Maximum number of price levels to return
            
        Returns:
            Dictionary containing bids and asks arrays
        """
        symbol = symbol or self.symbol
        
        current_price = self.get_current_price(symbol)
        
        bids = []
        asks = []
        
        # Generate bids (buy orders below current price)
        for i in range(limit):
            # Prices decrease as we go down the order book
            price_decrease = np.random.exponential(0.0001 * (i + 1)) * current_price
            price = current_price - price_decrease
            
            # Volume decreases with distance from current price
            volume = np.random.exponential(0.5) * current_price * self.liquidity * 10 / (i + 1)
            
            bids.append([price, volume])
            
        # Generate asks (sell orders above current price)
        for i in range(limit):
            # Prices increase as we go up the order book
            price_increase = np.random.exponential(0.0001 * (i + 1)) * current_price
            price = current_price + price_increase
            
            # Volume decreases with distance from current price
            volume = np.random.exponential(0.5) * current_price * self.liquidity * 10 / (i + 1)
            
            asks.append([price, volume])
            
        # Sort bids in descending order and asks in ascending order
        bids.sort(key=lambda x: x[0], reverse=True)
        asks.sort(key=lambda x: x[0])
        
        return {
            "symbol": symbol,
            "timestamp": int(time.time() * 1000),
            "datetime": datetime.now().isoformat(),
            "bids": bids,
            "asks": asks,
            "nonce": random.randint(1000000, 9999999)
        }
        
    def fetch_futures_open_interest(
        self,
        symbol: Optional[str] = None,
        interval: str = "4h",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch futures open interest data.
        
        Args:
            symbol: Trading symbol (defaults to self.symbol)
            interval: Time interval (e.g., "4h", "1d")
            limit: Maximum number of records to return
            
        Returns:
            List of open interest records
        """
        symbol = symbol or self.symbol
        
        # Convert interval to seconds
        interval_map = {
            "5m": 5 * 60,
            "15m": 15 * 60,
            "30m": 30 * 60,
            "1h": 60 * 60,
            "2h": 2 * 60 * 60,
            "4h": 4 * 60 * 60,
            "6h": 6 * 60 * 60,
            "12h": 12 * 60 * 60,
            "1d": 24 * 60 * 60,
        }
        
        if interval not in interval_map:
            raise ValueError(f"Invalid interval: {interval}")
            
        interval_seconds = interval_map[interval]
        
        # Use current time as end time
        now = int(time.time() * 1000)
        
        result = []
        base_open_interest = self._current_price * 1000 * self.liquidity
        current_ts = now - (interval_seconds * 1000 * limit)
        
        # Generate open interest data from start to end time
        for i in range(limit):
            open_interest = base_open_interest * (1 + np.random.normal(self.trend_bias * 0.001, 0.05))
            
            # Ensure open interest is positive
            open_interest = max(1000, open_interest)
            
            # Add long-short ratio with bias based on trend
            long_ratio = 0.5 + self.trend_bias * 0.1 + np.random.normal(0, 0.05)
            long_ratio = max(0.1, min(0.9, long_ratio))
            
            record = {
                "symbol": symbol,
                "timestamp": current_ts,
                "datetime": datetime.fromtimestamp(current_ts / 1000).isoformat(),
                "openInterest": open_interest,
                "openInterestValue": open_interest * self.get_current_price(),
                "longShortRatio": long_ratio / (1 - long_ratio),
                "longPosition": open_interest * long_ratio,
                "shortPosition": open_interest * (1 - long_ratio),
            }
            
            result.append(record)
            current_ts += interval_seconds * 1000
            
        return result

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including trading pairs and rules.
        
        Returns:
            Exchange information
        """
        return {
            "timezone": "UTC",
            "serverTime": int(time.time() * 1000),
            "rateLimits": [
                {
                    "rateLimitType": "REQUEST_WEIGHT",
                    "interval": "MINUTE",
                    "intervalNum": 1,
                    "limit": 1200
                }
            ],
            "exchangeFilters": [],
            "symbols": [
                {
                    "symbol": self.symbol.replace('/', ''),
                    "status": "TRADING",
                    "baseAsset": self.symbol.split('/')[0],
                    "quoteAsset": self.symbol.split('/')[1],
                    "baseAssetPrecision": 8,
                    "quoteAssetPrecision": 8,
                    "orderTypes": [
                        "LIMIT",
                        "MARKET",
                        "STOP_LOSS",
                        "STOP_LOSS_LIMIT",
                        "TAKE_PROFIT",
                        "TAKE_PROFIT_LIMIT",
                        "LIMIT_MAKER"
                    ],
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.00000100",
                            "maxPrice": "1000000.00000000",
                            "tickSize": "0.00000100"
                        },
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.00000100",
                            "maxQty": "9000.00000000",
                            "stepSize": "0.00000100"
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
            "balances": [
                {
                    "asset": "BTC",
                    "free": "1.0",
                    "locked": "0.0"
                },
                {
                    "asset": "USDT",
                    "free": "10000.0",
                    "locked": "0.0"
                }
            ]
        }