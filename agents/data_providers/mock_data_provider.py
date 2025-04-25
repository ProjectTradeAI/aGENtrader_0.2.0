"""
aGENtrader v2 Mock Data Provider

This module provides a mock data provider for demo mode when external APIs are unavailable.
It's used for testing and demonstration purposes only.
"""
import time
import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockDataProvider")

class MockDataProvider:
    """
    Mock data provider that generates synthetic market data for demo purposes.
    """
    
    def __init__(self, symbol: str = "BTCUSDT"):
        """
        Initialize the mock data provider.
        
        Args:
            symbol: Trading symbol to generate data for
        """
        self.symbol = symbol
        self.base_price = 50000.0 if symbol.startswith("BTC") else 3000.0
        logger.info(f"Initialized Mock Data Provider for {symbol}")
        
    def get_current_price(self, symbol: str) -> float:
        """
        Get a simulated current price.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Simulated current price
        """
        # Create a realistic-looking price with some randomness
        variation = self.base_price * 0.02 * random.random()
        price = self.base_price + (variation if random.random() > 0.5 else -variation)
        
        logger.info(f"Mock price for {symbol}: {price:.2f}")
        return price
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        interval: str = "1h", 
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch simulated OHLCV data.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            limit: Maximum number of records to return
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            List of simulated OHLCV records
        """
        now = datetime.now()
        data = []
        
        # Convert interval to seconds (approximately)
        if interval == "1m":
            interval_seconds = 60
        elif interval == "5m":
            interval_seconds = 300
        elif interval == "15m":
            interval_seconds = 900
        elif interval == "30m":
            interval_seconds = 1800
        elif interval == "1h":
            interval_seconds = 3600
        elif interval == "4h":
            interval_seconds = 14400
        elif interval == "1d":
            interval_seconds = 86400
        else:
            interval_seconds = 3600  # Default to 1h
        
        # Generate data
        for i in range(limit):
            candle_time = now - timedelta(seconds=interval_seconds * (limit - i))
            timestamp = int(candle_time.timestamp() * 1000)
            
            # Create realistic-looking price data
            base = self.base_price + (self.base_price * 0.1 * (random.random() - 0.5))
            price_range = base * 0.02
            
            open_price = base
            close_price = base + (price_range * (random.random() - 0.5))
            high_price = max(open_price, close_price) + (price_range * random.random())
            low_price = min(open_price, close_price) - (price_range * random.random())
            volume = self.base_price * 0.1 * random.random()
            
            data.append({
                "time": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "close_time": timestamp + interval_seconds * 1000 - 1,
                "quote_asset_volume": volume * ((open_price + close_price) / 2),
                "number_of_trades": int(100 * random.random()),
                "taker_buy_base_asset_volume": volume * 0.6,
                "taker_buy_quote_asset_volume": volume * 0.6 * ((open_price + close_price) / 2)
            })
        
        return data
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get simulated ticker data.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Simulated ticker data
        """
        current_price = self.get_current_price(symbol)
        
        return {
            "symbol": symbol,
            "priceChange": current_price * 0.01 * (random.random() - 0.5),
            "priceChangePercent": 0.01 * 100 * (random.random() - 0.5),
            "weightedAvgPrice": current_price * (1 + 0.005 * (random.random() - 0.5)),
            "prevClosePrice": current_price * (1 - 0.01 * random.random()),
            "lastPrice": current_price,
            "lastQty": 0.1 * random.random(),
            "bidPrice": current_price * (1 - 0.001 * random.random()),
            "bidQty": 0.5 * random.random(),
            "askPrice": current_price * (1 + 0.001 * random.random()),
            "askQty": 0.5 * random.random(),
            "openPrice": current_price * (1 - 0.02 * random.random()),
            "highPrice": current_price * (1 + 0.02 * random.random()),
            "lowPrice": current_price * (1 - 0.02 * random.random()),
            "volume": 100 * random.random(),
            "quoteVolume": 100 * current_price * random.random(),
            "openTime": int(time.time() * 1000) - 86400000,
            "closeTime": int(time.time() * 1000),
            "firstId": 123456789,
            "lastId": 123456889,
            "count": 100
        }
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get simulated exchange information.
        
        Returns:
            Simulated exchange info
        """
        return {
            "timezone": "UTC",
            "serverTime": int(time.time() * 1000),
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "baseAssetPrecision": 8,
                    "quoteAsset": "USDT",
                    "quotePrecision": 8,
                    "filters": []
                },
                {
                    "symbol": "ETHUSDT",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "baseAssetPrecision": 8,
                    "quoteAsset": "USDT",
                    "quotePrecision": 8,
                    "filters": []
                }
            ]
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get simulated account information.
        
        Returns:
            Simulated account information
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
                    "free": "0.01",
                    "locked": "0.0"
                },
                {
                    "asset": "ETH",
                    "free": "0.1",
                    "locked": "0.0"
                },
                {
                    "asset": "USDT",
                    "free": "10000.0",
                    "locked": "0.0"
                }
            ]
        }
    
    # Below are methods to maintain compatibility with the BinanceDataProvider interface
    def _make_request(self, endpoint: str, method: str = "GET", 
                      params: Optional[Dict[str, Any]] = None,
                      signed: bool = False) -> Dict[str, Any]:
        """Mock implementation of the make_request method."""
        return {"status": "ok", "msg": "mock request"}