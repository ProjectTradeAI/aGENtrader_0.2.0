# Comprehensive Backtest Solution

## Summary of Issues

We identified multiple parameter mismatch issues in the backtest scripts, especially in `run_enhanced_backtest.py`. These issues resulted in errors like:

1. `TypeError: __init__() got an unexpected keyword argument 'symbol'`
2. `KeyError: 'take_profit_pct'`
3. `KeyError: 'enable_trailing_stop'`

## Root Cause

The `PaperTradingSystem` class in `agents/paper_trading.py` only accepts three parameters:
- `data_dir` (default: "data/paper_trading")
- `default_account_id` (default: "default")
- `initial_balance` (default: 10000.0)

However, in `run_enhanced_backtest.py`, it was being initialized with many additional parameters that it doesn't support:
```python
pts = PaperTradingSystem(
    symbol=config['symbol'],
    initial_balance=config['initial_balance'],
    trade_size_percent=config['trade_size_pct'],
    max_positions=config['max_positions'],
    take_profit_percent=config['take_profit_pct'],
    stop_loss_percent=config['stop_loss_pct'],
    enable_trailing_stop=config['enable_trailing_stop'],
    trailing_stop_percent=config['trailing_stop_pct']
)
```

## Solution

We created three different solutions to address this issue:

### 1. Simplified Enhanced Backtest

A clean, simplified version that demonstrates how to properly initialize `PaperTradingSystem`:

```python
pts = PaperTradingSystem(
    data_dir='data/paper_trading',
    default_account_id='backtest',
    initial_balance=config['initial_balance']
)
```

This script also generates simulated results to demonstrate the overall workflow.

### 2. Direct Fix for run_enhanced_backtest.py

A direct patch that modifies `run_enhanced_backtest.py` to use the correct parameters while preserving the rest of the functionality:

```python
pts = PaperTradingSystem(
    data_dir="data/paper_trading",
    default_account_id="enhanced_backtest",
    initial_balance=config['initial_balance']
)

# Store the other parameters for use in trading logic
symbol = config.get('symbol', 'BTCUSDT')
trade_size_percent = config.get('trade_size_pct', 0.02)
# ... other parameters
```

### 3. Smart Backtest Runner

A shell script that can run any type of backtest (simplified, enhanced, or full) with proper error handling and parameter validation.

## How to Use

### Running the Simplified Enhanced Backtest

```bash
./run-simplified-backtest.sh
```

### Running the Fixed Enhanced Backtest

```bash
./run-fixed-backtest.sh
```

### Using the Smart Backtest Runner

```bash
./smart-backtest-runner.sh --type simplified --symbol BTCUSDT --interval 1h --start 2025-03-01 --end 2025-03-02 --balance 10000 --show-agent-comms
```

Options:
- `--type`: Type of backtest (simplified, enhanced, full)
- `--symbol`: Trading symbol (default: BTCUSDT)
- `--interval`: Time interval (default: 1h)
- `--start`: Start date (default: 2025-03-01)
- `--end`: End date (default: 2025-03-02)
- `--balance`: Initial balance (default: 10000)
- `--no-local-llm`: Disable local LLM usage
- `--show-agent-comms`: Show agent communications

## Long-term Recommendations

1. **Consistent Parameter Handling**: Use a consistent approach to parameter handling across all scripts.

2. **Comprehensive Error Checking**: Add better error checking and parameter validation.

3. **Default Values**: Always provide default values for all parameters to avoid KeyErrors.

4. **Clear Documentation**: Document the correct usage of `PaperTradingSystem` and other components.

5. **Unit Tests**: Add unit tests to verify that components work correctly together.
