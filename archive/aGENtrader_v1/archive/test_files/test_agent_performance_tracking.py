#!/usr/bin/env python
"""
Agent Performance Tracking Test

Tests the integration of decision tracking and agent prompt optimization.
"""

import os
import sys
import json
import logging
from datetime import datetime

from utils.decision_tracker import DecisionTracker
from utils.agent_prompt_optimizer import AgentPromptOptimizer
from orchestration.decision_session import DecisionSession

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("performance_tracking_test")

def test_decision_tracking():
    """Test the decision tracking functionality"""
    print("\n" + "=" * 80)
    print(" TESTING DECISION TRACKING ".center(80, "="))
    print("=" * 80)
    
    # Create performance directory
    os.makedirs("data/performance", exist_ok=True)
    
    # Initialize decision tracker
    tracker = DecisionTracker()
    print("\nInitialized DecisionTracker")
    
    # Create a sample decision
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    decision = {
        "symbol": "BTCUSDT",
        "action": "BUY",
        "confidence": 75.0,
        "price": 88000.0,
        "risk_level": "medium",
        "reasoning": "Test decision reasoning for BUY recommendation.",
        "timestamp": datetime.now().isoformat(),
        "is_simulated": True
    }
    
    session_data = {
        "session_id": session_id,
        "symbol": "BTCUSDT",
        "current_price": 88000.0,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "decision": decision,
        "market_data": {
            "market_summary": {
                "market_condition": "trending_up"
            }
        }
    }
    
    # Track the decision
    decision_id = tracker.track_session_decision(session_data)
    
    if decision_id:
        print(f"Successfully tracked decision with ID: {decision_id}")
        
        # Track an outcome (simulated)
        outcome_id = tracker.track_decision_outcome(
            decision_id,
            "price_change",
            3.5,
            {"final_price": 91080.0, "target_hit": True}
        )
        
        if outcome_id:
            print(f"Successfully tracked outcome with ID: {outcome_id}")
        else:
            print("Failed to track outcome")
    else:
        print("Failed to track decision")
    
    return decision_id is not None

def test_agent_prompt_optimizer():
    """Test the agent prompt optimizer functionality"""
    print("\n" + "=" * 80)
    print(" TESTING AGENT PROMPT OPTIMIZER ".center(80, "="))
    print("=" * 80)
    
    # Create config directories
    os.makedirs("config/backups", exist_ok=True)
    
    # Create a sample agent configuration if it doesn't exist
    config_path = "config/agent_config.json"
    if not os.path.exists(config_path):
        sample_config = {
            "agents": {
                "MarketAnalyst": {
                    "name": "MarketAnalyst",
                    "description": "Cryptocurrency market analyst specializing in technical analysis",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.2,
                    "system_message": "You are a cryptocurrency market analyst specializing in technical analysis. Provide insights on market conditions, patterns, and indicators."
                },
                "RiskManager": {
                    "name": "RiskManager",
                    "description": "Risk management specialist focusing on portfolio protection",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.3,
                    "system_message": "You are a risk management specialist. Analyze market risks and recommend appropriate position sizing and risk mitigation strategies."
                }
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Created sample agent configuration at {config_path}")
    
    # Initialize prompt optimizer
    optimizer = AgentPromptOptimizer()
    print("\nInitialized AgentPromptOptimizer")
    
    # Get current prompts
    analyst_prompt = optimizer.get_agent_prompt("MarketAnalyst")
    if analyst_prompt:
        print(f"\nCurrent MarketAnalyst prompt: \n{analyst_prompt[:100]}...")
    else:
        print("Failed to get MarketAnalyst prompt")
    
    # Analyze a prompt
    if analyst_prompt:
        analysis = optimizer.analyze_prompt_patterns(analyst_prompt)
        print("\nPrompt analysis:")
        print(f"  Word count: {analysis.get('word_count', 0)}")
        print(f"  Sentence count: {analysis.get('sentence_count', 0)}")
        print(f"  Specificity score: {analysis.get('specificity_score', 0)}/10")
        print(f"  Clarity score: {analysis.get('clarity_score', 0)}/10")
        print(f"  Instructions: {analysis.get('instruction_count', 0)}")
        
        if analysis.get('vague_terms'):
            print(f"  Vague terms: {', '.join(analysis.get('vague_terms', []))}")
        
        if analysis.get('ambiguity_issues'):
            print(f"  Ambiguity issues: {len(analysis.get('ambiguity_issues', []))}")
    
    return analyst_prompt is not None

def test_decision_session_with_tracking():
    """Test decision session with performance tracking enabled"""
    print("\n" + "=" * 80)
    print(" TESTING DECISION SESSION WITH TRACKING ".center(80, "="))
    print("=" * 80)
    
    try:
        # Initialize a decision session with tracking
        session = DecisionSession(
            symbol="BTCUSDT",
            track_performance=True
        )
        
        print(f"\nInitialized DecisionSession with ID: {session.session_id}")
        print(f"Performance tracking enabled: {session.track_performance}")
        print(f"Decision tracker initialized: {session.decision_tracker is not None}")
        
        # We don't actually need to run a full session for this test
        # Just verify that the session has a decision tracker
        return session.decision_tracker is not None
        
    except Exception as e:
        print(f"Error in decision session test: {str(e)}")
        return False

def main():
    """Run all tests"""
    tests_passed = 0
    tests_total = 3
    
    print("\n" + "=" * 80)
    print(" AGENT PERFORMANCE TRACKING TEST SUITE ".center(80, "="))
    print("=" * 80 + "\n")
    
    print("Starting tests...")
    
    try:
        # Test decision tracking
        if test_decision_tracking():
            tests_passed += 1
        
        # Test agent prompt optimizer
        if test_agent_prompt_optimizer():
            tests_passed += 1
        
        # Test decision session with tracking
        if test_decision_session_with_tracking():
            tests_passed += 1
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Error in tests: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
    
    # Print results
    print("\n" + "=" * 80)
    print(" TEST RESULTS ".center(80, "="))
    print("=" * 80)
    
    print(f"\nTests passed: {tests_passed}/{tests_total} ({tests_passed/tests_total*100:.1f}%)")
    
    if tests_passed == tests_total:
        print("\nAll tests PASSED!")
        return 0
    else:
        print("\nSome tests FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())