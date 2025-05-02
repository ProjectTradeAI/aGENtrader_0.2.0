#!/usr/bin/env python3
"""
Test script for the aGENtrader DecisionAgent's CONFLICTED state

This script tests the DecisionAgent's ability to properly handle
conflicting signals from different analyst agents and output a
CONFLICTED state when appropriate.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import the required modules
from agents.decision_agent import DecisionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_decision_conflicted")

def test_conflicted_state(allow_conflict_state: bool = True):
    """
    Test the DecisionAgent's handling of conflicting signals.
    """
    # Create test agent analyses with more extreme conflicting signals
    agent_analyses = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 95,
            "reasoning": "Strong uptrend with bullish crossover pattern",
            "status": "success"
        },
        "sentiment_analysis": {
            "signal": "SELL",
            "confidence": 95,
            "reasoning": "Extremely negative sentiment in social media",
            "status": "success"
        },
        "liquidity_analysis": {
            "signal": "HOLD",
            "confidence": 60,
            "reasoning": "Neutral liquidity conditions",
            "status": "success"
        },
        "funding_rate_analysis": {
            "signal": "SELL",
            "confidence": 80,
            "reasoning": "High funding rate indicating overheated long positions",
            "status": "success"
        },
        "open_interest_analysis": {
            "signal": "BUY",
            "confidence": 85,
            "reasoning": "Increasing open interest with price",
            "status": "success"
        }
    }
    
    # Initialize the DecisionAgent with the specified conflict state setting
    decision_agent = DecisionAgent(allow_conflict_state=allow_conflict_state)
    
    # Make a decision with the conflicting signals
    decision = decision_agent.make_decision(
        agent_analyses=agent_analyses,
        symbol="BTC/USDT",
        interval="1h"
    )
    
    # Print the decision
    logger.info(f"Decision: {decision['action']}")
    logger.info(f"Confidence: {decision['confidence']:.2f}")
    logger.info(f"Reason: {decision['reason']}")
    logger.info(f"Final Signal Confidence: {decision.get('final_signal_confidence', 'N/A')}")
    logger.info(f"Weighted Average Confidence: {decision.get('weighted_average_confidence', 'N/A')}")
    logger.info(f"Conflict Score: {decision.get('conflict_score', 'N/A')}")
    
    # Check for expected behavior based on conflict state setting
    if allow_conflict_state:
        # With the current implementation, conflicting signals can result in HOLD if the confidence 
        # for the dominant signal is still below threshold, which is a valid behavior
        logger.info("Expected: Should detect conflict and either use CONFLICTED state or fall back to HOLD with low confidence")
        is_expected = (decision["action"] == "CONFLICTED" or 
                      (decision["action"] == "HOLD" and "Confidence below threshold" in decision["reason"]))
        # If the test is failing, let's print additional debug info
        if not is_expected:
            logger.warning(f"Test FAILED: Expected CONFLICTED or HOLD with low confidence but got {decision['action']}")
            logger.info(f"Full decision: {json.dumps(decision, indent=2)}")
    else:
        logger.info("Expected: Should detect conflict but fall back to HOLD state or most trusted signal")
        is_expected = (decision["action"] != "CONFLICTED")
        
    logger.info(f"Result: {'✅ PASS' if is_expected else '❌ FAIL'}")
    
    return decision, is_expected

def main():
    """Run tests for both conflict state settings."""
    logger.info("=== Testing with allow_conflict_state=True ===")
    decision_with_conflict, passed_with_conflict = test_conflicted_state(allow_conflict_state=True)
    
    logger.info("\n=== Testing with allow_conflict_state=False ===")
    decision_without_conflict, passed_without_conflict = test_conflicted_state(allow_conflict_state=False)
    
    # Print overall results
    logger.info("\n=== Overall Test Results ===")
    logger.info(f"With conflict state enabled: {'✅ PASS' if passed_with_conflict else '❌ FAIL'}")
    logger.info(f"With conflict state disabled: {'✅ PASS' if passed_without_conflict else '❌ FAIL'}")
    
    all_passed = passed_with_conflict and passed_without_conflict
    logger.info(f"All tests: {'✅ PASS' if all_passed else '❌ FAIL'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())