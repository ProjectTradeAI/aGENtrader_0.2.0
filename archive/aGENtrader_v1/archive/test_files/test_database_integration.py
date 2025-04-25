"""
Test Database Integration

This script tests the database integration for the AutoGen framework,
allowing database querying by agents.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_db_integration")

# Import database query agent
try:
    from agents.database_query_agent import DatabaseQueryAgent
except ImportError as e:
    logger.error(f"Error importing DatabaseQueryAgent: {e}")
    sys.exit(1)

def test_available_symbols():
    """Test retrieving available symbols"""
    logger.info("Testing available symbols query...")
    
    agent = DatabaseQueryAgent()
    query = "List all available trading symbols"
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def test_symbol_intervals():
    """Test retrieving available intervals for a symbol"""
    logger.info("Testing symbol intervals query...")
    
    agent = DatabaseQueryAgent()
    query = """
    QUERY_TYPE: available_intervals
    PARAMS:
    symbol: BTCUSDT
    """
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def test_price_query():
    """Test retrieving current price data"""
    logger.info("Testing price query...")
    
    agent = DatabaseQueryAgent()
    query = "What is the current price of BTCUSDT?"
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def test_market_data():
    """Test retrieving historical market data"""
    logger.info("Testing market data query...")
    
    agent = DatabaseQueryAgent()
    query = """
    QUERY_TYPE: market_data
    PARAMS:
    symbol: BTCUSDT
    interval: 1h
    limit: 10
    """
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def test_market_summary():
    """Test retrieving market summary"""
    logger.info("Testing market summary query...")
    
    agent = DatabaseQueryAgent()
    query = """
    QUERY_TYPE: market_summary
    PARAMS:
    symbol: BTCUSDT
    interval: 4h
    days: 7
    """
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def test_technical_analysis():
    """Test retrieving technical analysis"""
    logger.info("Testing technical analysis query...")
    
    agent = DatabaseQueryAgent()
    query = """
    QUERY_TYPE: technical_analysis
    PARAMS:
    symbol: BTCUSDT
    interval: 4h
    days: 30
    """
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def test_natural_language_query():
    """Test a natural language query"""
    logger.info("Testing natural language query...")
    
    agent = DatabaseQueryAgent()
    # Test with 4-hour timeframe and 2-week period
    query = "Can you analyze the volatility of Bitcoin over the past 2 weeks using the 4-hour timeframe?"
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()
    
def test_market_summary_nlp():
    """Test market summary natural language query"""
    logger.info("Testing market summary natural language query...")
    
    agent = DatabaseQueryAgent()
    # Test with 4-hour timeframe specified in natural language
    query = "Give me a market summary for Bitcoin using 4-hour candles over the past week"
    
    response = agent.process_message(query)
    print("\nRESPONSE:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    agent.close()

def run_test(test_name):
    """Run a specific test by name"""
    tests = {
        "symbols": test_available_symbols,
        "intervals": test_symbol_intervals,
        "price": test_price_query,
        "market_data": test_market_data,
        "summary": test_market_summary,
        "analysis": test_technical_analysis,
        "nlp": test_natural_language_query,
        "market_summary_nlp": test_market_summary_nlp
    }
    
    if test_name in tests:
        tests[test_name]()
    elif test_name == "all":
        for name, test_func in tests.items():
            logger.info(f"Running test: {name}")
            test_func()
            print("\n")
    else:
        logger.error(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(tests.keys())} or 'all'")

def main():
    """Main function to run the tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test database integration for AutoGen")
    parser.add_argument("test", nargs="?", default="all", help="Test to run (default: all)")
    
    args = parser.parse_args()
    
    # Check if DATABASE_URL is set
    if not os.environ.get("DATABASE_URL"):
        logger.error("DATABASE_URL environment variable not set")
        print("Please set the DATABASE_URL environment variable before running this script.")
        sys.exit(1)
    
    # Run the specified test
    run_test(args.test)

if __name__ == "__main__":
    main()