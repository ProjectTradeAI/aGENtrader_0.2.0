#!/bin/bash
# Deploy direct agent fix script to EC2 and run it

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="direct-fix-${TIMESTAMP}.log"

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

echo "🔧 Deploying Direct Agent Fix" | tee "$LOG_FILE"
echo "============================" | tee -a "$LOG_FILE"

# Test EC2 connection
echo "Testing EC2 connection..." | tee -a "$LOG_FILE"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" >> "$LOG_FILE" 2>&1; then
  echo "Failed to connect to EC2. Please check your connection settings." | tee -a "$LOG_FILE"
  exit 1
fi
echo "✅ EC2 connection successful" | tee -a "$LOG_FILE"

# Create the run wrapper to execute the backtest after fixing
cat > run-backtest-after-fix.sh << 'EOF'
#!/bin/bash
# Run backtest after applying direct agent fix

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "PYTHONPATH set to: $PYTHONPATH"

# Create needed directories
mkdir -p data/logs results

# Run the direct agent fix and save the summary
echo "Running direct agent fix..."
python3 direct-agent-fix.py | tee direct-fix-summary.txt

# If successful, run a real backtest with proper parameters
echo "Running backtest with full agent communications..."
python3 -m backtesting.core.authentic_backtest \
  --symbol "$1" \
  --interval "$2" \
  --start_date "$3" \
  --end_date "$4" \
  --initial_balance "$5" \
  --output_dir results | tee agent-backtest.log

# Check if agent communications log exists
echo "Checking for agent communications logs..."
LATEST_LOG=$(find data/logs -name "direct_agent_comms_*.log" | sort -r | head -n 1)

if [ -n "$LATEST_LOG" ]; then
  echo "Found agent communications log: $LATEST_LOG"
  echo "Agent communications excerpt (first 20 lines):"
  head -n 20 "$LATEST_LOG"
  echo "Agent communications excerpt (last 20 lines):"
  tail -n 20 "$LATEST_LOG"
  echo "(... more content in $LATEST_LOG ...)"
else
  echo "No agent communications log found."
fi

# Check for result files
echo "Checking for result files..."
LATEST_RESULT=$(find results -name "*backtest*.json" | sort -r | head -n 1)

if [ -n "$LATEST_RESULT" ]; then
  echo "Found result file: $LATEST_RESULT"
  echo "Backtest results summary:"
  cat "$LATEST_RESULT" | python -m json.tool
else
  echo "No result file found."
fi

echo "Done."
EOF
chmod +x run-backtest-after-fix.sh

# Upload files to EC2
echo "Uploading files to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no direct-agent-fix.py "$SSH_USER@$EC2_IP:$EC2_DIR/" >> "$LOG_FILE" 2>&1
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no run-backtest-after-fix.sh "$SSH_USER@$EC2_IP:$EC2_DIR/" >> "$LOG_FILE" 2>&1
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/direct-agent-fix.py $EC2_DIR/run-backtest-after-fix.sh" >> "$LOG_FILE" 2>&1

# Run the direct fix and backtest
echo "Running direct agent fix and backtest on EC2..." | tee -a "$LOG_FILE"
echo "This may take a few minutes. Please be patient..." | tee -a "$LOG_FILE"

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' ./run-backtest-after-fix.sh BTCUSDT 1h 2025-04-10 2025-04-12 10000" | tee -a "$LOG_FILE"

# Download logs and results
echo "Downloading logs and results from EC2..." | tee -a "$LOG_FILE"
mkdir -p ./results/logs

# Download logs
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/direct_agent_fix_*.log" ./results/logs/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/data/logs/direct_agent_comms_*.log" ./results/logs/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/direct-fix-summary.txt" ./results/ 2>/dev/null
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/agent-backtest.log" ./results/ 2>/dev/null

# Download result files
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/results/*backtest*.json" ./results/ 2>/dev/null

echo "✅ Direct agent fix and backtest completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"

# Check if agent communications logs were downloaded
AGENT_LOGS=$(find ./results/logs -name "direct_agent_comms_*.log" 2>/dev/null)
if [ -n "$AGENT_LOGS" ]; then
  echo "✅ Agent communications logs were downloaded" | tee -a "$LOG_FILE"
  echo "Agent log files: $AGENT_LOGS" | tee -a "$LOG_FILE"
  
  # Display a sample of the agent communications
  LATEST_LOG=$(find ./results/logs -name "direct_agent_comms_*.log" | sort -r | head -n 1)
  if [ -n "$LATEST_LOG" ]; then
    echo -e "\n===== SAMPLE OF AGENT COMMUNICATIONS =====" | tee -a "$LOG_FILE"
    head -n 20 "$LATEST_LOG" | tee -a "$LOG_FILE"
    echo -e "\n(... more content in $LATEST_LOG ...)\n" | tee -a "$LOG_FILE"
  fi
else
  echo "❌ No agent communications logs were downloaded" | tee -a "$LOG_FILE"
fi