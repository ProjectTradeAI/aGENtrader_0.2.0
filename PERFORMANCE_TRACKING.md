# Performance Tracking System in aGENtrader v2

This document describes the performance tracking system implemented in aGENtrader v2 to monitor and analyze trading decisions and their outcomes.

## Overview

The performance tracking system provides:

1. Real-time monitoring of trading decisions
2. Win/loss rate calculation
3. Agent contribution analysis
4. Performance metrics and statistics
5. Persistent storage of decision data for later analysis

## Components

### PerformanceTracker

The main class responsible for tracking trading performance. It's implemented in `analytics/performance_tracker.py` and provides the following functionality:

- Recording trading decisions with agent contributions
- Tracking active trades
- Calculating performance metrics
- Updating performance when prices change
- Generating system-wide performance stats

### Integration Points

The performance tracker is fully integrated with the trading system:

1. **Initialization**: The tracker is initialized in the main function of `run.py`
2. **Decision Recording**: All trading decisions from the DecisionAgent are recorded
3. **Performance Updates**: Active trades are updated as market conditions change
4. **Agent Contribution Analysis**: Each agent's contribution to successful/unsuccessful trades is tracked

## Data Storage

Performance data is stored in two primary locations:

1. **Logs**: Human-readable performance logs are stored in `logs/performance_summary.logl`
2. **Datasets**: Machine-readable performance data is stored in `datasets/performance_dataset.jsonl` for later analysis

## Example Usage

### Initializing the Tracker

```python
from analytics.performance_tracker import PerformanceTracker

# Initialize with default log/dataset directories
performance_tracker = PerformanceTracker()

# Or specify custom directories
performance_tracker = PerformanceTracker(log_dir="custom_logs", datasets_dir="custom_datasets")
```

### Recording a Decision

```python
decision_data = {
    "symbol": "BTC/USDT",
    "interval": "1h",
    "price": 45000.0,
    "type": "BUY",
    "confidence": 85,
    "reason": "Strong bullish signals across multiple indicators",
    "agent_analyses": {
        "TechnicalAnalystAgent": {
            "signal": "BUY",
            "confidence": 90
        },
        "SentimentAnalystAgent": {
            "signal": "BUY",
            "confidence": 80
        }
        # ... other agents
    }
}

trade_id = performance_tracker.record_decision(decision_data)
```

### Updating Performance Metrics

```python
# Update performance of all active trades with automatic closing after 60 minutes
performance_tracker.update_performance(market_data_provider, max_hold_time=60)

# Or manually close a specific trade
performance_tracker.manually_close_trade(trade_id, market_data_provider)
```

### Getting System Metrics

```python
# Get overall system performance metrics
metrics = performance_tracker.get_system_metrics()

# Log system metrics to performance log
performance_tracker.log_system_metrics()
```

## Configuration

The performance tracker uses the following environment variables (configured in `.env`):

- `SYSTEM_VERSION`: Version tag for the trading system
- `MAX_HOLD_TIME_MINUTES`: Maximum holding time for automatic trade closing
- `LOG_DIR`: Directory for logging files
- `DATASETS_DIR`: Directory for dataset storage

## Future Enhancements

Planned enhancements to the performance tracking system include:

1. **Advanced Analytics**: More detailed statistical analysis of trading patterns
2. **Visualization**: Real-time dashboards for monitoring performance
3. **Feedback Loop**: Using performance data to adjust agent weights
4. **Machine Learning**: Training models on historical decision data