"""
Quick test for structured_decision_agent.py

A faster version of the test with a more focused objective
and shorter timeouts for demonstration purposes.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from agents.structured_decision_agent import StructuredDecisionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_quick_decision")

def run_quick_decision_test(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Run a quick decision test with a specific trading objective.
    
    Args:
        symbol: Trading symbol to test with
        
    Returns:
        Test result dictionary
    """
    logger.info(f"Running quick decision test for {symbol}")
    
    # Create manager with short timeout
    manager = StructuredDecisionManager(config={
        "log_dir": "test_outputs/quick_decisions",
        "model": "gpt-3.5-turbo-0125",
        "temperature": 0.1,
        "max_session_time": 120  # 2 minutes max
    })
    
    # Initialize
    initialized = manager.initialize()
    if not initialized:
        logger.error("Failed to initialize structured decision manager")
        return {"status": "error", "message": "Failed to initialize manager"}
    
    # Set a very specific objective to get a quicker response
    objective = f"Based ONLY on the most recent price action for {symbol}, make a QUICK trading decision with entry, exit and risk parameters. Focus on speed rather than exhaustive analysis."
    
    # Run trading session
    logger.info(f"Starting quick trading session with objective: {objective}")
    result = manager.run_trading_session(symbol, objective)
    
    # Process result
    if result["status"] == "success":
        decision = result["decision"]
        logger.info(f"Quick decision complete: {decision.get('decision', 'UNKNOWN')} {symbol}")
    else:
        logger.error(f"Quick decision failed: {result.get('message', 'Unknown error')}")
    
    return result

def main():
    """Run the quick decision test"""
    # Check OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    # Create output directory
    os.makedirs("test_outputs/quick_decisions", exist_ok=True)
    
    # Run test
    symbol = "BTCUSDT"
    print(f"Running quick decision test for {symbol}...")
    
    result = run_quick_decision_test(symbol)
    
    # Display result
    if result["status"] == "success":
        decision = result["decision"]
        print(f"\nDecision: {decision.get('decision', 'UNKNOWN')} {symbol}")
        print(f"Entry: ${decision.get('entry_price', 'N/A')}")
        print(f"Stop Loss: ${decision.get('stop_loss', 'N/A')}")
        print(f"Take Profit: ${decision.get('take_profit', 'N/A')}")
        print(f"Position Size: {decision.get('position_size_percent', 'N/A')}%")
        print(f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%")
        print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
        print(f"\nLog file: {result.get('log_file', 'Not available')}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()