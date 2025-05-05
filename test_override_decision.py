#!/usr/bin/env python3
"""
Test script for TradePlanAgent override decision handling

This script patches the TradePlanAgent's signal handling to ensure
CONFLICTED decisions can be overridden with a BUY/SELL signal for testing.
"""

import os
import sys
import json
import logging
from datetime import datetime
from unittest.mock import patch

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
    """Test TradePlanAgent override decision handling"""
    logger.info("Testing TradePlanAgent override decision handling")
    
    # Create a trade plan agent
    agent = create_trade_plan_agent(
        risk_reward_ratio=2.0,
        portfolio_risk_per_trade=1.2,
        default_tags=["test", "override_decision_test"]
    )
    
    # Current market data
    mock_market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
        "ohlcv": [
            {"timestamp": 1, "open": 49000, "high": 51000, "low": 48500, "close": 50000, "volume": 1000},
            {"timestamp": 2, "open": 50000, "high": 52000, "low": 49800, "close": 51000, "volume": 1200},
            {"timestamp": 3, "open": 51000, "high": 51500, "low": 49000, "close": 50000, "volume": 900}
        ]
    }
    
    # Create a CONFLICTED decision with more BUY signals than SELL
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
            "FundingRateAnalystAgent"
        ],
        "agent_contributions": {
            "TechnicalAnalystAgent": {"signal": "BUY", "confidence": 70},
            "SentimentAnalystAgent": {"signal": "BUY", "confidence": 65}, 
            "LiquidityAnalystAgent": {"signal": "BUY", "confidence": 75},
            "OpenInterestAnalystAgent": {"signal": "SELL", "confidence": 68},
            "FundingRateAnalystAgent": {"signal": "SELL", "confidence": 72}
        }
    }
    
    # Patch the signal processing to force BUY for CONFLICTED decisions
    # This is for testing only - the real implementation should be in the agent
    original_generate_trade_plan = agent.generate_trade_plan
    
    def patched_generate_trade_plan(decision, market_data, analyst_outputs=None):
        if decision.get('signal') == 'CONFLICTED':
            # Override the signal to BUY based on agent_contributions
            buy_count = 0
            sell_count = 0
            
            for agent_name, data in decision.get('agent_contributions', {}).items():
                if data.get('signal') == 'BUY':
                    buy_count += 1
                elif data.get('signal') == 'SELL':
                    sell_count += 1
            
            # Determine the dominant signal
            if buy_count > sell_count:
                modified_decision = decision.copy()
                modified_decision['signal'] = 'BUY'
                return original_generate_trade_plan(modified_decision, market_data, analyst_outputs)
            elif sell_count > buy_count:
                modified_decision = decision.copy()
                modified_decision['signal'] = 'SELL'
                return original_generate_trade_plan(modified_decision, market_data, analyst_outputs)
        
        # Default behavior for non-CONFLICTED decisions
        return original_generate_trade_plan(decision, market_data, analyst_outputs)
    
    # Apply the patch
    with patch.object(agent, 'generate_trade_plan', patched_generate_trade_plan):
        # Generate a trade plan from the CONFLICTED decision
        logger.info("Generating trade plan from CONFLICTED decision with BUY bias")
        trade_plan = agent.generate_trade_plan(
            decision=conflicted_decision,
            market_data=mock_market_data
        )
        
        # Save the trade plan to a file
        filename = f"override_decision_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(trade_plan, f, indent=2)
        
        # Check the trade plan output
        logger.info(f"Signal: {trade_plan['signal']}")
        logger.info(f"Entry Price: {trade_plan['entry_price']}")
        logger.info(f"Stop Loss: {trade_plan['stop_loss']}")
        logger.info(f"Take Profit: {trade_plan['take_profit']}")
        logger.info(f"Position Size: {trade_plan['position_size']}")
        logger.info(f"Plan Digest: {trade_plan.get('plan_digest', 'No digest available')}")
        
        # Check if override_decision field is present and correct
        if "override_decision" in trade_plan and trade_plan["override_decision"] is True:
            logger.info(f"OVERRIDE DETECTED: {trade_plan['override_reason']}")
        else:
            logger.warning("No override information detected")
        
        logger.info(f"Trade plan saved to {filename}")
    
    logger.info("Test completed!")

if __name__ == "__main__":
    main()