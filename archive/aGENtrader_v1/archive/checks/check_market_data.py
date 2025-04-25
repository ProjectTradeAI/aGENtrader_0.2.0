"""
Market Data Check Utility

This script provides a simple way to check market data for a specific cryptocurrency
without running the full agent framework.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def format_dict_as_text(data: Dict[str, Any]) -> str:
    """Format a dictionary as a plain text string"""
    if not data:
        return "No data available"
    
    lines = []
    for key, value in data.items():
        if isinstance(value, float):
            # Format floats with 2 decimal places
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        lines.append(f"{key}: {formatted_value}")
    
    return "\n".join(lines)

def format_dict_as_markdown(data: Dict[str, Any]) -> str:
    """Format a dictionary as a markdown string"""
    if not data:
        return "No data available"
    
    lines = ["| Key | Value |", "| --- | --- |"]
    
    for key, value in data.items():
        if isinstance(value, float):
            # Format floats with 2 decimal places
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        lines.append(f"| {key} | {formatted_value} |")
    
    return "\n".join(lines)

def format_market_data(data: List[Dict[str, Any]], format_type: str = "text") -> str:
    """Format market data in the specified format"""
    if not data:
        return "No market data available"
    
    if format_type == "json":
        return json.dumps(data, indent=2, default=str)
    elif format_type == "markdown":
        headers = ["timestamp", "open", "high", "low", "close", "volume"]
        
        # Create header row
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        rows = [header_row, separator_row]
        
        # Create data rows
        for item in data:
            formatted_row = []
            for header in headers:
                value = item.get(header, "")
                if isinstance(value, float):
                    formatted_row.append(f"{value:.2f}")
                elif isinstance(value, datetime):
                    formatted_row.append(value.strftime("%Y-%m-%d %H:%M"))
                else:
                    formatted_row.append(str(value))
            
            rows.append("| " + " | ".join(formatted_row) + " |")
        
        return "\n".join(rows)
    else:  # text format
        result = []
        for item in data:
            line = []
            for key, value in item.items():
                if isinstance(value, float):
                    line.append(f"{key}: {value:.2f}")
                elif isinstance(value, datetime):
                    line.append(f"{key}: {value.strftime('%Y-%m-%d %H:%M')}")
                else:
                    line.append(f"{key}: {value}")
            result.append(", ".join(line))
        
        return "\n".join(result)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Check market data for a specific cryptocurrency")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                       help="Trading symbol to check (default: BTCUSDT)")
    
    parser.add_argument("--interval", type=str, default="1h",
                       choices=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
                       help="Time interval for data (default: 1h)")
    
    parser.add_argument("--limit", type=int, default=24,
                       help="Number of data points to retrieve (default: 24)")
    
    parser.add_argument("--days", type=int, default=None,
                       help="Number of days to look back (alternative to limit)")
    
    parser.add_argument("--format", type=str, default="text",
                       choices=["text", "json", "markdown"],
                       help="Output format (default: text)")
    
    parser.add_argument("--output", type=str, default=None,
                       help="Output file path (default: print to console)")
    
    parser.add_argument("--price-only", action="store_true",
                       help="Only display the latest price")
    
    parser.add_argument("--stats", action="store_true",
                       help="Show market statistics")
    
    return parser.parse_args()

def get_latest_price(symbol: str) -> Optional[float]:
    """
    Get the latest price for a symbol
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Latest price or None if not available
    """
    try:
        from agents.database_integration import DatabaseQueryManager
        
        # Initialize database integration
        db = DatabaseQueryManager()
        
        # Get latest price
        price = db.get_latest_price(symbol)
        
        # Close database connection
        db.close()
        
        return price
    except Exception as e:
        logger.error(f"Error getting latest price: {str(e)}")
        return None

def query_market_data(symbol: str, interval: str = "1h", limit: int = 24, 
                     days: Optional[int] = None, format_type: str = "text") -> str:
    """
    Query market data for a specific symbol
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        interval: Time interval (e.g., "1m", "5m", "15m", "1h", "4h", "1d")
        limit: Number of data points to retrieve
        days: Number of days to look back (alternative to limit)
        format_type: Output format ("text", "json", "markdown")
        
    Returns:
        Formatted market data as a string
    """
    try:
        from agents.database_integration import DatabaseQueryManager
        
        # Initialize database integration
        db = DatabaseQueryManager()
        
        # Calculate start_time if days is specified
        start_time = None
        if days is not None:
            from datetime import datetime, timedelta
            start_time = datetime.now() - timedelta(days=days)
        
        # Get market data
        data = db.get_market_data(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            limit=limit
        )
        
        # Close database connection
        db.close()
        
        # Format the output based on the format_type
        return format_market_data(data, format_type)
    except Exception as e:
        logger.error(f"Error querying market data: {str(e)}")
        return f"Error: {str(e)}"

def get_market_statistics(symbol: str, interval: str = "1d", 
                         days: int = 30, format_type: str = "text") -> str:
    """
    Get market statistics for a specific symbol
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        interval: Time interval (e.g., "1h", "4h", "1d")
        days: Number of days to look back
        format_type: Output format ("text", "json", "markdown")
        
    Returns:
        Formatted market statistics as a string
    """
    try:
        from agents.database_integration import DatabaseQueryManager
        
        # Initialize database integration
        db = DatabaseQueryManager()
        
        # Get price statistics
        stats = db.get_price_statistics(
            symbol=symbol,
            interval=interval,
            days=days
        )
        
        # Format the output if needed
        if format_type == "json":
            import json
            stats = json.dumps(stats, indent=2)
        elif format_type == "markdown":
            stats = format_dict_as_markdown(stats)
        else:
            stats = format_dict_as_text(stats)
        
        # Close database connection
        db.close()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting market statistics: {str(e)}")
        return f"Error: {str(e)}"

def calculate_volatility(symbol: str, days: int = 30, format_type: str = "text") -> str:
    """
    Calculate volatility for a specific symbol
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        days: Number of days to look back
        format_type: Output format ("text", "json", "markdown")
        
    Returns:
        Formatted volatility as a string
    """
    try:
        from agents.database_integration import DatabaseQueryManager
        
        # Initialize database integration
        db = DatabaseQueryManager()
        
        # Calculate volatility using hourly interval since daily data might not be available
        volatility = db.calculate_volatility(
            symbol=symbol,
            interval="1h",
            days=days
        )
        
        # Format the output if needed
        if format_type == "json":
            import json
            formatted_volatility = json.dumps(volatility, indent=2)
        elif format_type == "markdown":
            formatted_volatility = format_dict_as_markdown(volatility)
        else:
            formatted_volatility = format_dict_as_text(volatility)
        
        # Close database connection
        db.close()
        
        return formatted_volatility
    except Exception as e:
        logger.error(f"Error calculating volatility: {str(e)}")
        return f"Error: {str(e)}"

def save_output(output: str, output_path: str) -> None:
    """
    Save output to a file
    
    Args:
        output: Output string
        output_path: Path to output file
    """
    try:
        with open(output_path, "w") as f:
            f.write(output)
        logger.info(f"Output saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving output to {output_path}: {str(e)}")

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print(f"\nMarket Data Check for {args.symbol}\n")
    print("=" * 50)
    
    # Only show the latest price if --price-only flag is set
    if args.price_only:
        price = get_latest_price(args.symbol)
        if price is not None:
            output = f"Latest price for {args.symbol}: ${price:,.2f}"
            print(output)
            
            if args.output:
                save_output(output, args.output)
            
            return
    
    # Show market statistics if --stats flag is set
    if args.stats:
        stats = get_market_statistics(
            symbol=args.symbol,
            interval=args.interval,
            days=args.days or 30,
            format_type=args.format
        )
        
        print(stats)
        
        if args.output:
            save_output(stats, args.output)
        
        # Also get volatility
        volatility = calculate_volatility(
            symbol=args.symbol,
            days=args.days or 30,
            format_type=args.format
        )
        
        print("\nVolatility Analysis:")
        print("-" * 50)
        print(volatility)
        
        return
    
    # Otherwise query market data
    data = query_market_data(
        symbol=args.symbol,
        interval=args.interval,
        limit=args.limit,
        days=args.days,
        format_type=args.format
    )
    
    print(data)
    
    if args.output:
        save_output(data, args.output)

if __name__ == "__main__":
    main()