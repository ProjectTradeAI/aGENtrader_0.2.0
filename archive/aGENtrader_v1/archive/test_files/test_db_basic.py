"""
Basic test script to demonstrate database integration with AutoGen
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("db_test")

# Import database tools
from agents.database_retrieval_tool import (
    get_recent_market_data,
    get_latest_price,
    get_market_summary,
    get_market_data_range,
    get_price_history,
    calculate_moving_average,
    calculate_rsi,
    find_support_resistance,
    detect_patterns,
    calculate_volatility,
    get_db_tool,
    CustomJSONEncoder
)

def display_header(title: str) -> None:
    """Display a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def test_db_functions():
    """Test basic database functions without AutoGen integration"""
    display_header("Testing Database Functions")
    
    # Get database tool
    db_tool = get_db_tool()
    
    # Test get_latest_price
    print("Getting latest price for BTCUSDT...")
    latest_price = get_latest_price("BTCUSDT")
    print(f"Latest price: {latest_price}")
    
    # Test get_recent_market_data
    print("\nGetting recent market data (last 3 entries)...")
    recent_data = get_recent_market_data("BTCUSDT", 3)
    
    # Handle string responses (parsing JSON if needed)
    if isinstance(recent_data, str):
        try:
            recent_data = json.loads(recent_data)
            print("Successfully parsed JSON response")
        except json.JSONDecodeError:
            print("Error: Could not parse JSON response")
            print(f"Raw response: {recent_data}")
            recent_data = {"data": []}
    
    # Format and display the data
    if recent_data and "data" in recent_data and len(recent_data["data"]) > 0:
        print(f"Retrieved {len(recent_data['data'])} entries")
        print("\nLatest data points:")
        for i, entry in enumerate(recent_data["data"]):
            print(f"{i+1}. {entry['timestamp']} - Open: {entry['open']}, Close: {entry['close']}")
    else:
        print("No data retrieved or empty response")
        
    # Calculate price change
    if recent_data and "data" in recent_data and len(recent_data["data"]) >= 2:
        latest = recent_data["data"][0]
        previous = recent_data["data"][1]
        
        price_change = latest["close"] - previous["close"]
        percent_change = (price_change / previous["close"]) * 100
        
        print(f"\nPrice change analysis:")
        print(f"Latest close ({latest['timestamp']}): ${latest['close']}")
        print(f"Previous close ({previous['timestamp']}): ${previous['close']}")
        print(f"Change: ${price_change:.2f} ({percent_change:.2f}%)")
        print(f"Direction: {'UP' if price_change > 0 else 'DOWN'}")
    
    return {
        "status": "success",
        "latest_price": latest_price,
        "recent_data": recent_data
    }

def save_results(results: Dict[str, Any]) -> str:
    """Save test results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/logs/db_basic_test_{timestamp}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, cls=CustomJSONEncoder, indent=2)
    
    print(f"\nSaved results to {output_file}")
    return output_file

def main():
    """Main function"""
    try:
        # Test database functions
        results = test_db_functions()
        
        # Save results
        save_results(results)
        
        print("\nTest completed successfully!")
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    main()