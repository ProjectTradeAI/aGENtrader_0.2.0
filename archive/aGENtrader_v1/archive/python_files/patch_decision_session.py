#!/usr/bin/env python3
"""
Patch decision_session.py to apply data integrity measures

This script adds data integrity measures to the decision_session module
by monkey patching its DecisionSession class to apply data integrity
measures during initialization.
"""

import os
import sys
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("patch_decision_session")

def apply_patch():
    """Apply data integrity patch to decision_session module"""
    try:
        # First, import the data integrity module
        from agents.data_integrity import ensure_data_integrity_for_agents
        
        # Then, import the decision_session module
        try:
            # First try from orchestration package
            from orchestration import decision_session
            logger.info("Successfully imported decision_session from orchestration package")
        except ImportError:
            # If not in orchestration, try to import directly
            import decision_session
            logger.info("Successfully imported decision_session directly")
        
        # Check if DecisionSession class exists
        if hasattr(decision_session, "DecisionSession"):
            # Store the original __init__ method
            decision_session_class = decision_session.DecisionSession
            original_init = decision_session_class.__init__
            
            # Define the patched __init__ method
            def patched_init(self, *args, **kwargs):
                # Call the original __init__ method
                original_init(self, *args, **kwargs)
                
                # Apply data integrity measures
                try:
                    logger.info("Applying data integrity measures to DecisionSession instance")
                    ensure_data_integrity_for_agents(self)
                    logger.info("Successfully applied data integrity measures")
                except Exception as e:
                    logger.error(f"Error applying data integrity measures: {str(e)}")
            
            # Apply the monkey patch
            decision_session_class.__init__ = patched_init
            logger.info("Successfully monkey patched DecisionSession.__init__")
            
            return {
                "success": True,
                "class": "DecisionSession",
                "module": decision_session.__name__
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
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    print("Applying Data Integrity Patch to DecisionSession")
    print("==============================================")
    
    result = apply_patch()
    
    if result["success"]:
        print("\n✅ Successfully applied data integrity patch")
        print(f"  Module: {result['module']}")
        print(f"  Class: {result['class']}")
        
        print("\nNow whenever a DecisionSession instance is created, data integrity measures will be applied automatically.")
        print("This ensures analyst agents will clearly state when they don't have access to real data.")
    else:
        print("\n❌ Failed to apply data integrity patch")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\nYou can still manually apply data integrity measures to your trading system:")
        print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Your trading system instance
trading_system = YourTradingSystem()

# Apply data integrity measures
results = ensure_data_integrity_for_agents(trading_system)
""")

if __name__ == "__main__":
    main()