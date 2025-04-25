"""
Database Connector Module

This module provides a unified interface for database operations:
- Connecting to PostgreSQL database
- Executing queries
- Fetching and parsing results
"""

import os
import yaml
import json
import psycopg2
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from psycopg2.extras import RealDictCursor

# Import centralized logger
from utils.logger import get_logger

# Get module logger
logger = get_logger("database")

# Load configuration
def load_config(config_path: str = "../config/settings.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_path)
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Return default config
        return {
            "database": {
                "type": "postgres",
                "connection_string": os.getenv("DATABASE_URL", "")
            }
        }

class DatabaseConnector:
    """
    Database connector class for PostgreSQL operations.
    
    This class handles:
    - Connection management
    - Query execution
    - Result parsing and formatting
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connector.
        
        Args:
            connection_string: PostgreSQL connection string (optional)
        """
        self.logger = get_logger("database")
        
        # Load configuration
        self.config = load_config()
        self.db_config = self.config.get("database", {})
        
        # Get connection string from args, config, or environment
        # Handle the potential ${DATABASE_URL} placeholder in config
        config_conn_string = self.db_config.get("connection_string", "")
        if config_conn_string == "${DATABASE_URL}":
            config_conn_string = os.getenv("DATABASE_URL", "")
            
        self.connection_string = (
            connection_string or 
            config_conn_string or 
            os.getenv("DATABASE_URL", "")
        )
        
        if not self.connection_string:
            self.logger.error("No database connection string provided")
            raise ValueError("Database connection string is required")
        
        # Initialize connection to None
        self.conn = None
        self.cursor = None
        
        self.logger.info("Database connector initialized")
    
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            self.logger.info("Connected to database")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the database"""
        if self.cursor:
            self.cursor.close()
        
        if self.conn:
            self.conn.close()
            self.logger.info("Disconnected from database")
        
        self.conn = None
        self.cursor = None
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> bool:
        """
        Execute a query without returning results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            True if execution successful, False otherwise
        """
        if not self.conn or not self.cursor:
            if not self.connect():
                return False
        
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            self.logger.info("Query executed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            return False
    
    def query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of dictionaries containing query results
        """
        if not self.conn or not self.cursor:
            if not self.connect():
                return []
        
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            return []
    
    def query_as_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute a query and return results as pandas DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            Pandas DataFrame containing query results
        """
        results = self.query(query, params)
        return pd.DataFrame(results)
    
    def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Get market data for a specific symbol and interval.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Maximum number of records to retrieve
            
        Returns:
            Pandas DataFrame with market data
        """
        # Normalize symbol format (remove / if present)
        symbol = symbol.replace('/', '')
        
        query = """
        SELECT * FROM market_data 
        WHERE symbol = %s AND interval = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        return self.query_as_dataframe(query, (symbol, interval, limit))
    
    def get_market_depth(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Get market depth data for a specific symbol and interval.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Maximum number of records to retrieve
            
        Returns:
            Pandas DataFrame with market depth data
        """
        # Normalize symbol format (remove / if present)
        symbol = symbol.replace('/', '')
        
        query = """
        SELECT * FROM market_depth 
        WHERE symbol = %s AND interval = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        return self.query_as_dataframe(query, (symbol, interval, limit))
    
    def get_volume_profile(self, 
                          symbol: str, 
                          interval: str = '1h', 
                          time_period: str = '24h',
                          limit: int = 1000) -> pd.DataFrame:
        """
        Get volume profile data for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            time_period: Time period for analysis (e.g., '24h', '7d', '30d')
            limit: Maximum number of records to retrieve
            
        Returns:
            Pandas DataFrame with volume profile data
        """
        # Normalize symbol format (remove / if present)
        symbol = symbol.replace('/', '')
        
        query = """
        SELECT * FROM volume_profile 
        WHERE symbol = %s AND interval = %s AND time_period = %s
        ORDER BY timestamp DESC, price_level ASC
        LIMIT %s
        """
        
        return self.query_as_dataframe(query, (symbol, interval, time_period, limit))
    
    def get_funding_rates(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """
        Get funding rate data for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'BTCUSDT')
            limit: Maximum number of records to retrieve
            
        Returns:
            Pandas DataFrame with funding rate data
        """
        # Normalize symbol format (remove / if present)
        symbol = symbol.replace('/', '')
        
        query = """
        SELECT * FROM funding_rates 
        WHERE symbol = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        return self.query_as_dataframe(query, (symbol, limit))
    
    def get_tables(self) -> List[str]:
        """
        Get list of tables in the database.
        
        Returns:
            List of table names
        """
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        
        results = self.query(query)
        return [row['table_name'] for row in results]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column definitions
        """
        query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s
        """
        
        return self.query(query, (table_name,))

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create database connector
    db = DatabaseConnector()
    
    # Test connection
    if db.connect():
        print("Connected to database successfully")
        
        # Get list of tables
        tables = db.get_tables()
        print(f"Tables: {tables}")
        
        # Get sample market data
        market_data = db.get_market_data("BTCUSDT", "1h", 5)
        print(f"Market data:\n{market_data}")
        
        # Disconnect
        db.disconnect()
    else:
        print("Failed to connect to database")