"""
Trading System Test Runner

Executes trading system tests with proper timing and error handling.
This runner enables executing specific test components individually or all tests
in sequence with appropriate timeouts.
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"data/logs/current_tests/test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("test_runner")

# Check if the OpenAI API key is available
def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not found.")
        logger.error("Please set the OPENAI_API_KEY environment variable to run the tests.")
        return False
    return True

# Parse command line arguments
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run trading system tests")
    parser.add_argument(
        "--test", 
        choices=["single", "multi", "workflow", "all"], 
        default="all",
        help="Specify which test to run (single=single agent, multi=multi-agent, workflow=decision workflow, all=all tests)"
    )
    parser.add_argument(
        "--symbol", 
        type=str, 
        default="BTCUSDT",
        help="Trading symbol to use for tests"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=300,
        help="Timeout in seconds for each test"
    )
    parser.add_argument(
        "--log-dir", 
        type=str, 
        default="data/logs/current_tests",
        help="Directory for log files"
    )
    return parser.parse_args()

async def run_test_with_timeout(coro, timeout: int):
    """Run a test coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Test timed out after {timeout} seconds")
        return {"status": "error", "error": f"Test timed out after {timeout} seconds"}

async def run_selected_test(args):
    """Run the selected test(s)"""
    # Import the test harness
    try:
        from test_multi_agent_trading import MultiAgentTradingTest
    except ImportError as e:
        logger.error(f"Failed to import test harness: {e}")
        return 1
    
    # Create the test harness
    test_harness = MultiAgentTradingTest(log_dir=args.log_dir)
    test_harness.symbol = args.symbol
    
    if args.test == "single" or args.test == "all":
        logger.info(f"Running single agent analysis test for {args.symbol}")
        result = await run_test_with_timeout(
            test_harness.test_single_agent_analysis(),
            args.timeout
        )
        if args.test == "single":
            return 0 if result.get("status") == "success" else 1
    
    if args.test == "multi" or args.test == "all":
        logger.info(f"Running multi-agent collaboration test for {args.symbol}")
        result = await run_test_with_timeout(
            test_harness.test_multi_agent_collaboration(),
            args.timeout
        )
        if args.test == "multi":
            return 0 if result.get("status") == "success" else 1
    
    if args.test == "workflow" or args.test == "all":
        logger.info(f"Running decision workflow test for {args.symbol}")
        result = await run_test_with_timeout(
            test_harness.test_decision_workflow(),
            args.timeout
        )
        if args.test == "workflow":
            return 0 if result.get("status") == "success" else 1
    
    if args.test == "all":
        logger.info("All tests completed")
        return 0
    
    logger.error(f"Unknown test: {args.test}")
    return 1

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Ensure the log directory exists
    os.makedirs(args.log_dir, exist_ok=True)
    
    # Check if OpenAI API key is available
    if not check_openai_api_key():
        return 1
    
    logger.info(f"Starting trading system tests for {args.symbol}")
    logger.info(f"Log directory: {args.log_dir}")
    logger.info(f"Test timeout: {args.timeout} seconds")
    
    # Run the selected test
    return asyncio.run(run_selected_test(args))

if __name__ == "__main__":
    sys.exit(main())