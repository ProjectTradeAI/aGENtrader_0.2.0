"""
Test Results Viewer

Provides a command-line interface to browse and view comprehensive test results.
"""

import os
import json
import argparse
import glob
from typing import Dict, Any, List, Optional
from datetime import datetime

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="View test results")
    
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs",
        help="Log directory (default: data/logs)"
    )
    
    parser.add_argument(
        "--test-type",
        type=str,
        default="all",
        choices=["all", "collaborative", "decision", "single"],
        help="Type of test results to view (default: all)"
    )
    
    parser.add_argument(
        "--session-id",
        type=str,
        help="View details for a specific session ID"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of summaries to display (default: 10)"
    )
    
    return parser.parse_args()

def find_summary_files(log_dir: str, test_type: str = "all") -> List[str]:
    """
    Find summary files for the specified test type
    
    Args:
        log_dir: Log directory
        test_type: Test type to filter by
        
    Returns:
        List of summary file paths
    """
    patterns = []
    
    if test_type == "all" or test_type == "collaborative":
        patterns.append(f"{log_dir}/**/collab_*_result.json")
    
    if test_type == "all" or test_type == "decision":
        patterns.append(f"{log_dir}/**/session_*_result.json")
    
    if test_type == "all" or test_type == "single":
        patterns.append(f"{log_dir}/**/single_*_result.json")
    
    # Collect all matching files
    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern, recursive=True))
    
    # Sort by modification time (newest first)
    all_files.sort(key=os.path.getmtime, reverse=True)
    
    return all_files

def find_session_files(log_dir: str, session_id: str) -> Dict[str, str]:
    """
    Find all files related to a specific session
    
    Args:
        log_dir: Log directory
        session_id: Session ID to search for
        
    Returns:
        Dictionary mapping file types to file paths
    """
    session_files = {}
    
    # Find param file
    param_files = glob.glob(f"{log_dir}/**/{session_id}_params.json", recursive=True)
    if param_files:
        session_files["params"] = param_files[0]
    
    # Find result file
    result_files = glob.glob(f"{log_dir}/**/{session_id}_result.json", recursive=True)
    if result_files:
        session_files["result"] = result_files[0]
    
    # Find full session file
    full_files = glob.glob(f"{log_dir}/**/{session_id}_full.json", recursive=True)
    if full_files:
        session_files["full"] = full_files[0]
    
    # Find chat history files
    chat_json_files = glob.glob(f"{log_dir}/**/{session_id}_chat.json", recursive=True)
    if chat_json_files:
        session_files["chat_json"] = chat_json_files[0]
    
    chat_text_files = glob.glob(f"{log_dir}/**/{session_id}_chat.txt", recursive=True)
    if chat_text_files:
        session_files["chat_text"] = chat_text_files[0]
    
    # Find log file
    log_files = glob.glob(f"{log_dir}/**/{session_id}.log", recursive=True)
    if log_files:
        session_files["log"] = log_files[0]
    
    return session_files

def list_test_summaries(log_dir: str, test_type: str = "all") -> List[Dict[str, Any]]:
    """
    List available test summaries
    
    Args:
        log_dir: Log directory
        test_type: Test type to filter by
        
    Returns:
        List of summary data
    """
    summary_files = find_summary_files(log_dir, test_type)
    summaries = []
    
    for file_path in summary_files:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Extract just the key information
            session_id = data.get("session_id", os.path.basename(file_path).split("_")[0])
            session_type = data.get("session_type", "unknown")
            timestamp = data.get("timestamp", data.get("end_time", "unknown"))
            status = data.get("status", "unknown")
            
            # Extract decision if available
            decision = None
            if "decision" in data and data["decision"]:
                decision = {
                    "symbol": data["decision"].get("symbol", "unknown"),
                    "action": data["decision"].get("action", "unknown"),
                    "confidence": data["decision"].get("confidence", 0)
                }
            
            summary = {
                "session_id": session_id,
                "session_type": session_type,
                "timestamp": timestamp,
                "status": status,
                "decision": decision,
                "file_path": file_path
            }
            
            summaries.append(summary)
            
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
    
    return summaries

def display_header(title: str) -> None:
    """
    Display a formatted header
    
    Args:
        title: Header title
    """
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def display_summary_list(summaries: List[Dict[str, Any]]) -> None:
    """
    Display a list of test summaries
    
    Args:
        summaries: List of summary data
    """
    if not summaries:
        print("\nNo test results found.")
        return
    
    display_header(f"Test Results ({len(summaries)} found)")
    
    for i, summary in enumerate(summaries, 1):
        session_id = summary["session_id"]
        session_type = summary["session_type"]
        timestamp = summary["timestamp"]
        status = summary["status"]
        
        # Format timestamp if it's a string in ISO format
        if isinstance(timestamp, str) and "T" in timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # Format the session type
        if session_type == "collaborative":
            session_type = "Collaborative Analysis"
        elif session_type == "decision":
            session_type = "Trading Decision"
        elif session_type == "single_agent":
            session_type = "Single Agent Analysis"
        
        # Status with color
        status_str = "✅ Success" if status == "completed" or status == "success" else "❌ " + status.capitalize()
        
        print(f"{i}. Session: {session_id}")
        print(f"   Type: {session_type}")
        print(f"   Time: {timestamp}")
        print(f"   Status: {status_str}")
        
        # Add decision if available
        if summary.get("decision"):
            decision = summary["decision"]
            print(f"   Decision: {decision['action']} {decision['symbol']} (Confidence: {decision['confidence']}%)")
        
        print()

def load_file_content(file_path: str) -> Any:
    """
    Load content from a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content (parsed JSON if possible)
    """
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Try to parse as JSON if it's a JSON file
    if file_path.endswith(".json"):
        try:
            return json.loads(content)
        except:
            return content
    
    return content

def display_session_details(session_id: str, log_dir: str) -> None:
    """
    Display details for a specific session
    
    Args:
        session_id: Session ID
        log_dir: Log directory
    """
    session_files = find_session_files(log_dir, session_id)
    
    if not session_files:
        print(f"\nNo files found for session ID: {session_id}")
        return
    
    display_header(f"Session Details: {session_id}")
    
    # Display basic session information from the result file
    if "result" in session_files:
        result_data = load_file_content(session_files["result"])
        if isinstance(result_data, dict):
            # Display session info
            print("Session Information:")
            print(f"  Type: {result_data.get('session_type', 'Unknown')}")
            print(f"  Status: {result_data.get('status', 'Unknown')}")
            timestamp = result_data.get("timestamp", result_data.get("end_time", "Unknown"))
            print(f"  Timestamp: {timestamp}")
            print()
    
    # Display decision if available
    if "full" in session_files:
        full_data = load_file_content(session_files["full"])
        if isinstance(full_data, dict) and "decision" in full_data and full_data["decision"]:
            decision = full_data["decision"]
            
            print("Trading Decision:")
            print(f"  Symbol: {decision.get('symbol', 'Unknown')}")
            print(f"  Action: {decision.get('action', 'Unknown')}")
            print(f"  Confidence: {decision.get('confidence', 0)}%")
            print(f"  Price: ${decision.get('price', 0)}")
            print(f"  Risk Level: {decision.get('risk_level', 'Unknown')}")
            print(f"  Reasoning: {decision.get('reasoning', 'No reasoning provided')[:100]}...")
            print()
    
    # List available files
    print("Available Files:")
    for file_type, file_path in session_files.items():
        print(f"  {file_type}: {file_path}")
    
    # Offer to display specific files
    print("\nTo view a specific file, run the command:")
    print(f"cat {list(session_files.values())[0]}")

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create the log directory if it doesn't exist
    os.makedirs(args.log_dir, exist_ok=True)
    
    # If a session ID is provided, display detailed information for that session
    if args.session_id:
        display_session_details(args.session_id, args.log_dir)
        return
    
    # Otherwise, list available summaries
    summaries = list_test_summaries(args.log_dir, args.test_type)
    
    # Limit the number of summaries displayed
    if args.limit and args.limit < len(summaries):
        summaries = summaries[:args.limit]
    
    display_summary_list(summaries)
    
    # Prompt for next action
    if summaries:
        print("\nTo view details for a specific session, run the command:")
        print(f"python view_test_results.py --session-id [SESSION_ID]")
        print("\nAvailable session IDs:")
        for i, summary in enumerate(summaries[:5], 1):
            print(f"  {i}. {summary['session_id']}")
        if len(summaries) > 5:
            print(f"  ... and {len(summaries) - 5} more")

if __name__ == "__main__":
    main()