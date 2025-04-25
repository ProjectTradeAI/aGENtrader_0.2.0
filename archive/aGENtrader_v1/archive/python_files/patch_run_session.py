#!/usr/bin/env python3
"""
Patch run_session.py to apply data integrity measures

This script adds data integrity measures to the decision_session module
by monkey patching its DecisionSession._run_agent_session method to apply
data integrity measures to agents when they are created or used.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("patch_run_session")

def apply_patch():
    """Apply data integrity patch to decision_session module"""
    try:
        # First, import the data integrity module
        from agents.data_integrity import ensure_data_integrity_for_agents
        logger.info("Successfully imported data integrity module")
        
        # Then, import the decision_session module
        try:
            from orchestration import decision_session
            logger.info("Successfully imported decision_session module")
        except ImportError:
            logger.error("Error importing decision_session module from orchestration")
            return {
                "success": False,
                "error": "Error importing decision_session module"
            }
        
        # Check if DecisionSession class exists
        if hasattr(decision_session, "DecisionSession"):
            decision_session_class = decision_session.DecisionSession
            
            # Patch the _run_agent_session method
            if hasattr(decision_session_class, "_run_agent_session"):
                logger.info("Found _run_agent_session method, patching it...")
                
                # Store the original method
                original_run_agent_session = decision_session_class._run_agent_session
                
                # Define the patched method
                def patched_run_agent_session(self, session_data):
                    """
                    Patched version of _run_agent_session that applies data integrity measures
                    before running the agent session.
                    """
                    logger.info("Running patched _run_agent_session with data integrity measures")
                    
                    # Create a dictionary to store agents for data integrity
                    session_agents = {}
                    
                    # Extract and process agents from the session data
                    # Note: This is a simplified approach; actual implementation depends on session_data structure
                    if isinstance(session_data, dict):
                        # Look for agents in the session data
                        for key, value in session_data.items():
                            if isinstance(key, str) and "agent" in key.lower() or "analyst" in key.lower():
                                session_agents[key] = value
                    
                    # Apply data integrity measures to the agents
                    if session_agents:
                        logger.info(f"Applying data integrity measures to {len(session_agents)} agents")
                        ensure_data_integrity_for_agents(session_agents)
                    
                    # Run the original method
                    return original_run_agent_session(self, session_data)
                
                # Apply the patch
                decision_session_class._run_agent_session = patched_run_agent_session
                logger.info("Successfully patched _run_agent_session method")
                
                # Also patch run_session as a fallback
                if hasattr(decision_session_class, "run_session"):
                    logger.info("Found run_session method, patching it as a fallback...")
                    
                    # Store the original method
                    original_run_session = decision_session_class.run_session
                    
                    # Define the patched method
                    def patched_run_session(self, *args, **kwargs):
                        """
                        Patched version of run_session that ensures data integrity is
                        maintained in the session.
                        """
                        logger.info("Running patched run_session with data integrity check")
                        
                        # Call the original method
                        result = original_run_session(self, *args, **kwargs)
                        
                        # Check if data integrity was applied (we can't verify this directly)
                        if hasattr(self, "_agent_data_integrity_applied"):
                            logger.info("Data integrity measures were applied by _run_agent_session")
                        else:
                            logger.info("Data integrity measures may not have been applied, applying now")
                            # Try to apply data integrity to any agents the session might have
                            ensure_data_integrity_for_agents(self)
                            self._agent_data_integrity_applied = True
                        
                        return result
                    
                    # Apply the patch
                    decision_session_class.run_session = patched_run_session
                    logger.info("Successfully patched run_session method")
                
                return {
                    "success": True,
                    "patched_methods": ["_run_agent_session", "run_session"]
                }
            elif hasattr(decision_session_class, "run_session"):
                logger.info("Found run_session method, patching it...")
                
                # Store the original method
                original_run_session = decision_session_class.run_session
                
                # Define the patched method
                def patched_run_session(self, *args, **kwargs):
                    """
                    Patched version of run_session that ensures data integrity is
                    maintained in the session.
                    """
                    logger.info("Running patched run_session with data integrity")
                    
                    # Apply data integrity measures before running the session
                    ensure_data_integrity_for_agents(self)
                    self._agent_data_integrity_applied = True
                    
                    # Call the original method
                    return original_run_session(self, *args, **kwargs)
                
                # Apply the patch
                decision_session_class.run_session = patched_run_session
                logger.info("Successfully patched run_session method")
                
                return {
                    "success": True,
                    "patched_methods": ["run_session"]
                }
            else:
                logger.error("Could not find _run_agent_session or run_session methods to patch")
                return {
                    "success": False,
                    "error": "Methods to patch not found"
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
        logger.error(f"Error applying patch: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    print("Applying Data Integrity Patch to Session Methods")
    print("============================================")
    
    result = apply_patch()
    
    if result["success"]:
        print("\n✅ Successfully applied data integrity patch")
        
        # Print details about patched methods
        if "patched_methods" in result:
            print("  Patched methods:")
            for method in result["patched_methods"]:
                print(f"  - {method}")
        
        print("\nData integrity measures will now be automatically applied when:")
        if "_run_agent_session" in result.get("patched_methods", []):
            print("- The DecisionSession runs an agent session")
        if "run_session" in result.get("patched_methods", []):
            print("- The DecisionSession runs a trading session")
        
        print("\nNow when analyst agents don't have access to real data, they will:")
        print("1. Clearly state they cannot provide analysis due to lack of data access")
        print("2. Explicitly recommend their input should NOT be counted in trading decisions")
        print("3. Never provide simulated data that could lead to poor trading decisions")
    else:
        print("\n❌ Failed to apply data integrity patch")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\nYou can still manually apply data integrity measures to your trading system:")
        print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Create your trading system instance
trading_system = YourTradingSystem()

# Apply data integrity measures before running a session
ensure_data_integrity_for_agents(trading_system)
trading_system.run_session(symbol="BTCUSDT")
""")

if __name__ == "__main__":
    main()