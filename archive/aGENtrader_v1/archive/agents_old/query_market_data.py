"""
AutoGen Market Data Query Functions

This module provides functions for querying market data from the integrated market data provider
to be used with AutoGen agents.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path if necessary
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the database module
try:
    from utils.database_market_data import (
        get_historical_data,
        get_latest_price,
        get_market_statistics,
        get_data_age
    )
except ImportError as e:
    logger.error(f"Error importing database market data: {e}")
    raise ImportError("Database market data module not available")

def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                     days: Optional[int] = None, format_type: str = 'json') -> str:
    """
    Query market data for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        limit: Number of data points to retrieve
        days: Number of days to look back (alternative to limit)
        format_type: Output format ('json', 'markdown', 'text')
        
    Returns:
        Formatted market data as a string
    """
    try:
        # Calculate start date from days if provided
        start_date = None
        end_date = datetime.now().isoformat()
        
        if days:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get the historical data
        data = get_historical_data(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            format_type='dict'  # Always get dict first
        )
        
        # Check if data is empty or has error
        if isinstance(data, dict) and 'error' in data:
            return json.dumps({
                "error": data['error'],
                "symbol": symbol,
                "interval": interval,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        
        # Get data age for additional context
        age_days = get_data_age(symbol, interval)
        
        # Format based on requested format
        if format_type == 'json':
            result = {
                "symbol": symbol,
                "interval": interval,
                "data": data,
                "count": len(data) if isinstance(data, list) else 0,
                "data_age_days": age_days,
                "timestamp": datetime.now().isoformat(),
                "source": "database"
            }
            return json.dumps(result, indent=2)
            
        elif format_type == 'markdown':
            if not data or not isinstance(data, list):
                return f"No data available for {symbol} ({interval})"
            
            # Create markdown table
            md = f"# Market Data: {symbol} ({interval})\n\n"
            md += f"*Data retrieved at {datetime.now().isoformat()} (data is {age_days} days old)*\n\n"
            
            # Table header
            md += "| Timestamp | Open | High | Low | Close | Volume |\n"
            md += "| --------- | ---- | ---- | --- | ----- | ------ |\n"
            
            # Table rows
            for row in data:
                timestamp = row.get('timestamp', '')
                timestamp = timestamp.replace('T', ' ').split('.')[0] if timestamp else ''
                
                md += f"| {timestamp} "
                md += f"| {row.get('open', 'N/A'):.2f} "
                md += f"| {row.get('high', 'N/A'):.2f} "
                md += f"| {row.get('low', 'N/A'):.2f} "
                md += f"| {row.get('close', 'N/A'):.2f} "
                md += f"| {row.get('volume', 'N/A'):.2f} |\n"
            
            return md
            
        else:  # text format
            if not data or not isinstance(data, list):
                return f"No data available for {symbol} ({interval})"
            
            text = f"Market Data: {symbol} ({interval})\n"
            text += f"Data retrieved at {datetime.now().isoformat()} (data is {age_days} days old)\n\n"
            
            # Format as text table
            text += f"{'Timestamp':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>10}\n"
            text += "-" * 75 + "\n"
            
            for row in data:
                timestamp = row.get('timestamp', '')
                timestamp = timestamp.replace('T', ' ').split('.')[0] if timestamp else ''
                
                text += f"{timestamp:<20} "
                text += f"{row.get('open', 'N/A'):>10.2f} "
                text += f"{row.get('high', 'N/A'):>10.2f} "
                text += f"{row.get('low', 'N/A'):>10.2f} "
                text += f"{row.get('close', 'N/A'):>10.2f} "
                text += f"{row.get('volume', 'N/A'):>10.2f}\n"
            
            return text
    
    except Exception as e:
        logger.error(f"Error in query_market_data: {e}")
        error_msg = {
            "error": f"Failed to retrieve market data: {str(e)}",
            "symbol": symbol,
            "interval": interval,
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_msg, indent=2)

def get_market_price(symbol: str) -> str:
    """
    Get the latest market price for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        
    Returns:
        Latest price information as a JSON string
    """
    try:
        price_data = get_latest_price(symbol)
        
        if price_data is None:
            return json.dumps({
                "error": "Price data not available",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        
        # Get data age for additional context
        age_days = get_data_age(symbol, '1h')
        
        # Add formatted information
        result = {
            "symbol": symbol,
            "price": price_data,
            "formatted_price": f"${price_data:,.2f}" if isinstance(price_data, (int, float)) else "N/A",
            "data_age_days": age_days,
            "timestamp": datetime.now().isoformat(),
            "source": "database"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in get_market_price: {e}")
        error_msg = {
            "error": f"Failed to retrieve market price: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_msg, indent=2)

def get_market_analysis(symbol: str, interval: str = '1d', 
                       days: int = 30, format_type: str = 'json') -> str:
    """
    Get market analysis and statistics for a specific symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h', '4h', '1d')
        days: Number of days to look back
        format_type: Output format ('json', 'markdown', 'text')
        
    Returns:
        Formatted market analysis as a string
    """
    try:
        # Get market statistics
        stats = get_market_statistics(symbol, interval, days, format_type='dict')
        
        # Check if stats has error
        if isinstance(stats, dict) and 'error' in stats:
            return json.dumps({
                "error": stats['error'],
                "symbol": symbol,
                "interval": interval,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        
        # Get data age for additional context
        age_days = get_data_age(symbol, interval)
        
        # Add information about data age to stats
        stats['data_age_days'] = age_days
        stats['timestamp'] = datetime.now().isoformat()
        
        # Format based on requested format
        if format_type == 'json':
            return json.dumps(stats, indent=2)
            
        elif format_type == 'markdown':
            md = f"# Market Analysis: {symbol} ({interval})\n\n"
            md += f"*Analysis as of {datetime.now().isoformat()} (data is {age_days} days old)*\n\n"
            
            # Current price and trend information
            md += "## Current Market Status\n\n"
            
            if 'current_price' in stats:
                md += f"**Current Price:** ${stats['current_price']:,.2f}\n\n"
            
            if 'daily_change_percent' in stats:
                change = stats['daily_change_percent']
                change_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                md += f"**24h Change:** {change_icon} {change:.2f}%\n\n"
            
            if 'trend' in stats:
                trend = stats['trend']
                trend_icon = "📈" if trend == "Uptrend" else "📉" if trend == "Downtrend" else "➡️"
                md += f"**Trend:** {trend_icon} {trend}\n\n"
            
            # Technical indicators
            md += "## Technical Indicators\n\n"
            
            if 'volatility' in stats:
                md += f"**Volatility:** {stats['volatility']:.4f}\n\n"
            
            if 'rsi' in stats:
                rsi = stats['rsi']
                rsi_rating = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
                md += f"**RSI:** {rsi:.2f} ({rsi_rating})\n\n"
            
            # Moving averages
            md += "## Moving Averages\n\n"
            
            if 'sma_20' in stats and 'sma_50' in stats:
                md += f"**SMA 20:** ${stats['sma_20']:,.2f}\n\n"
                md += f"**SMA 50:** ${stats['sma_50']:,.2f}\n\n"
                
                # Moving average analysis
                current_price = stats.get('current_price', 0)
                if current_price > stats['sma_20'] > stats['sma_50']:
                    md += "**MA Analysis:** Strong uptrend (price > SMA20 > SMA50)\n\n"
                elif stats['sma_20'] > current_price > stats['sma_50']:
                    md += "**MA Analysis:** Potential retracement in uptrend\n\n"
                elif stats['sma_20'] > stats['sma_50'] > current_price:
                    md += "**MA Analysis:** Weak uptrend or trend reversal\n\n"
                elif current_price < stats['sma_20'] < stats['sma_50']:
                    md += "**MA Analysis:** Strong downtrend (price < SMA20 < SMA50)\n\n"
                else:
                    md += "**MA Analysis:** Mixed signals\n\n"
            
            # Price range
            md += "## Price Range\n\n"
            
            if 'highest_price' in stats and 'lowest_price' in stats:
                high = stats['highest_price']
                low = stats['lowest_price']
                current = stats.get('current_price', 0)
                
                # Calculate where current price is in the range (0-100%)
                range_size = high - low
                if range_size > 0:
                    position = ((current - low) / range_size) * 100
                    md += f"**Price Range:** ${low:,.2f} - ${high:,.2f}\n\n"
                    md += f"**Current Position:** {position:.1f}% of range\n\n"
            
            return md
            
        else:  # text format
            text = f"Market Analysis: {symbol} ({interval})\n"
            text += f"Analysis as of {datetime.now().isoformat()} (data is {age_days} days old)\n\n"
            
            # Current price and trend
            text += "--- Current Market Status ---\n"
            
            if 'current_price' in stats:
                text += f"Current Price: ${stats['current_price']:,.2f}\n"
            
            if 'daily_change_percent' in stats:
                text += f"24h Change: {stats['daily_change_percent']:.2f}%\n"
            
            if 'trend' in stats:
                text += f"Trend: {stats['trend']}\n"
            
            # Technical indicators
            text += "\n--- Technical Indicators ---\n"
            
            if 'volatility' in stats:
                text += f"Volatility: {stats['volatility']:.4f}\n"
            
            if 'rsi' in stats:
                rsi = stats['rsi']
                rsi_rating = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
                text += f"RSI: {rsi:.2f} ({rsi_rating})\n"
            
            # Moving averages
            text += "\n--- Moving Averages ---\n"
            
            if 'sma_20' in stats:
                text += f"SMA 20: ${stats['sma_20']:,.2f}\n"
            
            if 'sma_50' in stats:
                text += f"SMA 50: ${stats['sma_50']:,.2f}\n"
            
            # Price range
            text += "\n--- Price Range ---\n"
            
            if 'highest_price' in stats and 'lowest_price' in stats:
                text += f"High: ${stats['highest_price']:,.2f}\n"
                text += f"Low: ${stats['lowest_price']:,.2f}\n"
            
            # Data info
            text += f"\nData Points: {stats.get('data_points', 'N/A')}\n"
            text += f"Period: {days} days\n"
            
            return text
    
    except Exception as e:
        logger.error(f"Error in get_market_analysis: {e}")
        error_msg = {
            "error": f"Failed to retrieve market analysis: {str(e)}",
            "symbol": symbol,
            "interval": interval,
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_msg, indent=2)

if __name__ == "__main__":
    # Example usage
    print("Testing AutoGen Market Data Query Functions\n")
    
    # Test query_market_data
    print("=== Market Data Query ===")
    market_data = query_market_data("BTCUSDT", interval="1h", limit=5, format_type="text")
    print(market_data)
    print("\n")
    
    # Test get_market_price
    print("=== Latest Market Price ===")
    price_data = get_market_price("BTCUSDT")
    print(price_data)
    print("\n")
    
    # Test get_market_analysis
    print("=== Market Analysis ===")
    analysis = get_market_analysis("BTCUSDT", interval="1h", days=7, format_type="text")
    print(analysis)