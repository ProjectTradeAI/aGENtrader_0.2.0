#!/usr/bin/env python3
"""
Test Trading Agent Framework

This script tests the enhanced trading agent framework with improved database integration
and collaborative agent decision-making capabilities.
"""

import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_trading_framework")

# Import components
from agents.trading_agent_framework import TradingAgentFramework
from agents.database_retrieval_tool import get_db_tool, get_latest_price
from utils.test_logging import display_header, TestLogger

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key not found in environment variables.")
        print("Please set the OPENAI_API_KEY environment variable and try again.")
        return False
    return True

def display_decision(decision: Dict[str, Any]) -> None:
    """
    Display the trading decision in a formatted manner.
    
    Args:
        decision: The trading decision dictionary
    """
    print("\n" + "="*80)
    print(" TRADING DECISION ".center(80, "-"))
    print("="*80)
    
    # Get main decision components
    action = decision.get("decision", "UNKNOWN")
    symbol = decision.get("symbol", "Unknown")
    confidence = decision.get("confidence_score", 0)
    if isinstance(confidence, float):
        confidence = confidence * 100  # Convert to percentage if it's a 0-1 scale
        
    entry_price = decision.get("entry_price", "N/A")
    stop_loss = decision.get("stop_loss", "N/A")
    take_profit = decision.get("take_profit", "N/A")
    position_size = decision.get("position_size_percent", "N/A")
    time_horizon = decision.get("time_horizon", "N/A")
    reasoning = decision.get("reasoning", "No reasoning provided")
    
    # Format as currency if numeric
    for field in ["entry_price", "stop_loss", "take_profit"]:
        value = decision.get(field)
        if isinstance(value, (int, float)):
            decision[field] = f"${value:,.2f}"
    
    # Display basic info
    print(f"Action: {action} {symbol}")
    print(f"Confidence: {confidence:.1f}%")
    print(f"Entry Price: {decision.get('entry_price', 'N/A')}")
    
    if action != "HOLD":
        print(f"Stop Loss: {decision.get('stop_loss', 'N/A')}")
        print(f"Take Profit: {decision.get('take_profit', 'N/A')}")
        print(f"Position Size: {position_size}%")
    
    print(f"Time Horizon: {time_horizon}")
    print("\nReasoning:")
    print(f"{reasoning}")
    print("\n" + "="*80)

def test_sequential_decision(symbol: str = "BTCUSDT") -> None:
    """
    Test the trading agent framework's sequential decision process.
    
    Args:
        symbol: Trading symbol to analyze
    """
    display_header(f"Testing Trading Agent Framework - Sequential Process with {symbol}")
    
    if not check_openai_api_key():
        return
    
    # Set up test logger
    test_logger = TestLogger(log_dir="data/logs/framework_tests", prefix="sequential")
    test_start = datetime.now().isoformat()
    session_id = f"seq_{int(datetime.now().timestamp())}"
    
    # Log session start
    test_logger.log_session_start(
        "sequential",
        {
            "session_id": session_id,
            "symbol": symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Get current price for context
        latest_price_json = get_latest_price(symbol)
        if latest_price_json:
            latest_price_data = json.loads(latest_price_json)
            latest_price = latest_price_data.get("close", "unknown")
            price_str = f"${latest_price:,.2f}" if isinstance(latest_price, (int, float)) else latest_price
            print(f"Current price for {symbol}: {price_str}")
        
        # Create and initialize trading agent framework
        print("Initializing trading agent framework...")
        framework = TradingAgentFramework()
        
        # Initialize the system
        success = framework.initialize()
        if not success:
            print("Failed to initialize trading agent framework")
            test_logger.log_error("sequential", "Failed to initialize framework")
            return
        
        # Define the trading objective
        objective = f"Analyze current market conditions for {symbol} and determine the optimal trading strategy based on technical and global market analysis"
        
        # Run a sequential trading decision session
        print(f"Starting sequential decision session for {symbol}...")
        result = framework.run_sequential_session(symbol, objective)
        
        # Display the result
        if result["status"] == "success":
            decision = result["decision"]
            display_decision(decision)
            print(f"Session log saved to: {result['log_file']}")
            
            # Log the decision
            test_logger.log_decision("sequential", decision)
            
            # Log session end
            test_logger.log_session_end("sequential", {
                "session_id": session_id,
                "symbol": symbol,
                "status": "success",
                "log_file": result["log_file"],
                "decision": decision,
                "end_time": datetime.now().isoformat()
            })
        else:
            print(f"Error in trading session: {result.get('message', 'Unknown error')}")
            test_logger.log_error("sequential", result.get('message', 'Unknown error'))
    
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        print(traceback.format_exc())
        test_logger.log_error("sequential", str(e), {
            "traceback": traceback.format_exc(),
            "session_id": session_id
        })

def test_group_decision(symbol: str = "BTCUSDT") -> None:
    """
    Test the trading agent framework's group chat decision process.
    
    Args:
        symbol: Trading symbol to analyze
    """
    display_header(f"Testing Trading Agent Framework - Group Process with {symbol}")
    
    if not check_openai_api_key():
        return
    
    # Set up test logger
    test_logger = TestLogger(log_dir="data/logs/framework_tests", prefix="group")
    test_start = datetime.now().isoformat()
    session_id = f"group_{int(datetime.now().timestamp())}"
    
    # Log session start
    test_logger.log_session_start(
        "group",
        {
            "session_id": session_id,
            "symbol": symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Get current price for context
        latest_price_json = get_latest_price(symbol)
        if latest_price_json:
            latest_price_data = json.loads(latest_price_json)
            latest_price = latest_price_data.get("close", "unknown")
            price_str = f"${latest_price:,.2f}" if isinstance(latest_price, (int, float)) else latest_price
            print(f"Current price for {symbol}: {price_str}")
        
        # Create and initialize trading agent framework
        print("Initializing trading agent framework...")
        framework = TradingAgentFramework()
        
        # Initialize the system
        success = framework.initialize()
        if not success:
            print("Failed to initialize trading agent framework")
            test_logger.log_error("group", "Failed to initialize framework")
            return
        
        # Define the trading objective
        objective = f"Analyze current market conditions for {symbol} and determine the optimal trading strategy based on collaborative technical and global market analysis"
        
        # Run a group trading decision session
        print(f"Starting group chat decision session for {symbol}...")
        result = framework.run_group_session(symbol, objective)
        
        # Display the result
        if result["status"] == "success":
            decision = result["decision"]
            display_decision(decision)
            print(f"Session log saved to: {result['log_file']}")
            
            # Log the decision
            test_logger.log_decision("group", decision)
            
            # Log session end
            test_logger.log_session_end("group", {
                "session_id": session_id,
                "symbol": symbol,
                "status": "success",
                "log_file": result["log_file"],
                "decision": decision,
                "end_time": datetime.now().isoformat()
            })
        else:
            print(f"Error in trading session: {result.get('message', 'Unknown error')}")
            test_logger.log_error("group", result.get('message', 'Unknown error'))
    
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        print(traceback.format_exc())
        test_logger.log_error("group", str(e), {
            "traceback": traceback.format_exc(),
            "session_id": session_id
        })

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test the trading agent framework")
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                        help="Trading symbol to test (default: BTCUSDT)")
    parser.add_argument("--mode", type=str, choices=["sequential", "group", "both"], 
                        default="sequential",
                        help="Test mode: sequential, group, or both (default: sequential)")
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    if args.mode == "sequential" or args.mode == "both":
        test_sequential_decision(args.symbol)
    
    if args.mode == "group" or args.mode == "both":
        test_group_decision(args.symbol)

if __name__ == "__main__":
    main()