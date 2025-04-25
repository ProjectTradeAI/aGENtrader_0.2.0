#!/usr/bin/env python3
"""
Demonstrate Data Integrity Implementation

This script demonstrates how the data integrity implementation works by
simulating agent communications and showing the validation in action.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("demonstrate_data_integrity")

class MockAnalyst:
    """Mock analyst agent for demonstration purposes"""
    
    def __init__(self, agent_type, system_message=""):
        self.agent_type = agent_type
        self.system_message = system_message
        self.name = f"{agent_type.replace('_', ' ').title()}"
    
    def set_system_message(self, system_message):
        """Set the system message for the agent"""
        self.system_message = system_message
        logger.info(f"Set system message for {self.name}")
    
    def respond(self, has_data_access=True):
        """Generate a response from the agent"""
        if has_data_access:
            if self.agent_type == "fundamental_analyst":
                return (
                    "Based on my analysis of the latest quarterly reports and earnings data, "
                    "Bitcoin's correlation with tech stocks has strengthened. Major firms holding "
                    "BTC as a reserve asset have reported increased values in their digital asset "
                    "holdings. The macroeconomic landscape of rising inflation and interest rates "
                    "is creating a favorable environment for Bitcoin's growth as a hedge."
                )
            elif self.agent_type == "sentiment_analyst":
                return (
                    "Social sentiment metrics show increasing positive momentum for Bitcoin over "
                    "the past 48 hours. Twitter activity has increased 23% with predominantly bullish "
                    "sentiment. The Fear & Greed Index is currently at 72, indicating 'Greed', up from "
                    "65 last week. Futures market positioning suggests institutional investors are "
                    "taking increasingly long positions."
                )
            elif self.agent_type == "onchain_analyst":
                return (
                    "On-chain metrics indicate strong accumulation patterns over the past two weeks. "
                    "Whale wallets (holding >1000 BTC) have increased their positions by 2.3%. "
                    "Network hashrate has increased 5% week-over-week, suggesting growing mining confidence. "
                    "Exchange outflows have exceeded inflows for 12 consecutive days, indicating "
                    "a preference for long-term holding rather than selling pressure."
                )
        else:
            if self.agent_type == "fundamental_analyst":
                return (
                    "I cannot provide fundamental analysis at this time due to lack of access to financial data sources. "
                    "My input should NOT be counted in trading decisions. To enable proper analysis, the system needs "
                    "access to real financial data through the appropriate API or data provider."
                )
            elif self.agent_type == "sentiment_analyst":
                return (
                    "I cannot provide sentiment analysis at this time due to lack of access to sentiment data sources. "
                    "My input should NOT be counted in trading decisions. Please ensure the system has proper "
                    "access to social media APIs and sentiment analysis services."
                )
            elif self.agent_type == "onchain_analyst":
                return (
                    "Unable to provide on-chain analysis at this time due to lack of access to blockchain data. "
                    "My input should NOT be counted in making trading decisions. Please provide access to "
                    "blockchain explorers or on-chain data providers to enable analysis."
                )
        
        return "No response generated"

def demonstrate_data_integrity():
    """Demonstrate data integrity implementation"""
    try:
        # Import data integrity functions
        from agents.data_integrity import (
            ensure_data_integrity_for_agents,
            validate_data_response
        )
        logger.info("Successfully imported data integrity functions")
        
        # Create mock trading system with analysts
        trading_system = {
            "fundamental_analyst": MockAnalyst("fundamental_analyst"),
            "sentiment_analyst": MockAnalyst("sentiment_analyst"),
            "onchain_analyst": MockAnalyst("onchain_analyst")
        }
        logger.info("Created mock trading system with analyst agents")
        
        # Apply data integrity measures
        result = ensure_data_integrity_for_agents(trading_system)
        logger.info(f"Applied data integrity measures: {json.dumps(result)}")
        
        # Simulate running with and without data access
        scenarios = [
            {"has_data_access": True, "name": "With Data Access"},
            {"has_data_access": False, "name": "Without Data Access"}
        ]
        
        validation_results = {}
        
        for scenario in scenarios:
            has_data_access = scenario["has_data_access"]
            scenario_name = scenario["name"]
            logger.info(f"Running scenario: {scenario_name}")
            
            validation_results[scenario_name] = {}
            
            print(f"\n{'=' * 60}")
            print(f"Scenario: {scenario_name}")
            print(f"{'=' * 60}")
            
            # Generate responses from each agent
            for agent_type, agent in trading_system.items():
                response = agent.respond(has_data_access)
                print(f"\n{agent.name} Response:")
                print("-" * 40)
                print(response)
                
                # Validate the response
                validation_result = validate_data_response(response, agent_type)
                is_valid = validation_result.get("is_valid", False)
                
                validation_results[scenario_name][agent_type] = is_valid
                
                validity_str = "✅ VALID" if is_valid else "❌ INVALID"
                if has_data_access and is_valid:
                    explanation = "Agent properly provided analysis with available data"
                elif not has_data_access and is_valid:
                    explanation = "Agent properly disclosed lack of data access"
                elif has_data_access and not is_valid:
                    explanation = "Agent should provide analysis but didn't format it properly"
                else:  # not has_data_access and not is_valid
                    explanation = "Agent failed to properly disclose lack of data access"
                
                print(f"\nValidation: {validity_str}")
                print(f"Explanation: {explanation}")
        
        # Show summary of validation results
        print("\n" + "=" * 60)
        print("Data Integrity Validation Summary")
        print("=" * 60)
        
        for scenario_name, results in validation_results.items():
            print(f"\n{scenario_name}:")
            for agent_type, is_valid in results.items():
                status = "✅ VALID" if is_valid else "❌ INVALID"
                print(f"  - {agent_type.replace('_', ' ').title()}: {status}")
        
        return {
            "success": True,
            "validation_results": validation_results
        }
    except ImportError as e:
        logger.error(f"Error importing data integrity functions: {str(e)}")
        print(f"\n❌ Could not import data integrity functions: {str(e)}")
        print("Make sure the agents/data_integrity.py module is properly implemented.")
        return {
            "success": False,
            "error": f"Import error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error demonstrating data integrity: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ Error demonstrating data integrity: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    print("Demonstrating Data Integrity Implementation")
    print("=======================================")
    print("\nThis script demonstrates how the data integrity measures work by simulating")
    print("agent communications with and without data access.")
    
    # Demonstrate data integrity
    result = demonstrate_data_integrity()
    
    if result["success"]:
        print("\n✅ Data integrity demonstration completed successfully")
        
        print("\nData integrity ensures that:")
        print("1. Agents properly disclose when they don't have access to real data")
        print("2. Agents explicitly state their input should NOT be counted when data is unavailable")
        print("3. Validation functions correctly identify proper and improper disclosures")
        
        print("\nThese measures are now integrated into your trading system via:")
        print("1. patch_decision_session.py - Patches DecisionSession.__init__")
        print("2. patch_run_session.py - Patches DecisionSession._run_agent_session and run_session")
    else:
        print("\n❌ Data integrity demonstration failed")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\nTo resolve this issue:")
        print("1. Ensure agents/data_integrity.py is properly implemented")
        print("2. Check that the validation functions are correctly defined")
        print("3. Verify the system can import the data integrity module")

if __name__ == "__main__":
    main()