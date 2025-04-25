"""
Single agent test script

Tests just a single agent with a simple task to verify basic functionality
without the complexity of multi-agent interactions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def display_header(title: str) -> None:
    """Display formatted header"""
    separator = "=" * 80
    header = f"------------------ {title} ------------------"
    print("\n" + separator)
    print(header)
    print(separator)

def test_market_analyst():
    """Test market analyst agent alone"""
    try:
        import autogen
        from autogen import AssistantAgent, UserProxyAgent
        
        # Ensure we have API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY not found in environment")
            return
            
        # Set up config
        llm_config = {
            "seed": 42,
            "config_list": [{
                "model": "gpt-4",
                "api_key": api_key
            }]
        }
        
        # Import the agent functions from the database retrieval module directly
        from agents.database_retrieval_tool import (
            get_latest_price, 
            get_market_summary,
            get_recent_market_data,
            get_market_data_range,
            get_price_history,
            calculate_moving_average,
            calculate_rsi,
            find_support_resistance,
            detect_patterns,
            calculate_volatility
        )
        
        # Define the function map
        function_map = {
            "get_latest_price": get_latest_price,
            "get_market_summary": get_market_summary,
        }
        
        # Create the market analyst agent with function calling enabled
        analyst = AssistantAgent(
            name="MarketAnalyst",
            system_message="You are a cryptocurrency market analyst specializing in technical analysis. Use the provided functions to retrieve market data and provide insightful analysis.",
            llm_config={
                **llm_config,
                "functions": [
                    {
                        "name": "get_latest_price",
                        "description": "Get the latest price data for a cryptocurrency symbol",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "The symbol to get price for, e.g., 'BTCUSDT'"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "get_market_summary",
                        "description": "Get a comprehensive market summary for a cryptocurrency symbol",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string", 
                                    "description": "The symbol to analyze, e.g., 'BTCUSDT'"
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "The time interval, e.g., '1h', '15m'"
                                }
                            },
                            "required": ["symbol"]
                        }
                    }
                ]
            }
        )
        
        # Register functions with the agent
        analyst.register_function(function_map=function_map)
        
        # Create user proxy agent with function execution capability
        user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False},
            llm_config=None,
            function_map=function_map  # Provide the same function map to user proxy
        )
        
        # Display test header
        display_header("Testing Market Analyst Agent")
        
        # Run a simple analysis with focused prompt to limit data volume
        prompt = """
        Follow these steps:
        1. Use the function get_latest_price("BTCUSDT") to retrieve the latest price data.
        2. Based on this price data, provide a brief price analysis.
        3. Mention the current price and any recent price movement.
        
        Keep your analysis focused and under 150 words total.
        """
        
        # Send message
        print("UserProxy (to MarketAnalyst): " + prompt)
        print("\n" + "-" * 80)
        
        # Run chat with more turns to allow for function calling
        print("Starting chat with max_turns=3 to allow function execution...")
        result = user_proxy.initiate_chat(
            analyst,
            message=prompt,
            max_turns=3
        )
        
        # Save result
        if result and result.chat_history:
            response = result.chat_history[-1].get("content", "No response")
            print(f"\nMarketAnalyst response:\n{response}")
            
            # Save to file
            os.makedirs("data/logs/agent_conversations", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/logs/agent_conversations/analyst_test_{timestamp}.txt"
            
            with open(filename, "w") as f:
                f.write(f"PROMPT:\n{prompt}\n\nRESPONSE:\n{response}")
                
            print(f"\nTest output saved to: {filename}")
            
    except Exception as e:
        logger.error(f"Error in market analyst test: {e}", exc_info=True)
        print(f"Error: {str(e)}")

def main():
    """Main entry point"""
    test_market_analyst()

if __name__ == "__main__":
    main()