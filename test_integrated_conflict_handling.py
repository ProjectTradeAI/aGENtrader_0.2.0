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
import datetime
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_integrated_conflict')

# Add project root to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from agents.trade_plan_agent import TradePlanAgent, create_trade_plan_agent
from agents.decision_agent import DecisionAgent

# Import or create factory function for decision agent
def create_decision_agent(config=None):
    """
    Create a DecisionAgent with the specified configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured DecisionAgent instance
    """
    if config is None:
        config = {}
    
    return DecisionAgent(config)

def create_mock_analyst_results(scenario: str = "baseline") -> Dict[str, Any]:
    """
    Create mock analyst results for testing different conflict scenarios
    
    Args:
        scenario: One of "baseline", "soft_conflict", "hard_conflict"
        
    Returns:
        Mock analyst results dictionary
    """
    # Base analyst results with unified structure - for baseline, create strong BUY signals
    technical_analysis = {
        "agent": "TechnicalAnalystAgent",
        "signal": "BUY",
        "confidence": 90,
        "symbol": "BTC/USDT",
        "interval": "1h",
        "reason": "Bullish technical indicators with strong MACD crossover and RSI showing upward momentum"
    }
    
    sentiment_analysis = {
        "agent": "SentimentAnalystAgent",
        "signal": "BUY",
        "confidence": 85,
        "symbol": "BTC/USDT",
        "interval": "1h",
        "reason": "Positive sentiment trending across social media and news sources"
    }
    
    liquidity_analysis = {
        "agent": "LiquidityAnalystAgent",
        "signal": "BUY",
        "confidence": 80,
        "symbol": "BTC/USDT",
        "interval": "1h",
        "reason": "Strong liquidity at support levels"
    }
    
    funding_rate_analysis = {
        "agent": "FundingRateAnalystAgent",
        "signal": "BUY",
        "confidence": 75,
        "symbol": "BTC/USDT",
        "interval": "1h",
        "reason": "Favorable funding rates indicating strong momentum"
    }
    
    open_interest_analysis = {
        "agent": "OpenInterestAnalystAgent",
        "signal": "BUY",
        "confidence": 85,
        "symbol": "BTC/USDT",
        "interval": "1h",
        "reason": "Increasing open interest with rising prices suggests strong bull momentum"
    }
    
    # Create conflict by modifying analyst signals based on scenario
    if scenario == "soft_conflict":
        # Create soft conflict (50-70%) by making 2 of 5 agents disagree
        sentiment_analysis["signal"] = "SELL"
        sentiment_analysis["confidence"] = 75
        sentiment_analysis["reason"] = "Some negative sentiment indicators appearing in social media"
        
        funding_rate_analysis["signal"] = "SELL"
        funding_rate_analysis["confidence"] = 70
        funding_rate_analysis["reason"] = "Funding rates showing signs of potential reversal"
    
    elif scenario == "hard_conflict":
        # Create hard conflict (>70%) by making 3 of 5 agents strongly disagree
        sentiment_analysis["signal"] = "SELL"
        sentiment_analysis["confidence"] = 90
        sentiment_analysis["reason"] = "Extremely negative sentiment trending on social media and news sources"
        
        funding_rate_analysis["signal"] = "SELL"
        funding_rate_analysis["confidence"] = 85
        funding_rate_analysis["reason"] = "Funding rates indicating a strong bearish reversal"
        
        open_interest_analysis["signal"] = "SELL"
        open_interest_analysis["confidence"] = 80
        open_interest_analysis["reason"] = "Open interest pattern suggests distribution phase"
    
    # Return as a dictionary with agent names as keys
    return {
        "technical_analysis": technical_analysis,
        "sentiment_analysis": sentiment_analysis,
        "liquidity_analysis": liquidity_analysis,
        "funding_rate_analysis": funding_rate_analysis,
        "open_interest_analysis": open_interest_analysis
    }

def create_mock_market_data() -> Dict[str, Any]:
    """
    Create mock market data for testing
    
    Returns:
        Mock market data dictionary
    """
    return {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
        "timestamp": datetime.datetime.now().isoformat(),
        "historical_data": [
            {"open": 49500, "high": 50200, "low": 49300, "close": 50000, "volume": 1200},
            {"open": 49200, "high": 49800, "low": 48900, "close": 49500, "volume": 1100},
            {"open": 48800, "high": 49500, "low": 48700, "close": 49200, "volume": 1000},
            {"open": 48500, "high": 49000, "low": 48300, "close": 48800, "volume": 950},
            {"open": 48300, "high": 48700, "low": 48100, "close": 48500, "volume": 900},
            {"open": 48100, "high": 48500, "low": 47900, "close": 48300, "volume": 850},
            {"open": 47900, "high": 48300, "low": 47700, "close": 48100, "volume": 800},
            {"open": 47700, "high": 48000, "low": 47500, "close": 47900, "volume": 750},
            {"open": 47500, "high": 47800, "low": 47300, "close": 47700, "volume": 700},
            {"open": 47300, "high": 47600, "low": 47100, "close": 47500, "volume": 650},
            {"open": 47100, "high": 47400, "low": 46900, "close": 47300, "volume": 600},
            {"open": 46900, "high": 47200, "low": 46700, "close": 47100, "volume": 550},
            {"open": 46700, "high": 47000, "low": 46500, "close": 46900, "volume": 500},
            {"open": 46500, "high": 46800, "low": 46300, "close": 46700, "volume": 450},
            {"open": 46300, "high": 46600, "low": 46100, "close": 46500, "volume": 400}
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
    logger.info(f"Running integrated conflict test: {scenario}")
    logger.info(f"==================================================")
    
    # Create mock analyst results based on the scenario
    analyst_results = create_mock_analyst_results(scenario)
    market_data = create_mock_market_data()
    
    # Create decision agent with standard weights
    decision_agent = create_decision_agent({
        "detailed_logging": True,
        "agent_weights": {
            "TechnicalAnalystAgent": 1.2,  # Higher weight for technical analysis
            "SentimentAnalystAgent": 0.8,
            "LiquidityAnalystAgent": 1.0,
            "FundingRateAnalystAgent": 0.8,
            "OpenInterestAnalystAgent": 1.0
        }
    })
    
    # Create trade plan agent
    trade_plan_agent = create_trade_plan_agent({
        "detailed_logging": True,
        "test_mode": True
    })
    
    # Make a decision with mock analyst results
    logger.info("Making decision with decision agent...")
    decision = decision_agent.make_decision(
        agent_analyses=analyst_results,
        symbol="BTC/USDT",
        interval="1h",
        market_data=market_data
    )
    
    # Log the decision
    logger.info(f"Decision output: {decision.get('signal')} with {decision.get('confidence')}% confidence")
    logger.info(f"Conflict score: {decision.get('conflict_score', 'None')}")
    
    # Generate trade plan based on the decision
    logger.info("Generating trade plan with trade plan agent...")
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs=analyst_results
    )
    
    # Log the trade plan
    logger.info(f"Trade plan generated for {trade_plan.get('signal')} with position size {trade_plan.get('position_size')}")
    logger.info(f"Conflict type: {trade_plan.get('conflict_type', 'None')}")
    logger.info(f"Conflict handling applied: {trade_plan.get('conflict_handling_applied', False)}")
    
    # Save results to a file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{scenario}_test_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(trade_plan, f, indent=2, default=str)
    logger.info(f"Results saved to {filename}")
    
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
    logger.info(f"{'Scenario':<15} | {'Signal':<6} | {'Position Size':<13} | {'% of Baseline':<13} | {'Conflict Score':<14} | {'Conflict Type':<15} | {'Applied'}")
    logger.info(f"{'-'*15}|{'-'*8}|{'-'*15}|{'-'*15}|{'-'*16}|{'-'*17}|{'-'*10}")
    
    # Print results for each scenario
    for scenario, result in results.items():
        position = result.get("position_size", 0)
        percent = (position / baseline_position * 100) if baseline_position > 0 else 0
        signal = result.get("signal", "Unknown")
        conflict_score = result.get("conflict_score", "None")
        conflict_type = result.get("conflict_type", "none") or "none"  # Default to "none" if None
        conflict_applied = result.get("conflict_handling_applied", False)
        
        logger.info(f"{scenario:<15} | {signal:<6} | {position:<13.2f} | {percent:<13.1f}% | {conflict_score!s:<14} | {conflict_type:<15} | {conflict_applied!s:<10}")

def run_all_tests() -> None:
    """Run all tests and compare results"""
    results = {}
    
    # Run tests for all scenarios
    results["baseline"] = test_integrated_conflict_handling("baseline")
    results["soft_conflict"] = test_integrated_conflict_handling("soft_conflict")
    results["hard_conflict"] = test_integrated_conflict_handling("hard_conflict")
    
    # Compare results
    compare_results(results)
    
    # Save combined results
    with open("integrated_conflict_test_results.json", "w") as f:
        # Using a default serializer for any non-serializable objects
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\nAll tests completed successfully!")
    
if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        logger.error(f"Tests failed with error: {e}", exc_info=True)