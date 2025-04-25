"""
AutoGen Database Integration Example

This script demonstrates how to use the database market data functions with AutoGen.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if AutoGen is available
try:
    import autogen
    from autogen import Agent, AssistantAgent, UserProxyAgent, config_list_from_json
except ImportError:
    logger.error("AutoGen not available. Please install with: pip install pyautogen")
    print("This example requires AutoGen to be installed.")
    print("Please install with: pip install pyautogen")
    sys.exit(1)

# Import market data functions
try:
    from agents.query_market_data import (
        query_market_data,
        get_market_price,
        get_market_analysis
    )
except ImportError as e:
    logger.error(f"Error importing market data functions: {str(e)}")
    print("Market data functions not available. Make sure you have the necessary modules.")
    sys.exit(1)

def setup_function_map():
    """Set up function mapping for AutoGen"""
    return {
        "query_market_data": {
            "name": "query_market_data",
            "description": "Query historical market data for a specific cryptocurrency symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)",
                        "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                        "default": "1h"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of data points to retrieve",
                        "default": 24
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (alternative to limit)"
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": query_market_data
        },
        "get_market_price": {
            "name": "get_market_price",
            "description": "Get the latest market price for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    }
                },
                "required": ["symbol"]
            },
            "function": get_market_price
        },
        "get_market_analysis": {
            "name": "get_market_analysis",
            "description": "Get technical analysis and market statistics for a cryptocurrency",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g., 'BTCUSDT'"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (1h, 4h, 1d)",
                        "enum": ["1h", "4h", "1d"],
                        "default": "1d"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 30
                    },
                    "format_type": {
                        "type": "string", 
                        "description": "Output format (json, markdown, text)",
                        "enum": ["json", "markdown", "text"],
                        "default": "json"
                    }
                },
                "required": ["symbol"]
            },
            "function": get_market_analysis
        }
    }

def setup_assistant_agent():
    """Set up the assistant agent with market data functions"""
    # Create function mapping
    function_map = setup_function_map()
    
    # Configure the assistant agent
    assistant = AssistantAgent(
        name="CryptoAnalyst",
        system_message="""You are a sophisticated cryptocurrency analyst assistant.
You have access to real market data through built-in functions.
Always use the available functions to get real data rather than making up information.
When analyzing crypto markets, be thorough and base your analysis on the actual market data.
Note that the market data might be slightly outdated, always check and mention the data age in your analysis.
""",
        llm_config={
            "functions": list(function_map.values()),
            "config_list": config_list_from_json("OAI_CONFIG_LIST")
        }
    )
    
    # Return the agent
    return assistant

def setup_user_proxy():
    """Set up the user proxy agent"""
    # Create function mapping
    function_map = setup_function_map()
    
    # Configure the user proxy agent
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        function_map=function_map
    )
    
    # Return the agent
    return user_proxy

def simulate_conversation():
    """Simulate a conversation with the assistant"""
    try:
        # Create the agents
        assistant = setup_assistant_agent()
        user_proxy = setup_user_proxy()
        
        # Start the conversation
        user_proxy.initiate_chat(
            assistant,
            message="""
            I'm interested in Bitcoin. Can you tell me:
            1. What's the current price of Bitcoin?
            2. How has Bitcoin been performing in the last 24 hours?
            3. Can you show me some recent price data for Bitcoin (last 5 hours)?
            
            Please provide a brief technical analysis based on this data.
            """
        )
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}")
        print(f"Error: {str(e)}")

def test_market_data_functions_directly():
    """Test the market data functions directly"""
    print("Testing market data functions directly...\n")
    
    # Test getting the current price
    print("=== Current Bitcoin Price ===")
    price_data = get_market_price("BTCUSDT")
    print(price_data)
    print()
    
    # Test getting historical data
    print("=== Recent Bitcoin Price Data (Last 5 Hours) ===")
    historical_data = query_market_data("BTCUSDT", interval="1h", limit=5, format_type="markdown")
    print(historical_data)
    print()
    
    # Test getting market analysis
    print("=== Bitcoin Market Analysis ===")
    analysis = get_market_analysis("BTCUSDT", interval="1h", days=7, format_type="markdown")
    print(analysis)

def main():
    """Main entry point"""
    print("AutoGen Database Integration Example")
    print("-----------------------------------")
    
    # Check if we should run the AutoGen conversation or just test the functions
    if len(sys.argv) > 1 and sys.argv[1] == "--test-functions":
        test_market_data_functions_directly()
    else:
        print("This will attempt to start an AutoGen conversation.")
        print("This requires a properly configured OAI_CONFIG_LIST file.")
        print("If you don't have this set up, use --test-functions to test the market data functions directly.")
        print()
        
        choice = input("Do you want to continue with the AutoGen conversation? (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            simulate_conversation()
        else:
            test_market_data_functions_directly()

if __name__ == "__main__":
    main()