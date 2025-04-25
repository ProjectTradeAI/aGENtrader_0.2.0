"""
Test script to verify serialization of database query results with direct calls
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from agents.database_retrieval_tool import (
    get_db_tool,
    get_latest_price,
    CustomJSONEncoder,
    serialize_results
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title: str) -> None:
    """Print a section header for better readability"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "-"))
    print("="*80 + "\n")

def test_direct_serialization():
    """Test direct serialization of database query results"""
    print_section("Testing Direct Serialization")
    
    # Get the database tool
    db_tool = get_db_tool()
    
    # Test with a symbol (first available or default to BTCUSDT)
    symbols = db_tool.get_available_symbols()
    symbol = symbols[0] if symbols else "BTCUSDT"
    
    print(f"Using symbol: {symbol}")
    
    # Get latest price data
    latest_price = db_tool.get_latest_price(symbol)
    print("\nLatest price data (raw):")
    print(latest_price)
    
    # Serialize using our CustomJSONEncoder
    serialized_price = serialize_results(latest_price)
    print("\nLatest price data (serialized JSON):")
    print(serialized_price)
    
    # Deserialize to verify integrity
    deserialized_price = json.loads(serialized_price)
    print("\nDeserialized price data:")
    print(deserialized_price)
    
    # Get price history
    price_history = db_tool.get_price_history(symbol, interval="1h", days=1)
    
    if price_history:
        # Take just the first few records for display
        limited_history = price_history[:2]
        print("\nPrice history data (first 2 records, raw):")
        print(limited_history)
        
        # Serialize using our CustomJSONEncoder
        serialized_history = serialize_results(limited_history)
        print("\nPrice history data (serialized JSON):")
        print(serialized_history)
        
        # Test the instance method as well
        json_history = db_tool.results_to_json(limited_history)
        print("\nPrice history using instance method:")
        print(json_history)
    else:
        print("\nNo price history data found for the selected time period")
    
    # Get moving averages
    moving_averages = db_tool.get_moving_averages(symbol, interval="1h", days=7)
    
    if moving_averages:
        print("\nMoving averages data (first record, raw):")
        print(moving_averages[0] if moving_averages else "No data available")
        
        # Serialize using our CustomJSONEncoder
        serialized_ma = serialize_results(moving_averages[0] if moving_averages else {})
        print("\nMoving averages data (serialized JSON):")
        print(serialized_ma)
    else:
        print("\nNo moving averages data found")
    
    # Get market summary
    market_summary = db_tool.get_market_summary(symbol)
    print("\nMarket summary data (raw):")
    print(market_summary)
    
    # Serialize using our CustomJSONEncoder
    serialized_summary = serialize_results(market_summary)
    print("\nMarket summary data (serialized JSON):")
    print(serialized_summary)
    
    print("\nSerialization test complete!")
    return True

def main():
    """Main test function"""
    print_section("Database Serialization Test")
    print("Testing serialization of market data database query results")
    
    # Test direct serialization
    result = test_direct_serialization()
    
    # Print summary
    print_section("Test Summary")
    print(f"Direct serialization test: {'✅ PASSED' if result else '❌ FAILED'}")
    print("\nTest completed!")

if __name__ == "__main__":
    main()