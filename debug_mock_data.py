"""
Debug LiquidityAnalystAgent with Mock Data

This script tests if the LiquidityAnalystAgent correctly processes mock order book data
when Binance API is unavailable due to geographic restrictions.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any

# Configure detailed logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from binance_data_provider import BinanceDataProvider

def test_mock_data_directly():
    """Test the mock data generation and analysis directly"""
    logger.info("=== Testing Mock Data Generation ===")
    
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Generate mock data with specific ratios
    mock_balanced = agent._generate_mock_order_book("BTCUSDT", unbalanced_ratio=1.0)
    mock_bearish = agent._generate_mock_order_book("BTCUSDT", unbalanced_ratio=0.65) 
    mock_bullish = agent._generate_mock_order_book("BTCUSDT", unbalanced_ratio=1.5)
    
    # Check mock data stats
    logger.info(f"Mock Balanced: {len(mock_balanced['bids'])} bids, {len(mock_balanced['asks'])} asks")
    
    # Calculate and log bid/ask ratios
    bid_total_balanced = mock_balanced.get('bid_total', 0)
    ask_total_balanced = mock_balanced.get('ask_total', 0)
    bid_ask_ratio_balanced = bid_total_balanced / ask_total_balanced if ask_total_balanced else 0
    
    bid_total_bearish = mock_bearish.get('bid_total', 0)
    ask_total_bearish = mock_bearish.get('ask_total', 0)
    bid_ask_ratio_bearish = bid_total_bearish / ask_total_bearish if ask_total_bearish else 0
    
    bid_total_bullish = mock_bullish.get('bid_total', 0)
    ask_total_bullish = mock_bullish.get('ask_total', 0)
    bid_ask_ratio_bullish = bid_total_bullish / ask_total_bullish if ask_total_bullish else 0
    
    logger.info(f"Balanced Bid/Ask Ratio: {bid_ask_ratio_balanced:.4f}")
    logger.info(f"Bearish Bid/Ask Ratio: {bid_ask_ratio_bearish:.4f}")
    logger.info(f"Bullish Bid/Ask Ratio: {bid_ask_ratio_bullish:.4f}")
    
    # Analyze each mock dataset
    market_data_balanced = {"order_book": mock_balanced, "symbol": "BTCUSDT"}
    market_data_bearish = {"order_book": mock_bearish, "symbol": "BTCUSDT"}
    market_data_bullish = {"order_book": mock_bullish, "symbol": "BTCUSDT"}
    
    logger.info("\n=== Analyzing Mock Balanced Data ===")
    result_balanced = agent.analyze(market_data=market_data_balanced)
    
    logger.info("\n=== Analyzing Mock Bearish Data ===")
    result_bearish = agent.analyze(market_data=market_data_bearish)
    
    logger.info("\n=== Analyzing Mock Bullish Data ===")
    result_bullish = agent.analyze(market_data=market_data_bullish)
    
    # Log results
    logger.info("\n=== ANALYSIS RESULTS ===")
    logger.info(f"Balanced: Signal={result_balanced.get('signal')}, Confidence={result_balanced.get('confidence')}")
    logger.info(f"Bearish: Signal={result_bearish.get('signal')}, Confidence={result_bearish.get('confidence')}")
    logger.info(f"Bullish: Signal={result_bullish.get('signal')}, Confidence={result_bullish.get('confidence')}")
    
    # Check if extreme ratio triggers are working
    logger.info("\n=== RATIO CHECKS ===")
    logger.info(f"Bearish ratio {bid_ask_ratio_bearish:.4f} < 0.75: {bid_ask_ratio_bearish < 0.75}")
    logger.info(f"Bullish ratio {bid_ask_ratio_bullish:.4f} > 1.25: {bid_ask_ratio_bullish > 1.25}")

def test_fetch_market_data():
    """Test the _fetch_market_data method with API errors"""
    logger.info("=== Testing _fetch_market_data with API restrictions ===")
    
    # Create agent with data fetcher
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '') 
    provider = BinanceDataProvider(api_key=api_key, api_secret=api_secret)
    agent = LiquidityAnalystAgent(data_fetcher=provider)
    
    # Test fetching with direct method call
    logger.info("Directly calling _fetch_market_data:")
    market_data = agent._fetch_market_data("BTCUSDT")
    
    # Check the structure of the returned data
    logger.info(f"Market data keys: {list(market_data.keys())}")
    if 'order_book' in market_data:
        order_book = market_data['order_book']
        logger.info(f"Order book contains {len(order_book.get('bids', []))} bids and {len(order_book.get('asks', []))} asks")
        
        # Calculate bid/ask ratio
        bid_total = order_book.get('bid_total', 0)
        ask_total = order_book.get('ask_total', 0)
        bid_ask_ratio = bid_total / ask_total if ask_total else 0
        logger.info(f"Bid/Ask Ratio: {bid_ask_ratio:.4f}")
        
        # Check if this should trigger a directional signal
        logger.info(f"Should trigger SELL: {bid_ask_ratio < 0.75}")
        logger.info(f"Should trigger BUY: {bid_ask_ratio > 1.25}")
    
    # Now analyze using the whole pipeline
    logger.info("\nTesting full analyze pipeline with fetched data:")
    result = agent.analyze(symbol="BTCUSDT")
    logger.info(f"Result: Signal={result.get('signal')}, Confidence={result.get('confidence')}")
    logger.info(f"Explanation: {result.get('explanation')}")

def main():
    """Run mock data debug tests"""
    logger.info("==== STARTING MOCK DATA DEBUG TESTS ====")
    
    # Test mock data generation and direct analysis
    test_mock_data_directly()
    
    # Test market data fetching with fallback
    test_fetch_market_data()
    
    logger.info("==== MOCK DATA DEBUG TESTS COMPLETE ====")

if __name__ == "__main__":
    main()