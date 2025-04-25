#!/usr/bin/env python
"""
DataProviderFactory for aGENtrader v2

This module provides a factory for creating data providers, enabling seamless
fallback between different data sources.
"""

import logging
import os
from typing import Dict, Any, Optional, List

# Setup logger
logger = logging.getLogger("aGENtrader.data_provider_factory")

class DataProviderFactory:
    """
    Factory for creating data providers with fallback capabilities.
    
    Responsibilities:
    - Create appropriate data provider based on configuration
    - Handle fallback between providers when one fails
    - Manage API keys and provider-specific configuration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data provider factory.
        
        Args:
            config: Configuration dictionary with parameters for providers
        """
        self.config = config or {}
        self.providers = []
        self._init_providers()
        
        logger.info(f"DataProviderFactory initialized with {len(self.providers)} providers")
    
    def _init_providers(self):
        """Initialize all available data providers in priority order."""
        # Import providers here to avoid circular imports
        from aGENtrader_v2.data.feed.binance_data_provider import BinanceDataProvider
        from aGENtrader_v2.data.feed.coinapi_fetcher import CoinAPIFetcher
        
        # Initialize Binance provider if configured
        if self.config.get("use_binance", True):
            try:
                binance_config = self.config.get("binance", {})
                binance_api_key = binance_config.get("api_key", os.environ.get("BINANCE_API_KEY", ""))
                binance_api_secret = binance_config.get("api_secret", os.environ.get("BINANCE_API_SECRET", ""))
                
                if binance_api_key and binance_api_secret:
                    binance_provider = BinanceDataProvider(
                        api_key=binance_api_key,
                        api_secret=binance_api_secret
                    )
                    self.providers.append(("binance", binance_provider))
                    logger.info("Binance data provider initialized")
                else:
                    logger.warning("Binance API keys not provided, skipping Binance provider")
            except ImportError:
                logger.warning("Binance provider module not available")
            except Exception as e:
                logger.error(f"Error initializing Binance provider: {e}")
        
        # Initialize CoinAPI provider (always available as fallback)
        try:
            coinapi_config = self.config.get("coinapi", {})
            coinapi_key = coinapi_config.get("key", os.environ.get("COINAPI_KEY", ""))
            
            if coinapi_key:
                coinapi_provider = CoinAPIFetcher(api_key=coinapi_key)
                self.providers.append(("coinapi", coinapi_provider))
                logger.info("CoinAPI data provider initialized")
            else:
                logger.warning("CoinAPI key not provided, using unauthenticated access")
                coinapi_provider = CoinAPIFetcher()
                self.providers.append(("coinapi", coinapi_provider))
        except Exception as e:
            logger.error(f"Error initializing CoinAPI provider: {e}")
    
    def create_provider(self, provider_name: Optional[str] = None):
        """
        Create a data provider instance.
        
        Args:
            provider_name: Specific provider to use (optional)
            
        Returns:
            Data provider instance
        """
        if not self.providers:
            logger.error("No data providers available")
            raise ValueError("No data providers initialized")
        
        # If specific provider requested, try to find it
        if provider_name:
            for name, provider in self.providers:
                if name.lower() == provider_name.lower():
                    logger.info(f"Using requested provider: {name}")
                    return provider
            
            logger.warning(f"Requested provider '{provider_name}' not available")
        
        # Use first (highest priority) provider
        logger.info(f"Using default provider: {self.providers[0][0]}")
        return self.providers[0][1]
    
    def fetch_ticker(self, symbol: str):
        """
        Fetch ticker data with fallback between providers.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data
        """
        errors = []
        
        # Try each provider in order until one succeeds
        for name, provider in self.providers:
            try:
                logger.debug(f"Fetching ticker for {symbol} using {name}")
                result = provider.fetch_ticker(symbol)
                logger.debug(f"Successfully fetched ticker with {name}")
                return result
            except Exception as e:
                logger.warning(f"Error fetching ticker with {name}: {e}")
                errors.append((name, str(e)))
        
        # If we get here, all providers failed
        error_details = "; ".join([f"{name}: {err}" for name, err in errors])
        raise Exception(f"All data providers failed to fetch ticker: {error_details}")
    
    def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100):
        """
        Fetch OHLCV data with fallback between providers.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            limit: Number of candles to fetch
            
        Returns:
            OHLCV data
        """
        errors = []
        
        # Try each provider in order until one succeeds
        for name, provider in self.providers:
            try:
                logger.debug(f"Fetching OHLCV for {symbol} on {interval} using {name}")
                result = provider.fetch_ohlcv(symbol, interval, limit)
                logger.debug(f"Successfully fetched OHLCV with {name}")
                return result
            except Exception as e:
                logger.warning(f"Error fetching OHLCV with {name}: {e}")
                errors.append((name, str(e)))
        
        # If we get here, all providers failed
        error_details = "; ".join([f"{name}: {err}" for name, err in errors])
        raise Exception(f"All data providers failed to fetch OHLCV: {error_details}")