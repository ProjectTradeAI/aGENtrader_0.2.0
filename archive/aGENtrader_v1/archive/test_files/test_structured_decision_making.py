"""
Test Structured Decision Making System

This script tests the structured decision making framework to ensure
it can successfully generate trading decisions based on market data.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure parent directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            f"data/logs/test_decision_making_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler()
    ]
)

def test_decision_extractor():
    """
    Test the decision extractor functionality.
    
    Returns:
        True if tests pass, False otherwise
    """
    try:
        from agents.structured_decision_extractor import test_decision_extraction
        
        logging.info("Testing decision extractor...")
        result = test_decision_extraction()
        
        if result:
            logging.info("Decision extractor tests passed!")
        else:
            logging.error("Decision extractor tests failed")
        
        return result
    
    except Exception as e:
        logging.error(f"Error testing decision extractor: {str(e)}")
        return False


def test_collaborative_framework(
    symbol: str = "BTCUSDT",
    interval: str = "1h"
) -> Optional[Dict[str, Any]]:
    """
    Test the collaborative trading framework.
    
    Args:
        symbol: Trading symbol to analyze
        interval: Time interval for analysis
        
    Returns:
        Trading decision dictionary or None if test fails
    """
    try:
        from agents.collaborative_trading_framework import CollaborativeTradingFramework
        
        logging.info(f"Testing collaborative framework with {symbol} at {interval} interval...")
        
        # Initialize framework with reduced max_consecutive_auto_reply for quicker testing
        framework = CollaborativeTradingFramework(max_consecutive_auto_reply=5)
        
        # Run a trading session
        decision = framework.run_trading_session(symbol, interval, full_output=True)
        
        # Check if decision contains error
        if "error" in decision:
            logging.error(f"Collaborative framework test failed: {decision['error']}")
            return None
        
        # Validate decision format
        required_fields = [
            "decision", "asset", "entry_price", "stop_loss", 
            "take_profit", "confidence_score", "reasoning"
        ]
        
        missing_fields = [field for field in required_fields if field not in decision]
        if missing_fields:
            logging.error(f"Decision missing required fields: {missing_fields}")
            return None
        
        logging.info("Collaborative framework test passed!")
        
        # Save the full conversation to a file
        if "conversation" in decision:
            conversation_file = f"data/logs/conversation_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(conversation_file, "w") as f:
                json.dump(decision["conversation"], f, indent=2)
            logging.info(f"Saved conversation to {conversation_file}")
            
            # Remove conversation from return value to avoid clutter
            del decision["conversation"]
        
        return decision
    
    except Exception as e:
        logging.error(f"Error testing collaborative framework: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_database_integration():
    """
    Test the database integration functionality.
    
    Returns:
        True if tests pass, False otherwise
    """
    try:
        from agents.database_retrieval_tool import query_market_data, get_market_statistics
        
        logging.info("Testing database integration...")
        
        # Test query_market_data function
        btc_data = query_market_data("BTCUSDT", "1h", limit=5, format_type="json")
        if not btc_data or "error" in btc_data:
            logging.error(f"Failed to query market data: {btc_data}")
            return False
        
        logging.info(f"Successfully queried market data")
        
        # Test get_market_statistics function
        btc_stats = get_market_statistics("BTCUSDT", "1d", days=7, format_type="json")
        if not btc_stats or "error" in btc_stats:
            logging.error(f"Failed to get market statistics: {btc_stats}")
            return False
        
        logging.info(f"Successfully retrieved market statistics")
        
        return True
    
    except Exception as e:
        logging.error(f"Error testing database integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(symbol: str = "BTCUSDT", interval: str = "1h") -> None:
    """
    Run all tests for the structured decision making system.
    
    Args:
        symbol: Trading symbol to analyze
        interval: Time interval for analysis
    """
    logging.info("Starting structured decision making system tests")
    
    # Test database integration
    db_test_result = test_database_integration()
    logging.info(f"Database integration test: {'PASSED' if db_test_result else 'FAILED'}")
    
    if not db_test_result:
        logging.warning("Skipping remaining tests due to database integration failure")
        return
    
    # Test decision extractor
    extractor_test_result = test_decision_extractor()
    logging.info(f"Decision extractor test: {'PASSED' if extractor_test_result else 'FAILED'}")
    
    # Test collaborative framework
    decision = test_collaborative_framework(symbol, interval)
    
    if decision:
        logging.info(f"Collaborative framework test: PASSED")
        logging.info("\n===== TRADING DECISION =====")
        logging.info(f"Decision: {decision['decision']}")
        logging.info(f"Asset: {decision['asset']}")
        logging.info(f"Entry Price: {decision['entry_price']}")
        logging.info(f"Stop Loss: {decision['stop_loss']}")
        logging.info(f"Take Profit: {decision['take_profit']}")
        logging.info(f"Confidence: {decision['confidence_score']:.2f}")
        logging.info(f"Reasoning: {decision['reasoning']}")
        logging.info("============================\n")
    else:
        logging.info(f"Collaborative framework test: FAILED")
    
    logging.info("Structured decision making system tests completed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Structured Decision Making System")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Time interval")
    parser.add_argument("--test_type", type=str, choices=["all", "extractor", "framework", "database"],
                       default="all", help="Type of test to run")
    args = parser.parse_args()
    
    # Make sure logs directory exists
    os.makedirs("data/logs", exist_ok=True)
    
    # Run specified test
    if args.test_type == "extractor":
        test_decision_extractor()
    elif args.test_type == "framework":
        test_collaborative_framework(args.symbol, args.interval)
    elif args.test_type == "database":
        test_database_integration()
    else:
        run_all_tests(args.symbol, args.interval)