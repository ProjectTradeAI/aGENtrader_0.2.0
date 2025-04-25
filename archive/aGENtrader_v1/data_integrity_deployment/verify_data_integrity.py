#!/usr/bin/env python3
"""
Verify Data Integrity Implementation

This script creates a test DecisionSession instance and manually applies
data integrity measures to verify they work properly.
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
logger = logging.getLogger("verify_data_integrity")

def verify_implementation():
    """Verify data integrity implementation works properly"""
    try:
        # First, import the data integrity module
        from agents.data_integrity import ensure_data_integrity_for_agents, validate_data_response
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
        
        # Check if DecisionSession exists
        if hasattr(decision_session, "DecisionSession"):
            # Create a DecisionSession instance
            logger.info("Creating DecisionSession instance...")
            session = decision_session.DecisionSession()
            logger.info("Successfully created DecisionSession instance")
            
            # Manually apply data integrity measures
            logger.info("Manually applying data integrity measures...")
            results = ensure_data_integrity_for_agents(session)
            
            logger.info(f"Data integrity application results: {json.dumps(results)}")
            
            # Check if measures were applied successfully
            if results.get("success", False):
                return {
                    "success": True,
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "error": "Data integrity measures were not applied successfully",
                    "results": results
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
        logger.error(f"Error verifying implementation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    print("Verifying Data Integrity Implementation")
    print("=====================================")
    
    # Verify implementation
    result = verify_implementation()
    
    if result["success"]:
        print("\n✅ Data integrity measures have been successfully applied")
        
        # Print details about the measures applied
        if "results" in result:
            for agent_type, status in result["results"].items():
                if agent_type != "success":
                    agent_status = "✅ Applied" if status is True else status
                    print(f"  - {agent_type}: {agent_status}")
        
        print("\nNow when analyst agents don't have access to real data, they will:")
        print("1. Clearly state they cannot provide analysis due to lack of data access")
        print("2. Explicitly recommend their input should NOT be counted in trading decisions")
        print("3. Never provide simulated data that could lead to poor trading decisions")
    else:
        print("\n❌ Failed to verify data integrity implementation")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        if "results" in result:
            print("\n  Details:")
            for agent_type, status in result["results"].items():
                print(f"  - {agent_type}: {status}")

    print("\nYou can use these measures in your existing code with:")
    print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Apply to any trading system instance
trading_system = YourTradingSystem()
ensure_data_integrity_for_agents(trading_system)
""")

if __name__ == "__main__":
    main()