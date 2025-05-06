# GrokClient for aGENtrader v0.2.2

## Overview

GrokClient is a dedicated module for interacting with xAI's Grok API in the aGENtrader v0.2.2 system. It provides a standardized interface for using Grok's advanced language models with features specifically tailored for the trading platform.

## Features

- **Text Summarization**: Condense trading reports and market analysis
- **Sentiment Analysis**: Analyze text to determine sentiment score and confidence
- **Trade Summary Formatting**: Generate human-like trade summaries with distinct agent voices
- **Image Analysis**: Process chart images with Grok's vision model (when available)

## Implementation

The GrokClient follows OpenAI's SDK patterns making it familiar for developers who have worked with OpenAI's services. It includes proper fallback mechanisms and error handling to ensure robustness.

### Models Available

| Model Name | Inputs | Output | Context Window | Capabilities |
|------------|--------|--------|---------------|--------------|
| grok-2-vision-1212 | text, image | text | 8192 tokens | Text and image input/output |
| grok-2-1212 | text | text | 131072 tokens | Text-only processing |
| grok-vision-beta | text, image | text | 8192 tokens | Text and image input/output |
| grok-beta | text | text | 131072 tokens | Text-only processing |

## Usage

### Setup

1. Ensure the `XAI_API_KEY` environment variable is set with your xAI API key
2. Import the client in your code:

```python
from models.grok_client import GrokClient

# Initialize the client
grok = GrokClient()

# Check if API is available
if grok.is_available():
    # Client is ready to use
    ...
```

### Examples

#### Text Summarization

```python
summary = grok.summarize_text("""
Bitcoin's price action has been consolidating in a tight range between $45,000 and $50,000 for the past week,
with decreasing volatility. Trading volume has dropped by 15% compared to the previous week, suggesting
trader uncertainty.
""")
```

#### Sentiment Analysis

```python
sentiment = grok.analyze_sentiment("Markets are showing signs of recovery with increased institutional buying.")
# Returns: {"rating": 4, "confidence": 0.85}
```

#### Trade Summary Generation

```python
trade_plan = {
    "symbol": "BTC/USDT",
    "signal": "BUY",
    "confidence": 85,
    # Additional trade details...
}

agent_analyses = [
    {
        "agent_name": "TechnicalAnalystAgent",
        "signal": "BUY",
        "confidence": 80,
        "reasoning": "Price broke above key resistance..."
    },
    # Additional agent analyses...
]

summary = grok.format_trade_summary(
    trade_plan=trade_plan,
    agent_analyses=agent_analyses,
    style="formal"  # Options: formal, casual, technical, balanced
)
```

## Integration with ToneAgent

The GrokClient is primarily used by the ToneAgent, which generates human-like styled summaries of multi-agent trade decisions. The integration provides:

1. Improved summary quality with more distinct agent voices
2. Better handling of complex market narratives
3. Proper fallback mechanisms when the API is unavailable
4. Configurable styling options (formal, casual, technical, balanced)

## Configuration

The ToneAgent's configuration in `config/settings.yaml` controls how the GrokClient is used:

```yaml
agents:
  tone_agent:
    enabled: true
    use_api: true
    api_model: grok-2-1212
    temperature: 0.7
    max_tokens: 1000
    log_summaries: true
    summaries_dir: logs/summaries
    style: balanced  # Options: formal, casual, technical, balanced
```

## Error Handling

The GrokClient includes robust error handling:

1. It checks for API key availability before making calls
2. Provides meaningful error messages when the API is unavailable
3. Returns structured responses even in error cases
4. Logs all API interactions for debugging

## Testing

A dedicated test script `test_grok_integration.py` is included to verify GrokClient functionality:

```bash
python test_grok_integration.py
```

This script tests all major features directly and through ToneAgent integration.

## Future Enhancements

- Add support for streaming responses
- Implement batched request processing for multiple analyses
- Add additional fine-tuning options for trade summaries
- Integrate with other analyst agents for improved market insights