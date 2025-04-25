# Authentic Backtesting Framework

## Overview

The Authentic Backtesting Framework provides a genuine way to backtest trading strategies using real trading system components with historical market data. Unlike simulation-based backtesting that uses hard-coded agent responses, this framework uses the actual trading agents and enforces proper data integrity measures.

## Key Features

- **Real Components**: Uses the actual trading system components (DecisionSession, agents) rather than simulations
- **Database Integration**: Retrieves authentic historical market data from the PostgreSQL database
- **Data Integrity**: Ensures analysts explicitly state when they don't have access to real data
- **Comprehensive Analysis**: Generates performance metrics and visualizations
- **Dual Deployment**: Can run both locally and on EC2

## Directory Structure

```
backtesting/
├── analysis/                # Analysis tools for backtest results
│   ├── analyze_backtest_performance.py
│   ├── analyze_backtest_results.py
│   └── visualize_backtest.py
├── core/                    # Core backtesting functionality
│   ├── authentic_backtest.py
│   └── simplified_working_backtest.py
├── scripts/                 # Utility scripts for running backtests
│   └── run_authentic_backtest.sh
└── utils/                   # Utilities for data retrieval and validation
    ├── data_integrity_checker.py
    └── market_data.py
```

## How It Works

1. **Market Data Retrieval**: The framework connects to the PostgreSQL database to retrieve historical market data for the specified symbol, interval, and date range.

2. **Trading System Integration**: It imports and initializes the actual trading system components, including the DecisionSession class and trading agents.

3. **Data Integrity Enforcement**: Data integrity measures are applied to ensure agents accurately disclose when they don't have access to real data.

4. **Authentic Backtesting**: The framework runs the trading system on historical data, capturing trades, equity changes, and agent decisions.

5. **Result Analysis**: Performance metrics are calculated and visualizations are generated to help evaluate the strategy.

## Usage

### Running a Backtest Locally

```bash
./backtesting/scripts/run_authentic_backtest.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10
```

### Running a Backtest on EC2

```bash
./backtesting/scripts/run_authentic_backtest.sh --symbol BTCUSDT --interval 1h --start 2025-04-01 --end 2025-04-10 --ec2
```

### Available Options

- `--symbol`: Trading symbol (default: BTCUSDT)
- `--interval`: Time interval (1m, 5m, 15m, 1h, 4h, 1d) (default: 1h)
- `--start`: Start date in YYYY-MM-DD format (default: 7 days ago)
- `--end`: End date in YYYY-MM-DD format (default: today)
- `--balance`: Initial balance for backtest (default: 10000)
- `--ec2`: Run the backtest on EC2 instead of locally
- `--verbose`: Show verbose output

## Deployment to EC2

To deploy the authentic backtesting framework to EC2:

```bash
./deploy-authentic-backtest.sh
```

This script:
1. Creates the necessary directory structure on EC2
2. Packages and uploads the backtesting framework
3. Extracts the package on EC2
4. Performs a simple test to verify deployment

## Verification

To verify that the authentic backtesting framework is working properly:

```bash
./verify-authentic-backtest.sh
```

This script:
1. Checks the database connection
2. Tests the market data utilities
3. Verifies data integrity utilities
4. Runs a short test backtest
5. Visualizes the results

## Technical Considerations

### Database Requirements

- The framework requires a PostgreSQL database with market data tables (klines_1m, klines_5m, etc.)
- The DATABASE_URL environment variable must be properly set

### EC2 Requirements

- The EC2_PUBLIC_IP environment variable must be set with the EC2 instance's public IP
- An SSH key must be provided via the EC2_SSH_KEY or EC2_PRIVATE_KEY environment variable

### Dependencies

- Python libraries: pandas, numpy, matplotlib, psycopg2
- Trading system components must be properly installed and importable

## Data Integrity

The authentic backtesting framework ensures data integrity by:

1. Applying data integrity wrappers to trading agents
2. Verifying data availability before executing trades
3. Ensuring that agents explicitly state when they don't have access to real data
4. Using real database connections for market data

This approach prevents simulation-based biases and ensures that backtest results more accurately reflect how the system would perform in real-world conditions.

## Differences from Previous Simulation-Based Approaches

Previous backtesting approaches had several limitations:

1. **Hardcoded Responses**: Agent responses were often hardcoded, leading to identical outputs regardless of the time period or market conditions.

2. **No Real Components**: They didn't use the actual trading system components, but rather simulated their behavior.

3. **Fake Data**: They sometimes used synthetic or simulated market data instead of authentic historical data.

4. **No Data Integrity**: They lacked mechanisms to ensure agents disclosed when they didn't have access to real data.

The new authentic backtesting framework addresses these issues by using real components, real data, and proper data integrity measures.