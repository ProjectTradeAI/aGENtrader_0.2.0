"""
Data Integrity Module for Analyst Agents

This module provides functions to modify analyst agents to ensure data integrity.
When data is not available, agents will explicitly state that they cannot provide
analysis due to data unavailability rather than using simulated data.
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
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def modify_fundamental_analyst_prompt(agent) -> bool:
    """
    Modify the Fundamental Analyst's prompt to ensure data integrity
    
    Args:
        agent: The fundamental analyst agent to modify
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the current system message
        current_message = agent.system_message
        
        # Add the data integrity instructions
        data_integrity_message = """
IMPORTANT DATA INTEGRITY INSTRUCTIONS:
1. NEVER use simulated, synthetic, or made-up data in your analysis
2. When you do not have access to real on-chain data, you MUST state clearly:
   "I cannot provide fundamental analysis at this time due to lack of access to on-chain data sources."
3. When data access is unavailable, explicitly recommend that your input should NOT be counted in trading decisions
4. Do not attempt to analyze the market without verifiable data from trusted sources
5. If a data source is returning errors or is unavailable, clearly communicate this limitation
6. Better to provide no analysis than potentially misleading analysis based on simulated data
"""
        
        # Check if these instructions already exist in the message
        if "DATA INTEGRITY INSTRUCTIONS" not in current_message:
            new_message = current_message + data_integrity_message
            agent.update_system_message(new_message)
            logger.info("Modified Fundamental Analyst prompt with data integrity instructions")
        else:
            logger.info("Fundamental Analyst already has data integrity instructions")
        
        return True
    except Exception as e:
        logger.error(f"Error modifying Fundamental Analyst prompt: {str(e)}")
        return False

def modify_sentiment_analyst_prompt(agent) -> bool:
    """
    Modify the Sentiment Analyst's prompt to ensure data integrity
    
    Args:
        agent: The sentiment analyst agent to modify
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the current system message
        current_message = agent.system_message
        
        # Add the data integrity instructions
        data_integrity_message = """
IMPORTANT DATA INTEGRITY INSTRUCTIONS:
1. NEVER use simulated, synthetic, or made-up sentiment data in your analysis
2. When you do not have access to real sentiment data sources, you MUST state clearly:
   "I cannot provide sentiment analysis at this time due to lack of access to sentiment data sources."
3. When data access is unavailable, explicitly recommend that your input should NOT be counted in trading decisions
4. Do not attempt to analyze market sentiment without verifiable data from trusted sources
5. If a data source is returning errors or is unavailable, clearly communicate this limitation
6. Better to provide no analysis than potentially misleading analysis based on simulated data
"""
        
        # Check if these instructions already exist in the message
        if "DATA INTEGRITY INSTRUCTIONS" not in current_message:
            new_message = current_message + data_integrity_message
            agent.update_system_message(new_message)
            logger.info("Modified Sentiment Analyst prompt with data integrity instructions")
        else:
            logger.info("Sentiment Analyst already has data integrity instructions")
        
        return True
    except Exception as e:
        logger.error(f"Error modifying Sentiment Analyst prompt: {str(e)}")
        return False

def modify_onchain_analyst_prompt(agent) -> bool:
    """
    Modify the On-Chain Analyst's prompt to ensure data integrity
    
    Args:
        agent: The on-chain analyst agent to modify
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the current system message
        current_message = agent.system_message
        
        # Add the data integrity instructions
        data_integrity_message = """
IMPORTANT DATA INTEGRITY INSTRUCTIONS:
1. NEVER use simulated, synthetic, or made-up on-chain data in your analysis
2. When you do not have access to real blockchain data sources, you MUST state clearly:
   "I cannot provide on-chain analysis at this time due to lack of access to blockchain data sources."
3. When data access is unavailable, explicitly recommend that your input should NOT be counted in trading decisions
4. Do not attempt to analyze blockchain metrics without verifiable data from trusted sources
5. If a data source is returning errors or is unavailable, clearly communicate this limitation
6. Better to provide no analysis than potentially misleading analysis based on simulated data
"""
        
        # Check if these instructions already exist in the message
        if "DATA INTEGRITY INSTRUCTIONS" not in current_message:
            new_message = current_message + data_integrity_message
            agent.update_system_message(new_message)
            logger.info("Modified On-Chain Analyst prompt with data integrity instructions")
        else:
            logger.info("On-Chain Analyst already has data integrity instructions")
        
        return True
    except Exception as e:
        logger.error(f"Error modifying On-Chain Analyst prompt: {str(e)}")
        return False

def ensure_data_integrity_for_agents(trading_system) -> Dict[str, Any]:
    """
    Ensure data integrity for all analyst agents in the trading system
    
    Args:
        trading_system: The trading system object containing the agents
        
    Returns:
        Dictionary with status for each agent
    """
    results = {}
    
    # Find and modify the Fundamental Analyst
    try:
        if hasattr(trading_system, "fundamental_analyst"):
            results["fundamental_analyst"] = modify_fundamental_analyst_prompt(
                trading_system.fundamental_analyst
            )
        elif hasattr(trading_system, "agents") and "fundamental_analyst" in trading_system.agents:
            results["fundamental_analyst"] = modify_fundamental_analyst_prompt(
                trading_system.agents["fundamental_analyst"]
            )
        else:
            results["fundamental_analyst"] = False
            results["fundamental_analyst_error"] = "Agent not found"
    except Exception as e:
        results["fundamental_analyst"] = False
        results["fundamental_analyst_error"] = str(e)
    
    # Find and modify the Sentiment Analyst
    try:
        if hasattr(trading_system, "sentiment_analyst"):
            results["sentiment_analyst"] = modify_sentiment_analyst_prompt(
                trading_system.sentiment_analyst
            )
        elif hasattr(trading_system, "agents") and "sentiment_analyst" in trading_system.agents:
            results["sentiment_analyst"] = modify_sentiment_analyst_prompt(
                trading_system.agents["sentiment_analyst"]
            )
        else:
            results["sentiment_analyst"] = False
            results["sentiment_analyst_error"] = "Agent not found"
    except Exception as e:
        results["sentiment_analyst"] = False
        results["sentiment_analyst_error"] = str(e)
    
    # Find and modify the On-Chain Analyst if it exists
    try:
        if hasattr(trading_system, "onchain_analyst"):
            results["onchain_analyst"] = modify_onchain_analyst_prompt(
                trading_system.onchain_analyst
            )
        elif hasattr(trading_system, "agents") and "onchain_analyst" in trading_system.agents:
            results["onchain_analyst"] = modify_onchain_analyst_prompt(
                trading_system.agents["onchain_analyst"]
            )
        else:
            # On-Chain Analyst is optional, so not finding it isn't an error
            results["onchain_analyst"] = "Not found (optional)"
    except Exception as e:
        results["onchain_analyst"] = False
        results["onchain_analyst_error"] = str(e)
    
    # Overall success
    results["success"] = results.get("fundamental_analyst", False) or results.get("sentiment_analyst", False)
    
    return results

def validate_data_response(response: str, analyst_type: str) -> Dict[str, Any]:
    """
    Validate if an analyst response properly discloses data unavailability
    
    Args:
        response: The analyst's response text
        analyst_type: Type of analyst ('fundamental', 'sentiment', 'onchain')
        
    Returns:
        Dictionary with validation results
    """
    # Common phrases that would indicate data unavailability is properly disclosed
    data_unavailable_phrases = [
        "cannot provide analysis",
        "lack of access to data",
        "data is unavailable",
        "no access to",
        "should not be counted",
        "data sources are not accessible",
        "unable to access",
        "without proper data",
        "data access limitations",
        "unable to provide",
        "do not count my input",
        "data sources unavailable",
        "insufficient data",
        "not enough data"
    ]
    
    # Check for appropriate disclosure in the response
    disclosed_properly = any(phrase in response.lower() for phrase in data_unavailable_phrases)
    
    # Phrases that might indicate simulated data is being used
    simulation_phrases = [
        "simulated",
        "synthetic",
        "generated",
        "approximated",
        "estimated",
        "modeled",
        "hypothetical"
    ]
    
    # Check if response might be using simulated data
    might_be_simulated = any(phrase in response.lower() for phrase in simulation_phrases)
    
    # Analyst-specific analysis phrases that shouldn't be present without data
    analysis_phrases = {
        "fundamental": ["on-chain metrics", "network activity", "whale accumulation", "exchange reserves"],
        "sentiment": ["social sentiment", "fear & greed", "social media", "sentiment is"],
        "onchain": ["blockchain data", "transaction volume", "active addresses", "miner revenue"]
    }
    
    # More flexible analysis for each analyst type
    if analyst_type == 'onchain':
        # Check for indications that this is a valid "no data available" message for on-chain
        onchain_specific_phrases = [
            "cannot provide on-chain analysis", 
            "unable to provide on-chain metrics",
            "lack of access to blockchain data",
            "data access limitations",
            "on-chain metrics analysis"
        ]
        onchain_disclosed = any(phrase in response.lower() for phrase in onchain_specific_phrases)
        if onchain_disclosed:
            disclosed_properly = True
    
    # Check if response contains analysis without proper data
    contains_analysis = any(phrase in response.lower() for phrase in analysis_phrases.get(analyst_type, []))
    
    # If the response explicitly states not to count the input in decisions, it's valid
    dont_count_phrases = [
        "should not be counted in trading decisions",
        "do not count my input",
        "not be counted in",
        "exclude my input",
        "disregard my analysis"
    ]
    explicitly_states_dont_count = any(phrase in response.lower() for phrase in dont_count_phrases)
    
    # If there's an explicit statement not to count the input, it strengthens the validity
    validity_boost = explicitly_states_dont_count
    
    return {
        "disclosed_properly": disclosed_properly,
        "might_be_simulated": might_be_simulated,
        "contains_analysis": contains_analysis,
        "explicitly_states_dont_count": explicitly_states_dont_count,
        "is_valid": (disclosed_properly and not might_be_simulated and not contains_analysis) or validity_boost
    }

if __name__ == "__main__":
    print("Data Integrity Module for Analyst Agents")
    print("Run this module as part of the trading system to ensure data integrity")
    
    # Example validation
    example_response = "I cannot provide fundamental analysis at this time due to lack of access to on-chain data sources. My input should not be counted in trading decisions."
    validation = validate_data_response(example_response, "fundamental")
    print("\nExample Validation:")
    print(json.dumps(validation, indent=2))