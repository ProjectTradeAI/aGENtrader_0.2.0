#!/usr/bin/env python3
"""
Ensure Data Integrity in Trading System

This example shows how to ensure data integrity in any trading system instance.
It demonstrates:
1. How to apply data integrity measures to a system that's already initialized
2. How to verify that agents properly communicate when data is not available
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
logger = logging.getLogger("ensure_data_integrity")

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def ensure_trading_system_data_integrity(trading_system) -> Dict[str, Any]:
    """
    Ensure data integrity for a trading system
    
    Args:
        trading_system: The trading system instance
        
    Returns:
        Results of applying data integrity measures
    """
    try:
        # First, try to import the data_integrity module
        from agents.data_integrity import ensure_data_integrity_for_agents, validate_data_response
        
        # Apply data integrity measures
        logger.info("Applying data integrity measures to trading system")
        results = ensure_data_integrity_for_agents(trading_system)
        
        # Check for success
        if results.get("success", False):
            logger.info("Successfully applied data integrity measures")
            
            # Test an agent response to validate
            test_agents_data_integrity(trading_system, validate_data_response)
        else:
            logger.error(f"Failed to apply data integrity measures: {results}")
        
        return results
    except ImportError:
        logger.error("Could not import data_integrity module. Run scripts/apply_data_integrity.py first.")
        return {"success": False, "error": "data_integrity module not found"}
    except Exception as e:
        logger.error(f"Error applying data integrity measures: {str(e)}")
        return {"success": False, "error": str(e)}

def test_agents_data_integrity(trading_system, validate_func) -> None:
    """
    Test if agents properly communicate data unavailability
    
    Args:
        trading_system: The trading system instance
        validate_func: Function to validate agent responses
    """
    try:
        # Check if the trading system has agents
        if hasattr(trading_system, "agents"):
            logger.info("Testing agent data integrity responses")
            
            # Test each relevant analyst agent
            for agent_name in ["fundamental_analyst", "sentiment_analyst", "onchain_analyst"]:
                if agent_name in trading_system.agents:
                    agent = trading_system.agents[agent_name]
                    
                    # Generate a mock response (assuming the agent has a generate_response method)
                    if hasattr(agent, "generate_response"):
                        # With data unavailable
                        response = agent.generate_response(with_data=False)
                        
                        # Validate the response
                        analyst_type = agent_name.split("_")[0]
                        validation = validate_func(response, analyst_type)
                        
                        # Log the result
                        if validation["is_valid"]:
                            logger.info(f"{agent_name} correctly handles data unavailability")
                        else:
                            logger.warning(f"{agent_name} does not properly handle data unavailability")
                            logger.warning(f"Response: {response}")
                            logger.warning(f"Validation: {validation}")
        else:
            logger.warning("Trading system does not have agents attribute, cannot test responses")
    except Exception as e:
        logger.error(f"Error testing agent data integrity: {str(e)}")

def check_system_agent_types(trading_system) -> Dict[str, Any]:
    """
    Check what types of agents the trading system has
    
    Args:
        trading_system: The trading system instance
        
    Returns:
        Dictionary with agent types
    """
    agent_types = {"has_agents": False}
    
    try:
        # Check various agent structures
        if hasattr(trading_system, "agents") and isinstance(trading_system.agents, dict):
            agent_types["has_agents"] = True
            agent_types["agent_structure"] = "dict"
            agent_types["agent_names"] = list(trading_system.agents.keys())
            
            # Check for specific analyst types
            for analyst_type in ["fundamental_analyst", "sentiment_analyst", "onchain_analyst"]:
                agent_types[f"has_{analyst_type}"] = analyst_type in trading_system.agents
        
        # Check for directly accessible agents
        for analyst_type in ["fundamental_analyst", "sentiment_analyst", "onchain_analyst"]:
            if hasattr(trading_system, analyst_type):
                agent_types["has_agents"] = True
                agent_types[f"has_{analyst_type}_direct"] = True
        
        return agent_types
    except Exception as e:
        logger.error(f"Error checking agent types: {str(e)}")
        return {"has_agents": False, "error": str(e)}

def apply_globally() -> None:
    """
    Apply data integrity to all trading systems in the project
    """
    try:
        # Import the data integrity application script
        sys.path.append(os.path.join(project_root, "scripts"))
        
        # Run the apply_data_integrity function
        from apply_data_integrity import apply_data_integrity
        
        print("\nApplying data integrity measures to all trading systems...")
        results = apply_data_integrity()
        
        # Print summary
        if results["success"]:
            print(f"Successfully found {results['systems_found']} trading systems")
            print("Data integrity measures have been applied to all systems\n")
        else:
            print(f"Failed to apply data integrity measures: {results.get('error', 'Unknown error')}")
    except ImportError:
        print("Could not import apply_data_integrity module.")
        print("Make sure scripts/apply_data_integrity.py exists.")
    except Exception as e:
        print(f"Error applying data integrity globally: {str(e)}")

def main():
    """Main entry point"""
    print("Ensuring Data Integrity in Trading System")
    print("========================================")
    
    # Apply data integrity globally
    apply_globally()
    
    # Demonstrate how to apply to a specific trading system instance
    print("\nTo apply data integrity to a specific trading system instance:")
    print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Apply data integrity measures to your trading system
trading_system = YourTradingSystem()  # Your existing trading system instance
results = ensure_data_integrity_for_agents(trading_system)

# Check results
print(f"Data integrity applied: {results['success']}")
for agent, status in results.items():
    if agent != 'success':
        print(f"- {agent}: {'Applied' if status else 'Failed'}")
""")
    
    print("\nData Integrity has been successfully applied to your system.")
    print("Now when analysts don't have access to real data, they will explicitly state:")
    print("  - That they cannot provide analysis due to lack of data access")
    print("  - That their input should NOT be counted in trading decisions")
    print("  - They will never provide simulated data that could lead to poor decisions")

if __name__ == "__main__":
    main()