#!/usr/bin/env python3
"""
Test script for TradePlanAgent integration

This script directly tests the integration of the TradePlanAgent into the trading system
by simulating a trade decision and generating a trade plan.
"""

import logging
import sys
import os
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_trade_plan_integration')

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Test the trade plan agent integration with mock data"""
    logger.info("Testing TradePlanAgent integration with mock data")
    
    # Mock a BUY decision from the DecisionAgent
    decision = {
        "signal": "BUY",
        "confidence": 75.5,
        "reasoning": "Technical indicators show strong bullish momentum",
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"]
    }
    
    # Mock market data with current price
    market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0  # Mock price
    }
    
    # Mock analyst outputs including liquidity analysis
    liquidity_analysis = {
        "signal": "BUY",
        "confidence": 65,
        "reasoning": "Strong support detected",
        "support_clusters": [49500.0, 49000.0],
        "resistance_clusters": [50500.0, 51000.0],
        "suggested_entry": 50100.0,
        "suggested_stop_loss": 49400.0
    }
    
    analyses = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 80,
            "reasoning": "All indicators bullish"
        },
        "sentiment_analysis": {
            "signal": "BUY",
            "confidence": 70,
            "reasoning": "Positive market sentiment"
        },
        "liquidity_analysis": liquidity_analysis
    }
    
    # Import the generate_trade_plan function
    try:
        from run_trading_system import generate_trade_plan
        
        # Generate a trade plan
        logger.info("Calling generate_trade_plan function")
        trade_plan = generate_trade_plan(decision, market_data, analyses)
        
        # Check if we successfully got a trade plan
        if trade_plan and not trade_plan.get('error', False):
            logger.info("✅ Trade plan generated successfully")
            
            # Print the trade plan details
            logger.info(f"Signal: {trade_plan.get('signal')}")
            logger.info(f"Confidence: {trade_plan.get('confidence')}%")
            logger.info(f"Entry Price: {trade_plan.get('entry_price')}")
            logger.info(f"Stop-Loss: {trade_plan.get('stop_loss')}")
            logger.info(f"Take-Profit: {trade_plan.get('take_profit')}")
            logger.info(f"Position Size: {trade_plan.get('position_size')}")
            
            # Combine with original decision
            decision.update(trade_plan)
            
            # Print the combined decision in JSON format
            logger.info("Combined Decision with Trade Plan:\n" + json.dumps(decision, indent=2))
            
            return 0
        else:
            logger.error(f"❌ Trade plan generation failed: {trade_plan.get('message', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error testing trade plan integration: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())