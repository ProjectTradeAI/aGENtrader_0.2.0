#!/usr/bin/env python
"""
Test Progress Checker

Quick utility to check on the progress of running tests and view latest results
without waiting for the full completion.
"""

import os
import sys
import glob
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

def find_latest_logs(log_dir: str = "data/logs", test_type: Optional[str] = None) -> List[str]:
    """Find the latest log files"""
    pattern = os.path.join(log_dir, "**/*.log")
    
    if test_type:
        # Add test type to pattern
        dir_pattern = os.path.join(log_dir, f"**/*{test_type}*/*.log")
        file_pattern = os.path.join(log_dir, f"**/*{test_type}*.log")
        
        # Try both patterns
        files = glob.glob(dir_pattern, recursive=True)
        files.extend(glob.glob(file_pattern, recursive=True))
    else:
        files = glob.glob(pattern, recursive=True)
    
    # Sort by modification time
    return sorted(files, key=os.path.getmtime, reverse=True)

def find_latest_results(log_dir: str = "data/logs", test_type: Optional[str] = None) -> List[str]:
    """Find the latest test result files"""
    pattern = os.path.join(log_dir, "**/*session*.json")
    
    if test_type:
        # Add test type to pattern
        pattern = os.path.join(log_dir, f"**/*{test_type}*/*session*.json")
    
    files = glob.glob(pattern, recursive=True)
    
    # Sort by modification time
    return sorted(files, key=os.path.getmtime, reverse=True)

def display_log_tail(log_file: str, lines: int = 20) -> None:
    """Display the last N lines of a log file"""
    try:
        with open(log_file, 'r') as f:
            # Read all lines and get the last N
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            print(f"\n===== Last {len(last_lines)} lines of {log_file} =====")
            print("".join(last_lines))
    except Exception as e:
        print(f"Error reading log file {log_file}: {e}")

def display_result_summary(result_file: str) -> None:
    """Display a summary of a test result file"""
    try:
        with open(result_file, 'r') as f:
            data = json.load(f)
            
            print(f"\n===== Summary of {result_file} =====")
            print(f"Session ID: {data.get('session_id', 'Unknown')}")
            print(f"Status: {data.get('status', 'Unknown')}")
            print(f"Test Type: {data.get('test_type', 'Unknown')}")
            print(f"Symbol: {data.get('symbol', 'Unknown')}")
            print(f"Timestamp: {data.get('timestamp', 'Unknown')}")
            
            # Check for decision
            if "decision" in data:
                print("\nDecision:")
                decision = data["decision"]
                print(f"  Signal: {decision.get('signal', 'Unknown')}")
                print(f"  Confidence: {decision.get('confidence', 'Unknown')}")
                print(f"  Reasoning: {decision.get('reasoning', 'Unknown')[:100]}...")
            
            # Check for chat file
            if "chat_file" in data:
                print(f"\nChat history saved to: {data['chat_file']}")
                
    except Exception as e:
        print(f"Error reading result file {result_file}: {e}")

def check_running_tests() -> None:
    """Check for running tests using process information"""
    import subprocess
    
    try:
        # Run ps command to find python processes
        result = subprocess.run(
            ["ps", "-ef"], 
            capture_output=True, 
            text=True
        )
        
        # Filter for test scripts
        test_processes = []
        for line in result.stdout.splitlines():
            if "run_" in line and "test" in line and "python" in line:
                test_processes.append(line)
        
        if test_processes:
            print("\n===== Running Test Processes =====")
            for proc in test_processes:
                print(proc)
        else:
            print("\nNo test processes currently running.")
            
    except Exception as e:
        print(f"Error checking running processes: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check test progress and results")
    
    parser.add_argument(
        "--log-dir", 
        default="data/logs",
        help="Base directory for logs"
    )
    
    parser.add_argument(
        "--test-type", 
        help="Test type filter (e.g., single, simplified, collaborative)"
    )
    
    parser.add_argument(
        "--show-logs", 
        action="store_true",
        help="Show tails of latest log files"
    )
    
    parser.add_argument(
        "--show-results", 
        action="store_true",
        help="Show summaries of latest result files"
    )
    
    parser.add_argument(
        "--show-processes", 
        action="store_true",
        help="Show running test processes"
    )
    
    parser.add_argument(
        "--watch", 
        action="store_true",
        help="Watch mode - continuously update"
    )
    
    parser.add_argument(
        "--lines", 
        type=int,
        default=20,
        help="Number of log lines to show"
    )
    
    parser.add_argument(
        "--max-results", 
        type=int,
        default=3,
        help="Maximum number of results to show"
    )
    
    args = parser.parse_args()
    
    # Default to showing everything if nothing specified
    show_all = not (args.show_logs or args.show_results or args.show_processes)
    
    try:
        while True:
            os.system('clear')  # Clear screen
            
            print(f"===== Test Progress Check =====")
            print(f"Time: {datetime.now().isoformat()}")
            print(f"Log Directory: {args.log_dir}")
            if args.test_type:
                print(f"Test Type Filter: {args.test_type}")
            print("=" * 30)
            
            # Check running processes
            if show_all or args.show_processes:
                check_running_tests()
            
            # Find latest logs
            if show_all or args.show_logs:
                latest_logs = find_latest_logs(args.log_dir, args.test_type)
                
                if latest_logs:
                    print(f"\n===== Latest Log Files ({min(len(latest_logs), 3)}/{len(latest_logs)}) =====")
                    
                    for i, log_file in enumerate(latest_logs[:3]):
                        display_log_tail(log_file, args.lines)
                        
                        if i < 2 and i < len(latest_logs) - 1:
                            print("\n" + "-" * 80 + "\n")
                else:
                    print("\nNo log files found.")
            
            # Find latest results
            if show_all or args.show_results:
                latest_results = find_latest_results(args.log_dir, args.test_type)
                
                if latest_results:
                    print(f"\n===== Latest Result Files ({min(len(latest_results), args.max_results)}/{len(latest_results)}) =====")
                    
                    for i, result_file in enumerate(latest_results[:args.max_results]):
                        display_result_summary(result_file)
                        
                        if i < args.max_results - 1 and i < len(latest_results) - 1:
                            print("\n" + "-" * 80 + "\n")
                else:
                    print("\nNo result files found.")
            
            if not args.watch:
                break
                
            # Wait before refreshing
            print("\nUpdating in 5 seconds... Press Ctrl+C to exit.")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nCheck interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()