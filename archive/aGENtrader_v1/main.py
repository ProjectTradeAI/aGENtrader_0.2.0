"""
Multi-Agent Trading System Entry Point

This file provides a simple entry point to the trading system.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/trading_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

def main():
    """Main entry point for the trading system"""
    try:
        from orchestration.decision_session import DecisionSession
        
        # Get symbol from command line if provided, otherwise use default
        symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
        logging.info(f"Starting decision session for {symbol}")
        
        # Initialize the decision session
        session = DecisionSession()
        
        # Run the decision
        result = session.run_decision(symbol)
        
        # Display the result
        print("\n===== Trading Decision =====")
        print(f"Symbol: {symbol}")
        print(f"Decision: {result.get('decision', 'No decision')}")
        print(f"Confidence: {result.get('confidence', 0)}")
        print(f"Entry Price: {result.get('entry_price', 'N/A')}")
        print(f"Stop Loss: {result.get('stop_loss', 'N/A')}")
        print(f"Take Profit: {result.get('take_profit', 'N/A')}")
        print(f"Position Size: {result.get('position_size', 'N/A')}")
        print("\nReasoning:")
        print(result.get('reasoning', 'No reasoning provided'))
        
        logging.info(f"Completed decision session for {symbol}")
        return 0
    
    except ImportError as e:
        logging.error(f"Import error: {str(e)}")
        print(f"Error: {str(e)}")
        print("The system may not be correctly installed or initialized.")
        return 1
    
    except Exception as e:
        logging.error(f"Error during execution: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the main function
    sys.exit(main())
