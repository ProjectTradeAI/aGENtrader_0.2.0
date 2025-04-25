#!/bin/bash
# Script to check available market data for backtesting

# Set parameters
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Create key file if it doesn't exist
if [ ! -f "$KEY_PATH" ]; then
  echo "Creating EC2 key file..."
  cat > "$KEY_PATH" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEAyxNT6X+1frDllJPAbCAjOjNV6+IYbJTBJF+NNUESxrYsMK8J
1Dt4OBuXKSMV7nttmb6/jy6tItkztExoPyqr1QuKwHUInkbkKTm15Cl90o6yzXba
UfntOfpwZHwmEOJRVniLRJPzkOldOplyTiIxaf8mZKLeaXDlleaHZlNyrBWs9wNN
gJJbCBve2Z1TJsZeRig3u0Tg0+xo1BPxSm8dROalr8/30UrXpCkDQVL5S3oA2kSd
6hvwQhUZclGNheGgLOGTMtZ/FxGAI/mVsD29ErWnEoysLGCpbLfXpw7o3yEDCND+
cpqtV+ckbTeX2gqbugyZmBVrxcnbafwW1ykoaQIDAQABAoIBAE53gmXn1c5FNgBp
8uEUrefwLBQAAeX6uIKAdUSNh17Gx15sVATwkaxEZO0dRH0orhnJDaWaqIWdnY/e
Mi2uJEUmt49T6WeXBtQzG2g07Awu3UHs2cDxLEvJzCHXorHFcR5TZ6Sw8l0c/swE
vJkaNzO4xjH+iKf/WobIU6sjNVzuNjJF7TNUJ/kZmfZHOjOKCSBF/ahY+weeVBFp
lqaSKrNINPYoYn4nrAgWVxMiPqItWhm3Y9G3c3z9ePNJKRkNKnRB+pCfGS3EZTq0
deI3rcurPsBe34B/SxZF7G1hLVhEtom18YUbZvSBxgCJmI7D239e/Qz6bgqB7FAo
rFJ/S3ECgYEA+oCEP5NjBilqOHSdLLPhI/Ak6pNIK017xMBdiBTjnRh93D8Xzvfh
glkHRisZo8gmIZsgW3izlEeUv4CaVf7OzlOUiu2KmmrLxGHPoT+QPLf/Ak3GZE14
XY9vtaQQSwxM+i5sNtAD/3/KcjH6wT1B+8R4xqtHUYXw7VoEQWRSs/UCgYEAz4hW
j7+ooYlyHzkfuiEMJG0CtKR/fYsd9Zygn+Y6gGQvCiL+skAmx/ymG/qU6D8ZejkN
Azzv7JGQ+1z8OtTNStgDPE7IT74pA0BC60jHySDYzyGAaoMJDhHxA2CPm60EwPDU
5pRVy+FN5LmCCT8oDgcpsPpgjALOqR2TUkcOziUCgYAFXdN3eTTZ4PFBnF3xozjj
iDWCQP1+z/4izOw0Ch6GMwwfN8rOyEiwfi/FtQ6rj5Ihji03SHKwboglQiAMT5Um
nmvEPiqF/Fu5LU9BaRcx9c8kwX3KkE5P0s7V2VnwAad0hKIU2of7ZUV1BNUWZrWP
KzpbJzgz6uaqbw9AR2HuMQJ/YuaWWer8cf8OY9LVS95z6ugIYg4Cs9GYdXQvGASf
3I/h2vLSbiAkWyoL/0lrrUJk4dpOWTyxGgxFC4VErsS7EO/gmtzwmRAGe4YkXfxR
OYhtykgs6pWHuyzRrspVpdrOaSRcUYZfXMoCVP4S+lUewZCoTa8EU7UCx5VQn+U9
KQKBgQDsjVRcsfC/szL7KgeheEN/2zRADix5bqrg0rAB1y+sw+yzkCCh3jcRn2O2
wNIMroggGNy+vcR8Xo/V1wLCsEn45cxB6W7onqxFRM6IkGxkBgdatEL/aBnETSAI
x4C5J+IqaT2T53O2n3DR+GsVoeNUbz8j/lPONNQnV0ZqHRVWpA==
-----END RSA PRIVATE KEY-----
KEYEOF
  chmod 600 "$KEY_PATH"
fi

# Get database URL
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL environment variable is not set!"
  exit 1
fi

# Test the connection
echo "Testing connection to EC2 instance at $EC2_IP..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'"; then
  echo "Failed to connect to EC2 instance. Check your EC2_PUBLIC_IP variable."
  exit 1
fi

echo "Connection successful!"

# Create a temporary script to check available data
echo "Creating script to check available data..."
cat > check_data.py << EOF
#!/usr/bin/env python3
"""
Script to check available market data in the database
"""
import os
import sys
import psycopg2
import psycopg2.extras
import json
from datetime import datetime

def check_available_data():
    """Check what market data is available in the database"""
    try:
        # Connect to the database
        db_url = "$DB_URL"
        print(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get available symbols
        print("\nAvailable symbols:")
        cursor.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol")
        symbols = [row[0] for row in cursor.fetchall()]
        
        for symbol in symbols:
            print(f"- {symbol}")
        
        # Get available intervals
        print("\nAvailable intervals:")
        cursor.execute("SELECT DISTINCT interval FROM market_data ORDER BY interval")
        intervals = [row[0] for row in cursor.fetchall()]
        
        for interval in intervals:
            print(f"- {interval}")
        
        # Get data date ranges for BTCUSDT
        print("\nData date ranges for BTCUSDT:")
        
        for interval in intervals:
            cursor.execute(
                "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM market_data WHERE symbol = 'BTCUSDT' AND interval = %s",
                (interval,)
            )
            row = cursor.fetchone()
            
            if row and row[2] > 0:
                min_date = row[0].strftime("%Y-%m-%d %H:%M:%S")
                max_date = row[1].strftime("%Y-%m-%d %H:%M:%S")
                count = row[2]
                
                print(f"- {interval}: {min_date} to {max_date} ({count} candles)")
            else:
                print(f"- {interval}: No data")
        
        # Get recent data samples for BTCUSDT 1h
        print("\nRecent data samples for BTCUSDT 1h:")
        cursor.execute(
            "SELECT timestamp, open, high, low, close, volume FROM market_data WHERE symbol = 'BTCUSDT' AND interval = '1h' ORDER BY timestamp DESC LIMIT 5"
        )
        
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                timestamp = row[0].strftime("%Y-%m-%d %H:%M:%S")
                print(f"- {timestamp}: Open={row[1]}, High={row[2]}, Low={row[3]}, Close={row[4]}, Volume={row[5]}")
        else:
            print("No data available")
        
        # Get recommended date range for backtesting
        print("\nRecommended date ranges for backtesting:")
        
        for interval in ['1h', '4h', '1d']:
            cursor.execute(
                "SELECT timestamp FROM market_data WHERE symbol = 'BTCUSDT' AND interval = %s ORDER BY timestamp DESC LIMIT 1 OFFSET 30",
                (interval,)
            )
            row = cursor.fetchone()
            
            if row:
                from_date = row[0].strftime("%Y-%m-%d")
                
                cursor.execute(
                    "SELECT timestamp FROM market_data WHERE symbol = 'BTCUSDT' AND interval = %s ORDER BY timestamp DESC LIMIT 1",
                    (interval,)
                )
                to_row = cursor.fetchone()
                to_date = to_row[0].strftime("%Y-%m-%d") if to_row else "N/A"
                
                print(f"- {interval}: --start {from_date} --end {to_date}")
            else:
                print(f"- {interval}: Not enough data")
        
        # Close database connection
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"Error checking available data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_available_data()
EOF

# Copy script to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no check_data.py "$SSH_USER@$EC2_IP:$EC2_DIR/check_data.py"

# Run script on EC2
echo "Checking available data on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && python3 check_data.py"

# Clean up
rm check_data.py

echo "Data check completed."