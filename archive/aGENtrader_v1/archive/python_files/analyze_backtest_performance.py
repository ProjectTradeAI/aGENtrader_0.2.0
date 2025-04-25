#!/usr/bin/env python3
"""
Backtest Performance Analyzer

This script analyzes and visualizes the performance of a backtest result.
"""

import os
import json
import argparse
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional

def load_backtest_data(backtest_id: str) -> Dict[str, Any]:
    """
    Load backtest data from JSON files.
    
    Args:
        backtest_id: The ID of the backtest to analyze
        
    Returns:
        A dictionary containing the backtest data
    """
    # Try to find the backtest files
    summary_path = f"data/backtests/summary_{backtest_id}.json"
    backtest_path = f"data/backtests/backtest_{backtest_id}.json"
    
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Summary file not found: {summary_path}")
    
    if not os.path.exists(backtest_path):
        raise FileNotFoundError(f"Backtest file not found: {backtest_path}")
    
    # Load the data
    with open(summary_path, 'r') as f:
        summary_data = json.load(f)
    
    with open(backtest_path, 'r') as f:
        backtest_data = json.load(f)
    
    return {
        "summary": summary_data,
        "backtest": backtest_data
    }

def create_equity_curve(backtest_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Create an equity curve dataframe from backtest data.
    
    Args:
        backtest_data: Dictionary containing backtest data
        
    Returns:
        DataFrame with datetime index and equity column
    """
    # Extract balance history if available
    if "balance_history" in backtest_data["backtest"]:
        balance_history = backtest_data["backtest"]["balance_history"]
        
        # Convert to DataFrame
        equity_data = []
        for entry in balance_history:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            balance = entry["balance"]
            equity_data.append({"timestamp": timestamp, "equity": balance})
        
        equity_df = pd.DataFrame(equity_data)
        equity_df.set_index("timestamp", inplace=True)
        
        return equity_df
    
    # If balance history not available, reconstruct from trades
    elif "trades" in backtest_data["backtest"] and len(backtest_data["backtest"]["trades"]) > 0:
        initial_balance = backtest_data["summary"]["metrics"]["initial_balance"]
        trades = backtest_data["backtest"]["trades"]
        
        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda x: x["entry_time"])
        
        # Create equity curve points
        equity_data = []
        current_balance = initial_balance
        
        # Add starting point
        start_time = datetime.fromisoformat(sorted_trades[0]["entry_time"])
        equity_data.append({"timestamp": start_time, "equity": current_balance})
        
        # Add points after each trade
        for trade in sorted_trades:
            exit_time = datetime.fromisoformat(trade["exit_time"])
            pnl_abs = trade["pnl_abs"] * current_balance / 100
            current_balance += pnl_abs
            equity_data.append({"timestamp": exit_time, "equity": current_balance})
        
        equity_df = pd.DataFrame(equity_data)
        equity_df.set_index("timestamp", inplace=True)
        
        return equity_df
    
    else:
        # Create a minimal equity curve with just initial and final balance
        summary = backtest_data["summary"]
        initial_balance = summary["metrics"]["initial_balance"]
        final_balance = summary["metrics"]["final_balance"]
        
        start_date = datetime.fromisoformat(summary["config"]["start_date"])
        end_date = datetime.fromisoformat(summary["config"]["end_date"])
        
        equity_data = [
            {"timestamp": start_date, "equity": initial_balance},
            {"timestamp": end_date, "equity": final_balance}
        ]
        
        equity_df = pd.DataFrame(equity_data)
        equity_df.set_index("timestamp", inplace=True)
        
        return equity_df

def analyze_trades(backtest_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Analyze the trades in a backtest.
    
    Args:
        backtest_data: Dictionary containing backtest data
        
    Returns:
        DataFrame with trade analysis
    """
    if "trades" not in backtest_data["backtest"]:
        raise KeyError("Trades not found in backtest data")
    
    trades = backtest_data["backtest"]["trades"]
    
    # Convert to DataFrame
    trades_df = pd.DataFrame(trades)
    
    if len(trades_df) == 0:
        return pd.DataFrame()
    
    # Convert time columns to datetime
    trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"])
    trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])
    
    # Calculate additional metrics
    trades_df["duration"] = (trades_df["exit_time"] - trades_df["entry_time"]).dt.total_seconds() / 3600
    trades_df["profitable"] = trades_df["pnl_pct"] > 0
    
    return trades_df

def plot_equity_curve(equity_df: pd.DataFrame, trades_df: Optional[pd.DataFrame] = None, save_path: Optional[str] = None):
    """
    Plot the equity curve and trades.
    
    Args:
        equity_df: DataFrame with equity curve
        trades_df: DataFrame with trade information
        save_path: Path to save the plot, if None the plot is displayed
    """
    plt.figure(figsize=(14, 8))
    
    # Plot equity curve
    plt.plot(equity_df.index, equity_df["equity"], label="Equity", color="blue")
    
    # Add trades if available
    if trades_df is not None and len(trades_df) > 0:
        for _, trade in trades_df.iterrows():
            color = "green" if trade["profitable"] else "red"
            plt.axvspan(trade["entry_time"], trade["exit_time"], alpha=0.2, color=color)
    
    # Format plot
    plt.title("Equity Curve", fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Balance", fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Add initial and final balance
    if len(equity_df) > 1:
        initial_balance = equity_df["equity"].iloc[0]
        final_balance = equity_df["equity"].iloc[-1]
        plt.axhline(y=initial_balance, color="gray", linestyle="--", label=f"Initial Balance: ${initial_balance:.2f}")
        
        # Calculate drawdown
        rolling_max = equity_df["equity"].cummax()
        drawdown = 100 * ((rolling_max - equity_df["equity"]) / rolling_max)
        max_drawdown = drawdown.max()
        
        # Add annotations
        plt.figtext(0.15, 0.02, f"Final Balance: ${final_balance:.2f}", fontsize=12)
        plt.figtext(0.4, 0.02, f"Return: {100 * (final_balance/initial_balance - 1):.2f}%", fontsize=12)
        plt.figtext(0.65, 0.02, f"Max Drawdown: {max_drawdown:.2f}%", fontsize=12)
    
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"Equity curve saved to {save_path}")
    else:
        plt.show()

def plot_trade_analysis(trades_df: pd.DataFrame, save_path: Optional[str] = None):
    """
    Plot trade analysis charts.
    
    Args:
        trades_df: DataFrame with trade information
        save_path: Path to save the plot, if None the plot is displayed
    """
    if len(trades_df) == 0:
        print("No trades to analyze")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: PnL Distribution
    axes[0, 0].hist(trades_df["pnl_pct"], bins=10, color="skyblue", edgecolor="black")
    axes[0, 0].set_title("PnL Distribution (%)")
    axes[0, 0].set_xlabel("PnL %")
    axes[0, 0].set_ylabel("Frequency")
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Cumulative PnL
    cumulative_pnl = trades_df["pnl_pct"].cumsum()
    axes[0, 1].plot(range(len(cumulative_pnl)), cumulative_pnl, marker='o', color="green")
    axes[0, 1].set_title("Cumulative PnL (%)")
    axes[0, 1].set_xlabel("Trade #")
    axes[0, 1].set_ylabel("Cumulative PnL %")
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Win vs Loss by Position Type
    if "position_type" in trades_df.columns:
        position_results = trades_df.groupby(["position_type", "profitable"]).size().unstack()
        position_results.plot(kind="bar", ax=axes[1, 0], stacked=True, color=["red", "green"])
        axes[1, 0].set_title("Win vs Loss by Position Type")
        axes[1, 0].set_xlabel("Position Type")
        axes[1, 0].set_ylabel("Count")
        axes[1, 0].legend(["Loss", "Win"])
        axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Trade Duration vs PnL
    axes[1, 1].scatter(trades_df["duration"], trades_df["pnl_pct"], 
                       c=trades_df["profitable"].map({True: "green", False: "red"}), alpha=0.7)
    axes[1, 1].set_title("Trade Duration vs PnL")
    axes[1, 1].set_xlabel("Duration (hours)")
    axes[1, 1].set_ylabel("PnL %")
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
        print(f"Trade analysis saved to {save_path}")
    else:
        plt.show()

def generate_performance_summary(backtest_data: Dict[str, Any], trades_df: pd.DataFrame) -> str:
    """
    Generate a text summary of the backtest performance.
    
    Args:
        backtest_data: Dictionary containing backtest data
        trades_df: DataFrame with trade information
        
    Returns:
        String containing the performance summary
    """
    summary = backtest_data["summary"]
    metrics = summary.get("metrics", {})
    config = summary.get("config", {})
    
    initial_balance = metrics.get("initial_balance", 0)
    final_balance = metrics.get("final_balance", 0)
    
    # Format summary
    lines = []
    lines.append("=" * 50)
    lines.append("BACKTEST PERFORMANCE SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Test ID: {summary.get('test_id', 'Unknown')}")
    lines.append(f"Symbol: {config.get('symbol', 'Unknown')}")
    lines.append(f"Interval: {config.get('interval', 'Unknown')}")
    lines.append(f"Period: {config.get('start_date', 'Unknown')} to {config.get('end_date', 'Unknown')}")
    lines.append(f"Initial Balance: ${initial_balance:.2f}")
    lines.append(f"Final Balance: ${final_balance:.2f}")
    lines.append(f"Absolute Return: ${metrics.get('absolute_return', 0):.2f}")
    lines.append(f"Total Return: {metrics.get('total_return', 0):.2f}%")
    lines.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    lines.append(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
    lines.append("-" * 50)
    lines.append("TRADE STATISTICS")
    lines.append("-" * 50)
    lines.append(f"Total Trades: {metrics.get('total_trades', 0)}")
    lines.append(f"Profitable Trades: {metrics.get('profitable_trades', 0)}")
    lines.append(f"Losing Trades: {metrics.get('losing_trades', 0)}")
    lines.append(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
    lines.append(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    lines.append(f"Average Profit: {metrics.get('avg_profit', 0):.2f}%")
    lines.append(f"Average Loss: {metrics.get('avg_loss', 0):.2f}%")
    lines.append(f"Max Profit: {metrics.get('max_profit', 0):.2f}%")
    lines.append(f"Max Loss: {metrics.get('max_loss', 0):.2f}%")
    lines.append(f"Average Hold Time: {metrics.get('avg_hold_time', 0):.2f} hours")
    
    # Add position type breakdown if trades exist
    if len(trades_df) > 0 and "position_type" in trades_df.columns:
        lines.append("-" * 50)
        lines.append("POSITION TYPE BREAKDOWN")
        lines.append("-" * 50)
        position_count = trades_df["position_type"].value_counts()
        for position_type, count in position_count.items():
            lines.append(f"{position_type.capitalize()}: {count} trades")
        
        # Calculate win rate by position type
        position_results = trades_df.groupby(["position_type"])["profitable"].mean() * 100
        for position_type, win_rate in position_results.items():
            lines.append(f"{position_type.capitalize()} Win Rate: {win_rate:.2f}%")
            
        # Calculate average profit by position type
        avg_profit_by_type = trades_df.groupby(["position_type"])["pnl_pct"].mean()
        for position_type, avg_profit in avg_profit_by_type.items():
            lines.append(f"{position_type.capitalize()} Avg PnL: {avg_profit:.2f}%")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Analyze and visualize backtest performance")
    parser.add_argument("backtest_id", help="ID of the backtest to analyze")
    parser.add_argument("--output-dir", help="Directory to save output files", default="data/analysis")
    args = parser.parse_args()
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Load backtest data
        backtest_data = load_backtest_data(args.backtest_id)
        
        # Create equity curve
        equity_df = create_equity_curve(backtest_data)
        
        # Analyze trades
        trades_df = analyze_trades(backtest_data)
        
        # Generate performance summary
        summary_text = generate_performance_summary(backtest_data, trades_df)
        print(summary_text)
        
        # Save summary to file
        summary_path = os.path.join(args.output_dir, f"{args.backtest_id}_summary.txt")
        with open(summary_path, 'w') as f:
            f.write(summary_text)
        print(f"Summary saved to {summary_path}")
        
        # Plot equity curve
        equity_curve_path = os.path.join(args.output_dir, f"{args.backtest_id}_equity.png")
        plot_equity_curve(equity_df, trades_df, equity_curve_path)
        
        # Plot trade analysis
        if len(trades_df) > 0:
            trade_analysis_path = os.path.join(args.output_dir, f"{args.backtest_id}_trades.png")
            plot_trade_analysis(trades_df, trade_analysis_path)
        
    except Exception as e:
        print(f"Error analyzing backtest: {str(e)}")

if __name__ == "__main__":
    main()