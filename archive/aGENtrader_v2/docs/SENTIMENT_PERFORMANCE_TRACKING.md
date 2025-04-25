# Sentiment Analysis Performance Tracking

This document describes how the sentiment analysis is integrated with the performance tracking system in aGENtrader v2.

## Overview

The SentimentAnalystAgent provides trading signals based on market sentiment, and the TradePerformanceTracker evaluates how these signals perform over time. This integration allows for:

1. Tracking the accuracy of sentiment-based signals
2. Comparing sentiment signal performance against other agents
3. Analyzing how different sentiment states correlate with trade outcomes
4. Finding the optimal weight for sentiment in the decision-making process

## Integration Points

### Agent Contribution in Decision Making

The SentimentAnalystAgent's recommendations are included in the weighted decision-making process with a default weight of 0.8. This means sentiment analysis is considered important but slightly less influential than technical analysis (which has a default weight of 1.2).

```python
# Decision Agent agent_weights default configuration
self.agent_weights = {
    "LiquidityAnalystAgent": 1.0,
    "TechnicalAnalystAgent": 1.2,
    "SentimentAnalystAgent": 0.8
}
```

### Trade Performance Tracking

When a trade is executed, the agent's contribution is recorded in the trade object:

```json
"agent_contributions": {
  "SentimentAnalystAgent": {
    "action": "BUY",
    "confidence": 75,
    "weight": 0.8,
    "weighted_confidence": 60.0
  },
  "TechnicalAnalystAgent": {
    "action": "BUY",
    "confidence": 65,
    "weight": 1.2,
    "weighted_confidence": 78.0
  }
}
```

The TradePerformanceTracker analyzes this data to generate agent-specific metrics:

```json
"agent_metrics": {
  "SentimentAnalystAgent": {
    "total_trades": 42,
    "winning_trades": 25,
    "average_confidence": 71.3,
    "average_weight": 0.8,
    "action_alignment": 34,
    "average_return_when_followed": 2.8,
    "average_return_when_not_followed": -1.2
  }
}
```

## Sentiment Performance Metrics

The performance reporting includes these sentiment-specific metrics:

| Metric | Description |
|--------|-------------|
| **Win Rate by Sentiment** | Percentage of winning trades for each sentiment state (Bullish, Neutral, Bearish) |
| **Average Return by Sentiment** | Average percentage return for trades made during each sentiment state |
| **Signal Alignment** | How often the final decision aligned with the sentiment signal |
| **Average Return When Followed** | Average return when the final decision followed the sentiment recommendation |
| **Average Confidence** | Average confidence score provided by the sentiment agent |

## Performance Reporting

The main view_performance.py utility displays agent contribution metrics including SentimentAnalystAgent's performance. The test_sentiment_performance.py script demonstrates this integration with sample data.

Example output:

```
===== AGENT CONTRIBUTION SUMMARY =====

SentimentAnalystAgent:
  Total Trades: 15
  Winning Trades: 9
  Win Rate: 60.0%
  Average Confidence: 77.5
  Average Weight: 0.8
  Actions:
    BUY: 4
    SELL: 4
    HOLD: 7
  Signal Alignment: 80.0%
  Avg Return When Followed: 2.50%
  Avg Return When Not Followed: -1.20%

===== PERFORMANCE BY SENTIMENT =====

Bullish Sentiment:
  Trades: 4
  Win Rate: 75.0%
  Average Return: 3.37%

Neutral Sentiment:
  Trades: 7
  Win Rate: 71.4%
  Average Return: 0.89%

Bearish Sentiment:
  Trades: 4
  Win Rate: 25.0%
  Average Return: -1.66%
```

## Interpreting the Results

The performance metrics can be used to:

1. **Adjust agent weights**: If sentiment consistently provides better signals, its weight can be increased
2. **Refine sentiment thresholds**: Tune confidence thresholds based on how well different sentiment states perform
3. **Optimize the sentiment configuration**: Adjust settings like confidence_map based on performance data
4. **Evaluate sentiment data sources**: When multiple sources are integrated, compare their predictive power

## Implementation Details

The key files involved in this integration are:

- **sentiment_analyst_agent.py**: Provides sentiment analysis and trading signals
- **trade_performance_tracker.py**: Calculates and tracks agent contribution metrics
- **decision_agent.py**: Incorporates sentiment into the weighted decision process
- **test_sentiment_performance.py**: Script to demonstrate and test the integration

## Future Enhancements

Planned improvements to the sentiment-performance integration:

1. **Sentiment Decay Model**: Track how sentiment signals perform over different time horizons
2. **Multi-Source Analysis**: Compare performance of different sentiment data sources
3. **Market Regime Detection**: Identify market regimes where sentiment is most predictive
4. **Dynamic Weight Adjustment**: Automatically adjust the sentiment weight based on recent performance
5. **Sentiment Pattern Recognition**: Detect patterns in sentiment changes that precede significant price movements