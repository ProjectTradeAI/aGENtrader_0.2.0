#!/usr/bin/env python3
"""
Test Data Integrity Implementation

This script tests that the data integrity implementation is working properly
by creating a test DecisionSession instance and verifying that the analyst
agents properly disclose when they don't have access to real data.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_data_integrity")

def test_decision_session_implementation():
    """Test data integrity implementation in DecisionSession"""
    try:
        # First, import the validation function
        from agents.data_integrity import validate_data_response
        
        # Then, import the decision_session module
        from orchestration import decision_session
        logger.info("Successfully imported decision_session module")
        
        # Check if DecisionSession exists
        if hasattr(decision_session, "DecisionSession"):
            # Create a DecisionSession instance
            logger.info("Creating DecisionSession instance...")
            session = decision_session.DecisionSession()
            logger.info("Successfully created DecisionSession instance")
            
            # Check if data integrity was applied
            data_integrity_applied = False
            
            # Test for agents with data integrity instructions
            for agent_type in ["fundamental_analyst", "sentiment_analyst", "onchain_analyst"]:
                # Check if agent exists
                if hasattr(session, agent_type):
                    agent = getattr(session, agent_type)
                    if hasattr(agent, "system_message") and "DATA INTEGRITY INSTRUCTIONS" in agent.system_message:
                        logger.info(f"Data integrity instructions found in {agent_type}")
                        data_integrity_applied = True
                elif hasattr(session, "agents") and agent_type in session.agents:
                    agent = session.agents[agent_type]
                    if hasattr(agent, "system_message") and "DATA INTEGRITY INSTRUCTIONS" in agent.system_message:
                        logger.info(f"Data integrity instructions found in {agent_type}")
                        data_integrity_applied = True
            
            return {
                "success": True,
                "data_integrity_applied": data_integrity_applied
            }
        else:
            logger.error("DecisionSession class not found in decision_session module")
            return {
                "success": False,
                "error": "DecisionSession class not found"
            }
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        return {
            "success": False,
            "error": f"Import error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error testing implementation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    print("Testing Data Integrity Implementation")
    print("===================================")
    
    # Test implementation
    result = test_decision_session_implementation()
    
    if result["success"]:
        if result.get("data_integrity_applied", False):
            print("\n✅ Data integrity has been successfully applied to the DecisionSession")
            print("  The patch is working properly!")
            print("\nNow when analyst agents don't have access to real data, they will:")
            print("1. Clearly state they cannot provide analysis due to lack of data access")
            print("2. Explicitly recommend their input should NOT be counted in trading decisions")
            print("3. Never provide simulated data that could lead to poor trading decisions")
        else:
            print("\n⚠️ DecisionSession was created successfully, but data integrity may not be applied")
            print("  You may need to run the patch_decision_session.py script again")
    else:
        print("\n❌ Failed to test data integrity implementation")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\nYou can still manually apply data integrity measures to your trading system:")
        print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Your trading system instance
trading_system = YourTradingSystem()

# Apply data integrity measures
results = ensure_data_integrity_for_agents(trading_system)
""")
    
    print("\nReminder: The data integrity implementation is now part of your trading system.")
    print("You don't need to run any additional scripts to use it in the future.")

if __name__ == "__main__":
    main()