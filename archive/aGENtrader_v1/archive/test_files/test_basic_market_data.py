"""
Basic Market Data Test

This is a simplified script to test the core market data functions
"""

import os
import sys
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Timer decorator for performance measurement
def time_function(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"Starting {func.__name__}...")
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Completed {func.__name__} in {elapsed:.2f} seconds")
        return result
    return wrapper

@time_function
def test_get_market_price():
    """Test the get_market_price function"""
    print("\n=== TESTING get_market_price ===")
    try:
        from agents.query_market_data import get_market_price
        
        # Get Bitcoin price
        print("Getting Bitcoin price...")
        btc_price = get_market_price("BTCUSDT")
        print(f"BTC Price: {btc_price}")
        
        return True
    except Exception as e:
        logger.error(f"Error in get_market_price test: {str(e)}")
        return False

@time_function
def test_query_market_data():
    """Test the query_market_data function"""
    print("\n=== TESTING query_market_data ===")
    try:
        from agents.query_market_data import query_market_data
        
        # Get recent Bitcoin data (last 5 hours)
        print("Getting recent Bitcoin data (last 3 hours)...")
        btc_data = query_market_data("BTCUSDT", interval="1h", limit=3, format_type="text")
        print(f"BTC Data:\n{btc_data}")
        
        return True
    except Exception as e:
        logger.error(f"Error in query_market_data test: {str(e)}")
        return False

@time_function
def test_register_functions():
    """Test the function registration module"""
    print("\n=== TESTING function registration ===")
    try:
        from agents.register_market_data_functions import create_function_mapping
        
        # Get function mapping
        print("Creating function mapping...")
        function_map = create_function_mapping()
        print(f"Function map created with {len(function_map)} functions")
        
        # Print function names
        function_names = [func["name"] for func in function_map]
        print(f"Registered functions: {', '.join(function_names)}")
        
        return True
    except Exception as e:
        logger.error(f"Error in function registration test: {str(e)}")
        return False

def main():
    """Main function"""
    print("BASIC MARKET DATA TEST")
    print("=====================")
    print("Testing core market data functionality")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print()
    
    # Run tests
    tests = [
        test_get_market_price,
        test_query_market_data,
        test_register_functions
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    # Print summary
    print("\nTEST SUMMARY")
    print("===========")
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASSED" if result else "FAILED"
        print(f"{i+1}. {test.__name__}: {status}")
    
    overall = all(results)
    print(f"\nOverall Status: {'PASSED' if overall else 'FAILED'}")

if __name__ == "__main__":
    main()