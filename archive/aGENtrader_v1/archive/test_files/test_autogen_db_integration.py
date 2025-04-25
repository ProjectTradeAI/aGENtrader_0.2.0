"""
Test script for AutoGen Database Integration

Tests the integration between AutoGen agents and the database retrieval tool.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

import autogen
from autogen import config_list_from_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure agents directory is in path
# Import create_speaker_llm_config for GroupChatManager
from agents.autogen_db_integration import create_speaker_llm_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        logger.error("OpenAI API key not found in environment variables")
        print("Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return None
    
    # Create config list for AutoGen - using gpt-3.5-turbo for faster response
    config_list = [
        {
            "model": "gpt-3.5-turbo",
            "api_key": openai_api_key,
        }
    ]
    
    print(f"Config list structure: {config_list}")
    
    # For compatibility, we're converting to a dict since get_integration expects a dict
    config_dict = {"model": "gpt-3.5-turbo", "api_key": openai_api_key}
    print(f"Config dict: {config_dict}")
    
    # Return as a dict to match get_integration expectations
    return config_dict

def save_test_results(results: Dict[str, Any], file_prefix: str = "autogen_db_test"):
    """Save test results to file"""
    # Create directory if it doesn't exist
    os.makedirs("data/test_results", exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/test_results/{file_prefix}_{timestamp}.json"
    
    # Save results to file
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to {filename}")

async def run_market_data_analysis_test():
    """Run a test of market data analysis with AutoGen integration"""
    from agents.database_retrieval_tool import get_db_tool
    from agents.autogen_db_integration import get_integration
    
    try:
        print("\n--- Starting market data analysis test ---")
        
        # Get database tool and available symbols
        print("Getting database tool...")
        db_tool = get_db_tool()
        
        print("Retrieving available symbols...")
        symbols = db_tool.get_available_symbols()
        print(f"Symbols retrieved: {symbols}, type: {type(symbols)}")
        
        if not symbols:
            print("No symbols available in the database")
            return
        
        print(f"First symbol: {symbols[0]}, type: {type(symbols[0])}")
        test_symbol = symbols[0]  # This is where the error might be occurring
        print(f"Using {test_symbol} for testing")
        
        # Set up OpenAI API config
        print("Setting up OpenAI API config...")
        config_list = setup_openai_config()
        print(f"Config list: {type(config_list)}")
        if not config_list:
            print("No OpenAI config available - exiting test")
            return
        
        # Initialize integration
        print("Initializing integration...")
        integration = get_integration(config_list)
        print(f"Integration type: {type(integration)}")
        
        try:
            print(f"\nIntegration keys: {integration.keys()}")
        except Exception as key_error:
            print(f"Error accessing integration keys: {str(key_error)}")
        
        # Import trading agent factory
        from agents.trading_agents import TradingAgentFactory
        
        print("\nCreating market analyst agent...")
        # Create market analyst agent using factory
        try:
            market_analyst = TradingAgentFactory.create_market_analyst()
            if market_analyst:
                print("Market analyst agent created successfully")
            else:
                print("Failed to create market analyst agent")
        except Exception as e:
            print(f"Error creating market analyst agent: {str(e)}")
            market_analyst = None
        
        print("\nCreating strategy advisor agent...")
        # Create strategy advisor agent using factory
        try:
            strategy_advisor = TradingAgentFactory.create_strategy_advisor()
            if strategy_advisor:
                print("Strategy advisor agent created successfully")
            else:
                print("Failed to create strategy advisor agent")
        except Exception as e:
            print(f"Error creating strategy advisor agent: {str(e)}")
            strategy_advisor = None
        
        # Set up user proxy agent with function map
        print("\nCreating user proxy agent...")
        # Create user proxy agent with function map from integration
        try:
            # Extract function map and specs from integration
            function_map = integration.get('function_map', {})
            function_specs = integration.get('function_specs', [])
            
            user_proxy = TradingAgentFactory.create_user_proxy(
                functions=function_specs,
                name="User"
            )
            
            if user_proxy:
                print("User proxy agent created successfully")
                # Register functions
                for func_name, func in function_map.items():
                    print(f"Registering function: {func_name}")
                    user_proxy.register_function(
                        function_map=({func_name: func})
                    )
            else:
                print("Failed to create user proxy agent")
        except Exception as e:
            print(f"Error creating user proxy agent: {str(e)}")
            user_proxy = None
        
        # Run a conversation with market data analysis
        query = f"""
            What is the current price of {test_symbol}? Also provide the main support and resistance levels.
            Use the get_latest_price and get_support_resistance functions to retrieve the data.
            Keep your answer brief and focused on the actual data.
            """
        print(f"\nSending query: \n{query}")
        
        # Check if we have both user_proxy and market_analyst before proceeding
        chat_history = []
        if user_proxy and market_analyst:
            # Start the conversation
            try:
                user_proxy.initiate_chat(market_analyst, message=query)
                # Save the conversation history
                chat_history = user_proxy.chat_messages[market_analyst]
                print("\nChat completed successfully!")
            except Exception as chat_error:
                print(f"Error during chat: {str(chat_error)}")
        else:
            print("Cannot initiate chat - agents not properly created")
        
        print("\nChat completed!")
        
        # Save test results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "market_data_analysis",
            "symbol": test_symbol,
            "conversation": chat_history
        }
        
        save_test_results(results)
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        print(f"\nError during test: {str(e)}")

async def run_trading_strategy_test():
    """Run a test of trading strategy recommendations with AutoGen integration"""
    from agents.database_retrieval_tool import get_db_tool
    from agents.autogen_db_integration import get_integration
    
    try:
        # Get database tool and available symbols
        db_tool = get_db_tool()
        symbols = db_tool.get_available_symbols()
        
        if not symbols:
            print("No symbols available in the database")
            return
        
        test_symbol = symbols[0]
        print(f"Using {test_symbol} for trading strategy testing")
        
        # Set up OpenAI API config
        config_list = setup_openai_config()
        if not config_list:
            return
        
        # Initialize integration
        integration = get_integration(config_list)
        
        # Import trading agent factory
        from agents.trading_agents import TradingAgentFactory
        
        # Create strategy advisor agent using factory
        strategy_advisor = TradingAgentFactory.create_strategy_advisor()
        print("Strategy advisor agent created successfully")
        
        # Set up user proxy agent with function map
        function_map = integration.get('function_map', {})
        function_specs = integration.get('function_specs', [])
        user_proxy = TradingAgentFactory.create_user_proxy(functions=function_specs)
        
        # Register functions
        for func_name, func in function_map.items():
            user_proxy.register_function(
                function_map=({func_name: func})
            )
        
        # Run a conversation with strategy recommendations
        query = f"""
            Based on the current market data for {test_symbol}, what trading strategy would you recommend?
            Provide specific entry and exit points, stop loss levels, and risk management advice.
            Use the database retrieval functions to get the actual market data.
            Show your work and explain your reasoning based on the data.
            """
        print(f"\nSending query: \n{query}")
        
        # Start the conversation
        user_proxy.initiate_chat(strategy_advisor, message=query)
        
        # Save the conversation history
        chat_history = user_proxy.chat_messages[strategy_advisor]
        
        print("\nStrategy chat completed!")
        
        # Save test results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "trading_strategy",
            "symbol": test_symbol,
            "conversation": chat_history
        }
        
        save_test_results(results, file_prefix="strategy_test")
        
    except Exception as e:
        logger.error(f"Error during strategy test: {str(e)}")
        print(f"\nError during strategy test: {str(e)}")

async def run_multi_agent_test():
    """Run a test with multiple agents collaborating on market analysis"""
    from agents.database_retrieval_tool import get_db_tool
    from agents.autogen_db_integration import get_integration
    
    try:
        # Get database tool and available symbols
        db_tool = get_db_tool()
        symbols = db_tool.get_available_symbols()
        
        if not symbols:
            print("No symbols available in the database")
            return
        
        test_symbol = symbols[0]
        print(f"Using {test_symbol} for multi-agent testing")
        
        # Set up OpenAI API config
        config_list = setup_openai_config()
        if not config_list:
            return
        
        # Initialize integration
        integration = get_integration(config_list)
        
        # Import trading agent factory and autogen
        from agents.trading_agents import TradingAgentFactory
        import autogen
        
        # Create agents using factory
        market_analyst = TradingAgentFactory.create_market_analyst({"name": "Technical_Analyst"})
        strategy_advisor = TradingAgentFactory.create_strategy_advisor({"name": "Strategy_Advisor"})
        
        # Create user proxy with code execution capabilities
        function_map = integration.get('function_map', {})
        function_specs = integration.get('function_specs', [])
        user_proxy = TradingAgentFactory.create_user_proxy(
            name="User",
            human_input_mode="NEVER",
            functions=function_specs,
            max_consecutive_auto_reply=10
        )
        
        # Register functions
        for func_name, func in function_map.items():
            user_proxy.register_function(
                function_map=({func_name: func})
            )
        
        # Create group chat and manager
        groupchat = autogen.GroupChat(
            agents=[market_analyst, strategy_advisor, user_proxy],
            messages=[],
            max_round=10
        )
        
        # Use a clean config without function tools for GroupChatManager
        speaker_llm_config = create_speaker_llm_config(config_list)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=speaker_llm_config)
        
        # Run a conversation with multiple agents
        query = f"""
            Let's perform a comprehensive analysis of {test_symbol}.
            
            Technical Analyst: Please analyze the current market data, including price trends, 
            support and resistance levels, and volume patterns.
            
            Strategy Advisor: Based on the Technical Analyst's findings, recommend a trading strategy
            with specific entry/exit points and risk management guidelines.
            
            Use the database retrieval functions to get actual market data for your analysis.
            """
        print(f"\nSending group query: \n{query}")
        
        # Start the conversation
        user_proxy.initiate_chat(manager, message=query)
        
        # Save the conversation history
        chat_history = user_proxy.chat_messages[manager]
        
        print("\nMulti-agent chat completed!")
        
        # Save test results
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "multi_agent_collaboration",
            "symbol": test_symbol,
            "conversation": chat_history
        }
        
        save_test_results(results, file_prefix="multi_agent_test")
        
    except Exception as e:
        logger.error(f"Error during multi-agent test: {str(e)}")
        print(f"\nError during multi-agent test: {str(e)}")

def main():
    """Main entry point"""
    print("\n=== Testing AutoGen Database Integration ===\n")
    
    # Create necessary directories
    os.makedirs("data/test_results", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    # Run market data analysis test
    asyncio.run(run_market_data_analysis_test())
    
    # Uncomment to run additional tests
    # asyncio.run(run_trading_strategy_test())
    # asyncio.run(run_multi_agent_test())
    
    print("\n=== Database Integration Test Complete ===")

if __name__ == "__main__":
    main()