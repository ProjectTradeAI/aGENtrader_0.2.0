# Grok API Sentiment Integration

This document describes the integration of Grok AI for sentiment analysis in the aGENtrader v2 system.

## Overview

The `SentimentAggregatorAgent` leverages the Grok API to retrieve AI-powered sentiment analysis for cryptocurrencies. This provides aGENtrader with authentic, model-generated sentiment data that can be used to enhance trading decisions.

## Implementation Details

### API Integration

The implementation uses Grok's official API endpoint:
- Endpoint: `https://api.x.ai/v1/chat/completions`
- Model: `grok-3-latest`
- Authentication: Bearer token using `XAI_API_KEY` environment variable

### Key Components

1. **SentimentAggregatorAgent** (`aGENtrader_v2/agents/sentiment_aggregator_agent.py`)
   - Extends the BaseAnalystAgent class
   - Manages API connections and request formatting
   - Processes and structures sentiment responses
   - Logs all sentiment data to the sentiment feed file

2. **Runner Script** (`run_sentiment_aggregator.py`)
   - Command-line interface for the SentimentAggregatorAgent
   - Supports querying sentiment for specific dates or date ranges
   - Allows for historical sentiment analysis with configurable intervals
   - Provides formatted output and optional saving of results

### Data Structure

The sentiment data is structured as follows:

```json
{
  "symbol": "BTC",
  "date": "2025-04-22",
  "timestamp": "2025-04-22T21:55:59.222485",
  "source": "Grok API",
  "sentiment_data": {
    "sentiment_score": 0.7,         // Score from -1 (bearish) to +1 (bullish)
    "confidence": 85,               // Confidence level (0-100)
    "reasoning": "Detailed analysis explaining the sentiment...",
    "dominant_topics": [            // Key topics driving sentiment
      "post-halving rally",
      "institutional adoption",
      "price predictions",
      "regulatory concerns"
    ]
  },
  "analysis": {
    "sentiment": "BULLISH",         // Mapped sentiment state (BULLISH, NEUTRAL, BEARISH)
    "confidence": 85,
    "reason": "Same as reasoning above",
    "topics": ["Same as dominant_topics above"],
    "score": 0.7
  }
}
```

### Sentiment Mapping

Sentiment scores from Grok API are mapped to sentiment states according to these rules:
- Score ≥ 0.3: BULLISH
- Score ≤ -0.3: BEARISH
- -0.3 < Score < 0.3: NEUTRAL

## Integration Points

### Logs Integration

All sentiment data is appended to the existing sentiment feed log file:
```
aGENtrader_v2/logs/sentiment_feed.jsonl
```

The sentiment feed file combines data from various sources, including both the original SentimentAnalystAgent and the new SentimentAggregatorAgent. Each entry includes a `source` field to identify where the data came from.

### Usage with Existing Components

1. **Standalone Usage**:
   ```bash
   ./run_sentiment_aggregator.py --symbol BTC --date 2025-04-22
   ```

2. **Historical Analysis**:
   ```bash
   ./run_sentiment_aggregator.py --symbol BTC --historical --start_date 2025-04-01 --end_date 2025-04-15
   ```

3. **Integration with SentimentAnalystAgent**:
   The SentimentAnalystAgent can be extended to read and incorporate data from the Grok API by:
   - Adding a new data source option (e.g., `grok_api`)
   - Reading from the sentiment feed file where Grok API data is stored
   - Integrating the sentiment scores and insights into its analysis

## Future Enhancements

1. **Sentiment Comparison**: Add functionality to compare sentiment across different sources (e.g., Grok API vs. LunarCrush)
2. **Multi-Asset Correlation**: Analyze sentiment correlations between related cryptocurrencies
3. **Topic Tracking**: Track the evolution of dominant topics over time
4. **Sentiment Decay Model**: Implement a model to account for how sentiment impact decays over time
5. **Custom Prompting**: Allow for customized prompting to focus on specific aspects of sentiment
6. **Batched Historical Analysis**: Optimize historical queries with batching and rate limiting

## API Key Management

The integration requires a valid Grok API key stored in the `XAI_API_KEY` environment variable. This key should be:
- Kept secure and never exposed in code or logs
- Managed through the Replit Secrets mechanism or similar secure storage
- Monitored for API usage and rate limits

## Usage Examples

### Basic Sentiment Query

```python
from aGENtrader_v2.agents.sentiment_aggregator_agent import SentimentAggregatorAgent

# Initialize the agent
agent = SentimentAggregatorAgent()

# Get current sentiment for Bitcoin
btc_sentiment = agent.analyze("BTC")

# Get sentiment for Ethereum from 30 days ago
eth_sentiment = agent.analyze("ETH", lookback_days=30)

# Print the sentiment state and confidence
print(f"BTC Sentiment: {btc_sentiment['analysis']['sentiment']} (Confidence: {btc_sentiment['analysis']['confidence']}%)")
```

### Historical Sentiment Analysis

```python
# Get historical sentiment for a date range
historical_sentiment = agent.analyze_historical_sentiment(
    "BTC",
    start_date="2025-01-01",
    end_date="2025-01-31",
    interval_days=7
)

# Process and analyze trends
for entry in historical_sentiment:
    print(f"{entry['date']}: {entry['analysis']['sentiment']} (Score: {entry['analysis']['score']})")
```