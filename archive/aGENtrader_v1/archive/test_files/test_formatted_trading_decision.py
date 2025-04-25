"""
Formatted Trading Decision Test

Tests the multi-agent trading decision system with an emphasis on output format
and validation of the decision structure.
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("formatted_trading_decision")

# Import the decision session module
from orchestration.decision_session import DecisionSession

# Import database functions for accessing market data
from agents.database_retrieval_tool import (
    get_latest_price,
    get_market_summary,
    get_db_tool
)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles special types."""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def display_header(title: str):
    """Display formatted header"""
    width = 80
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width + "\n")

def display_decision(decision: Dict[str, Any]):
    """Display a formatted trading decision"""
    width = 80
    print("\n" + "=" * width)
    print(f" TRADING DECISION: {decision.get('action', 'UNKNOWN')} {decision.get('symbol', '')} ".center(width, "="))
    print("=" * width)
    
    print(f"\nSymbol: {decision.get('symbol', 'UNKNOWN')}")
    print(f"Action: {decision.get('action', 'UNKNOWN')}")
    print(f"Confidence: {decision.get('confidence', 0):.2f}%")
    print(f"Price: ${decision.get('price', 0):.2f}")
    print(f"Risk Level: {decision.get('risk_level', 'medium')}")
    
    print("\nReasoning:")
    print("-" * width)
    reasoning = decision.get('reasoning', 'No reasoning provided')
    # Format reasoning as multiple lines for better readability
    for line in reasoning.split("\n"):
        print(f"  {line}")
    
    print("-" * width)

def check_openai_api_key():
    """Check if OpenAI API key is available"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ OpenAI API key not found in environment variables")
        print("Please set the OPENAI_API_KEY environment variable and try again")
        return False
    return True

def save_decision(decision: Dict[str, Any], suffix: str = "") -> str:
    """Save decision to file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = "data/decisions"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    symbol = decision.get("symbol", "unknown")
    action = decision.get("action", "unknown")
    filename = f"{output_dir}/{timestamp}_{symbol}_{action.lower()}"
    if suffix:
        filename += f"_{suffix}"
    filename += ".json"
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(decision, f, indent=2, cls=CustomJSONEncoder)
    
    logger.info(f"Decision saved to {filename}")
    return filename

def validate_decision_format(decision: Dict[str, Any]) -> bool:
    """
    Validate if decision has the correct format with all required fields
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["action", "confidence", "price", "risk_level", "reasoning"]
    
    for field in required_fields:
        if field not in decision:
            logger.error(f"Missing required field in decision: {field}")
            return False
    
    # Validate action value
    valid_actions = ["BUY", "SELL", "HOLD"]
    if decision.get("action") not in valid_actions:
        logger.error(f"Invalid action value: {decision.get('action')}")
        return False
    
    # Validate confidence is a number between 0-100
    try:
        confidence = float(decision.get("confidence", 0))
        if confidence < 0 or confidence > 100:
            logger.error(f"Confidence should be between 0-100, got {confidence}")
            return False
    except:
        logger.error("Confidence is not a valid number")
        return False
    
    # Validate risk_level
    valid_risk_levels = ["low", "medium", "high"]
    if decision.get("risk_level", "").lower() not in valid_risk_levels:
        logger.error(f"Invalid risk level: {decision.get('risk_level')}")
        return False
    
    return True

def run_trading_decision_test(symbol: str = "BTCUSDT", validate: bool = True):
    """
    Run a full trading decision test
    
    Args:
        symbol: Trading symbol to analyze
        validate: Whether to validate decision format
    """
    display_header(f"Trading Decision Test for {symbol}")
    
    # Create output directories
    os.makedirs("data/logs/structured_decisions", exist_ok=True)
    os.makedirs("data/decisions", exist_ok=True)
    
    # Get the latest price for the symbol
    logger.info(f"Getting latest price for {symbol}")
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
    start_time = time.time()
    session = DecisionSession()
    result = session.run_session(symbol, current_price)
    end_time = time.time()
    
    if result.get("status") == "error":
        logger.error(f"Decision session failed: {result.get('error', 'Unknown error')}")
        print(f"❌ Decision session failed: {result.get('error', 'Unknown error')}")
        return
    
    # Display the decision
    decision = result.get("decision")
    if decision:
        display_decision(decision)
        
        # Validate decision format
        if validate:
            print("\nValidating decision format...")
            is_valid = validate_decision_format(decision)
            if is_valid:
                print("✅ Decision format is valid")
            else:
                print("❌ Decision format is invalid")
        
        # Save decision to file
        save_path = save_decision(decision)
        print(f"\nDecision saved to: {save_path}")
    else:
        print("\n❌ No decision was reached in the session")
    
    # Display session info
    print(f"\nSession ID: {result.get('session_id', 'Unknown')}")
    print(f"Session logs saved to data/logs/decisions")
    print(f"Session completed in {end_time - start_time:.2f} seconds")

def test_multi_symbol_decisions(symbols: List[str], max_symbols: int = 3):
    """
    Test trading decisions with multiple symbols
    
    Args:
        symbols: List of symbols to test
        max_symbols: Maximum number of symbols to test
    """
    display_header("Multi-Symbol Trading Decision Test")
    
    if not symbols:
        logger.error("No symbols provided")
        print("❌ Error: No symbols provided")
        return
    
    # Limit to max_symbols
    if len(symbols) > max_symbols:
        print(f"Limiting test to {max_symbols} symbols out of {len(symbols)}")
        symbols = symbols[:max_symbols]
    
    results = {}
    for symbol in symbols:
        print(f"\nRunning test for {symbol}...")
        
        # Get the latest price for the symbol
        price_json = get_latest_price(symbol)
        
        if not price_json:
            logger.error(f"Failed to get price data for {symbol}")
            results[symbol] = {
                "status": "error",
                "error": "Failed to get price data"
            }
            continue
        
        # Parse the JSON response
        price_data = json.loads(price_json)
        current_price = float(price_data["close"])
        
        # Run the decision session
        session = DecisionSession()
        result = session.run_session(symbol, current_price)
        
        if result.get("status") == "error":
            logger.error(f"Decision session failed for {symbol}: {result.get('error')}")
            results[symbol] = {
                "status": "error",
                "error": result.get("error")
            }
            continue
        
        # Store decision
        decision = result.get("decision")
        if decision:
            results[symbol] = {
                "status": "success",
                "action": decision.get("action"),
                "confidence": decision.get("confidence"),
                "risk_level": decision.get("risk_level")
            }
            
            # Save decision to file
            save_decision(decision, suffix="multi")
        else:
            results[symbol] = {
                "status": "error",
                "error": "No decision reached"
            }
    
    # Display summary
    display_header("Multi-Symbol Test Summary")
    
    for symbol, result in results.items():
        if result.get("status") == "success":
            action = result.get("action")
            confidence = result.get("confidence")
            risk = result.get("risk_level")
            print(f"{symbol}: {action} (Confidence: {confidence:.1f}%, Risk: {risk})")
        else:
            print(f"{symbol}: ❌ {result.get('error', 'Unknown error')}")

def get_available_symbols(max_count: int = 5) -> List[str]:
    """
    Get available symbols from the database
    
    Args:
        max_count: Maximum number of symbols to return
        
    Returns:
        List of available symbols
    """
    try:
        # Use the DatabaseRetrievalTool class to get symbols
        db_tool = get_db_tool()
        symbols = db_tool.get_available_symbols()
        
        # Limit to max_count
        if symbols and len(symbols) > max_count:
            return symbols[:max_count]
        return symbols if symbols else ["BTCUSDT"]
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        return ["BTCUSDT"]  # Default on error

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test multi-agent trading decisions with format validation")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol to analyze")
    parser.add_argument("--multi", action="store_true", help="Test with multiple symbols")
    parser.add_argument("--max-symbols", type=int, default=3, help="Maximum number of symbols for multi-symbol test")
    parser.add_argument("--no-validate", action="store_true", help="Skip decision format validation")
    return parser.parse_args()

def main():
    """Main entry point"""
    if not check_openai_api_key():
        return
    
    args = parse_arguments()
    
    try:
        if args.multi:
            symbols = get_available_symbols(args.max_symbols)
            test_multi_symbol_decisions(symbols, args.max_symbols)
        else:
            run_trading_decision_test(args.symbol, not args.no_validate)
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()