# Structured Agent Decision-Making System

## Overview

This document outlines the implementation of a structured agent decision-making system for cryptocurrency trading. The system integrates database access with a collaborative multi-agent framework to produce consistent, reliable trading decisions in a well-defined format.

## Key Components

The structured decision-making system consists of the following key components:

1. **Database Integration** - Provides access to real-time market data
2. **Structured Decision Extractor** - Ensures consistent decision format
3. **Collaborative Trading Framework** - Orchestrates specialized agents
4. **Testing Framework** - Validates system functionality

## Structured Decision Format

All trading decisions conform to the following standardized JSON format:

```json
{
  "decision": "BUY",       // BUY, SELL, or HOLD
  "asset": "BTC",          // Asset symbol
  "entry_price": 45300,    // Target entry price
  "stop_loss": 44800,      // Stop loss price
  "take_profit": 46800,    // Take profit price
  "confidence_score": 0.85, // Confidence score (0.0-1.0)
  "reasoning": "Bullish momentum confirmed by RSI and positive on-chain flows."
}
```

This structured format ensures that decisions are:
- Machine-readable for automated execution
- Human-interpretable for review and analysis
- Consistent across all trading scenarios
- Fully auditable with clear reasoning

## Agent Roles and Collaboration

The trading system employs multiple specialized agents working together:

### 1. Market Analyst
- Retrieves and analyzes real-time data from the database
- Identifies key price levels, trends, and patterns
- Analyzes technical indicators and on-chain metrics
- Provides comprehensive market analysis

### 2. Strategic Advisor
- Interprets market analysis into actionable strategies
- Formulates precise trading plans with entry and exit points
- Considers multiple timeframes and scenarios
- Recommends specific trading directions

### 3. Risk Manager
- Evaluates risk-reward profile of proposed strategies
- Validates position sizing and risk parameters
- Challenges questionable assumptions
- Ensures proper stop-loss and risk management

### 4. Decision Maker
- Synthesizes input from all specialist agents
- Makes definitive trading decisions
- Specifies exact entry, stop-loss, and take-profit levels
- Outputs the final decision in the standardized JSON format

## Implementation Details

### Database Integration

The system integrates with our PostgreSQL database through two primary functions:

```python
def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                     days: Optional[int] = None, format_type: str = 'json') -> str:
    """Query market data for a specific symbol."""
    # Implementation details...
```

```python
def get_market_statistics(symbol: str, interval: str = '1d', 
                         days: int = 30, format_type: str = 'json') -> str:
    """Get market statistics for a specific symbol."""
    # Implementation details...
```

These functions are registered with AutoGen and made available to the Market Analyst agent.

### Decision Extraction

The system uses robust parsing techniques to extract structured decisions:

```python
def extract_trading_decision(agent_response: str) -> dict:
    """Extract trading decision from agent response."""
    # Try to find and parse JSON directly
    json_match = re.search(r'\{[\s\S]*\}', agent_response)
    if json_match:
        decision_json = json.loads(json_match.group(0))
        return validate_decision_format(decision_json)
        
    # Look for key-value pairs if JSON not found
    decision = {}
    for key in ["decision", "asset", "entry_price", "stop_loss", 
               "take_profit", "confidence_score", "reasoning"]:
        match = re.search(rf'{key}[:\s]+([^,\n]+)', agent_response, re.IGNORECASE)
        if match:
            decision[key] = match.group(1).strip('" ')
    
    if decision:
        return validate_decision_format(decision)
```

### Collaborative Framework

The collaborative framework orchestrates the multi-agent workflow:

```python
def run_trading_session(symbol: str, interval: str = "1h") -> dict:
    """Run a complete trading session with all agents."""
    # Initialize agents and group chat
    # Run the conversation
    # Extract and validate the final decision
    # Log decision for audit trail
```

## Testing and Validation

A comprehensive testing framework ensures system reliability:

1. **Decision Extractor Tests** - Verify extraction from various formats
2. **Database Integration Tests** - Confirm data access functionality
3. **Collaborative Framework Tests** - Validate end-to-end decision process

## Logging and Audit Trail

The system maintains detailed logs for auditing and improvement:

```python
def log_trading_decision(decision: dict) -> None:
    """Log trading decision to file and database."""
    # Configure logging
    logging.basicConfig(
        filename=f"data/logs/trading_decisions_{datetime.now().strftime('%Y%m%d')}.log",
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Log to file
    logging.info(f"Trading Decision: {json.dumps(decision)}")
    
    # Store in database
    store_decision_in_database(decision)
```

## Usage Examples

### Basic Usage

```python
from agents.collaborative_trading_framework import run_trading_framework

# Get trading decision for BTCUSDT at 1-hour interval
decision = run_trading_framework(symbol="BTCUSDT", interval="1h")

print(f"Decision: {decision['decision']}")
print(f"Entry Price: {decision['entry_price']}")
print(f"Stop Loss: {decision['stop_loss']}")
```

### Advanced Usage

```python
from agents.collaborative_trading_framework import CollaborativeTradingFramework

# Initialize framework with custom configuration
framework = CollaborativeTradingFramework(
    max_consecutive_auto_reply=10,
    log_dir="custom/log/directory"
)

# Run trading session with full conversation output
result = framework.run_trading_session(
    symbol="ETHUSDT", 
    interval="4h",
    full_output=True
)

# Access decision and conversation history
decision = result
conversation = result.get("conversation", [])
```

## Best Practices

1. **Prompting Consistency**
   - Maintain clear, structured prompts for each agent
   - Keep the Decision Maker's prompt consistent for reliable extraction

2. **Error Handling**
   - Always validate decisions before taking action
   - Implement fallback mechanisms for extraction failures

3. **Performance Optimization**
   - Cache frequently accessed market data
   - Use parameterized database queries for security and efficiency

4. **Continuous Improvement**
   - Regularly review agent conversations to refine prompts
   - Analyze decision quality against actual market outcomes

## Next Steps

1. Complete integration with trading execution systems
2. Implement backtesting framework to validate decision quality
3. Add more specialized agents for deeper market analysis
4. Enhance decision metrics with risk-adjusted return calculations