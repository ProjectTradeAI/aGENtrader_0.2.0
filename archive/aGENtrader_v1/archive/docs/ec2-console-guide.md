# EC2 Console Connection Guide

Since SSH connection from Replit continues to have issues, here's how to connect and run backtests via the AWS Console:

## Connect via AWS Console

1. Log in to your AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance (IP: 51.20.250.135)
4. Click the "Connect" button at the top of the page
5. Select the "EC2 Instance Connect" tab
6. Leave the username as is (it will default to the correct one)
7. Click "Connect"

## Run Backtests Once Connected

After connecting, you can run backtests with these commands:

```bash
# Navigate to your project directory
cd /home/ec2-user/aGENtrader

# List available files
ls -la

# Run a simplified backtest
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-04-01 --position_size 50

# Run with local Mixtral model
./ec2-multi-agent-backtest.sh --type simplified --symbol BTCUSDT --interval 1h --local-llm

# See backtest results
ls -la results/
cat results/backtest_result_YYYYMMDD_HHMMSS.json
```

## Troubleshooting

If you encounter any issues:

1. Check file permissions:
   ```bash
   chmod +x ec2-multi-agent-backtest.sh
   ```

2. Check if Mixtral model is available (for local-llm option):
   ```bash
   ls -la ~/models/
   ```

3. View log files for details on any failures:
   ```bash
   cat data/logs/backtest_YYYYMMDD_HHMMSS.log
   ```
