"""
Simple AutoGen Database Test

A simplified test case to debug integration issues with AutoGen and the database functions.
"""

import os
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simple_autogen_test")

# Import our database interface
from agents.database_integration import AgentDatabaseInterface

# Import AutoGen components
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    print("AutoGen package not found. Please install with 'pip install pyautogen'")
    import sys
    sys.exit(1)

def simple_database_query(query: str) -> str:
    """A simple function to query the database"""
    db_interface = AgentDatabaseInterface()
    try:
        # Use the database query manager to get market data
        data = db_interface.query_manager.get_market_data(symbol="BTCUSDT", interval="1h", limit=10)
        # Format as a simple table and return as a string
        result = "Recent BTCUSDT Market Data (1-hour intervals):\n"
        result += "\n| Timestamp | Open | High | Low | Close | Volume |\n"
        result += "|-----------|------|------|-----|-------|--------|\n"
        
        for record in data:
            ts = record.get("timestamp", "").replace("T", " ")[:19]
            result += f"| {ts} "
            result += f"| ${float(record.get('open', 0)):.2f} "
            result += f"| ${float(record.get('high', 0)):.2f} "
            result += f"| ${float(record.get('low', 0)):.2f} "
            result += f"| ${float(record.get('close', 0)):.2f} "
            result += f"| {float(record.get('volume', 0)):.1f} |\n"
            
        return result
    except Exception as e:
        return f"Error querying database: {str(e)}"

def run_simple_test():
    """Run a simple test with two agents"""
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return

    # Print API key info (just first/last 4 chars)
    print(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Create a simple assistant with the database function
    assistant = AssistantAgent(
        name="DatabaseAssistant",
        system_message="You are a helpful assistant with access to a cryptocurrency database.",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.2,
            "functions": [
                {
                    "name": "simple_database_query",
                    "description": "Function to query the cryptocurrency database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to run"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    )
    
    # Register function directly in the assistant's function_map instead
    assistant.register_function(
        function_map={
            "simple_database_query": simple_database_query
        }
    )
    
    # Create user proxy
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=1
    )
    
    # Run the chat
    user_proxy.initiate_chat(
        assistant,
        message="Can you show me some recent market data for Bitcoin?"
    )

if __name__ == "__main__":
    # Check for environment variables
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set the DATABASE_URL environment variable to your PostgreSQL connection string")
        import sys
        sys.exit(1)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set the OPENAI_API_KEY environment variable to your OpenAI API key")
        import sys
        sys.exit(1)
    
    # Run the test
    run_simple_test()