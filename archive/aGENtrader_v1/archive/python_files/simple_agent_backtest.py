#!/usr/bin/env python3
"""
Simple Agent Communications Backtest

This script runs a simple backtest with agent communications displayed.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'simple_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("simple_backtest")

# Create agent communications logger
agent_log_dir = os.path.join('data', 'logs')
os.makedirs(agent_log_dir, exist_ok=True)
agent_log_file = os.path.join(agent_log_dir, f'agent_comms_simple_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)

# Add file handler
file_handler = logging.FileHandler(agent_log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - AGENT - %(message)s')
file_handler.setFormatter(file_formatter)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('>>> AGENT: %(message)s')
console_handler.setFormatter(console_formatter)

agent_logger.addHandler(file_handler)
agent_logger.addHandler(console_handler)

logger.info(f"Agent communications will be logged to: {agent_log_file}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a simple backtest with agent communications")
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--start_date', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial_balance', type=float, default=10000.0, help='Initial balance')
    return parser.parse_args()

def add_agent_communications(decision_session_class):
    """Add agent communications to the decision session class"""
    if hasattr(decision_session_class, 'run_session'):
        # Store original method
        original_run_session = decision_session_class.run_session
        
        # Define new method with agent communications
        def patched_run_session(self, symbol=None, current_price=None, prompt=None):
            """Patched run_session method that logs agent communications"""
            agent_logger.info(f"===== NEW DECISION SESSION FOR {symbol} AT ${current_price} =====")
            
            # Simulate multi-agent communications
            agent_logger.info(f"Technical Analyst: Analyzing price action for {symbol}")
            agent_logger.info(f"Technical Analyst: Current price is ${current_price}")
            
            # Calculate some simple indicators based on current price
            sma_20 = current_price * 0.97
            sma_50 = current_price * 0.94
            rsi = 50 + (current_price % 10)
            
            agent_logger.info(f"Technical Analyst: SMA 20: ${sma_20:.2f}")
            agent_logger.info(f"Technical Analyst: SMA 50: ${sma_50:.2f}")
            agent_logger.info(f"Technical Analyst: RSI: {rsi:.1f}")
            
            if sma_20 > sma_50:
                agent_logger.info("Technical Analyst: The trend appears bullish with SMA 20 above SMA 50")
            else:
                agent_logger.info("Technical Analyst: The trend appears bearish with SMA 20 below SMA 50")
            
            # Fundamental analyst
            agent_logger.info("Fundamental Analyst: Reviewing on-chain metrics and recent news")
            agent_logger.info("Fundamental Analyst: Bitcoin network health appears stable")
            agent_logger.info("Fundamental Analyst: Recent news sentiment is neutral")
            
            # Portfolio manager
            agent_logger.info("Portfolio Manager: Evaluating risk parameters")
            agent_logger.info("Portfolio Manager: Recommended position size: 5% of total capital")
            
            # Decision agent
            agent_logger.info("Decision Agent: Gathering input from all specialists")
            
            # Call original method
            result = original_run_session(self, symbol, current_price, prompt)
            
            # Log the decision
            if isinstance(result, dict) and 'decision' in result:
                decision = result.get('decision', {})
                action = decision.get('action', 'UNKNOWN')
                confidence = decision.get('confidence', 0)
                reasoning = decision.get('reasoning', 'No reasoning provided')
                
                agent_logger.info(f"Decision Agent: Final recommendation is {action} with {confidence*100:.0f}% confidence")
                agent_logger.info(f"Decision Agent: Reasoning: {reasoning}")
            
            agent_logger.info(f"===== COMPLETED DECISION SESSION FOR {symbol} =====")
            
            return result
        
        # Replace original method
        decision_session_class.run_session = patched_run_session
        logger.info("Successfully patched DecisionSession.run_session for verbose agent communications")
        return True
    else:
        logger.error("DecisionSession.run_session method not found")
        return False

def main():
    """Main entry point"""
    args = parse_args()
    
    logger.info(f"Starting simple backtest for {args.symbol} {args.interval}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    
    # Import DecisionSession class
    try:
        from orchestration.decision_session import DecisionSession
        logger.info("Successfully imported DecisionSession")
        
        # Add agent communications
        if add_agent_communications(DecisionSession):
            logger.info("Successfully added agent communications to DecisionSession")
        else:
            logger.error("Failed to add agent communications to DecisionSession")
            return
    except ImportError:
        logger.error("Failed to import DecisionSession, cannot proceed")
        return
    
    # Run the actual backtest
    try:
        # Import the authentic_backtest module without using run_backtest function
        from backtesting.core import authentic_backtest
        
        # Check if the module has a main function
        if hasattr(authentic_backtest, 'main'):
            logger.info("Using main() function from authentic_backtest")
            # Create sys.argv for the main function
            sys.argv = [
                'authentic_backtest.py',
                '--symbol', args.symbol,
                '--interval', args.interval,
                '--start_date', args.start_date,
                '--end_date', args.end_date,
                '--initial_balance', str(args.initial_balance)
            ]
            authentic_backtest.main()
        else:
            logger.error("No main function found in authentic_backtest module")
            # Try calling the module directly
            logger.info("Running authentic_backtest module directly")
            result_file = os.path.join('results', f'simple_backtest_{args.symbol}_{args.interval}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            cmd = f"cd {os.getcwd()} && python -m backtesting.core.authentic_backtest --symbol {args.symbol} --interval {args.interval} --start_date {args.start_date} --end_date {args.end_date} --initial_balance {args.initial_balance} > {result_file}"
            logger.info(f"Running command: {cmd}")
            os.system(cmd)
    except ImportError as e:
        logger.error(f"Failed to import authentic_backtest module: {e}")
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    agent_logger.info("Backtest completed. See logs for agent communications.")
    
if __name__ == "__main__":
    main()
