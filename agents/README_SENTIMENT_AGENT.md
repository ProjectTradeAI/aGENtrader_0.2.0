# SentimentAnalystAgent Documentation

The `SentimentAnalystAgent` is a specialized analyst agent that analyzes market sentiment for crypto assets and provides trading signals based on that sentiment data.

## Overview

The SentimentAnalystAgent:
- Analyzes market sentiment (Bullish / Neutral / Bearish)
- Returns a confidence-weighted signal (BUY / SELL / HOLD)
- Provides insights from various sentiment sources
- Logs sentiment data for future analysis
- Can be configured to use different data modes

## Configuration

The agent can be configured in `settings.yaml` under the `sentiment_analyst` section:

```yaml
sentiment_analyst:
  enabled: true
  data_mode: mock  # or api or scrape
  api_source: lunarcrush  # placeholder for future API integration
  confidence_threshold: 65
  confidence_map:
    Bullish: 0.7
    Neutral: 0.5
    Bearish: 0.6
```

### Configuration Options:

- **enabled**: Enable or disable the agent (true/false)
- **data_mode**: Source of sentiment data
  - `mock`: Generate simulated sentiment data for testing
  - `api`: Use external sentiment API (when implemented)
  - `scrape`: Use web scraping sources (when implemented)
- **api_source**: Specific API source to use when data_mode is "api"
- **confidence_threshold**: Minimum confidence level for actionable signals
- **confidence_map**: Mapping of sentiment states to base confidence levels

## Integration with the Trading System

The SentimentAnalystAgent is integrated with:

1. **Core Orchestrator**: Initializes and coordinates the agent's analysis
2. **Decision Agent**: Uses sentiment signals weighted at 0.8 by default
3. **Trade Performance Tracker**: Tracks the agent's contribution to trading decisions

## Usage Examples

### Running Standalone

You can test the SentimentAnalystAgent directly using the `test_sentiment_agent.py` script:

```bash
# Test with random sentiment
python test_sentiment_agent.py --mode random --symbol BTCUSDT --interval 1h

# Test with fixed bullish sentiment
python test_sentiment_agent.py --mode bullish --symbol BTCUSDT --interval 1h

# Test with default rotating sentiment
python test_sentiment_agent.py --symbol BTCUSDT --interval 1h --count 5
```

### Using with the Full Pipeline

The SentimentAnalystAgent is automatically included in the standard analysis pipeline:

```bash
# Run the full analysis pipeline including sentiment analysis
python test_v2_pipeline.py
```

## Data Structure

### Analysis Output

The agent's analysis output follows this structure:

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "timestamp": "2025-04-18T20:07:43.039725",
  "sentiment_source": "mock",
  "sentiment_data": {
    "sources": { ... }
  },
  "analysis": {
    "sentiment": "Bullish",
    "action": "BUY",
    "confidence": 65,
    "reason": "Based on positive social media sentiment",
    "insights": [
      "Twitter sentiment: Bullish with volume 3955",
      "News sentiment: Bullish with 11 articles",
      "Fear & Greed Index: 32 (Fear)"
    ]
  }
}
```

## Future Enhancements

The SentimentAnalystAgent is designed for future expansion:

1. **Real API Integration**: Support for LunarCrush, Santiment, or other sentiment APIs
2. **Web Scraping**: Implementation of Reddit, Twitter, or news scraping
3. **Historical Analysis**: Deeper analysis of sentiment trends over time
4. **Customizable Sources**: Allow configuring which sentiment sources to prioritize
5. **LLM Integration**: Leverage LLMs for richer sentiment analysis of news and social media
6. **Multi-Asset Correlation**: Compare sentiment across related assets

## Troubleshooting

### Common Issues

- **Missing Action in Decision**: If the agent's action doesn't appear in the final decision, check that confidence exceeds the threshold
- **Inconsistent Sentiment**: The mock data mode can produce varying results by design to simulate real-world conditions
- **Low Confidence Scores**: The base confidence for each sentiment state can be adjusted in the configuration

### Logging

The agent logs its activity to the main application log:

```
sentiment_analyst - INFO - Starting sentiment analysis for BTCUSDT at 1h interval
sentiment_analyst - INFO - Sentiment analysis completed for BTCUSDT: Bullish (Confidence: 65)
```

It also maintains a sentiment history log at `logs/sentiment_feed.jsonl`.