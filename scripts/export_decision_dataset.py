#!/usr/bin/env python3
"""
aGENtrader v2 Decision Dataset Exporter

This script exports trading decisions from the log files into structured datasets
for analysis, model training, and performance evaluation.
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Export decision logs to CSV and JSONL datasets')
    parser.add_argument('-i', '--input', default='logs/decision_summary.logl',
                        help='Input log file path (default: logs/decision_summary.logl)')
    parser.add_argument('-o', '--output', default='datasets/decision_log_dataset',
                        help='Output file prefix (default: datasets/decision_log_dataset)')
    parser.add_argument('-v', '--version', default=None,
                        help='Version tag to append to the output file (e.g., v2.1.0)')
    parser.add_argument('-f', '--filter', default=None,
                        help='Filter entries by agent name (e.g., "SentimentAnalyst")')
    parser.add_argument('-l', '--limit', default=None, type=int,
                        help='Limit the number of entries to export')
    parser.add_argument('--format', choices=['csv', 'jsonl', 'both'], default='both',
                        help='Output format (default: both)')
    return parser.parse_args()


def ensure_dir_exists(path: str) -> None:
    """Ensure the directory exists, creating it if necessary."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def parse_decision_log(log_path: str) -> List[Dict[str, Any]]:
    """Parse the decision log file into a list of dictionaries."""
    if not os.path.exists(log_path):
        print(f"Error: Log file not found: {log_path}")
        return []
    
    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            try:
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse the JSON object
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON line: {line}")
    
    return entries


def filter_entries(entries: List[Dict[str, Any]], agent_filter: Optional[str] = None, 
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Filter entries by agent name and/or limit."""
    if agent_filter:
        entries = [e for e in entries if e.get('agent_name', '').lower() == agent_filter.lower()]
    
    if limit is not None and limit > 0:
        entries = entries[:limit]
    
    return entries


def export_to_csv(entries: List[Dict[str, Any]], output_path: str) -> None:
    """Export entries to a CSV file."""
    if not entries:
        print("No entries to export to CSV.")
        return
    
    ensure_dir_exists(output_path)
    
    # Get all unique keys from all entries
    fieldnames = set()
    for entry in entries:
        fieldnames.update(entry.keys())
    fieldnames = sorted(list(fieldnames))
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    
    print(f"Exported {len(entries)} entries to {output_path}")


def export_to_jsonl(entries: List[Dict[str, Any]], output_path: str) -> None:
    """Export entries to a JSONL file."""
    if not entries:
        print("No entries to export to JSONL.")
        return
    
    ensure_dir_exists(output_path)
    
    with open(output_path, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Exported {len(entries)} entries to {output_path}")


def generate_filename(base_path: str, version: Optional[str], 
                     agent_filter: Optional[str], limit: Optional[int]) -> Tuple[str, str]:
    """Generate output filenames for CSV and JSONL."""
    # Add timestamp if no version specified
    if version is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = f"v{timestamp}"
    else:
        suffix = version
    
    # Add filter info if present
    if agent_filter:
        suffix = f"{suffix}_{agent_filter.lower()}_only"
    
    # Add limit info if present
    if limit is not None:
        suffix = f"{suffix}_limit{limit}"
    
    csv_path = f"{base_path}_{suffix}.csv"
    jsonl_path = f"{base_path}_{suffix}.jsonl"
    
    return csv_path, jsonl_path


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    
    # Parse and filter decision log entries
    entries = parse_decision_log(args.input)
    if not entries:
        return 1
    
    filtered_entries = filter_entries(entries, args.filter, args.limit)
    if not filtered_entries:
        print(f"No entries found after filtering.")
        return 1
    
    # Generate output filenames
    csv_path, jsonl_path = generate_filename(
        args.output, args.version, args.filter, args.limit
    )
    
    # Export based on specified format
    if args.format in ['csv', 'both']:
        export_to_csv(filtered_entries, csv_path)
    
    if args.format in ['jsonl', 'both']:
        export_to_jsonl(filtered_entries, jsonl_path)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())