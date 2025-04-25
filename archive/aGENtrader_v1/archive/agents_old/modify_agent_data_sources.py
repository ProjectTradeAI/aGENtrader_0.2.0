"""
Modify Agent Data Sources

This module provides functions to update the analyst agents to use 
real data sources instead of simulated data.

The modified agents are:
1. Fundamental Analyst - Uses on-chain metrics and whale transaction data
2. Sentiment Analyst - Uses social sentiment data and Fear & Greed Index
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

# Import data providers
try:
    # For testing if API providers are available
    from utils.integrated_advanced_data import get_provider as get_advanced_data_provider
    
    # For registering functions with AutoGen
    from agents.register_advanced_data_functions import (
        register_advanced_data_functions,
        register_with_autogen
    )
    
    PROVIDERS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing data providers: {str(e)}")
    PROVIDERS_AVAILABLE = False

# Try to get the Santiment API key from environment
SANTIMENT_API_KEY = os.environ.get("SANTIMENT_API_KEY")

def check_api_availability() -> Dict[str, bool]:
    """
    Check if the necessary APIs are available
    
    Returns:
        Dictionary with API availability status
    """
    status = {
        "providers_importable": PROVIDERS_AVAILABLE,
        "santiment_key_available": bool(SANTIMENT_API_KEY)
    }
    
    # Try to initialize the provider if possible
    if PROVIDERS_AVAILABLE and SANTIMENT_API_KEY:
        try:
            provider = get_advanced_data_provider(SANTIMENT_API_KEY)
            
            # Try to get some data to verify access
            fear_greed = provider.get_fear_greed_index(days=1)
            status["fear_greed_available"] = "error" not in fear_greed
            
            # Try to get some Santiment data
            sentiment = provider.get_social_sentiment("BTC", days=1)
            status["santiment_available"] = "error" not in sentiment
            
        except Exception as e:
            logger.error(f"Error checking API availability: {str(e)}")
            status["fear_greed_available"] = False
            status["santiment_available"] = False
    else:
        status["fear_greed_available"] = False
        status["santiment_available"] = False
    
    return status

def modify_fundamental_analyst(agent, use_real_data: bool = True) -> bool:
    """
    Modify the Fundamental Analyst agent to use real data sources
    
    Args:
        agent: The AutoGen agent to modify
        use_real_data: Whether to use real data or fallback to simulation
        
    Returns:
        True if successful, False otherwise
    """
    if not PROVIDERS_AVAILABLE:
        logger.error("Data providers not available, cannot modify agent")
        return False
    
    try:
        if use_real_data:
            # Register the advanced data functions with the agent
            logger.info("Registering advanced data functions with Fundamental Analyst")
            success = register_advanced_data_functions(agent)
            
            if success:
                # Update the agent's system message to mention real data
                system_message = agent.system_message
                
                # Add information about real data sources if not already there
                if "real on-chain metrics" not in system_message:
                    new_message = system_message + """

You now have access to real on-chain metrics and whale transaction data through these functions:
- query_on_chain_metrics: Get on-chain metrics like active addresses, network growth, and more
- query_whale_transactions: Get data about large transactions and whale wallet movements
- get_fundamental_analysis: Get a comprehensive fundamental analysis combining multiple data sources

Always use these functions to get real data rather than making assumptions or using simulated data.
"""
                    agent.update_system_message(new_message)
                    logger.info("Updated Fundamental Analyst system message")
            
            return success
        else:
            logger.info("Not modifying Fundamental Analyst (use_real_data=False)")
            return True
            
    except Exception as e:
        logger.error(f"Error modifying Fundamental Analyst: {str(e)}")
        return False

def modify_sentiment_analyst(agent, use_real_data: bool = True) -> bool:
    """
    Modify the Sentiment Analyst agent to use real data sources
    
    Args:
        agent: The AutoGen agent to modify
        use_real_data: Whether to use real data or fallback to simulation
        
    Returns:
        True if successful, False otherwise
    """
    if not PROVIDERS_AVAILABLE:
        logger.error("Data providers not available, cannot modify agent")
        return False
    
    try:
        if use_real_data:
            # Register the advanced data functions with the agent
            logger.info("Registering advanced data functions with Sentiment Analyst")
            success = register_advanced_data_functions(agent)
            
            if success:
                # Update the agent's system message to mention real data
                system_message = agent.system_message
                
                # Add information about real data sources if not already there
                if "real sentiment data" not in system_message:
                    new_message = system_message + """

You now have access to real sentiment data and market mood indicators through these functions:
- query_social_sentiment: Get social media sentiment data across various platforms
- query_fear_greed_index: Get the Crypto Fear & Greed Index values
- get_sentiment_analysis: Get a comprehensive sentiment analysis combining multiple data sources

Always use these functions to get real data rather than making assumptions or using simulated data.
"""
                    agent.update_system_message(new_message)
                    logger.info("Updated Sentiment Analyst system message")
            
            return success
        else:
            logger.info("Not modifying Sentiment Analyst (use_real_data=False)")
            return True
            
    except Exception as e:
        logger.error(f"Error modifying Sentiment Analyst: {str(e)}")
        return False

def modify_trading_system(trading_system, use_real_data: bool = True) -> Dict[str, Any]:
    """
    Modify the entire trading system to use real data sources
    
    Args:
        trading_system: The trading system object with agent references
        use_real_data: Whether to use real data or fallback to simulation
        
    Returns:
        Dictionary with modification status for each agent
    """
    if not PROVIDERS_AVAILABLE:
        return {
            "success": False,
            "error": "Data providers not available",
            "api_status": check_api_availability()
        }
    
    results = {
        "api_status": check_api_availability()
    }
    
    # Check if we have the necessary components
    api_status = results["api_status"]
    if use_real_data and not (api_status["fear_greed_available"] or api_status["santiment_available"]):
        logger.warning("No API data sources available, falling back to simulation")
        use_real_data = False
    
    # Try to modify each analyst agent
    try:
        # Find and modify the Fundamental Analyst
        if hasattr(trading_system, "fundamental_analyst"):
            results["fundamental_analyst"] = modify_fundamental_analyst(
                trading_system.fundamental_analyst, 
                use_real_data
            )
        elif hasattr(trading_system, "agents") and "fundamental_analyst" in trading_system.agents:
            results["fundamental_analyst"] = modify_fundamental_analyst(
                trading_system.agents["fundamental_analyst"],
                use_real_data
            )
        else:
            results["fundamental_analyst"] = False
            results["fundamental_analyst_error"] = "Agent not found"
        
        # Find and modify the Sentiment Analyst
        if hasattr(trading_system, "sentiment_analyst"):
            results["sentiment_analyst"] = modify_sentiment_analyst(
                trading_system.sentiment_analyst,
                use_real_data
            )
        elif hasattr(trading_system, "agents") and "sentiment_analyst" in trading_system.agents:
            results["sentiment_analyst"] = modify_sentiment_analyst(
                trading_system.agents["sentiment_analyst"],
                use_real_data
            )
        else:
            results["sentiment_analyst"] = False
            results["sentiment_analyst_error"] = "Agent not found"
        
        # Overall success
        results["success"] = results.get("fundamental_analyst", False) or results.get("sentiment_analyst", False)
        results["using_real_data"] = use_real_data
        
        return results
    except Exception as e:
        logger.error(f"Error modifying trading system: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "api_status": api_status
        }

def set_santiment_api_key(api_key: str) -> bool:
    """
    Set the Santiment API key for use with the data providers
    
    Args:
        api_key: Santiment API key
        
    Returns:
        True if successful, False otherwise
    """
    if not api_key:
        logger.error("No API key provided")
        return False
    
    try:
        # Set the environment variable
        os.environ["SANTIMENT_API_KEY"] = api_key
        
        # Update the global variable
        global SANTIMENT_API_KEY
        SANTIMENT_API_KEY = api_key
        
        logger.info("Santiment API key set successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting Santiment API key: {str(e)}")
        return False

if __name__ == "__main__":
    # Print API availability status
    status = check_api_availability()
    print("API Availability Status:")
    print(json.dumps(status, indent=2))
    
    # Check if Santiment API key is available
    if not status["santiment_key_available"]:
        print("\nSantiment API key not found in environment variables.")
        print("Set the SANTIMENT_API_KEY environment variable to enable Santiment data.")
        
        # Ask if the user wants to provide a key
        if input("Would you like to provide a Santiment API key now? (y/n): ").lower() == "y":
            api_key = input("Enter your Santiment API key: ").strip()
            if set_santiment_api_key(api_key):
                print("API key set successfully")
                
                # Update status
                status = check_api_availability()
                print("\nUpdated API Availability Status:")
                print(json.dumps(status, indent=2))