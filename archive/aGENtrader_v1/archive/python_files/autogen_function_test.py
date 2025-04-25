"""
AutoGen Function Registration Test

This script tests the basic function registration functionality in AutoGen
using the latest recommended approaches.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

# Simple test functions
def add(a: int, b: int) -> str:
    """Add two numbers and return the result.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        String representation of the sum of a and b
    """
    result = a + b
    return f"The sum of {a} and {b} is {result}"

def get_weather(location: str = "San Francisco") -> str:
    """Get the weather for a location.
    
    Args:
        location: The location to get weather for
        
    Returns:
        Weather information as a string
    """
    # This is a mock function - in a real scenario, we would call a weather API
    if location.lower() == "san francisco":
        return "Sunny, 72°F"
    elif location.lower() == "new york":
        return "Partly cloudy, 65°F"
    elif location.lower() == "london":
        return "Rainy, 55°F"
    else:
        return f"Weather data not available for {location}"

def get_bitcoin_price() -> str:
    """Get the latest Bitcoin price.
    
    Returns:
        Bitcoin price information
    """
    # In a real scenario, we would query the database or an API
    return "Bitcoin Price: $88,081.87"

def main():
    """Test AutoGen function registration"""
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return "Please set the OPENAI_API_KEY environment variable"
    
    # Show API key info (first/last 4 chars only)
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Define the functions to register
    functions = [
        {
            "name": "add",
            "description": "Add two numbers and return the result",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                        "description": "First number"
                    },
                    "b": {
                        "type": "integer",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        },
        {
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get weather for"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_bitcoin_price",
            "description": "Get the latest Bitcoin price",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]
    
    # Create the assistant agent with function definitions
    assistant = AssistantAgent(
        name="FunctionTestAssistant",
        system_message="""You are a helpful assistant that can use functions to get information.
        When a user asks about the weather, Bitcoin price, or needs calculations, use the appropriate function.""",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.2,
            "functions": functions,
        }
    )
    
    # Define the function map
    function_map = {
        "add": add,
        "get_weather": get_weather,
        "get_bitcoin_price": get_bitcoin_price
    }
    
    # Register the functions with the assistant
    logger.info("Registering functions with the assistant")
    assistant.register_function(function_map=function_map)
    
    # Create the user proxy agent to handle function calls automatically
    user = UserProxyAgent(
        name="User",
        human_input_mode="NEVER", 
        code_execution_config=False,
        max_consecutive_auto_reply=5,  # Allow multiple auto-replies for all function calls
        llm_config=False,
        function_map=function_map  # Pass functions to user agent for execution
    )
    
    # Format the query
    query = "What's the weather in London? Also, what's the current Bitcoin price? Finally, what's 123 + 456?"
    
    # Start the conversation with a timeout
    logger.info(f"Starting conversation with query: {query}")
    try:
        user.initiate_chat(
            assistant,
            message=query,
            timeout=60  # 1 minute timeout
        )
    except TimeoutError:
        logger.warning("Conversation timed out after 60 seconds")
    
    return "Test completed"

if __name__ == "__main__":
    try:
        result = main()
        logger.info(result)
    except Exception as e:
        logger.error(f"Error: {str(e)}")