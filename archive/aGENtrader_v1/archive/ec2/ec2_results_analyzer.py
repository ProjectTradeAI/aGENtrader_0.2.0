#!/usr/bin/env python3
"""
EC2 Results Analyzer

This script analyzes trading test results from EC2 and generates comparison reports.
It can be used locally after pulling results from EC2.
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

def load_result_file(filepath: str) -> Dict[str, Any]:
    """
    Load a result file.
    
    Args:
        filepath: Path to result file
        
    Returns:
        Dictionary with results data
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def load_result_directory(directory: str, pattern: str = "*.json") -> List[Dict[str, Any]]:
    """
    Load all result files in a directory.
    
    Args:
        directory: Directory containing result files
        pattern: File pattern to match
        
    Returns:
        List of result dictionaries
    """
    result_files = glob.glob(os.path.join(directory, pattern))
    results = []
    
    for filepath in result_files:
        result = load_result_file(filepath)
        if result:
            result['_filename'] = os.path.basename(filepath)
            results.append(result)
    
    return results

def calculate_additional_metrics(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate additional performance metrics.
    
    Args:
        result: Dictionary with test results
        
    Returns:
        Dictionary with additional metrics
    """
    metrics = {}
    
    # Extract basic metrics
    metrics['net_profit'] = result.get('net_profit', 0)
    metrics['return_pct'] = result.get('return_pct', 0)
    metrics['win_rate'] = result.get('win_rate', 0)
    metrics['profit_factor'] = result.get('profit_factor', 0)
    metrics['max_drawdown'] = result.get('max_drawdown_pct', 0)
    metrics['sharpe_ratio'] = result.get('sharpe_ratio', 0)
    
    # Calculate average trade
    total_trades = result.get('total_trades', 0)
    if total_trades > 0:
        metrics['avg_trade'] = metrics['net_profit'] / total_trades
    else:
        metrics['avg_trade'] = 0
    
    # Calculate risk-adjusted return
    if metrics['max_drawdown'] > 0:
        metrics['return_to_drawdown'] = metrics['return_pct'] / metrics['max_drawdown']
    else:
        metrics['return_to_drawdown'] = float('inf')
    
    # Calculate expectancy
    win_rate = metrics['win_rate'] / 100.0  # Convert to decimal
    avg_win = result.get('avg_win', 0)
    avg_loss = abs(result.get('avg_loss', 0))
    
    if avg_loss > 0:
        metrics['win_loss_ratio'] = avg_win / avg_loss
    else:
        metrics['win_loss_ratio'] = float('inf')
        
    metrics['expectancy'] = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    return metrics

def format_metrics_table(results: List[Dict[str, Any]], sort_by: str = 'net_profit') -> str:
    """
    Format results as a comparison table.
    
    Args:
        results: List of result dictionaries
        sort_by: Metric to sort by
        
    Returns:
        Formatted table string
    """
    # Calculate metrics for all results
    for result in results:
        result['_metrics'] = calculate_additional_metrics(result)
    
    # Sort results
    sorted_results = sorted(results, key=lambda x: x['_metrics'].get(sort_by, 0), reverse=True)
    
    # Format table header
    output = []
    output.append("=" * 120)
    output.append("TRADING TEST RESULTS COMPARISON")
    output.append("=" * 120)
    
    headers = ["Filename", "Strategy", "Return%", "Profit", "Trades", "Win%", "PF", "Sharpe", "Max DD%", "Ret/DD", "Expectancy"]
    header_format = "{:<30} {:<10} {:>8} {:>10} {:>7} {:>7} {:>7} {:>7} {:>8} {:>7} {:>10}"
    output.append(header_format.format(*headers))
    output.append("-" * 120)
    
    # Add rows
    row_format = "{:<30} {:<10} {:>8.2f} ${:>9.2f} {:>7} {:>6.1f}% {:>7.2f} {:>7.2f} {:>7.1f}% {:>7.2f} ${:>9.2f}"
    
    for result in sorted_results:
        metrics = result['_metrics']
        strategy = result.get('strategy', 'unknown')
        filename = result.get('_filename', 'unknown')
        
        if len(filename) > 30:
            filename = filename[:27] + "..."
        
        output.append(row_format.format(
            filename,
            strategy,
            metrics['return_pct'],
            metrics['net_profit'],
            result.get('total_trades', 0),
            metrics['win_rate'],
            metrics['profit_factor'],
            metrics['sharpe_ratio'],
            metrics['max_drawdown'],
            metrics['return_to_drawdown'],
            metrics['expectancy']
        ))
    
    output.append("=" * 120)
    return "\n".join(output)

def generate_summary_report(results: List[Dict[str, Any]], output_file: Optional[str] = None) -> str:
    """
    Generate a summary report of all results.
    
    Args:
        results: List of result dictionaries
        output_file: Path to save the report (optional)
        
    Returns:
        Report string
    """
    # Group results by strategy
    strategies = {}
    for result in results:
        strategy = result.get('strategy', 'unknown')
        if strategy not in strategies:
            strategies[strategy] = []
        strategies[strategy].append(result)
    
    # Calculate averages by strategy
    strategy_summaries = {}
    for strategy, strategy_results in strategies.items():
        total_count = len(strategy_results)
        
        # Initialize summary with zeros
        summary = {
            'count': total_count,
            'net_profit': 0,
            'return_pct': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'max_drawdown_pct': 0,
            'avg_trade': 0,
            'expectancy': 0
        }
        
        # Calculate averages
        for result in strategy_results:
            metrics = calculate_additional_metrics(result)
            summary['net_profit'] += metrics['net_profit']
            summary['return_pct'] += metrics['return_pct']
            summary['win_rate'] += metrics['win_rate']
            summary['profit_factor'] += metrics['profit_factor']
            summary['sharpe_ratio'] += metrics['sharpe_ratio']
            summary['max_drawdown_pct'] += metrics['max_drawdown']
            summary['avg_trade'] += metrics['avg_trade']
            summary['expectancy'] += metrics['expectancy']
        
        # Divide by count to get averages
        for key in summary:
            if key != 'count':
                summary[key] /= total_count
        
        strategy_summaries[strategy] = summary
    
    # Format report
    output = []
    output.append("=" * 100)
    output.append("STRATEGY SUMMARY REPORT")
    output.append("=" * 100)
    
    # Strategy comparison table
    headers = ["Strategy", "Tests", "Avg Return%", "Avg Profit", "Avg Win%", "Avg PF", "Avg Sharpe", "Avg Max DD%", "Avg Expectancy"]
    header_format = "{:<15} {:>6} {:>12} {:>12} {:>10} {:>10} {:>12} {:>12} {:>15}"
    output.append(header_format.format(*headers))
    output.append("-" * 100)
    
    row_format = "{:<15} {:>6} {:>11.2f}% ${:>11.2f} {:>9.1f}% {:>10.2f} {:>12.2f} {:>11.1f}% ${:>14.2f}"
    
    # Sort strategies by average return
    sorted_strategies = sorted(strategy_summaries.keys(), 
                              key=lambda s: strategy_summaries[s]['return_pct'],
                              reverse=True)
    
    for strategy in sorted_strategies:
        summary = strategy_summaries[strategy]
        output.append(row_format.format(
            strategy,
            int(summary['count']),
            summary['return_pct'],
            summary['net_profit'],
            summary['win_rate'],
            summary['profit_factor'],
            summary['sharpe_ratio'],
            summary['max_drawdown_pct'],
            summary['expectancy']
        ))
    
    output.append("=" * 100)
    
    # Best performing tests
    output.append("\nTOP 5 PERFORMING TESTS")
    output.append("-" * 100)
    
    # Sort all results by return percentage
    sorted_results = sorted(results, key=lambda x: x.get('return_pct', 0), reverse=True)
    top_results = sorted_results[:5]
    
    for i, result in enumerate(top_results):
        metrics = calculate_additional_metrics(result)
        filename = result.get('_filename', 'unknown')
        strategy = result.get('strategy', 'unknown')
        
        output.append(f"{i+1}. {filename} (Strategy: {strategy})")
        output.append(f"   Return: {metrics['return_pct']:.2f}%, Profit: ${metrics['net_profit']:.2f}, Win Rate: {metrics['win_rate']:.1f}%")
        output.append(f"   Profit Factor: {metrics['profit_factor']:.2f}, Sharpe: {metrics['sharpe_ratio']:.2f}, Max Drawdown: {metrics['max_drawdown']:.1f}%")
        output.append(f"   Trades: {result.get('total_trades', 0)}, Expectancy: ${metrics['expectancy']:.2f}")
        output.append("")
    
    output.append("=" * 100)
    
    # Create final report
    report = "\n".join(output)
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Summary report saved to {output_file}")
    
    return report

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Analyze EC2 trading test results')
    parser.add_argument('--dir', type=str, default='results', help='Directory containing result files')
    parser.add_argument('--pattern', type=str, default='*.json', help='Pattern to match result files')
    parser.add_argument('--sort', type=str, default='net_profit', help='Metric to sort by')
    parser.add_argument('--output', type=str, help='Output file for summary report')
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.isdir(args.dir):
        print(f"Error: Directory '{args.dir}' not found")
        return 1
    
    # Load results
    results = load_result_directory(args.dir, args.pattern)
    
    if not results:
        print(f"No result files found in '{args.dir}' matching pattern '{args.pattern}'")
        return 1
    
    print(f"Loaded {len(results)} result files")
    
    # Display metrics table
    table = format_metrics_table(results, args.sort)
    print(table)
    
    # Generate summary report
    report = generate_summary_report(results, args.output)
    
    if not args.output:
        print("\n" + report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())