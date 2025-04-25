#!/usr/bin/env python3
"""
Simple test for database retrieval without agent interactions

Test focused on the specific fixes we've made.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the database retrieval tool
from agents.database_retrieval_tool import (
    get_recent_market_data,
    get_price_history,
    calculate_volatility
)

def print_separator():
    """Print a separator line for better readability"""
    print("\n" + "-" * 80 + "\n")

def test_db_retrieval():
    """Test database retrieval functions"""
    logger.info("Testing database retrieval functions")
    
    symbol = "BTCUSDT"
    
    # Test getting market data
    logger.info(f"Testing get_recent_market_data for {symbol}")
    market_data = get_recent_market_data(symbol, limit=10)
    print("Market Data (10 records):")
    print(json.dumps(market_data, indent=2, default=str))
    print_separator()
    
    # Test getting price data
    logger.info(f"Testing get_price_history for {symbol}")
    price_data = get_price_history(symbol, days=5)
    print("Price Data (5 days):")
    print(json.dumps(price_data, indent=2, default=str))
    print_separator()
    
    # Test calculating volatility (the function we fixed)
    logger.info(f"Testing calculate_volatility for {symbol}")
    volatility = calculate_volatility(symbol, days=7)
    print("Volatility (7 days):")
    print(json.dumps(volatility, indent=2, default=str))
    print_separator()
    
    return {
        "status": "success",
        "tests_run": ["get_recent_market_data", "get_price_history", "calculate_volatility"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    results = test_db_retrieval()
    logger.info(f"Test completed with status: {results['status']}")
