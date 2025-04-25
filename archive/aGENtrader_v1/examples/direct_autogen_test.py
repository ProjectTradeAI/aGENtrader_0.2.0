"""
Direct AutoGen Database Test

This version sidesteps the normal function registration by embedding the functions
directly within the script, allowing us to verify that the basic AutoGen integration works.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the database integration components
try:
    from agents.database_integration import AgentDatabaseInterface
    database_available = True
    # Initialize the database interface
    db_interface = AgentDatabaseInterface()
    query_manager = db_interface.query_manager
    logger.info("Database connection initialized")
except ImportError as e:
    database_available = False
    logger.error(f"Failed to import database components: {str(e)}")
    db_interface = None
    query_manager = None

# Import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

# Function that directly accesses database (if available)
def get_bitcoin_price() -> str:
    """
    Get the latest Bitcoin price information from the database.
    """
    try:
        if not database_available or query_manager is None:
            # Fallback to hardcoded data if database is not available
            return "Database not available - this is simulated data only for testing function calls.\n\nBitcoin Price: $88,081.87"
        
        # Get the latest price from the database
        symbol = "BTCUSDT"
        latest_price = query_manager.get_latest_price(symbol)
        
        # Get market data for the last 24 hours
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        market_data = query_manager.get_market_data(
            symbol=symbol,
            interval="1h",
            start_time=yesterday,
            limit=24
        )
        
        result = f"## Bitcoin Price Information\n\n"
        result += f"**Symbol**: {symbol}\n"
        result += f"**Current Price**: ${latest_price:.2f}\n"
        
        # Calculate 24h change if we have enough data
        if market_data and len(market_data) > 0:
            earliest_close = market_data[-1].get('close', 0)
            if earliest_close > 0:
                change_24h = (latest_price - earliest_close) / earliest_close * 100
                result += f"**24h Change**: {change_24h:.2f}%\n"
        
        result += f"**Timestamp**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return result
    
    except Exception as e:
        logger.error(f"Error in get_bitcoin_price: {str(e)}")
        return f"Error retrieving Bitcoin price: {str(e)}"

# Function that gets technical indicators
def get_technical_indicators(symbol: str = "BTCUSDT") -> str:
    """
    Get technical indicators for a cryptocurrency.
    """
    try:
        if not database_available or query_manager is None:
            # Fallback data for testing function calls
            return "Database not available - this is simulated data only for testing function calls.\n\nRSI(14): 62.5\nMACD: Bullish momentum\nBollinger Bands: Price within bands"
        
        # Get technical indicator data from the database
        # Since we don't have a direct method for indicators, we'll use a combined approach
        result = f"## Technical Indicators for {symbol}\n\n"
        
        # Get the latest price
        latest_price = query_manager.get_latest_price(symbol)
        result += f"**Current Price**: ${latest_price:.2f}\n\n"
        
        # Get volatility (as a proxy for Bollinger Band width)
        try:
            volatility = query_manager.calculate_volatility(symbol, "1d", days=14)
            result += f"**Volatility (14D)**: {volatility:.2f}%\n"
            
            if volatility > 4.0:
                result += "Interpretation: High volatility, suggesting significant price swings\n\n"
            elif volatility > 2.0:
                result += "Interpretation: Moderate volatility, normal market conditions\n\n"
            else:
                result += "Interpretation: Low volatility, potential breakout ahead\n\n"
        except Exception as e:
            logger.warning(f"Could not calculate volatility: {str(e)}")
        
        # Get directional indicators from recent price action
        try:
            # Get recent price data to determine trend
            now = datetime.now()
            two_weeks_ago = now - timedelta(days=14)
            market_data = query_manager.get_market_data(
                symbol=symbol,
                interval="1d",
                start_time=two_weeks_ago,
                limit=14
            )
            
            if market_data and len(market_data) >= 10:
                # Simple trend calculation
                first_price = market_data[-1].get('close', 0)
                last_price = market_data[0].get('close', 0)
                
                if first_price > 0:
                    price_change = (last_price - first_price) / first_price * 100
                    
                    result += f"**14-Day Price Change**: {price_change:.2f}%\n"
                    if price_change > 10:
                        result += "Interpretation: Strong bullish trend\n\n"
                    elif price_change > 5:
                        result += "Interpretation: Moderate bullish trend\n\n"
                    elif price_change > 0:
                        result += "Interpretation: Slight bullish bias\n\n"
                    elif price_change > -5:
                        result += "Interpretation: Slight bearish bias\n\n"
                    elif price_change > -10:
                        result += "Interpretation: Moderate bearish trend\n\n"
                    else:
                        result += "Interpretation: Strong bearish trend\n\n"
        except Exception as e:
            logger.warning(f"Could not calculate trend indicators: {str(e)}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in get_technical_indicators: {str(e)}")
        return f"Error retrieving technical indicators: {str(e)}"

def run_direct_test():
    """Run a test with AutoGen and directly embedded functions"""
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        sys.exit(1)
    
    # Show that we have an API key (first/last 4 chars only)
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Define functions to register with the assistant
    function_map = {
        "get_bitcoin_price": get_bitcoin_price,
        "get_technical_indicators": get_technical_indicators
    }
    
    # Create the assistant agent
    assistant = AssistantAgent(
        name="CryptoAnalyst",
        system_message="You are an expert cryptocurrency market analyst. You can analyze Bitcoin price data and technical indicators.",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.2,
            "functions": [
                {
                    "name": "get_bitcoin_price",
                    "description": "Get the latest Bitcoin price information",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_technical_indicators",
                    "description": "Get technical indicators for a cryptocurrency",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., 'BTCUSDT')"
                            }
                        },
                        "required": []
                    }
                }
            ]
        }
    )
    
    # Register functions
    assistant.register_function(function_map=function_map)
    
    # Create the user proxy agent
    user = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=1
    )
    
    # Start the conversation
    user.initiate_chat(
        assistant,
        message="What is the current Bitcoin price and what do the technical indicators suggest about market direction?"
    )

if __name__ == "__main__":
    run_direct_test()