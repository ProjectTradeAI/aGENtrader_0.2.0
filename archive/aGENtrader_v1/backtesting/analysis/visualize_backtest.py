#!/usr/bin/env python3
"""
Backtest Visualization Tool

This module provides functions for visualizing backtest results.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('backtest_visualizer')

# Set plot style
plt.style.use('seaborn-v0_8-darkgrid')

def load_backtest_results(file_path: str) -> Dict[str, Any]:
    """
    Load backtest results from a JSON file
    
    Args:
        file_path: Path to the backtest results file
        
    Returns:
        Dictionary with backtest results
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {}
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        logger.info(f"Loaded backtest results from {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading backtest results from {file_path}: {str(e)}")
        return {}

def create_equity_curve(backtest_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Create an equity curve DataFrame from backtest data
    
    Args:
        backtest_data: Dictionary with backtest results
        
    Returns:
        DataFrame with equity curve
    """
    try:
        # Get the transactions
        transactions = backtest_data.get('transactions', [])
        if not transactions:
            logger.warning("No transactions found in backtest data")
            return pd.DataFrame()
            
        # Create a DataFrame for equity curve
        equity_curve = []
        
        # Initial values
        initial_balance = backtest_data.get('initial_balance', 10000.0)
        current_balance = initial_balance
        
        # Add initial point
        start_date_str = backtest_data.get('start_date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            equity_curve.append({
                'timestamp': start_date,
                'equity': current_balance
            })
            
        # Add transaction points
        for tx in transactions:
            timestamp = tx.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
            balance_after = tx.get('balance_after', current_balance)
            current_balance = balance_after
            
            equity_curve.append({
                'timestamp': timestamp,
                'equity': current_balance
            })
            
        # Create DataFrame
        df = pd.DataFrame(equity_curve)
        
        # Sort by timestamp
        if not df.empty:
            df = df.sort_values('timestamp')
            
        return df
        
    except Exception as e:
        logger.error(f"Error creating equity curve: {str(e)}")
        return pd.DataFrame()

def analyze_trades(backtest_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Analyze trades from backtest data
    
    Args:
        backtest_data: Dictionary with backtest results
        
    Returns:
        DataFrame with trade analysis
    """
    try:
        # Get the transactions
        transactions = backtest_data.get('transactions', [])
        if not transactions:
            logger.warning("No transactions found in backtest data")
            return pd.DataFrame()
            
        # Create a list to store trade data
        trades = []
        
        # Extract trades from transactions
        position = None
        for tx in transactions:
            tx_type = tx.get('type', '').lower()
            
            # Handle different transaction types
            if tx_type == 'buy' or tx_type == 'long' or tx_type == 'entry':
                # Open position
                position = {
                    'entry_time': tx.get('timestamp'),
                    'entry_price': tx.get('price', 0.0),
                    'amount': tx.get('amount', 0.0),
                    'side': 'long'
                }
                
            elif tx_type == 'sell' or tx_type == 'short' or tx_type == 'exit':
                # Close position if we have one
                if position:
                    # Calculate P&L
                    entry_price = position.get('entry_price', 0.0)
                    exit_price = tx.get('price', 0.0)
                    amount = position.get('amount', 0.0)
                    side = position.get('side', 'long')
                    
                    if side == 'long':
                        pnl = (exit_price - entry_price) * amount
                        pnl_pct = ((exit_price / entry_price) - 1) * 100
                    else:
                        pnl = (entry_price - exit_price) * amount
                        pnl_pct = ((entry_price / exit_price) - 1) * 100
                        
                    # Add to trades list
                    trades.append({
                        'entry_time': position.get('entry_time'),
                        'exit_time': tx.get('timestamp'),
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'amount': amount,
                        'side': side,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'duration': None  # Will calculate below
                    })
                    
                    # Reset position
                    position = None
                    
        # Create DataFrame
        df = pd.DataFrame(trades)
        
        # Convert timestamps
        if not df.empty:
            if 'entry_time' in df.columns and df['entry_time'].iloc[0] and isinstance(df['entry_time'].iloc[0], str):
                df['entry_time'] = pd.to_datetime(df['entry_time'])
                
            if 'exit_time' in df.columns and df['exit_time'].iloc[0] and isinstance(df['exit_time'].iloc[0], str):
                df['exit_time'] = pd.to_datetime(df['exit_time'])
                
            # Calculate duration
            if 'entry_time' in df.columns and 'exit_time' in df.columns:
                df['duration'] = df['exit_time'] - df['entry_time']
            
        return df
        
    except Exception as e:
        logger.error(f"Error analyzing trades: {str(e)}")
        return pd.DataFrame()

def plot_equity_curve(equity_df: pd.DataFrame, trades_df: Optional[pd.DataFrame] = None, save_path: Optional[str] = None):
    """
    Plot equity curve
    
    Args:
        equity_df: DataFrame with equity curve
        trades_df: DataFrame with trade analysis (optional)
        save_path: Path to save the plot (optional)
    """
    try:
        if equity_df.empty:
            logger.warning("Cannot plot empty equity curve")
            return
            
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot equity curve
        ax.plot(equity_df['timestamp'], equity_df['equity'], label='Equity', linewidth=2)
        
        # Mark trades if available
        if trades_df is not None and not trades_df.empty:
            # Mark winning trades
            winning_trades = trades_df[trades_df['pnl'] > 0]
            if not winning_trades.empty:
                for _, trade in winning_trades.iterrows():
                    ax.axvspan(
                        trade['entry_time'], 
                        trade['exit_time'], 
                        alpha=0.2, 
                        color='green'
                    )
                    
            # Mark losing trades
            losing_trades = trades_df[trades_df['pnl'] <= 0]
            if not losing_trades.empty:
                for _, trade in losing_trades.iterrows():
                    ax.axvspan(
                        trade['entry_time'], 
                        trade['exit_time'], 
                        alpha=0.2, 
                        color='red'
                    )
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        # Format y-axis to show dollars
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.2f}'))
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add title and labels
        plt.title('Equity Curve', fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Account Balance', fontsize=12)
        
        # Add percentage change on right y-axis
        if len(equity_df) > 1:
            ax2 = ax.twinx()
            
            # Calculate percentage change
            initial_equity = equity_df['equity'].iloc[0]
            pct_change = [(eq / initial_equity - 1) * 100 for eq in equity_df['equity']]
            
            # Plot percentage change
            ax2.plot(equity_df['timestamp'], pct_change, 'r--', alpha=0.3)
            ax2.set_ylabel('Percentage Change (%)', color='red', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='red')
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}%'))
            
        # Adjust layout
        plt.tight_layout()
        
        # Save or show
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300)
            logger.info(f"Saved equity curve plot to {save_path}")
        else:
            plt.show()
            
        plt.close()
        
    except Exception as e:
        logger.error(f"Error plotting equity curve: {str(e)}")

def plot_trade_analysis(trades_df: pd.DataFrame, save_path: Optional[str] = None):
    """
    Plot trade analysis
    
    Args:
        trades_df: DataFrame with trade analysis
        save_path: Path to save the plot (optional)
    """
    try:
        if trades_df.empty:
            logger.warning("Cannot plot empty trades dataframe")
            return
            
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Profit/Loss per Trade
        ax1 = axes[0, 0]
        trade_nums = list(range(1, len(trades_df) + 1))
        colors = ['green' if pnl > 0 else 'red' for pnl in trades_df['pnl']]
        
        ax1.bar(trade_nums, trades_df['pnl'], color=colors)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.set_title('Profit/Loss per Trade', fontsize=14)
        ax1.set_xlabel('Trade Number', fontsize=12)
        ax1.set_ylabel('Profit/Loss ($)', fontsize=12)
        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.2f}'))
        
        # 2. Cumulative Profit/Loss
        ax2 = axes[0, 1]
        cumulative_pnl = trades_df['pnl'].cumsum()
        
        ax2.plot(trade_nums, cumulative_pnl, marker='o', linestyle='-', color='blue')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Cumulative Profit/Loss', fontsize=14)
        ax2.set_xlabel('Trade Number', fontsize=12)
        ax2.set_ylabel('Cumulative P/L ($)', fontsize=12)
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.2f}'))
        
        # 3. Win/Loss Distribution
        ax3 = axes[1, 0]
        win_count = (trades_df['pnl'] > 0).sum()
        loss_count = (trades_df['pnl'] <= 0).sum()
        
        ax3.pie(
            [win_count, loss_count],
            labels=['Wins', 'Losses'],
            colors=['green', 'red'],
            autopct='%1.1f%%',
            startangle=90
        )
        ax3.set_title('Win/Loss Distribution', fontsize=14)
        
        # 4. Trade Duration Distribution
        ax4 = axes[1, 1]
        
        if 'duration' in trades_df.columns:
            # Convert duration to hours if it's a timedelta
            if pd.api.types.is_timedelta64_dtype(trades_df['duration']):
                duration_hours = trades_df['duration'].dt.total_seconds() / 3600
            else:
                duration_hours = trades_df['duration']
                
            ax4.hist(duration_hours, bins=10, color='skyblue', edgecolor='black')
            ax4.set_title('Trade Duration Distribution', fontsize=14)
            ax4.set_xlabel('Duration (hours)', fontsize=12)
            ax4.set_ylabel('Frequency', fontsize=12)
        else:
            ax4.set_title('Trade Duration Distribution (No Data)', fontsize=14)
            
        # Adjust layout
        plt.tight_layout()
        
        # Save or show
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300)
            logger.info(f"Saved trade analysis plot to {save_path}")
        else:
            plt.show()
            
        plt.close()
        
    except Exception as e:
        logger.error(f"Error plotting trade analysis: {str(e)}")

def generate_performance_metrics(backtest_data: Dict[str, Any], trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate performance metrics from backtest data
    
    Args:
        backtest_data: Dictionary with backtest results
        trades_df: DataFrame with trade analysis
        
    Returns:
        Dictionary with performance metrics
    """
    metrics = {}
    
    try:
        # Basic metrics
        initial_balance = backtest_data.get('initial_balance', 10000.0)
        final_balance = backtest_data.get('final_balance', initial_balance)
        
        absolute_return = final_balance - initial_balance
        percent_return = (absolute_return / initial_balance) * 100
        
        metrics['initial_balance'] = initial_balance
        metrics['final_balance'] = final_balance
        metrics['absolute_return'] = absolute_return
        metrics['percent_return'] = percent_return
        
        # Trade metrics
        if not trades_df.empty:
            total_trades = len(trades_df)
            winning_trades = (trades_df['pnl'] > 0).sum()
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Average metrics
            avg_profit = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
            
            # Profit factor
            gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
            gross_loss = abs(trades_df[trades_df['pnl'] <= 0]['pnl'].sum())
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
            
            # Maximum drawdown
            if 'equity' in backtest_data:
                equity_series = pd.Series(backtest_data['equity'])
                running_max = equity_series.cummax()
                drawdown = (equity_series - running_max) / running_max * 100
                max_drawdown = abs(drawdown.min())
            else:
                max_drawdown = None
                
            # Add to metrics
            metrics['total_trades'] = total_trades
            metrics['winning_trades'] = winning_trades
            metrics['losing_trades'] = losing_trades
            metrics['win_rate'] = win_rate
            metrics['avg_profit'] = avg_profit
            metrics['avg_loss'] = avg_loss
            metrics['profit_factor'] = profit_factor
            metrics['max_drawdown'] = max_drawdown
            
            # Risk-adjusted return
            if max_drawdown and max_drawdown > 0:
                metrics['return_to_drawdown'] = percent_return / max_drawdown
            else:
                metrics['return_to_drawdown'] = None
                
            # Average trade duration
            if 'duration' in trades_df.columns and pd.api.types.is_timedelta64_dtype(trades_df['duration']):
                avg_duration = trades_df['duration'].mean()
                metrics['avg_duration'] = avg_duration.total_seconds() / 3600  # in hours
            else:
                metrics['avg_duration'] = None
            
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating performance metrics: {str(e)}")
        return metrics

def generate_performance_summary(backtest_data: Dict[str, Any], trades_df: pd.DataFrame) -> str:
    """
    Generate a text summary of backtest performance
    
    Args:
        backtest_data: Dictionary with backtest results
        trades_df: DataFrame with trade analysis
        
    Returns:
        Text summary of performance
    """
    try:
        # Get performance metrics
        metrics = generate_performance_metrics(backtest_data, trades_df)
        
        # Format summary
        summary = []
        summary.append("========== BACKTEST PERFORMANCE SUMMARY ==========")
        summary.append(f"Symbol: {backtest_data.get('symbol', 'Unknown')}")
        summary.append(f"Interval: {backtest_data.get('interval', 'Unknown')}")
        summary.append(f"Period: {backtest_data.get('start_date', 'Unknown')} to {backtest_data.get('end_date', 'Unknown')}")
        summary.append("")
        
        summary.append("--- Account Performance ---")
        summary.append(f"Initial Balance: ${metrics.get('initial_balance', 0):,.2f}")
        summary.append(f"Final Balance: ${metrics.get('final_balance', 0):,.2f}")
        summary.append(f"Absolute Return: ${metrics.get('absolute_return', 0):,.2f}")
        summary.append(f"Percent Return: {metrics.get('percent_return', 0):.2f}%")
        
        if 'max_drawdown' in metrics and metrics['max_drawdown'] is not None:
            summary.append(f"Maximum Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            
        if 'return_to_drawdown' in metrics and metrics['return_to_drawdown'] is not None:
            summary.append(f"Return/Drawdown Ratio: {metrics.get('return_to_drawdown', 0):.2f}")
            
        summary.append("")
        
        if not trades_df.empty:
            summary.append("--- Trade Statistics ---")
            summary.append(f"Total Trades: {metrics.get('total_trades', 0)}")
            summary.append(f"Winning Trades: {metrics.get('winning_trades', 0)} ({metrics.get('win_rate', 0):.2f}%)")
            summary.append(f"Losing Trades: {metrics.get('losing_trades', 0)} ({100 - metrics.get('win_rate', 0):.2f}%)")
            
            if 'avg_profit' in metrics and metrics['avg_profit'] is not None:
                summary.append(f"Average Profit: ${metrics.get('avg_profit', 0):,.2f}")
                
            if 'avg_loss' in metrics and metrics['avg_loss'] is not None:
                summary.append(f"Average Loss: ${metrics.get('avg_loss', 0):,.2f}")
                
            if 'profit_factor' in metrics and metrics['profit_factor'] is not None:
                if metrics['profit_factor'] == float('inf'):
                    summary.append(f"Profit Factor: ∞ (No losing trades)")
                else:
                    summary.append(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
                    
            if 'avg_duration' in metrics and metrics['avg_duration'] is not None:
                summary.append(f"Average Trade Duration: {metrics.get('avg_duration', 0):.1f} hours")
                
        summary.append("")
        summary.append("=====================================================")
        
        return "\n".join(summary)
        
    except Exception as e:
        logger.error(f"Error generating performance summary: {str(e)}")
        return f"Error generating performance summary: {str(e)}"

def analyze_and_visualize_backtest(
    backtest_file: str,
    output_dir: Optional[str] = None,
    base_filename: Optional[str] = None
) -> Dict[str, str]:
    """
    Analyze and visualize backtest results
    
    Args:
        backtest_file: Path to backtest results file
        output_dir: Directory to save output files (optional)
        base_filename: Base filename for output files (optional)
        
    Returns:
        Dictionary with paths to output files
    """
    results = {}
    
    try:
        # Load backtest results
        backtest_data = load_backtest_results(backtest_file)
        if not backtest_data:
            logger.error(f"Failed to load backtest results from {backtest_file}")
            return results
            
        # Create output directory if needed
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Generate base filename if not provided
        if not base_filename:
            run_id = backtest_data.get('run_id')
            if run_id:
                base_filename = run_id
            else:
                base_filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
        # Create equity curve
        equity_df = create_equity_curve(backtest_data)
        
        # Analyze trades
        trades_df = analyze_trades(backtest_data)
        
        # Plot equity curve
        if not equity_df.empty:
            equity_plot_path = None
            if output_dir:
                equity_plot_path = os.path.join(output_dir, f"{base_filename}_equity.png")
                
            plot_equity_curve(equity_df, trades_df, equity_plot_path)
            
            if equity_plot_path:
                results['equity_plot'] = equity_plot_path
                
        # Plot trade analysis
        if not trades_df.empty:
            trades_plot_path = None
            if output_dir:
                trades_plot_path = os.path.join(output_dir, f"{base_filename}_trades.png")
                
            plot_trade_analysis(trades_df, trades_plot_path)
            
            if trades_plot_path:
                results['trades_plot'] = trades_plot_path
                
        # Generate performance summary
        summary = generate_performance_summary(backtest_data, trades_df)
        
        summary_path = None
        if output_dir:
            summary_path = os.path.join(output_dir, f"{base_filename}_summary.txt")
            with open(summary_path, 'w') as f:
                f.write(summary)
                
            results['summary'] = summary_path
        
        # Print summary
        print(summary)
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing and visualizing backtest: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return results

def main():
    """Main function"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze and visualize backtest results')
    parser.add_argument('--backtest-file', '-f', type=str, required=True, help='Path to backtest results file')
    parser.add_argument('--output-dir', '-o', type=str, default='data/analysis', help='Directory to save output files')
    parser.add_argument('--base-filename', '-b', type=str, help='Base filename for output files')
    
    args = parser.parse_args()
    
    # Analyze and visualize backtest
    analyze_and_visualize_backtest(
        backtest_file=args.backtest_file,
        output_dir=args.output_dir,
        base_filename=args.base_filename
    )

if __name__ == '__main__':
    main()