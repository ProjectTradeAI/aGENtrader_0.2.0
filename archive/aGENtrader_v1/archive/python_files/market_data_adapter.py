#!/usr/bin/env python3
"""
Market Data Adapter for Multi-Agent Backtesting

This script adapts the market_data table for use with the authentic backtesting framework.
It creates views or functions to access the data in the format expected by agents.
"""
import os
import sys
import json
import time
import logging
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/db_adapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("market_data_adapter")

class MarketDataAdapter:
    """Adapter for the market_data database schema"""
    
    def __init__(self, db_url=None):
        """Initialize the adapter"""
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        logger.info(f"Initializing with database URL: {self.db_url[:10]}...{self.db_url[-10:]}")
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        """Test the database connection"""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
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
            else:
                logger.error("market_data table does not exist")
                
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            if conn:
                conn.close()
    
    def create_data_access_functions(self):
        """Create functions to access market data for backtesting"""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Create function to get market data by interval
            logger.info("Creating function get_market_data_by_interval")
            cursor.execute("""
            CREATE OR REPLACE FUNCTION get_market_data_by_interval(
                p_symbol TEXT,
                p_interval TEXT,
                p_start_date TIMESTAMP,
                p_end_date TIMESTAMP
            )
            RETURNS TABLE (
                timestamp TIMESTAMP,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume NUMERIC
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    md.timestamp,
                    md.open,
                    md.high,
                    md.low,
                    md.close,
                    md.volume
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
            
            # Create views for common intervals
            intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
            
            for interval in intervals:
                view_name = f"market_data_{interval.replace('m', 'min').replace('h', 'hour').replace('d', 'day')}"
                logger.info(f"Creating view {view_name}")
                
                try:
                    # Drop view if it exists
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    
                    # Create view
                    cursor.execute(f"""
                    CREATE VIEW {view_name} AS
                    SELECT
                        symbol,
                        timestamp,
                        open,
                        high,
                        low,
                        close,
                        volume
                    FROM
                        market_data
                    WHERE
                        interval = '{interval}'
                    """)
                    
                    logger.info(f"View {view_name} created successfully")
                except Exception as e:
                    logger.error(f"Error creating view {view_name}: {str(e)}")
            
            logger.info("Data access functions created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create data access functions: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            if conn:
                conn.close()
    
    def get_data_availability(self):
        """Get information about available data"""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
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
            
            availability = {}
            rows = cursor.fetchall()
            
            for row in rows:
                symbol = row['symbol']
                interval = row['interval']
                
                if symbol not in availability:
                    availability[symbol] = {}
                
                availability[symbol][interval] = {
                    "start_date": row['start_date'].strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date": row['end_date'].strftime("%Y-%m-%d %H:%M:%S"),
                    "count": row['row_count']
                }
            
            return availability
        except Exception as e:
            logger.error(f"Failed to get data availability: {str(e)}")
            traceback.print_exc()
            return {}
        finally:
            if conn:
                conn.close()

def main():
    """Main entry point"""
    try:
        # Ensure database URL is set
        if not os.environ.get("DATABASE_URL"):
            logger.error("DATABASE_URL environment variable is not set")
            return False
        
        # Create adapter
        adapter = MarketDataAdapter()
        
        # Create data access functions
        success = adapter.create_data_access_functions()
        
        if success:
            # Get data availability
            availability = adapter.get_data_availability()
            
            # Print availability in a nice format
            logger.info("Data availability:")
            for symbol, intervals in availability.items():
                logger.info(f"Symbol: {symbol}")
                for interval, data in intervals.items():
                    logger.info(f"  {interval}: {data['start_date']} to {data['end_date']} ({data['count']} records)")
            
            print("\nRecommended date ranges for backtesting:")
            for symbol, intervals in availability.items():
                if symbol == "BTCUSDT":  # Focus on BTC for now
                    for interval in ["1h", "4h", "1d"]:
                        if interval in intervals:
                            print(f"  BTCUSDT {interval}: {intervals[interval]['start_date']} to {intervals[interval]['end_date']}")
            
            return True
        else:
            logger.error("Failed to set up data access functions")
            return False
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Market data adapter setup completed successfully")
    else:
        print("❌ Market data adapter setup failed")
        sys.exit(1)
