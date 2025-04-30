# aGENtrader v2 Agent Migration Guide

This guide explains how to migrate existing agents to the new standardized agent architecture introduced in aGENtrader v0.2.0.

## Overview of Changes

The new agent architecture introduces:

1. **Standardized interfaces** for all agent types
2. **Clear inheritance hierarchy** with base classes
3. **Consistent naming and method signatures** across agents
4. **Better type hints** for improved IDE support and error detection
5. **Improved error handling** and logging across all agents

## Major Interface Changes

We now have the following main interfaces:

- `AgentInterface`: Base interface for all agents
- `AnalystAgentInterface`: Interface for market analysis agents 
- `DecisionAgentInterface`: Interface for trading decision agents
- `ExecutionAgentInterface`: Interface for trade execution agents

## Migration Steps

### 1. Update Agent Imports

Replace direct imports of specific agent classes with interface imports:

```python
# Old imports
from agents.technical_analyst_agent import TechnicalAnalystAgent

# New imports
from agents.base_agent import BaseAnalystAgent
from agents.agent_interface import AnalystAgentInterface
```

### 2. Update Class Inheritance

Change your agent's inheritance to use the appropriate base classes:

```python
# Old class definition
class MyCustomAgent:
    def __init__(self, data_fetcher=None):
        self.data_fetcher = data_fetcher
        
# New class definition
class MyCustomAgent(BaseAnalystAgent, AnalystAgentInterface):
    def __init__(self, data_fetcher=None):
        super().__init__(agent_name="my_custom_agent")
        self.data_fetcher = data_fetcher
```

### 3. Implement Required Methods

Ensure your agent implements all required methods from its interfaces:

```python
# Required AgentInterface properties
@property
def name(self) -> str:
    return self._agent_name
    
@property
def description(self) -> str:
    return "My custom trading agent that analyzes XYZ"
    
@property
def version(self) -> str:
    from core.version import VERSION
    return VERSION

# Required AnalystAgentInterface methods
def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
    # Your analysis logic here
    result = {
        'signal': 'HOLD', 
        'confidence': 75,
        'reasoning': 'Analysis shows...',
        'data': {'indicator1': 0.5, 'indicator2': 0.8}
    }
    return result
```

### 4. Use Standardized Result Format

All agent results should follow the standardized format:

```python
# Analyst agent results
{
    'signal': 'BUY',  # One of: 'BUY', 'SELL', 'HOLD', 'NEUTRAL'
    'confidence': 85,  # Integer 0-100
    'reasoning': 'Price is above moving averages and momentum is strong',
    'timestamp': '2025-04-30T12:34:56',  # ISO format timestamp
    'data': {  # Optional supporting data
        'indicators': {'rsi': 65, 'macd': 0.5},
        'metrics': {'risk_ratio': 1.5}
    }
}

# Decision agent results
{
    'signal': 'BUY',
    'confidence': 80,
    'reasoning': 'Strong buy signals from technical and sentiment analysis',
    'timestamp': '2025-04-30T12:34:56',
    'contributions': {  # Weighted contributions from analysts
        'technical_analysis': {'signal': 'BUY', 'confidence': 85, 'contribution': 25.5},
        'sentiment_analysis': {'signal': 'BUY', 'confidence': 75, 'contribution': 15.0}
    },
    'data': {
        'signal_scores': {'BUY': 65.5, 'SELL': 12.0, 'HOLD': 22.5},
        'analyst_data': {...}  # Collected from analyst results
    }
}
```

### 5. Use Helper Methods from Base Classes

The base classes provide helpful methods for common operations:

```python
# Create standardized result
result = self.create_standard_result(
    signal='BUY',
    confidence=85,
    reason='Price is above moving averages and momentum is strong',
    data={'indicators': {'rsi': 65, 'macd': 0.5}}
)

# Handle errors consistently
try:
    # Analysis code
except Exception as e:
    return self.handle_analysis_error(e, 'technical')
    
# Validate input parameters
if not self.validate_input(symbol, interval):
    return self.build_error_response('INVALID_INPUT', 'Symbol and interval are required')
    
# Validate agent results
result = self.validate_result(result)
```

### 6. Update Decision Agents

Decision agents now collect and weigh analyst results explicitly:

```python
# Old decision making
def make_decision(self, analyst_results):
    # Direct processing of results
    
# New decision making pattern
def add_analyst_result(self, analysis_type: str, result: Dict[str, Any]) -> None:
    self.analyst_results[analysis_type] = result
    
def make_decision(self) -> Dict[str, Any]:
    # Process collected results from self.analyst_results
    # Calculate weighted scores
    # Return standardized decision
```

## Testing Your Migration

Use the new test harness to verify your migrated agents:

```bash
python tests/test_agent_individual.py --agent YourCustomAgent --mock-data --explain
```

This will run your agent in isolation and show detailed information about its operation, including any errors or warnings.

## Common Migration Issues

1. **Missing properties**: Ensure all required properties (`name`, `description`, `version`) are implemented
2. **Method signature mismatches**: Double-check that method signatures match the interfaces exactly
3. **Incorrect result formats**: Verify that your agent returns results in the standardized format
4. **Initialization errors**: Make sure to call `super().__init__()` in your constructor
5. **Import errors**: Update imports to use the new module structure

## Getting Help

If you encounter issues with the migration, please create detailed error reports in GitHub Issues with:

1. The original agent code
2. Your migration attempt
3. The exact error message or unexpected behavior
4. Environment details (OS, Python version, etc.)