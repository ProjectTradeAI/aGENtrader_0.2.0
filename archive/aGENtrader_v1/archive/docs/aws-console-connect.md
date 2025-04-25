# AWS Console Connect Instructions

If SSH is not working, you can use AWS Console to connect directly to your EC2 instance:

1. Go to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance (with IP: 51.20.250.135)
4. Click the "Connect" button
5. Choose "EC2 Instance Connect" tab
6. Click "Connect"

This will open a browser-based terminal session directly to your instance, bypassing any SSH key issues.

## Running Backtests from the Console

Once connected via the AWS Console, you can run backtests with these commands:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# Run a simplified backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50

# Run an enhanced backtest with OpenAI
./ec2-multi-agent-backtest.sh --type enhanced --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75

# Use local Mixtral model
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm
```

## Getting Results

To view backtest results:
```bash
# List all result files
ls -la results/

# View a specific result file
cat results/backtest_result_YYYYMMDD_HHMMSS.json
```
