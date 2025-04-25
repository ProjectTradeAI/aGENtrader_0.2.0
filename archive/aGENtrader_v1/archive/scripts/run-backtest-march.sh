#!/bin/bash
# Run hardcoded backtest for March 2025 data

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

# Test the connection
echo "Testing connection to EC2 instance at $EC2_IP..."
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'"; then
  echo "Failed to connect to EC2 instance. Check your EC2_PUBLIC_IP variable."
  exit 1
fi

echo "Connection successful!"

# Run backtests with March 2025 data
echo "🚀 Running Hardcoded Backtest on EC2 (March 2025 data)"
echo "==================================================="
echo "Parameters:"
echo "- Symbol: BTCUSDT"
echo "- Interval: 1h"
echo "- Date Range: 2025-03-01 to 2025-03-31"
echo "- Initial Balance: 10000"
echo ""

# Run the backtest on EC2
echo "Running backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && ./run_backtest_hardcoded.sh --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-31 --initial_balance 10000"

# Get the latest result file from EC2
echo "Checking for results..."
LATEST_RESULT=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t $EC2_DIR/results/backtest_*.json 2>/dev/null | head -n 1")

if [ -n "$LATEST_RESULT" ]; then
  echo "Latest result file on EC2: $LATEST_RESULT"
  
  # Download the result file
  echo "Downloading result file from EC2..."
  mkdir -p ./results
  LOCAL_RESULT="./results/$(basename $LATEST_RESULT)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_RESULT" "$LOCAL_RESULT"
  echo "Downloaded result file to: $LOCAL_RESULT"
  
  # Display a summary
  if [ -f "$LOCAL_RESULT" ]; then
    echo "Result summary:"
    grep -E '"symbol"|"interval"|"initial_balance"|"final_balance"|"profit"|"percent_return"|"total_trades"|"winning_trades"|"win_rate"' "$LOCAL_RESULT" | sed 's/,$//'
  fi
fi

# Get the latest log file from EC2
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t $EC2_DIR/logs/backtests/backtest_*.log 2>/dev/null | head -n 1")

if [ -n "$LATEST_LOG" ]; then
  echo "Latest log file on EC2: $LATEST_LOG"
  
  # Download the log file
  echo "Downloading log file from EC2..."
  mkdir -p ./logs/backtests
  LOCAL_LOG="./logs/backtests/$(basename $LATEST_LOG)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_LOG" "$LOCAL_LOG"
  echo "Downloaded log file to: $LOCAL_LOG"
fi

echo "✅ Backtest process completed!"