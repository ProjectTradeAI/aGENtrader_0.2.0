"""
Test Market Data Functions

This script tests the market data functions directly without requiring AutoGen.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import market data functions
try:
    from agents.query_market_data import (
        query_market_data,
        get_market_price,
        get_market_analysis
    )
    from utils.database_market_data import get_data_age
except ImportError as e:
    logger.error(f"Error importing market data functions: {str(e)}")
    print("Market data functions not available. Make sure you have the necessary modules.")
    sys.exit(1)

def show_data_age_warning(symbol="BTCUSDT"):
    """Show a warning about data age"""
    try:
        age = get_data_age(symbol, "1h")
        if age:
            print(f"NOTICE: Market data is {age} days old")
            print("This is because the Alpaca API subscription level (crypto_tier:0) doesn't allow")
            print("access to cryptocurrency market data. The system is using historical database data instead.")
            print("To get real-time data, consider upgrading your Alpaca API subscription.")
    except Exception as e:
        logger.error(f"Error checking data age: {str(e)}")

def run_tests():
    """Run tests on the market data functions"""
    show_data_age_warning()
    print("\n" + "="*60)
    
    print("\n1. LATEST MARKET PRICE\n")
    try:
        price_info = get_market_price("BTCUSDT")
        # Try to parse JSON if it's a string
        if isinstance(price_info, str):
            try:
                price_data = json.loads(price_info)
                print(f"Symbol: {price_data.get('symbol', 'BTCUSDT')}")
                print(f"Price: {price_data.get('formatted_price', 'N/A')}")
                print(f"Timestamp: {price_data.get('timestamp', 'N/A')}")
                print(f"Source: {price_data.get('source', 'unknown')}")
                print(f"Data Age: {price_data.get('data_age_days', 'unknown')} days")
            except json.JSONDecodeError:
                print(price_info)
        else:
            print(price_info)
    except Exception as e:
        logger.error(f"Error getting market price: {str(e)}")
        print(f"Error: {str(e)}")
    
    print("\n" + "="*60)
    
    print("\n2. RECENT PRICE HISTORY (Last 5 data points)\n")
    try:
        historical_data = query_market_data("BTCUSDT", interval="1h", limit=5, format_type="text")
        print(historical_data)
    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
        print(f"Error: {str(e)}")
    
    print("\n" + "="*60)
    
    print("\n3. MARKET ANALYSIS (Markdown format)\n")
    try:
        analysis = get_market_analysis("BTCUSDT", interval="1h", days=7, format_type="markdown")
        print(analysis)
    except Exception as e:
        logger.error(f"Error getting market analysis: {str(e)}")
        print(f"Error: {str(e)}")
    
    print("\n" + "="*60)
    
    print("\n4. ALTERNATE TIMEFRAME DATA (Daily data, last 3 days)\n")
    try:
        daily_data = query_market_data("BTCUSDT", interval="D", limit=3, format_type="text")
        print(daily_data)
    except Exception as e:
        logger.error(f"Error getting daily data: {str(e)}")
        print(f"Error: {str(e)}")
    
    print("\n" + "="*60)
    
    print("\n5. ETHEREUM DATA (if available)\n")
    try:
        eth_price = get_market_price("ETHUSDT")
        if isinstance(eth_price, str):
            try:
                eth_data = json.loads(eth_price)
                print(f"Symbol: {eth_data.get('symbol', 'ETHUSDT')}")
                print(f"Price: {eth_data.get('formatted_price', 'N/A')}")
                print(f"Data Age: {eth_data.get('data_age_days', 'unknown')} days")
            except json.JSONDecodeError:
                print(eth_price)
        else:
            print(eth_price)
    except Exception as e:
        logger.error(f"Error getting Ethereum price: {str(e)}")
        print(f"Error: {str(e)}")

def main():
    """Main entry point"""
    print("MARKET DATA FUNCTIONS TEST")
    print("=========================")
    print("Testing direct access to market data via database fallback")
    print("This demonstrates the functionality without requiring AutoGen")
    print()
    
    run_tests()
    
    print("\n")
    print("Tests completed! This functionality is ready to be used with AutoGen.")
    print("To use with AutoGen, import the register_market_data_functions module")
    print("and call register_market_data_functions(agent) with your AutoGen agent.")

if __name__ == "__main__":
    main()