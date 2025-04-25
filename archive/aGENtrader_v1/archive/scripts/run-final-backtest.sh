#!/bin/bash
# Run the final backtest using the fixed agent framework

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"

# Command line arguments
SYMBOL="BTCUSDT"
INTERVAL="1h"
START_DATE="2025-03-20"
END_DATE="2025-03-22"
BALANCE="10000"

while [[ $# -gt 0 ]]; do
  case $1 in
    --symbol)
      SYMBOL="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --start)
      START_DATE="$2"
      shift 2
      ;;
    --end)
      END_DATE="$2"
      shift 2
      ;;
    --balance)
      BALANCE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create key file if needed
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

# Get environment variables
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")
OPENAI_API_KEY=$(node -e "console.log(process.env.OPENAI_API_KEY || '')")

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL environment variable is not set!"
  exit 1
fi

echo "🔄 Checking for agent framework on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && [ -f orchestration/decision_session.py ] && echo 'Agent framework found' || echo 'Agent framework missing'"

echo -e "\n🔍 Verifying Python imports..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && python3 -c 'import sys; sys.path.insert(0, \".\"); try: from orchestration.decision_session import DecisionSession; print(\"✅ DecisionSession imported successfully\"); except Exception as e: print(f\"❌ Import error: {str(e)}\")'"

echo -e "\n🚀 Running Multi-Agent Backtest on EC2"
echo "==================================================="
echo "Parameters:"
echo "- Symbol: $SYMBOL"
echo "- Interval: $INTERVAL"
echo "- Date Range: $START_DATE to $END_DATE"
echo "- Initial Balance: $BALANCE"
echo -e "==================================================="

# Run the backtest with PYTHONPATH set
echo -e "\n▶️ Executing backtest..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && PYTHONPATH=\$PWD DATABASE_URL=\"$DB_URL\" ALPACA_API_KEY=\"$ALPACA_API_KEY\" ALPACA_API_SECRET=\"$ALPACA_API_SECRET\" OPENAI_API_KEY=\"$OPENAI_API_KEY\" python3 backtesting/core/authentic_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE"

# Download results
echo -e "\n📊 Retrieving backtest results..."
LATEST_RESULT=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "ls -t $EC2_DIR/results/backtest_*.json 2>/dev/null | head -n 1")

if [ -n "$LATEST_RESULT" ]; then
  echo "Latest result file on EC2: $LATEST_RESULT"
  
  # Download and display results
  mkdir -p ./results
  LOCAL_RESULT="./results/$(basename $LATEST_RESULT)"
  scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$LATEST_RESULT" "$LOCAL_RESULT"
  
  echo -e "\n📈 BACKTEST RESULTS SUMMARY"
  echo "========================="
  
  if [ -f "$LOCAL_RESULT" ]; then
    python3 -c "
import json
import sys

try:
    with open('$LOCAL_RESULT', 'r') as f:
        data = json.load(f)
    
    print(f\"Symbol: {data.get('symbol')}\")
    print(f\"Interval: {data.get('interval')}\")
    print(f\"Period: {data.get('start_date')} to {data.get('end_date')}\")
    
    metrics = data.get('performance_metrics', {})
    print(f\"\\nPerformance Metrics:\")
    print(f\"Initial Balance: \${metrics.get('initial_balance', 0):.2f}\")
    print(f\"Final Equity: \${metrics.get('final_equity', 0):.2f}\")
    print(f\"Total Return: {metrics.get('total_return_pct', 0):.2f}%\")
    print(f\"Win Rate: {metrics.get('win_rate', 0):.2f}% ({metrics.get('winning_trades', 0)}/{metrics.get('total_trades', 0)})\")
    print(f\"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%\")
    
    trades = data.get('trades', [])
    if trades:
        print(f\"\\nTrades:\")
        for i, trade in enumerate(trades):
            if trade.get('type') == 'ENTRY':
                print(f\"{i+1}. {trade.get('direction', '')} Entry at \${trade.get('price', 0):.2f} ({trade.get('timestamp', '')})\")
            else:
                print(f\"{i+1}. {trade.get('direction', '')} Exit at \${trade.get('exit_price', 0):.2f} ({trade.get('timestamp', '')}) - PnL: {trade.get('pnl_percentage', 0):.2f}%\")
    
except Exception as e:
    print(f\"Error reading results: {str(e)}\")
    sys.exit(1)
"
  else
    echo "Failed to download results file"
  fi
else
  echo "No results found on EC2"
fi

echo -e "\n✅ Multi-agent backtest process completed!"