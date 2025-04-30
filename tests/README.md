# aGENtrader v2 Test Suite

This directory contains test utilities and scripts for the aGENtrader v2 trading system.

## Individual Agent Testing

The `test_agent_individual.py` script allows testing of individual analyst agents in isolation with:

- Controlled input data (real or mock)
- Full visibility into decision processes
- Deterministic testing for reproducibility
- Flexible agent selection via CLI

### Usage

```bash
python tests/test_agent_individual.py \
  --agent TechnicalAnalystAgent \
  --symbol BTC/USDT \
  --interval 4h \
  --mock-data \
  --temperature 0.0 \
  --explain \
  --repeat 3
```

### Parameters

- `--agent`: Name of the agent class to test (required)
- `--symbol`: Trading symbol (e.g., BTC/USDT)
- `--interval`: Time interval (e.g., 1h, 4h, 1d)
- `--mock-data`: Use mock data instead of real API
- `--temperature`: LLM temperature (0.0-1.0)
- `--explain`: Show detailed prompts and responses
- `--repeat`: Run N iterations to observe variability
- `--list`: List available agent classes

### Examples

List all available agents:
```bash
python tests/test_agent_individual.py --list
```

Test TechnicalAnalystAgent with real data:
```bash
python tests/test_agent_individual.py --agent TechnicalAnalystAgent --symbol BTC/USDT --interval 4h
```

Test SentimentAnalystAgent with mock data:
```bash
python tests/test_agent_individual.py --agent SentimentAnalystAgent --symbol BTC/USDT --interval 1d --mock-data
```

Test DecisionAgent with multiple iterations and varying temperature:
```bash
python tests/test_agent_individual.py --agent DecisionAgent --temperature 0.5 --repeat 3 --explain
```

## Agent Architecture

The test suite is built on top of the following architecture:

- `AgentInterface`: The base interface that all agents must implement
- `AnalystAgentInterface`: Interface for agents that analyze market data
- `DecisionAgentInterface`: Interface for agents that make trading decisions
- `ExecutionAgentInterface`: Interface for agents that execute trades

Each interface defines the minimal contract that agents must fulfill to be compatible with the system, promoting consistency across agent implementations and making the system more maintainable.

## Implementing New Agents

When implementing a new agent:

1. Choose the appropriate interface to implement (`AnalystAgentInterface` for most agents)
2. Extend the appropriate base class (`BaseAnalystAgent` for most agents)
3. Implement the required methods (e.g., `analyze()` for analyst agents)
4. Register the agent in the appropriate factory

## Mock Data Providers

For testing purposes, you can use the `MockDataProvider` class to generate synthetic market data. This is useful when you don't have access to the real API or want deterministic test results.

To use mock data:
```bash
python tests/test_agent_individual.py --agent TechnicalAnalystAgent --mock-data
```

## LLM Integration Testing

You can test agent interactions with LLMs by using the `--explain` flag:
```bash
python tests/test_agent_individual.py --agent TechnicalAnalystAgent --explain
```

This will show the prompts sent to the LLM and the responses received, which is useful for debugging and improving agent prompts.