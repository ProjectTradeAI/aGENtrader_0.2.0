"""
Market Data Module

Provides access to market data from various sources for use in trading systems.
Acts as a unified interface for retrieving market data regardless of source.
"""
import os
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta

# Try to import required libraries
try:
    import pandas as pd
    import numpy as np
    from sqlalchemy import create_engine, text
except ImportError:
    logging.warning("Required market data libraries not installed.")

# Import local modules
try:
    from data.storage.database import get_market_data as db_get_market_data
    from data.storage.database import get_available_symbols, get_available_intervals
    from data.storage.database import check_data_availability
except ImportError:
    logging.warning("Database module not found. Some functionality will be limited.")
    
    # Define placeholder functions if imports fail
    def db_get_market_data(*args, **kwargs):
        logging.error("Database module not available")
        return pd.DataFrame()
    
    def get_available_symbols():
        logging.error("Database module not available")
        return []
    
    def get_available_intervals(*args, **kwargs):
        logging.error("Database module not available")
        return []
    
    def check_data_availability(*args, **kwargs):
        logging.error("Database module not available")
        return {"available": False, "error": "Database module not available"}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataProvider:
    """
    Market data provider that aggregates data from multiple sources
    """
    
    def __init__(self):
        """Initialize the market data provider"""
        self.data_sources = {
            "database": {
                "enabled": True,
                "priority": 1,
                "get_data": db_get_market_data
            }
        }
        
        # Check for API keys for external data sources
        if os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_API_SECRET"):
            logger.info("Alpaca API credentials found")
            self.data_sources["alpaca"] = {
                "enabled": True,
                "priority": 2,
                "get_data": self._get_alpaca_data
            }
        
        # Sort data sources by priority
        self.data_sources_by_priority = sorted(
            self.data_sources.items(),
            key=lambda x: x[1]["priority"]
        )
    
    def _get_alpaca_data(self, symbol: str, interval: str, limit: int = 100,
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get market data from Alpaca API
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            limit: Maximum number of records
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with market data
        """
        # Implementation for Alpaca API would go here
        logger.info(f"Getting Alpaca data for {symbol} {interval}")
        return pd.DataFrame()
    
    def get_market_data(self, symbol: str, interval: str, limit: int = 100,
                      start_date: Optional[str] = None, end_date: Optional[str] = None,
                      source: Optional[str] = None) -> pd.DataFrame:
        """
        Get market data from available sources
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            limit: Maximum number of records
            start_date: Start date
            end_date: End date
            source: Specific source to use (optional)
            
        Returns:
            DataFrame with market data
        """
        # If source is specified, try to use it
        if source and source in self.data_sources:
            if self.data_sources[source]["enabled"]:
                logger.info(f"Using specified source: {source}")
                return self.data_sources[source]["get_data"](
                    symbol, interval, limit, start_date, end_date
                )
            else:
                logger.warning(f"Specified source {source} is not enabled")
        
        # Try sources in priority order
        for source_name, source_config in self.data_sources_by_priority:
            if source_config["enabled"]:
                logger.info(f"Trying source: {source_name}")
                data = source_config["get_data"](
                    symbol, interval, limit, start_date, end_date
                )
                
                if not data.empty:
                    logger.info(f"Got data from source: {source_name}")
                    return data
        
        # If we get here, we couldn't get data from any source
        logger.warning(f"No data available for {symbol} {interval}")
        return pd.DataFrame()
    
    def check_data_available(self, symbol: str, interval: str,
                           start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if data is available from any source
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with availability information
        """
        # Use the database check function
        return check_data_availability(symbol, interval, start_date, end_date)

# Create a singleton instance
market_data_provider = MarketDataProvider()

# Helper functions for easier access
def get_market_data(symbol: str, interval: str, limit: int = 100,
                   start_date: Optional[str] = None, end_date: Optional[str] = None,
                   source: Optional[str] = None) -> pd.DataFrame:
    """Get market data using the provider"""
    return market_data_provider.get_market_data(
        symbol, interval, limit, start_date, end_date, source
    )

def check_data_available(symbol: str, interval: str,
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Check if data is available"""
    return market_data_provider.check_data_available(
        symbol, interval, start_date, end_date
    )

def compute_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators on market data
    
    Args:
        data: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added technical indicators
    """
    # Check if data is empty
    if data.empty:
        return data
    
    # Make a copy to avoid modifying the original
    df = data.copy()
    
    try:
        # Simple Moving Averages
        df['SMA_5'] = df['close'].rolling(window=5).mean()
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Relative Strength Index (RSI)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        df['BB_Std'] = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + 2 * df['BB_Std']
        df['BB_Lower'] = df['BB_Middle'] - 2 * df['BB_Std']
        
        # Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close_prev = (df['high'] - df['close'].shift(1)).abs()
        low_close_prev = (df['low'] - df['close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()
        
        # Returns
        df['Daily_Return'] = df['close'].pct_change() * 100
        
        return df
    except Exception as e:
        logger.error(f"Error computing technical indicators: {str(e)}")
        return data

def format_market_data(data: pd.DataFrame, format_type: str = 'json') -> Union[str, pd.DataFrame]:
    """
    Format market data for output
    
    Args:
        data: DataFrame with market data
        format_type: Output format ('json', 'markdown', 'text', 'dataframe')
        
    Returns:
        Formatted data as specified type
    """
    if data.empty:
        if format_type == 'json':
            return '{"error": "No data available"}'
        elif format_type == 'markdown':
            return "## Market Data\n\nNo data available."
        elif format_type == 'text':
            return "Market Data: No data available."
        else:
            return data
    
    # Format based on type
    if format_type == 'dataframe':
        return data
    elif format_type == 'json':
        return data.to_json(orient='records', date_format='iso')
    elif format_type == 'markdown':
        md = "## Market Data\n\n"
        md += data.to_markdown(index=False)
        return md
    elif format_type == 'text':
        text = "Market Data:\n"
        text += data.to_string(index=False)
        return text
    else:
        logger.warning(f"Unknown format type: {format_type}")
        return data.to_json(orient='records')

# If executed as a script, run a simple test
if __name__ == "__main__":
    print("Testing market data access...")
    symbols = get_available_symbols()
    print(f"Available symbols: {symbols}")
    
    if symbols:
        symbol = symbols[0]
        intervals = get_available_intervals(symbol)
        print(f"Available intervals for {symbol}: {intervals}")
        
        if intervals:
            interval = intervals[0]
            availability = check_data_available(symbol, interval)
            print(f"Data availability for {symbol} {interval}: {availability}")
            
            if availability.get("available", False):
                data = get_market_data(symbol, interval, limit=10)
                print(f"Sample data for {symbol} {interval}:")
                print(data.head())
                
                # Compute technical indicators
                data_with_indicators = compute_technical_indicators(data)
                print("\nData with technical indicators:")
                print(data_with_indicators.head())