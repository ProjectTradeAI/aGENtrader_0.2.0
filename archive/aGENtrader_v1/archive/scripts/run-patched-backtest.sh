#!/bin/bash
# Run a patched backtest with enhanced agent communications logging

# Setup SSH key
KEY_PATH="/tmp/run_patched_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

echo "Running the patched backtest with enhanced logging..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && chmod +x run_patched_backtest.py && python3 run_patched_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --initial_balance 10000 --risk_per_trade 0.02 --use_local_llm"

echo
echo "Retrieving the agent communications log..."
# Get the latest agent communications log
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "find /home/ec2-user/aGENtrader/data/logs -name 'agent_communications_*.log' | sort -r | head -n 1")

if [ -n "$LATEST_LOG" ]; then
  echo "Found log: $LATEST_LOG"
  echo "Log content:"
  echo "========================================================="
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cat $LATEST_LOG"
  echo "========================================================="
else
  echo "No agent communications log found."
fi
