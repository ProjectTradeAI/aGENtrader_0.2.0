"""
Minimal test script for AutoGen database integration

This script tests just the basic functionality with a timeout
to ensure it completes in a reasonable time.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import AutoGen components if available
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    logging.warning("AutoGen not available. Will run in mock mode.")
    AUTOGEN_AVAILABLE = False

# Import database tools
from agents.database_retrieval_tool import (
    get_db_tool,
    get_recent_market_data,
    get_latest_price,
    CustomJSONEncoder
)

# Import AutoGen integration
from agents.autogen_db_integration import (
    get_integration
)

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found in environment variables.")
        return None
    
    return {
        "config_list": [{
            "model": "gpt-4",
            "api_key": os.environ.get("OPENAI_API_KEY")
        }],
        "temperature": 0.2,
        "timeout": 30,
        "max_tokens": 1000
    }

async def run_test_with_timeout(timeout_seconds=60):
    """Run a minimal test with timeout"""
    # Check if we can run AutoGen tests
    if not AUTOGEN_AVAILABLE:
        print("AutoGen is not available. Skipping AutoGen tests.")
        return
    
    # Set up OpenAI config
    openai_config = setup_openai_config()
    if not openai_config:
        print("OpenAI configuration not available. Skipping AutoGen tests.")
        return
    
    # Test database access first
    print("\n=== Testing Database Access ===")
    
    # Test get_latest_price function
    print("Testing get_latest_price function...")
    latest_price = get_latest_price("BTCUSDT")
    print(f"Latest BTCUSDT price data: {latest_price}")
    
    # Parse the JSON response if it's a string
    if isinstance(latest_price, str):
        try:
            latest_price_data = json.loads(latest_price)
            print(f"  Close: {latest_price_data['close']} at {latest_price_data['timestamp']}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
    else:
        print(f"  Close: {latest_price['close']} at {latest_price['timestamp']}")
    
    # Test get_recent_market_data as well
    db_tool = get_db_tool()
    recent_data = db_tool.get_recent_market_data("BTCUSDT", 1)
    print(f"Recent BTCUSDT data: {recent_data['data'][0]['close']} at {recent_data['data'][0]['timestamp']}")
    
    print("\n=== Testing AutoGen Integration ===")
    try:
        # Create AutoGen integration
        integration = get_integration(openai_config)
        
        # Create a simple agent
        agent = integration.create_analyst_agent("SimpleAnalyst")
        print(f"Created agent: {agent.name}")
        
        # Create a user proxy
        user_proxy = autogen.UserProxyAgent(
            name="TestUser",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2,
            code_execution_config={"use_docker": False},
            function_map=integration.function_map
        )
        print("Created user proxy agent")
        
        # Run a simple chat with timeout
        print("\n=== Starting Simple Chat (60s timeout) ===")
        try:
            chat_result = await asyncio.wait_for(
                user_proxy.a_initiate_chat(
                    agent,
                    message="""Get the latest price for BTCUSDT and compare it to yesterday's price. 
Calculate the percentage change and tell me if the price has gone up or down."""
                ),
                timeout=timeout_seconds
            )
            print("\n=== Chat Completed Successfully ===")
            save_result(chat_result)
            
        except asyncio.TimeoutError:
            print(f"\n=== Chat timed out after {timeout_seconds} seconds ===")
            return
            
    except Exception as e:
        print(f"Error during test: {str(e)}")

def save_result(result):
    """Save test result to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/logs/minimal_test_{timestamp}.txt"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get the chat history if available
    chat_history = []
    if hasattr(result, 'chat_history'):
        chat_history = result.chat_history
    elif hasattr(result, 'messages'):
        chat_history = result.messages
    
    # Write chat history to text file in a readable format
    with open(output_file, "w") as f:
        f.write(f"Test completed at: {timestamp}\n\n")
        f.write(f"=== PRICE COMPARISON TEST ===\n\n")
        f.write(f"Total messages: {len(chat_history)}\n\n")
        
        # Track function calls for summary
        function_calls = []
        
        for i, message in enumerate(chat_history):
            sender = message.get('sender', 'Unknown')
            receiver = message.get('receiver', 'Unknown')
            content = message.get('content', 'No content')
            
            # Handle None values
            if content is None:
                content = "No content available"
            
            # Check if this is a function call
            if "Suggested function call:" in content:
                # Extract function name
                try:
                    func_name = content.split("Suggested function call:")[1].split("*****")[0].strip()
                    function_calls.append(func_name)
                except:
                    pass
            
            f.write(f"Message {i+1}: {sender} -> {receiver}\n")
            f.write("-" * 80 + "\n")
            f.write(content)
            f.write("\n\n" + "=" * 80 + "\n\n")
        
        # Add a summary section
        f.write("\n\n=== TEST SUMMARY ===\n")
        f.write(f"Total messages exchanged: {len(chat_history)}\n")
        f.write(f"Functions called: {', '.join(function_calls) if function_calls else 'None'}\n")
        f.write(f"Conversation turns: {len(chat_history) // 2}\n")
    
    print(f"Saved chat result to {output_file}")
    
    # Print message count for verification
    print(f"Total messages exchanged: {len(chat_history)}")
    
    # Print the last message if available
    if chat_history:
        last_message = chat_history[-1]
        print("\nLast message content:")
        if isinstance(last_message, dict) and 'content' in last_message:
            content = last_message['content']
            if content is not None:
                print(content[:500] + "..." if len(content) > 500 else content)
            else:
                print("No content available in the last message")

if __name__ == "__main__":
    # Increase timeout for more comprehensive analysis
    asyncio.run(run_test_with_timeout(120))