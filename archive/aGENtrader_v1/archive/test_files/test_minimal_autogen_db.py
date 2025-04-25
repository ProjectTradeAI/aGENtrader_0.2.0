#!/usr/bin/env python3
"""
Minimal test script for AutoGen database integration

This script tests just the basic functionality with a timeout
to ensure it completes in a reasonable time.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("autogen_db_test")

try:
    import autogen
    from agents.database_retrieval_tool import get_db_tool
    from agents.autogen_db_integration import get_integration
except ImportError as e:
    logger.error(f"Error importing required modules: {str(e)}")
    sys.exit(1)

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return None
    
    config_list = [{"model": "gpt-3.5-turbo", "api_key": api_key}]
    return config_list

async def run_test_with_timeout(timeout_seconds=30):
    """Run a minimal test with timeout"""
    print("\n=== Running Minimal AutoGen DB Integration Test ===\n")
    
    try:
        # Get database tool
        db_tool = get_db_tool()
        print("Database tool initialized successfully")
        
        # Get available symbols
        symbols = db_tool.get_available_symbols()
        print(f"Available symbols: {symbols}")
        
        if not symbols:
            print("No symbols available in the database")
            return {"status": "error", "message": "No symbols available"}
        
        symbol = symbols[0]
        print(f"Testing with symbol: {symbol}")
        
        # Set up OpenAI config
        config_list = setup_openai_config()
        if not config_list:
            return {"status": "error", "message": "Failed to set up OpenAI config"}
        
        # Get integration with specific error handling
        try:
            # First, print the type of config_list
            print(f"Config list type: {type(config_list)}, value: {config_list}")
            
            # Try to get integration
            integration = get_integration(config_list)
            print(f"Integration initialized successfully, type: {type(integration)}")
            
            # Better debugging of integration structure
            if isinstance(integration, dict):
                print(f"Integration keys: {list(integration.keys())}")
                
                # Extract components
                function_map = integration["function_map"]
                print(f"Function map type: {type(function_map)}")
                print(f"Function map keys: {list(function_map.keys())}")
                
                # Test a function from the function map directly
                if "get_latest_price" in function_map:
                    try:
                        test_result = function_map["get_latest_price"](symbol)
                        print(f"Direct function test - get_latest_price result: {test_result}")
                    except Exception as e:
                        print(f"Direct function test failed: {str(e)}")
                
                llm_config = integration["llm_config"]
                print(f"LLM config type: {type(llm_config)}")
            else:
                print(f"Unexpected integration type: {type(integration)}")
                # If not a dict, create safe defaults
                function_map = {}
                llm_config = {}
        except Exception as e:
            print(f"Error getting integration: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            # Create safe defaults
            function_map = {}
            llm_config = {}
        
        # Create a simple assistant agent
        market_analyst = autogen.AssistantAgent(
            name="Market_Analyst",
            llm_config=llm_config,
            system_message=f"""You are a cryptocurrency market analyst specialized in technical analysis.
            Your role is to analyze {symbol} market data and provide insights.
            Use the available functions to retrieve and analyze market data."""
        )
        
        # Define a safer termination message checker
        def safe_is_termination(msg):
            if not msg:
                return False
            content = msg.get("content")
            if not content:
                return False
            return "TERMINATE" in content
            
        # Create a simple user proxy agent with function calling capabilities
        user_proxy = autogen.UserProxyAgent(
            name="User_Proxy",
            human_input_mode="NEVER",
            is_termination_msg=safe_is_termination,
            function_map=function_map  # Pass the entire function map directly
        )
        
        # Start the conversation with a simple prompt
        prompt = f"What is the current price of {symbol}? Use the get_latest_price function."
        
        # Initialize the chat with timeout
        async def chat_with_timeout():
            try:
                # Add extra error handling around the initiate_chat call
                try:
                    print("Starting chat between User_Proxy and Market_Analyst")
                    user_proxy.initiate_chat(
                        market_analyst, 
                        message=prompt,
                        max_turns=3  # Limit the conversation to 3 turns for testing
                    )
                    print("Chat completed successfully")
                except Exception as chat_error:
                    print(f"Error during chat: {str(chat_error)}")
                    import traceback
                    traceback.print_exc()
                    raise chat_error
                
                # Return success results
                return {
                    "status": "success", 
                    "message": "Conversation completed successfully",
                    "conversation": user_proxy.chat_messages.get(market_analyst, [])
                }
            except Exception as e:
                print(f"Exception during conversation: {str(e)}")
                return {"status": "error", "message": f"Error during conversation: {str(e)}"}
        
        result = await asyncio.wait_for(chat_with_timeout(), timeout=timeout_seconds)
        return result
        
    except asyncio.TimeoutError:
        print(f"Test timed out after {timeout_seconds} seconds")
        return {"status": "timeout", "message": f"Test timed out after {timeout_seconds} seconds"}
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        return {"status": "error", "message": f"Error during test: {str(e)}"}

def save_result(result):
    """Save test result to file"""
    os.makedirs("data/test_results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/test_results/db_test_{timestamp}.json"
    
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            # Handle other non-serializable types
            try:
                return str(o)
            except:
                return "UNSERIALIZABLE_OBJECT"
    
    with open(filename, "w") as f:
        json.dump(result, f, indent=2, cls=CustomJSONEncoder)
    
    print(f"Test results saved to {filename}")
    return filename

async def main():
    """Main entry point"""
    # Run test with timeout
    result = await run_test_with_timeout(timeout_seconds=30)
    
    # Display success/failure status
    if result.get("status") == "success":
        print("\n✅ Test completed successfully!")
        
        # Display conversation summary if available
        conversation = result.get("conversation", [])
        if conversation:
            print("\nConversation summary:")
            for i, msg in enumerate(conversation[:3]):  # Show first 3 messages
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if content:
                        print(f"Message {i+1} from {role}: {content[:100]}...")
                    else:
                        print(f"Message {i+1} from {role}: [No content or function call]")
                else:
                    print(f"Message {i+1}: [Unexpected format: {type(msg)}]")
            
            if len(conversation) > 3:
                print(f"...and {len(conversation) - 3} more messages")
    else:
        print(f"\n❌ Test failed: {result.get('message')}")
    
    # Save results
    save_result(result)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())