"""
Minimal Trading System Test

A simplified, minimal test of the trading system focusing on database integration
and basic agent functionality with a single agent.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("minimal_test")

# Import database tools
from agents.database_retrieval_tool import (
    get_latest_price,
    get_recent_market_data,
    CustomJSONEncoder
)

# Try to import AutoGen
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    logger.warning("AutoGen not available. Running in simulation mode.")
    AUTOGEN_AVAILABLE = False

def display_header(title: str) -> None:
    """Display a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def setup_openai_config() -> Optional[Dict[str, Any]]:
    """Set up OpenAI API configuration"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OpenAI API key found in environment variables")
        return None
    
    return {
        "model": "gpt-3.5-turbo-0125",
        "temperature": 0,
        "config_list": [{"model": "gpt-3.5-turbo-0125", "api_key": api_key}]
    }

async def test_minimal_trading_system():
    """Run a minimal test of the trading system"""
    display_header("Minimal Trading System Test")
    
    if not AUTOGEN_AVAILABLE:
        logger.warning("Test skipped: AutoGen not available")
        return {"status": "skipped", "reason": "AutoGen not available"}
    
    # Set up OpenAI config
    config = setup_openai_config()
    if not config:
        logger.warning("Test skipped: No OpenAI API configuration available")
        return {"status": "skipped", "reason": "No OpenAI API configuration"}
    
    # Trading symbol
    symbol = "BTCUSDT"
    
    try:
        # Directly call database functions to verify connectivity
        logger.info(f"Testing database connectivity for {symbol}...")
        
        # Get latest price
        latest_price_raw = get_latest_price(symbol)
        if not latest_price_raw:
            logger.error(f"Failed to get latest price for {symbol}")
            return {"status": "error", "reason": "Database connectivity issue"}
        
        # Parse JSON if it's a string
        if isinstance(latest_price_raw, str):
            try:
                latest_price = json.loads(latest_price_raw)
                logger.info("Successfully parsed latest price JSON")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse latest price JSON: {latest_price_raw}")
                if latest_price_raw.replace('.', '', 1).isdigit():
                    latest_price = {"close": float(latest_price_raw)}
                else:
                    latest_price = {"raw_response": latest_price_raw}
        else:
            latest_price = latest_price_raw
        
        if isinstance(latest_price, dict) and "close" in latest_price:
            logger.info(f"Latest price for {symbol}: Close = {latest_price['close']}")
        else:
            logger.info(f"Latest price for {symbol}: Raw data = {latest_price}")
        
        # Get recent market data
        recent_data_raw = get_recent_market_data(symbol, 3)
        if not recent_data_raw:
            logger.error(f"Failed to get recent market data for {symbol}")
            return {"status": "error", "reason": "Database retrieval issue"}
            
        # Parse JSON if it's a string
        if isinstance(recent_data_raw, str):
            try:
                recent_data = json.loads(recent_data_raw)
                logger.info("Successfully parsed recent market data JSON")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse recent market data JSON: {recent_data_raw}")
                recent_data = None
        else:
            recent_data = recent_data_raw
        
        # Special case handling: if we got a list directly instead of expected dict with "data" field
        if recent_data and isinstance(recent_data, list):
            logger.info("Response is a direct list, wrapping in standard format")
            recent_data = {"data": recent_data}
        
        if not recent_data or not isinstance(recent_data, dict) or "data" not in recent_data:
            logger.error(f"Failed to get recent market data for {symbol}")
            return {"status": "error", "reason": "Database retrieval issue"}
        
        logger.info(f"Retrieved {len(recent_data.get('data', []))} recent data points")
        
        # Create a market analyst agent with function calling
        llm_config = config.copy()
        llm_config.update({
            "functions": [
                {
                    "name": "get_latest_price",
                    "description": "Get the latest price data for a cryptocurrency symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading symbol, e.g., BTCUSDT"
                            }
                        },
                        "required": ["symbol"]
                    }
                },
                {
                    "name": "get_recent_market_data",
                    "description": "Get a list of recent market data points for a cryptocurrency symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The trading symbol, e.g., BTCUSDT"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of data points to retrieve"
                            }
                        },
                        "required": ["symbol", "limit"]
                    }
                }
            ]
        })
        
        display_header("Creating Agents for Basic Test")
        analyst = AssistantAgent(
            name="Analyst",
            system_message="""You are a cryptocurrency market analyst. Your task is to analyze market data and provide insights.
Use the get_latest_price and get_recent_market_data functions to access real market data.
Keep your analysis concise and focus on key metrics.""",
            llm_config=llm_config
        )
        
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,  # Prevent back-and-forth conversation
            function_map={
                "get_latest_price": get_latest_price,
                "get_recent_market_data": get_recent_market_data
            }
        )
        
        display_header("Running Basic Agent Test (Limited to 2 Turns)")
        
        # Use a simple, specific task that requires database access
        message = f"""Get the latest price for {symbol} and calculate the percentage change 
from the previous price point. Format your response as a brief analysis."""
        
        logger.info("Starting basic agent conversation...")
        try:
            # Set a timeout for the chat
            async def chat_with_timeout():
                return user_proxy.initiate_chat(
                    analyst,
                    message=message,
                    max_turns=2  # Strict limit to prevent long conversations
                )
            
            # Run the chat with a timeout
            chat_result = await asyncio.wait_for(chat_with_timeout(), timeout=60)
            
            # Save the results
            result = {
                "status": "success",
                "symbol": symbol,
                "chat_history": chat_result.chat_history if hasattr(chat_result, 'chat_history') else [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to file
            os.makedirs("data/logs/current_tests", exist_ok=True)
            output_file = f"data/logs/current_tests/minimal_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_file, "w") as f:
                json.dump(result, f, cls=CustomJSONEncoder, indent=2)
            
            logger.info(f"Test results saved to {output_file}")
            
            display_header("Test Completed Successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.error("Agent conversation timed out")
            return {"status": "error", "reason": "Conversation timeout"}
        except Exception as e:
            logger.error(f"Error during agent conversation: {str(e)}")
            return {"status": "error", "reason": str(e)}
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return {"status": "error", "reason": str(e)}

async def main():
    """Main entry point"""
    try:
        result = await test_minimal_trading_system()
        
        # Display status
        if result["status"] == "success":
            print("\n✅ Test completed successfully")
        elif result["status"] == "skipped":
            print(f"\n⏭️ Test skipped: {result.get('reason', 'Unknown reason')}")
        else:
            print(f"\n❌ Test failed: {result.get('reason', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())