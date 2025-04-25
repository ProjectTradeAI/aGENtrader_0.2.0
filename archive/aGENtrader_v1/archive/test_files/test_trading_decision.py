"""
Test script for trading decision system

Tests the structured agent decision-making sessions for trading decisions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("trading_decision")

# Import the decision session module
from orchestration.decision_session import DecisionSession

# Import database functions for initialization testing
from agents.database_retrieval_tool import get_latest_price

def display_header(title: str):
    """Display formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def display_decision(decision: Dict[str, Any]):
    """Display a formatted trading decision"""
    print("\n" + "=" * 80)
    print(f" TRADING DECISION: {decision.get('action', 'UNKNOWN')} {decision.get('symbol', '')} ".center(80, "="))
    print("=" * 80)
    
    print(f"\nSymbol: {decision.get('symbol', 'UNKNOWN')}")
    print(f"Action: {decision.get('action', 'UNKNOWN')}")
    print(f"Confidence: {decision.get('confidence', 0):.2f}%")
    print(f"Price: ${decision.get('price', 0):.2f}")
    print(f"Risk Level: {decision.get('risk_level', 'medium')}")
    
    print("\nReasoning:")
    print("-" * 80)
    reasoning = decision.get('reasoning', 'No reasoning provided')
    # Format reasoning as multiple lines for better readability
    for line in reasoning.split("\n"):
        print(f"  {line}")

def check_openai_api_key():
    """Check if OpenAI API key is available"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ OpenAI API key not found in environment variables")
        print("Please set the OPENAI_API_KEY environment variable and try again")
        return False
    return True

def test_decision_session():
    """Test the trading decision session"""
    display_header("Trading Decision Session Test")
    
    # Create output directories
    os.makedirs("data/logs/decisions", exist_ok=True)
    os.makedirs("data/decisions", exist_ok=True)
    
    # Create the decision session
    session = DecisionSession()
    
    # Get the latest price for the symbol
    symbol = "BTCUSDT"
    price_json = get_latest_price(symbol)
    
    if not price_json:
        logger.error(f"Failed to get price data for {symbol}")
        print(f"❌ Error: Failed to get price data for {symbol}")
        return
    
    # Parse the JSON response
    price_data = json.loads(price_json)
    current_price = float(price_data["close"])
    
    print(f"Running trading decision session for {symbol} at ${current_price}")
    
    # Run the decision session
    result = session.run_session(symbol, current_price)
    
    if result.get("status") == "error":
        logger.error(f"Decision session failed: {result.get('error', 'Unknown error')}")
        print(f"❌ Decision session failed: {result.get('error', 'Unknown error')}")
        return
    
    # Display the decision
    decision = result.get("decision")
    if decision:
        display_decision(decision)
    else:
        print("\n❌ No decision was reached in the session")
    
    print(f"\nSession ID: {result.get('session_id', 'Unknown')}")
    print(f"Session logs saved to data/logs/decisions")

def main():
    """Main entry point"""
    if not check_openai_api_key():
        return
    
    try:
        test_decision_session()
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()