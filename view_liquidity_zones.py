#!/usr/bin/env python
"""
aGENtrader v2 Liquidity Zones Visualizer

This script provides a visualization tool for examining liquidity zones,
support/resistance clusters, and entry/stop-loss recommendations from
the LiquidityAnalystAgent.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Import project modules
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from binance_data_provider import BinanceDataProvider
from market_data_provider_factory import MarketDataProviderFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('liquidity_zones')

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Visualize liquidity zones, support/resistance clusters, and entry/stop-loss recommendations.'
    )
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                        help='Trading symbol to analyze (default: BTC/USDT)')
    parser.add_argument('--limit', type=int, default=100,
                        help='Number of order book levels to fetch (default: 100)')
    parser.add_argument('--save', action='store_true',
                        help='Save the plot to a file instead of displaying it')
    parser.add_argument('--output', type=str, default='liquidity_zones.png',
                        help='Output file name for saved plot (default: liquidity_zones.png)')
    return parser.parse_args()

def fetch_order_book(symbol: str, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch order book data from Binance.
    
    Args:
        symbol: Trading symbol (e.g., "BTC/USDT")
        limit: Maximum number of price levels to return
        
    Returns:
        Dictionary containing order book data
    """
    try:
        # Create data provider
        data_provider_factory = MarketDataProviderFactory()
        data_provider = data_provider_factory.get_provider("binance")
        
        if not data_provider:
            logger.error("Failed to initialize data provider")
            return {}
        
        # Fetch order book
        logger.info(f"Fetching order book data for {symbol} with limit {limit}")
        order_book = data_provider.fetch_market_depth(symbol, limit=limit)
        
        return order_book
    except Exception as e:
        logger.error(f"Error fetching order book: {str(e)}")
        return {}

def analyze_liquidity(symbol: str, limit: int = 100) -> Dict[str, Any]:
    """
    Analyze liquidity for a trading pair.
    
    Args:
        symbol: Trading symbol (e.g., "BTC/USDT")
        limit: Maximum number of price levels to return
        
    Returns:
        Dictionary containing liquidity analysis
    """
    try:
        # Create data provider
        data_provider_factory = MarketDataProviderFactory()
        data_provider = data_provider_factory.get_provider("binance")
        
        if not data_provider:
            logger.error("Failed to initialize data provider")
            return {}
            
        # Create liquidity analyst agent
        agent = LiquidityAnalystAgent(data_fetcher=data_provider)
        
        # Analyze liquidity
        logger.info(f"Analyzing liquidity for {symbol}")
        result = agent.analyze(symbol)
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing liquidity: {str(e)}")
        return {}

def plot_liquidity_zones(analysis_result: Dict[str, Any], save: bool = False, output: str = 'liquidity_zones.png'):
    """
    Plot liquidity zones, support/resistance clusters, and entry/stop-loss recommendations.
    
    Args:
        analysis_result: Liquidity analysis result from LiquidityAnalystAgent
        save: Whether to save the plot to a file
        output: Output file name for saved plot
    """
    if not analysis_result:
        logger.error("Empty analysis result")
        # Create error message plot
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "Error: Empty analysis result", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        
        if save:
            plt.savefig(output, dpi=150)
            logger.info(f"Error plot saved as {output}")
        else:
            plt.show()
        return
    
    # Extract data
    symbol = analysis_result.get('symbol', 'Unknown')
    current_price = analysis_result.get('current_price', 0)
    metrics = analysis_result.get('metrics', {})
    
    # Get liquidity zones
    liquidity_zones = metrics.get('liquidity_zones', {})
    support_clusters = liquidity_zones.get('support_clusters', [])
    resistance_clusters = liquidity_zones.get('resistance_clusters', [])
    gaps = liquidity_zones.get('gaps', [])
    
    # Get entry and stop-loss zones
    entry_zone = metrics.get('suggested_entry')
    stop_loss_zone = metrics.get('suggested_stop_loss')
    
    # Get order book data
    top_bids = metrics.get('top_bids', [])
    top_asks = metrics.get('top_asks', [])
    
    # Check if we have valid order book data
    if not top_bids or not top_asks:
        logger.error("Empty order book data")
        # Create error message plot
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Error: No order book data available for {symbol}\nAPI might be unavailable in this region", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        
        if save:
            plt.savefig(output, dpi=150)
            logger.info(f"Error plot saved as {output}")
        else:
            plt.show()
        return
    
    try:
        # Format prices and volumes for plotting
        bid_prices = [float(price) for price, _ in top_bids if price is not None]
        bid_volumes = [float(volume) for _, volume in top_bids if volume is not None]
        ask_prices = [float(price) for price, _ in top_asks if price is not None]
        ask_volumes = [float(volume) for _, volume in top_asks if volume is not None]
        
        # Check for empty lists after filtering None values
        if not bid_prices or not ask_prices:
            logger.error("No valid prices in order book")
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, f"Error: No valid prices in order book for {symbol}", 
                    horizontalalignment='center', verticalalignment='center', fontsize=14)
            plt.axis('off')
            
            if save:
                plt.savefig(output, dpi=150)
                logger.info(f"Error plot saved as {output}")
            else:
                plt.show()
            return
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [1, 3]})
        
        # Set title
        fig.suptitle(f'Liquidity Analysis for {symbol}', fontsize=16)
        
        # Plot 1: Volume distribution (horizontal bar chart)
        ax1.barh(range(len(bid_prices)), bid_volumes, height=0.8, color='green', alpha=0.7, label='Bids')
        ax1.barh(range(len(ask_prices)), [-vol for vol in ask_volumes], height=0.8, color='red', alpha=0.7, label='Asks')
        
        # Add y-axis labels (prices)
        bid_labels = [f"{price:.2f}" for price in bid_prices]
        ask_labels = [f"{price:.2f}" for price in ask_prices]
        
        # Combine labels and determine positions
        all_labels = bid_labels + ask_labels
        all_positions = list(range(len(all_labels)))
        
        # Set tick positions and labels
        ax1.set_yticks(all_positions)
        ax1.set_yticklabels(all_labels)
        
        # Set labels
        ax1.set_xlabel('Volume')
        ax1.set_ylabel('Price')
        ax1.set_title('Order Book Depth')
        ax1.legend()
        
        try:
            # Plot 2: Price levels with liquidity zones
            combined_prices = ask_prices + bid_prices
            if combined_prices:
                price_range = max(combined_prices) - min(combined_prices)
                min_price = min(combined_prices) - price_range * 0.05
                max_price = max(combined_prices) + price_range * 0.05
                
                # Plot price range
                if current_price > 0:
                    ax2.axhline(y=current_price, color='blue', linestyle='-', label='Current Price')
                
                # Plot support clusters
                for price in support_clusters:
                    if price is not None:
                        ax2.axhline(y=price, color='green', linestyle='--', linewidth=2, label=f'Support @ {price:.2f}')
                
                # Plot resistance clusters
                for price in resistance_clusters:
                    if price is not None:
                        ax2.axhline(y=price, color='red', linestyle='--', linewidth=2, label=f'Resistance @ {price:.2f}')
                
                # Plot gaps
                for price in gaps:
                    if price is not None:
                        ax2.axhline(y=price, color='orange', linestyle=':', linewidth=1, label=f'Gap @ {price:.2f}')
                
                # Plot entry and stop-loss zones
                if entry_zone is not None:
                    ax2.axhline(y=entry_zone, color='purple', linestyle='-', linewidth=2, label=f'Entry @ {entry_zone:.2f}')
                
                if stop_loss_zone is not None:
                    ax2.axhline(y=stop_loss_zone, color='black', linestyle='-', linewidth=2, label=f'Stop-Loss @ {stop_loss_zone:.2f}')
                
                # Set axis limits
                ax2.set_ylim(min_price, max_price)
                
                # Handle duplicate labels in legend
                handles, labels = ax2.get_legend_handles_labels()
                unique_labels = []
                unique_handles = []
                for handle, label in zip(handles, labels):
                    if label not in unique_labels:
                        unique_labels.append(label)
                        unique_handles.append(handle)
                
                # Add legend
                ax2.legend(unique_handles, unique_labels, loc='best')
            else:
                ax2.text(0.5, 0.5, "No price data available", 
                        horizontalalignment='center', verticalalignment='center', fontsize=14)
                ax2.axis('off')
            
            # Set labels
            ax2.set_xlabel('Index')
            ax2.set_ylabel('Price')
            ax2.set_title('Liquidity Zones')
            
            # Add signal and confidence
            signal = analysis_result.get('signal', 'NEUTRAL')
            confidence = analysis_result.get('confidence', 0)
            explanation = analysis_result.get('explanation', [''])[0]
            
            # Add text annotations
            fig.text(0.1, 0.02, f"Signal: {signal}", fontsize=12)
            fig.text(0.3, 0.02, f"Confidence: {confidence}%", fontsize=12)
            
            # Format explanation to fit in plot
            if explanation and len(explanation) > 100:
                explanation = explanation[:97] + '...'
            fig.text(0.1, 0.01, f"Explanation: {explanation}", fontsize=10)
            
        except Exception as e:
            logger.error(f"Error creating price level plot: {str(e)}")
            ax2.text(0.5, 0.5, f"Error plotting price levels: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center', fontsize=12)
            ax2.axis('off')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Save or show plot
        if save:
            plt.savefig(output, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {output}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error in plot_liquidity_zones: {str(e)}")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Error creating liquidity zones plot: {str(e)}", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        
        if save:
            plt.savefig(output, dpi=150)
            logger.info(f"Error plot saved as {output}")
        else:
            plt.show()

def main():
    """Main function."""
    args = parse_args()
    
    # Fetch and analyze order book
    analysis_result = analyze_liquidity(args.symbol, args.limit)
    
    # Save the result for debugging
    try:
        with open(f"{args.symbol.replace('/', '')}_liquidity_analysis_result.json", 'w') as f:
            json.dump(analysis_result, f, indent=2)
        logger.info(f"Analysis result saved to {args.symbol.replace('/', '')}_liquidity_analysis_result.json")
    except Exception as e:
        logger.warning(f"Failed to save analysis result: {str(e)}")
    
    # Check for empty result or error
    if not analysis_result:
        logger.error("Analysis returned empty result")
        # Create a simple error message plot instead of exiting
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, f"ERROR: Could not analyze liquidity for {args.symbol}\nCheck logs for details", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        if args.save:
            plt.savefig(args.output)
            logger.info(f"Error message saved to {args.output}")
        else:
            plt.show()
        return
    
    # Even if there's a non-successful status, try to extract useful information
    metrics = analysis_result.get('metrics', {})
    top_bids = metrics.get('top_bids', [])
    top_asks = metrics.get('top_asks', [])
    
    if not top_bids and not top_asks:
        logger.error("No order book data available")
        # Create a simple error message plot
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, f"ERROR: No order book data available for {args.symbol}\nAPI may be unavailable in this region", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        if args.save:
            plt.savefig(args.output)
            logger.info(f"Error message saved to {args.output}")
        else:
            plt.show()
        return
    
    # Plot liquidity zones
    try:
        plot_liquidity_zones(analysis_result, args.save, args.output)
    except Exception as e:
        logger.error(f"Error plotting liquidity zones: {str(e)}")
        # Create a simple error message plot
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, f"ERROR: Could not plot liquidity zones for {args.symbol}\n{str(e)}", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.axis('off')
        if args.save:
            plt.savefig(args.output)
            logger.info(f"Error message saved to {args.output}")
        else:
            plt.show()

if __name__ == '__main__':
    main()