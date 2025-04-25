"""
Test Database Connection

This script tests the database connection and retrieves some basic market data.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test connection to the PostgreSQL database"""
    try:
        # Get database connection string from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not found")
            return False
        
        # Connect to the database
        conn = psycopg2.connect(db_url)
        logger.info("Database connection established")
        
        # Test a simple query
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            logger.info(f"Test query result: {result}")
        
        # Close the connection
        conn.close()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def get_available_symbols():
    """Get list of available trading symbols"""
    try:
        # Get database connection string from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not found")
            return []
        
        # Connect to the database
        conn = psycopg2.connect(db_url)
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT symbol FROM market_data
                    ORDER BY symbol
                """)
                symbols = [row[0] for row in cur.fetchall()]
                logger.info(f"Found {len(symbols)} symbols: {symbols}")
                return symbols
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        return []

def get_latest_prices(symbols):
    """Get the latest prices for symbols"""
    try:
        # Get database connection string from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not found")
            return {}
        
        # Connect to the database
        conn = psycopg2.connect(db_url)
        
        results = {}
        try:
            with conn.cursor() as cur:
                for symbol in symbols:
                    cur.execute("""
                        SELECT close, timestamp
                        FROM market_data
                        WHERE symbol = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (symbol,))
                    result = cur.fetchone()
                    if result:
                        price, timestamp = result
                        results[symbol] = {
                            "price": float(price),
                            "timestamp": timestamp.isoformat()
                        }
                        logger.info(f"{symbol}: ${float(price):.2f} at {timestamp}")
                    else:
                        logger.warning(f"No price data found for {symbol}")
            return results
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting latest prices: {str(e)}")
        return {}

def get_market_summary():
    """Get a summary of the market data"""
    try:
        # Get database connection string from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not found")
            return {}
        
        # Connect to the database
        conn = psycopg2.connect(db_url)
        
        try:
            with conn.cursor() as cur:
                # Get table counts
                cur.execute("""
                    SELECT table_name, 
                           (SELECT COUNT(*) FROM information_schema.columns 
                            WHERE table_name=t.table_name) as column_count,
                           (SELECT COUNT(*) FROM ONLY pg_catalog.pg_class c 
                            WHERE c.relname=t.table_name)::bigint as row_count
                    FROM (
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema='public'
                    ) t
                    ORDER BY table_name
                """)
                tables = []
                for table_name, column_count, row_count in cur.fetchall():
                    tables.append({
                        "name": table_name,
                        "columns": column_count,
                        "rows": row_count
                    })
                
                # Get available intervals for BTCUSDT
                cur.execute("""
                    SELECT interval, COUNT(*) as count, 
                           MIN(timestamp) as min_time, 
                           MAX(timestamp) as max_time
                    FROM market_data
                    WHERE symbol = 'BTCUSDT'
                    GROUP BY interval
                    ORDER BY interval
                """)
                intervals = []
                for interval, count, min_time, max_time in cur.fetchall():
                    intervals.append({
                        "interval": interval,
                        "count": count,
                        "start_date": min_time.isoformat(),
                        "end_date": max_time.isoformat()
                    })
                
                return {
                    "tables": tables,
                    "btcusdt_intervals": intervals
                }
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting market summary: {str(e)}")
        return {}

def main():
    """Main function to test database connection and queries"""
    # Test connection
    if not test_database_connection():
        logger.error("Database connection test failed")
        return
    
    # Get available symbols
    symbols = get_available_symbols()
    if not symbols:
        logger.warning("No symbols found in database")
    
    # Get latest prices
    prices = get_latest_prices(symbols[:5])  # First 5 symbols only
    if not prices:
        logger.warning("Could not retrieve latest prices")
    
    # Get market summary
    summary = get_market_summary()
    if summary:
        # Print tables
        logger.info("Database Tables:")
        for table in summary.get("tables", []):
            logger.info(f"  {table['name']}: {table['columns']} columns, {table['rows']} rows")
        
        # Print BTCUSDT intervals
        logger.info("BTCUSDT Data Intervals:")
        for interval in summary.get("btcusdt_intervals", []):
            logger.info(f"  {interval['interval']}: {interval['count']} records from {interval['start_date']} to {interval['end_date']}")
    else:
        logger.warning("Could not retrieve market summary")

if __name__ == "__main__":
    main()