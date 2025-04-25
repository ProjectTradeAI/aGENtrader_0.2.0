#!/usr/bin/env python3
"""
aGENtrader v2 Open Trades Viewer

This script displays currently open trades with various filters and sorting options.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from tabulate import tabulate
from typing import List, Dict, Any, Optional


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='View open trades')
    parser.add_argument('-i', '--input', default='logs/trade_book.jsonl',
                        help='Path to trade book file (default: logs/trade_book.jsonl)')
    parser.add_argument('-s', '--symbol', default=None,
                        help='Filter by symbol (e.g., "BTCUSDT")')
    parser.add_argument('-a', '--agent', default=None,
                        help='Filter by agent name that opened the trade')
    parser.add_argument('--sort', choices=['time', 'profit', 'size'], default='time',
                        help='Sort criterion (default: time)')
    parser.add_argument('--reverse', action='store_true',
                        help='Reverse the sort order')
    parser.add_argument('--closed', action='store_true',
                        help='Show closed trades instead of open ones')
    parser.add_argument('--detailed', action='store_true',
                        help='Show detailed trade information')
    return parser.parse_args()


def load_trade_book(path: str) -> List[Dict[str, Any]]:
    """Load the trade book from a JSONL file."""
    if not os.path.exists(path):
        print(f"Error: Trade book file not found: {path}")
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


def filter_trades(trades: List[Dict[str, Any]], symbol: Optional[str] = None,
                 agent: Optional[str] = None, closed: bool = False) -> List[Dict[str, Any]]:
    """Filter trades by symbol, agent, and open/closed status."""
    filtered = []
    for trade in trades:
        # Skip trades with opposite closed status
        is_closed = trade.get('closed', False)
        if is_closed != closed:
            continue
        
        # Apply symbol filter if specified
        if symbol and trade.get('symbol', '').lower() != symbol.lower():
            continue
        
        # Apply agent filter if specified
        if agent and trade.get('agent', '').lower() != agent.lower():
            continue
        
        filtered.append(trade)
    
    return filtered


def sort_trades(trades: List[Dict[str, Any]], sort_by: str, reverse: bool) -> List[Dict[str, Any]]:
    """Sort trades by the specified criterion."""
    if sort_by == 'time':
        return sorted(trades, key=lambda t: t.get('timestamp', 0), reverse=reverse)
    elif sort_by == 'profit':
        return sorted(trades, key=lambda t: t.get('current_profit_pct', 0), reverse=reverse)
    elif sort_by == 'size':
        return sorted(trades, key=lambda t: t.get('size', 0), reverse=reverse)
    return trades


def format_trades_table(trades: List[Dict[str, Any]], detailed: bool) -> List[List[Any]]:
    """Format trades for tabular display."""
    table_data = []
    
    if detailed:
        headers = ['ID', 'Symbol', 'Side', 'Entry Price', 'Current Price', 
                  'Size', 'Profit %', 'Time', 'Agent']
    else:
        headers = ['Symbol', 'Side', 'Entry Price', 'Profit %', 'Time']
    
    for trade in trades:
        if detailed:
            row = [
                trade.get('id', 'N/A'),
                trade.get('symbol', 'N/A'),
                trade.get('side', 'N/A'),
                f"{trade.get('entry_price', 0):.2f}",
                f"{trade.get('current_price', 0):.2f}",
                f"{trade.get('size', 0):.4f}",
                f"{trade.get('current_profit_pct', 0):.2f}%",
                datetime.fromtimestamp(trade.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M'),
                trade.get('agent', 'N/A')
            ]
        else:
            row = [
                trade.get('symbol', 'N/A'),
                trade.get('side', 'N/A'),
                f"{trade.get('entry_price', 0):.2f}",
                f"{trade.get('current_profit_pct', 0):.2f}%",
                datetime.fromtimestamp(trade.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M')
            ]
        
        table_data.append(row)
    
    return [headers] + table_data if table_data else [headers]


def display_trade_summary(trades: List[Dict[str, Any]]) -> None:
    """Display a summary of the trades."""
    if not trades:
        print("No trades found matching your criteria.")
        return
    
    # Basic stats
    total_trades = len(trades)
    total_value = sum(trade.get('size', 0) * trade.get('entry_price', 0) for trade in trades)
    avg_profit = sum(trade.get('current_profit_pct', 0) for trade in trades) / total_trades
    
    # Count per side
    long_trades = sum(1 for t in trades if t.get('side', '').lower() == 'buy')
    short_trades = sum(1 for t in trades if t.get('side', '').lower() == 'sell')
    
    # Count per symbol
    symbols = {}
    for trade in trades:
        symbol = trade.get('symbol', 'unknown')
        symbols[symbol] = symbols.get(symbol, 0) + 1
    
    print(f"\n=== Trade Summary ===")
    print(f"Total Trades: {total_trades}")
    print(f"Total Value: ${total_value:.2f}")
    print(f"Average Profit: {avg_profit:.2f}%")
    print(f"Long Positions: {long_trades}")
    print(f"Short Positions: {short_trades}")
    print(f"\nTrades per Symbol:")
    for symbol, count in sorted(symbols.items(), key=lambda x: x[1], reverse=True):
        print(f"  {symbol}: {count}")
    print("=====================\n")


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    
    # Load and process trades
    trades = load_trade_book(args.input)
    if not trades:
        return 1
    
    # Filter and sort
    filtered_trades = filter_trades(trades, args.symbol, args.agent, args.closed)
    sorted_trades = sort_trades(filtered_trades, args.sort, args.reverse)
    
    # Display summary
    display_trade_summary(filtered_trades)
    
    # Display table
    table_data = format_trades_table(sorted_trades, args.detailed)
    print(tabulate(table_data[1:], headers=table_data[0], tablefmt='fancy_grid'))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())