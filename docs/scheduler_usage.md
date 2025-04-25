# aGENtrader DecisionTriggerScheduler

## Overview

The DecisionTriggerScheduler provides a flexible way to trigger trading decisions at precise intervals, with optional alignment to clock boundaries. This document explains how to use and configure the scheduler in your trading applications.

## Basic Usage

```python
from aGENtrader_v2.core.trigger_scheduler import DecisionTriggerScheduler

# Initialize a scheduler that triggers every hour, aligned to clock boundaries
scheduler = DecisionTriggerScheduler(
    interval="1h",
    align_to_clock=True,
    log_file="logs/my_triggers.jsonl"
)

# In your trading loop:
while running:
    # Your trading code here...
    
    # Wait until the next scheduled time
    trigger_time, wait_duration = scheduler.wait_for_next_tick()
    
    # Trigger_time contains the actual time the scheduler triggered
    print(f"Triggered at {trigger_time}, waited {wait_duration} seconds")
```

## Configuration Options

The scheduler can be configured with the following parameters:

- **interval**: Specifies how often triggers should occur. Supported formats:
  - Minutes: "1m", "5m", "15m", "30m"
  - Hours: "1h", "2h", "4h", "12h"
  - Days: "1d", "2d", "7d"

- **align_to_clock**: When true, triggers will align to clock boundaries:
  - For minute intervals: xx:00, xx:15, xx:30, xx:45 (for "15m")
  - For hour intervals: 08:00, 09:00, 10:00 (for "1h")
  - For day intervals: 00:00 each day

- **log_file**: Path to a JSONL file where trigger timing information will be logged. Set to None to disable logging.

## Command-Line Integration

The scheduler can be controlled through command-line arguments in your application:

```python
parser.add_argument('--interval', type=str, default='1h',
                  help='Trading interval (e.g., 1m, 5m, 15m, 1h, 4h, 1d)')
                  
parser.add_argument('--align-clock', type=str, default='true', choices=['true', 'false'],
                  help='Align trading cycles to clock boundaries')
```

## Timing Log Format

When logging is enabled, the scheduler creates a JSONL file with detailed timing information for each trigger:

```json
{
  "cycle": 1,
  "timestamp": "2025-04-23T14:30:00.123456Z",
  "scheduled": "2025-04-23T14:30:00.000000Z",
  "actual": "2025-04-23T14:30:00.123456Z",
  "delay_seconds": 0.123456,
  "wait_seconds": 60.0,
  "interval": "1m",
  "aligned": true
}
```

This data can be used for:
- Monitoring timing accuracy
- Analyzing system performance
- Debugging scheduling issues

## Best Practices

1. **Clock Alignment**: Use `align_to_clock=True` for production systems to ensure consistent timing.
2. **Error Handling**: Always handle exceptions that may occur during wait_for_next_tick().
3. **Log Rotation**: For long-running systems, implement log rotation for trigger logs.
4. **Performance Monitoring**: Regularly check the delay_seconds in logs to ensure timing accuracy.

## Advanced Usage

### Getting Scheduler Statistics

```python
stats = scheduler.get_stats()
print(f"Cycles completed: {stats['cycle_count']}")
print(f"Next trigger at: {stats['next_trigger']}")
```

### Testing with Accelerated Time

For testing, you can use shorter intervals:

```python
# Test mode with 4x acceleration
test_interval = f"{max(1, int(parse_interval(interval) / 4))}{interval[-1]}"
test_scheduler = DecisionTriggerScheduler(interval=test_interval)
```

This allows testing trading logic without waiting for full intervals.