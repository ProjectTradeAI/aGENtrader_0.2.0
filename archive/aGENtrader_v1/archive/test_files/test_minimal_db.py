#!/usr/bin/env python3
"""
Minimal test script for database access with limited timeout
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_test")

try:
    from agents.database_retrieval_tool import get_db_tool
except ImportError:
    logger.error("Error importing the database tool. Make sure the agents module is in your path.")
    sys.exit(1)

def serialize_results(results: Dict[str, Any]) -> str:
    """Serialize results to a JSON string"""
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            return super().default(o)
    
    return json.dumps(results, indent=2, cls=CustomJSONEncoder)

async def test_with_timeout(timeout_seconds=30):
    """Run a simple database test with timeout"""
    try:
        # Get database tool
        db_tool = get_db_tool()
        print("Database tool initialized successfully")
        
        # Get available symbols
        symbols = db_tool.get_available_symbols()
        print(f"Available symbols: {symbols}")
        
        if not symbols:
            print("No symbols available in the database")
            return
        
        test_symbol = symbols[0]
        print(f"Testing with symbol: {test_symbol}")
        
        # Get the latest price
        latest_price = db_tool.get_latest_price(test_symbol)
        print(f"Latest price for {test_symbol}: {latest_price}")
        
        # Get recent market data (limited to 5 records for speed)
        recent_data = db_tool.get_recent_market_data(test_symbol, limit=5)
        print(f"Recent market data (5 records): {serialize_results(recent_data)}")
        
        # Calculate moving average
        ma = db_tool.calculate_moving_average(test_symbol, period=10, ma_type="SMA")
        print(f"10-period SMA for {test_symbol}: {ma}")
        
        # Find support and resistance levels
        levels = db_tool.find_support_resistance(test_symbol)
        print(f"Support and resistance levels for {test_symbol}: {levels}")
        
        print("All database tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during database test: {str(e)}")
        print(f"Error during database test: {str(e)}")

def main():
    """Main entry point"""
    print("\n=== Running Minimal Database Test ===\n")
    
    # Create necessary directories
    os.makedirs("data/test_results", exist_ok=True)
    
    try:
        # Run test with timeout
        asyncio.run(asyncio.wait_for(test_with_timeout(), timeout=30))
    except asyncio.TimeoutError:
        print("Test timed out after 30 seconds")
    
    print("\n=== Database Test Complete ===")

if __name__ == "__main__":
    main()