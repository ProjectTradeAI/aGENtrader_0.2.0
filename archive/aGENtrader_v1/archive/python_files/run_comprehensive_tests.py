"""
Comprehensive Testing Suite

Runs a series of tests for the trading agent system with detailed logging
and session recording for further analysis.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test utilities
from utils.test_logging import TestLogger, display_header

# Try to import test modules (will be skipped if import fails)
try:
    from test_single_agent import test_market_analyst
    single_agent_available = True
except ImportError:
    single_agent_available = False
    print("Warning: Single agent test module not available")

try:
    from test_simplified_collaborative import test_simplified_collaborative
    simplified_collaborative_available = True
except ImportError:
    simplified_collaborative_available = False
    print("Warning: Simplified collaborative test module not available")

try:
    from test_collaborative_decision import test_collaborative_decision
    decision_available = True
except ImportError:
    decision_available = False
    print("Warning: Collaborative decision test module not available")

try:
    from test_trading_decision import test_decision_session
    trading_decision_available = True
except ImportError:
    trading_decision_available = False
    print("Warning: Trading decision test module not available")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for the trading system")
    
    parser.add_argument(
        "--tests",
        type=str,
        default="all",
        choices=["all", "single", "simplified", "decision", "collaborative"],
        help="Tests to run (default: all)"
    )
    
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Trading symbol to use for tests (default: BTCUSDT)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/logs/current_tests",
        help="Directory to store test logs (default: data/logs/current_tests)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds for each test (default: 600)"
    )
    
    return parser.parse_args()

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    if os.environ.get("OPENAI_API_KEY"):
        return True
    
    print("Error: OPENAI_API_KEY environment variable is not set")
    print("Please set the OPENAI_API_KEY environment variable and try again")
    print("Example: export OPENAI_API_KEY=your-api-key")
    return False

def run_single_agent_test(test_logger: TestLogger, symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Run single agent market analyst test
    
    Args:
        test_logger: Test logger instance
        symbol: Trading symbol
        
    Returns:
        Test results
    """
    if not single_agent_available:
        return {"status": "skipped", "reason": "Module not available"}
    
    display_header("Running Single Agent Market Analyst Test")
    
    test_start = datetime.now().isoformat()
    session_id = f"single_{int(time.time())}"
    
    # Log session start
    test_logger.log_session_start(
        "single_agent",
        {
            "session_id": session_id,
            "symbol": symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Run the test
        result = test_market_analyst()
        
        # Add session metadata
        result["session_id"] = session_id
        result["session_type"] = "single_agent"
        result["symbol"] = symbol
        result["start_time"] = test_start
        result["end_time"] = datetime.now().isoformat()
        result["status"] = "completed"
        
        # Log session end
        test_logger.log_session_end("single_agent", result)
        
        return result
    
    except Exception as e:
        error_result = {
            "session_id": session_id,
            "session_type": "single_agent",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }
        
        # Log session end with error
        test_logger.log_session_end("single_agent", error_result)
        
        return error_result

def run_simplified_collaborative_test(test_logger: TestLogger, symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Run simplified collaborative test
    
    Args:
        test_logger: Test logger instance
        symbol: Trading symbol
        
    Returns:
        Test results
    """
    if not simplified_collaborative_available:
        return {"status": "skipped", "reason": "Module not available"}
    
    display_header("Running Simplified Collaborative Test")
    
    test_start = datetime.now().isoformat()
    session_id = f"collab_simple_{int(time.time())}"
    
    # Log session start
    test_logger.log_session_start(
        "collaborative",
        {
            "session_id": session_id,
            "symbol": symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Run the test
        test_simplified_collaborative(symbol)
        
        # Construct result
        result = {
            "session_id": session_id,
            "session_type": "collaborative",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # Log session end
        test_logger.log_session_end("collaborative", result)
        
        return result
    
    except Exception as e:
        error_result = {
            "session_id": session_id,
            "session_type": "collaborative",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }
        
        # Log session end with error
        test_logger.log_session_end("collaborative", error_result)
        
        return error_result

def run_decision_session_test(test_logger: TestLogger, symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Run decision session test
    
    Args:
        test_logger: Test logger instance
        symbol: Trading symbol
        
    Returns:
        Test results
    """
    if not trading_decision_available:
        return {"status": "skipped", "reason": "Module not available"}
    
    display_header("Running Trading Decision Session Test")
    
    test_start = datetime.now().isoformat()
    session_id = f"session_{int(time.time())}"
    
    # Log session start
    test_logger.log_session_start(
        "decision",
        {
            "session_id": session_id,
            "symbol": symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Run the test
        test_decision_session()
        
        # Construct result
        result = {
            "session_id": session_id,
            "session_type": "decision",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # Log session end
        test_logger.log_session_end("decision", result)
        
        return result
    
    except Exception as e:
        error_result = {
            "session_id": session_id,
            "session_type": "decision",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }
        
        # Log session end with error
        test_logger.log_session_end("decision", error_result)
        
        return error_result

def run_collaborative_test(test_logger: TestLogger, symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Run full collaborative test
    
    Args:
        test_logger: Test logger instance
        symbol: Trading symbol
        
    Returns:
        Test results
    """
    if not decision_available:
        return {"status": "skipped", "reason": "Module not available"}
    
    display_header("Running Full Collaborative Decision Test")
    
    test_start = datetime.now().isoformat()
    session_id = f"collab_full_{int(time.time())}"
    
    # Log session start
    test_logger.log_session_start(
        "collaborative",
        {
            "session_id": session_id,
            "symbol": symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Run the test
        test_collaborative_decision(symbol)
        
        # Construct result
        result = {
            "session_id": session_id,
            "session_type": "collaborative",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # Log session end
        test_logger.log_session_end("collaborative", result)
        
        return result
    
    except Exception as e:
        error_result = {
            "session_id": session_id,
            "session_type": "collaborative",
            "symbol": symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }
        
        # Log session end with error
        test_logger.log_session_end("collaborative", error_result)
        
        return error_result

def run_tests(args):
    """Run specified tests"""
    # Create test logger
    test_logger = TestLogger(log_dir=args.output_dir)
    
    # Track overall results
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Run selected tests
    if args.tests == "all" or args.tests == "single":
        display_header("Single Agent Test")
        results["tests"]["single_agent"] = run_single_agent_test(test_logger, args.symbol)
    
    if args.tests == "all" or args.tests == "simplified":
        display_header("Simplified Collaborative Test")
        results["tests"]["simplified_collaborative"] = run_simplified_collaborative_test(
            test_logger, args.symbol
        )
    
    if args.tests == "all" or args.tests == "decision":
        display_header("Trading Decision Test")
        results["tests"]["decision_session"] = run_decision_session_test(
            test_logger, args.symbol
        )
    
    if args.tests == "all" or args.tests == "collaborative":
        display_header("Full Collaborative Test")
        results["tests"]["collaborative_decision"] = run_collaborative_test(
            test_logger, args.symbol
        )
    
    # Save overall results
    results_file = os.path.join(args.output_dir, f"comprehensive_results_{int(time.time())}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Display summary
    display_header("Test Summary")
    for test_name, test_result in results["tests"].items():
        status = test_result.get("status", "unknown")
        status_str = "✅ Success" if status == "completed" else f"❌ {status.capitalize()}"
        print(f"{test_name}: {status_str}")
    
    print("\nDetailed results saved to:", results_file)
    print("To view specific test results, run: python view_test_results.py")

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Check OpenAI API key
    if not check_openai_api_key():
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run tests
    run_tests(args)

if __name__ == "__main__":
    main()