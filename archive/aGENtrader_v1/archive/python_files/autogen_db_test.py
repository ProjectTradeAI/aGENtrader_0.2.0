"""
AutoGen Database Integration Test

This script tests the integration of the database query functionality with AutoGen.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

# Import database query agent
try:
    from agents.database_query_agent import DatabaseQueryAgent
except ImportError:
    logger.error("Failed to import DatabaseQueryAgent. Make sure the module is in the path.")
    sys.exit(1)

# DB Query functions that will be registered with AutoGen
db_agent = DatabaseQueryAgent()

def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                     days: Optional[int] = None, format_type: str = 'json') -> str:
    """
    Query market data for a specific symbol.
    
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

def main():
    """Test AutoGen database integration"""
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return "Please set the OPENAI_API_KEY environment variable"
    
    # Show API key info (first/last 4 chars only)
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Define database functions for the assistant
    functions = [
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
    
    # Create function map for registration
    function_map = {
        "query_market_data": query_market_data,
        "get_market_statistics": get_market_statistics
    }
    
    # Create the assistant agent
    assistant = AssistantAgent(
        name="MarketAnalyst",
        system_message="""You are an expert cryptocurrency market analyst.
        When asked about market data or statistics, use the appropriate functions to retrieve data.
        Analyze the data and provide detailed insights in a clear, concise manner.
        Always explain your reasoning and include technical factors that support your analysis.""",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.1,
            "functions": functions,
        }
    )
    
    # Register functions with the assistant
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
    
    # Format the query - use a simple query that will complete quickly 
    query = "What was the latest closing price of BTC/USDT? Use query_market_data with interval='1h', limit=1, and format_type='markdown' to show the result."
    
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
    
    # Clean up
    db_agent.db_interface.query_manager.close()
    
    return "Test completed"

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