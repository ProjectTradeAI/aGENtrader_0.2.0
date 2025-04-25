#!/usr/bin/env python3
"""
Market Data Utilities for Backtesting

This module provides functions for retrieving and processing authentic
market data from the database for use in backtesting.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('market_data')

def get_database_connection():
    """
    Get a connection to the market data database
    
    Returns:
        Database connection or None if connection fails
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Get database URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable is not set")
            return None
            
        # Connect to database
        conn = psycopg2.connect(database_url)
        logger.info("Connected to market data database")
        return conn
        
    except ImportError:
        logger.error("psycopg2 module not found. Please install it with: pip install psycopg2-binary")
        return None
        
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_available_symbols() -> List[str]:
    """
    Get a list of available trading symbols in the database
    
    Returns:
        List of available symbols
    """
    conn = get_database_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        
        # Query to get distinct symbols from klines_1h
        cursor.execute("""
        SELECT DISTINCT symbol
        FROM klines_1h
        ORDER BY symbol
        """)
        
        # Get results
        symbols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return symbols
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {str(e)}")
        if conn:
            conn.close()
        return []

def get_available_intervals() -> List[str]:
    """
    Get a list of available time intervals in the database
    
    Returns:
        List of available intervals
    """
    conn = get_database_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        
        # Query to get table names that look like klines_*
        cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'klines_%'
        ORDER BY table_name
        """)
        
        # Get results
        tables = [row[0] for row in cursor.fetchall()]
        
        # Extract intervals from table names
        intervals = [table.replace('klines_', '') for table in tables]
        
        cursor.close()
        conn.close()
        
        return intervals
        
    except Exception as e:
        logger.error(f"Error getting available intervals: {str(e)}")
        if conn:
            conn.close()
        return []

def get_date_range_for_symbol(symbol: str, interval: str = '1h') -> Dict[str, str]:
    """
    Get the available date range for a symbol and interval
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h')
        
    Returns:
        Dictionary with start_date and end_date in YYYY-MM-DD format
    """
    conn = get_database_connection()
    if not conn:
        return {'start_date': None, 'end_date': None}
        
    try:
        cursor = conn.cursor()
        
        table_name = f"klines_{interval}"
        
        # Query to get min and max dates
        cursor.execute(f"""
        SELECT 
            MIN(open_time),
            MAX(open_time)
        FROM {table_name}
        WHERE symbol = %s
        """, (symbol,))
        
        # Get results
        row = cursor.fetchone()
        if not row or not row[0] or not row[1]:
            cursor.close()
            conn.close()
            return {'start_date': None, 'end_date': None}
            
        # Format dates
        start_date = row[0].strftime('%Y-%m-%d')
        end_date = row[1].strftime('%Y-%m-%d')
        
        cursor.close()
        conn.close()
        
        return {'start_date': start_date, 'end_date': end_date}
        
    except Exception as e:
        logger.error(f"Error getting date range for {symbol}: {str(e)}")
        if conn:
            conn.close()
        return {'start_date': None, 'end_date': None}

def get_market_data(
    symbol: str,
    interval: str = '1h',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Get market data for a symbol and time range
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of data points to retrieve (optional)
        
    Returns:
        DataFrame with market data
    """
    conn = get_database_connection()
    if not conn:
        return pd.DataFrame()
        
    try:
        cursor = conn.cursor()
        
        table_name = f"klines_{interval}"
        
        # Build query
        query = f"""
        SELECT 
            open_time, 
            open, 
            high, 
            low, 
            close, 
            volume,
            close_time,
            quote_asset_volume,
            number_of_trades,
            taker_buy_base_asset_volume,
            taker_buy_quote_asset_volume
        FROM 
            {table_name}
        WHERE 
            symbol = %s
        """
        
        params = [symbol]
        
        # Add date filters if provided
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query += " AND open_time >= %s"
            params.append(start_dt)
            
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include the end date
            end_dt = end_dt + timedelta(days=1)
            query += " AND open_time < %s"
            params.append(end_dt)
            
        # Add order and limit
        query += " ORDER BY open_time ASC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
            
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        rows = cursor.fetchall()
        cursor.close()
        
        if not rows:
            logger.warning(f"No data found for {symbol} {interval}")
            conn.close()
            return pd.DataFrame()
            
        # Create DataFrame
        df = pd.DataFrame(rows, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume'
        ])
        
        # Convert types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_asset_volume', 'number_of_trades',
                          'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Add symbol column
        df['symbol'] = symbol
        
        conn.close()
        
        logger.info(f"Retrieved {len(df)} rows of {interval} data for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        if conn:
            conn.close()
        return pd.DataFrame()

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators for a DataFrame of market data
    
    Args:
        df: DataFrame with market data (must include OHLCV columns)
        
    Returns:
        DataFrame with added technical indicators
    """
    if df.empty:
        return df
        
    # Make a copy to avoid modifying the original
    result = df.copy()
    
    try:
        # Create simple moving averages
        result['sma_20'] = result['close'].rolling(window=20).mean()
        result['sma_50'] = result['close'].rolling(window=50).mean()
        result['sma_200'] = result['close'].rolling(window=200).mean()
        
        # Exponential moving averages
        result['ema_12'] = result['close'].ewm(span=12, adjust=False).mean()
        result['ema_26'] = result['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        result['macd'] = result['ema_12'] - result['ema_26']
        result['macd_signal'] = result['macd'].ewm(span=9, adjust=False).mean()
        result['macd_hist'] = result['macd'] - result['macd_signal']
        
        # RSI
        delta = result['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        # For the first 14 periods, use simple averages
        # For subsequent periods, use the EMA
        for i in range(14, len(result)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * 13 + gain.iloc[i]) / 14
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * 13 + loss.iloc[i]) / 14
            
        rs = avg_gain / avg_loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        result['bb_middle'] = result['close'].rolling(window=20).mean()
        result['bb_std'] = result['close'].rolling(window=20).std()
        result['bb_upper'] = result['bb_middle'] + 2 * result['bb_std']
        result['bb_lower'] = result['bb_middle'] - 2 * result['bb_std']
        
        # ATR (Average True Range)
        tr1 = result['high'] - result['low']
        tr2 = abs(result['high'] - result['close'].shift())
        tr3 = abs(result['low'] - result['close'].shift())
        result['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        result['atr'] = result['tr'].rolling(window=14).mean()
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return df

def save_market_data_to_file(df: pd.DataFrame, file_path: str) -> bool:
    """
    Save market data DataFrame to a file
    
    Args:
        df: DataFrame with market data
        file_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    if df.empty:
        logger.warning("Cannot save empty DataFrame")
        return False
        
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            df.to_csv(file_path, index=False)
        elif ext == '.json':
            df.to_json(file_path, orient='records', date_format='iso')
        elif ext == '.pkl' or ext == '.pickle':
            df.to_pickle(file_path)
        else:
            logger.warning(f"Unsupported file extension: {ext}. Using CSV format.")
            df.to_csv(file_path + '.csv', index=False)
            file_path = file_path + '.csv'
            
        logger.info(f"Saved market data to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving market data to {file_path}: {str(e)}")
        return False

def load_market_data_from_file(file_path: str) -> pd.DataFrame:
    """
    Load market data from a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        DataFrame with market data
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return pd.DataFrame()
            
        # Load based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext == '.json':
            df = pd.read_json(file_path, orient='records')
        elif ext == '.pkl' or ext == '.pickle':
            df = pd.read_pickle(file_path)
        else:
            logger.error(f"Unsupported file extension: {ext}")
            return pd.DataFrame()
            
        logger.info(f"Loaded market data from {file_path}")
        
        # Convert timestamp to datetime if it's a string
        if 'timestamp' in df.columns and isinstance(df['timestamp'].iloc[0], str):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        return df
        
    except Exception as e:
        logger.error(f"Error loading market data from {file_path}: {str(e)}")
        return pd.DataFrame()

def prepare_backtest_data(
    symbol: str,
    interval: str = '1h',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cache_dir: Optional[str] = None,
    use_cache: bool = True,
    calculate_technical_indicators: bool = True
) -> pd.DataFrame:
    """
    Prepare market data for backtesting
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        cache_dir: Directory to cache market data (optional)
        use_cache: Whether to use cached data if available
        calculate_technical_indicators: Whether to calculate technical indicators
        
    Returns:
        DataFrame with market data ready for backtesting
    """
    # Create a unique file name for this data request
    cache_file = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        
        start_str = start_date or 'earliest'
        end_str = end_date or 'latest'
        
        cache_file = os.path.join(
            cache_dir,
            f"{symbol}_{interval}_{start_str}_to_{end_str}.pkl"
        )
        
        # Check if cache file exists and should be used
        if use_cache and os.path.exists(cache_file):
            logger.info(f"Loading cached market data from {cache_file}")
            df = load_market_data_from_file(cache_file)
            if not df.empty:
                return df
                
    # Get market data
    df = get_market_data(
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date
    )
    
    if df.empty:
        logger.warning(f"No market data available for {symbol} {interval}")
        return df
        
    # Calculate technical indicators if requested
    if calculate_technical_indicators:
        df = calculate_indicators(df)
        
    # Cache the data if requested
    if cache_file:
        save_market_data_to_file(df, cache_file)
        
    return df

if __name__ == "__main__":
    # This can be run as a standalone script to test the market data functions
    
    print("Testing market data functions...")
    
    # Get available symbols
    symbols = get_available_symbols()
    print(f"\nAvailable symbols: {len(symbols)}")
    if symbols:
        print(f"Sample symbols: {symbols[:5]}")
        
    # Get available intervals
    intervals = get_available_intervals()
    print(f"\nAvailable intervals: {intervals}")
    
    # If we have symbols, get date range for first symbol
    if symbols:
        symbol = symbols[0]
        date_range = get_date_range_for_symbol(symbol)
        
        print(f"\nDate range for {symbol}:")
        print(f"  Start date: {date_range['start_date']}")
        print(f"  End date: {date_range['end_date']}")
        
        # Get sample market data
        if date_range['start_date'] and date_range['end_date']:
            # Calculate a week-long date range ending at the end date
            end_date = date_range['end_date']
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            start_dt = end_dt - timedelta(days=7)
            start_date = start_dt.strftime('%Y-%m-%d')
            
            print(f"\nGetting market data for {symbol} from {start_date} to {end_date}...")
            df = get_market_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                print(f"Retrieved {len(df)} rows of data")
                print("\nSample data:")
                print(df.head().to_string())
                
                # Calculate indicators
                print("\nCalculating technical indicators...")
                df_with_indicators = calculate_indicators(df)
                
                print("\nSample data with indicators:")
                # Select a subset of columns to display
                columns_to_show = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                  'sma_20', 'ema_12', 'rsi', 'macd']
                print(df_with_indicators[columns_to_show].head().to_string())
                
    print("\nMarket data testing complete.")