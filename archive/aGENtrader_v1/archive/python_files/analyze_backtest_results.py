#!/usr/bin/env python3
"""
Backtest Results Analyzer

This script analyzes backtest results from the simplified_backtest.py script
and provides a summary of the performance statistics.
"""

import os
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Analyze backtest results")
    
    parser.add_argument(
        "--file", 
        type=str,
        help="Path to backtest results JSON file"
    )
    
    parser.add_argument(
        "--output", 
        type=str,
        default="results/backtests",
        help="Directory to save analysis results"
    )
    
    parser.add_argument(
        "--format", 
        type=str,
        choices=["text", "json", "csv", "md"],
        default="text",
        help="Output format (text, json, csv, or md)"
    )
    
    return parser.parse_args()

def load_backtest_results(file_path: str) -> Dict[str, Any]:
    """
    Load backtest results from JSON file
    
    Args:
        file_path: Path to backtest results JSON file
        
    Returns:
        Dictionary with backtest results
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading backtest results: {str(e)}")
        return {}

def calculate_additional_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate additional performance metrics from backtest results
    
    Args:
        results: Dictionary with backtest results
        
    Returns:
        Dictionary with additional metrics
    """
    metrics = results.get("metrics", [])
    trade_history = results.get("trade_history", [])
    
    if not metrics or not trade_history:
        return {}
    
    # Create pandas DataFrame from metrics
    try:
        df = pd.DataFrame(metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
    except Exception as e:
        print(f"Error processing metrics: {str(e)}")
        return {}
    
    # Calculate additional metrics
    additional_metrics = {}
    
    # Calculate Sharpe Ratio (assuming 0% risk-free rate)
    if len(df) > 1:
        returns = df['portfolio_value'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252 * 24) * returns.mean() / returns.std() if returns.std() > 0 else 0
        additional_metrics["sharpe_ratio"] = sharpe_ratio
    
    # Calculate average profit per trade
    if trade_history:
        closed_trades = [t for t in trade_history if t.get("status") == "CLOSED"]
        if closed_trades:
            profits = [t.get("profit_loss", 0) for t in closed_trades]
            additional_metrics["avg_profit_per_trade"] = sum(profits) / len(profits)
            additional_metrics["min_profit"] = min(profits)
            additional_metrics["max_profit"] = max(profits)
            
            # Calculate profit factor (sum of profits / sum of losses)
            profits_sum = sum(p for p in profits if p > 0)
            losses_sum = abs(sum(p for p in profits if p < 0))
            additional_metrics["profit_factor"] = profits_sum / losses_sum if losses_sum > 0 else float('inf')
            
            # Calculate average trade duration
            durations = []
            for trade in closed_trades:
                try:
                    entry_time = datetime.fromisoformat(trade.get("entry_time", ""))
                    exit_time = datetime.fromisoformat(trade.get("exit_time", ""))
                    duration = (exit_time - entry_time).total_seconds() / 3600  # in hours
                    durations.append(duration)
                except Exception:
                    pass
            
            if durations:
                additional_metrics["avg_trade_duration_hours"] = sum(durations) / len(durations)
    
    # Calculate volatility of returns
    if len(df) > 1:
        returns = df['portfolio_value'].pct_change().dropna()
        additional_metrics["returns_volatility"] = returns.std()
        additional_metrics["annual_volatility"] = returns.std() * np.sqrt(252 * 24)
    
    # Calculate equity curve properties
    if not df.empty:
        # Check for equity curve quality
        additional_metrics["portfolio_value_min"] = df['portfolio_value'].min()
        additional_metrics["portfolio_value_max"] = df['portfolio_value'].max()
        
        # Calculate time below high-water mark
        df['high_water_mark'] = df['portfolio_value'].cummax()
        df['pct_below_hwm'] = (df['high_water_mark'] - df['portfolio_value']) / df['high_water_mark'] * 100
        additional_metrics["avg_pct_below_hwm"] = df['pct_below_hwm'].mean()
        additional_metrics["max_time_below_hwm_hours"] = df['pct_below_hwm'].astype(bool).astype(int).groupby(df['pct_below_hwm'].eq(0).cumsum()).sum().max()
    
    # Calculate Win/Loss ratio
    if results.get("winning_trades", 0) > 0 and results.get("trades", 0) - results.get("winning_trades", 0) > 0:
        wins = results.get("winning_trades", 0)
        losses = results.get("trades", 0) - wins
        additional_metrics["win_loss_ratio"] = wins / losses
    
    return additional_metrics

def format_results_text(results: Dict[str, Any], additional_metrics: Dict[str, Any]) -> str:
    """
    Format results as text
    
    Args:
        results: Dictionary with backtest results
        additional_metrics: Dictionary with additional metrics
        
    Returns:
        Formatted text
    """
    if not results:
        return "No results to display"
    
    lines = [
        "=== BACKTEST RESULTS ===",
        f"Symbol: {results.get('symbol')}",
        f"Interval: {results.get('interval')}",
        f"Period: {results.get('start_date', 'N/A')} to {results.get('end_date', 'N/A')}",
        "",
        "--- PERFORMANCE ---",
        f"Initial Balance: ${results.get('initial_balance', 0):.2f}",
        f"Final Balance: ${results.get('final_equity', 0):.2f}",
        f"Total Return: {results.get('total_return_pct', 0):.2f}%",
        f"Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}%",
        "",
        "--- TRADING STATISTICS ---",
        f"Number of Trades: {results.get('trades', 0)}",
        f"Winning Trades: {results.get('winning_trades', 0)}",
        f"Win Rate: {results.get('win_rate', 0):.2f}%",
    ]
    
    if additional_metrics:
        lines.extend([
            "",
            "--- ADDITIONAL METRICS ---",
            f"Sharpe Ratio: {additional_metrics.get('sharpe_ratio', 0):.2f}",
            f"Profit Factor: {additional_metrics.get('profit_factor', 0):.2f}",
            f"Average Profit per Trade: ${additional_metrics.get('avg_profit_per_trade', 0):.2f}",
            f"Min Profit: ${additional_metrics.get('min_profit', 0):.2f}",
            f"Max Profit: ${additional_metrics.get('max_profit', 0):.2f}",
            f"Win/Loss Ratio: {additional_metrics.get('win_loss_ratio', 0):.2f}",
            f"Average Trade Duration: {additional_metrics.get('avg_trade_duration_hours', 0):.2f} hours",
            f"Returns Volatility (Daily): {additional_metrics.get('returns_volatility', 0):.4f}",
            f"Annualized Volatility: {additional_metrics.get('annual_volatility', 0):.4f}",
            f"Average % Below High-Water Mark: {additional_metrics.get('avg_pct_below_hwm', 0):.2f}%",
            f"Max Time Below High-Water Mark: {additional_metrics.get('max_time_below_hwm_hours', 0)} hours",
        ])
    
    return "\n".join(lines)

def format_results_markdown(results: Dict[str, Any], additional_metrics: Dict[str, Any]) -> str:
    """
    Format results as Markdown
    
    Args:
        results: Dictionary with backtest results
        additional_metrics: Dictionary with additional metrics
        
    Returns:
        Formatted markdown
    """
    if not results:
        return "# No results to display"
    
    lines = [
        "# Backtest Results Analysis",
        "",
        f"## Configuration",
        f"- **Symbol:** {results.get('symbol')}",
        f"- **Interval:** {results.get('interval')}",
        f"- **Period:** {results.get('start_date', 'N/A')} to {results.get('end_date', 'N/A')}",
        "",
        f"## Performance Metrics",
        f"- **Initial Balance:** ${results.get('initial_balance', 0):.2f}",
        f"- **Final Balance:** ${results.get('final_equity', 0):.2f}",
        f"- **Total Return:** {results.get('total_return_pct', 0):.2f}%",
        f"- **Max Drawdown:** {results.get('max_drawdown_pct', 0):.2f}%",
        "",
        f"## Trading Statistics",
        f"- **Number of Trades:** {results.get('trades', 0)}",
        f"- **Winning Trades:** {results.get('winning_trades', 0)}",
        f"- **Win Rate:** {results.get('win_rate', 0):.2f}%",
    ]
    
    if additional_metrics:
        lines.extend([
            "",
            f"## Additional Metrics",
            f"- **Sharpe Ratio:** {additional_metrics.get('sharpe_ratio', 0):.2f}",
            f"- **Profit Factor:** {additional_metrics.get('profit_factor', 0):.2f}",
            f"- **Average Profit per Trade:** ${additional_metrics.get('avg_profit_per_trade', 0):.2f}",
            f"- **Min Profit:** ${additional_metrics.get('min_profit', 0):.2f}",
            f"- **Max Profit:** ${additional_metrics.get('max_profit', 0):.2f}",
            f"- **Win/Loss Ratio:** {additional_metrics.get('win_loss_ratio', 0):.2f}",
            f"- **Average Trade Duration:** {additional_metrics.get('avg_trade_duration_hours', 0):.2f} hours",
            f"- **Returns Volatility (Daily):** {additional_metrics.get('returns_volatility', 0):.4f}",
            f"- **Annualized Volatility:** {additional_metrics.get('annual_volatility', 0):.4f}",
            f"- **Average % Below High-Water Mark:** {additional_metrics.get('avg_pct_below_hwm', 0):.2f}%",
            f"- **Max Time Below High-Water Mark:** {additional_metrics.get('max_time_below_hwm_hours', 0)} hours",
        ])
    
    return "\n".join(lines)

def save_output(output: str, output_dir: str, format_type: str) -> str:
    """
    Save output to file
    
    Args:
        output: Formatted output
        output_dir: Directory to save output
        format_type: Output format (text, json, csv, md)
        
    Returns:
        Path to output file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    extension = format_type if format_type != "text" else "txt"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_analysis_{timestamp}.{extension}"
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, 'w') as f:
        f.write(output)
    
    print(f"Analysis saved to {file_path}")
    return file_path

def main():
    args = parse_arguments()
    
    # If no file specified, use the latest file
    if not args.file:
        latest_file = None
        latest_time = 0
        
        for root, _, files in os.walk("data/logs/backtests"):
            for file in files:
                if file.startswith("simplified_backtest_results_") and file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = file_path
        
        if latest_file:
            args.file = latest_file
        else:
            print("No backtest results file found")
            return
    
    # Load backtest results
    results = load_backtest_results(args.file)
    
    if not results:
        print("No valid backtest results found")
        return
    
    # Calculate additional metrics
    additional_metrics = calculate_additional_metrics(results)
    
    # Format results based on output format
    if args.format == "text":
        output = format_results_text(results, additional_metrics)
    elif args.format == "json":
        combined_results = {**results, "additional_metrics": additional_metrics}
        output = json.dumps(combined_results, indent=2)
    elif args.format == "csv":
        # Create a flat dictionary for CSV output
        flat_dict = {
            "symbol": results.get("symbol"),
            "interval": results.get("interval"),
            "start_date": results.get("start_date"),
            "end_date": results.get("end_date"),
            "initial_balance": results.get("initial_balance"),
            "final_equity": results.get("final_equity"),
            "total_return_pct": results.get("total_return_pct"),
            "max_drawdown_pct": results.get("max_drawdown_pct"),
            "trades": results.get("trades"),
            "winning_trades": results.get("winning_trades"),
            "win_rate": results.get("win_rate"),
        }
        
        # Add additional metrics
        for key, value in additional_metrics.items():
            flat_dict[key] = value
        
        # Convert to CSV
        output = ",".join(flat_dict.keys()) + "\n" + ",".join(str(v) for v in flat_dict.values())
    elif args.format == "md":
        output = format_results_markdown(results, additional_metrics)
    else:
        output = format_results_text(results, additional_metrics)
    
    # Save output to file
    save_output(output, args.output, args.format)
    
    # Print summary to console
    print("\nSUMMARY:")
    print(f"Symbol: {results.get('symbol')}")
    print(f"Period: {results.get('start_date', 'N/A')} to {results.get('end_date', 'N/A')}")
    print(f"Total Return: {results.get('total_return_pct', 0):.2f}%")
    print(f"Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}%")
    print(f"Win Rate: {results.get('win_rate', 0):.2f}% ({results.get('winning_trades', 0)}/{results.get('trades', 0)})")
    
    if additional_metrics:
        print(f"Sharpe Ratio: {additional_metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Profit Factor: {additional_metrics.get('profit_factor', 0):.2f}")
        print(f"Win/Loss Ratio: {additional_metrics.get('win_loss_ratio', 0):.2f}")

if __name__ == "__main__":
    main()