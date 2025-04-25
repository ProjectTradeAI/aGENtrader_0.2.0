#!/usr/bin/env python3
"""
Data Integrity Integration Example

This example demonstrates how to integrate data integrity measures into
different trading system initialization scenarios.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("integrate_data_integrity")

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import the data integrity module
try:
    from agents.data_integrity import ensure_data_integrity_for_agents, validate_data_response
    DATA_INTEGRITY_AVAILABLE = True
    logger.info("Successfully imported data integrity module")
except ImportError as e:
    logger.error(f"Could not import data integrity module: {str(e)}")
    DATA_INTEGRITY_AVAILABLE = False


class ExampleAgentAdapter:
    """
    Adapter class for agents that don't implement update_system_message directly
    """
    def __init__(self, agent_impl):
        self.agent_impl = agent_impl
        # Copy the system message from the implementation
        if hasattr(agent_impl, "system_message"):
            self.system_message = agent_impl.system_message
        elif hasattr(agent_impl, "get_system_message"):
            self.system_message = agent_impl.get_system_message()
        else:
            self.system_message = "No system message available"
    
    def update_system_message(self, new_message: str):
        """Update the system message in the implementation"""
        self.system_message = new_message
        
        # Try different ways to update the implementation
        if hasattr(self.agent_impl, "system_message"):
            self.agent_impl.system_message = new_message
        elif hasattr(self.agent_impl, "set_system_message"):
            self.agent_impl.set_system_message(new_message)
        elif hasattr(self.agent_impl, "update_system_message"):
            self.agent_impl.update_system_message(new_message)


class BaseExampleWithIntegration:
    """Base class for integration examples"""
    
    def apply_data_integrity(self) -> Dict[str, Any]:
        """Apply data integrity measures"""
        if not DATA_INTEGRITY_AVAILABLE:
            return {
                "success": False,
                "error": "Data integrity module not available"
            }
        
        return ensure_data_integrity_for_agents(self)


# Example 1: Direct agent dictionary
class SimpleTrading(BaseExampleWithIntegration):
    """
    Simple trading system with a direct agents dictionary
    """
    def __init__(self):
        """Initialize with simple agents"""
        self.agents = {
            "fundamental_analyst": SimpleAgent("Fundamental Analyst", 
                                             "You analyze on-chain metrics and fundamentals."),
            "sentiment_analyst": SimpleAgent("Sentiment Analyst", 
                                           "You analyze social sentiment and market mood."),
            "technical_analyst": SimpleAgent("Technical Analyst", 
                                           "You analyze price charts and indicators.")
        }


# Example 2: Different agent structure
class AlternativeTrading(BaseExampleWithIntegration):
    """
    Alternative trading system with a different agent structure
    """
    def __init__(self):
        """Initialize with direct agent properties"""
        self.fundamental_analyst = SimpleAgent("Fundamental Analyst", 
                                             "You analyze on-chain metrics and fundamentals.")
        self.sentiment_analyst = SimpleAgent("Sentiment Analyst", 
                                           "You analyze social sentiment and market mood.")
        self.technical_analyst = SimpleAgent("Technical Analyst", 
                                           "You analyze price charts and indicators.")


# Example 3: Custom agent implementation that needs an adapter
class CustomAgent:
    """
    Custom agent implementation with a different interface
    """
    def __init__(self, name: str, instructions: str):
        """Initialize the custom agent"""
        self.name = name
        self._system_message = instructions
    
    def get_system_message(self) -> str:
        """Get the system message"""
        return self._system_message
    
    def get_response(self, with_data: bool = True) -> str:
        """Get a response from the agent"""
        if not with_data and "DATA INTEGRITY INSTRUCTIONS" in self._system_message:
            return f"I cannot provide {self.name.lower()} analysis at this time due to lack of access to data sources."
        else:
            return f"{self.name} provides analysis based on market data."


class CustomTrading(BaseExampleWithIntegration):
    """
    Custom trading system with agents that need adapters
    """
    def __init__(self):
        """Initialize with custom agents that need adapters"""
        self.agents = {
            "fundamental_analyst": ExampleAgentAdapter(CustomAgent("Fundamental Analyst", 
                                                             "You analyze on-chain metrics and fundamentals.")),
            "sentiment_analyst": ExampleAgentAdapter(CustomAgent("Sentiment Analyst", 
                                                           "You analyze social sentiment and market mood.")),
            "technical_analyst": ExampleAgentAdapter(CustomAgent("Technical Analyst", 
                                                           "You analyze price charts and indicators."))
        }


# Example 4: MonkeyPatch initialization
class MonkeyPatchableTrading:
    """
    Trading system that requires monkey patching
    """
    def __init__(self):
        """Initialize the trading system"""
        self.agents = {}
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up the agents - this will be monkey patched"""
        self.agents = {
            "fundamental_analyst": SimpleAgent("Fundamental Analyst", 
                                             "You analyze on-chain metrics and fundamentals."),
            "sentiment_analyst": SimpleAgent("Sentiment Analyst", 
                                           "You analyze social sentiment and market mood."),
            "technical_analyst": SimpleAgent("Technical Analyst", 
                                           "You analyze price charts and indicators.")
        }


# Simple agent implementation
class SimpleAgent:
    """
    Simple agent implementation
    """
    def __init__(self, name: str, system_message: str):
        """Initialize the simple agent"""
        self.name = name
        self.system_message = system_message
    
    def update_system_message(self, new_message: str):
        """Update the system message"""
        self.system_message = new_message
    
    def generate_response(self, with_data: bool = True) -> str:
        """Generate a response from the agent"""
        if not with_data and "DATA INTEGRITY INSTRUCTIONS" in self.system_message:
            if "Fundamental" in self.name:
                return "I cannot provide fundamental analysis at this time due to lack of access to on-chain data sources. My input should NOT be counted in trading decisions."
            elif "Sentiment" in self.name:
                return "I cannot provide sentiment analysis at this time due to lack of access to sentiment data sources. My input should NOT be counted in trading decisions."
            else:
                return f"I cannot provide {self.name.lower()} analysis at this time due to lack of access to data sources."
        else:
            return f"{self.name} provides analysis based on market data."


def demonstrate_initialization_integration():
    """
    Demonstrate integrating data integrity during initialization
    """
    print("\nIntegrating Data Integrity During Initialization")
    print("==============================================")
    
    # Example with monkey patching initialization
    print("\nExample: Monkey Patching Initialization")
    
    # Store the original setup method
    original_setup = MonkeyPatchableTrading._setup_agents
    
    # Define the patched setup method
    def patched_setup(self):
        """Patched setup method that applies data integrity"""
        # Call the original setup method
        original_setup(self)
        
        # Apply data integrity measures
        if DATA_INTEGRITY_AVAILABLE:
            ensure_data_integrity_for_agents(self)
    
    # Apply the monkey patch
    MonkeyPatchableTrading._setup_agents = patched_setup
    
    # Create an instance (which will use the patched method)
    trading_system = MonkeyPatchableTrading()
    
    # Verify the patch worked
    for agent_name, agent in trading_system.agents.items():
        if "DATA INTEGRITY INSTRUCTIONS" in agent.system_message:
            print(f"✅ {agent.name} has data integrity instructions")
        else:
            print(f"❌ {agent.name} does not have data integrity instructions")


def demonstrate_existing_system_integration():
    """
    Demonstrate integrating data integrity with existing systems
    """
    print("\nIntegrating Data Integrity with Existing Systems")
    print("==============================================")
    
    # Test different trading system implementations
    systems = [
        ("Simple Trading System", SimpleTrading()),
        ("Alternative Trading System", AlternativeTrading()),
        ("Custom Trading System", CustomTrading())
    ]
    
    for name, system in systems:
        print(f"\n{name}:")
        
        if not DATA_INTEGRITY_AVAILABLE:
            print("❌ Data integrity module not available")
            continue
        
        # Apply data integrity measures
        results = system.apply_data_integrity()
        
        # Print results
        if results.get("success", False):
            print("✅ Successfully applied data integrity measures")
            
            # Check each agent
            for agent_type, status in results.items():
                if agent_type != "success":
                    print(f"  - {agent_type}: {'Applied' if status is True else status}")
            
            # Test agent responses
            print("\nAgent responses with no data access:")
            
            # Simple Trading System
            if isinstance(system, SimpleTrading):
                for agent_name, agent in system.agents.items():
                    if agent_name in ["fundamental_analyst", "sentiment_analyst"]:
                        response = agent.generate_response(with_data=False)
                        print(f"\n{agent.name}:")
                        print(f'"{response}"')
                        
                        # Validate the response
                        analyst_type = agent_name.split("_")[0]
                        validation = validate_data_response(response, analyst_type)
                        if validation["is_valid"]:
                            print("✅ Response correctly discloses data unavailability")
                        else:
                            print("❌ Response does not properly disclose data unavailability")
            
            # Alternative Trading System
            elif isinstance(system, AlternativeTrading):
                for agent_name in ["fundamental_analyst", "sentiment_analyst"]:
                    if hasattr(system, agent_name):
                        agent = getattr(system, agent_name)
                        response = agent.generate_response(with_data=False)
                        print(f"\n{agent.name}:")
                        print(f'"{response}"')
                        
                        # Validate the response
                        analyst_type = agent_name.split("_")[0]
                        validation = validate_data_response(response, analyst_type)
                        if validation["is_valid"]:
                            print("✅ Response correctly discloses data unavailability")
                        else:
                            print("❌ Response does not properly disclose data unavailability")
        else:
            print("❌ Failed to apply data integrity measures")
            if "error" in results:
                print(f"  Error: {results['error']}")


def main():
    """Main entry point"""
    print("Data Integrity Integration Examples")
    print("==================================")
    
    if not DATA_INTEGRITY_AVAILABLE:
        print("\nERROR: Data integrity module is not available")
        print("Make sure agents/data_integrity.py exists and is properly implemented")
        return
    
    # Demonstrate initialization integration
    demonstrate_initialization_integration()
    
    # Demonstrate existing system integration
    demonstrate_existing_system_integration()
    
    print("\nConclusion")
    print("==========")
    print("These examples demonstrate different ways to integrate data integrity into your trading system:")
    print("1. Directly applying ensure_data_integrity_for_agents() to existing systems")
    print("2. Using monkey patching to integrate during initialization")
    print("3. Using adapters for custom agent implementations")
    print("\nUse the approach that best fits your trading system architecture.")


if __name__ == "__main__":
    main()