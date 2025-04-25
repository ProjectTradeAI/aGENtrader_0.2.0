#!/usr/bin/env python3
"""
aGENtrader v2 Performance Viewer

This script analyzes and displays trading performance metrics from the trade history.
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from tabulate import tabulate
from typing import List, Dict, Any, Optional, Tuple


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='View trading performance metrics')
    parser.add_argument('-i', '--input', default='logs/trade_history.jsonl',
                        help='Path to trade history file (default: logs/trade_history.jsonl)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output directory for generated charts (default: logs/performance)')
    parser.add_argument('-p', '--period', default='all',
                        choices=['day', 'week', 'month', 'year', 'all'],
                        help='Time period to analyze (default: all)')
    parser.add_argument('-s', '--symbol', default=None,
                        help='Filter by symbol (e.g., "BTCUSDT")')
    parser.add_argument('-a', '--agent', default=None,
                        help='Filter by agent name')
    parser.add_argument('--no-charts', action='store_true',
                        help='Disable chart generation')
    return parser.parse_args()


def load_trade_history(path: str) -> List[Dict[str, Any]]:
    """Load the trade history from a JSONL file."""
    if not os.path.exists(path):
        print(f"Error: Trade history file not found: {path}")
        return []
    
    trades = []
    with open(path, 'r') as f:
        for line in f:
            try:
                line = line.strip()
                if not line:
                    continue
                trade = json.loads(line)
                trades.append(trade)
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON line: {line}")
    
    return trades


def filter_trades_by_period(trades: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
    """Filter trades by time period."""
    now = datetime.now()
    
    if period == 'day':
        start_time = int((now - timedelta(days=1)).timestamp())
    elif period == 'week':
        start_time = int((now - timedelta(weeks=1)).timestamp())
    elif period == 'month':
        start_time = int((now - timedelta(days=30)).timestamp())
    elif period == 'year':
        start_time = int((now - timedelta(days=365)).timestamp())
    else:  # 'all'
        return trades
    
    return [t for t in trades if t.get('close_timestamp', 0) >= start_time]


def filter_trades(trades: List[Dict[str, Any]], period: str, 
                 symbol: Optional[str] = None, agent: Optional[str] = None) -> List[Dict[str, Any]]:
    """Apply all filters to the trade history."""
    # Filter by time period
    filtered = filter_trades_by_period(trades, period)
    
    # Filter by symbol if specified
    if symbol:
        filtered = [t for t in filtered if t.get('symbol', '').lower() == symbol.lower()]
    
    # Filter by agent if specified
    if agent:
        filtered = [t for t in filtered if t.get('agent', '').lower() == agent.lower()]
    
    return filtered


def calculate_performance_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate trading performance metrics."""
    if not trades:
        return {}
    
    # Extract profit information
    profits = [t.get('profit_pct', 0) for t in trades]
    profits_abs = [t.get('profit_amount', 0) for t in trades]
    durations = [(t.get('close_timestamp', 0) - t.get('timestamp', 0)) / 3600 for t in trades]
    
    # Basic metrics
    total_trades = len(trades)
    winning_trades = sum(1 for p in profits if p > 0)
    losing_trades = sum(1 for p in profits if p < 0)
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Profit metrics
    total_profit_pct = sum(profits)
    avg_profit_pct = np.mean(profits) if profits else 0
    median_profit_pct = np.median(profits) if profits else 0
    max_profit_pct = max(profits) if profits else 0
    max_loss_pct = min(profits) if profits else 0
    
    # Absolute profit metrics
    total_profit_abs = sum(profits_abs)
    avg_profit_abs = np.mean(profits_abs) if profits_abs else 0
    
    # Time metrics
    avg_duration = np.mean(durations) if durations else 0
    
    # Risk metrics
    std_dev = np.std(profits) if len(profits) > 1 else 0
    sharpe = avg_profit_pct / std_dev if std_dev > 0 else 0
    
    # Drawdown calculation
    cumulative = np.cumsum(profits)
    max_dd = 0
    peak = cumulative[0]
    for value in cumulative:
        if value > peak:
            peak = value
        dd = (peak - value)
        if dd > max_dd:
            max_dd = dd
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate * 100,  # Convert to percentage
        'total_profit_pct': total_profit_pct,
        'avg_profit_pct': avg_profit_pct,
        'median_profit_pct': median_profit_pct,
        'max_profit_pct': max_profit_pct,
        'max_loss_pct': max_loss_pct,
        'total_profit_abs': total_profit_abs,
        'avg_profit_abs': avg_profit_abs,
        'avg_duration': avg_duration,
        'std_dev': std_dev,
        'sharpe': sharpe,
        'max_drawdown': max_dd
    }


def generate_equity_curve(trades: List[Dict[str, Any]], output_dir: str) -> str:
    """Generate an equity curve chart."""
    if not trades:
        return ""
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Sort trades by timestamp
    trades = sorted(trades, key=lambda t: t.get('close_timestamp', 0))
    
    # Extract timestamps and profits
    timestamps = [datetime.fromtimestamp(t.get('close_timestamp', 0)) for t in trades]
    profits = [t.get('profit_pct', 0) for t in trades]
    cumulative = np.cumsum(profits)
    
    # Generate chart
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, cumulative, label='Equity Curve')
    plt.grid(True, alpha=0.3)
    plt.title('Trading Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Profit (%)')
    plt.legend()
    
    # Save chart
    output_path = os.path.join(output_dir, 'equity_curve.png')
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def generate_profit_distribution(trades: List[Dict[str, Any]], output_dir: str) -> str:
    """Generate a profit distribution histogram."""
    if not trades:
        return ""
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract profits
    profits = [t.get('profit_pct', 0) for t in trades]
    
    # Generate chart
    plt.figure(figsize=(12, 6))
    plt.hist(profits, bins=50, alpha=0.7, color='blue')
    plt.axvline(x=0, color='red', linestyle='--')
    plt.grid(True, alpha=0.3)
    plt.title('Profit Distribution')
    plt.xlabel('Profit (%)')
    plt.ylabel('Frequency')
    
    # Save chart
    output_path = os.path.join(output_dir, 'profit_distribution.png')
    plt.savefig(output_path)
    plt.close()
    
    return output_path


def display_performance_metrics(metrics: Dict[str, Any]) -> None:
    """Display performance metrics in a tabular format."""
    if not metrics:
        print("No data available for performance analysis.")
        return
    
    # Format data for tabular display
    data = [
        ["Total Trades", f"{metrics['total_trades']}"],
        ["Winning Trades", f"{metrics['winning_trades']} ({metrics['win_rate']:.2f}%)"],
        ["Losing Trades", f"{metrics['losing_trades']}"],
        ["Total Profit", f"{metrics['total_profit_pct']:.2f}%"],
        ["Average Profit", f"{metrics['avg_profit_pct']:.2f}%"],
        ["Median Profit", f"{metrics['median_profit_pct']:.2f}%"],
        ["Maximum Profit", f"{metrics['max_profit_pct']:.2f}%"],
        ["Maximum Loss", f"{metrics['max_loss_pct']:.2f}%"],
        ["Total Profit (Absolute)", f"${metrics['total_profit_abs']:.2f}"],
        ["Average Duration", f"{metrics['avg_duration']:.2f} hours"],
        ["Standard Deviation", f"{metrics['std_dev']:.2f}"],
        ["Sharpe Ratio", f"{metrics['sharpe']:.2f}"],
        ["Maximum Drawdown", f"{metrics['max_drawdown']:.2f}%"]
    ]
    
    # Print the table
    print("\n=== Performance Metrics ===")
    print(tabulate(data, headers=["Metric", "Value"], tablefmt="fancy_grid"))
    print()


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    
    # Set default output directory if not specified
    output_dir = args.output if args.output else 'logs/performance'
    
    # Load and process trades
    trades = load_trade_history(args.input)
    if not trades:
        return 1
    
    # Apply filters
    filtered_trades = filter_trades(trades, args.period, args.symbol, args.agent)
    if not filtered_trades:
        print(f"No trades found matching your criteria.")
        return 0
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(filtered_trades)
    
    # Display metrics
    display_performance_metrics(metrics)
    
    # Generate charts
    if not args.no_charts:
        equity_path = generate_equity_curve(filtered_trades, output_dir)
        dist_path = generate_profit_distribution(filtered_trades, output_dir)
        
        if equity_path and dist_path:
            print(f"Charts generated in: {output_dir}")
            print(f"  - Equity Curve: {os.path.basename(equity_path)}")
            print(f"  - Profit Distribution: {os.path.basename(dist_path)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())