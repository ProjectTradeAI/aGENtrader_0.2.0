#!/usr/bin/env python3
"""
Fixed Market Data Adapter for Multi-Agent Backtesting
"""
import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fixed_adapter")

def test_connection(db_url=None):
    """Test database connection"""
    db_url = db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        return False
        
    conn = None
    try:
        logger.info(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"Connected to PostgreSQL: {version[0]}")
        
        # Check if market_data table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'market_data'
            );
        """)
        
        if cursor.fetchone()[0]:
            logger.info("market_data table exists")
            
            # Check columns
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'market_data';
            """)
            
            columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"market_data columns: {', '.join(columns)}")
            
            # Check for data
            cursor.execute("SELECT COUNT(*) FROM market_data")
            count = cursor.fetchone()[0]
            logger.info(f"market_data contains {count} rows")
            
            # Check for intervals
            cursor.execute("SELECT DISTINCT interval FROM market_data")
            intervals = [row[0] for row in cursor.fetchall()]
            logger.info(f"Available intervals: {', '.join(intervals)}")
            
            # Sample data
            cursor.execute("""
                SELECT symbol, interval, timestamp, open, high, low, close, volume
                FROM market_data
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            sample = cursor.fetchone()
            if sample:
                logger.info(f"Sample data: {sample}")
                
            # Get data date ranges
            cursor.execute("""
                SELECT 
                    symbol,
                    interval,
                    MIN(timestamp) as start_date,
                    MAX(timestamp) as end_date,
                    COUNT(*) as row_count
                FROM
                    market_data
                GROUP BY
                    symbol, interval
                ORDER BY
                    symbol, interval
            """)
            
            rows = cursor.fetchall()
            
            print("\nAvailable data for backtesting:")
            for row in rows:
                symbol, interval, start_date, end_date, count = row
                print(f"  {symbol} {interval}: {start_date} to {end_date} ({count} records)")
                
            return True
        else:
            logger.error("market_data table does not exist")
            return False
            
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if conn:
            conn.close()

def fix_database_tables(db_url=None):
    """Create helper views for database tables"""
    db_url = db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        return False
        
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create a function to get market data
        logger.info("Creating function to access market data")
        cursor.execute("""
        DROP FUNCTION IF EXISTS get_market_data_by_interval;
        
        CREATE OR REPLACE FUNCTION get_market_data_by_interval(
            p_symbol TEXT,
            p_interval TEXT,
            p_start_date TIMESTAMP,
            p_end_date TIMESTAMP
        )
        RETURNS TABLE (
            time_stamp TIMESTAMP,
            open_price NUMERIC,
            high_price NUMERIC,
            low_price NUMERIC,
            close_price NUMERIC,
            volume_val NUMERIC
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                md.timestamp as time_stamp,
                md.open as open_price,
                md.high as high_price,
                md.low as low_price,
                md.close as close_price,
                md.volume as volume_val
            FROM
                market_data md
            WHERE
                md.symbol = p_symbol
                AND md.interval = p_interval
                AND md.timestamp >= p_start_date
                AND md.timestamp <= p_end_date
            ORDER BY
                md.timestamp;
        END;
        $$;
        """)
        
        # Create a function to get latest market data
        logger.info("Creating function to get latest market data")
        cursor.execute("""
        DROP FUNCTION IF EXISTS get_latest_market_data;
        
        CREATE OR REPLACE FUNCTION get_latest_market_data(
            p_symbol TEXT,
            p_interval TEXT DEFAULT '1h'
        )
        RETURNS TABLE (
            symbol TEXT,
            interval TEXT,
            time_stamp TIMESTAMP,
            open_price NUMERIC,
            high_price NUMERIC,
            low_price NUMERIC,
            close_price NUMERIC,
            volume_val NUMERIC
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                md.symbol,
                md.interval,
                md.timestamp as time_stamp,
                md.open as open_price,
                md.high as high_price,
                md.low as low_price,
                md.close as close_price,
                md.volume as volume_val
            FROM
                market_data md
            WHERE
                md.symbol = p_symbol
                AND md.interval = p_interval
            ORDER BY
                md.timestamp DESC
            LIMIT 1;
        END;
        $$;
        """)
        
        logger.info("Database functions created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database functions: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main entry point"""
    # Test connection
    if not test_connection():
        return 1
        
    # Fix database tables
    if not fix_database_tables():
        return 1
        
    print("\n✅ Market data adapter setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
