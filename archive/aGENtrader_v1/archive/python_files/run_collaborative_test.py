"""
Collaborative Market Analysis Test Runner

Executes the collaborative market analysis agent test with proper logging and error handling.
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test utilities
from utils.test_logging import TestLogger, display_header

# Try to import the collaborative test module
try:
    from test_simplified_collaborative import test_simplified_collaborative
    collaborative_available = True
except ImportError:
    collaborative_available = False
    print("Warning: Simplified collaborative test module not available")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run collaborative market analysis test")
    
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCUSDT",
        help="Trading symbol to use for test (default: BTCUSDT)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/logs/current_tests",
        help="Directory to store test logs (default: data/logs/current_tests)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
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

def ensure_output_directories(output_dir: str) -> None:
    """Ensure output directories exist"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create log subdirectories
    os.makedirs(os.path.join(output_dir, "chat_logs"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "session_logs"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "results"), exist_ok=True)

def run_test(args) -> None:
    """Run the specified test"""
    # Skip if module not available
    if not collaborative_available:
        print("Error: Collaborative test module not available")
        print("Please ensure the test_simplified_collaborative.py file exists")
        sys.exit(1)
    
    # Display header
    display_header(f"Running Collaborative Market Analysis Test for {args.symbol}")
    
    # Create test logger
    test_logger = TestLogger(log_dir=args.output_dir)
    
    # Generate session ID and timestamps
    test_start = datetime.now().isoformat()
    session_id = f"collab_{int(time.time())}"
    
    # Log session start
    test_logger.log_session_start(
        "collaborative",
        {
            "session_id": session_id,
            "symbol": args.symbol,
            "start_time": test_start
        }
    )
    
    try:
        # Run the test
        print(f"Starting collaborative test for {args.symbol}...")
        test_simplified_collaborative(args.symbol)
        
        # Construct result
        result = {
            "session_id": session_id,
            "session_type": "collaborative",
            "symbol": args.symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # Log session end
        test_logger.log_session_end("collaborative", result)
        
        print(f"Test completed successfully")
        print(f"Session ID: {session_id}")
        print(f"Results saved to: {args.output_dir}")
    
    except Exception as e:
        error_message = str(e)
        
        # Construct error result
        error_result = {
            "session_id": session_id,
            "session_type": "collaborative",
            "symbol": args.symbol,
            "start_time": test_start,
            "end_time": datetime.now().isoformat(),
            "status": "error",
            "error": error_message
        }
        
        # Log session end with error
        test_logger.log_session_end("collaborative", error_result)
        
        print(f"Test failed: {error_message}")
        print(f"Session ID: {session_id}")
        print(f"Error logs saved to: {args.output_dir}")
        
        sys.exit(1)

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Check OpenAI API key
    if not check_openai_api_key():
        sys.exit(1)
    
    # Create output directories
    ensure_output_directories(args.output_dir)
    
    # Run the test
    run_test(args)

if __name__ == "__main__":
    main()