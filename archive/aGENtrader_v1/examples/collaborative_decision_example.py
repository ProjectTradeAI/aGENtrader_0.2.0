"""
Collaborative Decision Example

This example demonstrates how to use the collaborative decision agent
to generate trading decisions based on real-time market data.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add the root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_current_market_conditions(symbol: str) -> Dict[str, Any]:
    """
    Get current market conditions for a trading symbol
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Market conditions dictionary
    """
    try:
        # Import database modules
        from agents.database_integration import DatabaseQueryManager
        
        # Create database query manager
        db_manager = DatabaseQueryManager()
        
        # Get the latest price
        price = db_manager.get_latest_price(symbol)
        
        # Get market statistics
        stats = db_manager.get_price_statistics(symbol, interval="1h", days=7)
        
        # Get volatility
        volatility = db_manager.calculate_volatility(symbol, interval="1h", days=7)
        
        # Combine into market conditions
        conditions = {
            "symbol": symbol,
            "current_price": price,
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "volatility": volatility
        }
        
        # Clean up
        db_manager.close()
        
        return conditions
    
    except Exception as e:
        logger.error(f"Error getting market conditions: {str(e)}")
        return {"error": str(e)}

def run_collaborative_decision(symbol: str = "BTCUSDT", verbose: bool = True):
    """
    Run the collaborative decision agent
    
    Args:
        symbol: Trading symbol to analyze
        verbose: Whether to print verbose output
        
    Returns:
        Trading decision
    """
    try:
        # Import collaborative decision agent
        from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        
        # Check API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            return {"error": "No OpenAI API key found"}
        
        # Get market conditions for context
        if verbose:
            logger.info(f"Getting market conditions for {symbol}...")
        
        conditions = get_current_market_conditions(symbol)
        
        if "error" in conditions:
            logger.error(f"Error getting market conditions: {conditions['error']}")
            return {"error": f"Market data error: {conditions['error']}"}
        
        price = conditions.get("current_price")
        price_str = f"${price:.2f}" if price else "N/A"
        
        if verbose:
            logger.info(f"Current price for {symbol}: {price_str}")
        
        # Create the collaborative decision framework
        if verbose:
            logger.info("Creating collaborative decision framework...")
        
        framework = CollaborativeDecisionFramework(api_key=api_key)
        
        # Create a prompt with market context
        volatility = conditions.get("volatility", {}).get("daily_volatility", "N/A")
        stats = conditions.get("statistics", {})
        
        prompt = f"""
        Analyze the current market conditions for {symbol} trading at {price_str}.
        
        Market Context:
        - Current Price: {price_str}
        - 7-Day Daily Volatility: {volatility}
        - 7-Day Price Range: ${stats.get('min_price', 'N/A')} to ${stats.get('max_price', 'N/A')}
        - 7-Day Average Price: ${stats.get('avg_price', 'N/A')}
        
        Follow this structured process:
        1. MarketAnalyst: Begin by retrieving the latest market data and providing a technical analysis
        2. StrategyManager: Review the market analysis and assess which trading strategies are appropriate
        3. RiskManager: Evaluate the potential risks and suggest risk mitigation measures
        4. TradingDecisionAgent: Make a final trading decision in the required JSON format
        
        Use database query functions as needed to retrieve additional market data.
        """
        
        # Run the decision session
        if verbose:
            logger.info("Running collaborative decision session...")
        
        decision = framework.run_decision_session(symbol=symbol, prompt=prompt)
        
        if verbose:
            # Format decision for display
            formatted_decision = format_decision_for_display(decision)
            print(formatted_decision)
        
        return decision
    
    except Exception as e:
        logger.error(f"Error in collaborative decision: {str(e)}")
        return {"error": str(e)}

def format_decision_for_display(decision: Dict[str, Any]) -> str:
    """
    Format a decision dictionary for display
    
    Args:
        decision: Decision dictionary
        
    Returns:
        Formatted string
    """
    if "error" in decision:
        return f"ERROR: {decision['error']}"
    
    lines = [
        "=" * 60,
        f"TRADING DECISION: {decision.get('decision', 'UNKNOWN')} {decision.get('asset', '')}",
        "=" * 60,
        f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%",
        f"Entry Price: ${decision.get('entry_price', 0):.2f}",
        f"Stop Loss: ${decision.get('stop_loss', 0):.2f} ({calc_percentage(decision.get('entry_price', 0), decision.get('stop_loss', 0)):.2f}%)",
        f"Take Profit: ${decision.get('take_profit', 0):.2f} ({calc_percentage(decision.get('entry_price', 0), decision.get('take_profit', 0)):.2f}%)",
        f"Risk/Reward Ratio: {calc_risk_reward(decision):.2f}",
        "-" * 60,
        "Reasoning:",
        decision.get("reasoning", "No reasoning provided"),
        "-" * 60,
        f"Price at Analysis: ${decision.get('price_at_analysis', 0):.2f}",
        f"Timestamp: {decision.get('timestamp', 'Unknown')}",
        "=" * 60
    ]
    
    return "\n".join(lines)

def calc_percentage(base: float, target: float) -> float:
    """Calculate percentage difference"""
    if base == 0:
        return 0
    return ((target - base) / base) * 100

def calc_risk_reward(decision: Dict[str, Any]) -> float:
    """Calculate risk/reward ratio"""
    entry = decision.get('entry_price', 0)
    if entry == 0:
        return 0
        
    stop = decision.get('stop_loss', 0)
    target = decision.get('take_profit', 0)
    
    risk = abs(entry - stop)
    reward = abs(entry - target)
    
    if risk == 0:
        return 0
    
    return reward / risk

def main():
    """Main example function"""
    try:
        # Check API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            return "Please set the OPENAI_API_KEY environment variable"
        
        print("\nCollaborative Decision Agent Example")
        print("-----------------------------------\n")
        
        symbol = "BTCUSDT"  # Default symbol for testing
        
        # Use default symbol for automated testing
        print(f"Using default symbol: {symbol}")
        
        # Confirm to the user
        print(f"\nRunning collaborative decision for {symbol}...")
        print("This may take a minute or two to complete...\n")
        
        # Run the collaborative decision
        decision = run_collaborative_decision(symbol=symbol, verbose=True)
        
        if "error" in decision:
            return f"Error: {decision['error']}"
        
        # Save the decision to a file
        try:
            os.makedirs("data/examples", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/examples/decision_{symbol.lower()}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(decision, f, indent=2)
                
            print(f"\nDecision saved to: {filename}\n")
        except Exception as e:
            logger.warning(f"Could not save decision to file: {str(e)}")
        
        return "Example completed successfully!"
    
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = main()
    print(f"\n{result}")