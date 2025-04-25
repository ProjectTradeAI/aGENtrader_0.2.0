# Comprehensive EC2 Connection Guide

## Current Issue
We're experiencing persistent issues with SSH key formatting that prevent direct SSH connections to your EC2 instance.

## Recommended Solutions

### Solution 1: Access via AWS Console (No SSH Needed)

1. Log in to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance
4. Click "Connect"
5. Choose "EC2 Instance Connect"
6. Click "Connect"

This opens a browser-based terminal without needing SSH keys.

### Solution 2: Create a New Key Pair

1. Log in to the AWS Management Console
2. Navigate to EC2 > Key Pairs
3. Click "Create key pair"
4. Name: "ec2-new-key"
5. Key pair type: RSA
6. Format: .pem
7. Click "Create key pair" and download the .pem file

After creating the new key pair:

1. Connect to EC2 via AWS Console (Solution 1)
2. Add the new public key to authorized_keys:
   ```bash
   # Generate public key from the private key on your local machine
   ssh-keygen -y -f /path/to/new-key.pem > new-key.pub
   
   # Add to authorized_keys on EC2 (via AWS Console)
   cat >> ~/.ssh/authorized_keys << 'EOF'
   [PASTE PUBLIC KEY HERE]
   EOF
   ```

### Solution 3: Launch a New Instance

If you need to start fresh:

1. Launch a new EC2 instance with the same configuration
2. Create a new key pair during setup
3. Transfer your code to the new instance

## Running Backtests

Once connected (via ANY method), run:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# Simplified backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50

# Enhanced backtest
./ec2-multi-agent-backtest.sh --type enhanced --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75

# Use local LLM (Mixtral)
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm
```

## Checking Results

```bash
# List result files
ls -la results/

# View a specific result
cat results/backtest_result_YYYYMMDD_HHMMSS.json

# If you need to download the results
# Option 1: Install AWS CLI and use S3
aws s3 cp results/backtest_result.json s3://your-bucket/

# Option 2: Copy to a public directory (if configured)
cp results/backtest_result.json /var/www/html/
```

## Summary

The AWS Console approach is the most reliable method for now. It bypasses SSH entirely and provides a direct browser-based terminal.
