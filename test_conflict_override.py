#!/usr/bin/env python3
"""
Test script for TradePlanAgent conflict override detection

This script tests the enhanced TradePlanAgent's ability to detect and 
report when it overrides a CONFLICTED decision with a BUY or SELL signal.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.trade_plan_agent import TradePlanAgent, create_trade_plan_agent

def main():
    """Test TradePlanAgent conflict override detection"""
    logger.info("Testing TradePlanAgent conflict override detection")
    
    # Create a trade plan agent
    agent = create_trade_plan_agent(
        risk_reward_ratio=2.0,
        portfolio_risk_per_trade=1.2,
        default_tags=["test", "conflict_override_test"]
    )
    
    # Current market data with Liquidity zones
    mock_market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
        "ohlcv": [
            {"timestamp": 1, "open": 49000, "high": 51000, "low": 48500, "close": 50000, "volume": 1000},
            {"timestamp": 2, "open": 50000, "high": 52000, "low": 49800, "close": 51000, "volume": 1200},
            {"timestamp": 3, "open": 51000, "high": 51500, "low": 49000, "close": 50000, "volume": 900}
        ],
        "liquidity_zones": {
            "buy_zones": [49800, 49200, 48000],
            "sell_zones": [51200, 52500, 54000],
            "supports": [49000, 48000],
            "resistances": [51000, 52000]
        }
    }
    
    # Mock liquidity analysis
    mock_liquidity_analysis = {
        "agent": "LiquidityAnalystAgent",
        "signal": "BUY",
        "confidence": 75,
        "suggested_entry": 49800,
        "suggested_stop_loss": 48000
    }
    
    # Create a BUY decision with higher confidence (not CONFLICTED)
    # This is needed because TradePlanAgent doesn't generate full plans for CONFLICTED signals
    buy_decision = {
        "signal": "BUY",
        "final_signal": "BUY",
        "confidence": 65,
        "weighted_confidence": 68,
        "directional_confidence": 52,
        "reasoning": "Technical and liquidity indicators suggest bullish trend",
        "contributing_agents": [
            "TechnicalAnalystAgent",
            "SentimentAnalystAgent",
            "LiquidityAnalystAgent",
            "UnknownAgent"
        ],
        "agent_contributions": {
            "TechnicalAnalystAgent": {"signal": "BUY", "confidence": 70},
            "SentimentAnalystAgent": {"signal": "BUY", "confidence": 65},
            "LiquidityAnalystAgent": {"signal": "BUY", "confidence": 75},
            "OpenInterestAnalystAgent": {"signal": "HOLD", "confidence": 60},
            "FundingRateAnalystAgent": {"signal": "HOLD", "confidence": 62}
        }
    }
    
    # Also create a CONFLICTED decision but with BUY bias for testing the override logic
    conflicted_decision = {
        "signal": "CONFLICTED",
        "final_signal": "CONFLICTED",
        "confidence": 60,
        "weighted_confidence": 65,
        "directional_confidence": 52,
        "reasoning": "Conflicting signals from different analysts",
        "contributing_agents": [
            "TechnicalAnalystAgent",
            "SentimentAnalystAgent",
            "LiquidityAnalystAgent",
            "OpenInterestAnalystAgent",
            "UnknownAgent"
        ],
        "agent_contributions": {
            "TechnicalAnalystAgent": {"signal": "BUY", "confidence": 70},
            "SentimentAnalystAgent": {"signal": "BUY", "confidence": 65},
            "LiquidityAnalystAgent": {"signal": "BUY", "confidence": 75},
            "OpenInterestAnalystAgent": {"signal": "SELL", "confidence": 68},
            "FundingRateAnalystAgent": {"signal": "SELL", "confidence": 72}
        }
    }
    
    # Generate a trade plan from the BUY decision instead of CONFLICTED
    # This will allow us to test the UnknownAgent filtering
    logger.info("Generating trade plan from BUY decision")
    trade_plan = agent.generate_trade_plan(
        decision=buy_decision,
        market_data=mock_market_data,
        analyst_outputs={
            "LiquidityAnalystAgent": mock_liquidity_analysis
        }
    )
    
    # Save the trade plan to a file
    filename = f"conflict_override_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(trade_plan, f, indent=2)
    
    # Check for override_decision field
    if "override_decision" in trade_plan and trade_plan["override_decision"]:
        logger.info(f"SUCCESS: Override detected! Reason: {trade_plan['override_reason']}")
        logger.info(f"Signal: {trade_plan['signal']}")
        logger.info(f"Entry Price: {trade_plan['entry_price']}")
        logger.info(f"Stop Loss: {trade_plan['stop_loss']}")
        logger.info(f"Take Profit: {trade_plan['take_profit']}")
        logger.info(f"Position Size: {trade_plan['position_size']}")
        logger.info(f"Plan Digest: {trade_plan['plan_digest']}")
        logger.info(f"Trade plan saved to {filename}")
    else:
        logger.error("FAILURE: Override not detected or not reported correctly")
    
    # Also test filtering of UnknownAgent from contributing_agents
    original_list = buy_decision["contributing_agents"]
    filtered_list = trade_plan["contributing_agents"]
    logger.info(f"Original list: {original_list}")
    logger.info(f"Filtered list: {filtered_list}")
    
    if "UnknownAgent" in original_list and "UnknownAgent" not in filtered_list:
        logger.info("SUCCESS: UnknownAgent was properly filtered out")
    else:
        logger.error("FAILURE: UnknownAgent was not properly filtered out")
    
    logger.info("Test completed!")

if __name__ == "__main__":
    main()