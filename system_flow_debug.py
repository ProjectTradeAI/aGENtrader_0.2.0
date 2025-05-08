"""
Debug the system data flow for LiquidityAnalystAgent.

This script uses wrappers to check what the main system is passing to the LiquidityAnalystAgent
and where the data is being processed incorrectly.
"""

import os
import sys
import logging
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from binance_data_provider import BinanceDataProvider
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.base_agent import BaseAnalystAgent

def main():
    """Run the system flow debug."""
    logger.info("==== SYSTEM FLOW DEBUG ====")
    
    # Create data provider with API credentials
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    
    if not api_key or not api_secret:
        logger.warning("No API credentials found, some functionality may be limited")
    
    provider = BinanceDataProvider(api_key=api_key, api_secret=api_secret)
    
    # Create the agent
    original_agent = LiquidityAnalystAgent(data_fetcher=provider)
    
    # Save references to original methods
    original_fetch_market_data = original_agent._fetch_market_data
    original_analyze_order_book = original_agent._analyze_order_book
    original_generate_signal = original_agent._generate_signal
    
    # Replace with debug versions that log everything
    def debug_fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"DEBUG FETCH_MARKET_DATA: Called with symbol={symbol}")
        
        # Call original method
        result = original_fetch_market_data(symbol, **kwargs)
        
        # Log the result
        if result and 'order_book' in result:
            order_book = result['order_book']
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            logger.info(f"FETCH RESULT: {len(bids)} bids, {len(asks)} asks")
            
            # Check for empty order book
            if not bids or not asks:
                logger.critical("EMPTY ORDER BOOK DETECTED - Should trigger mock data")
                
                # Calculate bid/ask ratio
                bid_total = order_book.get('bid_total', 0)
                ask_total = order_book.get('ask_total', 0)
                bid_ask_ratio = bid_total / ask_total if ask_total else 0
                
                logger.info(f"Empty order book bid/ask ratio: {bid_ask_ratio}")
        
        return result
    
    def debug_analyze_order_book(self, order_book, market_context=None):
        logger.info("DEBUG ANALYZE_ORDER_BOOK: Called")
        
        # Log input details
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        logger.info(f"Input order book: {len(bids)} bids, {len(asks)} asks")
        
        # Check for extreme ratio triggers
        if bids and asks:
            bid_total = sum(float(b[0]) * float(b[1]) for b in bids)
            ask_total = sum(float(a[0]) * float(a[1]) for a in asks)
            ratio = bid_total / ask_total if ask_total > 0 else 1.0
            logger.info(f"ORDER BOOK RATIO: {ratio:.4f}")
            logger.info(f"Should trigger SELL (ratio < 0.75): {ratio < 0.75}")
            logger.info(f"Should trigger BUY (ratio > 1.25): {ratio > 1.25}")
            
            # Check the first few levels
            logger.info(f"Sample bids: {bids[:3]}")
            logger.info(f"Sample asks: {asks[:3]}")
        
        # Call original method
        result = original_analyze_order_book(order_book, market_context)
        
        # Log output details
        logger.info(f"Output metrics: bid_ask_ratio={result.get('bid_ask_ratio', 0)}")
        logger.info(f"Bid depth: {result.get('bid_depth_usdt', 0)}, Ask depth: {result.get('ask_depth_usdt', 0)}")
        
        # Check thresholds again with output values
        ratio = result.get('bid_ask_ratio', 1.0)
        logger.info(f"RESULT RATIO CHECK: {ratio:.4f} < 0.75 = {ratio < 0.75}")
        logger.info(f"RESULT RATIO CHECK: {ratio:.4f} > 1.25 = {ratio > 1.25}")
        
        return result
    
    def debug_generate_signal(self, metrics, market_context=None):
        logger.info("DEBUG GENERATE_SIGNAL: Called")
        
        # Log key metrics for signal generation
        bid_ask_ratio = metrics.get('bid_ask_ratio', 1.0)
        bid_depth = metrics.get('bid_depth_usdt', 0)
        ask_depth = metrics.get('ask_depth_usdt', 0)
        
        logger.info(f"Signal input - bid/ask ratio: {bid_ask_ratio:.4f}")
        logger.info(f"Signal input - bid depth: {bid_depth:.2f}, ask depth: {ask_depth:.2f}")
        
        # Direct check of thresholds (this is what should trigger signals)
        if bid_depth > 0 and ask_depth > 0:
            logger.info(f"RATIO < 0.75 check: {bid_ask_ratio < 0.75}")
            logger.info(f"RATIO > 1.25 check: {bid_ask_ratio > 1.25}")
            
            if bid_ask_ratio < 0.75:
                logger.info("Should generate SELL signal")
            elif bid_ask_ratio > 1.25:
                logger.info("Should generate BUY signal")
            else:
                logger.info("Should not trigger threshold signal")
        
        # Call original method
        signal, confidence, explanation = original_generate_signal(metrics, market_context)
        
        # Log the result
        logger.info(f"Signal result: {signal}, confidence: {confidence}")
        logger.info(f"Explanation: {explanation}")
        
        return signal, confidence, explanation
    
    # Replace the methods
    original_agent._fetch_market_data = lambda symbol, **kwargs: debug_fetch_market_data(original_agent, symbol, **kwargs)
    original_agent._analyze_order_book = lambda order_book, market_context=None: debug_analyze_order_book(original_agent, order_book, market_context)
    original_agent._generate_signal = lambda metrics, market_context=None: debug_generate_signal(original_agent, metrics, market_context)
    
    # Test with a direct call to the agent (this is how the main system uses it)
    logger.info("\n==== TESTING DIRECT AGENT CALL WITH FULL PIPELINE ====")
    
    symbol = "BTCUSDT"
    logger.info(f"Analyzing {symbol} with full pipeline...")
    result = original_agent.analyze(symbol=symbol)
    
    logger.info(f"Final agent result: {result.get('signal')}, confidence: {result.get('confidence')}")
    
    logger.info("==== SYSTEM FLOW DEBUG COMPLETE ====")
    
if __name__ == "__main__":
    main()