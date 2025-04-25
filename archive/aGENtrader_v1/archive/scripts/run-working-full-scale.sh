#!/bin/bash
# Run working full-scale backtest

# Setup SSH key
KEY_PATH="/tmp/working_full_scale_key.pem"
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

echo "Running working full-scale backtest with parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Balance: $BALANCE"
echo

# Upload the working full-scale backtest script to EC2
echo "Uploading working full-scale backtest script to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no working_full_scale_backtest.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Run the working full-scale backtest
echo "Running working full-scale backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 working_full_scale_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE"

# Check the results
echo
echo "Checking latest results..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | grep 'working_full_scale' | tail -n 5"

# Check the log files
echo
echo "Checking latest agent communication log files..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_*.log' -type f -mmin -5 | xargs ls -la"

# Retrieve the latest agent log
echo
echo "Retrieving the latest agent communication log..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_*.log' -type f -mmin -5 | sort -r | head -n 1 | xargs cat | tail -n 20"
