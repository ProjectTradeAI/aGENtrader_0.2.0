"""
Market Data Update Script

This script updates the market data in the database with recent data.
"""
import os
import sys
import time
import json
import logging
import argparse
import psycopg2
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("market_data_updater")

# Default settings
DEFAULT_SYMBOLS = ["BTCUSDT"]
DEFAULT_INTERVALS = ["1m", "15m", "30m", "1h", "4h", "1d"]

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Update market data in the database")
    
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS,
                        help="Trading symbols to update (default: BTCUSDT)")
    parser.add_argument("--intervals", nargs="+", default=DEFAULT_INTERVALS,
                        help="Timeframe intervals to update (default: 1m 15m 30m 1h 4h 1d)")
    parser.add_argument("--days", type=int, default=5,
                        help="Number of days of history to fetch (default: 5)")
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="Batch size for Binance API requests (default: 1000)")
    
    return parser.parse_args()

def get_database_connection():
    """Get a connection to the PostgreSQL database"""
    connection_string = os.environ.get("DATABASE_URL")
    
    if not connection_string:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        connection = psycopg2.connect(connection_string)
        connection.autocommit = False
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        sys.exit(1)

def get_latest_timestamp(conn, symbol: str, interval: str) -> Optional[datetime]:
    """Get the latest timestamp for a symbol and interval in the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(timestamp) FROM market_data 
            WHERE symbol = %s AND interval = %s
        """, (symbol, interval))
        
        result = cursor.fetchone()[0]
        cursor.close()
        
        return result
    except Exception as e:
        logger.error(f"Error fetching latest timestamp: {str(e)}")
        return None

def fetch_market_data(symbol: str, interval: str, start_time: int, end_time: int, batch_size: int = 1000) -> List[Dict]:
    """Fetch market data from Binance API"""
    url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": batch_size
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Convert Binance kline data to our format
        klines = response.json()
        
        data = []
        for kline in klines:
            data.append({
                "timestamp": datetime.fromtimestamp(kline[0] / 1000),
                "symbol": symbol,
                "interval": interval,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": datetime.fromtimestamp(kline[6] / 1000),
                "quote_asset_volume": float(kline[7]),
                "number_of_trades": int(kline[8]),
                "taker_buy_base_volume": float(kline[9]),
                "taker_buy_quote_volume": float(kline[10])
            })
        
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching market data from Binance: {str(e)}")
        return []

def insert_market_data(conn, data: List[Dict]) -> int:
    """Insert market data into the database"""
    if not data:
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    try:
        for item in data:
            cursor.execute("""
                INSERT INTO market_data (
                    timestamp, symbol, interval, open, high, low, close, volume,
                    close_time, quote_asset_volume, number_of_trades,
                    taker_buy_base_volume, taker_buy_quote_volume
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, interval, timestamp) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    close_time = EXCLUDED.close_time,
                    quote_asset_volume = EXCLUDED.quote_asset_volume,
                    number_of_trades = EXCLUDED.number_of_trades,
                    taker_buy_base_volume = EXCLUDED.taker_buy_base_volume,
                    taker_buy_quote_volume = EXCLUDED.taker_buy_quote_volume
            """, (
                item["timestamp"], item["symbol"], item["interval"],
                item["open"], item["high"], item["low"], item["close"], item["volume"],
                item["close_time"], item["quote_asset_volume"], item["number_of_trades"],
                item["taker_buy_base_volume"], item["taker_buy_quote_volume"]
            ))
            count += 1
        
        conn.commit()
        return count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting market data: {str(e)}")
        return 0
    finally:
        cursor.close()

def update_market_data(args):
    """Main function to update market data"""
    conn = get_database_connection()
    
    for symbol in args.symbols:
        for interval in args.intervals:
            # Get the latest timestamp in the database for this symbol and interval
            latest_timestamp = get_latest_timestamp(conn, symbol, interval)
            
            if latest_timestamp:
                # Start from the latest timestamp
                start_time = int(latest_timestamp.timestamp() * 1000)
                logger.info(f"Updating {symbol} {interval} data from {latest_timestamp}")
            else:
                # If no data exists, start from specified days ago
                start_time = int((datetime.now() - timedelta(days=args.days)).timestamp() * 1000)
                logger.info(f"No existing data for {symbol} {interval}, fetching last {args.days} days")
            
            # End at current time
            end_time = int(datetime.now().timestamp() * 1000)
            
            total_inserted = 0
            
            # Fetch data in batches to avoid hitting rate limits
            current_start = start_time
            while current_start < end_time:
                current_end = min(current_start + (args.batch_size * 60 * 1000), end_time)
                
                data = fetch_market_data(symbol, interval, current_start, current_end, args.batch_size)
                
                if data:
                    inserted = insert_market_data(conn, data)
                    total_inserted += inserted
                    logger.info(f"Inserted {inserted} rows for {symbol} {interval}")
                else:
                    logger.warning(f"No data retrieved for {symbol} {interval} in current batch")
                
                # Update start time for next batch
                current_start = current_end
                
                # Respect rate limits
                time.sleep(1)
            
            logger.info(f"Total inserted for {symbol} {interval}: {total_inserted} rows")
    
    conn.close()
    logger.info("Market data update completed")

def main():
    """Main entry point"""
    args = parse_arguments()
    update_market_data(args)

if __name__ == "__main__":
    main()