# Backtest Parameter Issue - Fixed

## The Problem

There was a critical bug in the backtesting system that caused the error:
```
run_backtest_with_local_llm.py: error: unrecognized arguments: --position_size 50
```

The issue was in the `ec2-multi-agent-backtest.sh` script on EC2, which incorrectly passed `--position_size` parameter to `run_backtest_with_local_llm.py` script that doesn't support this parameter.

## Changes Made

We made the following changes:

1. Fixed the `ec2-multi-agent-backtest.sh` script on EC2 to:
   - Use the correct Python script (`run_simplified_backtest.py`) when running simplified backtests with local LLM
   - Use the correct parameters based on the backtest type

2. Updated the local `ec2-backtest.sh` script to:
   - Properly handle different parameter sets based on backtest type
   - Provide better error messages and help information
   - Improve configuration display

3. Created a smart helper script (`smart-backtest-runner.sh`) that:
   - Automatically selects the right parameters based on backtest type
   - Provides an option to show agent communications in logs
   - Includes comprehensive documentation

## How to Run Backtests

### Basic Usage

```bash
# Simplified backtest with local LLM
./ec2-backtest.sh run --type simplified --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-07 --position_size 50 --local-llm

# Enhanced backtest with local LLM
./ec2-backtest.sh run --type enhanced --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-07 --balance 10000 --risk 0.02 --local-llm
```

### Using the Smart Runner

```bash
# Simplified backtest
./smart-backtest-runner.sh --type simplified --start 2025-03-01 --end 2025-03-03 --position-size 50

# Enhanced backtest with agent communications
./smart-backtest-runner.sh --type enhanced --start 2025-03-01 --end 2025-03-03 --show-agent-comms
```

## Verifying Agent Communications

To verify that the multi-agent framework is working properly, add the `--show-agent-comms` flag when using `smart-backtest-runner.sh`:

```bash
./smart-backtest-runner.sh --type enhanced --start 2025-03-01 --end 2025-03-02 --show-agent-comms
```

This will:
1. Create a custom logging script on EC2
2. Patch key agent classes to add detailed logging
3. Show agent communications in the log output
4. Save a detailed agent communications log file

## Checking Results

- List available results: `./ec2-backtest.sh list`
- View the latest log: `./ec2-backtest.sh log`
- Download a result file: `./ec2-backtest.sh get <filename>`
