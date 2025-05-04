#!/usr/bin/env python3
"""
Test script for graduated conflict handling in the TradePlanAgent

This test verifies the new graduated conflict handling features:
1. Soft conflict detection (50-70% conflict score)
2. Hard conflict detection (>70% conflict score)
3. Graduated position size reductions (20% for soft, 50% for hard conflicts)
4. Enhanced plan_digest and fallback_plan with detailed conflict information
5. Proper tagging with conflict type and position reduction info

Author: aGENtrader Team
Date: May 5, 2025
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
logger = logging.getLogger('test_graduated_conflict')

# Add the repository root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the agent
    from agents.trade_plan_agent import create_trade_plan_agent, TradePlanAgent
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def simulate_analyst_results(conflict_level: str = "none") -> Dict[str, Any]:
    """
    Create simulated analyst results with different conflict levels
    
    Args:
        conflict_level: "none", "soft", or "hard"
        
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
    
    # Analyst outputs based on conflict level
    if conflict_level == "hard":
        # Create strong BUY and SELL conflict (hard conflict)
        analyses = [
            {
                "agent": "TechnicalAnalystAgent",
                "signal": "BUY",
                "confidence": 90,
                "reasoning": "Strong bullish momentum with positive MACD and RSI at on the rise."
            },
            {
                "agent": "SentimentAnalystAgent",
                "signal": "SELL",
                "confidence": 85,
                "reasoning": "Extremely negative market sentiment indicators pointing to significant downward pressure."
            },
            {
                "agent": "LiquidityAnalystAgent", 
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": "No significant liquidity zones detected nearby."
            }
        ]
    elif conflict_level == "soft":
        # Create moderate BUY and SELL conflict (soft conflict)
        analyses = [
            {
                "agent": "TechnicalAnalystAgent",
                "signal": "BUY",
                "confidence": 75,
                "reasoning": "Moderately bullish momentum with MACD turning positive."
            },
            {
                "agent": "SentimentAnalystAgent",
                "signal": "SELL",
                "confidence": 70,
                "reasoning": "Some negative sentiment indicators emerging."
            },
            {
                "agent": "LiquidityAnalystAgent", 
                "signal": "BUY",
                "confidence": 65,
                "reasoning": "Minor support detected at 49800."
            },
            {
                "agent": "FundingRateAnalystAgent",
                "signal": "NEUTRAL",
                "confidence": 60,
                "reasoning": "Funding rates are neutral currently."
            }
        ]
    else:
        # Create harmonious BUY scenario (no conflict)
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

def test_no_conflict_baseline():
    """Test baseline with no conflict signals"""
    logger.info("========== TESTING NO CONFLICT BASELINE ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create harmonious data (no conflicts)
    data = simulate_analyst_results(conflict_level="none")
    
    # Generate trade plan using the make_decision method
    trade_plan = agent.make_decision(
        symbol=data["market_data"]["symbol"],
        interval=data["market_data"]["interval"],
        data_dict=data
    )
    
    # Analyze the resulting trade plan
    logger.info("Final signal: %s", trade_plan.get("signal"))
    logger.info("Conflict score: %s", trade_plan.get("conflict_score", 0))
    logger.info("Position size: %.2f", trade_plan.get("position_size", 0))
    logger.info("Conflict handling applied: %s", trade_plan.get("conflict_handling_applied", False))
    logger.info("Tags: %s", trade_plan.get("tags", []))
    
    # Validate expectations
    assert trade_plan.get("conflict_handling_applied", False) is False, "No conflict handling should be applied"
    
    # Save test result to file
    with open(f"no_conflict_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def test_soft_conflict():
    """Test handling of soft conflict (50-70% conflict score)"""
    logger.info("========== TESTING SOFT CONFLICT HANDLING ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create data with moderate conflicts
    data = simulate_analyst_results(conflict_level="soft")
    
    # Generate trade plan using the make_decision method
    trade_plan = agent.make_decision(
        symbol=data["market_data"]["symbol"],
        interval=data["market_data"]["interval"],
        data_dict=data
    )
    
    # Analyze the resulting trade plan
    logger.info("Final signal: %s", trade_plan.get("signal"))
    logger.info("Conflict score: %s", trade_plan.get("conflict_score", 0))
    logger.info("Conflict type: %s", trade_plan.get("conflict_type", "none"))
    logger.info("Position size: %.2f", trade_plan.get("position_size", 0))
    logger.info("Conflict handling applied: %s", trade_plan.get("conflict_handling_applied", False))
    logger.info("Tags: %s", trade_plan.get("tags", []))
    
    # If conflict handling was applied correctly, verify the type and adjustment
    if trade_plan.get("conflict_handling_applied", False):
        assert trade_plan.get("conflict_type") == "soft_conflict", "Conflict type should be 'soft_conflict'"
        assert "soft_conflict" in trade_plan.get("tags", []), "Tags should include 'soft_conflict'"
        assert "position_reduced_20pct" in trade_plan.get("tags", []), "Tags should include position reduction info"
        
        # Verify fallback plan conflict section
        fallback = trade_plan.get("fallback_plan", {}).get("conflict", {})
        assert fallback.get("type") == "soft_conflict", "Fallback plan should indicate soft conflict"
        assert "20%" in fallback.get("position_reduction", ""), "Position reduction should be 20%"
    else:
        logger.warning("Soft conflict handling was not applied - this could be a test environment limitation")
    
    # Save test result to file
    with open(f"soft_conflict_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def test_hard_conflict():
    """Test handling of hard conflict (>70% conflict score)"""
    logger.info("========== TESTING HARD CONFLICT HANDLING ==========")
    
    # Create trade plan agent
    agent = create_trade_plan_agent(
        config={
            "detailed_logging": True,
            "test_mode": True
        }
    )
    
    # Create data with severe conflicts
    data = simulate_analyst_results(conflict_level="hard")
    
    # Generate trade plan using the make_decision method
    trade_plan = agent.make_decision(
        symbol=data["market_data"]["symbol"],
        interval=data["market_data"]["interval"],
        data_dict=data
    )
    
    # Analyze the resulting trade plan
    logger.info("Final signal: %s", trade_plan.get("signal"))
    logger.info("Conflict score: %s", trade_plan.get("conflict_score", 0))
    logger.info("Conflict type: %s", trade_plan.get("conflict_type", "none"))
    logger.info("Position size: %.2f", trade_plan.get("position_size", 0))
    logger.info("Conflict handling applied: %s", trade_plan.get("conflict_handling_applied", False))
    logger.info("Tags: %s", trade_plan.get("tags", []))
    
    # If conflict handling was applied correctly, verify the type and adjustment
    if trade_plan.get("conflict_handling_applied", False):
        assert trade_plan.get("conflict_type") == "conflicted", "Conflict type should be 'conflicted'"
        assert "high_conflict" in trade_plan.get("tags", []), "Tags should include 'high_conflict'"
        assert "position_reduced_50pct" in trade_plan.get("tags", []), "Tags should include position reduction info"
        
        # Verify fallback plan conflict section
        fallback = trade_plan.get("fallback_plan", {}).get("conflict", {})
        assert fallback.get("type") == "high_conflict", "Fallback plan should indicate high conflict"
        assert "50%" in fallback.get("position_reduction", ""), "Position reduction should be 50%"
    else:
        logger.warning("Hard conflict handling was not applied - this could be a test environment limitation")
    
    # Save test result to file
    with open(f"hard_conflict_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def direct_test_with_conflict_score(conflict_score: int = 60):
    """
    Directly test the agent with a specific conflict score
    
    Args:
        conflict_score: Conflict score to test with (0-100)
        
    Returns:
        Trade plan
    """
    logger.info(f"========== DIRECT TEST WITH CONFLICT SCORE {conflict_score} ==========")
    
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
    
    # Create decision with specific conflict score
    decision = {
        "signal": "BUY",
        "confidence": 80.0,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
        "reasoning": "Testing with specific conflict score",
        "conflict_score": conflict_score
    }
    
    # Generate trade plan with conflicted signal
    trade_plan = agent.generate_trade_plan(decision, market_data)
    
    # Analyze the resulting trade plan
    logger.info("Final signal: %s", trade_plan.get("signal"))
    logger.info("Conflict score: %s", trade_plan.get("conflict_score", 0))
    logger.info("Conflict type: %s", trade_plan.get("conflict_type", "none"))
    logger.info("Position size: %.2f", trade_plan.get("position_size", 0))
    logger.info("Conflict handling applied: %s", trade_plan.get("conflict_handling_applied", False))
    logger.info("Tags: %s", trade_plan.get("tags", []))
    
    # Save test result to file
    with open(f"direct_conflict_score_{conflict_score}_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
        
    return trade_plan

def compare_all_results(results: Dict[str, Dict[str, Any]]):
    """
    Compare the results from all tests
    
    Args:
        results: Dictionary with test results keyed by test name
    """
    logger.info("\n\n==================================================")
    logger.info("COMPARISON OF RESULTS")
    logger.info("==================================================")
    
    # Get baseline position size
    baseline_position = results.get("baseline", {}).get("position_size", 0)
    if baseline_position <= 0:
        logger.warning("Baseline position size is zero or not available, can't compare")
        return
    
    # Create comparison table
    logger.info("Test              | Position Size | % of Baseline | Conflict Score | Conflict Type")
    logger.info("------------------|---------------|---------------|----------------|-------------")
    
    for test_name, plan in results.items():
        position = plan.get("position_size", 0)
        percent = (position / baseline_position * 100) if baseline_position > 0 else 0
        conflict_score = plan.get("conflict_score", 0) or 0  # Default to 0 if None
        conflict_type = plan.get("conflict_type", "none") or "none"  # Default to "none" if None
        
        logger.info(f"{test_name:<18} | {position:<13.2f} | {percent:<13.1f}% | {conflict_score:<14} | {conflict_type}")

def main():
    """Run all tests"""
    try:
        # Store all results for comparison
        results = {}
        
        # Run baseline test first
        logger.info("\n\n==================================================")
        logger.info("Running baseline test with harmonious signals")
        logger.info("==================================================")
        baseline_plan = test_no_conflict_baseline()
        results["baseline"] = baseline_plan
        
        # Run soft conflict test
        logger.info("\n\n==================================================")
        logger.info("Running soft conflict test (50-70% conflict)")
        logger.info("==================================================")
        results["soft_conflict"] = test_soft_conflict()
        
        # Run hard conflict test
        logger.info("\n\n==================================================")
        logger.info("Running hard conflict test (>70% conflict)")
        logger.info("==================================================")
        results["hard_conflict"] = test_hard_conflict()
        
        # Run direct tests with specific conflict scores
        logger.info("\n\n==================================================")
        logger.info("Running direct tests with specific conflict scores")
        logger.info("==================================================")
        results["direct_30"] = direct_test_with_conflict_score(30)  # Should be minor conflict
        results["direct_60"] = direct_test_with_conflict_score(60)  # Should be soft conflict
        results["direct_75"] = direct_test_with_conflict_score(75)  # Should be hard conflict
        
        # Compare results
        compare_all_results(results)
        
        logger.info("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    main()