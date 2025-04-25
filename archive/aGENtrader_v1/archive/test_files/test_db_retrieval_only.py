"""
Simplified test script for database retrieval functionality without AutoGen
"""
import os
import sys
import json
from datetime import datetime, timedelta
import logging
from decimal import Decimal

# Custom JSON encoder to handle datetime and Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

# Ensure agents directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_db_retrieval():
    """Test basic database retrieval functionality"""
    from agents.database_retrieval_tool import get_db_tool
    
    try:
        # Initialize the database tool
        db_tool = get_db_tool()
        print("\n=== Database Retrieval Tool Test ===\n")
        
        # Get available symbols
        symbols = db_tool.get_available_symbols()
        print(f"Available symbols: {symbols}")
        
        if not symbols:
            print("No symbols available in the database")
            return
        
        test_symbol = symbols[0]
        print(f"\nUsing {test_symbol} for testing\n")
        
        # Test getting latest price
        print("== Testing get_latest_price ==")
        latest_price = db_tool.get_latest_price(test_symbol)
        print(f"Latest price: {json.dumps(latest_price, indent=2, cls=CustomJSONEncoder)}")
        
        # Test getting price history
        print("\n== Testing get_price_history ==")
        hours_24 = db_tool.get_price_history(test_symbol, interval="1h", days=1)
        print(f"Last 24 hours price points: {len(hours_24)}")
        if hours_24:
            print(f"First price point: {json.dumps(hours_24[0], indent=2, cls=CustomJSONEncoder)}")
            print(f"Last price point: {json.dumps(hours_24[-1], indent=2, cls=CustomJSONEncoder)}")
        
        # Test getting moving averages
        print("\n== Testing get_moving_averages ==")
        moving_avgs = db_tool.get_moving_averages(test_symbol, days=7)
        print(f"Moving averages: {json.dumps(moving_avgs, indent=2, cls=CustomJSONEncoder)}")
        
        # Test getting support and resistance levels
        print("\n== Testing get_support_resistance ==")
        support_resistance = db_tool.get_support_resistance(test_symbol)
        print(f"Support and resistance levels: {json.dumps(support_resistance, indent=2, cls=CustomJSONEncoder)}")
        
        # Test getting technical indicators
        print("\n== Testing get_technical_indicators ==")
        indicators = db_tool.get_technical_indicators(test_symbol)
        print(f"Technical indicators: {json.dumps(indicators, indent=2, cls=CustomJSONEncoder)}")
        
        # Test market summary
        print("\n== Testing get_market_summary ==")
        summary = db_tool.get_market_summary(test_symbol)
        print(f"Market summary: {json.dumps(summary, indent=2, cls=CustomJSONEncoder)}")
        
        print("\n=== Database Retrieval Test Complete ===")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        print(f"\nError during test: {str(e)}")

if __name__ == "__main__":
    test_db_retrieval()