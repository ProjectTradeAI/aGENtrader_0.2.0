"""
Market Data Availability Checker

This utility checks the availability of market data in the database
and provides an overview of what symbols and time ranges are available.
"""

import os
import sys
import json
import argparse
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Check market data availability")
    
    parser.add_argument(
        "--symbol",
        type=str,
        help="Check specific symbol only"
    )
    
    parser.add_argument(
        "--interval",
        type=str,
        choices=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        help="Check specific interval only"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)"
    )
    
    return parser.parse_args()

def get_database_connection():
    """Get a connection to the PostgreSQL database"""
    # Try to get the database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Please set the DATABASE_URL environment variable and try again")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def close_database_connection(conn):
    """Close the database connection"""
    if conn:
        conn.close()

def get_available_symbols(conn) -> List[str]:
    """Get a list of available symbols in the database"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol")
        symbols = [row[0] for row in cursor.fetchall()]
        
        return symbols
    except Exception as e:
        print(f"Error querying symbols: {str(e)}")
        return []
    finally:
        cursor.close()

def get_available_intervals(conn, symbol: Optional[str] = None) -> List[str]:
    """Get a list of available intervals in the database"""
    cursor = conn.cursor()
    
    try:
        if symbol:
            cursor.execute(
                "SELECT DISTINCT interval FROM market_data WHERE symbol = %s ORDER BY interval",
                (symbol,)
            )
        else:
            cursor.execute("SELECT DISTINCT interval FROM market_data ORDER BY interval")
        
        intervals = [row[0] for row in cursor.fetchall()]
        
        return intervals
    except Exception as e:
        print(f"Error querying intervals: {str(e)}")
        return []
    finally:
        cursor.close()

def get_symbol_data_range(conn, symbol: str, interval: Optional[str] = None) -> Dict[str, Any]:
    """Get the data range for a specific symbol"""
    cursor = conn.cursor()
    
    try:
        if interval:
            cursor.execute(
                """
                SELECT 
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    COUNT(*) as record_count,
                    MIN(close) as min_price,
                    MAX(close) as max_price,
                    AVG(close) as avg_price
                FROM market_data 
                WHERE symbol = %s AND interval = %s
                """,
                (symbol, interval)
            )
        else:
            cursor.execute(
                """
                SELECT 
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    COUNT(*) as record_count,
                    MIN(close) as min_price,
                    MAX(close) as max_price,
                    AVG(close) as avg_price
                FROM market_data 
                WHERE symbol = %s
                """,
                (symbol,)
            )
        
        row = cursor.fetchone()
        
        if row:
            return {
                "symbol": symbol,
                "interval": interval if interval else "all",
                "start_time": row[0].isoformat() if row[0] else None,
                "end_time": row[1].isoformat() if row[1] else None,
                "record_count": row[2],
                "min_price": float(row[3]) if row[3] else None,
                "max_price": float(row[4]) if row[4] else None,
                "avg_price": float(row[5]) if row[5] else None
            }
        else:
            return {
                "symbol": symbol,
                "interval": interval if interval else "all",
                "start_time": None,
                "end_time": None,
                "record_count": 0,
                "min_price": None,
                "max_price": None,
                "avg_price": None
            }
    except Exception as e:
        print(f"Error querying data range: {str(e)}")
        return {
            "symbol": symbol,
            "interval": interval if interval else "all",
            "error": str(e)
        }
    finally:
        cursor.close()

def get_data_coverage(conn, symbol: str, interval: str) -> Dict[str, Any]:
    """Get data coverage information for a specific symbol and interval"""
    cursor = conn.cursor()
    
    try:
        # Get the expected number of records based on time range and interval
        cursor.execute(
            """
            SELECT 
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time
            FROM market_data 
            WHERE symbol = %s AND interval = %s
            """,
            (symbol, interval)
        )
        
        row = cursor.fetchone()
        if not row or not row[0] or not row[1]:
            return {
                "symbol": symbol,
                "interval": interval,
                "coverage": 0,
                "gaps": []
            }
        
        start_time, end_time = row[0], row[1]
        
        # Calculate interval in seconds
        interval_seconds = 60  # Default to 1 minute
        if interval == "1m":
            interval_seconds = 60
        elif interval == "5m":
            interval_seconds = 5 * 60
        elif interval == "15m":
            interval_seconds = 15 * 60
        elif interval == "30m":
            interval_seconds = 30 * 60
        elif interval == "1h":
            interval_seconds = 60 * 60
        elif interval == "4h":
            interval_seconds = 4 * 60 * 60
        elif interval == "1d":
            interval_seconds = 24 * 60 * 60
        
        # Calculate expected records
        time_diff = (end_time - start_time).total_seconds()
        expected_records = int(time_diff / interval_seconds) + 1
        
        # Get actual record count
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM market_data 
            WHERE symbol = %s AND interval = %s
            """,
            (symbol, interval)
        )
        
        actual_records = cursor.fetchone()[0]
        
        # Calculate coverage
        coverage = min(1.0, actual_records / expected_records) if expected_records > 0 else 0
        
        # Find major gaps (more than 5 intervals)
        cursor.execute(
            """
            SELECT timestamp 
            FROM market_data 
            WHERE symbol = %s AND interval = %s
            ORDER BY timestamp
            """,
            (symbol, interval)
        )
        
        timestamps = [row[0] for row in cursor.fetchall()]
        
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).total_seconds()
            if gap > 5 * interval_seconds:
                gaps.append({
                    "start": timestamps[i-1].isoformat(),
                    "end": timestamps[i].isoformat(),
                    "duration_hours": round(gap / 3600, 2)
                })
        
        return {
            "symbol": symbol,
            "interval": interval,
            "coverage": coverage,
            "expected_records": expected_records,
            "actual_records": actual_records,
            "major_gaps": gaps[:5] if len(gaps) > 5 else gaps,  # Limit to top 5 gaps
            "gap_count": len(gaps)
        }
    except Exception as e:
        print(f"Error calculating coverage: {str(e)}")
        return {
            "symbol": symbol,
            "interval": interval,
            "error": str(e)
        }
    finally:
        cursor.close()

def check_market_data_availability(args):
    """Check market data availability based on arguments"""
    conn = get_database_connection()
    
    try:
        results = {}
        
        # Get symbols to check
        if args.symbol:
            symbols = [args.symbol]
        else:
            symbols = get_available_symbols(conn)
        
        if not symbols:
            print("No symbols found in the database")
            return {"status": "error", "message": "No symbols found"}
        
        # Initialize results structure
        results = {
            "timestamp": datetime.now().isoformat(),
            "symbols_count": len(symbols),
            "symbols": {}
        }
        
        # Check each symbol
        for symbol in symbols:
            # Get intervals to check
            if args.interval:
                intervals = [args.interval]
            else:
                intervals = get_available_intervals(conn, symbol)
            
            # Get overall data range for the symbol
            symbol_data = get_symbol_data_range(conn, symbol)
            
            # Check data for each interval
            interval_data = {}
            for interval in intervals:
                interval_info = get_symbol_data_range(conn, symbol, interval)
                coverage_info = get_data_coverage(conn, symbol, interval)
                
                interval_data[interval] = {
                    "range": interval_info,
                    "coverage": coverage_info
                }
            
            # Store symbol results
            results["symbols"][symbol] = {
                "overview": symbol_data,
                "intervals": interval_data
            }
        
        return results
    
    finally:
        close_database_connection(conn)

def display_text_results(results: Dict[str, Any]) -> None:
    """Display results in text format"""
    print("\n" + "=" * 80)
    print(f" Market Data Availability Check - {results['timestamp']} ".center(80, "="))
    print("=" * 80 + "\n")
    
    print(f"Found {results['symbols_count']} symbol(s)\n")
    
    for symbol, symbol_data in results["symbols"].items():
        print("-" * 80)
        print(f"Symbol: {symbol}")
        
        overview = symbol_data["overview"]
        print(f"  Data Range: {overview['start_time']} to {overview['end_time']}")
        print(f"  Total Records: {overview['record_count']:,}")
        print(f"  Price Range: ${overview['min_price']:,.2f} to ${overview['max_price']:,.2f} (Avg: ${overview['avg_price']:,.2f})")
        
        print("\n  Intervals:")
        for interval, interval_data in symbol_data["intervals"].items():
            range_info = interval_data["range"]
            coverage_info = interval_data["coverage"]
            
            print(f"    {interval}:")
            print(f"      Records: {range_info['record_count']:,}")
            print(f"      Range: {range_info['start_time']} to {range_info['end_time']}")
            print(f"      Coverage: {coverage_info['coverage']*100:.1f}% ({coverage_info['actual_records']:,}/{coverage_info['expected_records']:,} records)")
            
            if coverage_info.get("major_gaps") and len(coverage_info["major_gaps"]) > 0:
                print(f"      Gaps: {coverage_info['gap_count']} major gaps found")
                for i, gap in enumerate(coverage_info["major_gaps"][:3], 1):  # Show top 3
                    print(f"        Gap {i}: {gap['start']} to {gap['end']} ({gap['duration_hours']} hours)")
            
            print()
        
        print()

def save_results(results: Dict[str, Any], output_path: str, format_type: str = "json") -> None:
    """Save results to a file"""
    try:
        with open(output_path, "w") as f:
            if format_type == "json":
                json.dump(results, f, indent=2)
            else:
                # Redirect stdout to file and print text results
                original_stdout = sys.stdout
                sys.stdout = f
                display_text_results(results)
                sys.stdout = original_stdout
        
        print(f"Results saved to {output_path}")
    except Exception as e:
        print(f"Error saving results to {output_path}: {str(e)}")

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check market data availability
    results = check_market_data_availability(args)
    
    # Display or save results
    if args.output:
        save_results(results, args.output, args.format)
    else:
        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            display_text_results(results)

if __name__ == "__main__":
    main()