"""
Test the mock data implementation in LiquidityAnalystAgent.

This script directly tests the _create_extreme_mock_data method to ensure
it properly generates mock data that triggers a SELL signal.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from agents.liquidity_analyst_agent import LiquidityAnalystAgent

def test_extreme_mock_data():
    """Test the extreme mock data implementation."""
    logger.info("==== TESTING EXTREME MOCK DATA IMPLEMENTATION ====")
    
    # Create a Mock Data Fetcher
    class MockDataFetcher:
        def fetch_market_depth(self, symbol, limit=100):
            """Mock implementation that returns empty data to force fallback"""
            return {
                "timestamp": int(time.time() * 1000),
                "bids": [],
                "asks": [],
                "bid_total": 0,
                "ask_total": 0
            }
        
        def get_ticker(self, symbol):
            """Mock implementation that returns a fake ticker"""
            return {"lastPrice": 50000.0}
    
    # Create a LiquidityAnalystAgent with our mock fetcher
    agent = LiquidityAnalystAgent(data_fetcher=MockDataFetcher())
    
    # Set force_mock_data flag to True to ensure mock data is used
    agent.force_mock_data = True
    
    # Call the analyze method with a symbol
    symbol = "BTCUSDT"
    logger.info(f"Analyzing {symbol} with forced mock data...")
    
    # Get the result
    result = agent.analyze(symbol=symbol)
    
    # Log the result
    logger.info(f"Result: {result}")
    logger.info(f"Signal: {result.get('signal')}")
    logger.info(f"Confidence: {result.get('confidence')}")
    logger.info(f"Explanation: {result.get('explanation')}")
    
    # Log metrics
    metrics = result.get('metrics', {})
    bid_ask_ratio = metrics.get('bid_ask_ratio', 1.0)
    bid_depth = metrics.get('bid_depth_usdt', 0)
    ask_depth = metrics.get('ask_depth_usdt', 0)
    
    logger.info(f"Bid/Ask Ratio: {bid_ask_ratio:.4f}")
    logger.info(f"Bid Depth: {bid_depth:.2f}")
    logger.info(f"Ask Depth: {ask_depth:.2f}")
    
    # Check if the signal is as expected (should be SELL)
    expected_signal = "SELL"
    if result.get('signal') == expected_signal:
        logger.info(f"SUCCESS: Got expected {expected_signal} signal")
    else:
        logger.warning(f"FAILED: Expected {expected_signal} signal but got {result.get('signal')}")
    
    logger.info("==== EXTREME MOCK DATA TEST COMPLETE ====")

if __name__ == "__main__":
    test_extreme_mock_data()