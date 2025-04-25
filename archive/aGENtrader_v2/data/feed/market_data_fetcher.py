"""
Market Data Fetcher Base Class

This module defines the base class for different market data fetching implementations.
It provides a common interface for fetching market data from different sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class MarketDataFetcher(ABC):
    """
    Abstract base class for market data fetching.
    
    This class defines the interface that all market data fetchers
    must implement, regardless of the data source.
    """
    
    @abstractmethod
    def fetch_ohlcv(self, symbol: str, interval: str, 
                   limit: Optional[int] = None, 
                   start_time: Optional[str] = None,
                   end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data.
        
        Args:
            symbol: Trading pair symbol
            interval: Time interval (e.g., "1m", "1h", "1d")
            limit: Number of candles to fetch (optional)
            start_time: Start time in ISO8601 format (optional)
            end_time: End time in ISO8601 format (optional)
            
        Returns:
            List of OHLCV dictionaries
        """
        pass
    
    @abstractmethod
    def fetch_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current price data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with current price information
        """
        pass
    
    @abstractmethod
    def fetch_orderbook(self, symbol: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch orderbook data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            limit: Depth of the orderbook to fetch (optional)
            
        Returns:
            Dictionary with orderbook data
        """
        pass
    
    @abstractmethod
    def create_market_event(self, symbol: str, interval: Optional[str] = "1h") -> Dict[str, Any]:
        """
        Create a comprehensive market event with all available data.
        
        Args:
            symbol: Trading pair symbol
            interval: Time interval for OHLCV data
            
        Returns:
            Market event dictionary with all available data
        """
        pass