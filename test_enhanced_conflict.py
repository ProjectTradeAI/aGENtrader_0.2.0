"""
Test for Enhanced Conflict Handling with Directional Confidence

This test specifically verifies the enhanced conflict handling mechanism with
explicit CONFLICTED signals and directional confidence metrics.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the modules to test
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.trade_plan_agent import create_trade_plan_agent, TradeType


def test_direct_conflict_decision():
    """Test handling of direct CONFLICTED signals with enhanced directional confidence."""
    logger.info("Running test for explicit CONFLICTED signal with directional confidence")
    
    # Create a TradePlanAgent instance with default config
    agent = create_trade_plan_agent()
    
    # Create a mock conflict decision with CONFLICTED signal and directional confidence
    mock_decision = {
        "signal": "CONFLICTED",
        "confidence": 40,
        "directional_confidence": 65,  # Strong directional confidence despite conflict
        "summary_confidence": {
            "average": 40,
            "weighted": 45, 
            "directional": 65
        },
        "conflict_score": 85,  # High conflict score
        "reason": "Strong disagreement between analyst agents",
        "decision_time": datetime.now().isoformat(),
        "opposing_signals": {
            "BUY": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
            "SELL": ["LiquidityAnalystAgent", "OpenInterestAnalystAgent"]
        },
        "underlying_signal": "BUY"  # The signal it would have been without conflict
    }
    
    # Mock market data with current price
    mock_market_data = {
        "symbol": "BTC/USDT",
        "price": 50000.0,
        "last": 50000.0,
        "bid": 49990.0,
        "ask": 50010.0,
        "historical": [
            {"time": 1714636800000, "open": 50000.0, "high": 51000.0, "low": 49000.0, "close": 50000.0, "volume": 100.0},
            {"time": 1714633200000, "open": 49500.0, "high": 50500.0, "low": 49000.0, "close": 50000.0, "volume": 90.0},
            {"time": 1714629600000, "open": 49000.0, "high": 49800.0, "low": 48500.0, "close": 49500.0, "volume": 80.0},
        ]
    }
    
    # Mock analyst outputs
    mock_analyst_outputs = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 75,
            "reason": "Strong bullish momentum with RSI crossing above 50"
        },
        "sentiment_analysis": {
            "signal": "BUY", 
            "confidence": 80,
            "reason": "Positive news flow and social sentiment metrics"
        },
        "liquidity_analysis": {
            "signal": "SELL",
            "confidence": 65,
            "reason": "Significant sell walls at 50500 and 51000"
        },
        "open_interest_analysis": {
            "signal": "SELL",
            "confidence": 70,
            "reason": "Rising open interest with falling price indicates bearish momentum"
        }
    }
    
    # Generate trade plan
    trade_plan = agent.generate_trade_plan(
        decision=mock_decision,
        market_data=mock_market_data,
        analyst_outputs=mock_analyst_outputs
    )
    
    # Verify the trade plan
    assert trade_plan is not None, "Trade plan should not be None"
    
    # Verify explicit CONFLICTED handling
    assert trade_plan.get("conflict_flag", False) == True, "Trade plan should have conflict_flag=True"
    
    # Verify position size reduction (should be 70% reduction)
    # For CONFLICTED signal, we expect only 30% of normal position size
    position_size = trade_plan.get("position_size", 0)
    
    # The base position size would be in the low tier (0.3-0.4 range)
    # With 70% reduction, we'd expect position_size to be around 0.1-0.12
    # (exact value depends on agent config)
    logger.info(f"Position size: {position_size}")
    assert position_size < 0.15, "Position size should be reduced by 70%"
    
    # Verify directional confidence was preserved in summary_confidence
    summary_confidence = trade_plan.get("summary_confidence", {})
    logger.info(f"Summary confidence from trade plan: {summary_confidence}")
    logger.info(f"Original directional confidence: {mock_decision.get('directional_confidence')}")
    directional_value = summary_confidence.get("directional")
    logger.info(f"Got directional confidence: {directional_value}")
    assert isinstance(summary_confidence, dict), "summary_confidence should be a dictionary"
    assert directional_value == 65, f"Directional confidence should be preserved in summary_confidence (got {directional_value}, expected 65)"
    
    # Verify the plan digest mentions explicit conflict
    plan_digest = trade_plan.get("plan_digest", "")
    logger.info(f"Plan digest content: '{plan_digest}'")
    assert "EXPLICIT CONFLICT DETECTED" in plan_digest, "Plan digest should mention EXPLICIT CONFLICT DETECTED"
    assert "EXTREME CAUTION" in plan_digest, "Plan digest should advise extreme caution"
    assert "directional confidence" in plan_digest.lower(), "Plan digest should include directional confidence"
    
    # Verify conflict tags
    tags = trade_plan.get("tags", [])
    assert "conflicted" in tags, "Tags should include 'conflicted'"
    assert "position_reduced_70pct" in tags, "Tags should include 'position_reduced_70pct'"
    
    # Print the trade plan summary for manual review
    logger.info("Trade plan generated successfully")
    agent.log_trade_plan_summary(trade_plan)
    
    # Save to file for record
    with open("explicit_conflict_test_result.json", "w") as f:
        json.dump(trade_plan, f, indent=2, default=str)
        
    logger.info("Test completed successfully")
    return trade_plan


if __name__ == "__main__":
    # Run the test
    test_direct_conflict_decision()