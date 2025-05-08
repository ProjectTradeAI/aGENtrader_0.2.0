"""
Test script for LiquidityAnalystAgent

This script directly tests the LiquidityAnalystAgent with debug output
"""
import json
import logging
import os
from agents.liquidity_analyst_agent import LiquidityAnalystAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test the liquidity analyst agent directly."""
    logger.info("Starting LiquidityAnalystAgent test")
    
    # Initialize the agent
    agent = LiquidityAnalystAgent()
    
    # Run analysis
    logger.info("Running analysis")
    results = agent.analyze("BTCUSDT")
    
    # Print results
    logger.info("=== ANALYSIS RESULT ===")
    logger.info(f"Signal: {results['signal']}")
    logger.info(f"Confidence: {results['confidence']}")
    logger.info(f"Entry: ${results.get('entry_zone', 'N/A')}")
    logger.info(f"Stop-Loss: ${results.get('stop_loss_zone', 'N/A')}")
    logger.info(f"Take-Profit: ${results.get('metrics', {}).get('suggested_take_profit', 'N/A')}")
    logger.info(f"Bid/Ask Ratio: {results.get('metrics', {}).get('bid_ask_ratio', 'N/A')}")
    
    if 'liquidity_zones' in results['metrics']:
        zones = results['metrics']['liquidity_zones']
        logger.info(f"Support Clusters: {len(zones.get('support_clusters', []))}")
        logger.info(f"Resistance Clusters: {len(zones.get('resistance_clusters', []))}")
    
    # Save results to a file for inspection
    with open("liquidity_analysis_result.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Results saved to liquidity_analysis_result.json")

if __name__ == "__main__":
    main()