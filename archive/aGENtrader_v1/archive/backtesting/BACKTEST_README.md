# Smart Backtest Runner

This script automates the process of running backtests with the correct parameters based on the backtest type.

## Features

- Automatically selects the right parameters based on backtest type
- Supports simplified, enhanced, and full-scale backtests
- Option to show agent communications in the logs
- Support for both local LLM and OpenAI API
- User-friendly configuration display

## Usage

```bash
./smart-backtest-runner.sh [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Type of backtest: simplified, enhanced, full-scale | enhanced |
| `--symbol SYMBOL` | Trading symbol | BTCUSDT |
| `--interval INTERVAL` | Time interval: 1m, 5m, 15m, 1h, 4h, 1d | 1h |
| `--start DATE` | Start date in YYYY-MM-DD format | 2025-03-01 |
| `--end DATE` | End date in YYYY-MM-DD format | 2025-03-07 |
| `--balance AMOUNT` | Initial balance for enhanced/full-scale | 10000 |
| `--risk DECIMAL` | Risk percentage as decimal | 0.02 |
| `--position-size SIZE` | Position size for simplified backtest | 50 |
| `--openai` | Use OpenAI API instead of local LLM | (not set) |
| `--show-agent-comms` | Show agent communications in the log | (not set) |
| `--help` | Show help message | (not set) |

## Examples

### Run a simplified backtest for 3 days
```bash
./smart-backtest-runner.sh --type simplified --start 2025-03-01 --end 2025-03-03
```

### Run an enhanced backtest with 4-hour interval
```bash
./smart-backtest-runner.sh --type enhanced --symbol BTCUSDT --interval 4h
```

### Run a full-scale backtest with custom balance and risk, showing agent communications
```bash
./smart-backtest-runner.sh --type full-scale --balance 20000 --risk 0.01 --show-agent-comms
```

## Checking Results

- To check the latest results: `./ec2-backtest.sh list`
- To view the latest log: `./ec2-backtest.sh log`
- To download a specific result file: `./ec2-backtest.sh get [filename]`

## Agent Communications

Using the `--show-agent-comms` option will enable detailed logging of agent communications during the backtest, allowing you to see how the agents are interacting and making decisions.
