#!/usr/bin/env python3
"""
Data Integrity Module for Trading Agents

This module ensures that analyst agents explicitly state when they don't have
access to real data sources instead of providing simulated responses.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("data_integrity")

# Data integrity instructions for different analyst types
FUNDAMENTAL_ANALYST_INSTRUCTIONS = """
DATA INTEGRITY INSTRUCTIONS:
If you DO NOT have access to real financial data sources (earnings reports, balance sheets, financial statements, etc.):
1. State clearly: "I cannot provide fundamental analysis at this time due to lack of access to financial data sources."
2. Add: "My input should NOT be counted in trading decisions."
3. Do NOT provide simulated or imagined analysis.
4. DO NOT suggest any market overview, trend, or sentiment if data access is unavailable.
5. DO NOT speculate on economic conditions or corporate actions without data.
"""

SENTIMENT_ANALYST_INSTRUCTIONS = """
DATA INTEGRITY INSTRUCTIONS:
If you DO NOT have access to real sentiment data sources (social media, news sentiment, Fear & Greed Index, etc.):
1. State clearly: "I cannot provide sentiment analysis at this time due to lack of access to sentiment data sources."
2. Add: "My input should NOT be counted in trading decisions."
3. Do NOT provide simulated or imagined sentiment analysis.
4. DO NOT suggest any market sentiment or social media trends if data access is unavailable.
5. DO NOT speculate on public opinion or market mood without data.
"""

ONCHAIN_ANALYST_INSTRUCTIONS = """
DATA INTEGRITY INSTRUCTIONS:
If you DO NOT have access to real blockchain data (transactions, wallet activities, exchange flows, etc.):
1. State clearly: "I cannot provide on-chain analysis at this time due to lack of access to blockchain data."
2. Add: "My input should NOT be counted in trading decisions."
3. Do NOT provide simulated or imagined on-chain analysis.
4. DO NOT suggest any blockchain metrics or trends if data access is unavailable.
5. DO NOT speculate on whale movements, exchange flows, or network activity without data.
"""

def modify_fundamental_analyst_prompt(agent) -> bool:
    """
    Add data integrity instructions to fundamental analyst prompt
    
    Args:
        agent: Agent object
        
    Returns:
        True if modified successfully, False otherwise
    """
    try:
        if hasattr(agent, "system_message"):
            if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                agent.system_message += FUNDAMENTAL_ANALYST_INSTRUCTIONS
                logger.info("Added data integrity instructions to fundamental analyst")
                return True
            else:
                logger.info("Fundamental analyst already has data integrity instructions")
                return True
        else:
            logger.warning("Fundamental analyst does not have system_message attribute")
            return False
    except Exception as e:
        logger.error(f"Error modifying fundamental analyst prompt: {str(e)}")
        return False

def modify_sentiment_analyst_prompt(agent) -> bool:
    """
    Add data integrity instructions to sentiment analyst prompt
    
    Args:
        agent: Agent object
        
    Returns:
        True if modified successfully, False otherwise
    """
    try:
        if hasattr(agent, "system_message"):
            if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                agent.system_message += SENTIMENT_ANALYST_INSTRUCTIONS
                logger.info("Added data integrity instructions to sentiment analyst")
                return True
            else:
                logger.info("Sentiment analyst already has data integrity instructions")
                return True
        else:
            logger.warning("Sentiment analyst does not have system_message attribute")
            return False
    except Exception as e:
        logger.error(f"Error modifying sentiment analyst prompt: {str(e)}")
        return False

def modify_onchain_analyst_prompt(agent) -> bool:
    """
    Add data integrity instructions to on-chain analyst prompt
    
    Args:
        agent: Agent object
        
    Returns:
        True if modified successfully, False otherwise
    """
    try:
        if hasattr(agent, "system_message"):
            if "DATA INTEGRITY INSTRUCTIONS" not in agent.system_message:
                agent.system_message += ONCHAIN_ANALYST_INSTRUCTIONS
                logger.info("Added data integrity instructions to on-chain analyst")
                return True
            else:
                logger.info("On-chain analyst already has data integrity instructions")
                return True
        else:
            logger.warning("On-chain analyst does not have system_message attribute")
            return False
    except Exception as e:
        logger.error(f"Error modifying on-chain analyst prompt: {str(e)}")
        return False

def ensure_data_integrity_for_agents(trading_system) -> Dict[str, Any]:
    """
    Ensure data integrity for all analyst agents in the trading system
    
    Args:
        trading_system: Trading system object or dictionary
        
    Returns:
        Dictionary with results
    """
    results = {}
    
    # Try to modify fundamental analyst
    try:
        # Check if trading_system is a dictionary or an object
        if isinstance(trading_system, dict):
            if "fundamental_analyst" in trading_system:
                results["fundamental_analyst"] = modify_fundamental_analyst_prompt(
                    trading_system["fundamental_analyst"]
                )
            else:
                results["fundamental_analyst"] = False
                results["fundamental_analyst_error"] = "Agent not found"
        else:
            # Try to access agents as attributes
            if hasattr(trading_system, "fundamental_analyst"):
                results["fundamental_analyst"] = modify_fundamental_analyst_prompt(
                    trading_system.fundamental_analyst
                )
            # Try to access agents as a dictionary
            elif hasattr(trading_system, "agents") and isinstance(trading_system.agents, dict):
                if "fundamental_analyst" in trading_system.agents:
                    results["fundamental_analyst"] = modify_fundamental_analyst_prompt(
                        trading_system.agents["fundamental_analyst"]
                    )
                else:
                    results["fundamental_analyst"] = False
                    results["fundamental_analyst_error"] = "Agent not found in agents dictionary"
            else:
                results["fundamental_analyst"] = False
                results["fundamental_analyst_error"] = "Agent not found"
    except Exception as e:
        results["fundamental_analyst"] = False
        results["fundamental_analyst_error"] = str(e)
    
    # Try to modify sentiment analyst
    try:
        # Check if trading_system is a dictionary or an object
        if isinstance(trading_system, dict):
            if "sentiment_analyst" in trading_system:
                results["sentiment_analyst"] = modify_sentiment_analyst_prompt(
                    trading_system["sentiment_analyst"]
                )
            else:
                results["sentiment_analyst"] = False
                results["sentiment_analyst_error"] = "Agent not found"
        else:
            # Try to access agents as attributes
            if hasattr(trading_system, "sentiment_analyst"):
                results["sentiment_analyst"] = modify_sentiment_analyst_prompt(
                    trading_system.sentiment_analyst
                )
            # Try to access agents as a dictionary
            elif hasattr(trading_system, "agents") and isinstance(trading_system.agents, dict):
                if "sentiment_analyst" in trading_system.agents:
                    results["sentiment_analyst"] = modify_sentiment_analyst_prompt(
                        trading_system.agents["sentiment_analyst"]
                    )
                else:
                    results["sentiment_analyst"] = False
                    results["sentiment_analyst_error"] = "Agent not found in agents dictionary"
            else:
                results["sentiment_analyst"] = False
                results["sentiment_analyst_error"] = "Agent not found"
    except Exception as e:
        results["sentiment_analyst"] = False
        results["sentiment_analyst_error"] = str(e)
    
    # Try to modify on-chain analyst (optional)
    try:
        # Check if trading_system is a dictionary or an object
        if isinstance(trading_system, dict):
            if "onchain_analyst" in trading_system:
                results["onchain_analyst"] = modify_onchain_analyst_prompt(
                    trading_system["onchain_analyst"]
                )
            else:
                results["onchain_analyst"] = "Not found (optional)"
        else:
            # Try to access agents as attributes
            if hasattr(trading_system, "onchain_analyst"):
                results["onchain_analyst"] = modify_onchain_analyst_prompt(
                    trading_system.onchain_analyst
                )
            # Try to access agents as a dictionary
            elif hasattr(trading_system, "agents") and isinstance(trading_system.agents, dict):
                if "onchain_analyst" in trading_system.agents:
                    results["onchain_analyst"] = modify_onchain_analyst_prompt(
                        trading_system.agents["onchain_analyst"]
                    )
                else:
                    results["onchain_analyst"] = "Not found in agents dictionary (optional)"
            else:
                results["onchain_analyst"] = "Not found (optional)"
    except Exception as e:
        results["onchain_analyst"] = f"Error: {str(e)} (optional)"
    
    # Check if at least fundamental and sentiment analysts were modified
    results["success"] = results.get("fundamental_analyst", False) and results.get("sentiment_analyst", False)
    
    return results

def validate_data_response(response: str, analyst_type: str) -> Dict[str, Any]:
    """
    Validate if an analyst response properly discloses data unavailability
    
    Args:
        response: The analyst's response text
        analyst_type: Type of analyst ('fundamental_analyst', 'sentiment_analyst', 'onchain_analyst')
        
    Returns:
        Dictionary with validation results
    """
    if not response:
        return {
            "is_valid": False,
            "reason": "Empty response"
        }
    
    # Normalize analyst type
    analyst_type = analyst_type.lower()
    
    # Set expected patterns based on analyst type
    if "fundamental" in analyst_type:
        disclosure_pattern = r"cannot provide (fundamental|financial) analysis|lack of access to (financial|fundamental) data"
    elif "sentiment" in analyst_type:
        disclosure_pattern = r"cannot provide sentiment analysis|lack of access to sentiment data"
    elif "onchain" in analyst_type or "on-chain" in analyst_type or "on chain" in analyst_type:
        disclosure_pattern = r"(cannot|unable to) provide (on.?chain|blockchain) analysis|lack of access to (blockchain|on.?chain) data"
    else:
        disclosure_pattern = r"cannot provide .* analysis|lack of access to .* data|unable to provide .* analysis"
    
    # Common pattern for "should not be counted" statement
    not_counted_pattern = r"(should )?not be counted|don'?t count|shouldn'?t (be )?count(ed)?|disregard|ignore"
    
    # Check if response contains disclosure pattern (case insensitive)
    has_disclosure = bool(re.search(disclosure_pattern, response, re.IGNORECASE))
    has_not_counted = bool(re.search(not_counted_pattern, response, re.IGNORECASE))
    
    # Validate based on disclosure patterns
    if "cannot provide" in response.lower() or "unable to provide" in response.lower():
        # Data unavailability is disclosed
        if has_disclosure and has_not_counted:
            return {
                "is_valid": True,
                "reason": "Properly discloses lack of data access and advises not to count input"
            }
        elif has_disclosure:
            return {
                "is_valid": False,
                "reason": "Discloses lack of data access but doesn't advise not to count input"
            }
        else:
            return {
                "is_valid": False,
                "reason": "Mentions inability but doesn't clearly state lack of data access"
            }
    else:
        # No disclosure of data unavailability
        # For demo purposes, we'll consider normal responses as valid
        # In a real implementation, we would need to check if the agent actually has data access
        return {
            "is_valid": False,
            "reason": "No disclosure of data unavailability"
        }
