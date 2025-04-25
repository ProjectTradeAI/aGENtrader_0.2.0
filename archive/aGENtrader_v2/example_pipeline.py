#!/usr/bin/env python3
"""
aGENtrader v2 Example Pipeline

This script demonstrates a complete pipeline using the aGENtrader v2 system:
- Generates a simulated market event
- Processes it through the agents
- Outputs the trading decision
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("example_pipeline")

# Import modules
from simulators.market_event_simulator import MarketEventSimulator
from orchestrator.core_orchestrator import CoreOrchestrator


def setup_environment() -> None:
    """Set up environment for the pipeline."""
    # Create necessary directories
    os.makedirs("data/simulated", exist_ok=True)
    os.makedirs("logs/decisions", exist_ok=True)
    
    logger.info("Environment set up successfully")


def run_single_event(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    event_type: str = "normal",
    seed: Optional[int] = None,
    output_dir: str = "data/simulated"
) -> Dict[str, Any]:
    """
    Run a single market event through the pipeline.
    
    Args:
        symbol: Trading symbol
        interval: Time interval
        event_type: Type of event
        seed: Random seed for reproducibility
        output_dir: Directory to save output files
        
    Returns:
        Dictionary with results
    """
    logger.info(f"Running pipeline for {symbol} at {interval} interval (event type: {event_type})")
    
    # Create simulator
    simulator = MarketEventSimulator(seed=seed)
    
    # Generate market event
    logger.info("Generating market event")
    market_event = simulator.generate_market_event(
        symbol=symbol,
        interval=interval,
        event_type=event_type
    )
    
    # Save market event to file
    event_file = os.path.join(output_dir, f"market_event_{symbol}_{interval}.json")
    simulator.save_to_file(market_event, event_file)
    logger.info(f"Market event saved to: {event_file}")
    
    # Create orchestrator
    logger.info("Initializing orchestrator")
    orchestrator = CoreOrchestrator()
    
    # Run analysis through orchestrator
    logger.info("Running analysis")
    start_time = time.time()
    results = orchestrator.run_analysis(symbol, interval)
    end_time = time.time()
    
    # Calculate runtime
    runtime = end_time - start_time
    logger.info(f"Analysis completed in {runtime:.2f} seconds")
    
    # Add runtime to results
    results["runtime"] = runtime
    
    # Save results to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join("logs/decisions", f"{symbol}_{timestamp}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to: {results_file}")
    
    # Return results
    return results


def run_batch(
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"],
    intervals: List[str] = ["1h", "4h"],
    event_types: List[str] = ["normal", "bullish", "bearish", "volatile"],
    num_runs: int = 5,
    output_dir: str = "data/simulated"
) -> List[Dict[str, Any]]:
    """
    Run a batch of market events through the pipeline.
    
    Args:
        symbols: List of trading symbols
        intervals: List of time intervals
        event_types: List of event types
        num_runs: Number of runs per combination
        output_dir: Directory to save output files
        
    Returns:
        List of result dictionaries
    """
    logger.info(f"Running batch of {len(symbols) * len(intervals) * len(event_types) * num_runs} events")
    
    # Create results list
    all_results = []
    
    # Loop through combinations
    for symbol in symbols:
        for interval in intervals:
            for event_type in event_types:
                for i in range(num_runs):
                    logger.info(f"Run {i+1}/{num_runs} for {symbol} at {interval} interval (event type: {event_type})")
                    
                    # Run single event
                    seed = i * 100 + symbols.index(symbol) * 10 + intervals.index(interval) + event_types.index(event_type)
                    results = run_single_event(
                        symbol=symbol,
                        interval=interval,
                        event_type=event_type,
                        seed=seed,
                        output_dir=output_dir
                    )
                    
                    # Add metadata
                    results["run_id"] = i + 1
                    
                    # Add to results list
                    all_results.append(results)
    
    # Calculate summary statistics
    total_runtime = sum(r["runtime"] for r in all_results)
    avg_runtime = total_runtime / len(all_results)
    
    # Print summary
    logger.info(f"Batch completed: {len(all_results)} events processed")
    logger.info(f"Total runtime: {total_runtime:.2f} seconds")
    logger.info(f"Average runtime per event: {avg_runtime:.2f} seconds")
    
    # Return results
    return all_results


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="aGENtrader v2 Example Pipeline")
    
    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "batch"],
        default="single",
        help="Mode to run (single event or batch)"
    )
    
    # Single mode options
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Trading symbol"
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1h",
        help="Time interval"
    )
    parser.add_argument(
        "--event-type",
        type=str,
        choices=["normal", "bullish", "bearish", "volatile", "low_liquidity"],
        default="normal",
        help="Type of event to simulate"
    )
    
    # Batch mode options
    parser.add_argument(
        "--num-runs",
        type=int,
        default=3,
        help="Number of runs per combination in batch mode"
    )
    
    # Common options
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/simulated",
        help="Directory to save output files"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
    args = parse_arguments()
    
    try:
        # Set up environment
        setup_environment()
        
        # Run in selected mode
        if args.mode == "single":
            # Run single event
            results = run_single_event(
                symbol=args.symbol,
                interval=args.interval,
                event_type=args.event_type,
                seed=args.seed,
                output_dir=args.output_dir
            )
            
            # Print decision
            if "decision" in results and results["decision"]:
                print("\nTrading Decision:")
                print(f"Action: {results['decision']['action']}")
                print(f"Pair: {results['decision']['pair']}")
                print(f"Confidence: {results['decision']['confidence']}")
                print(f"Reason: {results['decision']['reason']}")
            else:
                print("\nNo trading decision generated")
            
        else:  # batch mode
            # Define combinations for batch run
            symbols = ["BTCUSDT", "ETHUSDT"]
            intervals = ["1h", "4h"]
            event_types = ["normal", "bullish", "bearish", "volatile"]
            
            # Run batch
            all_results = run_batch(
                symbols=symbols,
                intervals=intervals,
                event_types=event_types,
                num_runs=args.num_runs,
                output_dir=args.output_dir
            )
            
            # Print summary
            decisions = [r["decision"]["action"] for r in all_results if "decision" in r and r["decision"]]
            buy_count = decisions.count("BUY")
            sell_count = decisions.count("SELL")
            hold_count = decisions.count("HOLD")
            
            print("\nBatch Summary:")
            print(f"Total events: {len(all_results)}")
            print(f"Decisions: BUY={buy_count}, SELL={sell_count}, HOLD={hold_count}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())