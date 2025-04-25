"""
Simple market analyst test using AutoGen with direct database function calls

This simplified test focuses on a single agent analyzing market data
with a limited set of messages to avoid timeout issues.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("analyst_test")

# Import database tools
from agents.database_retrieval_tool import (
    get_recent_market_data,
    get_latest_price,
    CustomJSONEncoder
)

# Try to import AutoGen
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
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

def test_market_analyst() -> Dict[str, Any]:
    """Test market analyst with simple database access"""
    display_header("Testing Market Analyst")
    
    if not AUTOGEN_AVAILABLE:
        logger.warning("Test running in simulation mode (AutoGen not available)")
        return {"status": "skipped", "reason": "AutoGen not available"}
    
    # Get OpenAI configuration
    config = setup_openai_config()
    if not config:
        logger.warning("Test skipped: No OpenAI API configuration available")
        return {"status": "skipped", "reason": "No OpenAI API configuration"}
    
    results = {"status": "success", "messages": []}
    
    try:
        # Create the assistant agent with function calling configured
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
        
        # Create the assistant agent
        assistant = AssistantAgent(
            name="MarketAnalyst",
            system_message="""You are a cryptocurrency market analyst specializing in technical analysis.
You have access to market data through function calls and MUST USE THEM to get real data.
DO NOT make up or invent price data - ALWAYS call the appropriate functions.

You should:
1. Call get_latest_price() to get current price information
2. Call get_recent_market_data() to analyze trends over multiple data points
3. Perform calculations only on data received from these functions
4. Make trading recommendations based on real price movements

Provide insights on price action, trends, and potential trading opportunities 
based ONLY on real data retrieved through these function calls.""",
            llm_config=llm_config
        )
        
        # Create a user proxy agent with function calling capabilities
        user_proxy = UserProxyAgent(
            name="TraderProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            function_map={
                "get_latest_price": get_latest_price,
                "get_recent_market_data": get_recent_market_data
            }
        )
        
        # Start the conversation with a specific question
        user_query = """Analyze the BTCUSDT market with these steps:
1. First, call get_latest_price("BTCUSDT") to retrieve the latest price data
2. Then, call get_recent_market_data("BTCUSDT", 5) to get the 5 most recent data points
3. Calculate the percentage change between the oldest and newest price
4. Analyze the trend direction (up, down, or sideways)
5. Provide a recommendation (buy, sell, or hold) based on this real data

DO NOT skip any of these steps. I need to verify that you're using the actual database functions."""
        
        # Initiate chat with termination messages to keep it short
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=user_query,
            max_turns=3  # Limit to avoid timeouts
        )
        
        # Record the messages
        for message in chat_result.chat_history:
            results["messages"].append({
                "role": message.get("role", "unknown"),
                "content": message.get("content", ""),
                "timestamp": datetime.now().isoformat()
            })
        
        return results
    
    except Exception as e:
        logger.error(f"Error testing market analyst: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "messages": results.get("messages", [])
        }
    
def save_results(results: Dict[str, Any]) -> str:
    """Save test results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/logs/analyst_test_{timestamp}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, cls=CustomJSONEncoder, indent=2)
    
    print(f"\nSaved results to {output_file}")
    return output_file

def main() -> None:
    """Main entry point"""
    try:
        # Test market analyst
        results = test_market_analyst()
        
        # Save the results
        save_results(results)
        
        # Display result summary
        if results["status"] == "success":
            print("\nTest completed successfully!")
            print(f"Recorded {len(results['messages'])} messages")
        else:
            print(f"\nTest failed: {results.get('reason', results.get('error', 'Unknown error'))}")
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    main()