"""
aGENtrader v2 Market Data Provider Factory

This module provides a factory for creating market data providers,
using Binance as the primary source with fallback to CoinAPI.
"""
import os
import logging
from typing import Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MarketDataProviderFactory")

class MarketDataProviderFactory:
    """
    Factory class for creating market data providers.
    
    This factory attempts to use Binance as the primary data source,
    with fallback to CoinAPI when Binance is unavailable or when specific
    data is not available through Binance.
    """
    
    def __init__(self):
        """Initialize the factory and check available providers."""
        self.binance_available = False
        self.coinapi_available = False
        self.binance_provider = None
        self.coinapi_provider = None
        
        # Check for Binance API
        binance_key = os.environ.get("BINANCE_API_KEY")
        binance_secret = os.environ.get("BINANCE_API_SECRET")
        
        if binance_key and binance_secret:
            try:
                from aGENtrader_v2.data.feed.binance_data_provider import BinanceDataProvider
                self.binance_provider = BinanceDataProvider(
                    api_key=binance_key,
                    api_secret=binance_secret
                )
                self.binance_available = True
                logger.info("Binance API provider initialized as primary data source")
            except ImportError:
                logger.warning("Binance data provider module not found")
            except Exception as e:
                logger.error(f"Failed to initialize Binance provider: {str(e)}")
        else:
            logger.warning("Binance API credentials not found in environment")
        
        # Check for CoinAPI
        coinapi_key = os.environ.get("COINAPI_KEY")
        
        if coinapi_key:
            try:
                # Import CoinAPI provider if available
                from coinapi_fetcher import CoinAPIFetcher
                self.coinapi_provider = CoinAPIFetcher(api_key=coinapi_key)
                self.coinapi_available = True
                logger.info("CoinAPI provider initialized as fallback data source")
            except ImportError:
                logger.warning("CoinAPI fetcher module not found")
            except Exception as e:
                logger.error(f"Failed to initialize CoinAPI provider: {str(e)}")
        else:
            logger.warning("CoinAPI key not found in environment")
            
        # Log availability status
        if not self.binance_available and not self.coinapi_available:
            logger.error("No market data providers available! System may not function correctly.")
        elif self.binance_available and not self.coinapi_available:
            logger.info("Using Binance API as the only data source (no fallback available)")
        elif not self.binance_available and self.coinapi_available:
            logger.info("Using CoinAPI as the primary data source (Binance not available)")
        else:
            logger.info("Using Binance as primary with CoinAPI fallback - optimal configuration")
    
    def get_provider(self, preferred: str = "binance"):
        """
        Get the appropriate market data provider based on availability.
        
        Args:
            preferred: Preferred provider ("binance" or "coinapi")
            
        Returns:
            Market data provider instance or None if no providers are available
        """
        if preferred.lower() == "binance":
            if self.binance_available:
                return self.binance_provider
            elif self.coinapi_available:
                logger.info("Binance provider not available, using CoinAPI fallback")
                return self.coinapi_provider
        elif preferred.lower() == "coinapi":
            if self.coinapi_available:
                return self.coinapi_provider
            elif self.binance_available:
                logger.info("CoinAPI provider not available, using Binance fallback")
                return self.binance_provider
        
        # If we get here, no providers are available
        logger.error("No market data providers available!")
        return None
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        interval: str = "1h", 
        limit: int = 100,
        provider: str = "binance"
    ):
        """
        Fetch OHLCV data using the appropriate provider.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            limit: Maximum number of records to return
            provider: Preferred provider to use
            
        Returns:
            List of OHLCV records or empty list if fetch fails
        """
        data_provider = self.get_provider(preferred=provider)
        
        if not data_provider:
            logger.error(f"No data provider available to fetch OHLCV data for {symbol}")
            return []
        
        try:
            # Format symbol if needed
            if hasattr(data_provider, 'fetch_ohlcv'):
                return data_provider.fetch_ohlcv(symbol, interval, limit)
            else:
                logger.error(f"Provider does not support fetch_ohlcv method")
                return []
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {str(e)}")
            
            # Try fallback if primary provider fails
            if provider.lower() == "binance" and self.coinapi_available:
                logger.info(f"Trying CoinAPI fallback for OHLCV data")
                try:
                    return self.coinapi_provider.fetch_ohlcv(symbol, interval, limit)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {str(e2)}")
                    return []
            elif provider.lower() == "coinapi" and self.binance_available:
                logger.info(f"Trying Binance fallback for OHLCV data")
                try:
                    return self.binance_provider.fetch_ohlcv(symbol, interval, limit)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {str(e2)}")
                    return []
            
            return []
    
    def get_current_price(self, symbol: str, provider: str = "binance") -> float:
        """
        Get current price for a trading pair.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            provider: Preferred provider to use
            
        Returns:
            Current price as float or 0.0 if fetch fails
        """
        data_provider = self.get_provider(preferred=provider)
        
        if not data_provider:
            logger.error(f"No data provider available to fetch current price for {symbol}")
            return 0.0
        
        try:
            # Check method availability
            if hasattr(data_provider, 'get_current_price'):
                return data_provider.get_current_price(symbol)
            else:
                logger.error(f"Provider does not support get_current_price method")
                return 0.0
        except Exception as e:
            logger.error(f"Error fetching current price: {str(e)}")
            
            # Try fallback if primary provider fails
            if provider.lower() == "binance" and self.coinapi_available:
                logger.info(f"Trying CoinAPI fallback for current price")
                try:
                    return self.coinapi_provider.get_current_price(symbol)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {str(e2)}")
                    return 0.0
            elif provider.lower() == "coinapi" and self.binance_available:
                logger.info(f"Trying Binance fallback for current price")
                try:
                    return self.binance_provider.get_current_price(symbol)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {str(e2)}")
                    return 0.0
            
            return 0.0