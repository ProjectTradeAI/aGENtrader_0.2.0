"""
Test AutoGen Database Integration

This script tests the integration of our market data functions with AutoGen.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
import time

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
    print("This test requires AutoGen to be installed.")
    print("Please install with: pip install pyautogen")
    sys.exit(1)

# Import function registration module
try:
    from agents.register_market_data_functions import register_with_autogen, create_function_mapping
except ImportError as e:
    logger.error(f"Error importing market data functions: {str(e)}")
    print("Market data function registration module not available.")
    sys.exit(1)

def get_api_key():
    """Get OpenAI API key from environment"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        logger.info("Using default test API key")
        # This is just a placeholder key format for testing
        api_key = "sk-" + "x" * 48
    
    # Log part of the key (securely)
    if api_key:
        masked_key = f"sk-{api_key[3:5]}...{api_key[-4:]}" if len(api_key) > 10 else "Invalid Key"
        logger.info(f"Using API key: {masked_key} (length: {len(api_key)})")
    
    return api_key

def create_config_list(api_key):
    """Create a configuration list for LLM"""
    return [
        {
            "model": "gpt-3.5-turbo-0125",
            "api_key": api_key
        }
    ]

def save_config_list(config_list):
    """Save config list to a temporary file"""
    config_path = "oai_config_list.json"
    with open(config_path, "w") as f:
        json.dump(config_list, f)
    
    return config_path

def setup_assistant_agent(config_list):
    """Set up the assistant agent with market data functions"""
    # Create function mapping with AutoGen format
    function_list = create_function_mapping()
    function_map = register_with_autogen()
    
    # Configure the assistant agent
    logger.info("Creating assistant agent with market data functions")
    assistant = AssistantAgent(
        name="MarketDataAssistant",
        system_message="""You are a cryptocurrency market data assistant.
You have access to real market data through these functions.
Always use the available functions to get data rather than making up information.
Be aware that the market data might be from a database and slightly outdated, 
so always mention the data age in your responses.""",
        llm_config={
            "config_list": config_list,
            "functions": function_list
        }
    )
    
    return assistant, function_map

def setup_user_proxy(function_map):
    """Set up the user proxy agent"""
    logger.info("Creating user proxy agent")
    
    # Configure the user proxy agent
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        function_map=function_map
    )
    
    return user_proxy

def run_market_data_test():
    """Run a test of the market data functions with AutoGen"""
    logger.info("Starting market data integration test")
    
    # Get API key and create config
    api_key = get_api_key()
    if not api_key:
        logger.error("No API key available, cannot proceed with test")
        return
    
    config_list = create_config_list(api_key)
    
    try:
        # Save config to file (required by AutoGen)
        config_path = save_config_list(config_list)
        logger.info(f"Config saved to {config_path}")
        
        # Create agents
        assistant, function_map = setup_assistant_agent(config_list)
        user_proxy = setup_user_proxy(function_map)
        
        # Run a simple conversation
        logger.info("Starting conversation")
        user_proxy.initiate_chat(
            assistant,
            message="""
            I need some information about Bitcoin:
            1. What's the current price of Bitcoin?
            2. Show me the last 5 hours of price data.
            3. Provide a brief technical analysis of recent Bitcoin performance.
            """
        )
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
    finally:
        # Clean up config file
        if os.path.exists("oai_config_list.json"):
            os.remove("oai_config_list.json")
            logger.info("Removed temporary config file")

def run_simple_function_test():
    """Run a simplified test using just the market data functions directly"""
    logger.info("Running simplified function test")
    
    # Import functions directly
    try:
        from agents.query_market_data import query_market_data, get_market_price, get_market_analysis
        
        print("\n=== Bitcoin Price ===")
        price_data = get_market_price("BTCUSDT")
        print(price_data)
        
        print("\n=== Recent Price History ===")
        history = query_market_data("BTCUSDT", interval="1h", limit=5, format_type="markdown")
        print(history)
        
        print("\n=== Simple Market Analysis ===")
        analysis = get_market_analysis("BTCUSDT", interval="1d", days=7, format_type="text")
        print(analysis)
        
        logger.info("Direct function test completed")
        
    except Exception as e:
        logger.error(f"Error in direct function test: {str(e)}")

def main():
    """Main entry point"""
    print("AutoGen Database Integration Test")
    print("================================")
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        run_simple_function_test()
    else:
        run_market_data_test()

if __name__ == "__main__":
    main()