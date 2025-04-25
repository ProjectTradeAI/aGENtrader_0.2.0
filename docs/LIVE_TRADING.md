# aGENtrader v2 Live Trading System

This document provides technical information about the live trading system in aGENtrader v2, including the new precision scheduling system.

## Overview

The aGENtrader v2 Live Trading System runs trading cycles at precise intervals, with configurable parameters for trading frequency and alignment. It integrates multiple specialized agents to make trading decisions based on technical analysis, sentiment, and market conditions.

## Precision Scheduler

The system uses the `DecisionTriggerScheduler` to manage trading cycles with precise timing:

### Key Features

- **Clock Alignment**: When enabled, trading cycles will align to clock boundaries (e.g., exactly at 08:00, 09:00 for hourly intervals)
- **Flexible Intervals**: Supports various time intervals (1m, 5m, 15m, 1h, 4h, 1d)
- **Detailed Logging**: Records precise timing information about each trading cycle
- **Resilient Execution**: Handles exceptions and provides fallback mechanisms

### Command-Line Options

The scheduler can be configured using command-line arguments:

```
--interval 1h         # Sets the trading interval (1m, 5m, 15m, 1h, 4h, 1d)
--align-clock true    # Enables clock alignment (true/false)
--log-triggers        # Enables detailed timing logs
```

### Example Usage

```bash
# Run with hourly intervals aligned to the clock
python run.py --mode live --interval 1h --align-clock true

# Test mode with 15-minute intervals, not aligned to clock boundaries
python run.py --mode test --interval 15m --align-clock false --duration 4h
```

## Trading Cycle Process

Each trading cycle follows this sequence:

1. **Data Collection**: Fetch current market data
2. **Analysis**: Run all analysis agents on the collected data
3. **Decision Making**: Make trading decisions based on analysis results
4. **Execution**: Execute trades if necessary
5. **Logging**: Record decisions and trades
6. **Scheduling**: Wait for the next scheduled cycle using the precision scheduler

## Logs and Monitoring

The system generates several log files to help with monitoring and debugging:

- **Main Log**: `logs/agentrader_YYYYMMDD_HHMMSS.log`
- **Trading Triggers**: `logs/trading_triggers.jsonl` (timing information for each cycle)
- **Test Triggers**: `logs/test_triggers.jsonl` (timing information for test mode)
- **Trading Decisions**: `logs/decisions/SYMBOL_decisions.jsonl` (all trading decisions)

## Test Mode

Test mode simulates live trading but with the following differences:

1. Runs for a fixed duration specified by `--duration`
2. Uses accelerated cycles (4x faster than the specified interval)
3. Simulates trade execution without actual trades
4. Records results to separate log files

## Internal Scheduler Implementation

The scheduler uses the following algorithm to determine when to trigger the next cycle:

1. For non-aligned mode: Simply add the interval to the current time
2. For aligned mode:
   - For minute intervals: Align to the next multiple of X minutes
   - For hour intervals: Align to the next multiple of X hours
   - For day intervals: Align to the start of the next day

The scheduler handles edge cases such as:
- Rolling over to the next hour or day when needed
- Preventing past-scheduled times
- Recovering from exceptions with emergency intervals

## Extending the System

To add new trigger mechanisms:

1. Extend the `DecisionTriggerScheduler` class
2. Override the `_calculate_next_trigger` method
3. Add appropriate CLI arguments in `main.py`