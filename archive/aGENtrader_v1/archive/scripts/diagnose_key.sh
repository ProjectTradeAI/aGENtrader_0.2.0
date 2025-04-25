#!/bin/bash
# SSH Key diagnostic tool

KEY_PATH="/tmp/ec2_key_diagnostic.pem"
REPAIRED_KEY_PATH="/tmp/ec2_key_repaired.pem"

echo "======================================================"
echo "  SSH Key Diagnostic Tool"
echo "======================================================"
echo

# Save the key from environment variable
echo "$EC2_PRIVATE_KEY" > "$KEY_PATH"
chmod 600 "$KEY_PATH"

# Basic file info
echo "Key file information:"
echo "--------------------"
ls -la "$KEY_PATH"
file "$KEY_PATH"
echo "File size: $(wc -c < "$KEY_PATH") bytes"
echo "Line count: $(wc -l < "$KEY_PATH") lines"
echo

# Check beginning and end of file
echo "First 3 lines of key file:"
head -n 3 "$KEY_PATH" | cat -A
echo
echo "Last 3 lines of key file:"
tail -n 3 "$KEY_PATH" | cat -A
echo

# Check for PEM headers
echo "Checking PEM format:"
echo "------------------"
if grep -q "BEGIN RSA PRIVATE KEY" "$KEY_PATH"; then
    echo "✓ Found BEGIN RSA PRIVATE KEY marker"
else
    echo "✗ Missing BEGIN RSA PRIVATE KEY marker"
fi

if grep -q "END RSA PRIVATE KEY" "$KEY_PATH"; then
    echo "✓ Found END RSA PRIVATE KEY marker"
else
    echo "✗ Missing END RSA PRIVATE KEY marker"
fi
echo

# Try OpenSSL check
echo "OpenSSL validation:"
echo "-----------------"
openssl rsa -in "$KEY_PATH" -check -noout 2>&1 | head -n 3
echo

# Try to create a normalized key
echo "Creating normalized key file:"
echo "--------------------------"
grep -v "BEGIN\|END" "$KEY_PATH" | tr -d '\r\n' > /tmp/key_content.txt
echo "-----BEGIN RSA PRIVATE KEY-----" > "$REPAIRED_KEY_PATH"
fold -w 64 /tmp/key_content.txt >> "$REPAIRED_KEY_PATH"
echo "-----END RSA PRIVATE KEY-----" >> "$REPAIRED_KEY_PATH"
chmod 600 "$REPAIRED_KEY_PATH"
echo "Created normalized key at $REPAIRED_KEY_PATH"
echo

# Test the repaired key
echo "Testing repaired key with OpenSSL:"
echo "-------------------------------"
openssl rsa -in "$REPAIRED_KEY_PATH" -check -noout 2>&1 | head -n 3
echo

# Try to extract public key
echo "Attempting to extract public key:"
echo "------------------------------"
ssh-keygen -y -f "$REPAIRED_KEY_PATH" > /tmp/pubkey.txt 2>&1 || echo "Failed to extract public key"
cat /tmp/pubkey.txt | head -n 2
echo

# Create AWS console guide
cat > aws-console-guide.md << 'INNEREOF'
# AWS Console Guide for EC2 Access

Since we're encountering persistent issues with SSH key format, here are alternative methods to access your EC2 instance using the AWS Console:

## Method 1: EC2 Instance Connect

1. Log in to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance
4. Click "Connect"
5. Choose "EC2 Instance Connect"
6. Click "Connect"

This will open a browser-based terminal to your instance without requiring SSH keys.

## Method 2: AWS Systems Manager Session Manager

1. Log in to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance
4. Click "Connect"
5. Choose "Session Manager"
6. Click "Connect"

This provides more advanced remote access capabilities.

## Running Backtests from the Console

Once connected via the console:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# Run a simplified backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50

# Run an enhanced backtest
./ec2-multi-agent-backtest.sh --type enhanced --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75

# Use local LLM (Mixtral)
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm
```

## Viewing Results

To view backtest results:
```bash
# List result files
ls -la results/

# View a specific result file
cat results/backtest_result_2025-04-09_123456.json
```
INNEREOF

echo "Created key diagnostic tool and AWS Console guide."
