"""
Test Database Market Data Access

This script tests the database market data provider solution.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the database module directly (without relative import)
from utils.database_market_data import DatabaseMarketData
from utils.database_market_data import get_historical_data, get_latest_price, get_market_statistics

def test_database_connection():
    """Test connection to the database"""
    try:
        db_provider = DatabaseMarketData()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def test_get_historical_data():
    """Test getting historical data from the database"""
    logger.info("Testing get_historical_data...")
    
    # Test with default parameters
    data_json = get_historical_data("BTCUSDT", interval="1h", limit=5, format_type="json")
    logger.info(f"JSON data: {data_json[:200]}..." if len(data_json) > 200 else data_json)
    
    # Test with dataframe output
    data_df = get_historical_data("BTCUSDT", interval="1h", limit=5, format_type="dataframe")
    logger.info(f"DataFrame shape: {data_df.shape}")
    logger.info(f"DataFrame columns: {data_df.columns.tolist()}")
    if not data_df.empty:
        logger.info(f"First record: {data_df.iloc[0].to_dict()}")
    
    # Test with different interval
    data_daily = get_historical_data("BTCUSDT", interval="D", limit=3, format_type="dict")
    logger.info(f"Daily data records: {len(data_daily)}")
    
    return True

def test_get_latest_price():
    """Test getting the latest price from the database"""
    logger.info("Testing get_latest_price...")
    
    # Get the latest price
    price = get_latest_price("BTCUSDT")
    logger.info(f"Latest price: {price}")
    
    return price is not None

def test_market_statistics():
    """Test getting market statistics from the database"""
    logger.info("Testing get_market_statistics...")
    
    # Test with hourly data
    stats_hourly = get_market_statistics("BTCUSDT", interval="1h", days=7, format_type="dict")
    logger.info(f"Hourly statistics keys: {stats_hourly.keys()}")
    
    # Test with daily data
    stats_daily = get_market_statistics("BTCUSDT", interval="D", days=30, format_type="json")
    logger.info(f"Daily statistics: {stats_daily[:200]}..." if len(stats_daily) > 200 else stats_daily)
    
    return True

def main():
    """Main entry point"""
    logger.info("Starting database access tests")
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Historical Data", test_get_historical_data),
        ("Latest Price", test_get_latest_price),
        ("Market Statistics", test_market_statistics)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            logger.info(f"Running test: {name}")
            result = test_func()
            results.append((name, result))
            logger.info(f"Test completed: {name} - {'Success' if result else 'Failed'}")
        except Exception as e:
            logger.error(f"Error in test {name}: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n=== Test Results ===")
    for name, result in results:
        print(f"{name}: {'✓' if result else '✗'}")
    
    # Final assessment
    successful = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {successful}/{total} tests passed")

if __name__ == "__main__":
    main()