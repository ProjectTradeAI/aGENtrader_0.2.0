"""
Database Access Module

Provides unified database access for market data storage and retrieval.
"""
import os
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta

try:
    from sqlalchemy import create_engine, text
    import pandas as pd
    import numpy as np
except ImportError:
    logging.warning("Required database libraries not installed. Install with: pip install sqlalchemy pandas numpy")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            connection_string: The database connection string. If None, uses DATABASE_URL environment variable.
        """
        self.connection_string = connection_string or os.environ.get('DATABASE_URL')
        self.engine = None
        
        if self.connection_string:
            try:
                self.engine = create_engine(self.connection_string)
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {str(e)}")
        else:
            logger.warning("No database connection string provided")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results as a list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        if not self.engine:
            logger.error("No database connection available")
            return []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return []
    
    def get_market_data(self, symbol: str, interval: str, limit: int = 100, 
                       start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve market data for a specific symbol and interval.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1m', '1h', '1d')
            limit: Maximum number of records to retrieve
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            
        Returns:
            DataFrame with market data
        """
        query = """
        SELECT * FROM market_data 
        WHERE symbol = :symbol AND interval = :interval
        """
        
        params = {"symbol": symbol, "interval": interval}
        
        if start_date:
            query += " AND timestamp >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND timestamp <= :end_date"
            params["end_date"] = end_date
            
        query += " ORDER BY timestamp DESC LIMIT :limit"
        params["limit"] = limit
        
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(text(query), conn, params=params)
        except Exception as e:
            logger.error(f"Failed to retrieve market data: {str(e)}")
            return pd.DataFrame()
    
    def get_available_symbols(self) -> List[str]:
        """
        Get a list of available trading symbols in the database.
        
        Returns:
            List of symbol strings
        """
        query = "SELECT DISTINCT symbol FROM market_data ORDER BY symbol"
        
        try:
            results = self.execute_query(query)
            return [row["symbol"] for row in results]
        except Exception as e:
            logger.error(f"Failed to retrieve symbols: {str(e)}")
            return []
    
    def get_available_intervals(self, symbol: Optional[str] = None) -> List[str]:
        """
        Get available time intervals for a symbol or all symbols.
        
        Args:
            symbol: Optional symbol to filter by
            
        Returns:
            List of interval strings
        """
        query = "SELECT DISTINCT interval FROM market_data"
        params = {}
        
        if symbol:
            query += " WHERE symbol = :symbol"
            params["symbol"] = symbol
            
        query += " ORDER BY interval"
        
        try:
            results = self.execute_query(query, params)
            return [row["interval"] for row in results]
        except Exception as e:
            logger.error(f"Failed to retrieve intervals: {str(e)}")
            return []
    
    def check_data_availability(self, symbol: str, interval: str, 
                              start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Check data availability for a specific symbol and interval.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary with availability information
        """
        query = """
        SELECT 
            MIN(timestamp) as first_date,
            MAX(timestamp) as last_date,
            COUNT(*) as count
        FROM market_data
        WHERE symbol = :symbol AND interval = :interval
        """
        
        params = {"symbol": symbol, "interval": interval}
        
        if start_date:
            query += " AND timestamp >= :start_date"
            params["start_date"] = start_date
            
        if end_date:
            query += " AND timestamp <= :end_date"
            params["end_date"] = end_date
        
        try:
            results = self.execute_query(query, params)
            
            if results and results[0]["count"] > 0:
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "available": True,
                    "first_date": results[0]["first_date"],
                    "last_date": results[0]["last_date"],
                    "count": results[0]["count"]
                }
            else:
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "available": False
                }
        except Exception as e:
            logger.error(f"Failed to check data availability: {str(e)}")
            return {
                "symbol": symbol,
                "interval": interval,
                "available": False,
                "error": str(e)
            }

# Create a singleton instance
db_manager = DatabaseManager()

# Helper functions for easier access
def get_market_data(symbol: str, interval: str, limit: int = 100, 
                    start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Retrieve market data using the database manager"""
    return db_manager.get_market_data(symbol, interval, limit, start_date, end_date)

def get_available_symbols() -> List[str]:
    """Get available symbols using the database manager"""
    return db_manager.get_available_symbols()

def get_available_intervals(symbol: Optional[str] = None) -> List[str]:
    """Get available intervals using the database manager"""
    return db_manager.get_available_intervals(symbol)

def check_data_availability(symbol: str, interval: str, 
                           start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Check data availability using the database manager"""
    return db_manager.check_data_availability(symbol, interval, start_date, end_date)

# If executed as a script, run a simple test
if __name__ == "__main__":
    print("Testing database connection...")
    symbols = get_available_symbols()
    print(f"Available symbols: {symbols}")
    
    if symbols:
        symbol = symbols[0]
        intervals = get_available_intervals(symbol)
        print(f"Available intervals for {symbol}: {intervals}")
        
        if intervals:
            interval = intervals[0]
            availability = check_data_availability(symbol, interval)
            print(f"Data availability for {symbol} {interval}: {availability}")
            
            data = get_market_data(symbol, interval, limit=5)
            print(f"Sample data for {symbol} {interval}:")
            print(data.head())