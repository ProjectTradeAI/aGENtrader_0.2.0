"""
Debug System Data Integration

This script ensures our changes to the LiquidityAnalystAgent work correctly by
checking the actual data passed to it by the main system.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from binance_data_provider import BinanceDataProvider
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.base_agent import BaseAnalystAgent

class DataCapture:
    """Capture and dump data for debugging."""
    
    @staticmethod
    def dump_obj(obj, label="Object", max_depth=2, current_depth=0):
        """Recursive helper to dump object contents."""
        prefix = "  " * current_depth
        if current_depth >= max_depth:
            return f"{prefix}[Max depth reached]"
        
        if isinstance(obj, dict):
            result = f"{prefix}{label} (dict with {len(obj)} keys):\n"
            for k, v in obj.items():
                result += f"{prefix}  {k}: "
                if isinstance(v, (dict, list)) and current_depth < max_depth:
                    result += "\n" + DataCapture.dump_obj(v, label=k, 
                                                         max_depth=max_depth,
                                                         current_depth=current_depth+1)
                else:
                    # For large objects, just show type and size
                    if isinstance(v, (list, dict)) and len(v) > 10:
                        result += f"[{type(v).__name__} with {len(v)} items]\n"
                    else:
                        result += f"{v}\n"
            return result
        
        elif isinstance(obj, list):
            result = f"{prefix}{label} (list with {len(obj)} items):\n"
            if len(obj) > 0:
                # Only show first few items for lists
                for i, item in enumerate(obj[:min(5, len(obj))]):
                    result += f"{prefix}  [{i}]: "
                    if isinstance(item, (dict, list)) and current_depth < max_depth:
                        result += "\n" + DataCapture.dump_obj(item, label=f"item {i}", 
                                                             max_depth=max_depth,
                                                             current_depth=current_depth+1)
                    else:
                        result += f"{item}\n"
                if len(obj) > 5:
                    result += f"{prefix}  ... and {len(obj) - 5} more items\n"
            return result
        
        else:
            return f"{prefix}{label}: {obj}\n"

def check_market_data(market_data: Dict[str, Any], 
                      label: str = "Market Data"):
    """Check market data content."""
    if not market_data:
        logger.error(f"{label} is empty!")
        return
    
    # Look for specific keys
    logger.info(f"{label} contains keys: {list(market_data.keys())}")
    
    # Check if order book data is included
    if 'order_book' in market_data:
        order_book = market_data['order_book']
        logger.info(f"Order book data found with keys: {list(order_book.keys())}")
        
        # Extract and validate bid/ask data
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        logger.info(f"Order book contains {len(bids)} bids and {len(asks)} asks")
        
        # Calculate bid/ask ratio and check thresholds
        if bids and asks:
            bid_depth = sum(float(b[0]) * float(b[1]) for b in bids)
            ask_depth = sum(float(a[0]) * float(a[1]) for a in asks)
            bid_ask_ratio = bid_depth / ask_depth if ask_depth > 0 else 1.0
            
            logger.info(f"Calculated bid_depth: {bid_depth}")
            logger.info(f"Calculated ask_depth: {ask_depth}")
            logger.info(f"Calculated bid/ask ratio: {bid_ask_ratio:.4f}")
            
            logger.info(f"Extreme ratio check (< 0.75): {bid_ask_ratio < 0.75}")
            logger.info(f"Extreme ratio check (> 1.25): {bid_ask_ratio > 1.25}")
    else:
        logger.warning(f"No order book data found in {label}!")

def main():
    """Fetch and test order book and liquidity analysis."""
    logger.info("=== System Data Debug Script ===")
    
    # Create data provider with API credentials
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    
    if not api_key or not api_secret:
        logger.warning("No API credentials found, some functionality may be limited")
    
    provider = BinanceDataProvider(api_key=api_key, api_secret=api_secret)
    
    # Fetch fresh order book
    symbol = "BTCUSDT"
    logger.info(f"Fetching order book for {symbol}...")
    
    try:
        order_book = provider.fetch_market_depth(symbol, limit=100)
        logger.info(f"Order book contains {len(order_book.get('bids', []))} bids and {len(order_book.get('asks', []))} asks")
        
        # Debug order book structure 
        check_market_data({"order_book": order_book}, "Direct order book")
        
        # Test with LiquidityAnalystAgent
        logger.info("Creating and testing LiquidityAnalystAgent...")
        agent = LiquidityAnalystAgent(data_fetcher=provider)
        
        # Get a result directly
        direct_result = agent.analyze(
            symbol=symbol,
            market_data={"order_book": order_book, "symbol": symbol})
        
        logger.info(f"Direct result: {direct_result}")
        logger.info(f"Signal: {direct_result.get('signal')}, Confidence: {direct_result.get('confidence')}")
        logger.info(f"Explanation: {direct_result.get('explanation')}")
        
        # Try to figure out what's happening in main system
        logger.info("\n=== CHECKING HOW AGENT IS CALLED IN MAIN SYSTEM ===")
        
        # Save the original analyze method
        original_analyze = agent.analyze
        
        # Replace with debug version that logs input
        def debug_analyze(symbol=None, market_data=None, **kwargs):
            logger.info("INTERCEPTED ANALYZE CALL:")
            logger.info(f"symbol = {symbol}")
            logger.info(f"market_data keys = {list(market_data.keys()) if market_data else 'None'}")
            
            # Check if market_data contains order_book
            if market_data and 'order_book' in market_data:
                check_market_data(market_data, "Passed market_data")
            else:
                logger.warning("No order_book in market_data!")
                
                # Check if data fetcher is being used
                if hasattr(agent, 'data_fetcher') and agent.data_fetcher:
                    logger.info("Agent will attempt to use data_fetcher")
            
            # Call original method and return result
            result = original_analyze(symbol=symbol, market_data=market_data, **kwargs)
            logger.info(f"ORIGINAL METHOD RETURNED: signal={result.get('signal')}, confidence={result.get('confidence')}")
            return result
        
        # Replace the method
        agent.analyze = debug_analyze
        
        # Now try without providing the order book, which is how the main system calls it
        logger.info("\n=== TESTING WITH ONLY SYMBOL (DATA FETCHER MODE) ===")
        fetch_result = agent.analyze(symbol=symbol)
        
        logger.info(f"Fetch result: {fetch_result}")
        logger.info(f"Signal: {fetch_result.get('signal')}, Confidence: {fetch_result.get('confidence')}")
        logger.info(f"Explanation: {fetch_result.get('explanation')}")
        
    except Exception as e:
        logger.error(f"Error in script: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()