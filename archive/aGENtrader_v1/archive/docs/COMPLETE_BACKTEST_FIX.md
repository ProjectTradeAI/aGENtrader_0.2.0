# Complete Backtest Fix

## The Problem

We had several parameter mismatches in the backtest scripts:

1. `run_backtest_with_local_llm.py: error: unrecognized arguments: --position_size 50`
2. `KeyError: 'symbol'`
3. `KeyError: 'take_profit_pct'`
4. `TypeError: __init__() got an unexpected keyword argument 'symbol'`
5. `KeyError: 'enable_trailing_stop'`

## Root Cause Analysis

There were two main issues:

1. **PaperTradingSystem initialization**: The script was trying to pass parameters like `symbol` directly to the PaperTradingSystem constructor, but it only accepts three parameters:
   - `data_dir` (default: "data/paper_trading")
   - `default_account_id` (default: "default")
   - `initial_balance` (default: 10000.0)

2. **Missing configuration parameters**: The configuration file was missing required keys that were used in the script, including:
   - `enable_trailing_stop`
   - `trailing_stop_pct`
   - and others

## Solution

We created a complete configuration file with ALL required parameters:

```json
{
  "api_key": "none",
  "output_dir": "results",
  "log_dir": "data/logs",
  "symbol": "BTCUSDT",
  "interval": "1h",
  "start_date": "2025-03-01",
  "end_date": "2025-03-07",
  "initial_balance": 10000.0,
  "risk_per_trade": 0.02,
  "trade_size_pct": 0.02,
  "max_positions": 1,
  "stop_loss_pct": 5.0,
  "take_profit_pct": 10.0,
  "enable_trailing_stop": false,
  "trailing_stop_pct": 2.0,
  "local_llm": {
    "enabled": true,
    "model_path": "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
    "max_tokens": 4096,
    "temperature": 0.7,
    "timeout": 300
  },
  "openai": {
    "model": "gpt-4",
    "temperature": 0.7,
    "timeout": 180
  },
  "logging": {
    "level": "DEBUG",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "debug": true,
  "verbose": true
}
```

This configuration provides values for all parameters that the script might try to use.

## How to Run

To run the enhanced backtest with this complete configuration:

```bash
./run-fixed-enhanced-backtest.sh
```

This will use the configuration file directly without passing additional command-line parameters.

## Long-term Recommendations

1. **Use default values for all parameters**: Modify the script to provide default values for any parameters that might be missing in the configuration.

2. **Consistent parameter naming**: Ensure consistent parameter naming across different scripts.

3. **Better error handling**: Add better error checking and parameter validation.

4. **Complete documentation**: Document all required parameters for each script.
