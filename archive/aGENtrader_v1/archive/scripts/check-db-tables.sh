#!/bin/bash
# Script to check database tables and structure

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
  echo "DATABASE_URL environment variable is not set!"
  exit 1
fi

# Create a script on EC2 to check database tables
cat > check_db_tables.py << 'EOF'
#!/usr/bin/env python3
"""
Script to check database tables and structure
"""
import os
import sys
import psycopg2
import psycopg2.extras
import json

def check_database_tables():
    """Check tables in the database"""
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("ERROR: DATABASE_URL not set")
            return False
        
        # Connect to the database
        print(f"Connecting to database: {db_url[:10]}...{db_url[-10:]}")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get list of tables
        print("\nListing tables in database:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            print(f"- {table}")
        
        # Check for market data tables
        print("\nSearching for market data tables:")
        for table in tables:
            if 'market' in table.lower() or 'candle' in table.lower() or 'kline' in table.lower() or 'price' in table.lower():
                print(f"\nExamining table: {table}")
                
                # Get table structure
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                print("Columns:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                
                # Get sample data
                cursor.execute(f"""
                    SELECT * FROM {table} LIMIT 1
                """)
                
                sample = cursor.fetchone()
                if sample:
                    print("\nSample data:")
                    for k, v in dict(sample).items():
                        print(f"  - {k}: {type(v).__name__}({v})")
        
        # Check specifically for time-interval related tables
        print("\nSearching for time-interval tables (1h, 4h, etc.):")
        interval_found = False
        for table in tables:
            # Look for tables with interval names in them
            if any(interval in table.lower() for interval in ['1m', '5m', '15m', '1h', '4h', '1d']):
                interval_found = True
                print(f"- {table}")
                
                # Get sample data
                cursor.execute(f"""
                    SELECT * FROM {table} LIMIT 1
                """)
                
                sample = cursor.fetchone()
                if sample:
                    print(f"\nSample data from {table}:")
                    for k, v in dict(sample).items():
                        print(f"  - {k}: {type(v).__name__}({v})")
        
        if not interval_found:
            print("No specific interval tables found")
        
        # Check if the market_data table has an interval column
        if 'market_data' in tables:
            print("\nChecking market_data table for interval column:")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'market_data' AND column_name = 'interval'
            """)
            
            if cursor.fetchone():
                print("- 'interval' column found in market_data table")
                
                # Get unique intervals
                cursor.execute("""
                    SELECT DISTINCT interval FROM market_data
                """)
                
                intervals = [row[0] for row in cursor.fetchall()]
                print("- Available intervals: " + ", ".join(intervals))
                
                # Check data availability
                print("\nChecking data availability for different intervals:")
                for interval in intervals:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM market_data WHERE interval = '{interval}'
                    """)
                    
                    count = cursor.fetchone()[0]
                    print(f"- {interval}: {count} rows")
            else:
                print("- No 'interval' column found in market_data table")
        
        # Close database connection
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"Error checking database tables: {str(e)}")
        return False

if __name__ == "__main__":
    check_database_tables()
EOF

# Copy script to EC2
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no check_db_tables.py "$SSH_USER@$EC2_IP:$EC2_DIR/check_db_tables.py"

# Run the script on EC2
echo "Running database table check on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL=\"$DB_URL\" python3 check_db_tables.py"

# Clean up local script
rm check_db_tables.py

echo "Database check completed."