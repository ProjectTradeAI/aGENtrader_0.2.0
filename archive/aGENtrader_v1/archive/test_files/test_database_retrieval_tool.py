"""
Test script for the Database Retrieval Tool

This script tests the functionality of the database retrieval tool for AutoGen agents.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_tool_test")

# Import database retrieval functions
from agents.database_retrieval_tool import (
    get_latest_price,
    get_recent_market_data,
    get_market_data_range,
    calculate_moving_average,
    calculate_rsi,
    get_market_summary,
    CustomJSONEncoder
)

def display_results(title, data):
    """Display formatted results"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)
    
    # If data is a string (JSON), try to parse and pretty print it
    if isinstance(data, str):
        try:
            parsed_data = json.loads(data)
            print(json.dumps(parsed_data, indent=2))
        except json.JSONDecodeError:
            print(data)
    else:
        # Otherwise just print the data
        print(data)

async def test_database_retrieval_tool():
    """Test the database retrieval tool"""
    
    print("\n\n")
    print("=" * 80)
    print(" DATABASE RETRIEVAL TOOL TEST ".center(80, "="))
    print("=" * 80)
    print("\nTesting database retrieval functions for AutoGen integration...\n")
    
    # Test get_latest_price
    symbol = "BTCUSDT"
    print(f"\nGetting latest price for {symbol}...")
    latest_price_json = get_latest_price(symbol)
    
    if latest_price_json:
        display_results("Latest Price Data", latest_price_json)
        
        # Parse the JSON and display actual price
        try:
            latest_price = json.loads(latest_price_json)
            print(f"\nLast close price: ${latest_price['close']} at {latest_price['timestamp']}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing latest price: {str(e)}")
    else:
        print("❌ Failed to retrieve latest price data")
    
    # Test get_recent_market_data
    limit = 3
    print(f"\nGetting recent market data for {symbol} (limit {limit})...")
    recent_data_json = get_recent_market_data(symbol, limit)
    
    if recent_data_json:
        display_results("Recent Market Data", recent_data_json)
        
        # Parse the JSON and display price changes
        try:
            recent_data = json.loads(recent_data_json)
            if len(recent_data["data"]) >= 2:
                latest = recent_data["data"][0]
                previous = recent_data["data"][1]
                
                price_change = latest["close"] - previous["close"]
                percent_change = (price_change / previous["close"]) * 100
                
                print(f"\nPrice change analysis:")
                print(f"Latest close ({latest['timestamp']}): ${latest['close']}")
                print(f"Previous close ({previous['timestamp']}): ${previous['close']}")
                print(f"Change: ${price_change:.2f} ({percent_change:.2f}%)")
                print(f"Direction: {'UP' if price_change > 0 else 'DOWN' if price_change < 0 else 'UNCHANGED'}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error analyzing recent data: {str(e)}")
    else:
        print("❌ Failed to retrieve recent market data")
    
    # Test get_market_data_range with a 1-day range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    start_str = start_time.isoformat()
    end_str = end_time.isoformat()
    
    print(f"\nGetting market data for {symbol} from {start_str} to {end_str}...")
    range_data_json = get_market_data_range(symbol, start_str, end_str)
    
    if range_data_json:
        range_data = json.loads(range_data_json)
        print(f"Retrieved {range_data.get('count', 0)} data points in the time range")
        
        # Don't display full data as it might be large
        if range_data.get("count", 0) > 0:
            display_results("First Data Point in Range", 
                           json.dumps(range_data["data"][0], cls=CustomJSONEncoder))
    else:
        print("❌ Failed to retrieve market data range")
    
    # Test calculate_moving_average
    window = 10
    print(f"\nCalculating {window}-period SMA for {symbol}...")
    sma_json = calculate_moving_average(symbol, window)
    
    if sma_json:
        display_results("Simple Moving Average", sma_json)
    else:
        print("❌ Failed to calculate moving average")
    
    # Test calculate_rsi
    period = 14
    print(f"\nCalculating {period}-period RSI for {symbol}...")
    rsi_json = calculate_rsi(symbol, period)
    
    if rsi_json:
        display_results("Relative Strength Index", rsi_json)
    else:
        print("❌ Failed to calculate RSI")
    
    # Test get_market_summary
    print(f"\nGetting market summary for {symbol}...")
    summary_json = get_market_summary(symbol)
    
    if summary_json:
        display_results("Market Summary", summary_json)
    else:
        print("❌ Failed to get market summary")
    
    print("\n\n")
    print("=" * 80)
    print(" TEST COMPLETED ".center(80, "="))
    print("=" * 80)

def main():
    """Main entry point"""
    import asyncio
    asyncio.run(test_database_retrieval_tool())

if __name__ == "__main__":
    main()