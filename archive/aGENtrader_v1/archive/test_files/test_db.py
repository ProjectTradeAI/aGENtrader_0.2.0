#!/usr/bin/env python3
import os
import sys
import psycopg2

def test_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL is not set")
        return False
    
    try:
        print(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Connected! Testing query...")
        cursor.execute("SELECT COUNT(*) FROM market_data WHERE symbol=%s AND interval=%s", ("BTCUSDT", "1h"))
        count = cursor.fetchone()[0]
        print(f"Found {count} records for BTCUSDT 1h")
        
        # Get date range
        cursor.execute("""
            SELECT 
                MIN(timestamp) as start_date,
                MAX(timestamp) as end_date
            FROM market_data 
            WHERE symbol=%s AND interval=%s
        """, ("BTCUSDT", "1h"))
        
        start_date, end_date = cursor.fetchone()
        print(f"Date range: {start_date} to {end_date}")
        
        # Get sample data
        cursor.execute("""
            SELECT 
                timestamp, open, high, low, close, volume
            FROM market_data 
            WHERE symbol=%s AND interval=%s
            ORDER BY timestamp DESC
            LIMIT 3
        """, ("BTCUSDT", "1h"))
        
        print("\nSample data:")
        for row in cursor.fetchall():
            print(row)
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection()
