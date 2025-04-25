"""
aGENtrader v2 Data Provider Adapter

This module implements an adapter that wraps the DataProviderFactory
to provide backward compatibility with the legacy CoinAPIFetcher interface.
"""

import logging
from typing import Dict, List, Any, Optional

from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory

logger = logging.getLogger('aGENtrader.data.provider_adapter')

class DataProviderAdapter:
    """
    Adapter class that wraps the DataProviderFactory to provide
    backward compatibility with the legacy CoinAPIFetcher interface.
    This allows the new provider to be used with existing code.
    """
    
    def __init__(self, provider_factory: DataProviderFactory):
        """
        Initialize the adapter with a DataProviderFactory.
        
        Args:
            provider_factory: The DataProviderFactory instance to wrap
        """
        self.provider_factory = provider_factory
        self.logger = logger
        self.logger.info("DataProviderAdapter initialized")
    
    def fetch_ohlcv(self, symbol: str, interval: str = "1d", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Legacy method for fetching OHLCV data, maps to the factory's get_ohlcv method.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            interval: Time interval (e.g., 1d, 4h, 1h)
            limit: Number of candles to retrieve
            
        Returns:
            List of OHLCV data dictionaries
            
        Raises:
            Exception: If data fetching fails
        """
        self.logger.debug(f"Adapter: Fetching OHLCV data for {symbol} at {interval} interval")
        return self.provider_factory.get_ohlcv(symbol, interval, limit)
    
    def fetch_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        Legacy method for fetching current price, maps to the factory's get_current_price method.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            
        Returns:
            Dictionary with current price information
            
        Raises:
            Exception: If data fetching fails
        """
        self.logger.debug(f"Adapter: Fetching current price for {symbol}")
        price = self.provider_factory.get_current_price(symbol)
        # Convert to CoinAPI-like response format
        return {'symbol': symbol, 'price': price}
    
    def fetch_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Legacy method for fetching order book, maps to the factory's get_order_book method.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            limit: Depth of the order book
            
        Returns:
            Order book dictionary
            
        Raises:
            Exception: If data fetching fails
        """
        self.logger.debug(f"Adapter: Fetching order book for {symbol}")
        return self.provider_factory.get_order_book(symbol, limit)
    
    def create_market_event(self, symbol: str) -> Dict[str, Any]:
        """
        Legacy method for creating a market event, maps to the factory's create_market_event method.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            
        Returns:
            Market event dictionary
            
        Raises:
            Exception: If data fetching fails
        """
        self.logger.debug(f"Adapter: Creating market event for {symbol}")
        return self.provider_factory.create_market_event(symbol)