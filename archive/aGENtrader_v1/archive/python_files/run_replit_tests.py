#!/usr/bin/env python
"""
Replit-Optimized Testing Suite

A simplified version of the comprehensive testing suite optimized for the Replit environment.
Reduces API usage and execution time while still validating core functionality.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import test logging utilities
from utils.test_logging import TestLogger, display_header

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run Replit-optimized trading agent tests")
    
    parser.add_argument(
        "--test-type", 
        choices=["single", "simplified"],
        default="single",
        help="Type of test to run"
    )
    
    parser.add_argument(
        "--symbol", 
        default="BTCUSDT",
        help="Trading symbol to use for testing"
    )
    
    parser.add_argument(
        "--log-dir", 
        default="data/logs/replit_tests",
        help="Directory to store test logs"
    )
    
    parser.add_argument(
        "--max-turns", 
        type=int,
        default=3,
        help="Maximum conversation turns for agent interactions"
    )
    
    return parser.parse_args()

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        print("\n⚠️  OPENAI_API_KEY not found in environment variables.")
        
        # Prompt for key
        key = input("Enter your OpenAI API key to continue: ").strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
            logger.info("OpenAI API key manually provided")
            return True
        else:
            logger.error("No API key provided, tests cannot proceed")
            return False
    
    logger.info("OpenAI API key found in environment variables")
    return True

def run_single_agent_test(test_logger: TestLogger, symbol: str = "BTCUSDT", max_turns: int = 3) -> Dict[str, Any]:
    """
    Run single agent market analyst test with limited API usage
    
    Args:
        test_logger: Test logger instance
        symbol: Trading symbol
        max_turns: Maximum conversation turns
        
    Returns:
        Test results
    """
    session_id = f"single_agent_{int(time.time())}"
    
    test_logger.log_session_start("single_agent", {
        "session_id": session_id,
        "symbol": symbol,
        "description": "Testing Market Analyst agent in isolation"
    })
    
    try:
        import autogen
        from autogen import AssistantAgent, UserProxyAgent
        
        # Get API key
        api_key = os.environ.get("OPENAI_API_KEY")
        
        # Set up config with reduced tokens
        llm_config = {
            "seed": 42,
            "config_list": [{
                "model": "gpt-4",
                "api_key": api_key,
                "max_tokens": 1000  # Reduce max tokens to limit API usage
            }]
        }
        
        # Import database tools
        from agents.database_retrieval_tool import DatabaseRetrievalTool
        db_tool = DatabaseRetrievalTool()
        
        # Define the function map with only essential functions
        function_map = {
            "get_latest_price": db_tool.get_latest_price,
            "get_market_summary": db_tool.get_market_summary,
            "get_technical_indicators": db_tool.get_technical_indicators,
        }
        
        # Create the market analyst agent with simplified prompt
        analyst = AssistantAgent(
            name="MarketAnalyst",
            system_message=f"""You are a cryptocurrency market analyst focusing on {symbol}.
            You have access to market data through API functions.
            Keep your analysis brief and focused.
            Limit your API calls to only what's necessary.""",
            llm_config=llm_config
        )
        
        # Register function
        analyst.register_function(function_map=function_map)
        
        # Create user proxy agent
        user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False}
        )
        
        # Run a simplified analysis
        prompt = f"""
        Provide a brief market analysis for {symbol} with:
        1. Current price and trend
        2. Key technical signals
        3. Trading recommendation
        
        Use these functions sparingly:
        - get_latest_price("{symbol}")
        - get_market_summary("{symbol}", "1h")
        - get_technical_indicators("{symbol}")
        
        Keep your response under 300 words.
        """
        
        # Run chat with reduced max_turns
        result = user_proxy.initiate_chat(
            analyst,
            message=prompt,
            max_turns=max_turns  # Use provided max_turns
        )
        
        # Extract the response
        chat_history = result.chat_history
        
        # Save chat history to file
        chat_file = test_logger.save_chat_history(
            chat_history, 
            session_id,
            output_dir="data/logs/replit_tests/single_agent"
        )
        
        # Prepare and return results
        full_result = {
            "status": "success",
            "session_id": session_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "chat_history": chat_history,
            "chat_file": chat_file,
            "test_type": "single_agent"
        }
        
        # Save full result
        result_file = test_logger.save_full_session(
            full_result,
            session_id,
            output_dir="data/logs/replit_tests/single_agent"
        )
        
        # Update with file path
        full_result["result_file"] = result_file
        
        test_logger.log_session_end("single_agent", full_result)
        return full_result
        
    except Exception as e:
        logger.error(f"Error in single agent test: {e}", exc_info=True)
        error_result = {
            "status": "error",
            "session_id": session_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "test_type": "single_agent"
        }
        test_logger.log_session_end("single_agent", error_result)
        return error_result

def run_simplified_collaborative_test(test_logger: TestLogger, symbol: str = "BTCUSDT", max_turns: int = 3) -> Dict[str, Any]:
    """
    Run extremely simplified collaborative test for Replit environment
    
    Args:
        test_logger: Test logger instance
        symbol: Trading symbol
        max_turns: Maximum conversation turns
        
    Returns:
        Test results
    """
    session_id = f"simplified_collab_{int(time.time())}"
    
    test_logger.log_session_start("simplified_collaborative", {
        "session_id": session_id,
        "symbol": symbol,
        "description": "Testing minimalist collaborative decision making"
    })
    
    try:
        import autogen
        from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
        
        # Get API key
        api_key = os.environ.get("OPENAI_API_KEY")
        
        # Set up config with reduced tokens
        llm_config = {
            "seed": 42,
            "config_list": [{
                "model": "gpt-4",
                "api_key": api_key,
                "max_tokens": 800  # Reduce max tokens to limit API usage
            }]
        }
        
        # Import database tools
        from agents.database_retrieval_tool import DatabaseRetrievalTool
        db_tool = DatabaseRetrievalTool()
        
        # Define the function map with only essential functions
        function_map = {
            "get_latest_price": db_tool.get_latest_price,
            "get_market_summary": db_tool.get_market_summary,
            "get_technical_indicators": db_tool.get_technical_indicators,
        }
        
        # Create simplified agents
        analyst = AssistantAgent(
            name="Analyst",
            system_message=f"""You are a market analyst for {symbol}. 
            Keep analysis brief and use data sparingly.""",
            llm_config=llm_config
        )
        
        strategy = AssistantAgent(
            name="Strategist",
            system_message=f"""You are a trading strategist for {symbol}.
            Recommend trade actions based on the analyst's insights.""",
            llm_config=llm_config
        )
        
        manager = AssistantAgent(
            name="Manager",
            system_message=f"""You are the decision manager who combines insights 
            to make a final trading decision for {symbol}.""",
            llm_config=llm_config
        )
        
        # Register functions with analyst only
        analyst.register_function(function_map=function_map)
        
        # Create user proxy agent
        user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False}
        )
        
        # Set up group chat
        agents = [user_proxy, analyst, strategy, manager]
        
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=max_turns
        )
        
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config
        )
        
        # Start the conversation
        prompt = f"""
        Conduct a quick trading analysis for {symbol} with:
        
        1. Analyst: Provide current price and key indicators using minimal API calls
        2. Strategist: Suggest a trade action based on the analysis
        3. Manager: Make a final decision with reasoning
        
        Keep all responses extremely brief and use API calls sparingly.
        Formulate a clear buy/sell/hold decision with confidence level.
        """
        
        # Run chat with reduced max_turns
        result = user_proxy.initiate_chat(
            manager, 
            message=prompt
        )
        
        # Extract the response
        chat_history = result.chat_history
        
        # Save chat history to file
        chat_file = test_logger.save_chat_history(
            chat_history, 
            session_id,
            output_dir="data/logs/replit_tests/simplified_collaborative"
        )
        
        # Prepare and return results
        full_result = {
            "status": "success",
            "session_id": session_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "chat_history": chat_history,
            "chat_file": chat_file,
            "test_type": "simplified_collaborative"
        }
        
        # Save full result
        result_file = test_logger.save_full_session(
            full_result,
            session_id,
            output_dir="data/logs/replit_tests/simplified_collaborative"
        )
        
        # Update with file path
        full_result["result_file"] = result_file
        
        test_logger.log_session_end("simplified_collaborative", full_result)
        return full_result
        
    except Exception as e:
        logger.error(f"Error in simplified collaborative test: {e}", exc_info=True)
        error_result = {
            "status": "error",
            "session_id": session_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "test_type": "simplified_collaborative"
        }
        test_logger.log_session_end("simplified_collaborative", error_result)
        return error_result

def run_tests(args):
    """Run specified tests with Replit optimization"""
    # Create log directory
    os.makedirs(args.log_dir, exist_ok=True)
    
    # Initialize test logger
    test_logger = TestLogger(args.log_dir, "replit_tests")
    
    # Display test header
    display_header(f"Running Replit-Optimized Testing Suite - {args.test_type.upper()}")
    print(f"Symbol: {args.symbol}")
    print(f"Log Directory: {args.log_dir}")
    print(f"Max Turns: {args.max_turns}")
    print(f"Started at: {datetime.now().isoformat()}")
    display_header("")
    
    # Check for API key
    if not check_openai_api_key():
        return
    
    # Store results
    results = {}
    
    # Run tests based on type
    if args.test_type == "single" or args.test_type == "all":
        display_header("Single Agent Test")
        results["single"] = run_single_agent_test(test_logger, args.symbol, args.max_turns)
    
    if args.test_type == "simplified" or args.test_type == "all":
        display_header("Simplified Collaborative Test")
        results["simplified"] = run_simplified_collaborative_test(test_logger, args.symbol, args.max_turns)
    
    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "test_type": args.test_type,
        "symbol": args.symbol,
        "results": results
    }
    
    summary_file = os.path.join(
        args.log_dir, 
        f"summary_{args.test_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Display completion message
    display_header("Test Completion Summary")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    for test_type, result in results.items():
        status = result.get("status", "unknown")
        status_icon = "✓" if status == "success" else "✗"
        session_id = result.get("session_id", "unknown")
        
        print(f"{status_icon} {test_type.capitalize()}: {status} (Session: {session_id})")
    
    print(f"\nSummary saved to: {summary_file}")
    print(f"\nTo view results, run: python view_test_results.py --log-dir {args.log_dir}")

def main():
    """Main entry point"""
    try:
        args = parse_arguments()
        run_tests(args)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()