#!/usr/bin/env python
"""
Offline Test Runner

Runs a simple offline test that doesn't require API calls but validates 
our testing framework setup.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import test logging utilities
from utils.test_logging import TestLogger, display_header

def run_offline_test(log_dir: str = "data/logs/offline_tests") -> None:
    """
    Run a simple offline test to validate the testing framework
    
    Args:
        log_dir: Directory to store test logs
    """
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Initialize test logger
    test_logger = TestLogger(log_dir, "offline_test")
    
    # Display test header
    display_header("Running Offline Test")
    print(f"Log Directory: {log_dir}")
    print(f"Started at: {datetime.now().isoformat()}")
    display_header("")
    
    # Generate a session ID
    session_id = f"offline_test_{int(time.time())}"
    
    # Log session start
    test_logger.log_session_start("offline_test", {
        "session_id": session_id,
        "description": "Testing logging framework without API calls"
    })
    
    try:
        # Simulate chat history
        chat_history = [
            {
                "sender": "System",
                "receiver": "MarketAnalyst",
                "content": "Initialize market analysis session",
                "timestamp": datetime.now().isoformat()
            },
            {
                "sender": "MarketAnalyst",
                "receiver": "UserProxy",
                "content": "I'm ready to analyze market data. What would you like me to focus on?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "sender": "UserProxy",
                "receiver": "MarketAnalyst",
                "content": "Please analyze recent price trends for BTCUSDT and provide a recommendation.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "sender": "MarketAnalyst",
                "receiver": "UserProxy",
                "content": """Based on simulated analysis of BTCUSDT:
                
                Current Price: $67,245.32
                
                Technical Analysis:
                - Moving Averages: Bullish
                - RSI: Neutral (52.4)
                - MACD: Weakly bullish
                
                Recommendation: HOLD
                - Support level: $65,800
                - Resistance level: $68,500
                
                The market is showing consolidation after recent gains. Wait for a clearer breakout signal.
                """,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Simulate market analysis
        market_analysis = {
            "symbol": "BTCUSDT",
            "timestamp": datetime.now().isoformat(),
            "price": 67245.32,
            "trend": "neutral",
            "signals": [
                {"indicator": "MA", "value": "bullish"},
                {"indicator": "RSI", "value": "neutral"},
                {"indicator": "MACD", "value": "weakly bullish"}
            ],
            "support": 65800,
            "resistance": 68500
        }
        
        # Simulate trading decision
        trading_decision = {
            "signal": "HOLD",
            "confidence": 0.68,
            "reasoning": "Market showing consolidation pattern after recent gains. Wait for clearer directional signal before entering new position.",
            "risk_level": "medium",
            "time_horizon": "short-term",
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None
        }
        
        # Save chat history
        chat_file = test_logger.save_chat_history(
            chat_history,
            session_id,
            output_dir=os.path.join(log_dir, "chat_logs")
        )
        
        # Prepare full result
        full_result = {
            "status": "success",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "chat_history": chat_history,
            "chat_file": chat_file,
            "market_analysis": market_analysis,
            "decision": trading_decision,
            "test_type": "offline_test"
        }
        
        # Save full result
        result_file = test_logger.save_full_session(
            full_result,
            session_id,
            output_dir=os.path.join(log_dir, "results")
        )
        
        # Update with file path
        full_result["result_file"] = result_file
        
        # Log session end
        test_logger.log_session_end("offline_test", full_result)
        
        # Display decision
        test_logger._print_decision(trading_decision)
        
        # Display completion message
        display_header("Test Completion Summary")
        print(f"Completed at: {datetime.now().isoformat()}")
        print(f"Status: success")
        print(f"Session ID: {session_id}")
        print(f"\nFull result saved to: {result_file}")
        print(f"Chat history saved to: {chat_file}")
        
    except Exception as e:
        logger.error(f"Error in offline test: {e}", exc_info=True)
        error_result = {
            "status": "error",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "test_type": "offline_test"
        }
        test_logger.log_session_end("offline_test", error_result)
        
        # Display error message
        display_header("Test Error")
        print(f"Error: {str(e)}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run offline test of the framework")
    
    parser.add_argument(
        "--log-dir", 
        default="data/logs/offline_tests",
        help="Directory to store test logs"
    )
    
    args = parser.parse_args()
    
    try:
        run_offline_test(args.log_dir)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()