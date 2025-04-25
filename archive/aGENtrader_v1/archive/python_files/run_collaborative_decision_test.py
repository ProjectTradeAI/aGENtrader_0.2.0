"""
Collaborative Decision Agent Test

This script tests the collaborative decision-making framework where multiple
specialized agents work together to analyze market data and generate trading decisions.
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import collaborative decision agent
from agents.collaborative_decision_agent import CollaborativeDecisionFramework

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test collaborative decision-making framework")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                        help="Trading symbol to analyze (e.g., 'BTCUSDT')")
    
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo",
                        help="Language model to use (e.g., 'gpt-3.5-turbo', 'gpt-4')")
    
    parser.add_argument("--temperature", type=float, default=0.2,
                        help="Temperature for language model (0.0 to 1.0)")
    
    parser.add_argument("--save_dir", type=str, default="data/decisions",
                        help="Directory to save decisions")
    
    parser.add_argument("--timeout", type=int, default=120,
                        help="Maximum time for decision session in seconds")
    
    parser.add_argument("--custom_prompt", type=str, default=None,
                        help="Custom prompt to initiate the session")
    
    return parser.parse_args()

def save_decision(decision: Dict[str, Any], save_dir: str) -> str:
    """
    Save decision to a file
    
    Args:
        decision: Decision dictionary
        save_dir: Directory to save decision
        
    Returns:
        Path to saved file
    """
    # Create the save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    symbol = decision.get("symbol", "unknown").lower()
    filename = f"decision_{symbol}_{timestamp}.json"
    
    # Full path to the file
    file_path = os.path.join(save_dir, filename)
    
    # Save the decision to a JSON file
    with open(file_path, 'w') as f:
        json.dump(decision, f, indent=2)
    
    logger.info(f"Decision saved to: {file_path}")
    return file_path

def format_decision_output(decision: Dict[str, Any]) -> str:
    """
    Format decision for display
    
    Args:
        decision: Decision dictionary
        
    Returns:
        Formatted string
    """
    if "error" in decision:
        return f"ERROR: {decision.get('error', 'Unknown error')}"
    
    decision_type = decision.get("decision", "UNKNOWN")
    asset = decision.get("asset", "Unknown")
    confidence = decision.get("confidence_score", 0) * 100
    
    # Create formatted output
    output = [
        "=" * 50,
        f"TRADING DECISION: {decision_type} {asset}",
        "=" * 50,
        f"Confidence: {confidence:.1f}%",
        f"Entry Price: ${decision.get('entry_price', 0):.2f}",
        f"Stop Loss: ${decision.get('stop_loss', 0):.2f}",
        f"Take Profit: ${decision.get('take_profit', 0):.2f}",
        "-" * 50,
        "Reasoning:",
        decision.get("reasoning", "No reasoning provided"),
        "-" * 50,
        f"Price at Analysis: ${decision.get('price_at_analysis', 0):.2f}",
        f"Timestamp: {decision.get('timestamp', 'Unknown')}",
        "=" * 50
    ]
    
    return "\n".join(output)

def main():
    """Main entry point for the collaborative decision test"""
    args = parse_arguments()
    
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            return "Please set the OPENAI_API_KEY environment variable"
        
        # Create collaborative decision framework
        logger.info(f"Initializing collaborative decision framework with model: {args.model}")
        framework = CollaborativeDecisionFramework(
            api_key=api_key,
            llm_model=args.model,
            temperature=args.temperature,
            max_session_time=args.timeout
        )
        
        # Run decision session
        logger.info(f"Running decision session for {args.symbol}")
        decision = framework.run_decision_session(
            symbol=args.symbol,
            prompt=args.custom_prompt
        )
        
        # Save decision
        save_decision(decision, args.save_dir)
        
        # Format and print decision
        formatted_decision = format_decision_output(decision)
        print(formatted_decision)
        
        return "Collaborative decision test completed successfully"
        
    except Exception as e:
        logger.error(f"Error in collaborative decision test: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = main()
    logger.info(result)