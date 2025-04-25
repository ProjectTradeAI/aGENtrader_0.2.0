# Decision Session System

## Overview

The Decision Session System is a structured agent-based framework for making trading decisions. It coordinates the interaction between specialized trading agents to produce consistent, well-formatted trading decisions with clear parameters and confidence scores.

## Key Components

### 1. DecisionSession

The main orchestration class that manages trading decision sessions:

```python
from orchestration.decision_session import DecisionSession

# Initialize the session manager
session_manager = DecisionSession()

# Start a trading decision session
result = await session_manager.start_decision_session(
    symbol="BTCUSDT",
    objective="Identify short-term trading opportunities"
)

# Get session ID
session_id = result["session_id"]

# Check session status
status = session_manager.get_session_status(session_id)
```

### 2. TradingAgentSystem

The class that manages specialized trading agents and their interactions:

```python
from agents.trading_agents import TradingAgentSystem

# Initialize the trading agent system
agent_system = TradingAgentSystem()

# Initialize the system (creates agents)
await agent_system.initialize()

# Run a trading session
result = await agent_system.run_trading_session(
    symbol="BTCUSDT",
    objective="Evaluate if current market conditions warrant a position change"
)

# Get the decision
decision = result["decision"]
```

## Session Flow

1. **Session Initialization**
   - User initiates a decision session with a symbol and objective
   - System creates unique session ID and initializes session context

2. **Agent System Setup**
   - Specialized agents are initialized with appropriate roles
   - Agent capabilities and tools are configured

3. **Trading Analysis**
   - Agents collaborate to analyze market data and develop strategies
   - Multi-turn conversation leads to consensus decision

4. **Decision Extraction**
   - Final decision is extracted and validated
   - Decision is formatted in standard JSON structure

5. **Logging and History**
   - Complete session details are logged for audit trail
   - Decision is added to history for future reference

## Decision Format

All trading decisions follow a standard format:

```json
{
  "decision": "BUY",
  "asset": "BTCUSDT",
  "entry_price": 45000.0,
  "stop_loss": 43500.0,
  "take_profit": 48000.0,
  "confidence_score": 0.85,
  "reasoning": "Strong support at $45,000 with positive momentum indicators"
}
```

## Configuration

The system is configurable via JSON configuration files:

1. **Agent Configuration** (`config/agent_config.json`)
   - Define agent roles and capabilities
   - Configure LLM settings and temperature
   - Set up session parameters

2. **Decision Session Configuration** (`config/decision_session.json`)
   - Define timeouts and concurrency limits
   - Configure logging and storage
   - Set up predefined session templates

## Usage Examples

### Starting a Decision Session

```python
from orchestration.decision_session import DecisionSession
import asyncio

async def run_session():
    # Initialize session manager
    session_manager = DecisionSession()
    
    # Start a trading decision session
    result = await session_manager.start_decision_session(
        symbol="BTCUSDT",
        objective="Identify short-term trading opportunities"
    )
    
    print(f"Session started: {result['session_id']}")
    
    # Wait for result
    while True:
        status = session_manager.get_session_status(result['session_id'])
        if status['status'] == 'completed':
            decision = status['session_info']['result']['decision']
            print(f"Decision: {decision['decision']} at ${decision['entry_price']}")
            break
        await asyncio.sleep(5)

# Run the async function
asyncio.run(run_session())
```

### Using Predefined Sessions

```python
from orchestration.decision_session import DecisionSession
import asyncio

async def run_predefined():
    # Initialize session manager
    session_manager = DecisionSession()
    
    # Start a predefined session
    result = await session_manager.start_predefined_session("btc_short_term")
    
    print(f"Predefined session started: {result['session_id']}")

# Run the async function
asyncio.run(run_predefined())
```

### Getting Session Status

```python
from orchestration.decision_session import DecisionSession

# Initialize session manager
session_manager = DecisionSession()

# Get status of a specific session
status = session_manager.get_session_status("session_12345678_1234567890")
print(f"Session status: {status['status']}")

if status['status'] == 'completed':
    decision = status['session_info']['result']['decision']
    print(f"Decision: {decision['decision']} at ${decision['entry_price']}")
```

### Listing Sessions

```python
from orchestration.decision_session import DecisionSession

# Initialize session manager
session_manager = DecisionSession()

# List all sessions
all_sessions = session_manager.list_sessions()
print(f"Found {all_sessions['count']} sessions")

# List only completed sessions
completed = session_manager.list_sessions(status="completed")
print(f"Found {completed['count']} completed sessions")
```

### Getting Latest Decision

```python
from orchestration.decision_session import DecisionSession

# Initialize session manager
session_manager = DecisionSession()

# Get latest BTC decision
latest = session_manager.get_latest_decision(symbol="BTCUSDT")

if latest['status'] == 'success':
    decision = latest['decision']
    print(f"Latest decision: {decision['decision']} at ${decision['entry_price']}")
    print(f"Reasoning: {decision['reasoning']}")
else:
    print(f"Error: {latest['message']}")
```

## Running Tests

The system includes a test script for verification:

```bash
# Run the test script
python test_trading_decision.py
```

This script demonstrates the complete workflow of a trading decision session.