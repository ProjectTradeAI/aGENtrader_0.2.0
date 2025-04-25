#!/bin/bash
# Run simplified enhanced backtest

# Setup SSH key
KEY_PATH="/tmp/simplified_key.pem"
echo "Setting up SSH key..."
echo "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_PATH"
echo "$EC2_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY----- //g' | sed 's/ -----END RSA PRIVATE KEY-----//g' | fold -w 64 >> "$KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Run the simplified backtest
echo "Running simplified enhanced backtest..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && python3 run_simplified_enhanced_backtest.py"

# Check the results
echo
echo "Checking latest results..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$EC2_PUBLIC_IP "cd /home/ec2-user/aGENtrader && ls -la results/ | grep 'simplified' | tail -n 5"
