# Multi-Agent Trading System Comparison Framework

This document describes the framework for comparing the performance of different agent decision-making approaches in the trading system.

## Overview

The trading system supports multiple decision-making approaches, from simple technical indicator-based strategies to sophisticated multi-agent collaborative decision frameworks. The Agent Comparison Framework allows side-by-side performance comparison of these different approaches using identical market data and trading parameters.

## Comparison Framework Components

### 1. TradingSimulator

The `TradingSimulator` class provides a unified interface for backtesting different session types:

- Handles market data processing
- Creates appropriate decision session instances
- Executes trading decisions based on session output
- Tracks portfolio performance and trade history
- Calculates comparable performance metrics

### 2. Decision Session Types

The framework currently supports two primary decision session types:

#### Simple Decision Session
- Uses a streamlined, rule-based approach
- Evaluates technical indicators with pre-defined thresholds
- Makes decisions based on indicator alignment
- Faster execution with lower computational requirements
- Optimized for specific market conditions

#### Multi-Agent Decision Session
- Uses a collaborative, multi-agent system
- Employs specialized agents for different analysis aspects:
  - Market Analyst (technical analysis)
  - Risk Manager (risk assessment)
  - Trading Strategist (strategy selection)
  - Trading Advisor (final decision synthesis)
  - *Optional*: Global Market Analyst (macro context)
  - *Optional*: Liquidity Analyst (market microstructure)
- Makes decisions through agent discussion and consensus
- Provides more comprehensive analysis and reasoning
- Adaptable to a wider range of market conditions

### 3. Performance Metrics

The framework calculates a comprehensive set of performance metrics for comparison:

- **Return Metrics**:
  - Total Return (%)
  - Net Profit ($)
  - Annualized Return (%)

- **Trade Metrics**:
  - Win Rate (%)
  - Total Trades
  - Winning/Losing Trades
  - Average Win/Loss (%)
  - Profit Factor

- **Risk Metrics**:
  - Maximum Drawdown (%)
  - Volatility
  - Sharpe Ratio
  - Sortino Ratio
  - Calmar Ratio

## Using the Comparison Framework

### Running Comparisons

The `run_agent_comparison.sh` script provides a convenient interface for running comparisons:

```bash
# Run a standard comparison (7 days, both session types)
./run_agent_comparison.sh

# Run a short comparison (3 days, max 3 trades)
./run_agent_comparison.sh --short

# Compare with specific parameters
./run_agent_comparison.sh --symbol=BTCUSDT --days=10 --interval=4h --confidence=60

# Run only the multi-agent decision session
./run_agent_comparison.sh --multi-only

# Run only the simple decision session
./run_agent_comparison.sh --simple-only

# Run with a specific date range
./run_agent_comparison.sh --start=2025-02-01 --end=2025-02-28
```

### Output and Analysis

The comparison framework generates structured output for analysis:

1. **JSON Results File**: Complete performance data and trade history
2. **Console Summary**: Side-by-side comparison of key metrics
3. **Performance Database**: (Optional) Results stored in a database for trend analysis

## Benefits of Comparison

The comparison framework provides several key benefits:

1. **Objective Performance Assessment**: Directly compares different decision approaches using identical data and parameters.

2. **Resource Optimization**: Helps determine when to use simpler approaches (saving API costs) vs. when to use more sophisticated multi-agent systems.

3. **Strategic Insights**: Identifies market conditions where each approach performs better.

4. **Continuous Improvement**: Provides a benchmark for measuring the impact of system improvements.

5. **Cost-Benefit Analysis**: Allows evaluation of the additional value provided by more complex and costly multi-agent approaches.

## EC2 Integration

The comparison framework can be run on AWS EC2 for larger backtests:

```bash
# Deploy and run comparison on EC2
./deploy-and-run-ec2-test.sh --script=run_agent_comparison.sh --args="--days=30 --interval=1h"
```

## Case Study: February 2025 Backtest

A comprehensive backtest comparing the simple and multi-agent decision sessions for February 2025 revealed:

- **Simple Session**: 5 trades, 60% win rate, 15.3% return
- **Multi-Agent Session**: 4 trades, 75% win rate, 23.7% return

The multi-agent system showed a 55% improvement in overall return, primarily due to:
1. Better entry timing based on liquidity analysis
2. More effective risk management during volatile periods
3. Superior market condition classification