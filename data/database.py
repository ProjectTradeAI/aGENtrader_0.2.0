"""
aGENtrader v2 Database Connector

This module provides a connector for interacting with the database.
"""

import os
import json
import logging
import sqlite3
import psycopg2
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

class DatabaseConnector:
    """
    Connector for interacting with the database.
    
    This connector supports both SQLite (for local development) and
    PostgreSQL (for production) databases.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the database connector.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        
        # Get database configuration
        self.db_type = self.config.get('db_type', os.environ.get('DB_TYPE', 'sqlite'))
        self.db_path = self.config.get('db_path', os.environ.get('DB_PATH', 'data/agentrader.db'))
        self.db_url = self.config.get('db_url', os.environ.get('DATABASE_URL'))
        
        # Initialize connection
        self.conn = None
        self.initialized = False
        
        # Connect to database
        try:
            self.connect()
            logger.info(f"Connected to {self.db_type} database")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
            
    def connect(self) -> None:
        """Connect to the database."""
        try:
            if self.db_type == 'sqlite':
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                
                # Connect to SQLite database
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            elif self.db_type == 'postgres':
                # Connect to PostgreSQL database
                if not self.db_url:
                    logger.error("DATABASE_URL environment variable not set")
                    return
                    
                self.conn = psycopg2.connect(self.db_url)
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return
            
            # Initialize database schema if needed
            if not self.initialized:
                self.initialize_schema()
                self.initialized = True
                
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
            self.conn = None
            
    def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def initialize_schema(self) -> None:
        """Initialize the database schema."""
        if not self.conn:
            logger.error("Cannot initialize schema: not connected to database")
            return
            
        try:
            cursor = self.conn.cursor()
            
            # Create market data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    data_source TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Create trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    decision_agent TEXT,
                    decision_confidence REAL,
                    execution_id TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Create decisions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT,
                    timestamp TEXT NOT NULL,
                    price REAL,
                    additional_data TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Commit changes
            self.conn.commit()
            logger.info("Database schema initialized")
            
        except Exception as e:
            logger.error(f"Error initializing schema: {str(e)}", exc_info=True)
            
    def execute(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """
        Execute a query and return the result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query result or None if error
        """
        if not self.conn:
            logger.error("Cannot execute query: not connected to database")
            return None
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            return None
            
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Row as dictionary or None if not found
        """
        cursor = self.execute(query, params)
        if not cursor:
            return None
            
        row = cursor.fetchone()
        if not row:
            return None
            
        if self.db_type == 'sqlite':
            return dict(row)
        else:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
            
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of rows as dictionaries
        """
        cursor = self.execute(query, params)
        if not cursor:
            return []
            
        rows = cursor.fetchall()
        if not rows:
            return []
            
        if self.db_type == 'sqlite':
            return [dict(row) for row in rows]
        else:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Insert data into a table.
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            ID of inserted row or None if error
        """
        if not self.conn:
            logger.error("Cannot insert data: not connected to database")
            return None
            
        try:
            # Add created_at timestamp
            if 'created_at' not in data:
                data['created_at'] = datetime.now().isoformat()
                
            # Create query
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            
            # Return last insert ID
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}", exc_info=True)
            return None
            
    def update(self, table: str, data: Dict[str, Any], condition: str, params: Tuple = ()) -> Optional[int]:
        """
        Update data in a table.
        
        Args:
            table: Table name
            data: Data to update
            condition: WHERE condition
            params: Condition parameters
            
        Returns:
            Number of rows updated or None if error
        """
        if not self.conn:
            logger.error("Cannot update data: not connected to database")
            return None
            
        try:
            # Create SET clause
            set_clause = ', '.join([f"{key} = ?" for key in data])
            
            # Create query
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(query, tuple(data.values()) + params)
            self.conn.commit()
            
            # Return number of rows affected
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}", exc_info=True)
            return None
            
    def delete(self, table: str, condition: str, params: Tuple = ()) -> Optional[int]:
        """
        Delete data from a table.
        
        Args:
            table: Table name
            condition: WHERE condition
            params: Condition parameters
            
        Returns:
            Number of rows deleted or None if error
        """
        if not self.conn:
            logger.error("Cannot delete data: not connected to database")
            return None
            
        try:
            # Create query
            query = f"DELETE FROM {table} WHERE {condition}"
            
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            
            # Return number of rows affected
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error deleting data: {str(e)}", exc_info=True)
            return None
            
    def get_market_data(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get market data for a symbol and interval.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            limit: Maximum number of records to return
            
        Returns:
            List of market data records
        """
        query = """
            SELECT * FROM market_data
            WHERE symbol = ? AND interval = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        return self.fetch_all(query, (symbol, interval, limit))
        
    def save_market_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Save market data to the database.
        
        Args:
            data: List of market data records
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            logger.error("Cannot save market data: not connected to database")
            return False
            
        try:
            cursor = self.conn.cursor()
            
            for record in data:
                # Check if record already exists
                query = """
                    SELECT id FROM market_data
                    WHERE symbol = ? AND interval = ? AND timestamp = ?
                """
                
                existing = self.fetch_one(query, (
                    record['symbol'],
                    record['interval'],
                    record['timestamp']
                ))
                
                if existing:
                    # Update existing record
                    self.update(
                        table='market_data',
                        data={
                            'open': record['open'],
                            'high': record['high'],
                            'low': record['low'],
                            'close': record['close'],
                            'volume': record['volume'],
                            'data_source': record.get('data_source', 'unknown')
                        },
                        condition='id = ?',
                        params=(existing['id'],)
                    )
                else:
                    # Insert new record
                    self.insert(
                        table='market_data',
                        data={
                            'symbol': record['symbol'],
                            'interval': record['interval'],
                            'timestamp': record['timestamp'],
                            'open': record['open'],
                            'high': record['high'],
                            'low': record['low'],
                            'close': record['close'],
                            'volume': record['volume'],
                            'data_source': record.get('data_source', 'unknown'),
                            'created_at': datetime.now().isoformat()
                        }
                    )
            
            return True
        except Exception as e:
            logger.error(f"Error saving market data: {str(e)}", exc_info=True)
            return False
            
    def log_decision(self, agent: str, signal: str, confidence: float, reason: str,
                     symbol: str, timestamp: str, price: Optional[float] = None,
                     additional_data: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Log a trading decision to the database.
        
        Args:
            agent: Name of the agent making the decision
            signal: Trading signal (BUY, SELL, HOLD)
            confidence: Confidence level (0-100)
            reason: Reason for the decision
            symbol: Trading symbol
            timestamp: Decision timestamp
            price: Current price (optional)
            additional_data: Additional data (optional)
            
        Returns:
            ID of inserted record or None if error
        """
        try:
            # Convert additional_data to JSON string
            additional_data_json = None
            if additional_data:
                additional_data_json = json.dumps(additional_data)
                
            # Insert decision
            return self.insert(
                table='decisions',
                data={
                    'agent': agent,
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'reason': reason,
                    'timestamp': timestamp,
                    'price': price,
                    'additional_data': additional_data_json,
                    'created_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error logging decision: {str(e)}", exc_info=True)
            return None
            
    def get_recent_decisions(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trading decisions.
        
        Args:
            symbol: Trading symbol (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of decision records
        """
        if symbol:
            query = """
                SELECT * FROM decisions
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            return self.fetch_all(query, (symbol, limit))
        else:
            query = """
                SELECT * FROM decisions
                ORDER BY timestamp DESC
                LIMIT ?
            """
            return self.fetch_all(query, (limit,))
            
    def log_trade(self, symbol: str, trade_type: str, price: float, quantity: float,
                  timestamp: str, status: str, decision_agent: Optional[str] = None,
                  decision_confidence: Optional[float] = None,
                  execution_id: Optional[str] = None) -> Optional[int]:
        """
        Log a trade to the database.
        
        Args:
            symbol: Trading symbol
            trade_type: Trade type (BUY, SELL)
            price: Trade price
            quantity: Trade quantity
            timestamp: Trade timestamp
            status: Trade status (EXECUTED, PENDING, FAILED)
            decision_agent: Name of the agent making the decision (optional)
            decision_confidence: Confidence level of the decision (optional)
            execution_id: External execution ID (optional)
            
        Returns:
            ID of inserted record or None if error
        """
        try:
            return self.insert(
                table='trades',
                data={
                    'symbol': symbol,
                    'type': trade_type,
                    'price': price,
                    'quantity': quantity,
                    'timestamp': timestamp,
                    'status': status,
                    'decision_agent': decision_agent,
                    'decision_confidence': decision_confidence,
                    'execution_id': execution_id,
                    'created_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error logging trade: {str(e)}", exc_info=True)
            return None
            
    def get_recent_trades(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trades.
        
        Args:
            symbol: Trading symbol (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of trade records
        """
        if symbol:
            query = """
                SELECT * FROM trades
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            return self.fetch_all(query, (symbol, limit))
        else:
            query = """
                SELECT * FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """
            return self.fetch_all(query, (limit,))