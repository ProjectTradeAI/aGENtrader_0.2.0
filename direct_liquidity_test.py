"""
Direct Liquidity Analyst Testing Script

This script directly tests the LiquidityAnalystAgent with real order book data
from a previously saved file to diagnose why it's consistently returning NEUTRAL signals.
"""

import json
import os
import sys
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.base_agent import BaseAnalystAgent

class MockMarketContext:
    """Simple mock market context for testing."""
    
    def __init__(self, symbol="BTC/USDT", price=97140.0):
        self.symbol = symbol
        self.price = price
        self.volatility_1h = 0.01  # 1% volatility
        self.market_phase = "consolidation"

def main():
    """Run the direct liquidity analyst test."""
    print("=== Direct LiquidityAnalystAgent Test ===")
    
    # Load order book data from file
    with open('debug_order_book.json', 'r') as f:
        order_book = json.load(f)
    
    # Calculate market metrics for reporting
    bid_total = sum(float(b[0]) * float(b[1]) for b in order_book['bids'])
    ask_total = sum(float(a[0]) * float(a[1]) for a in order_book['asks'])
    bid_ask_ratio = bid_total / ask_total if ask_total > 0 else 1.0
    
    print(f"Loaded order book with {len(order_book['bids'])} bids and {len(order_book['asks'])} asks")
    print(f"Calculated bid/ask ratio from raw data: {bid_ask_ratio:.4f}")
    
    # Initialize the LiquidityAnalystAgent
    agent = LiquidityAnalystAgent()
    
    # Create mock market context
    context = MockMarketContext()
    
    # Keep a reference to the original _analyze_order_book method
    original_analyze = agent._analyze_order_book
    
    # Define a wrapper to capture the output
    def debug_analyze_wrapper(order_book, market_context=None):
        print("\n=== CAPTURING _analyze_order_book CALL ===")
        result = original_analyze(order_book, market_context)
        print("\n=== RESULT FROM _analyze_order_book ===")
        print(f"bid_depth_usdt: {result.get('bid_depth_usdt', 'N/A')}")
        print(f"ask_depth_usdt: {result.get('ask_depth_usdt', 'N/A')}")
        print(f"bid_ask_ratio: {result.get('bid_ask_ratio', 'N/A')}")
        print(f"agent_sane: {result.get('agent_sane', 'N/A')}")
        print(f"sanity_message: {result.get('sanity_message', 'N/A')}")
        return result
    
    # Replace the method with our debug wrapper
    agent._analyze_order_book = debug_analyze_wrapper
    
    # Inspect the actual order book structure
    print("\n=== ORDER BOOK INSPECTION ===")
    print(f"Order book keys: {list(order_book.keys())}")
    
    # Fix order book data format if necessary
    # Some environments might use different structures
    if 'bids' not in order_book or 'asks' not in order_book:
        print("WARNING: Order book data might be in wrong format, trying to fix...")
        if 'data' in order_book and isinstance(order_book['data'], dict):
            order_book = order_book['data']
            print(f"Fixed order book keys: {list(order_book.keys())}")
    
    # Directly analyze the order book
    print("\n=== DIRECT ANALYSIS ===")
    print("Calling analyze() with order book data...")
    
    # First directly invoke the _analyze_order_book method to see what's happening
    print("\n=== DIRECT _analyze_order_book CALL ===")
    order_book_result = agent._analyze_order_book(order_book, context)
    print("Direct order book analysis complete!")
    
    # Print key bits of the direct result
    print("\n=== DIRECT ORDER BOOK ANALYSIS RESULT ===")
    print(f"Bid/Ask Ratio: {order_book_result.get('bid_ask_ratio', 'N/A')}")
    print(f"Bid Depth USDT: {order_book_result.get('bid_depth_usdt', 'N/A')}")
    print(f"Ask Depth USDT: {order_book_result.get('ask_depth_usdt', 'N/A')}")
    
    # Calculate bid/ask ratio directly from the raw data to verify
    bids = order_book.get('bids', [])
    asks = order_book.get('asks', [])
    if bids and asks:
        bid_depth_manual = sum(float(b[0]) * float(b[1]) for b in bids)
        ask_depth_manual = sum(float(a[0]) * float(a[1]) for a in asks)
        bid_ask_ratio_manual = bid_depth_manual / ask_depth_manual if ask_depth_manual > 0 else 1.0
        print(f"Manual Bid/Ask Ratio Calculation: {bid_ask_ratio_manual:.4f}")
        print(f"Manual Bid Depth: {bid_depth_manual:.2f}")
        print(f"Manual Ask Depth: {ask_depth_manual:.2f}")
        
        # Check conditions for extreme bid/ask ratio
        print(f"Extreme ratio check (bid_ask_ratio < 0.75): {bid_ask_ratio_manual < 0.75}")
        print(f"Extreme ratio check (bid_ask_ratio > 1.25): {bid_ask_ratio_manual > 1.25}")
    
    try:
        # Now try the full analyze method with symbol
        result = agent.analyze(
            symbol="BTCUSDT",  # Add explicit symbol parameter
            market_data={"order_book": order_book, "symbol": "BTCUSDT"},  # Add symbol in market_data too
            market_context=context
        )
        
        # Print full result for debugging
        print("\n=== FULL RESULT DICTIONARY ===")
        for key, value in result.items():
            print(f"{key}: {value}")
        
        # Print results
        print("\n=== ANALYSIS RESULTS ===")
        print(f"Signal: {result.get('signal', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 'N/A')}")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
        
        # Print liquidity zones if available
        if 'detail' in result and 'liquidity_zones' in result['detail']:
            zones = result['detail']['liquidity_zones']
            print(f"\nSupport zones: {len(zones.get('support_clusters', []))}")
            print(f"Resistance zones: {len(zones.get('resistance_clusters', []))}")
            
        # Print additional debug info
        print("\n=== ADDITIONAL DEBUG INFO ===")
        print(f"Suggested entry: {result.get('detail', {}).get('suggested_entry', 'N/A')}")
        print(f"Suggested stop loss: {result.get('detail', {}).get('suggested_stop_loss', 'N/A')}")
        print(f"Suggested take profit: {result.get('detail', {}).get('suggested_take_profit', 'N/A')}")
    
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()