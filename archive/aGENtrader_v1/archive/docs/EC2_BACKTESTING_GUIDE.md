# EC2 Backtesting Guide

This guide provides comprehensive instructions for running backtests on your EC2 instance from Replit.

## Table of Contents
- [Overview](#overview)
- [Connection Methods](#connection-methods)
- [Backtest Scripts](#backtest-scripts)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The multi-agent trading system is deployed on an EC2 instance with the following capabilities:
- Support for multiple backtest types (simplified, enhanced, full-scale)
- Local LLM inference using Mixtral 8x7B (quantized model)
- Comprehensive market data for BTC/USDT and other pairs
- Advanced technical indicators and decision-making frameworks

## Connection Methods

### Using the Mixtral Backtest Script (Recommended)

For running full-scale backtests using the Mixtral model:

```bash
./mixtral-backtest.sh [options]
```

This script provides a streamlined interface for running full-scale multi-agent backtests with the Mixtral model.

### Using the Full Backtest Script

For more customization options:

```bash
./run-full-backtest.sh [options]
```

This script provides all available options for configuring full-scale backtests.

### Using the EC2 Connection Script

For direct command execution on EC2:

```bash
./ec2-connect.sh [command]
```

This script provides a reliable connection to your EC2 instance for running arbitrary commands.

### Using the EC2 Backtest Script

For running any type of backtest:

```bash
./ec2-backtest.sh [command] [options]
```

This script provides a comprehensive interface for managing all types of backtests.

## Backtest Scripts

### Full-Scale Multi-Agent Backtest

Run a full-scale backtest with multiple collaborative agents:

```bash
./mixtral-backtest.sh --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-31
```

### Enhanced Backtest

Run an enhanced backtest with improved position sizing:

```bash
./ec2-backtest.sh run --type enhanced --symbol BTCUSDT --interval 4h --start 2025-02-01 --end 2025-03-01
```

### Simplified Backtest

Run a simplified backtest for quick performance evaluation:

```bash
./ec2-backtest.sh run --type simplified --symbol BTCUSDT --interval 1h --position 100
```

## Usage Examples

### Running a Full-Scale Backtest with Mixtral

```bash
./mixtral-backtest.sh --interval 1h --risk 0.03
```

This will run a full-scale backtest with:
- Trading symbol: BTCUSDT
- Time interval: 1h
- Date range: 2025-03-01 to 2025-03-31
- Risk percentage: 0.03
- LLM: Mixtral 8x7B (local)

### Downloading Results

```bash
./ec2-backtest.sh get BTCUSDT_combined_backtest_20250406_145142.json
```

This will download the specified result file to `./ec2_results/` directory.

### Checking EC2 Status

```bash
./ec2-backtest.sh status
```

This will display:
- EC2 system status (CPU, memory, disk)
- Running backtest processes
- Latest backtest results and logs

## Troubleshooting

### SSH Connection Issues

If you encounter SSH connection issues:

1. Ensure the EC2 instance is running
2. Check that the EC2_KEY secret is properly configured in Replit
3. Try running commands with the `--verbose` flag for detailed output
4. Use the AWS Console method as a fallback (see aws-console-connect.md)

### Backtest Failures

If a backtest fails:

1. Check the backtest logs: `./ec2-backtest.sh log`
2. Verify that the date range has available market data
3. Ensure the Mixtral model is properly installed on EC2
4. Try running with the `--verbose` flag for more detailed output

## Best Practices

1. **Start Small**: Begin with shorter date ranges and simplified backtests
2. **Save Configuration**: The scripts save your configuration for easy reuse
3. **Disk Space**: Monitor disk space on the EC2 instance (currently 96% full)
4. **Verify Parameters**: Use `--dry-run` to verify parameters before running long backtests
5. **Download Results**: Always download important backtest results to Replit for safekeeping