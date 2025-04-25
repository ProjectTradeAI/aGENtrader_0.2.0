# Local LLM Integration Guide

This guide explains how to use the local LLM integration in your trading bot to reduce OpenAI API costs during backtesting and development.

## Overview

The local LLM integration provides a way to use a local LLM (TinyLlama-1.1B-chat) for agent interactions instead of making API calls to OpenAI. This can significantly reduce costs during backtesting and development.

The integration supports a hybrid approach where:
- Analysis agents use the local LLM (lower cost, adequate for data analysis)
- Decision agents use OpenAI (higher quality for critical decision-making)

## Key Components

The integration consists of several modules:

1. `utils/llm_integration/local_llm.py` - Core implementation of the local LLM
2. `utils/llm_integration/llm_router.py` - Routes requests to local LLM or OpenAI
3. `utils/llm_integration/autogen_integration.py` - Integrates with AutoGen

## Usage Examples

### Basic Usage

```python
from utils.llm_integration import LocalChatCompletion

# Create a completion using the local LLM
completion = LocalChatCompletion.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is technical analysis?"}
    ],
    temperature=0.7,
    max_tokens=256,
    timeout=30  # Set a timeout to prevent long-running generations
)

print(completion['choices'][0]['message']['content'])
```

### Using the LLM Router

```python
from utils.llm_integration import llm_router

# Determine if we should use local LLM or OpenAI
config = llm_router.get_llm_config("MarketAnalyst")

# config will have the right model based on agent type
```

### Integration with AutoGen Agents

```python
from utils.llm_integration import AutoGenLLMConfig

# Patch AutoGen to use our local LLM implementation
AutoGenLLMConfig.patch_autogen()

# Create LLM configuration for AutoGen agents
config_list = AutoGenLLMConfig.get_autogen_config_list()

# Create agent with proper configuration
config = AutoGenLLMConfig.get_agent_config("MarketAnalyst", config_list)

agent = AssistantAgent(
    name="MarketAnalyst",
    llm_config=config
)
```

## Performance Considerations

- The local LLM is slower than OpenAI API calls but eliminates network latency
- First inference is slow due to model loading (~9-10 seconds)
- Subsequent inferences are slower for complex prompts
- Memory usage is ~600MB with the quantized TinyLlama model
- CPU usage is higher than when using OpenAI API
- We've implemented timeout handling to prevent hanging during generation

## Model Selection

For this implementation, we use a quantized version of TinyLlama-1.1B-chat:
- Smaller model size (~669MB vs 4GB for Llama-2-7B-chat)
- Works within Replit's memory constraints
- Faster inference time than larger models
- Acceptable quality for simple analysis tasks
- Not suitable for complex reasoning or final decisions

## When to Use Local LLM vs OpenAI

### Use Local LLM For:
- Development and testing
- Backtesting with many iterations
- Analysis agents that don't make critical decisions
- Data processing tasks

### Use OpenAI For:
- Final decision-making agents
- Production environments
- Complex reasoning tasks
- When inference quality is critical

## Extending the Integration

To add support for new agent types, update the agent categories in `utils/llm_integration/llm_router.py`:

```python
ANALYST_AGENTS = [
    "MarketAnalyst",
    "GlobalMarketAnalyst", 
    "LiquidityAnalyst",
    "PatternRecognitionAnalyst",  # Add new analyst types here
]

DECISION_AGENTS = [
    "TradingDecisionAgent",
    "RiskManager",
    "StrategyManager",
    "PortfolioManager"  # Add new decision agent types here
]
```

## Testing Results

### Simple Query Test
- Model: TinyLlama-1.1B-chat (quantized)
- Query: "Hello, how are you?"
- Response time: ~9.2 seconds (includes model loading)
- Result: Successfully generated coherent response

### Market Analysis Test
- Model: TinyLlama-1.1B-chat (quantized)
- Task: Simple market trend analysis based on price, RSI, MACD, and MA data
- Response: More complex market analysis tasks may time out with the default timeout
- Recommendation: Use simpler prompts or increase timeout for complex tasks

## Conclusion

The local LLM integration provides a cost-effective way to use agent-based systems during development and backtesting. By using a hybrid approach where analysis agents use the local LLM and decision agents use OpenAI, we can balance cost savings with decision quality.