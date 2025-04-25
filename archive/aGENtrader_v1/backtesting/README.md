# Backtesting Framework

This directory contains the backtesting framework for evaluating trading strategies using historical market data.

## Directory Structure

### `/backtesting/core`
Core backtesting engine components.

### `/backtesting/analysis`
Tools for analyzing and visualizing backtest results.

### `/backtesting/strategies`
Strategy implementations for testing.

### `/backtesting/utils`
Utility functions for backtesting.

### `/backtesting/scripts`
Execution scripts for running backtests.

## Unified Backtesting Script

The `scripts/run_backtest.sh` script provides a single entry point for running various types of backtests:

```bash
./backtesting/scripts/run_backtest.sh --symbol BTCUSDT --interval 1h --days 30 --mode authentic
```

Options:
- `--symbol`: Trading symbol (e.g., BTCUSDT)
- `--interval`: Time interval (e.g., 1h, 4h, 1d)
- `--days`: Number of days to backtest
- `--start`/`--end`: Specific date range (overrides --days)
- `--mode`: Backtest mode (standard, authentic, full)
- `--strategy`: Trading strategy to use
- `--ec2`: Run on EC2 instead of locally

## Backtest Modes

The framework supports several backtest modes:

1. **Standard**: Basic backtest with simplified agent decision logic
2. **Authentic**: Realistic backtest using full agent framework with authentic market data
3. **Full**: Comprehensive backtest with all agent types and extended analysis

## Results Analysis

Backtest results are saved in the `results/backtests` directory and can be analyzed using the tools in the `analysis` directory:

```python
from backtesting.analysis.analyze_results import analyze_backtest
results = analyze_backtest("results/backtests/backtest_20250416_123456.json")
```
