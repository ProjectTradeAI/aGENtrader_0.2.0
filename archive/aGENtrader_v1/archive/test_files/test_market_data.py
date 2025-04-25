#!/usr/bin/env python3
"""
Test script to verify database market data access
"""
import os
import sys
import json
import psycopg2
from datetime import datetime

def test_market_data():
    """Test market data access"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        return False
    
    try:
        print(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Get available symbols and intervals
        cursor.execute("""
            SELECT 
                symbol, 
                interval, 
                MIN(timestamp) as start_date, 
                MAX(timestamp) as end_date,
                COUNT(*) as count
            FROM 
                market_data 
            GROUP BY 
                symbol, interval
            ORDER BY 
                symbol, interval
        """)
        
        print("\nAvailable market data:")
        print("======================")
        print(f"{'Symbol':<10} {'Interval':<8} {'Start Date':<20} {'End Date':<20} {'Count':<8}")
        print("-" * 70)
        
        for row in cursor.fetchall():
            symbol, interval, start_date, end_date, count = row
            print(f"{symbol:<10} {interval:<8} {start_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {end_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {count:<8}")
        
        # Create a simple query to fetch some data
        symbol = "BTCUSDT"
        interval = "1h"
        start_date = "2025-03-20"
        end_date = "2025-03-22"
        
        print(f"\nFetching sample data for {symbol} {interval} from {start_date} to {end_date}")
        cursor.execute("""
            SELECT 
                timestamp, open, high, low, close, volume
            FROM 
                market_data 
            WHERE 
                symbol = %s 
                AND interval = %s
                AND timestamp >= %s
                AND timestamp <= %s
            ORDER BY 
                timestamp
            LIMIT 5
        """, (symbol, interval, start_date, end_date))
        
        sample_data = cursor.fetchall()
        print("\nSample data (first 5 records):")
        print("============================")
        for row in sample_data:
            timestamp, open_price, high, low, close, volume = row
            print(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | Open: {float(open_price):.2f} | High: {float(high):.2f} | Low: {float(low):.2f} | Close: {float(close):.2f} | Volume: {float(volume):.2f}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_market_data()
