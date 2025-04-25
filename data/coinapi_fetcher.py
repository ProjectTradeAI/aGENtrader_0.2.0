"""
aGENtrader v2 CoinAPI Fetcher - Simplified Test Version

This module implements a simplified CoinAPIFetcher class for testing.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger('aGENtrader.data.coinapi')

class CoinAPIFetcher:
    """Simplified class for fetching cryptocurrency market data from CoinAPI."""
    
    BASE_URL = "https://rest.coinapi.io/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CoinAPI fetcher.
        
        Args:
            api_key: CoinAPI key
        """
        self.api_key = api_key or os.environ.get('COINAPI_KEY')
        
        if not self.api_key:
            logger.warning("No CoinAPI key provided.")
        else:
            logger.info(f"CoinAPI Fetcher initialized with key: {self.api_key[:4]}...{self.api_key[-4:]}")
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        interval: str = "1d", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Simplified mock method for testing - returns dummy data
        """
        logger.info(f"Mock fetch OHLCV for {symbol} at {interval} interval")
        
        # Return a simple mock data structure
        return [
            {
                "time_period_start": "2023-01-01T00:00:00.0000000Z",
                "time_period_end": "2023-01-01T01:00:00.0000000Z",
                "time_open": "2023-01-01T00:00:00.0000000Z",
                "time_close": "2023-01-01T00:59:59.0000000Z",
                "price_open": 20000.0,
                "price_high": 21000.0,
                "price_low": 19500.0,
                "price_close": 20500.0,
                "volume_traded": 100.0,
                "trades_count": 1000
            }
        ]