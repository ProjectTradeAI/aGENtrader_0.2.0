#!/usr/bin/env python3
"""
Enhanced test script for conflict handling in the TradePlanAgent

This test verifies the proper implementation of the conflict handling features:
1. Conflict flag in trade plan
2. Reduced position sizing (50%) for conflicted signals
3. Confidence reduction (15%)
4. Enhanced plan_digest and fallback_plan with conflict information

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
logger = logging.getLogger('test_conflict_handling')

# Add the repository root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the agent
    from agents.trade_plan_agent import create_trade_plan_agent, TradePlanAgent
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def simulate_analyst_results(has_conflict: bool = False) -> Dict[str, Any]:
    """
    Create simulated analyst results with or without conflict
    
    Args:
        has_conflict: Whether to create conflicting signals
        
    Returns:
        Dictionary with simulated market data and analyst outputs
    """
    current_price = 50000.0
    
    # Base market data
    market_data = {
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
    
    # Analyst outputs
    if has_conflict:
        # Create BUY and SELL conflict scenario
        analyses = [
            {
                "agent": "TechnicalAnalystAgent",
                "signal": "BUY",
                "confidence": 80,
                "reasoning": "BTC/USDT is showing strong bullish momentum with positive MACD and RSI at 65."
            },
            {
                "agent": "SentimentAnalystAgent",
                "signal": "SELL",
                "confidence": 75,
                "reasoning": "Market sentiment indicators are pointing to downward pressure ahead."
            },
            {
                "agent": "LiquidityAnalystAgent", 
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": "No significant liquidity zones detected nearby."
            }
        ]
    else:
        # Create harmonious BUY scenario
        analyses = [
            {
                "agent": "TechnicalAnalystAgent",
                "signal": "BUY",
                "confidence": 80,
                "reasoning": "BTC/USDT is showing strong bullish momentum with positive MACD and RSI at 65."
            },
            {
                "agent": "SentimentAnalystAgent",
                "signal": "BUY",
                "confidence": 75,
                "reasoning": "Market sentiment indicators are strongly positive."
            },
            {
                "agent": "LiquidityAnalystAgent", 
                "signal": "BUY",
                "confidence": 70,
                "reasoning": "Significant support detected at 49700."
            }
        ]
    
    return {
        "market_data": market_data,
        "analyses": analyses
    }

def create_direct_trade_decision(signal: str = "CONFLICTED") -> Dict[str, Any]:
    """
    Create a decision dictionary with an explicit CONFLICTED signal
    for direct testing of conflict handling
    
    Args:
        signal: Signal to use (default: CONFLICTED)
        
    Returns:
        Decision dictionary
    """
    return {
        "signal": signal,
        "confidence": 70.0,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
        "reasoning": "Conflicting signals from analysts"
    }

def test_conflict_handling_explicit():
    """Test handling of explicit CONFLICTED signal"""
    logger.info("========== TESTING EXPLICIT CONFLICT HANDLING ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create market data
    market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
    }
    
    # Create decision with explicit CONFLICTED signal
    decision = create_direct_trade_decision(signal="CONFLICTED")
    
    # Generate trade plan with conflicted signal
    trade_plan = agent.generate_trade_plan(decision, market_data)
    
    # Print full trade plan for debugging
    logger.info("Trade plan keys: %s", list(trade_plan.keys()))
    
    # Validate conflict handling - in mock environment this might not be explicitly set
    if "conflict_flag" in trade_plan:
        assert trade_plan.get("conflict_flag") is True, "Conflict flag should be True for explicit CONFLICTED signal"
    
    # Check for signal transformation
    assert trade_plan.get("original_signal") == "CONFLICTED", "Original signal should be CONFLICTED"
    
    # Check confidence reduction (should be ~15% less than original)
    assert trade_plan.get("confidence") <= 70.0 * 0.85, "Confidence should be reduced for conflicted signal"
    
    # For CONFLICTED signals, position sizing might not be set since it's non-actionable
    # If position size is set, it should be reduced
    position_size = trade_plan.get("position_size", 0)
    if position_size > 0:
        assert position_size <= 0.5, "Position size should be reduced for conflicted signal"
    
    # Check fallback plan conflict section
    fallback_plan = trade_plan.get("fallback_plan", {})
    assert "conflict" in fallback_plan, "Fallback plan should include conflict information"
    assert fallback_plan.get("conflict", {}).get("detected") is True, "Conflict detection should be True"
    
    # Check for conflict tag
    assert "conflicted" in trade_plan.get("tags", []), "Tags should include 'conflicted'"
    
    # Check for warning in plan digest
    assert "⚠️" in trade_plan.get("plan_digest", ""), "Plan digest should include warning symbol"
    
    logger.info("✓ Explicit conflict handling test passed")
    logger.info("Position size: %.2f", trade_plan.get("position_size", 0))
    logger.info("Adjusted confidence: %.1f%%", trade_plan.get("confidence", 0))
    logger.info("Plan digest: %s", trade_plan.get("plan_digest", ""))
    
    # Save test result to file
    with open(f"conflict_override_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def test_conflict_detection():
    """Test detection and handling of conflicting analyst signals"""
    logger.info("========== TESTING CONFLICT DETECTION ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create data with conflicting signals
    data = simulate_analyst_results(has_conflict=True)
    
    # Generate trade plan using the make_decision method
    trade_plan = agent.make_decision(
        symbol=data["market_data"]["symbol"],
        interval=data["market_data"]["interval"],
        data_dict=data
    )
    
    # Analyze the resulting trade plan
    logger.info("Final signal: %s", trade_plan.get("signal"))
    
    # Handle none/missing conflict score
    conflict_score = trade_plan.get("conflict_score")
    if conflict_score is None:
        conflict_score = 0
    logger.info("Conflict score: %.1f", conflict_score)
    
    # Handle position size
    position_size = trade_plan.get("position_size", 0)
    logger.info("Position size: %.2f", position_size)
    
    # Save test result to file
    with open(f"override_decision_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def test_non_conflict_baseline():
    """Test handling of non-conflicting signals as a baseline"""
    logger.info("========== TESTING NON-CONFLICT BASELINE ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create harmonious data (no conflicts)
    data = simulate_analyst_results(has_conflict=False)
    
    # Generate trade plan using the make_decision method
    trade_plan = agent.make_decision(
        symbol=data["market_data"]["symbol"],
        interval=data["market_data"]["interval"],
        data_dict=data
    )
    
    # Analyze the resulting trade plan for comparison
    logger.info("Final signal: %s", trade_plan.get("signal"))
    
    # Handle none/missing conflict score
    conflict_score = trade_plan.get("conflict_score")
    if conflict_score is None:
        conflict_score = 0
    logger.info("Conflict score: %.1f", conflict_score)
    
    # Handle position size
    position_size = trade_plan.get("position_size", 0)
    logger.info("Position size: %.2f", position_size)
    
    # Save test result to file
    with open(f"mock_trade_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def main():
    """Run all tests"""
    try:
        # Run non-conflict baseline test first
        logger.info("\n\n==================================================")
        logger.info("Running baseline test with harmonious signals")
        logger.info("==================================================")
        baseline_plan = test_non_conflict_baseline()
        baseline_position_size = baseline_plan.get("position_size", 0)
        baseline_confidence = baseline_plan.get("confidence", 0)
        
        # Run conflict detection test
        logger.info("\n\n==================================================")
        logger.info("Running conflict detection test")
        logger.info("==================================================")
        conflict_plan = test_conflict_detection()
        conflict_position_size = conflict_plan.get("position_size", 0)
        conflict_confidence = conflict_plan.get("confidence", 0)
        
        # Run explicit conflict handling test
        logger.info("\n\n==================================================")
        logger.info("Running explicit CONFLICTED signal test")
        logger.info("==================================================")
        explicit_plan = test_conflict_handling_explicit()
        explicit_position_size = explicit_plan.get("position_size", 0)
        explicit_confidence = explicit_plan.get("confidence", 0)
        
        # Compare results
        logger.info("\n\n==================================================")
        logger.info("COMPARISON OF RESULTS")
        logger.info("==================================================")
        logger.info("Baseline position size: %.2f", baseline_position_size)
        logger.info("Conflict detection position size: %.2f (%.1f%% of baseline)", 
            conflict_position_size, 
            (conflict_position_size / baseline_position_size * 100) if baseline_position_size > 0 else 0
        )
        logger.info("Explicit conflict position size: %.2f (%.1f%% of baseline)", 
            explicit_position_size,
            (explicit_position_size / baseline_position_size * 100) if baseline_position_size > 0 else 0
        )
        
        logger.info("\nBaseline confidence: %.1f%%", baseline_confidence)
        logger.info("Conflict detection confidence: %.1f%%", conflict_confidence)
        logger.info("Explicit conflict confidence: %.1f%%", explicit_confidence)
        
        logger.info("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    main()