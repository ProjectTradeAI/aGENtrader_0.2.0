#!/usr/bin/env python3
"""
Debug script for LiquidityAnalystAgent

This script directly tests the LiquidityAnalystAgent with debug output
to diagnose why it's consistently returning NEUTRAL signals.
"""

import logging
import json
import sys
from pprint import pprint
from typing import Dict, Any, List

from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from binance_data_provider import BinanceDataProvider

# Setup basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def main():
    """Run the liquidity analyst debug routine."""
    logger.info("Starting LiquidityAnalystAgent debug")
    
    # First, try to load an order book from a file if available
    try:
        with open('debug_order_book.json', 'r') as f:
            order_book = json.load(f)
            logger.info("Loaded order book from debug_order_book.json")
    except (FileNotFoundError, json.JSONDecodeError):
        logger.info("No valid order book file found, fetching from Binance")
        # Fetch fresh data
        data_fetcher = BinanceDataProvider()
        symbol = "BTCUSDT"
        order_book = data_fetcher.fetch_market_depth(symbol, limit=100)
        
        # Save to file for future debugging
        with open('debug_order_book.json', 'w') as f:
            json.dump(order_book, f, indent=2)
            logger.info(f"Saved order book to debug_order_book.json")
    
    # Get real-time order book data too
    data_fetcher = BinanceDataProvider()
    live_order_book = None
    
    try:
        symbol = "BTCUSDT"
        print(f"Fetching live order book from Binance for {symbol}...")
        live_order_book = data_fetcher.fetch_market_depth(symbol, limit=100)
        
        if live_order_book:
            # Calculate live bid/ask ratio directly
            live_bids = live_order_book.get('bids', [])
            live_asks = live_order_book.get('asks', [])
            live_bid_volume = sum(float(b[1]) for b in live_bids)
            live_ask_volume = sum(float(a[1]) for a in live_asks)
            live_ratio = live_bid_volume / live_ask_volume if live_ask_volume > 0 else 0
            
            print(f"LIVE DATA - Total bid volume: {live_bid_volume}")
            print(f"LIVE DATA - Total ask volume: {live_ask_volume}")
            print(f"LIVE DATA - Bid/Ask ratio: {live_ratio}")
            
            # Compare with our test data
            print(f"\nCOMPARISON BETWEEN TEST AND LIVE DATA:")
            print(f"Test data bid/ask ratio: {bid_ask_ratio}")
            print(f"Live data bid/ask ratio: {live_ratio}")
            print(f"This helps verify if our testing data matches current conditions\n")
    except Exception as e:
        print(f"Error fetching live order book: {str(e)}")
        print("Continuing with test data only...")
    
    # Create a liquidity analyst agent with modified config for more aggressive signals
    agent = LiquidityAnalystAgent(
        data_fetcher=data_fetcher,  # Pass the data fetcher
        config={
            "depth_levels": 100,
            "price_bin_size_pct": 0.1,  # Make it more sensitive
            "large_order_threshold": 1.5,  # Even more sensitive (was 2.0)
            "support_resistance_strength": 1.5,  # More sensitive clusters
            "min_level_count": 3,
            "bid_ask_threshold": 0.75  # Make sure this matches our code changes
        }
    )
    
    # Analyze the order book
    logger.info("Starting analysis of order book")
    
    # Print size of data
    logger.info(f"Order book has {len(order_book['bids'])} bids and {len(order_book['asks'])} asks")
    
    # Print first few entries
    logger.info(f"Sample bids: {order_book['bids'][:3]}")
    logger.info(f"Sample asks: {order_book['asks'][:3]}")
    
    # Calculate bid/ask ratio directly
    total_bid_volume = sum(float(b[1]) for b in order_book['bids'])
    total_ask_volume = sum(float(a[1]) for a in order_book['asks'])
    bid_ask_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0
    
    logger.info(f"Direct calculation - Total bid volume: {total_bid_volume}")
    logger.info(f"Direct calculation - Total ask volume: {total_ask_volume}")
    logger.info(f"Direct calculation - Bid/Ask ratio: {bid_ask_ratio}")
    
    # If ratio is far from 1.0, we should get a clear signal
    if bid_ask_ratio < 0.9:
        logger.info(f"This should generate a SELL signal (bid_ask_ratio={bid_ask_ratio})")
    elif bid_ask_ratio > 1.1:
        logger.info(f"This should generate a BUY signal (bid_ask_ratio={bid_ask_ratio})")
    
    # Perform the analysis
    try:
        market_data = {"order_book": order_book, "symbol": "BTCUSDT"}
        result = agent.analyze(market_data)
        
        logger.info("=== ANALYSIS RESULT ===")
        logger.info(f"Signal: {result.get('signal')}")
        logger.info(f"Confidence: {result.get('confidence')}")
        logger.info(f"Explanation: {result.get('explanation')[0] if result.get('explanation') else 'No explanation'}")
        
        # Print key metrics
        metrics = result.get('metrics', {})
        logger.info(f"Bid/Ask ratio: {metrics.get('bid_ask_ratio')}")
        logger.info(f"Liquidity score: {metrics.get('liquidity_score')}")
        
        # Print any support/resistance areas
        liquidity_zones = metrics.get('liquidity_zones', {})
        support_clusters = liquidity_zones.get('support_clusters', [])
        resistance_clusters = liquidity_zones.get('resistance_clusters', [])
        
        logger.info(f"Support clusters: {len(support_clusters)}")
        for cluster in support_clusters[:3]:
            logger.info(f"  Support: price={cluster.get('price', 'N/A')}, strength={cluster.get('strength', 'N/A')}")
            
        logger.info(f"Resistance clusters: {len(resistance_clusters)}")
        for cluster in resistance_clusters[:3]:
            logger.info(f"  Resistance: price={cluster.get('price', 'N/A')}, strength={cluster.get('strength', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()