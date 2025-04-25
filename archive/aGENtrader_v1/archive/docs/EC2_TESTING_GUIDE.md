# EC2 Testing Guide for Trading System

This guide provides instructions for running simplified backtests on your EC2 instance and analyzing the results.

## Prerequisites

1. EC2 instance set up with Python 3.x
2. SSH key for connecting to EC2
3. SSH access to your EC2 instance
4. Environment variables:
   - `EC2_PUBLIC_IP` - Public IP of your EC2 instance
   - `EC2_SSH_KEY` - SSH private key (content of PEM file)

## Testing Scripts Overview

The following scripts are available for conducting tests on your EC2 instance:

1. **improved_simplified_test.py** - A robust testing framework for running strategy backtests with mock data
2. **advanced_test.py** - A simplified test that generates trades based on win rate rather than market data
3. **ec2_file_transfer.sh** - Utility for transferring files to/from the EC2 instance
4. **run-ec2-backtest.sh** - Simplifies running backtests on EC2 using environment variables
5. **ec2_results_analyzer.py** - Analyzes and compares test results

## Step 1: Upload Scripts to EC2

First, transfer the test scripts to your EC2 instance:

```bash
./ec2_file_transfer.sh -i your_key.pem -h EC2_IP_ADDRESS push improved_simplified_test.py
./ec2_file_transfer.sh -i your_key.pem -h EC2_IP_ADDRESS push advanced_test.py
```

Alternatively, you can use the direct SSH command approach:

```bash
./direct-ssh-command.sh "cat > /home/ec2-user/aGENtrader/improved_simplified_test.py" < improved_simplified_test.py
./direct-ssh-command.sh "cat > /home/ec2-user/aGENtrader/advanced_test.py" < advanced_test.py
./direct-ssh-command.sh "chmod +x /home/ec2-user/aGENtrader/improved_simplified_test.py /home/ec2-user/aGENtrader/advanced_test.py"
```

## Step 2: Run Backtests on EC2

You can run backtests using the `run-ec2-backtest.sh` script:

### Using Environment Variables

If you've set up the environment variables `EC2_PUBLIC_IP` and `EC2_SSH_KEY`, you can simply run:

```bash
# Run improved test with default parameters
./run-ec2-backtest.sh

# Run improved test with specific strategy
./run-ec2-backtest.sh --strategy combined

# Compare all strategies
./run-ec2-backtest.sh --compare

# Advanced test with customized parameters
./run-ec2-backtest.sh --advanced --trades 50 --win-rate 0.65
```

### Manual SSH Approach

Alternatively, you can run the tests directly via SSH:

```bash
# Run improved test
ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && python3 improved_simplified_test.py --strategy combined"

# Compare strategies
ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && python3 improved_simplified_test.py --compare"

# Run advanced test
ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && python3 advanced_test.py --trades 50 --win_rate 0.65"
```

## Step 3: Download Results from EC2

After running tests, download the results to your local machine:

```bash
# Using the transfer utility
./ec2_file_transfer.sh -i your_key.pem -h EC2_IP_ADDRESS sync-from-ec2

# Or directly with SCP
mkdir -p ./ec2_results
scp -i your_key.pem ec2-user@EC2_IP_ADDRESS:/home/ec2-user/aGENtrader/results/* ./ec2_results/
```

## Step 4: Analyze Results

Use the `ec2_results_analyzer.py` script to analyze the test results:

```bash
# Analyze all results in the directory
python3 ec2_results_analyzer.py --dir ec2_results

# Sort by a specific metric
python3 ec2_results_analyzer.py --dir ec2_results --sort sharpe_ratio

# Save a detailed report
python3 ec2_results_analyzer.py --dir ec2_results --output detailed_report.txt
```

## Available Trading Strategies

The improved simplified test supports the following trading strategies:

1. **ma_crossover** - Moving average crossover strategy (short MA crosses long MA)
2. **rsi** - Relative Strength Index based strategy (buy on oversold, sell on overbought)
3. **combined** - Combined strategy requiring confirmation from both MA and RSI signals

## Full-Scale Backtesting Options

For full-scale backtesting with real market data, you have several options:

1. **Database-Driven Backtest**:
   ```bash
   ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && python3 run_backtest_with_real_data.py --symbol BTCUSDT --interval 1h --start 2025-01-01 --end 2025-03-01"
   ```

2. **AutoGen Integration Test**:
   ```bash
   ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && python3 test_autogen_integration.py --symbol BTCUSDT --sessions 5"
   ```

3. **Local LLM Integration Test**:
   ```bash
   ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && python3 test_autogen_local_llm.py --model TinyLlama-1.1B-Chat-v1.0"
   ```

## Troubleshooting

Common issues and solutions:

1. **Permission Denied**: Make sure the SSH key has correct permissions:
   ```bash
   chmod 600 your_key.pem
   ```

2. **SSH Connection Issues**: Check if the EC2 instance is running and security group allows SSH:
   ```bash
   ping EC2_IP_ADDRESS
   ```

3. **Python Script Errors**: Check the logs on EC2:
   ```bash
   ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "cd /home/ec2-user/aGENtrader && cat *.log"
   ```

4. **Missing Results**: Ensure the results directory exists on EC2:
   ```bash
   ssh -i your_key.pem ec2-user@EC2_IP_ADDRESS "mkdir -p /home/ec2-user/aGENtrader/results"
   ```

5. **Environment Variable Issues**: Check if environment variables are set:
   ```bash
   echo $EC2_PUBLIC_IP
   echo "EC2_SSH_KEY is $(if [ -n \"$EC2_SSH_KEY\" ]; then echo \"set\"; else echo \"not set\"; fi)"
   ```