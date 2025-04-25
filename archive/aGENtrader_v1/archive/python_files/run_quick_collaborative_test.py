"""
Quick Collaborative Decision Test

This script runs a quick test of the collaborative decision agent with a shorter timeout.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Run a quick test of the collaborative decision agent"""
    try:
        # Import collaborative decision agent
        from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        
        # Check API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            return "Please set the OPENAI_API_KEY environment variable"
        
        # Symbol to analyze
        symbol = "BTCUSDT"
        
        print(f"\nQuick Collaborative Decision Test for {symbol}")
        print("="*50)
        
        # Create the collaborative decision framework with a shorter timeout
        framework = CollaborativeDecisionFramework(
            api_key=api_key,
            max_session_time=60  # Short 60-second timeout
        )
        
        # Create a very brief prompt for quick testing
        prompt = f"""
        This is a quick test of the {symbol} analysis system.
        
        As this is only a test run, please keep all responses extremely brief:
        
        1. MarketAnalyst: Just retrieve and state the latest price
        2. StrategyManager: Give a one-sentence strategy assessment 
        3. RiskManager: Provide a one-sentence risk assessment
        4. TradingDecisionAgent: Make a final trading decision in this EXACT format:
        
        ```json
        {{
          "decision": "BUY or SELL or HOLD",
          "asset": "{symbol}",
          "entry_price": 88000,
          "stop_loss": 87000,
          "take_profit": 90000,
          "confidence_score": 0.75,
          "reasoning": "Very brief explanation of your decision"
        }}
        ```
        
        THIS IS A TEST - all agents must be extremely concise.
        """
        
        # Run the decision session
        logger.info(f"Running quick collaborative decision session for {symbol}...")
        start_time = datetime.now()
        
        decision = framework.run_decision_session(symbol=symbol, prompt=prompt)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log the decision
        logger.info(f"Decision received in {duration:.1f} seconds: {decision.get('decision', 'ERROR')}")
        
        # Print formatted decision
        if "error" in decision:
            print(f"\nERROR: {decision['error']}")
        else:
            format_and_print_decision(decision)
        
        # Save the decision
        save_dir = "results"
        os.makedirs(save_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{save_dir}/quick_decision_{symbol.lower()}_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(decision, f, indent=2)
        
        print(f"\nDecision saved to: {filename}")
        print(f"Test completed in {duration:.1f} seconds")
        
        return "Quick collaborative decision test completed successfully!"
        
    except Exception as e:
        logger.error(f"Error in collaborative decision test: {str(e)}")
        return f"Error: {str(e)}"

def format_and_print_decision(decision: Dict[str, Any]) -> None:
    """Format and print a decision dictionary"""
    lines = [
        "\n" + "="*60,
        f"TRADING DECISION: {decision.get('decision', 'UNKNOWN')} {decision.get('asset', '')}",
        "="*60,
        f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%",
        f"Entry Price: ${decision.get('entry_price', 0):.2f}",
        f"Stop Loss: ${decision.get('stop_loss', 0):.2f}",
        f"Take Profit: ${decision.get('take_profit', 0):.2f}",
        "-"*60,
        "Reasoning:",
        decision.get("reasoning", "No reasoning provided"),
        "-"*60,
        f"Price at Analysis: ${decision.get('price_at_analysis', 0):.2f}",
        f"Timestamp: {decision.get('timestamp', 'Unknown')}",
        "="*60
    ]
    
    print("\n".join(lines))

if __name__ == "__main__":
    result = main()
    print(f"\n{result}")