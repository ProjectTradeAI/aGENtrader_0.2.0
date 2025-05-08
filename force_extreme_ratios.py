"""
Force Extreme Ratios Test

This script directly tests the extreme ratio detection in LiquidityAnalystAgent
with deliberately manipulated market data to force specific signals.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from agents.liquidity_analyst_agent import LiquidityAnalystAgent

def create_extreme_order_book(is_bearish=True):
    """
    Create an extremely imbalanced order book directly.
    
    Args:
        is_bearish: If True, create bearish (sell) pressure with bid/ask ratio below 0.75
                   If False, create bullish (buy) pressure with bid/ask ratio above 1.25
    
    Returns:
        Dictionary containing order book data
    """
    current_price = 50000.0
    spread = current_price * 0.0001  # 0.01% spread
    
    # Generate bid and ask prices around current price
    bid_start = current_price - spread/2
    ask_start = current_price + spread/2
    
    # Create bids and asks with the requested imbalance
    bids = []
    asks = []
    
    # Generate bids (lower than current price)
    for i in range(10):
        price = bid_start - (i * 10)
        # Volume varies based on scenario
        volume = 0.1 if is_bearish else 0.5
        bids.append([price, volume])
    
    # Generate asks (higher than current price)
    for i in range(10):
        price = ask_start + (i * 10)
        # Volume varies based on scenario
        volume = 0.5 if is_bearish else 0.1
        asks.append([price, volume])
    
    # Calculate USDT totals
    bid_total = sum(float(b[0]) * float(b[1]) for b in bids)
    ask_total = sum(float(a[0]) * float(a[1]) for a in asks)
    
    # Calculate bid/ask ratio
    ratio = bid_total / ask_total if ask_total > 0 else 1.0
    
    logger.info(f"Created {'BEARISH' if is_bearish else 'BULLISH'} order book")
    logger.info(f"Bid depth: {bid_total:.2f}, Ask depth: {ask_total:.2f}")
    logger.info(f"Bid/Ask ratio: {ratio:.4f}")
    
    # Make sure the ratio meets our thresholds
    # Bearish should be < 0.75, Bullish should be > 1.25
    if is_bearish and ratio >= 0.75:
        logger.warning(f"Bearish ratio {ratio:.4f} is not below the 0.75 threshold!")
        # Adjust asks to ensure ratio is below threshold
        adjustment_factor = (ratio / 0.7) * 1.2  # Make it well below the threshold
        new_asks = [[a[0], a[1] * adjustment_factor] for a in asks]
        asks = new_asks
        ask_total = sum(float(a[0]) * float(a[1]) for a in asks)
        ratio = bid_total / ask_total
        logger.info(f"Adjusted to ensure ratio below 0.75: {ratio:.4f}")
    
    elif not is_bearish and ratio <= 1.25:
        logger.warning(f"Bullish ratio {ratio:.4f} is not above the 1.25 threshold!")
        # Adjust bids to ensure ratio is above threshold
        adjustment_factor = (1.3 / ratio) * 1.2  # Make it well above the threshold
        new_bids = [[b[0], b[1] * adjustment_factor] for b in bids]
        bids = new_bids
        bid_total = sum(float(b[0]) * float(b[1]) for b in bids)
        ratio = bid_total / ask_total
        logger.info(f"Adjusted to ensure ratio above 1.25: {ratio:.4f}")
    
    return {
        "timestamp": int(time.time() * 1000),
        "bids": bids,
        "asks": asks,
        "bid_total": bid_total,
        "ask_total": ask_total
    }

def test_direct_signal_generation():
    """Test the _generate_signal method directly with controlled metrics."""
    logger.info("=== TESTING DIRECT SIGNAL GENERATION ===")
    
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Create metrics dictionaries with extreme ratios
    bearish_metrics = {
        "bid_ask_ratio": 0.65,
        "bid_depth_usdt": 50000.0,
        "ask_depth_usdt": 80000.0,
        "agent_sane": True,
        "liquidity_zones": {
            "support_clusters": [{"price": 49800, "volume": 0.5}],
            "resistance_clusters": [{"price": 50200, "volume": 0.5}],
            "gaps": []
        }
    }
    
    bullish_metrics = {
        "bid_ask_ratio": 1.35,
        "bid_depth_usdt": 80000.0,
        "ask_depth_usdt": 60000.0,
        "agent_sane": True,
        "liquidity_zones": {
            "support_clusters": [{"price": 49800, "volume": 0.5}],
            "resistance_clusters": [{"price": 50200, "volume": 0.5}],
            "gaps": []
        }
    }
    
    # Call _generate_signal directly
    logger.info("Testing bearish metrics (bid/ask ratio 0.65)")
    bearish_signal, bearish_confidence, bearish_explanation = agent._generate_signal(bearish_metrics)
    
    logger.info("Testing bullish metrics (bid/ask ratio 1.35)")
    bullish_signal, bullish_confidence, bullish_explanation = agent._generate_signal(bullish_metrics)
    
    logger.info("\n=== RESULTS FROM DIRECT _generate_signal CALLS ===")
    logger.info(f"Bearish: Signal={bearish_signal}, Confidence={bearish_confidence}")
    logger.info(f"Bearish explanation: {bearish_explanation}")
    
    logger.info(f"Bullish: Signal={bullish_signal}, Confidence={bullish_confidence}")
    logger.info(f"Bullish explanation: {bullish_explanation}")

def test_extreme_order_books():
    """Test the agent with manually created extreme order books."""
    logger.info("=== TESTING WITH EXTREME ORDER BOOKS ===")
    
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Create extreme order books
    bearish_order_book = create_extreme_order_book(is_bearish=True)
    bullish_order_book = create_extreme_order_book(is_bearish=False)
    
    # Create market data packages
    bearish_market_data = {"order_book": bearish_order_book, "symbol": "BTCUSDT"}
    bullish_market_data = {"order_book": bullish_order_book, "symbol": "BTCUSDT"}
    
    # Analyze the market data
    logger.info("Analyzing bearish market data...")
    bearish_result = agent.analyze(market_data=bearish_market_data)
    
    logger.info("Analyzing bullish market data...")
    bullish_result = agent.analyze(market_data=bullish_market_data)
    
    # Log results
    logger.info("\n=== RESULTS FROM analyze() WITH EXTREME ORDER BOOKS ===")
    logger.info(f"Bearish: Signal={bearish_result.get('signal')}, Confidence={bearish_result.get('confidence')}")
    logger.info(f"Bearish explanation: {bearish_result.get('explanation')}")
    
    logger.info(f"Bullish: Signal={bullish_result.get('signal')}, Confidence={bullish_result.get('confidence')}")
    logger.info(f"Bullish explanation: {bullish_result.get('explanation')}")

def test_inject_debug_in_analyze_order_book():
    """Test with injected value tracing in _analyze_order_book."""
    logger.info("=== TESTING WITH EXTREME DIRECT BID/ASK RATIO MANIPULATION ===")
    
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Create a basic order book
    order_book = {
        "timestamp": int(time.time() * 1000),
        "bids": [[49995.0, 0.1], [49990.0, 0.1]],
        "asks": [[50005.0, 0.1], [50010.0, 0.1]],
    }
    
    # Save original method
    original_analyze_order_book = agent._analyze_order_book
    
    # Create a wrapper that injects extreme values
    def analyze_order_book_wrapper(order_book, market_context=None):
        result = original_analyze_order_book(order_book, market_context)
        
        # HACK: Force extreme values to see if they trigger signals
        # These values should be way beyond thresholds
        logger.info("INJECTING EXTREME VALUES TO TEST THRESHOLD DETECTION")
        result['bid_ask_ratio'] = 0.6  # Should trigger SELL
        result['bid_depth_usdt'] = 50000.0
        result['ask_depth_usdt'] = 90000.0
        
        logger.info(f"Injected forced bid/ask ratio: {result['bid_ask_ratio']:.4f}")
        return result
    
    # Replace the method
    agent._analyze_order_book = analyze_order_book_wrapper
    
    # Test with our hacked method
    market_data = {"order_book": order_book, "symbol": "BTCUSDT"}
    logger.info("Analyzing with forced extreme values...")
    result = agent.analyze(market_data=market_data)
    
    # Log result
    logger.info("\n=== RESULT WITH FORCED EXTREME VALUES ===")
    logger.info(f"Signal: {result.get('signal')}, Confidence: {result.get('confidence')}")
    logger.info(f"Explanation: {result.get('explanation')}")
    
    # Restore original method
    agent._analyze_order_book = original_analyze_order_book

def main():
    """Run tests to diagnose extreme ratio detection."""
    logger.info("====== EXTREME RATIO DETECTION TESTS ======")
    
    # Test direct signal generation with controlled metrics
    test_direct_signal_generation()
    
    # Test with extreme order books
    test_extreme_order_books()
    
    # Test with injected debug values
    test_inject_debug_in_analyze_order_book()
    
    logger.info("====== EXTREME RATIO DETECTION TESTS COMPLETE ======")

if __name__ == "__main__":
    main()