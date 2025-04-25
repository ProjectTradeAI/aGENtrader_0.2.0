"""
Test script to verify AutoGen integration with database serialization

This script tests how AutoGen agents interact with the database retrieval tool
and use the serialization functions to handle complex data types.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
    from agents.autogen_db_integration import get_integration
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("AutoGen not installed, cannot run test")
    exit(1)

def print_section(title: str) -> None:
    """Print a section header for better readability"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "-"))
    print("="*80 + "\n")

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        return None
    
    config_list = [
        {
            "model": "gpt-3.5-turbo",
            "api_key": openai_api_key
        }
    ]
    
    return config_list

async def run_autogen_serialization_test():
    """Test serialization with AutoGen agents"""
    print_section("Testing AutoGen Integration with Serialization")
    
    # Set up OpenAI config
    config_list = setup_openai_config()
    if not config_list:
        print("⚠️ Skipping test: No OpenAI API key found")
        return False
    
    # Create integration
    integration = get_integration(config_list)
    
    # Create a market analyst agent with serialization capability
    market_analyst = integration.create_market_analyst(name="Market_Analyst")
    
    # Create a user proxy agent for automated execution
    user_proxy = integration.create_user_proxy(
        name="User",
        human_input_mode="NEVER",
        code_execution_config={"work_dir": ".", "use_docker": False}
    )
    
    # Create a test message that involves data serialization
    test_message = """
    Please perform the following tasks:
    1. First, import the necessary functions with:
       from agents.database_retrieval_tool import get_db_tool, serialize_results, CustomJSONEncoder
    2. Get the database tool instance with:
       db_tool = get_db_tool()
    3. Get the latest price for BTCUSDT with:
       latest_price = db_tool.get_latest_price('BTCUSDT')
    4. Serialize the result using the serialize_results function
    5. Get the price history for BTCUSDT for the last day
    6. Take the first 3 records from the price history result (if any are available)
    7. Serialize those selected records
    8. Get the market summary for BTCUSDT and serialize it
    9. Explain the benefits of using the serialization function in the context of database queries
    """
    
    print("Initiating chat with AutoGen agents...")
    try:
        # Start the conversation
        await user_proxy.a_initiate_chat(
            market_analyst,
            message=test_message
        )
        print("AutoGen test completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error during AutoGen test: {str(e)}")
        print(f"❌ AutoGen test failed with error: {str(e)}")
        return False

async def main():
    """Main entry point"""
    print_section("AutoGen Database Serialization Test")
    
    result = await run_autogen_serialization_test()
    
    print_section("Test Summary")
    print(f"AutoGen serialization test: {'✅ PASSED' if result else '❌ FAILED'}")
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main())