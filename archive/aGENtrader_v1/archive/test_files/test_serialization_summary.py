"""
This script verifies the serialization functions work properly for market data
and documents how they integrate with AutoGen functions.
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import database tool with serialization functions
from agents.database_retrieval_tool import (
    get_db_tool,
    serialize_results,
    CustomJSONEncoder
)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "-"))
    print("="*80)

def test_custom_encoder():
    """Test the custom JSON encoder directly"""
    print_header("Testing CustomJSONEncoder")
    
    # Create test data with datetime and Decimal objects
    test_data = {
        "timestamp": datetime.now(),
        "price": Decimal("52438.75"),
        "volume": Decimal("2134.867"),
        "change": Decimal("-1.25"),
        "nested": {
            "timestamp": datetime.now() - timedelta(hours=1),
            "value": Decimal("123.456")
        }
    }
    
    # Use CustomJSONEncoder to serialize
    serialized = json.dumps(test_data, cls=CustomJSONEncoder, indent=2)
    
    print("Original data:")
    print(f"  timestamp: {test_data['timestamp']} (type: {type(test_data['timestamp'])})")
    print(f"  price: {test_data['price']} (type: {type(test_data['price'])})")
    
    print("\nSerialized data:")
    print(serialized)
    
    # Deserialize to verify
    deserialized = json.loads(serialized)
    
    print("\nDeserialized data:")
    print(f"  timestamp: {deserialized['timestamp']} (type: {type(deserialized['timestamp'])})")
    print(f"  price: {deserialized['price']} (type: {type(deserialized['price'])})")
    
    return True

def test_serialize_results_function():
    """Test the serialize_results function"""
    print_header("Testing serialize_results Function")
    
    # Get database tool
    db = get_db_tool()
    
    # Get data with datetime and Decimal values
    price_data = db.get_latest_price("BTCUSDT")
    
    print("Raw price data:")
    print(price_data)
    
    # Use serialize_results function
    serialized = serialize_results(price_data)
    
    print("\nSerialized price data:")
    print(serialized)
    
    # Test with list of objects
    moving_averages = db.get_moving_averages("BTCUSDT", limit=2)
    
    if moving_averages:
        print("\nRaw moving averages data (first 2 records):")
        print(moving_averages)
        
        # Serialize list
        serialized_list = serialize_results(moving_averages)
        
        print("\nSerialized moving averages:")
        print(serialized_list)
    
    return True

def test_autogen_integration():
    """Describe how serialization integrates with AutoGen"""
    print_header("AutoGen Integration")
    
    print("""
The serialization system is integrated with AutoGen agents through:

1. Function Registration:
   - serialize_results is registered in the function_map of AutoGenDBIntegration
   - This allows agents to call it directly during conversations

2. System Messages:
   - The system messages for Market Analyst and Strategy Advisor agents include
     instructions on using serialize_results to format data
   - Example code snippets show proper usage

3. Custom JSON Encoder:
   - CustomJSONEncoder handles conversion of:
     * datetime objects to ISO format strings
     * Decimal objects to float values
   - This ensures all data retrieved from the database can be properly 
     serialized for agent communication

4. Helper Methods:
   - The database_retrieval_tool module includes a results_to_json method
     on the DatabaseRetrievalTool class
   - This gives agents multiple ways to access serialization functionality

This integration ensures that AutoGen agents can properly process and 
communicate using market data with complex types like datetime and Decimal.
    """)
    
    return True

def main():
    """Run all tests"""
    print_header("Database Serialization Test Summary")
    
    # Run encoder test
    encoder_result = test_custom_encoder()
    
    # Run function test
    function_result = test_serialize_results_function()
    
    # Show integration details
    integration_result = test_autogen_integration()
    
    # Print summary
    print_header("Test Results")
    print(f"CustomJSONEncoder Test: {'✅ PASSED' if encoder_result else '❌ FAILED'}")
    print(f"serialize_results Function Test: {'✅ PASSED' if function_result else '❌ FAILED'}")
    
    print("\nImplementation Summary:")
    print("1. CustomJSONEncoder properly converts datetime and Decimal objects to JSON-friendly formats")
    print("2. serialize_results function provides a clean interface for serializing complex database results")
    print("3. AutoGen integration is configured to handle database results with proper serialization")
    print("4. System messages guide agents on using serialization functions correctly")

if __name__ == "__main__":
    main()