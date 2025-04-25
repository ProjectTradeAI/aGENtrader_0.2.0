"""
Run Backtest with Local LLM Integration

This script runs a simplified backtest using local LLM for analysis agents
and OpenAI (if available) for decision agents.
"""

import os
import sys
import json
import time
import logging
import argparse
import importlib.util
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/backtest_local_llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("backtest_local_llm")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run backtest with local LLM integration')
    
    parser.add_argument(
        '--symbol',
        type=str,
        default='BTCUSDT',
        help='Trading symbol to backtest'
    )
    
    parser.add_argument(
        '--interval',
        type=str,
        default='1h',
        help='Trading interval (1m, 5m, 15m, 1h, 4h, 1d)'
    )
    
    parser.add_argument(
        '--start_date',
        type=str,
        default='2025-03-01',
        help='Start date for backtest (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end_date',
        type=str,
        default='2025-03-15',
        help='End date for backtest (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--initial_balance',
        type=float,
        default=10000.0,
        help='Initial account balance for trading'
    )
    
    parser.add_argument(
        '--risk_per_trade',
        type=float,
        default=0.02,
        help='Risk per trade as percentage of account (0.01 = 1%)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default='data/backtest_results',
        help='Directory to save backtest results'
    )
    
    parser.add_argument(
        '--use_mock_data',
        action='store_true',
        help='Use mock data if no database is available'
    )
    
    parser.add_argument(
        '--analysis_timeout',
        type=int,
        default=30,
        help='Timeout in seconds for local LLM analysis'
    )
    
    return parser.parse_args()

def setup_autogen_config(args):
    """
    Sets up AutoGen configuration with local LLM integration.
    
    Args:
        args: Command line arguments
    
    Returns:
        Dictionary with AutoGen configuration
    """
    # Check if autogen is available
    autogen_spec = importlib.util.find_spec("autogen")
    if autogen_spec is None:
        logger.error("AutoGen is not installed. Install it using 'pip install autogen-agentchat'")
        return None
    
    # Load the autogen module
    spec = importlib.util.find_spec("utils.llm_integration.autogen_integration")
    if spec is not None:
        try:
            module = importlib.util.module_from_spec(spec)
            if spec.loader and hasattr(spec.loader, 'exec_module'):
                spec.loader.exec_module(module)
            else:
                logger.error("Failed to load autogen_integration module: loader not available")
                return None
        except Exception as e:
            logger.error(f"Error loading autogen_integration module: {str(e)}")
            return None
        
        # Patch AutoGen to use our local LLM implementation
        AutoGenLLMConfig = module.AutoGenLLMConfig
        AutoGenLLMConfig.patch_autogen()
        
        # Set up config list
        config_list = AutoGenLLMConfig.get_autogen_config_list(timeout=args.analysis_timeout)
        
        return {
            "AutoGenLLMConfig": AutoGenLLMConfig,
            "config_list": config_list
        }
    else:
        logger.error("Could not find autogen_integration module")
        return None

def run_backtest(args):
    """
    Runs the backtest with local LLM integration.
    
    Args:
        args: Command line arguments
    
    Returns:
        Dictionary with backtest results
    """
    try:
        # Set up AutoGen config
        autogen_config = setup_autogen_config(args)
        if autogen_config is None:
            logger.error("Failed to set up AutoGen configuration")
            return None
        
        # Load the simplified backtest module
        spec = importlib.util.find_spec("utils.backtest.simplified_backtest")
        if spec is None:
            logger.error("Could not find simplified_backtest module")
            return None
        
        try:
            module = importlib.util.module_from_spec(spec)
            if spec.loader and hasattr(spec.loader, 'exec_module'):
                spec.loader.exec_module(module)
            else:
                logger.error("Failed to load simplified_backtest module: loader not available")
                return None
        except Exception as e:
            logger.error(f"Error loading simplified_backtest module: {str(e)}")
            return None
        
        # Run the backtest
        logger.info(f"Starting backtest for {args.symbol} from {args.start_date} to {args.end_date}")
        start_time = time.time()
        
        backtest_results = module.run_backtest(
            symbol=args.symbol,
            interval=args.interval,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_balance=args.initial_balance,
            risk_per_trade=args.risk_per_trade,
            use_mock_data=args.use_mock_data,
            autogen_config=autogen_config
        )
        
        end_time = time.time()
        logger.info(f"Backtest completed in {end_time - start_time:.2f} seconds")
        
        # Save results
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(
            args.output_dir,
            f"backtest_local_llm_{args.symbol}_{args.interval}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w') as f:
            json.dump(backtest_results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        return backtest_results
        
    except Exception as e:
        logger.error(f"Error in run_backtest: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)
    
    # Run backtest
    results = run_backtest(args)
    
    if results:
        # Print summary
        print("\n========== BACKTEST RESULTS ==========")
        print(f"Symbol: {args.symbol}, Interval: {args.interval}")
        print(f"Period: {args.start_date} to {args.end_date}")
        print(f"Initial Balance: ${args.initial_balance:.2f}")
        print(f"Final Balance: ${results['final_balance']:.2f}")
        print(f"Net Profit: ${results['net_profit']:.2f} ({results['return_pct']:.2f}%)")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Winning Trades: {results['winning_trades']}")
        print(f"Losing Trades: {results['losing_trades']}")
        print(f"Sharpe Ratio: {results.get('sharpe_ratio', 'N/A')}")
        print(f"Max Drawdown: {results.get('max_drawdown_pct', 'N/A')}%")
        print("=======================================")
        
        # Suggest next steps
        print("\nNext Steps:")
        print("1. Run 'python analyze_backtest_results.py --file " + 
              os.path.join(args.output_dir, os.path.basename(results['output_file'])) + 
              "' to analyze detailed performance metrics")
        print("2. Adjust risk parameters and rerun to compare results")
        print("3. Try different date ranges to test strategy robustness")
    else:
        print("\nBacktest failed. Check logs for details.")

if __name__ == "__main__":
    main()