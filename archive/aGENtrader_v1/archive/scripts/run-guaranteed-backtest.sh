#!/bin/bash
# Run guaranteed agent communications backtest

# Setup SSH key
KEY_PATH="/tmp/guaranteed_backtest_key.pem"
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

echo "Running guaranteed agent communications backtest with parameters:"
echo "Symbol: $SYMBOL"
echo "Interval: $INTERVAL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Balance: $BALANCE"
echo

# Upload the guaranteed backtest script to EC2
echo "Uploading guaranteed backtest script to EC2..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no guaranteed_agent_comms_backtest.py ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/

# Run the guaranteed backtest
echo "Running guaranteed backtest on EC2..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 guaranteed_agent_comms_backtest.py --symbol $SYMBOL --interval $INTERVAL --start_date $START_DATE --end_date $END_DATE --initial_balance $BALANCE"

# Check the results
echo
echo "Checking latest results and logs..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | grep 'guaranteed' | tail -n 5"

echo
echo "Locating the latest agent communication log file..."
LATEST_LOG=$(ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && find data/logs -name 'agent_comms_guaranteed_*.log' -type f -mmin -60 | sort -r | head -n 1")
echo "Latest agent comms log: $LATEST_LOG"

# Download the latest agent communications log
echo
echo "Downloading the latest agent communications log..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$EC2_PUBLIC_IP:/home/ec2-user/aGENtrader/$LATEST_LOG" ./latest_agent_comms.log

echo
echo "Latest agent communications log downloaded to: ./latest_agent_comms.log"
echo "Showing content of downloaded log:"
cat ./latest_agent_comms.log | head -n 20
echo "..."
cat ./latest_agent_comms.log | tail -n 10
