#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export Decision Dataset Script

This script exports decision data from aGENtrader's logs into a standardized dataset
format that can be used for analysis, visualization, and potentially for model training.
"""

import os
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Default paths
DEFAULT_DECISION_LOG = "logs/decision_summary.logl"
DEFAULT_TRADE_LOG = "logs/trade_book.jsonl"
DEFAULT_PERFORMANCE_LOG = "logs/trade_performance.jsonl"
DEFAULT_OUTPUT = "datasets/decision_dataset.jsonl"


def parse_decision_log(file_path: str, limit: int = None) -> List[Dict[str, Any]]:
    """
    Parse the decision log file.
    
    Args:
        file_path: Path to the decision log file
        limit: Maximum number of entries to parse (newest first)
        
    Returns:
        List of parsed decision entries
    """
    decisions = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Process lines in reverse order to get newest first if limit is specified
        if limit:
            lines = lines[-limit:]
            
        for line in lines:
            # Parse decision log format
            if line.strip():
                try:
                    # Example format: [2025-04-24 18:32:15] [TechnicalAnalyst] SIGNAL: BUY, CONF: 75%, PRICE: 62485.23
                    parts = line.strip().split(']')
                    if len(parts) < 3:
                        continue
                        
                    timestamp_str = parts[0].strip('[')
                    agent = parts[1].strip('[').strip()
                    
                    # Parse the details part
                    details = parts[2].strip()
                    signal = None
                    confidence = None
                    price = None
                    reason = None
                    
                    if "SIGNAL:" in details:
                        signal_part = details.split("SIGNAL:")[1].split(",")[0].strip()
                        signal = signal_part
                        
                    if "CONF:" in details:
                        conf_part = details.split("CONF:")[1].split(",")[0].strip()
                        confidence = int(conf_part.strip("%"))
                        
                    if "PRICE:" in details:
                        price_part = details.split("PRICE:")[1].split(",")[0].strip()
                        price = float(price_part)
                        
                    if "REASON:" in details:
                        reason = details.split("REASON:")[1].strip()
                    
                    decision = {
                        "timestamp": timestamp_str,
                        "agent": agent,
                        "signal": signal,
                        "confidence": confidence,
                        "price": price,
                        "reason": reason
                    }
                    
                    decisions.append(decision)
                except Exception as e:
                    print(f"Error parsing line: {line}. Error: {str(e)}")
    except FileNotFoundError:
        print(f"Warning: Decision log file {file_path} not found.")
    
    return decisions


def parse_trade_log(file_path: str, limit: int = None) -> List[Dict[str, Any]]:
    """
    Parse the trade log file.
    
    Args:
        file_path: Path to the trade log file
        limit: Maximum number of entries to parse (newest first)
        
    Returns:
        List of parsed trade entries
    """
    trades = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Process lines in reverse order to get newest first if limit is specified
        if limit:
            lines = lines[-limit:]
            
        for line in lines:
            if line.strip():
                try:
                    trade = json.loads(line.strip())
                    trades.append(trade)
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse trade log line: {line}")
    except FileNotFoundError:
        print(f"Warning: Trade log file {file_path} not found.")
    
    return trades


def parse_performance_log(file_path: str, limit: int = None) -> List[Dict[str, Any]]:
    """
    Parse the performance log file.
    
    Args:
        file_path: Path to the performance log file
        limit: Maximum number of entries to parse (newest first)
        
    Returns:
        List of parsed performance entries
    """
    performances = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Process lines in reverse order to get newest first if limit is specified
        if limit:
            lines = lines[-limit:]
            
        for line in lines:
            if line.strip():
                try:
                    performance = json.loads(line.strip())
                    performances.append(performance)
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse performance log line: {line}")
    except FileNotFoundError:
        print(f"Warning: Performance log file {file_path} not found.")
    
    return performances


def merge_data(
    decisions: List[Dict[str, Any]],
    trades: List[Dict[str, Any]],
    performances: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge decision, trade, and performance data based on timestamps.
    
    Args:
        decisions: List of decision entries
        trades: List of trade entries
        performances: List of performance entries
        
    Returns:
        List of merged dataset entries
    """
    dataset = []
    
    # Create a dictionary of trades by timestamp for easier lookup
    trades_by_time = {}
    for trade in trades:
        if "timestamp" in trade and trade["timestamp"]:
            trades_by_time[trade["timestamp"]] = trade
    
    # Create a dictionary of performances by trade_id for easier lookup
    performances_by_trade_id = {}
    for perf in performances:
        if "trade_id" in perf and perf["trade_id"]:
            performances_by_trade_id[perf["trade_id"]] = perf
    
    # Merge decisions with corresponding trades and performances
    for decision in decisions:
        entry = {
            "timestamp": decision.get("timestamp"),
            "agent": decision.get("agent"),
            "signal": decision.get("signal"),
            "confidence": decision.get("confidence"),
            "price": decision.get("price"),
            "reason": decision.get("reason"),
            "trade_executed": False,
            "trade_id": None,
            "trade_type": None,
            "trade_volume": None,
            "trade_price": None,
            "pnl": None,
            "roi": None
        }
        
        # Look for a corresponding trade
        timestamp = decision.get("timestamp")
        if timestamp and timestamp in trades_by_time:
            trade = trades_by_time[timestamp]
            entry["trade_executed"] = True
            entry["trade_id"] = trade.get("trade_id")
            entry["trade_type"] = trade.get("type")
            entry["trade_volume"] = trade.get("volume")
            entry["trade_price"] = trade.get("price")
            
            # Look for corresponding performance data
            trade_id = trade.get("trade_id")
            if trade_id and trade_id in performances_by_trade_id:
                perf = performances_by_trade_id[trade_id]
                entry["pnl"] = perf.get("pnl")
                entry["roi"] = perf.get("roi")
        
        dataset.append(entry)
    
    return dataset


def export_dataset(dataset: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export the dataset to a JSONL file.
    
    Args:
        dataset: List of dataset entries
        output_path: Path to the output file
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for entry in dataset:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Dataset exported to {output_path} ({len(dataset)} entries)")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Export aGENtrader decision dataset")
    parser.add_argument(
        "--decision-log",
        default=DEFAULT_DECISION_LOG,
        help=f"Path to decision log file (default: {DEFAULT_DECISION_LOG})"
    )
    parser.add_argument(
        "--trade-log",
        default=DEFAULT_TRADE_LOG,
        help=f"Path to trade log file (default: {DEFAULT_TRADE_LOG})"
    )
    parser.add_argument(
        "--performance-log",
        default=DEFAULT_PERFORMANCE_LOG,
        help=f"Path to performance log file (default: {DEFAULT_PERFORMANCE_LOG})"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Path to output JSONL file (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of entries to process (default: all)"
    )
    
    args = parser.parse_args()
    
    # Parse log files
    print(f"Parsing decision log from {args.decision_log}...")
    decisions = parse_decision_log(args.decision_log, args.limit)
    print(f"Found {len(decisions)} decision entries")
    
    print(f"Parsing trade log from {args.trade_log}...")
    trades = parse_trade_log(args.trade_log, args.limit)
    print(f"Found {len(trades)} trade entries")
    
    print(f"Parsing performance log from {args.performance_log}...")
    performances = parse_performance_log(args.performance_log, args.limit)
    print(f"Found {len(performances)} performance entries")
    
    # Merge data
    print("Merging data...")
    dataset = merge_data(decisions, trades, performances)
    
    # Export dataset
    print(f"Exporting dataset to {args.output}...")
    export_dataset(dataset, args.output)
    
    print("Done!")


if __name__ == "__main__":
    main()