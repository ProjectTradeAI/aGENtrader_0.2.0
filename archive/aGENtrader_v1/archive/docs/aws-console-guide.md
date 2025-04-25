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
