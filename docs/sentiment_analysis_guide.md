# aGENtrader v2 Sentiment Analysis Guide

This guide explains how to use the SentimentAggregatorAgent to fetch cryptocurrency sentiment data from Grok API.

## Overview

The `SentimentAggregatorAgent` retrieves sentiment data from xAI's Grok API. It queries for sentiment about Bitcoin on a specific date or a range of dates. The sentiment data is logged to `logs/sentiment_feed.jsonl` in JSON format.

## Prerequisites

- xAI API Key (set as `XAI_API_KEY` environment variable)
- Python 3.8 or higher
- Required Python packages: `requests`
- (Optional) `python-dotenv` for loading environment variables from `.env` file

## Usage Examples

### Basic Usage

To fetch sentiment data for the current date:

```bash
python sentiment_aggregator_agent.py
```

### Fetch Sentiment for a Specific Date

```bash
python sentiment_aggregator_agent.py --date 2025-04-15
```

### Fetch Historical Sentiment

To fetch sentiment data for the last 7 days up to a specific date:

```bash
python sentiment_aggregator_agent.py --date 2025-04-15 --lookback_days 7
```

## Example EC2 Deployment Workflow

The following steps demonstrate how to set up a daily sentiment feed on an EC2 instance:

1. SSH into your EC2 instance:
   ```bash
   ssh -i aGENtrader.pem ec2-user@your-ec2-instance
   ```

2. Navigate to the aGENtrader directory:
   ```bash
   cd ~/aGENtrader
   ```

3. Create a cron job to fetch sentiment data daily:
   ```bash
   crontab -e
   ```

4. Add the following line to run the sentiment aggregator daily at 2:00 AM:
   ```
   0 2 * * * cd ~/aGENtrader && python sentiment_aggregator_agent.py --lookback_days 1
   ```

5. Save and exit the crontab editor.

## Viewing Sentiment Data

Sentiment data is stored in `logs/sentiment_feed.jsonl`. Each line is a JSON object with the following structure:

```json
{
  "date": "2025-04-15",
  "asset": "BTC",
  "sentiment_score": 0.65,
  "confidence": 85,
  "reasoning": "Bitcoin price stabilized after regulatory clarity...",
  "dominant_topics": ["ETF approval", "Institutional adoption", "Regulatory clarity"],
  "source": "Grok API",
  "timestamp": "2025-04-16T02:00:15.123456"
}
```

## Integration with TechnicalAnalystAgent

To incorporate sentiment data into your trading decisions, you can integrate the sentiment feed with your TechnicalAnalystAgent:

```python
# Example integration in technical_analyst_agent.py
def analyze(self, symbol, interval, **kwargs):
    # Perform technical analysis...
    
    # Include sentiment data in analysis
    sentiment_data = self._get_latest_sentiment()
    if sentiment_data and sentiment_data.get("sentiment_score") > 0.5:
        # Adjust signals based on positive sentiment
        signals["sentiment_boost"] = True
    
    return analysis_result
    
def _get_latest_sentiment(self):
    """Get the latest sentiment data from the sentiment feed."""
    try:
        with open("logs/sentiment_feed.jsonl", "r") as f:
            lines = f.readlines()
            if lines:
                latest = json.loads(lines[-1])
                return latest
    except (FileNotFoundError, json.JSONDecodeError):
        return None
```

## Real-Time Sentiment Analysis

For more real-time sentiment analysis, you can:

1. Run the sentiment agent in a separate screen session:
   ```bash
   screen -S sentiment
   python sentiment_aggregator_agent.py --date $(date +%Y-%m-%d)
   # Press Ctrl+A, D to detach
   ```

2. Configure the agent to run at specific intervals using a script:
   ```bash
   # sentiment_scheduler.sh
   #!/bin/bash
   while true; do
     python sentiment_aggregator_agent.py
     sleep 3600  # Run hourly
   done
   ```

3. Start this scheduler in a screen session:
   ```bash
   screen -S sentiment_scheduler
   ./sentiment_scheduler.sh
   # Press Ctrl+A, D to detach
   ```

## Troubleshooting

If you encounter issues:

1. Check that `XAI_API_KEY` is properly set in the environment or `.env` file
2. Ensure you have internet connectivity to reach the xAI API
3. Check log files for detailed error messages
4. Verify that the `logs` directory exists and is writable

For additional support, please contact the aGENtrader team.