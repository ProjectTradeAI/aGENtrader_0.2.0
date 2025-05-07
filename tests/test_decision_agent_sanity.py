#!/usr/bin/env python3
"""
Test for Decision Agent with Self-Sanity Checks

This script tests the integration of self-sanity checks in the DecisionAgent.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_analysis(signal, confidence, pass_sanity=True, agent_type="mock"):
    """Create a mock analysis result"""
    return {
        "agent_name": f"{agent_type.capitalize()}AnalystAgent",
        "agent_type": agent_type,
        "timestamp": datetime.now().isoformat(),
        "signal": signal,
        "confidence": confidence,
        "reasoning": f"Mock {signal} signal with {confidence}% confidence",
        "data": {
            "value": 1.0,
            "indicator": "mock_indicator"
        },
        "passed_sanity_check": pass_sanity
    }

def test_decision_agent_with_sanity_checks():
    """Test the DecisionAgent with various sanity check scenarios"""
    try:
        from agents.updated_decision_agent import DecisionAgent
        
        # Create a decision agent
        decision_agent = DecisionAgent()
        
        # Test 1: All analyses pass sanity checks
        logger.info("=== Test 1: All analyses pass sanity checks ===")
        analyses = {
            "technical_analysis": create_mock_analysis("BUY", 80),
            "sentiment_analysis": create_mock_analysis("BUY", 75),
            "liquidity_analysis": create_mock_analysis("NEUTRAL", 60),
            "funding_rate_analysis": create_mock_analysis("NEUTRAL", 50)
        }
        
        decision = decision_agent.make_decision(agent_analyses=analyses, symbol="BTC/USDT", interval="1h")
        
        logger.info(f"Decision: {decision['signal']} with {decision['confidence']}% confidence")
        logger.info(f"Decision passed sanity check: {decision.get('passed_sanity_check', False)}")
        
        # Test 2: Some analyses fail sanity checks
        logger.info("\n=== Test 2: Some analyses fail sanity checks ===")
        analyses = {
            "technical_analysis": create_mock_analysis("BUY", 80),
            "sentiment_analysis": create_mock_analysis("BUY", 75, pass_sanity=False),  # This one fails
            "liquidity_analysis": create_mock_analysis("NEUTRAL", 60),
            "funding_rate_analysis": create_mock_analysis("NEUTRAL", 50, pass_sanity=False)  # This one fails
        }
        
        decision = decision_agent.make_decision(agent_analyses=analyses, symbol="BTC/USDT", interval="1h")
        
        logger.info(f"Decision: {decision['signal']} with {decision['confidence']}% confidence")
        logger.info(f"Decision passed sanity check: {decision.get('passed_sanity_check', False)}")
        
        # Test 3: All analyses fail sanity checks
        logger.info("\n=== Test 3: All analyses fail sanity checks ===")
        analyses = {
            "technical_analysis": create_mock_analysis("BUY", 80, pass_sanity=False),
            "sentiment_analysis": create_mock_analysis("BUY", 75, pass_sanity=False),
            "liquidity_analysis": create_mock_analysis("NEUTRAL", 60, pass_sanity=False),
            "funding_rate_analysis": create_mock_analysis("NEUTRAL", 50, pass_sanity=False)
        }
        
        decision = decision_agent.make_decision(agent_analyses=analyses, symbol="BTC/USDT", interval="1h")
        
        logger.info(f"Decision: {decision['signal']} with {decision['confidence']}% confidence")
        logger.info(f"Decision passed sanity check: {decision.get('passed_sanity_check', False)}")
        logger.info(f"Error type: {decision.get('error_type', 'None')}")
        
        return True
    except ImportError:
        logger.error("Could not import required modules. Make sure updated_decision_agent.py is in the agents directory.")
        return False
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_decision_agent_with_sanity_checks()
    if success:
        logger.info("All tests completed successfully")
    else:
        logger.error("Tests failed")
        sys.exit(1)