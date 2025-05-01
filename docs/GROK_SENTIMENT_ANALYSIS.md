# Grok Sentiment Analysis Integration for aGENtrader

This document describes the integration of xAI's Grok language model for market sentiment analysis in aGENtrader.

## Overview

The system uses the Grok API (provided by xAI) to analyze market-related text content (news, social media, etc.) to determine sentiment and generate trading signals. Grok models provide advanced natural language understanding capabilities that can identify subtle nuances in financial text.

## Requirements

- xAI API key (stored as `XAI_API_KEY` in environment variables)
- OpenAI Python package (`pip install openai`)

## Components

### 1. GrokSentimentClient

The `GrokSentimentClient` class (in `models/grok_sentiment_client.py`) provides the interface to the Grok API. It offers the following functionality:

- **analyze_sentiment(text)**: Analyzes a single text for sentiment, providing a rating (1-5), confidence score (0-1), sentiment category (positive/neutral/negative), and reasoning.

- **analyze_market_news(news_items)**: Analyzes a list of news headlines or articles, providing an overall sentiment analysis and individual assessment of each item.

- **convert_sentiment_to_signal(sentiment_result)**: Converts sentiment analysis output to trading signals (BUY/HOLD/SELL), with confidence scores and reasoning.

### 2. SentimentAnalystAgent

The `SentimentAnalystAgent` class (in `agents/sentiment_analyst_agent.py`) integrates the Grok client into the agent architecture:

- Analyzes market sentiment from various text sources
- Handles different input formats (symbol string or market_data dictionary)
- Provides standardized output with signal, confidence, and reasoning
- Includes fallback analysis when Grok API is unavailable

## Usage Example

```python
# Initialize the agent
sentiment_agent = SentimentAnalystAgent()

# Analyze with just a symbol (general market sentiment)
result = sentiment_agent.analyze(symbol="BTC/USDT")

# Analyze with market data including news and social posts
market_data = {
    "symbol": "BTC/USDT",
    "news": [
        "Bitcoin reaches new all-time high above $100,000 as institutional adoption grows",
        "Major central bank announces interest rate hike to combat inflation pressures"
    ],
    "social_posts": [
        "Just bought more $BTC, feeling bullish for the next month! #Bitcoin #ToTheMoon",
        "Markets looking uncertain with these mixed economic signals, staying cautious"
    ]
}
result = sentiment_agent.analyze(market_data=market_data)

# Output format
print(f"Signal: {result['signal']}")  # BUY, SELL, or HOLD
print(f"Confidence: {result['confidence']}%")  # 0-100
print(f"Reasoning: {result['reasoning']}")
```

## Technical Details

The integration uses the xAI API with the same patterns and structure as OpenAI's API:

- Base URL: `https://api.x.ai/v1`
- Model used: `grok-2-1212` (text-only model)
- Request format follows OpenAI's chat completion structure
- Response format is JSON for easier parsing

## Testing

A test script (`test_grok_sentiment.py`) is provided to validate the Grok sentiment analysis functionality:

- Tests basic sentiment analysis on positive, negative, and neutral texts
- Tests analysis of multiple news items
- Tests conversion of sentiment results to trading signals

## Error Handling

The integration includes robust error handling:

- Automatic fallback to neutral sentiment if Grok API is unavailable
- Graceful handling of missing API keys
- Validation and normalization of API responses
- Detailed logging for debugging

## Integration with Decision Agent

The SentimentAnalystAgent is factored into the trading decision with a configurable weight (default: 0.8). This allows the system to balance the sentiment analysis with other factors like technical analysis, liquidity, etc.