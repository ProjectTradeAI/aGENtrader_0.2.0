# Using AWS Console to Access EC2

Since we're continuing to have SSH key format issues, let's use these alternative methods:

## Method 1: EC2 Instance Connect (Browser-Based Access)

1. Log in to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance
4. Click "Connect"
5. Choose "EC2 Instance Connect"
6. Click "Connect"

This opens a browser-based terminal without needing SSH keys.

## EC2 Backtesting Commands

Once connected via the browser terminal, run:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# Run a simplified backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50

# Run an enhanced backtest with OpenAI
./ec2-multi-agent-backtest.sh --type enhanced --symbol BTCUSDT --interval 4h --start_date 2025-03-01 --end_date 2025-04-01 --balance 10000 --risk 0.02 --decision_interval 2 --min_confidence 75

# Run a backtest with local Mixtral model
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm
```

## View Results

```bash
# List result files
ls -la results/

# View a specific result
cat results/backtest_result_YYYYMMDD_HHMMSS.json
```
