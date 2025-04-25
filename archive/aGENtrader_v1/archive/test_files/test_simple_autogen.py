"""
Simple test script for AutoGen database serialization

This script tests a basic interaction between AutoGen agents and the 
database retrieval tool with focus on proper serialization.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_autogen")

# Import AutoGen components
try:
    import autogen
    from autogen import Agent, AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    logger.warning("AutoGen not available. Will run in mock mode.")
    AUTOGEN_AVAILABLE = False

# Import our database tools
from agents.database_retrieval_tool import (
    get_db_tool, 
    get_recent_market_data,
    get_market_data_range, 
    calculate_technical_indicators,
    get_market_summary,
    CustomJSONEncoder
)

# Import AutoGen integration
from agents.autogen_db_integration import (
    AutoGenDBIntegration,
    get_integration,
    db_function_map
)

def print_section(title: str) -> None:
    """Print a section header for better readability"""
    print("\n" + "="*80)
    print(f"  {title}  ".center(80, "="))
    print("="*80 + "\n")

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found in environment variables.")
        print("Will run in mock mode without actual API calls.")
        return None
    
    return {
        "config_list": [{
            "model": "gpt-4",
            "api_key": os.environ.get("OPENAI_API_KEY")
        }],
        "temperature": 0.2,
        "timeout": 60,
        "max_tokens": 4000
    }

async def run_simple_test():
    """Run a simple test of AutoGen with database serialization"""
    print_section("Testing Database + AutoGen Integration")
    
    # Test direct database access first
    db_tool = get_db_tool()
    recent_data = db_tool.get_recent_market_data("BTCUSDT", 3)
    print("Recent Market Data:")
    print(json.dumps(recent_data, cls=CustomJSONEncoder, indent=2))
    print()
    
    # Check if we can run AutoGen tests
    if not AUTOGEN_AVAILABLE:
        print("AutoGen is not available. Skipping AutoGen tests.")
        return
    
    # Set up OpenAI config
    openai_config = setup_openai_config()
    if not openai_config:
        print("OpenAI configuration not available. Skipping AutoGen tests.")
        return
    
    # Create AutoGen integration
    integration = get_integration(openai_config)
    
    # Create an analyst agent
    analyst = integration.create_analyst_agent("MarketAnalyst")
    
    # Create a user proxy for interaction
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,  # Reduced from 10 to ensure timely completion
        code_execution_config={"use_docker": False},
        function_map=integration.function_map
    )
    
    print_section("Starting Conversation with Market Analyst")
    
    # Start the conversation with timeout
    try:
        import asyncio
        # Create a timeout coroutine
        async def chat_with_timeout():
            # Run chat with a timeout of 90 seconds
            try:
                return await asyncio.wait_for(
                    asyncio.create_task(
                        user_proxy.a_initiate_chat(
                            analyst,
                            message="""
                            Please provide a brief analysis of the current market conditions for BTCUSDT.
                            Focus on the 1-hour timeframe and include:
                            1. Current trend direction (bullish/bearish)
                            2. Key technical indicators (RSI, MACD)
                            3. Your trading recommendation (buy/sell/hold)
                            
                            Keep your response concise. Use the database functions to retrieve the necessary data.
                            """
                        )
                    ),
                    timeout=90
                )
            except asyncio.TimeoutError:
                print("Analysis took too long and was interrupted after 90 seconds.")
                return {"messages": ["Analysis timeout occurred"]}
        
        # Run the chat with timeout
        chat_result = await chat_with_timeout()
        
        print_section("Chat Result")
        message_count = len(chat_result.get('messages', []))
        print(f"Total messages: {message_count}")
        
        # Print the last message if available
        if message_count > 0:
            last_message = chat_result.get('messages', [])[-1]
            print("\nLast message content:")
            if isinstance(last_message, dict) and 'content' in last_message:
                print(last_message['content'][:500] + "..." if len(last_message['content']) > 500 else last_message['content'])
            else:
                print("Last message format unknown or empty")
        
        # Save conversation to file for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/logs/autogen_conversation_{timestamp}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(chat_result, f, cls=CustomJSONEncoder, indent=2)
        
        print(f"Conversation saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error in AutoGen chat: {e}")
        print(f"Error: {e}")

async def main():
    """Main entry point"""
    await run_simple_test()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())