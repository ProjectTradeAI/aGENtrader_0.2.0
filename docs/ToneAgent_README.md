# ToneAgent Documentation

## Overview

The ToneAgent is a specialized agent in the aGENtrader v0.2.2 system that generates human-like styled summaries of multi-agent trade decisions. It provides a unique "voice" for each analyst agent and synthesizes an overall narrative that makes the complex decision-making process more engaging and accessible.

## Features

- Generates distinct voices for each analyst agent based on their role and analysis
- Produces a cohesive system summary that explains the final decision logic
- Determines the overall market mood (bullish, bearish, cautious, etc.)
- Outputs structured JSON with agent_comments, system_summary, and mood fields
- Integrated with Grok API for natural language generation
- Fallback mechanisms for resilience when API is unavailable

## Integration with aGENtrader System

The ToneAgent is designed to be run at the end of the full trade cycle after:
1. All analyst agents have provided their analyses
2. The DecisionAgent has made a final decision
3. The TradePlanAgent has generated a trade plan

It takes the combined outputs of these processes and transforms them into a human-readable narrative.

## Usage

```python
from agents.tone_agent import ToneAgent

# Initialize the ToneAgent
tone_agent = ToneAgent()

# Generate a summary from analysis results and final decision
summary = tone_agent.generate_summary(
    analysis_results=analyst_results,  # Dictionary of analyst results
    final_decision=decision,           # Final decision dictionary
    symbol="BTC/USDT",                 # Trading symbol
    interval="4h"                      # Time interval
)

# Print a styled summary to the console
tone_agent.print_styled_summary(summary, "BTC/USDT", "4h")
```

## Output Format

The ToneAgent generates a structured JSON output with the following fields:

```json
{
  "agent_comments": {
    "TechnicalAnalystAgent": "The moving averages have crossed bullishly...",
    "SentimentAnalystAgent": "The vibes on social media are turning positive...",
    "LiquidityAnalystAgent": "The order book's a standoff right now...",
    "FundingRateAnalystAgent": "Watch out, the funding rates are dipping...",
    "OpenInterestAnalystAgent": "Open interest isn't moving much..."
  },
  "system_summary": "While technical indicators and social sentiment strongly support...",
  "mood": "cautious"
}
```

## Technical Implementation

The ToneAgent uses the LLM client to generate summaries, specifically using the Grok API. It constructs a prompt that includes:

1. Context about each agent's analysis
2. The final decision and its rationale
3. Instructions for generating a coherent narrative with distinct voices

The agent also implements fallback mechanisms for cases where the LLM API is unavailable or returns an error.

## Testing

The ToneAgent can be tested independently using the standalone test script:

```bash
python tests/run_tone_agent_test.py
```

This script creates a mock analysis and decision scenario, generates a summary, and saves the output to a JSON file for inspection.

## Version Compatibility

The ToneAgent is part of aGENtrader v0.2.2 and is designed to work with the unified agent architecture. It expects analyst results and decisions to follow the standardized format implemented in this version.

## Error Handling

If the Grok API is unavailable or returns an error, the ToneAgent will fall back to a simpler templated summary. All errors are logged for troubleshooting, but the agent will never fail catastrophically.

## Future Enhancements

- Support for multiple LLM providers beyond Grok
- Customizable tone and style preferences
- Historical summary comparison for trend analysis
- Integration with notification systems for alerts