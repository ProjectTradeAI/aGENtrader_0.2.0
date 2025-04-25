# Backtest Parameter Issue - Simple Solution

## The Problem

There was a mismatch between the parameters in the configuration and the actual parameters expected by `PaperTradingSystem`. The error messages were:

1. `run_backtest_with_local_llm.py: error: unrecognized arguments: --position_size 50`
2. `KeyError: 'symbol'`
3. `KeyError: 'take_profit_pct'`
4. `TypeError: __init__() got an unexpected keyword argument 'symbol'`

## Root Cause

After examining the code, we found that `PaperTradingSystem` only accepts three parameters:
- `data_dir` (default: "data/paper_trading")
- `default_account_id` (default: "default") 
- `initial_balance` (default: 10000.0)

However, the backtesting scripts were trying to pass many additional parameters like `symbol`, `trade_size_percent`, etc.

## Solution

We created a simplified working backtest script (`run_working_backtest.py`) that correctly initializes `PaperTradingSystem` with only the parameters it accepts. This script successfully runs a backtest and generates results.

## How to Run

```bash
./run-working-backtest.sh BTCUSDT 1h 2025-03-01 2025-03-02 10000
```

## Long-term Recommendations

1. Update all backtest scripts to correctly initialize `PaperTradingSystem` with only the parameters it accepts
2. Consider extending `PaperTradingSystem` to handle the additional parameters needed for more sophisticated backtests
3. Use a consistent configuration format across all scripts
4. Add better error checking and parameter validation

## Next Steps

The current solution provides a working backtest. For full functionality:

1. Use the working backtest script as a template
2. Gradually add the trading logic and agent communications
3. Test incrementally to ensure each component works properly
