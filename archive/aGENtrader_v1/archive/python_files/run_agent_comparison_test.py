#!/usr/bin/env python
"""
Agent Comparison Backtest

This script runs a side-by-side backtest comparing the performance of:
1. SimpleDecisionSession (optimized version)
2. Full MultiAgent DecisionSession

It allows us to evaluate whether the more complex multi-agent system
provides better trading decisions compared to our simpler implementation.
"""

import os
import sys
import json
import argparse
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join("data", "logs", f"agent_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    ]
)
logger = logging.getLogger("agent_comparison")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import decision sessions
from orchestration.simple_decision_session import SimpleDecisionSession
from orchestration.decision_session_fixed import DecisionSession as MultiAgentDecisionSession
from utils.market_data import MarketDataProvider
from utils.performance_tracker import PerformanceTracker
from utils.trading_simulator import TradingSimulator

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run a side-by-side comparison backtest of the simple and multi-agent decision systems")
    
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--start_date", default=None, help="Start date for backtest (YYYY-MM-DD)")
    parser.add_argument("--end_date", default=None, help="End date for backtest (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=7, help="Number of days to backtest (alternative to start/end dates)")
    parser.add_argument("--interval", default="1h", help="Time interval for market data")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital for the simulation")
    parser.add_argument("--position_size", type=float, default=0.5, help="Position size as a fraction of capital")
    parser.add_argument("--confidence_threshold", type=float, default=55.0, help="Minimum confidence level for taking action")
    parser.add_argument("--output_dir", default="data/results", help="Directory to save results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--max_trades", type=int, default=None, help="Maximum number of trades to execute (for testing)")
    parser.add_argument("--use_simple_only", action="store_true", help="Only run the simple decision session (for testing/comparison)")
    parser.add_argument("--use_multi_only", action="store_true", help="Only run the multi-agent decision session (for testing/comparison)")
    parser.add_argument("--simulate_api", action="store_true", help="Use simulated API responses for testing without OpenAI API")
    
    return parser.parse_args()

def setup_date_range(args) -> Tuple[datetime, datetime]:
    """
    Set up date range for backtest based on args
    
    Args:
        args: Command line arguments
        
    Returns:
        Tuple of (start_date, end_date)
    """
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        # Use days argument to calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    
    return start_date, end_date

def create_simulators(args, symbol: str) -> Dict[str, TradingSimulator]:
    """
    Create trading simulators for each session type
    
    Args:
        args: Command line arguments
        symbol: Trading symbol
        
    Returns:
        Dictionary of simulators for each session
    """
    simulators = {}
    
    # Create simple session simulator if requested
    if not args.use_multi_only:
        simple_config = {
            "confidence_threshold": args.confidence_threshold,
            "position_size": args.position_size,
            "simulate_api": args.simulate_api
        }
        
        simple_simulator = TradingSimulator(
            session_type="simple",
            symbol=symbol,
            initial_capital=args.capital,
            position_size=args.position_size,
            session_config=simple_config
        )
        simulators["simple"] = simple_simulator
    
    # Create multi-agent session simulator if requested
    if not args.use_simple_only:
        multi_config = {
            "confidence_threshold": args.confidence_threshold,
            "position_size": args.position_size,
            "max_turns": 10,
            "simulate_api": args.simulate_api
        }
        
        multi_simulator = TradingSimulator(
            session_type="multi-agent",
            symbol=symbol,
            initial_capital=args.capital,
            position_size=args.position_size,
            session_config=multi_config
        )
        simulators["multi-agent"] = multi_simulator
    
    return simulators

def prepare_market_data(
        data_provider: MarketDataProvider,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
    """
    Prepare market data for the backtest
    
    Args:
        data_provider: MarketDataProvider instance
        symbol: Trading symbol
        start_date: Start date
        end_date: End date
        interval: Time interval
        
    Returns:
        List of market data points
    """
    # Fetch data with indicators for the time range
    market_data = data_provider.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        include_indicators=True
    )
    
    if not market_data:
        logger.error(f"No market data available for {symbol} from {start_date} to {end_date}")
        return []
    
    logger.info(f"Loaded {len(market_data)} market data points for {symbol}")
    return market_data

def run_backtest(
        simulators: Dict[str, TradingSimulator],
        market_data: List[Dict[str, Any]],
        max_trades: Optional[int] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
    """
    Run the backtest simulation with all simulators
    
    Args:
        simulators: Dictionary of simulators by session type
        market_data: Market data for backtest
        max_trades: Maximum number of trades (for testing)
        verbose: Enable verbose output
        
    Returns:
        Results dictionary
    """
    results = {}
    
    # Track start time
    start_time = time.time()
    
    # For each simulator, run through the market data
    for session_type, simulator in simulators.items():
        logger.info(f"Starting backtest for {session_type} session")
        
        # Run simulation
        simulator_result = simulator.run_simulation(
            market_data=market_data,
            max_trades=max_trades,
            verbose=verbose
        )
        
        results[session_type] = simulator_result
    
    # Calculate total runtime
    total_runtime = time.time() - start_time
    
    # Add runtime information
    results["runtime"] = {
        "total_seconds": total_runtime,
        "formatted": f"{total_runtime:.2f} seconds"
    }
    
    return results

def save_results(results: Dict[str, Any], args, test_id: str) -> str:
    """
    Save backtest results to file
    
    Args:
        results: Backtest results
        args: Command line arguments
        test_id: Test ID (timestamp)
        
    Returns:
        Path to saved results file
    """
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate filename
    filename = f"agent_comparison_{args.symbol}_{test_id}.json"
    filepath = os.path.join(args.output_dir, filename)
    
    # Save results
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {filepath}")
    return filepath

def display_summary(results: Dict[str, Any]) -> None:
    """
    Display a summary of the backtest results
    
    Args:
        results: Backtest results
    """
    print("\n" + "="*80)
    print(f"AGENT COMPARISON BACKTEST RESULTS")
    print("="*80)
    
    if "runtime" in results:
        print(f"Total Runtime: {results['runtime']['formatted']}")
    
    print("\nPERFORMANCE COMPARISON:")
    print("-"*80)
    
    # Create comparison table
    headers = ["Metric", "Simple Session", "Multi-Agent Session"]
    data = []
    
    # Only include session types that exist in results
    headers = ["Metric"]
    if "simple" in results:
        headers.append("Simple Session")
    if "multi-agent" in results:
        headers.append("Multi-Agent Session")
    
    # Add performance metrics
    metrics = [
        ("Net Profit %", "net_profit_percent"),
        ("Net Profit $", "net_profit"),
        ("Win Rate", "win_rate"),
        ("Total Trades", "total_trades"),
        ("Winning Trades", "winning_trades"),
        ("Losing Trades", "losing_trades"),
        ("Avg Win %", "avg_win_percent"),
        ("Avg Loss %", "avg_loss_percent"),
        ("Max Drawdown %", "max_drawdown_percent")
    ]
    
    for label, key in metrics:
        row = [label]
        
        # Add values for each session type
        if "simple" in results:
            if key in results["simple"]["performance"]:
                value = results["simple"]["performance"][key]
                
                # Format based on metric type
                if "percent" in key:
                    row.append(f"{value:.2f}%")
                elif key == "win_rate":
                    row.append(f"{value:.2f}%")
                elif "net_profit" == key:
                    row.append(f"${value:.2f}")
                else:
                    row.append(str(value))
            else:
                row.append("N/A")
                
        if "multi-agent" in results:
            if key in results["multi-agent"]["performance"]:
                value = results["multi-agent"]["performance"][key]
                
                # Format based on metric type
                if "percent" in key:
                    row.append(f"{value:.2f}%")
                elif key == "win_rate":
                    row.append(f"{value:.2f}%")
                elif "net_profit" == key:
                    row.append(f"${value:.2f}")
                else:
                    row.append(str(value))
            else:
                row.append("N/A")
        
        data.append(row)
    
    # Print header
    header_fmt = "| {:<20} | {:<20} | {:<20} |"
    if len(headers) == 3:
        print(header_fmt.format(*headers))
    elif len(headers) == 2:
        print("| {:<20} | {:<20} |".format(*headers))
    
    # Print separator
    if len(headers) == 3:
        print("|" + "-"*22 + "|" + "-"*22 + "|" + "-"*22 + "|")
    elif len(headers) == 2:
        print("|" + "-"*22 + "|" + "-"*22 + "|")
    
    # Print data rows
    for row in data:
        if len(row) == 3:
            print(header_fmt.format(*row))
        elif len(row) == 2:
            print("| {:<20} | {:<20} |".format(*row))
    
    print("\n" + "="*80)

def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Generate test ID
    test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set up logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting agent comparison backtest for {args.symbol}")
    
    # Set up date range
    start_date, end_date = setup_date_range(args)
    logger.info(f"Backtest date range: {start_date} to {end_date}")
    
    # Create market data provider
    data_provider = MarketDataProvider()
    
    # Prepare market data
    market_data = prepare_market_data(
        data_provider=data_provider,
        symbol=args.symbol,
        start_date=start_date,
        end_date=end_date,
        interval=args.interval
    )
    
    if not market_data:
        logger.error("No market data available for backtest. Exiting.")
        return
    
    # Create simulators
    simulators = create_simulators(args, args.symbol)
    
    # Run backtest
    results = run_backtest(
        simulators=simulators,
        market_data=market_data,
        max_trades=args.max_trades,
        verbose=args.verbose
    )
    
    # Add test configuration to results
    results["config"] = {
        "symbol": args.symbol,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "interval": args.interval,
        "capital": args.capital,
        "position_size": args.position_size,
        "confidence_threshold": args.confidence_threshold,
        "test_id": test_id
    }
    
    # Save results
    results_file = save_results(results, args, test_id)
    
    # Display summary
    display_summary(results)
    
    logger.info(f"Backtest completed. Results saved to {results_file}")

if __name__ == "__main__":
    main()