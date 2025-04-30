# Agent Migration Guide

This guide provides instructions for migrating existing agent implementations to use the new standardized interfaces and base classes. The new architecture simplifies agent development, improves error handling, and enables more advanced testing capabilities.

## Why Migrate?

The new architecture offers several benefits:

1. **Standardized Interfaces**: Consistent method signatures and return values across all agents
2. **Improved Error Handling**: Built-in error handling and validation
3. **Testing Support**: Easy integration with the test harness for isolated testing
4. **Backward Compatibility**: Legacy methods and attributes are preserved
5. **Simplified Development**: Common functionality is implemented in base classes

## Migration Steps

Follow these steps to migrate your agent to the new architecture:

### 1. Identify the Agent Type

Determine which type of agent you're migrating:

- **Analyst Agent**: Analyzes market data and returns a signal (e.g., TechnicalAnalystAgent)
- **Decision Agent**: Consolidates signals from analyst agents (e.g., DecisionAgent)
- **Execution Agent**: Executes trades based on decisions

### 2. Update the Import Statements

```python
# Old imports
from some_module import BaseAgent

# New imports
from agents.agent_interface import AnalystAgentInterface  # Or appropriate interface
from agents.base_agent import BaseAnalystAgent  # Or appropriate base class
```

### 3. Update the Class Definition

```python
# Old definition
class MyAnalystAgent(BaseAgent):
    # ...

# New definition
class MyAnalystAgent(BaseAnalystAgent):  # Use appropriate base class
    # ...
```

### 4. Update Constructor Parameters

```python
# Old constructor
def __init__(self, name="MyAnalystAgent", config=None):
    # ...

# New constructor
def __init__(
    self,
    name: str = "MyAnalystAgent",
    config: Optional[Dict[str, Any]] = None,
    data_provider: Optional[Any] = None,
    symbol: str = "BTC/USDT",
    interval: str = "1h",
    llm_client: Optional[Any] = None,
    **kwargs
):
    # Call the parent constructor with all parameters
    super().__init__(
        name=name,
        config=config,
        data_provider=data_provider,
        symbol=symbol,
        interval=interval,
        llm_client=llm_client,
        **kwargs
    )
    
    # Add agent-specific initialization
    # ...
```

### 5. Update the Analysis Method (for Analyst Agents)

```python
# Old method
def analyze(self, market_data):
    # ...
    return {
        'signal': signal,
        'confidence': confidence,
        'reasoning': reasoning
    }

# New method
def analyze(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Analyze market data and return insights.
    
    Args:
        market_data: Dictionary containing market data
        
    Returns:
        Dictionary with analysis results
    """
    # ...
    result = {
        'signal': signal,
        'confidence': confidence,
        'reasoning': reasoning,
        'data': {}  # Add any additional data for debugging/tracking
    }
    
    # Validate the result format
    self.validate_analysis_result(result)
    
    return result
```

### 6. Update the Decision Method (for Decision Agents)

```python
# Old method
def make_decision(self, analyst_results):
    # ...

# New method
def make_decision(self, analyst_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Make a trading decision based on analyst results.
    
    Args:
        analyst_results: Dictionary containing outputs from analyst agents
        
    Returns:
        Dictionary with decision results
    """
    # ...
    result = {
        'signal': signal,
        'confidence': confidence,
        'reasoning': reasoning,
        'contributions': contributions  # How each analyst contributed
    }
    
    # Validate the result format
    self.validate_decision_result(result)
    
    return result
```

### 7. Remove Redundant Methods

The following methods are now provided by the base classes and can be removed from your implementation:

- `get_agent_config()` - Use the one provided by BaseAgent
- `run()` - Use the one provided by BaseAgent, which calls your `analyze()` or `make_decision()`
- Basic validation methods - Use `validate_analysis_result()` or `validate_decision_result()`

### 8. Test the Migration

Use the test harness to verify your migrated agent works correctly:

```bash
python tests/test_agent_individual.py --agent MyAnalystAgent --mock-data --explain
```

## Example: Before and After Migration

### Before Migration

```python
class TechnicalAnalystAgent:
    def __init__(self, config=None):
        self.config = config or {}
        self.agent_config = self.get_agent_config()
        # ...
        
    def get_agent_config(self):
        return {
            "name": "TechnicalAnalystAgent",
            "provider": "mistral",
            # ...
        }
        
    def analyze(self, market_data):
        # Analysis logic...
        return {
            'signal': 'BUY',
            'confidence': 75,
            'reasoning': 'Technical indicators suggest upward momentum.'
        }
```

### After Migration

```python
from typing import Dict, Any, Optional
from agents.base_agent import BaseAnalystAgent

class TechnicalAnalystAgent(BaseAnalystAgent):
    def __init__(
        self,
        name: str = "TechnicalAnalystAgent",
        config: Optional[Dict[str, Any]] = None,
        data_provider: Optional[Any] = None,
        symbol: str = "BTC/USDT",
        interval: str = "1h",
        llm_client: Optional[Any] = None,
        **kwargs
    ):
        # Call the parent constructor
        super().__init__(
            name=name,
            config=config,
            data_provider=data_provider,
            symbol=symbol,
            interval=interval,
            llm_client=llm_client,
            **kwargs
        )
        
        # Add agent-specific initialization
        self.indicators = self.config.get('indicators', ['rsi', 'macd', 'ema'])
        
    def analyze(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Analyze market data using technical indicators.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with technical analysis results
        """
        # Analysis logic...
        result = {
            'signal': 'BUY',
            'confidence': 75,
            'reasoning': 'Technical indicators suggest upward momentum.',
            'data': {
                'indicators': {
                    'rsi': 65,
                    'macd': 0.5,
                    'ema': 'bullish'
                }
            }
        }
        
        # Validate the result format
        self.validate_analysis_result(result)
        
        return result
```

## Troubleshooting

### Common Issues

1. **Missing attributes**: If your agent uses attributes from the old BaseAgent that aren't in the new base classes, you can add them in your constructor.

2. **Method signature mismatches**: Make sure your methods have the correct signatures, especially type hints and return types.

3. **Validation errors**: If `validate_analysis_result()` fails, check that your result dictionary has all required keys and proper values.

### Getting Help

If you encounter issues during migration, you can:

1. Check the base class implementations for reference
2. Look at other migrated agents for examples
3. Run the test harness with `--explain` to see detailed diagnostics