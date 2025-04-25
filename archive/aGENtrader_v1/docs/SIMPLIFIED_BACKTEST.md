# Simplified Backtesting Implementation

## Overview

The simplified backtesting system provides a lightweight alternative to the full agent-based decision making framework for evaluating trading strategies. This approach allows users to:

1. Test trading strategies using either real market data from the database or generated synthetic data
2. Evaluate various risk parameters and position sizing strategies
3. Compare performance across different parameter sets
4. Operate without relying on the full decision session infrastructure

## Implementation Details

### Key Components

The simplified backtesting system consists of several key components:

#### 1. PaperTradingAccount & PaperTradingSystem

The `agents/paper_trading.py` module provides a comprehensive simulation environment with the following features:

- Account management with balance tracking
- Position tracking with unrealized P&L calculation
- Trade execution and order history
- Risk management with take profit, stop loss, and trailing stop functionality
- JSON serialization for results storage

#### 2. Market Data Utilities

The `utils/market_data.py` module provides database access for historical market data:

- Retrieval of OHLCV data by symbol, interval, and time range
- Database connection management
- Synthetic data generation for testing without database

#### 3. RSI-Based Decision Generator

A simple RSI-based trading strategy is implemented that:

- Generates BUY signals when RSI is below 30 (oversold)
- Generates SELL signals when RSI is above 70 (overbought)
- Calculates confidence levels based on RSI distance from thresholds

#### 4. Configuration System

Trading parameters are defined in `backtesting_config.json`:

- Trading symbol and interval
- Date range for backtesting
- Initial account balance
- Risk parameters (take profit, stop loss, trailing stop)
- Position sizing settings

### Workflow

The backtesting process follows these steps:

1. Load configuration from JSON file
2. Initialize PaperTradingSystem with specified parameters
3. Obtain historical data (from database or synthetic)
4. Calculate technical indicators (RSI)
5. Iterate through historical data points
6. Generate trading decisions based on indicators
7. Execute trades in paper trading system
8. Track equity curve and portfolio performance
9. Calculate performance metrics
10. Save results to JSON file

### Risk Management Features

The system includes several risk management features:

- **Take Profit**: Automatically close profitable trades at specified price levels
- **Stop Loss**: Limit downside risk by closing trades at a specified loss percentage
- **Trailing Stop**: Protect profits by adjusting stop loss as price moves favorably
- **Position Sizing**: Limit exposure by controlling trade size as percentage of account

## Results

From the initial run of the simplified backtest, we observed the following results:

- Initial Balance: $10,000
- Final Balance: $10,376.48
- Total Return: 3.76%
- Max Drawdown: 0.46%
- Win Rate: 66.67% (10 winning trades out of 15 total trades)

### Parameter Comparison

The system automatically tested different parameter sets:

| Parameter Set | Return % | Max Drawdown % | Win Rate % | Trades |
|---------------|----------|----------------|------------|--------|
| Base Config   | 3.76%    | 0.46%          | 66.67%     | 15     |
| TP: 3%, SL: 2%| 4.06%    | 0.46%          | 66.67%     | 15     |
| TP: 8%, SL: 5%| 2.24%    | 0.46%          | 66.67%     | 9      |
| Size: 10%, Max Pos: 10 | 3.00% | 0.46%   | 66.67%     | 12     |
| Trailing Stop: 1.5% | 3.76% | 0.46%      | 66.67%     | 15     |

These results suggest that tighter take profit and stop loss levels (3% TP, 2% SL) produced better results for this particular market condition, likely due to the sideways price action in the period being tested.

## Using the System

### Basic Usage

To run a backtest with default parameters:

```bash
python run_simplified_backtest.py
```

### Customizing Parameters

1. Edit `backtesting_config.json` to set the desired parameters:

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "start_date": "2025-02-17T23:00:00",
  "end_date": "2025-03-24T19:00:00",
  "initial_balance": 10000.0,
  "trade_size_pct": 25.0,
  "max_positions": 4,
  "enable_trailing_stop": true,
  "trailing_stop_pct": 2.5,
  "take_profit_pct": 5.0,
  "stop_loss_pct": 3.0
}
```

2. Run the backtest script which will automatically test your base configuration along with variations.

### Output Files

Results are saved to the following locations:

- Detailed backtest results: `data/logs/backtests/simplified_backtest_results_[timestamp].json`
- Parameter comparison: `data/logs/backtests/parameter_comparison_[timestamp].json`
- Account state: `data/paper_trading/backtests/backtest_[timestamp].json`
- Log file: `data/logs/backtests/simplified_backtest_[timestamp].log`

## Future Enhancements

1. Add more technical indicators beyond RSI
2. Implement custom strategy plugins
3. Add visualization tools for equity curves and trade statistics
4. Integrate with the full agent decision-making framework 
5. Implement portfolio backtesting with multiple symbols
6. Add more sophisticated position sizing algorithms

## Comparison to Enhanced Backtest

While the simplified backtest uses a rules-based approach, the enhanced backtest implemented in `run_enhanced_backtest.py` integrates the full agent-based decision framework, including:

- GlobalMarketAnalyst for macro market data analysis
- LiquidityAnalyst for order book and futures data analysis
- Collaborative agent decision making through group chat

The enhanced system provides more sophisticated analysis but requires more computational resources and a full database setup.