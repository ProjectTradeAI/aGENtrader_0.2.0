# Backtest Fix Instructions

## Problem Summary

The `run_enhanced_backtest.py` script is trying to initialize `PaperTradingSystem` with parameters that it doesn't accept. In particular, it's trying to use:

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

But the actual `PaperTradingSystem` class only accepts these parameters:

```python
pts = PaperTradingSystem(
    data_dir="data/paper_trading",
    default_account_id="backtest",
    initial_balance=config['initial_balance']
)
```

## Direct Fix

To fix this issue directly, you need to edit `run_enhanced_backtest.py` and change the `PaperTradingSystem` initialization to match what it actually accepts.

1. Open the file:
```
cd /home/ec2-user/aGENtrader
nano run_enhanced_backtest.py
```

2. Find this code section (around line 57):
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

3. Replace it with:
```python
pts = PaperTradingSystem(
    data_dir="data/paper_trading",
    default_account_id="enhanced_backtest",
    initial_balance=config['initial_balance']
)

# Store the other parameters for use in trading logic
symbol = config['symbol']
trade_size_percent = config['trade_size_pct']
max_positions = config['max_positions']
take_profit_percent = config['take_profit_pct']
stop_loss_percent = config['stop_loss_pct']
enable_trailing_stop = config['enable_trailing_stop']
trailing_stop_percent = config['trailing_stop_pct']
```

4. Save the file and exit.

5. Test the modified script:
```
cd /home/ec2-user/aGENtrader
python3 run_enhanced_backtest.py
```

## Using the Simplified Backtest

Alternatively, you can use the simplified backtest script we've created, which demonstrates how to properly initialize `PaperTradingSystem`:

```
cd /home/ec2-user/aGENtrader
python3 run_simplified_enhanced_backtest.py
```

This script generates simulated results and saves them to a file, demonstrating the correct approach to initializing `PaperTradingSystem`.

## Long-term Solution

For a more complete solution, consider:

1. Adding default values for all parameters to avoid KeyErrors.
2. Creating a wrapper class that handles the additional parameters for trading logic.
3. Ensuring consistent parameter naming across all scripts.
4. Adding better error checking and validation.
