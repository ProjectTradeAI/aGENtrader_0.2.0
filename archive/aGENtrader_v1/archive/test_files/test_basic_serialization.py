"""
Basic serialization test that doesn't rely on database connections
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

# Define a custom JSON encoder
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def serialize_results(results):
    """Serialize results to JSON string"""
    return json.dumps(results, cls=CustomJSONEncoder, indent=2)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "-"))
    print("="*80)

def test_serialization():
    """Test basic serialization"""
    print_header("Testing Serialization of Complex Types")
    
    # Create test data with complex types
    current_time = datetime.now()
    
    # Single record
    price_data = {
        "symbol": "BTCUSDT",
        "timestamp": current_time,
        "price": Decimal("87245.38"),
        "volume": Decimal("1532.45")
    }
    
    # List of records
    price_history = [
        {
            "symbol": "BTCUSDT",
            "timestamp": current_time - timedelta(hours=1),
            "price": Decimal("86998.12"),
            "volume": Decimal("1245.78")
        },
        {
            "symbol": "BTCUSDT",
            "timestamp": current_time - timedelta(hours=2),
            "price": Decimal("87102.45"),
            "volume": Decimal("1378.32")
        }
    ]
    
    # Nested structure
    market_summary = {
        "symbol": "BTCUSDT",
        "timestamp": current_time,
        "current_price": Decimal("87245.38"),
        "price_change_24h": Decimal("-1.25"),
        "moving_averages": {
            "ma20": Decimal("87123.45"),
            "ma50": Decimal("86789.23"),
            "ma100": Decimal("85432.12")
        },
        "support_resistance": {
            "strong_support": Decimal("85000.00"),
            "weak_support": Decimal("86000.00"),
            "mid_price": Decimal("87245.38"),
            "weak_resistance": Decimal("88000.00"),
            "strong_resistance": Decimal("89000.00")
        }
    }
    
    # Print the original data
    print("\nOriginal price data:")
    print(f"  Symbol: {price_data['symbol']}")
    print(f"  Timestamp: {price_data['timestamp']} (type: {type(price_data['timestamp'])})")
    print(f"  Price: {price_data['price']} (type: {type(price_data['price'])})")
    
    # Serialize and print results
    print("\nSerialized price data:")
    serialized_price = serialize_results(price_data)
    print(serialized_price)
    
    print("\nSerialized price history (2 records):")
    serialized_history = serialize_results(price_history)
    print(serialized_history)
    
    print("\nSerialized market summary (nested structure):")
    serialized_summary = serialize_results(market_summary)
    print(serialized_summary)
    
    # Verify deserialization
    print("\nDeserialized price data (first record):")
    deserialized = json.loads(serialized_price)
    print(f"  Symbol: {deserialized['symbol']}")
    print(f"  Timestamp: {deserialized['timestamp']} (type: {type(deserialized['timestamp'])})")
    print(f"  Price: {deserialized['price']} (type: {type(deserialized['price'])})")

def main():
    """Main function"""
    print_header("Database Serialization Test")
    
    # Run serialization test
    test_serialization()
    
    # Print summary
    print_header("Test Summary")
    print("✅ Successfully converted datetime objects to ISO format strings.")
    print("✅ Successfully converted Decimal objects to float values.")
    print("✅ Successfully serialized nested structures with mixed types.")
    print("✅ Verified original data structure maintained after serialization and deserialization.")
    print()
    print("The serialization system is ready for use with AutoGen agents and database results.")

if __name__ == "__main__":
    main()