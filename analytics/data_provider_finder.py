#!/usr/bin/env python
"""
DataProviderFinder for aGENtrader v2.1

A utility module to find the best available data provider for performance tracking.
It tries different data providers in sequence until finding one that works.
"""

import logging
from typing import Optional, Dict, Any, List, Callable

logger = logging.getLogger("aGENtrader.data_provider_finder")

class DataProviderFinder:
    """
    Utility to find the best available data provider for performance tracking.
    
    This class will try multiple data providers in sequence until finding one
    that successfully returns price data. This is useful for trade performance
    tracking where having access to current price data is essential.
    """
    
    def __init__(self, providers: Optional[List[Any]] = None):
        """
        Initialize the data provider finder.
        
        Args:
            providers: List of data provider instances to try
        """
        self.providers = providers or []
        self.active_provider = None
        self.last_success_index = -1
    
    def add_provider(self, provider: Any) -> None:
        """
        Add a data provider to the list.
        
        Args:
            provider: Data provider instance
        """
        self.providers.append(provider)
        logger.info(f"Added data provider: {provider.__class__.__name__}")
    
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker data for a symbol using the best available provider.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with ticker data or empty dict if all providers fail
        """
        # Try the last successful provider first
        if self.last_success_index >= 0 and self.last_success_index < len(self.providers):
            try:
                provider = self.providers[self.last_success_index]
                ticker = provider.fetch_ticker(symbol)
                self.active_provider = provider
                return ticker
            except Exception as e:
                logger.warning(f"Last successful provider failed: {e}")
        
        # Try all providers in sequence
        for i, provider in enumerate(self.providers):
            try:
                ticker = provider.fetch_ticker(symbol)
                logger.info(f"Successfully fetched ticker using {provider.__class__.__name__}")
                self.last_success_index = i
                self.active_provider = provider
                return ticker
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
        
        logger.error(f"All data providers failed to fetch ticker for {symbol}")
        return {}
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV data for a symbol using the best available provider.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for candles
            limit: Number of candles to fetch
            
        Returns:
            List of OHLCV candles or empty list if all providers fail
        """
        # Try the last successful provider first
        if self.last_success_index >= 0 and self.last_success_index < len(self.providers):
            try:
                provider = self.providers[self.last_success_index]
                ohlcv = provider.fetch_ohlcv(symbol, timeframe, limit)
                self.active_provider = provider
                return ohlcv
            except Exception as e:
                logger.warning(f"Last successful provider failed: {e}")
        
        # Try all providers in sequence
        for i, provider in enumerate(self.providers):
            try:
                ohlcv = provider.fetch_ohlcv(symbol, timeframe, limit)
                logger.info(f"Successfully fetched OHLCV using {provider.__class__.__name__}")
                self.last_success_index = i
                self.active_provider = provider
                return ohlcv
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
        
        logger.error(f"All data providers failed to fetch OHLCV for {symbol}")
        return []
    
    def get_active_provider(self) -> Optional[Any]:
        """
        Get the currently active provider.
        
        Returns:
            Active provider instance or None if no provider is active
        """
        return self.active_provider
    
    def create_provider(self) -> Any:
        """
        Factory method for compatibility with existing code that expects a factory.
        
        Returns:
            DataProviderFinder instance (self)
        """
        return self
    
    def is_available(self) -> bool:
        """
        Check if any data provider is available.
        
        Returns:
            True if at least one provider is available
        """
        return len(self.providers) > 0

# Helper functions for quickly creating a provider with common configurations

def create_factory_with_binance_coinapi(
    binance_api_key: Optional[str] = None,
    binance_api_secret: Optional[str] = None,
    coinapi_api_key: Optional[str] = None
) -> DataProviderFinder:
    """
    Create a factory with Binance and CoinAPI providers.
    
    Args:
        binance_api_key: Binance API key
        binance_api_secret: Binance API secret
        coinapi_api_key: CoinAPI key
        
    Returns:
        DataProviderFinder instance
    """
    finder = DataProviderFinder()
    
    # Try to import and add Binance provider
    if binance_api_key and binance_api_secret:
        try:
            from aGENtrader_v2.data.feed.binance_data_provider import BinanceDataProvider
            binance_provider = BinanceDataProvider(
                api_key=binance_api_key,
                api_secret=binance_api_secret
            )
            finder.add_provider(binance_provider)
            logger.info("Added Binance data provider")
        except Exception as e:
            logger.warning(f"Failed to add Binance provider: {e}")
    
    # Try to import and add CoinAPI provider
    if coinapi_api_key:
        try:
            from aGENtrader_v2.data.feed.coinapi_data_provider import CoinAPIDataProvider
            coinapi_provider = CoinAPIDataProvider(api_key=coinapi_api_key)
            finder.add_provider(coinapi_provider)
            logger.info("Added CoinAPI data provider")
        except Exception as e:
            logger.warning(f"Failed to add CoinAPI provider: {e}")
    
    return finder

def create_factory_from_environment() -> DataProviderFinder:
    """
    Create a factory using API keys from environment variables.
    
    Returns:
        DataProviderFinder instance
    """
    import os
    
    binance_api_key = os.environ.get("BINANCE_API_KEY")
    binance_api_secret = os.environ.get("BINANCE_API_SECRET")
    coinapi_api_key = os.environ.get("COINAPI_KEY")
    
    return create_factory_with_binance_coinapi(
        binance_api_key=binance_api_key,
        binance_api_secret=binance_api_secret,
        coinapi_api_key=coinapi_api_key
    )