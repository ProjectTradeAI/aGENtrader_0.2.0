"""
Fixed AutoGen Database Test

This version properly integrates the database with AutoGen using a simpler approach.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the database interface
try:
    from agents.database_integration import DatabaseQueryManager, AgentDatabaseInterface
except ImportError as e:
    logger.error(f"Error importing database modules: {e}")
    sys.exit(1)

# Try to import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    logger.error("AutoGen package not found. Please install with 'pip install pyautogen'")
    sys.exit(1)

# Create a global database interface instance to be used by functions
db_query_manager = DatabaseQueryManager()

def get_market_data(symbol: str, interval: str = '1h', limit: int = 24) -> str:
    """
    Get market data for a specific symbol and interval.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        limit: Number of data points to retrieve
        
    Returns:
        A formatted string with market data
    """
    try:
        # Convert limit to int
        if isinstance(limit, str):
            try:
                limit = int(limit)
            except ValueError:
                limit = 24
        
        # Get market data
        data = db_query_manager.get_market_data(symbol=symbol, interval=interval, limit=limit)
        
        # Format as markdown table
        result = f"## Recent {symbol} Market Data ({interval} intervals)\n\n"
        result += "| Timestamp | Open | High | Low | Close | Volume |\n"
        result += "|-----------|------|------|-----|-------|--------|\n"
        
        for record in data:
            timestamp = record.get("timestamp", "")
            if timestamp and isinstance(timestamp, str):
                ts = timestamp.replace("T", " ")[:19]
            else:
                ts = "N/A"
                
            # Extract numeric values safely
            try:
                open_price = float(record.get("open", 0))
                high_price = float(record.get("high", 0))
                low_price = float(record.get("low", 0))
                close_price = float(record.get("close", 0))
                volume = float(record.get("volume", 0))
                
                result += f"| {ts} "
                result += f"| ${open_price:.2f} "
                result += f"| ${high_price:.2f} "
                result += f"| ${low_price:.2f} "
                result += f"| ${close_price:.2f} "
                result += f"| {volume:.1f} |\n"
            except (ValueError, TypeError) as e:
                result += f"| {ts} | Error parsing record: {e} |\n"
        
        return result
    except Exception as e:
        return f"Error retrieving market data: {str(e)}"

def get_price_statistics(symbol: str, interval: str = '1d', days: int = 30) -> str:
    """
    Get price statistics for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days to look back
        
    Returns:
        A formatted string with price statistics
    """
    try:
        # Convert days to int
        if isinstance(days, str):
            try:
                days = int(days)
            except ValueError:
                days = 30
        
        # Get price statistics
        stats = db_query_manager.get_price_statistics(symbol=symbol, interval=interval, days=days)
        
        # Format as markdown
        result = f"## {symbol} Price Statistics ({interval} intervals, last {days} days)\n\n"
        
        try:
            min_price = float(stats.get('min_price', 0))
            max_price = float(stats.get('max_price', 0))
            avg_price = float(stats.get('avg_price', 0))
            current_price = float(stats.get('current_price', 0))
            
            result += f"- **Minimum Price**: ${min_price:.2f}\n"
            result += f"- **Maximum Price**: ${max_price:.2f}\n"
            result += f"- **Average Price**: ${avg_price:.2f}\n"
            result += f"- **Current Price**: ${current_price:.2f}\n"
            
            # Calculate some additional metrics
            price_range = max_price - min_price
            range_percentage = (price_range / min_price) * 100 if min_price > 0 else 0
            current_vs_avg = ((current_price / avg_price) - 1) * 100
            
            result += f"- **Price Range**: ${price_range:.2f} ({range_percentage:.2f}%)\n"
            result += f"- **Current vs Average**: {current_vs_avg:.2f}%\n"
            
            return result
        except (ValueError, TypeError) as e:
            return f"Error processing statistics values: {e}"
    except Exception as e:
        return f"Error retrieving price statistics: {str(e)}"

def run_fixed_test():
    """Run a test with AutoGen agents and database functions"""
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return
    
    # Create function definitions for the assistant
    function_definitions = [
        {
            "name": "get_market_data",
            "description": "Get recent market data for a cryptocurrency symbol",
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
                    }
                },
                "required": ["symbol"]
            }
        },
        {
            "name": "get_price_statistics",
            "description": "Get price statistics for a cryptocurrency",
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
                    }
                },
                "required": ["symbol"]
            }
        }
    ]
    
    # Create the assistant agent
    assistant = AssistantAgent(
        name="DatabaseAssistant",
        system_message="""You are a helpful cryptocurrency market analysis assistant.
You have access to market data and statistics through database functions.
When analyzing market data, always look for trends and provide insights on:
1. Price movements and volatility
2. Current price relative to recent highs/lows
3. Trading volume changes

Always use the database functions to get real data before providing analysis.""",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.2,
            "functions": function_definitions
        }
    )
    
    # Register functions
    assistant.register_function(
        function_map={
            "get_market_data": get_market_data,
            "get_price_statistics": get_price_statistics
        }
    )
    
    # Create the user proxy agent
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=2
    )
    
    # Run the conversation
    user_proxy.initiate_chat(
        assistant,
        message="""I'd like to understand how Bitcoin has been performing recently.
Can you show me some recent price data and provide a brief analysis?"""
    )

if __name__ == "__main__":
    # Check for environment variables
    if not os.environ.get("DATABASE_URL"):
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Run the test
    run_fixed_test()