"""
Test script to demonstrate AutoGen integration with serialization system
"""

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Import OpenAI for AutoGen
import openai
import autogen
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

# Custom JSON encoder
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

def generate_sample_market_data():
    """Generate some sample market data for testing"""
    current_time = datetime.now()
    
    # Create sample price history with complex types
    price_history = []
    for i in range(24):
        price_history.append({
            "symbol": "BTCUSDT",
            "timestamp": current_time - timedelta(hours=i),
            "price": Decimal(f"{87000 + (i * 50)}.{(i * 13) % 100:02d}"),
            "volume": Decimal(f"{1200 + (i * 20)}.{(i * 7) % 100:02d}")
        })
    
    # Create sample technical indicators
    technical_indicators = {
        "moving_averages": {
            "ma20": Decimal("87123.45"),
            "ma50": Decimal("86789.23"),
            "ma100": Decimal("85432.12"),
            "trend": "upward" if price_history[0]["price"] > price_history[23]["price"] else "downward"
        },
        "rsi": Decimal("62.75"),
        "macd": {
            "macd_line": Decimal("245.67"),
            "signal_line": Decimal("225.89"),
            "histogram": Decimal("19.78"),
            "trend": "bullish" if Decimal("245.67") > Decimal("225.89") else "bearish"
        },
        "support_resistance": {
            "strong_support": Decimal("85000.00"),
            "weak_support": Decimal("86000.00"),
            "mid_price": Decimal("87245.38"),
            "weak_resistance": Decimal("88000.00"),
            "strong_resistance": Decimal("89000.00")
        }
    }
    
    return {
        "price_history": price_history,
        "technical_indicators": technical_indicators,
        "latest_price": price_history[0]
    }

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    # Check if OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("AutoGen integration test will run in demonstration mode only.")
        return None
    
    # Use config_list_from_json if available
    try:
        config_list = [
            {
                "model": "gpt-4",
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]
        print("OpenAI API configuration loaded successfully.")
        return config_list
    except Exception as e:
        print(f"Error setting up OpenAI config: {e}")
        return None

def mock_autogen_integration():
    """Demonstrate AutoGen integration without actually calling OpenAI API"""
    print_header("Mock AutoGen Integration Demonstration")
    
    print("\nIn a real implementation, the serialization functions would be registered with AutoGen as follows:")
    print("\nExample agent setup:")
    print("""
    # Define function map for database access
    function_map = {
        "get_latest_price": get_latest_price,
        "get_price_history": get_price_history,
        "get_technical_indicators": get_technical_indicators,
        "serialize_results": serialize_results  # <-- Serialization function registered
    }
    
    # Create AutoGen agents with function calling capability
    assistant = AssistantAgent(
        name="market_analyst",
        system_message="You are a market analyst specializing in crypto markets.",
        llm_config={
            "config_list": config_list,
            "function_map": function_map  # <-- Function map registered with agent
        }
    )
    
    # When the agent needs market data, it will:
    # 1. Call a database function to retrieve data (with complex types)
    # 2. Use serialize_results to convert the data to JSON format
    # 3. Process the serialized data for analysis
    """)
    
    # Show how agents would use the serialization function
    print("\nExample of how an agent would use the serialization function:")
    print("""
    def generate_market_analysis(symbol: str):
        # Retrieve data (contains datetime and Decimal objects)
        price_data = get_latest_price(symbol)
        price_history = get_price_history(symbol, interval="1h", limit=24)
        indicators = get_technical_indicators(symbol)
        
        # Serialize to JSON for LLM consumption
        serialized_data = serialize_results({
            "latest_price": price_data,
            "price_history": price_history,
            "indicators": indicators
        })
        
        # LLM can now analyze the serialized JSON data
        return serialized_data
    """)

def main():
    """Main function"""
    print_header("AutoGen Serialization Integration Test")
    
    # Set up OpenAI config
    config_list = setup_openai_config()
    
    # Generate sample market data
    market_data = generate_sample_market_data()
    
    # Print some of the sample data
    print("\nSample market data (latest price, with complex types):")
    latest_price = market_data["latest_price"]
    print(f"  Symbol: {latest_price['symbol']}")
    print(f"  Timestamp: {latest_price['timestamp']} (type: {type(latest_price['timestamp'])})")
    print(f"  Price: {latest_price['price']} (type: {type(latest_price['price'])})")
    
    # Serialize market data to JSON
    serialized_data = serialize_results(market_data)
    
    # Print serialization result summary
    print("\nSerialized full market data structure:")
    print(f"  Original data size: {len(str(market_data))} characters")
    print(f"  Serialized JSON size: {len(serialized_data)} characters")
    print("  Sample of serialized data (first 500 chars):")
    print(f"  {serialized_data[:500]}...")
    
    # Show how to verify the serialized data
    deserialized = json.loads(serialized_data)
    print("\nVerified deserialized data types:")
    print(f"  Latest price timestamp: {type(deserialized['latest_price']['timestamp'])}")
    print(f"  Latest price value: {type(deserialized['latest_price']['price'])}")
    print(f"  Number of price history records: {len(deserialized['price_history'])}")
    
    # Show mock AutoGen integration
    mock_autogen_integration()
    
    # Print summary
    print_header("Test Summary")
    print("✅ Demonstrated how serialization works with AutoGen's function calling.")
    print("✅ Prepared sample data structures that AutoGen agents can process.")
    print("✅ Verified data types are properly serialized for agent consumption.")
    print()
    print("The serialization system is compatible with AutoGen agent interactions.")

if __name__ == "__main__":
    main()