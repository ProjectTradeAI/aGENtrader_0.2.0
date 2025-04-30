# aGENtrader Test Framework

This directory contains test tools and utilities for the aGENtrader v2 system.

## Individual Agent Testing

The `test_agent_individual.py` script is a test harness for running individual agents in isolation to verify their behavior and debug their functionality.

### Usage

```bash
# List available agents
python tests/test_agent_individual.py --list

# Test a specific agent with default settings
python tests/test_agent_individual.py --agent TechnicalAnalystAgent

# Test with custom parameters
python tests/test_agent_individual.py \
  --agent SentimentAnalystAgent \
  --symbol BTC/USDT \
  --interval 4h \
  --mock-data \
  --temperature 0.0 \
  --explain \
  --repeat 3
```

### Command Line Options

- `--list`: Display available agents
- `--agent AGENT_NAME`: Specify the agent to test
- `--symbol SYMBOL`: Trading symbol (default: BTC/USDT)
- `--interval INTERVAL`: Time interval (default: 1h)
- `--mock-data`: Use mock data provider instead of real API
- `--temperature TEMP`: Set LLM temperature (0.0-1.0)
- `--explain`: Show detailed explanations
- `--repeat N`: Repeat the test N times

### Requirements

- API keys should be set in environment variables for testing with real data:
  - `BINANCE_API_KEY` and `BINANCE_API_SECRET` for Binance API access
  - `XAI_API_KEY` for Grok API access (sentiment analysis)

### Testing with Mock Data

When `--mock-data` is specified, the harness uses the `MockDataProvider` from `utils/mock_data_provider.py` which generates realistic-looking market data based on configurable parameters. This allows testing without relying on external API services.

## Implementing New Tests

When adding new test cases, follow these guidelines:

1. Put unit tests in `tests/unit/`
2. Put integration tests in `tests/integration/`
3. Put end-to-end tests in `tests/e2e/`
4. Add test utilities to `tests/utils/`

## Running all Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/unit/
```