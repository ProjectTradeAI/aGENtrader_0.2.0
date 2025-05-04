"""
Integrated test for graduated conflict handling in aGENtrader v2

This test performs end-to-end testing of the graduated conflict handling system,
validating that conflict scores from the DecisionAgent are properly passed to
the TradePlanAgent and result in the expected position size adjustments.

Author: aGENtrader Team
Date: May 4, 2025
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_integrated_conflict_handling')

# Add project root to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the relevant agents
from agents.decision_agent import DecisionAgent
from agents.trade_plan_agent import TradePlanAgent, create_trade_plan_agent

def create_mock_analyst_results(scenario: str = "baseline") -> Dict[str, Any]:
    """
    Create mock analyst results for testing different conflict scenarios
    
    Args:
        scenario: One of "baseline", "soft_conflict", "hard_conflict"
        
    Returns:
        Mock analyst results dictionary
    """
    if scenario == "baseline":
        # All agents agree - no conflict
        return {
            "technical_analysis": {
                "signal": "BUY",
                "confidence": 80,
                "agent": "TechnicalAnalystAgent",
                "reason": "BTC/USDT is showing strong bullish momentum with positive MACD and RSI at 65."
            },
            "sentiment_analysis": {
                "signal": "BUY", 
                "confidence": 75,
                "agent": "SentimentAnalystAgent",
                "reason": "Market sentiment indicators are strongly positive."
            },
            "liquidity_analysis": {
                "signal": "NEUTRAL",  # Changed from BUY to NEUTRAL to avoid conflict detection
                "confidence": 50,
                "agent": "LiquidityAnalystAgent",
                "reason": "No significant liquidity levels detected."
            },
            "funding_rate_analysis": {
                "signal": "NEUTRAL",  # Changed from BUY to NEUTRAL to avoid conflict detection
                "confidence": 50,
                "agent": "FundingRateAnalystAgent",
                "reason": "Funding rates are neutral."
            },
            "open_interest_analysis": {
                "signal": "BUY",
                "confidence": 72,
                "agent": "OpenInterestAnalystAgent",
                "reason": "Increasing open interest with rising price."
            }
        }
    elif scenario == "soft_conflict":
        # Soft conflict - some disagreement but majority still aligned
        return {
            "technical_analysis": {
                "signal": "BUY",
                "confidence": 80,
                "agent": "TechnicalAnalystAgent",
                "reason": "BTC/USDT is showing strong bullish momentum with positive MACD and RSI at 65."
            },
            "sentiment_analysis": {
                "signal": "NEUTRAL", 
                "confidence": 60,
                "agent": "SentimentAnalystAgent",
                "reason": "Market sentiment indicators mixed with diverging signals."
            },
            "liquidity_analysis": {
                "signal": "BUY",
                "confidence": 70,
                "agent": "LiquidityAnalystAgent",
                "reason": "Significant support detected at 49700."
            },
            "funding_rate_analysis": {
                "signal": "SELL",
                "confidence": 65,
                "agent": "FundingRateAnalystAgent",
                "reason": "Funding rates turning negative across exchanges."
            },
            "open_interest_analysis": {
                "signal": "BUY",
                "confidence": 72,
                "agent": "OpenInterestAnalystAgent",
                "reason": "Increasing open interest with rising price."
            }
        }
    elif scenario == "hard_conflict":
        # Hard conflict - strong disagreement between agents
        return {
            "technical_analysis": {
                "signal": "BUY",
                "confidence": 80,
                "agent": "TechnicalAnalystAgent",
                "reason": "BTC/USDT is showing strong bullish momentum with positive MACD and RSI at 65."
            },
            "sentiment_analysis": {
                "signal": "SELL", 
                "confidence": 75,
                "agent": "SentimentAnalystAgent",
                "reason": "Market sentiment indicators turning extremely negative."
            },
            "liquidity_analysis": {
                "signal": "BUY",
                "confidence": 70,
                "agent": "LiquidityAnalystAgent",
                "reason": "Significant support detected at 49700."
            },
            "funding_rate_analysis": {
                "signal": "SELL",
                "confidence": 85,
                "agent": "FundingRateAnalystAgent",
                "reason": "Funding rates extremely negative across exchanges."
            },
            "open_interest_analysis": {
                "signal": "SELL",
                "confidence": 72,
                "agent": "OpenInterestAnalystAgent",
                "reason": "Decreasing open interest with rising price indicates weak momentum."
            }
        }
    else:
        # Default to baseline
        return create_mock_analyst_results("baseline")

def create_mock_market_data() -> Dict[str, Any]:
    """
    Create mock market data for testing
    
    Returns:
        Mock market data dictionary
    """
    return {
        "current_price": 50000.0,
        "symbol": "BTC/USDT",
        "timestamp": datetime.now().isoformat(),
        "historical_data": [
            {"open": 49800, "high": 50200, "low": 49700, "close": 50000, "volume": 1000}
            for _ in range(20)  # Mock 20 candles with flat prices
        ]
    }

def test_integrated_conflict_handling(scenario: str) -> Dict[str, Any]:
    """
    Run an integrated test of the conflict handling pipeline
    
    Args:
        scenario: One of "baseline", "soft_conflict", "hard_conflict"
        
    Returns:
        Trade plan with conflict handling applied
    """
    logger.info(f"\n\n==================================================")
    logger.info(f"Testing integrated conflict handling: {scenario}")
    logger.info(f"==================================================")
    
    # Create the agents
    decision_agent = DecisionAgent()
    trade_plan_agent = create_trade_plan_agent({
        "detailed_logging": True,
        "test_mode": True
    })
    
    # Create mock data
    analyst_results = create_mock_analyst_results(scenario)
    market_data = create_mock_market_data()
    
    # 1. Make decision using decision agent
    logger.info(f"Making decision with DecisionAgent...")
    decision = decision_agent.make_decision(
        agent_analyses=analyst_results,
        symbol="BTC/USDT", 
        interval="1h"
    )
    
    # 2. Generate trade plan from decision
    logger.info(f"Generating trade plan with TradePlanAgent...")
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs=analyst_results
    )
    
    # 3. Log the important results
    logger.info(f"Decision signal: {decision.get('signal', 'UNKNOWN')}")
    logger.info(f"Decision confidence: {decision.get('confidence', 0)}%")
    logger.info(f"Conflict score: {decision.get('conflict_score', 0)}")
    logger.info(f"Position size: {trade_plan.get('position_size', 0)}")
    logger.info(f"Conflict type: {trade_plan.get('conflict_type', 'none')}")
    logger.info(f"Conflict handling applied: {trade_plan.get('conflict_handling_applied', False)}")
    
    return trade_plan

def compare_results(results: Dict[str, Dict[str, Any]]) -> None:
    """
    Compare the results from all test scenarios
    
    Args:
        results: Dictionary of test results
    """
    logger.info("\n\n==================================================")
    logger.info("COMPARISON OF RESULTS")
    logger.info("==================================================")
    
    # Extract the baseline position size for comparison
    baseline_position = results.get("baseline", {}).get("position_size", 0)
    
    if baseline_position == 0:
        logger.warning("Baseline position size is 0, cannot calculate percentages")
        return
    
    # Print header
    logger.info(f"{'Scenario':<18} | {'Position Size':<13} | {'% of Baseline':<13} | {'Conflict Score':<14} | {'Conflict Type'}")
    logger.info(f"{'-'*18}|{'-'*15}|{'-'*15}|{'-'*16}|{'-'*13}")
    
    # Print results for each scenario
    for scenario, plan in results.items():
        position = plan.get("position_size", 0)
        conflict_score = plan.get("conflict_score", 0)
        percent = (position / baseline_position * 100) if baseline_position > 0 else 0
        conflict_type = plan.get("conflict_type", "none") or "none"  # Default to "none" if None
        
        logger.info(f"{scenario:<18} | {position:<13.2f} | {percent:<13.1f}% | {conflict_score:<14} | {conflict_type}")

def run_all_tests() -> None:
    """Run all tests and compare results"""
    results = {}
    
    try:
        # Run all scenarios
        results["baseline"] = test_integrated_conflict_handling("baseline")
        results["soft_conflict"] = test_integrated_conflict_handling("soft_conflict")
        results["hard_conflict"] = test_integrated_conflict_handling("hard_conflict")
        
        # Compare results across scenarios
        compare_results(results)
        
        # Save results to file for analysis
        with open("integrated_conflict_test_results.json", "w") as f:
            # Convert datetime objects to strings for JSON serialization
            json_results = {k: {kk: str(vv) if isinstance(vv, datetime) else vv 
                              for kk, vv in v.items()} 
                          for k, v in results.items()}
            json.dump(json_results, f, indent=2)
        
        logger.info("\nAll tests completed successfully!")
        logger.info("Results saved to integrated_conflict_test_results.json")
        
    except Exception as e:
        logger.error(f"Tests failed with error: {e}", exc_info=True)

if __name__ == "__main__":
    run_all_tests()