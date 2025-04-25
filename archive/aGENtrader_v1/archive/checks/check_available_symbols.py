"""
Simple script to check available symbols in the database
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("symbol_checker")

# Import the database connection from the retrieval tool
from agents.database_retrieval_tool import get_db_connection

def get_available_symbols():
    """Get a list of available symbols in the database"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return []
        
        with conn.cursor() as cur:
            # Query for distinct symbols
            cur.execute("""
                SELECT DISTINCT symbol 
                FROM market_data
                ORDER BY symbol
            """)
            
            results = cur.fetchall()
            if not results:
                logger.warning("No symbols found in database")
                return []
            
            # Extract symbol strings from results
            symbols = [row['symbol'] for row in results]
            return symbols
    except Exception as e:
        logger.error(f"Error retrieving symbols: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def get_symbol_stats(symbol):
    """Get statistics for a specific symbol"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return None
        
        with conn.cursor() as cur:
            # Query for symbol statistics
            cur.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as record_count,
                    MIN(timestamp) as oldest_record,
                    MAX(timestamp) as newest_record,
                    MIN(close) as lowest_price,
                    MAX(close) as highest_price,
                    AVG(close) as average_price,
                    ARRAY_AGG(DISTINCT interval) as intervals
                FROM market_data
                WHERE symbol = %s
                GROUP BY symbol
            """, (symbol,))
            
            result = cur.fetchone()
            if not result:
                logger.warning(f"No data found for symbol {symbol}")
                return None
            
            # Convert to dictionary
            stats = dict(result)
            
            # Add additional insights
            cur.execute("""
                SELECT interval, COUNT(*) as count
                FROM market_data
                WHERE symbol = %s
                GROUP BY interval
                ORDER BY interval
            """, (symbol,))
            
            interval_counts = cur.fetchall()
            stats['interval_counts'] = [dict(row) for row in interval_counts]
            
            return stats
    except Exception as e:
        logger.error(f"Error retrieving symbol stats: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def main():
    """Check available symbols in the database"""
    print("\n\n")
    print("=" * 80)
    print(" DATABASE SYMBOL CHECK ".center(80, "="))
    print("=" * 80)
    
    # Get available symbols
    symbols = get_available_symbols()
    
    if not symbols:
        print("\nNo symbols found in the database.")
        return
    
    print(f"\nFound {len(symbols)} symbol(s) in the database:")
    for i, symbol in enumerate(symbols, 1):
        print(f"{i}. {symbol}")
    
    # Get statistics for each symbol
    print("\n")
    print("=" * 80)
    print(" SYMBOL STATISTICS ".center(80, "="))
    print("=" * 80)
    
    for symbol in symbols:
        stats = get_symbol_stats(symbol)
        if not stats:
            print(f"\nNo statistics available for {symbol}")
            continue
        
        print(f"\nSymbol: {symbol}")
        print(f"Record count: {stats['record_count']}")
        print(f"Date range: {stats['oldest_record']} to {stats['newest_record']}")
        print(f"Price range: ${stats['lowest_price']} to ${stats['highest_price']}")
        print(f"Average price: ${stats['average_price']:.2f}")
        
        print("\nInterval breakdown:")
        for interval_count in stats['interval_counts']:
            print(f"  - {interval_count['interval']}: {interval_count['count']} records")
    
    print("\n")
    print("=" * 80)
    print(" CHECK COMPLETED ".center(80, "="))
    print("=" * 80)

if __name__ == "__main__":
    main()