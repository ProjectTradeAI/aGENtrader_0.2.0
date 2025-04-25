"""
Database Structure Check

This script examines the PostgreSQL database structure and prints
information about tables, columns, and available data.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

def get_database_connection():
    """Establish a connection to the PostgreSQL database"""
    # Get database URL from environment variable
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Connect to the database
    conn = psycopg2.connect(database_url)
    return conn

def close_database_connection(conn):
    """Close the database connection"""
    if conn:
        conn.close()

def get_table_list(conn):
    """Get a list of all tables in the database"""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
    
    return tables

def get_table_structure(conn, table_name):
    """Get the structure (columns) of a specific table"""
    with conn.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
    
    return columns

def get_table_row_count(conn, table_name):
    """Get the number of rows in a specific table"""
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
    
    return count

def get_sample_data(conn, table_name, limit=5):
    """Get a sample of data from a specific table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        sample_data = cursor.fetchall()
    
    return sample_data

def get_market_data_summary(conn):
    """Get a summary of market data in the database"""
    summary = {}
    
    try:
        # Check if market_data table exists
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'market_data'
                )
            """)
            has_market_data = cursor.fetchone()[0]
        
        if not has_market_data:
            return {"error": "market_data table not found"}
        
        # Get available symbols
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT symbol FROM market_data
            """)
            symbols = [row[0] for row in cursor.fetchall()]
            summary["symbols"] = symbols
        
        # Get available intervals
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT interval FROM market_data
            """)
            intervals = [row[0] for row in cursor.fetchall()]
            summary["intervals"] = intervals
        
        # Get date range for each symbol and interval
        symbol_data = {}
        for symbol in symbols:
            symbol_data[symbol] = {}
            
            for interval in intervals:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            MIN(timestamp) as first_date,
                            MAX(timestamp) as last_date,
                            COUNT(*) as count,
                            MIN(close) as min_price,
                            MAX(close) as max_price,
                            AVG(close) as avg_price
                        FROM market_data
                        WHERE symbol = %s AND interval = %s
                    """, (symbol, interval))
                    result = cursor.fetchone()
                
                if result and result[0] is not None:
                    symbol_data[symbol][interval] = {
                        "first_date": result[0].isoformat() if result[0] else None,
                        "last_date": result[1].isoformat() if result[1] else None,
                        "count": result[2],
                        "min_price": float(result[3]) if result[3] else None,
                        "max_price": float(result[4]) if result[4] else None,
                        "avg_price": float(result[5]) if result[5] else None
                    }
        
        summary["data_by_symbol"] = symbol_data
        
    except Exception as e:
        summary["error"] = str(e)
    
    return summary

def main():
    """Main function to check database structure"""
    try:
        # Connect to the database
        conn = get_database_connection()
        
        # Get a list of all tables
        tables = get_table_list(conn)
        print(f"Found {len(tables)} tables in the database:")
        for table in tables:
            print(f"  - {table}")
        print()
        
        # Get detailed information for each table
        table_info = {}
        for table in tables:
            row_count = get_table_row_count(conn, table)
            columns = get_table_structure(conn, table)
            sample_data = []
            
            # Only get sample data if the table has rows
            if row_count > 0:
                sample_data = get_sample_data(conn, table)
            
            table_info[table] = {
                "row_count": row_count,
                "columns": [{
                    "name": col[0], 
                    "type": col[1], 
                    "nullable": col[2]
                } for col in columns],
                "sample_data": [dict(row) for row in sample_data]
            }
            
            print(f"Table: {table}")
            print(f"  Rows: {row_count}")
            print("  Columns:")
            for col in columns:
                print(f"    - {col[0]} ({col[1]}, {'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            if sample_data:
                print("  Sample data:")
                for i, row in enumerate(sample_data):
                    if i >= 2:  # Limit to 2 sample rows in console output to avoid clutter
                        print(f"    ... and {len(sample_data) - 2} more rows")
                        break
                    
                    print(f"    - Row {i+1}: {dict(row)}")
            print()
        
        # Get market data summary if the table exists
        if "market_data" in tables:
            print("Market Data Summary:")
            market_summary = get_market_data_summary(conn)
            
            if "error" in market_summary:
                print(f"  Error: {market_summary['error']}")
            else:
                symbols = market_summary.get("symbols", [])
                intervals = market_summary.get("intervals", [])
                
                print(f"  Available symbols: {', '.join(symbols)}")
                print(f"  Available intervals: {', '.join(intervals)}")
                
                # Print stats for BTCUSDT or the first available symbol
                focus_symbol = "BTCUSDT" if "BTCUSDT" in symbols else (symbols[0] if symbols else None)
                
                if focus_symbol:
                    print(f"\n  Details for {focus_symbol}:")
                    for interval in intervals:
                        interval_data = market_summary.get("data_by_symbol", {}).get(focus_symbol, {}).get(interval)
                        
                        if interval_data:
                            print(f"    Interval: {interval}")
                            print(f"      Date range: {interval_data['first_date']} to {interval_data['last_date']}")
                            print(f"      Records: {interval_data['count']}")
                            print(f"      Price range: ${interval_data['min_price']:.2f} to ${interval_data['max_price']:.2f} (avg: ${interval_data['avg_price']:.2f})")
            
            # Save full market summary to file
            os.makedirs("data", exist_ok=True)
            with open("data/market_data_summary.json", "w") as f:
                json.dump(market_summary, f, indent=2)
            print(f"\n  Full market data summary saved to data/market_data_summary.json")
        
        # Close the database connection
        close_database_connection(conn)
        
        # Save full database structure to a file
        os.makedirs("data", exist_ok=True)
        with open("data/database_structure.json", "w") as f:
            json.dump(table_info, f, indent=2)
        
        print(f"\nFull database structure saved to data/database_structure.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()