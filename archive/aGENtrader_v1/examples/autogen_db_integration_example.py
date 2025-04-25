"""
AutoGen Database Integration Example

This script demonstrates how to integrate a database query agent with AutoGen.
This example contains detailed comments explaining each step of the process.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

# Import database query agent
try:
    from agents.database_query_agent import DatabaseQueryAgent
except ImportError:
    logger.error("Failed to import DatabaseQueryAgent. Make sure the module is in the path.")
    sys.exit(1)

# ==================================================================
# STEP 1: Define the database query functions and wrapper
# ==================================================================

# Initialize the database query agent
# This agent handles the connection to the database and provides
# methods to query market data and statistics
db_agent = DatabaseQueryAgent()

def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                     days: Optional[int] = None, format_type: str = 'json') -> str:
    """
    Query market data for a specific symbol.
    
    IMPORTANT: Notice that this function returns a string.
    All functions registered with AutoGen MUST return strings.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        limit: Number of data points to retrieve
        days: Number of days to look back (alternative to limit)
        format_type: Output format ('json', 'markdown', 'text')
        
    Returns:
        Formatted market data as a string
    """
    logger.info(f"Calling query_market_data with symbol={symbol}, interval={interval}, limit={limit}, days={days}, format_type={format_type}")
    
    # Call the DatabaseQueryAgent's method to retrieve the data
    # This abstracts all the database connection logic
    return db_agent.query_market_data(symbol, interval, limit, days, format_type)

def get_market_statistics(symbol: str, interval: str = '1d', 
                         days: int = 30, format_type: str = 'json') -> str:
    """
    Get market statistics for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days to look back
        format_type: Output format ('json', 'markdown', 'text')
        
    Returns:
        Formatted market statistics as a string
    """
    logger.info(f"Calling get_market_statistics with symbol={symbol}, interval={interval}, days={days}, format_type={format_type}")
    return db_agent.get_market_statistics(symbol, interval, days, format_type)

# ==================================================================
# STEP 2: Define the AutoGen function schemas for the LLM
# ==================================================================

def create_function_schemas():
    """
    Create function schemas for AutoGen.
    
    The function schemas define the parameters and descriptions for the functions
    that the LLM can call. These are used to generate proper function calls.
    
    Returns:
        List of function schema dictionaries
    """
    return [
        {
            "name": "query_market_data",
            "description": "Query historical market data for a trading symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol (e.g., 'BTCUSDT')"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of data points to retrieve"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (alternative to limit)"
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format ('json', 'markdown', 'text')"
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_market_statistics",
            "description": "Get market statistics (price range, volatility, etc.) for a trading symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol (e.g., 'BTCUSDT')"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval (e.g., '1h', '4h', '1d')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back"
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Output format ('json', 'markdown', 'text')"
                    }
                },
                "required": ["symbol"]
            }
        }
    ]

def main():
    """
    Demonstrate AutoGen database integration.
    
    This function shows the complete workflow of integrating a database
    with AutoGen, from defining the functions to registering them with
    the assistant and user agents, and finally running a query.
    """
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return "Please set the OPENAI_API_KEY environment variable"
    
    # Show API key info (first/last 4 chars only)
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # ==================================================================
    # STEP 3: Create the function map for registration
    # ==================================================================
    
    # The function_map maps function names to their implementations
    function_map = {
        "query_market_data": query_market_data,
        "get_market_statistics": get_market_statistics
    }
    
    # ==================================================================
    # STEP 4: Create and configure the assistant agent
    # ==================================================================
    
    # Get the function schemas
    functions = create_function_schemas()
    
    # Create the assistant agent with function calling capability
    assistant = AssistantAgent(
        name="MarketAnalyst",
        system_message="""You are an expert cryptocurrency market analyst.
        When asked about market data or statistics, use the appropriate functions to retrieve data.
        Analyze the data and provide detailed insights in a clear, concise manner.
        Always explain your reasoning and include technical factors that support your analysis.""",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.1,
            "functions": functions,  # Pass the function schemas to the LLM
        }
    )
    
    # ==================================================================
    # STEP 5: Register the functions with the assistant
    # ==================================================================
    
    # Register the functions with the assistant
    # This allows the assistant to execute the functions when called
    logger.info("Registering functions with the assistant")
    assistant.register_function(function_map=function_map)
    
    # ==================================================================
    # STEP 6: Create the user proxy agent
    # ==================================================================
    
    # Create the user proxy agent to handle function calls automatically
    # IMPORTANT: The user proxy MUST have access to the function_map to execute the functions
    user = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",  # No human input needed
        code_execution_config=False,  # We don't need code execution
        max_consecutive_auto_reply=3,  # Allow multiple auto-replies
        llm_config=False,  # No LLM needed for the user
        function_map=function_map  # Pass functions to user agent for execution
    )
    
    # ==================================================================
    # STEP 7: Define the query and start the conversation
    # ==================================================================
    
    # Format the query
    query = "Analyze the current price and volatility of BTC/USDT using hourly data for the past 24 hours."
    
    # Start the conversation with a timeout
    logger.info(f"Starting conversation with query: {query}")
    try:
        user.initiate_chat(
            assistant,
            message=query,
            timeout=30  # 30 second timeout
        )
    except TimeoutError:
        logger.warning("Conversation timed out after 30 seconds")
    
    # ==================================================================
    # STEP 8: Clean up resources
    # ==================================================================
    
    # Close the database connection
    db_agent.db_interface.query_manager.close()
    
    return "Example completed successfully"

if __name__ == "__main__":
    try:
        result = main()
        logger.info(result)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        # Make sure to clean up database connection
        try:
            db_agent.db_interface.query_manager.close()
        except:
            pass