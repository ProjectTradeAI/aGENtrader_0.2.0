# EC2 Connection Issue Resolution Guide

## The Problem

We've identified that your EC2 SSH key is causing a `Load key: error in libcrypto` error. After multiple repair attempts, it appears the key is fundamentally corrupted or in an invalid format. This issue prevents SSH connections to your EC2 instance, which is needed for running backtests.

## Solution Options

### Option 1: Re-download a Fresh Key from AWS (Recommended)

The most reliable solution is to obtain a fresh, properly formatted key:

1. Log in to the AWS Management Console
2. Navigate to EC2 → Key Pairs
3. Create a new key pair:
   - Click "Create key pair"
   - Give it a name like "ec2-new-key"
   - Choose "RSA" as the key pair type
   - Choose ".pem" as the private key file format
   - Click "Create key pair" and download the .pem file
4. Associate the new key with your instance:
   - If you can connect via the AWS Console (see Option 2), you can add the new public key to `/home/ec2-user/.ssh/authorized_keys`
   - If you can't connect at all, you may need to create a new EC2 instance with the new key

### Option 2: Use AWS Console for Direct Access (No SSH Required)

AWS provides browser-based terminal access that doesn't require SSH keys:

1. Log in to the AWS Management Console
2. Navigate to EC2 → Instances
3. Select your instance
4. Click "Connect"
5. Choose one of these options:
   - "EC2 Instance Connect" - Simple browser terminal
   - "Session Manager" - More advanced access (requires SSM Agent)
6. Click "Connect"

Once connected, you can run commands directly:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# Run a backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm
```

### Option 3: Create a New EC2 Instance

If you can't connect at all and need to start fresh:

1. Launch a new EC2 instance using the same AMI
2. Create a new key pair during the setup process
3. Configure security groups to allow SSH access
4. Transfer your code to the new instance (or clone from GitHub/source)

## Running Backtests via AWS Console

The `ec2-multi-agent-backtest.sh` script should already be on your EC2 instance. Here's how to use it via AWS Console:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# Simplified backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50

# Enhanced backtest with OpenAI
./ec2-multi-agent-backtest.sh --type enhanced --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75

# Simplified backtest with local Mixtral model
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm

# Full-scale backtest
./ec2-multi-agent-backtest.sh --type full-scale --symbol BTCUSDT --interval 4h --balance 10000 --risk 0.02
```

## Viewing Backtest Results

To check results:

```bash
# List all result files
ls -la results/

# View a specific result file
cat results/backtest_result_YYYYMMDD_HHMMSS.json

# Copy results to a more accessible location
# (if AWS Console session times out)
cp results/backtest_result_YYYYMMDD_HHMMSS.json /tmp/
```

## Conclusion

While we couldn't fix the SSH key issue directly, these alternatives should allow you to continue your work with the EC2 instance. The AWS Console approach is especially useful as it requires no SSH keys at all.
