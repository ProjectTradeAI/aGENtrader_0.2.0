# Backtest Parameter Issues - Solution

## The Problem

The backtest scripts were failing with errors like:
- `run_backtest_with_local_llm.py: error: unrecognized arguments: --position_size 50`
- `KeyError: 'symbol'`
- `KeyError: 'take_profit_pct'`
- `TypeError: __init__() got an unexpected keyword argument 'symbol'`

## Root Cause

After examining the code, we discovered a parameter mismatch. The `PaperTradingSystem` class only accepts three parameters:
- `data_dir` (default: "data/paper_trading")
- `default_account_id` (default: "default") 
- `initial_balance` (default: 10000.0)

However, the backtest scripts were trying to pass many additional parameters like `symbol`, `trade_size_percent`, `take_profit_percent`, etc. These are not valid parameters for `PaperTradingSystem.__init__()`.

## Solution

To fix this issue:

1. Initialize `PaperTradingSystem` with only the parameters it accepts:
   ```python
   pts = PaperTradingSystem(
       data_dir='data/paper_trading',
       default_account_id='backtest',
       initial_balance=args.initial_balance
   )
   ```

2. Handle the other parameters in your trading logic after initializing the system.

## How to Run Backtests

### Option 1: Use the ec2-backtest.sh script with direct Python command

```bash
./ec2-backtest.sh run "cd /home/ec2-user/aGENtrader && python3 run_simplified_backtest.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-02 --initial_balance 10000 --use_local_llm"
```

### Option 2: Update the EC2 Scripts

The EC2 backtest scripts (`run_enhanced_backtest.py`, `run_simplified_backtest.py`, etc.) need to be updated to initialize `PaperTradingSystem` correctly with only the parameters it accepts.

## Checking Agent Communications

To verify agent communications, use the `--show-agent-comms` flag with the `smart-backtest-runner.sh` script:

```bash
./smart-backtest-runner.sh --type simplified --start 2025-03-01 --end 2025-03-02 --show-agent-comms
```

This will log agent communications during the backtest.

## Long-term Recommendations

1. Update all backtest scripts to correctly initialize `PaperTradingSystem`
2. Implement consistent parameter naming across all scripts
3. Add better error handling and parameter validation
4. Consider extending `PaperTradingSystem` to handle additional parameters directly if needed
