#!/usr/bin/env python3
"""
Test script for conflict override in the TradePlanAgent

This test verifies that the trade plan agent can override a CONFLICTED signal
to generate an actionable trade plan when appropriate, with appropriate risk reduction.

Author: aGENtrader Team
Date: May 4, 2025
"""

import sys
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_conflict_override')

# Add the repository root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the agent
    from agents.trade_plan_agent import create_trade_plan_agent, TradePlanAgent
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def create_conflicted_decision_with_override(override_to: str = "BUY") -> Dict[str, Any]:
    """
    Create a decision dictionary with an explicit CONFLICTED signal
    but with agent contributions that would justify overriding to a specific signal
    
    Args:
        override_to: Signal to override to (BUY or SELL)
        
    Returns:
        Decision dictionary
    """
    # Create agent contributions with a bias toward the override signal
    if override_to == "BUY":
        agent_contributions = {
            "TechnicalAnalystAgent": {
                "signal": "BUY",
                "confidence": 85,
                "reasoning": "Strong bullish momentum"
            },
            "SentimentAnalystAgent": {
                "signal": "SELL",
                "confidence": 65,
                "reasoning": "Negative market sentiment"
            },
            "LiquidityAnalystAgent": {
                "signal": "BUY",
                "confidence": 75,
                "reasoning": "Strong support level detected"
            },
            "FundingRateAnalystAgent": {
                "signal": "BUY",
                "confidence": 70,
                "reasoning": "Positive funding rate"
            }
        }
    else:  # SELL
        agent_contributions = {
            "TechnicalAnalystAgent": {
                "signal": "SELL",
                "confidence": 85,
                "reasoning": "Strong bearish momentum"
            },
            "SentimentAnalystAgent": {
                "signal": "BUY",
                "confidence": 65,
                "reasoning": "Positive market sentiment"
            },
            "LiquidityAnalystAgent": {
                "signal": "SELL",
                "confidence": 75,
                "reasoning": "Strong resistance level detected"
            },
            "FundingRateAnalystAgent": {
                "signal": "SELL",
                "confidence": 70,
                "reasoning": "Negative funding rate"
            }
        }
        
    return {
        "signal": "CONFLICTED",  # Conflicted signal
        "original_signal": "CONFLICTED",
        "final_signal": "CONFLICTED",
        "confidence": 70.0,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent", "LiquidityAnalystAgent", "FundingRateAnalystAgent"],
        "reasoning": "Conflicting signals from analysts (3 BUY, 1 SELL)" if override_to == "BUY" else "Conflicting signals from analysts (3 SELL, 1 BUY)",
        "directional_confidence": 60.0,
        "agent_contributions": agent_contributions,
        "conflict_score": 25  # Moderate conflict (25%)
    }

def create_market_data() -> Dict[str, Any]:
    """Create simulated market data"""
    current_price = 50000.0
    
    # Base market data
    return {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": current_price,
        "ohlcv": [
            # timestamp, open, high, low, close, volume
            [datetime.now().timestamp() - 3600*3, 49800, 50200, 49700, 49900, 100],
            [datetime.now().timestamp() - 3600*2, 49900, 50300, 49800, 50100, 120],
            [datetime.now().timestamp() - 3600, 50100, 50400, 49950, 50000, 150]
        ]
    }

def test_conflict_override_to_buy():
    """Test the agent's ability to override a CONFLICTED signal to BUY"""
    logger.info("========== TESTING CONFLICT OVERRIDE TO BUY ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create decision and market data
    decision = create_conflicted_decision_with_override(override_to="BUY")
    market_data = create_market_data()
    
    # Generate trade plan
    trade_plan = agent.generate_trade_plan(decision, market_data)
    
    # Verify the trade plan
    logger.info(f"Generated signal: {trade_plan.get('signal')}")
    logger.info(f"Position size: {trade_plan.get('position_size')}")
    logger.info(f"Confidence: {trade_plan.get('confidence')}%")
    logger.info(f"Conflict flag: {trade_plan.get('conflict_flag', False)}")
    
    # Validate the trade plan has a reduced position size compared to normal
    assert trade_plan.get("signal") == "BUY", "Trade plan should override to BUY"
    assert trade_plan.get("conflict_flag") is True, "Conflict flag should be True"
    
    # Estimated normal position size would be around 0.6 for 70% confidence
    # But with conflict, it should be around half that
    assert trade_plan.get("position_size") <= 0.35, "Position size should be reduced due to conflict"
    
    # Reduced confidence (15% reduction from base 70%)
    assert trade_plan.get("confidence") <= 70.0 * 0.85, "Confidence should be reduced"
    
    # Check for conflict tag
    assert "conflicted" in trade_plan.get("tags", []), "Tags should include 'conflicted'"
    
    # Look for conflict warning in plan digest
    assert "⚠️" in trade_plan.get("plan_digest", ""), "Plan digest should include warning symbol"
    
    # Save test result to file
    with open(f"conflict_override_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def test_conflict_override_to_sell():
    """Test the agent's ability to override a CONFLICTED signal to SELL"""
    logger.info("========== TESTING CONFLICT OVERRIDE TO SELL ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create decision and market data
    decision = create_conflicted_decision_with_override(override_to="SELL")
    market_data = create_market_data()
    
    # Generate trade plan
    trade_plan = agent.generate_trade_plan(decision, market_data)
    
    # Verify the trade plan
    logger.info(f"Generated signal: {trade_plan.get('signal')}")
    logger.info(f"Position size: {trade_plan.get('position_size')}")
    logger.info(f"Confidence: {trade_plan.get('confidence')}%")
    logger.info(f"Conflict flag: {trade_plan.get('conflict_flag', False)}")
    
    # Validate the trade plan
    assert trade_plan.get("signal") == "SELL", "Trade plan should override to SELL"
    assert trade_plan.get("conflict_flag") is True, "Conflict flag should be True"
    
    # Estimated normal position size would be around 0.6 for 70% confidence
    # But with conflict, it should be around half that
    assert trade_plan.get("position_size") <= 0.35, "Position size should be reduced due to conflict"
    
    # Reduced confidence (15% reduction from base 70%)
    assert trade_plan.get("confidence") <= 70.0 * 0.85, "Confidence should be reduced"
    
    # Check for conflict tag
    assert "conflicted" in trade_plan.get("tags", []), "Tags should include 'conflicted'"
    
    # Look for conflict warning in plan digest
    assert "⚠️" in trade_plan.get("plan_digest", ""), "Plan digest should include warning symbol"
    
    # Save test result to file
    with open(f"conflict_override_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def main():
    """Run all tests"""
    try:
        # Run BUY override test
        logger.info("\n\n==================================================")
        logger.info("Running test: Override CONFLICTED to BUY")
        logger.info("==================================================")
        buy_override_plan = test_conflict_override_to_buy()
        
        # Run SELL override test
        logger.info("\n\n==================================================")
        logger.info("Running test: Override CONFLICTED to SELL")
        logger.info("==================================================")
        sell_override_plan = test_conflict_override_to_sell()
        
        # Compare results
        logger.info("\n\n==================================================")
        logger.info("COMPARISON OF RESULTS")
        logger.info("==================================================")
        logger.info("BUY override position size: %.2f", buy_override_plan.get("position_size", 0))
        logger.info("SELL override position size: %.2f", sell_override_plan.get("position_size", 0))
        logger.info("BUY override confidence: %.1f%%", buy_override_plan.get("confidence", 0))
        logger.info("SELL override confidence: %.1f%%", sell_override_plan.get("confidence", 0))
        
        logger.info("\nAll tests completed successfully!")
        
    except AssertionError as e:
        logger.error(f"Test failed with assertion error: {e}")
        return False
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    main()