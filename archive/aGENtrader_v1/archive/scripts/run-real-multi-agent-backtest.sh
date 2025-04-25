#!/bin/bash
# Run real multi-agent backtest

# Setup SSH key
KEY_PATH="/tmp/real_multi_agent_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Get parameters
SYMBOL=${1:-BTCUSDT}
INTERVAL=${2:-1h}
START_DATE=${3:-2025-03-01}
END_DATE=${4:-2025-03-02}
BALANCE=${5:-10000}

echo "Running real multi-agent backtest with parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Balance: $BALANCE"
echo

# Run the real multi-agent backtest
echo "Running real multi-agent backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 real_multi_agent_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE --use_local_llm --show_agent_comms"

# Check the results
echo
echo "Checking latest results..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | grep 'multi_agent' | tail -n 5"

# Check the agent communication logs
echo
echo "Checking for agent communication logs..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_*.log' -type f -mmin -5 | xargs ls -la"

echo
echo "Showing the latest agent communication log (if available)..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_*.log' -type f -mmin -5 | sort -r | head -n 1 | xargs cat || echo 'No recent agent communication logs found'"
