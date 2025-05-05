#!/usr/bin/env python
"""
Test script for the enhanced LiquidityAnalystAgent with liquidity zone detection.
"""

import os
import json
import logging
from typing import Dict, Any

from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from binance_data_provider import BinanceDataProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_liquidity_zones')

def create_sample_order_book() -> Dict[str, Any]:
    """
    Create a sample order book with some price clusters for testing.
    
    This simulates a realistic order book structure with some deliberate
    support/resistance clusters and volume gaps for testing.
    
    Returns:
        Dictionary containing a simulated order book
    """
    # Base price
    base_price = 50000.0
    
    # Create bids (buy orders) with a few clusters
    bids = []
    
    # Support cluster 1 (strong)
    support_level_1 = base_price - 500
    for i in range(5):
        price = support_level_1 - (i * 10)
        # Higher volume at the support level
        volume = 5.0 if i == 0 else 2.0 - (i * 0.2)
        bids.append([price, volume])
    
    # Support cluster 2 (medium)
    support_level_2 = base_price - 1000
    for i in range(3):
        price = support_level_2 - (i * 10)
        volume = 3.0 if i == 0 else 1.5 - (i * 0.2)
        bids.append([price, volume])
    
    # Regular bids between clusters
    for i in range(20):
        price = base_price - 100 - (i * 25)
        if abs(price - support_level_1) > 100 and abs(price - support_level_2) > 100:
            # Create a liquidity gap
            volume = 0.1 if (i % 3 == 0) else 0.8
            bids.append([price, volume])
    
    # Create asks (sell orders) with a few clusters
    asks = []
    
    # Resistance cluster 1 (strong)
    resistance_level_1 = base_price + 300
    for i in range(5):
        price = resistance_level_1 + (i * 10)
        # Higher volume at the resistance level
        volume = 4.0 if i == 0 else 1.8 - (i * 0.2)
        asks.append([price, volume])
    
    # Resistance cluster 2 (medium)
    resistance_level_2 = base_price + 800
    for i in range(3):
        price = resistance_level_2 + (i * 10)
        volume = 2.5 if i == 0 else 1.2 - (i * 0.2)
        asks.append([price, volume])
    
    # Regular asks between clusters
    for i in range(20):
        price = base_price + 50 + (i * 25)
        if abs(price - resistance_level_1) > 100 and abs(price - resistance_level_2) > 100:
            # Create a liquidity gap
            volume = 0.2 if (i % 4 == 0) else 0.7
            asks.append([price, volume])
    
    # Sort bids and asks
    bids.sort(key=lambda x: float(x[0]), reverse=True)
    asks.sort(key=lambda x: float(x[0]))
    
    # Create order book
    order_book = {
        "bids": bids,
        "asks": asks,
        "timestamp": 1651234567890
    }
    
    return order_book

def test_with_mock_data():
    """Test LiquidityAnalystAgent with mock order book data."""
    logger.info("Testing LiquidityAnalystAgent with mock order book data")
    
    # Create mock order book
    order_book = create_sample_order_book()
    
    # Create mock market data
    market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "order_book": order_book
    }
    
    # Create agent
    agent = LiquidityAnalystAgent()
    
    # Analyze liquidity
    result = agent.analyze(market_data)
    
    # Check if analysis was successful
    if result.get('status') != 'success':
        logger.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    # Extract key metrics
    signal = result.get('signal', 'NEUTRAL')
    confidence = result.get('confidence', 0)
    entry_zone = result.get('entry_zone')
    stop_loss_zone = result.get('stop_loss_zone')
    liquidity_zones = result.get('liquidity_zones', {})
    
    # Display results
    logger.info(f"Signal: {signal} with {confidence}% confidence")
    logger.info(f"Entry zone: {entry_zone}")
    logger.info(f"Stop-loss zone: {stop_loss_zone}")
    
    # Display support/resistance clusters
    support_clusters = liquidity_zones.get('support_clusters', [])
    resistance_clusters = liquidity_zones.get('resistance_clusters', [])
    gaps = liquidity_zones.get('gaps', [])
    
    logger.info(f"Support clusters: {support_clusters}")
    logger.info(f"Resistance clusters: {resistance_clusters}")
    logger.info(f"Liquidity gaps: {gaps}")
    
    # Save results to file for inspection
    with open('liquidity_analysis_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info("Results saved to liquidity_analysis_result.json")
    logger.info("Test completed successfully")

def test_with_binance_data():
    """Test LiquidityAnalystAgent with real Binance data."""
    logger.info("Testing LiquidityAnalystAgent with real Binance data")
    
    # Check if Binance API keys are available
    if 'BINANCE_API_KEY' not in os.environ or 'BINANCE_API_SECRET' not in os.environ:
        logger.warning("Binance API keys not found in environment variables")
        logger.warning("Using Binance without authentication (limited API access)")
    
    # Create data provider
    data_provider = BinanceDataProvider()
    
    # Create agent
    agent = LiquidityAnalystAgent(data_fetcher=data_provider)
    
    # Analyze liquidity
    result = agent.analyze("BTC/USDT")
    
    # Check if analysis was successful
    if result.get('status') != 'success':
        logger.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    # Extract key metrics
    signal = result.get('signal', 'NEUTRAL')
    confidence = result.get('confidence', 0)
    entry_zone = result.get('entry_zone')
    stop_loss_zone = result.get('stop_loss_zone')
    liquidity_zones = result.get('liquidity_zones', {})
    
    # Display results
    logger.info(f"Signal: {signal} with {confidence}% confidence")
    logger.info(f"Entry zone: {entry_zone}")
    logger.info(f"Stop-loss zone: {stop_loss_zone}")
    
    # Display support/resistance clusters
    support_clusters = liquidity_zones.get('support_clusters', [])
    resistance_clusters = liquidity_zones.get('resistance_clusters', [])
    gaps = liquidity_zones.get('gaps', [])
    
    logger.info(f"Support clusters: {support_clusters}")
    logger.info(f"Resistance clusters: {resistance_clusters}")
    logger.info(f"Liquidity gaps: {gaps}")
    
    # Save results to file for inspection
    with open('binance_liquidity_analysis_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info("Results saved to binance_liquidity_analysis_result.json")
    logger.info("Test completed successfully")

def main():
    """Run tests for the enhanced LiquidityAnalystAgent."""
    # Test with mock data
    test_with_mock_data()
    
    # Test with real Binance data
    test_with_binance_data()

if __name__ == '__main__':
    main()