# Trading Decision Framework with AutoGen

## Overview

This document outlines the design and implementation of a structured agentic decision-making framework for trading using AutoGen. The system enables consistent, well-formatted trading decisions through specialized agent roles, structured outputs, and comprehensive logging.

## Architecture

```
┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
│                       │      │                       │      │                       │
│  Decision Session     │      │   TradingAgentSystem  │      │   Database Retrieval  │
│      Manager          │─────▶│     (Agent Roles)     │─────▶│        Tool           │
│                       │      │                       │      │                       │
└───────────────────────┘      └───────────────────────┘      └───────────────────────┘
           │                             │                               │
           │                             │                               │
           ▼                             ▼                               ▼
┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
│                       │      │                       │      │                       │
│  Decision Extraction  │      │  Agent Conversations  │      │  SQL Database with    │
│      & Validation     │◀─────│     & Collaboration   │◀─────│    Market Data        │
│                       │      │                       │      │                       │
└───────────────────────┘      └───────────────────────┘      └───────────────────────┘
           │
           │
           ▼
┌───────────────────────┐
│                       │
│   Decision Logging    │
│    & Audit Trail      │
│                       │
└───────────────────────┘
```

## Key Components

### 1. Decision Session Manager (`DecisionSession`)

The `DecisionSession` class manages trading decision sessions, coordinating the interaction between various specialized agents to produce structured, well-formatted trading decisions.

**Key features:**
- Handles session lifecycle (start, monitor, complete)
- Manages concurrent sessions
- Provides session status and results
- Maintains session history and audit trail

### 2. Trading Agent System (`TradingAgentSystem`)

The `TradingAgentSystem` class orchestrates the specialized agent roles, directing the conversation flow and ensuring proper data access.

**Agent roles:**
- **Market Analyst**: Analyzes market data and provides technical insights
- **Strategy Manager**: Formulates trading strategies based on market analysis
- **Risk Manager**: Evaluates strategies for risk and suggests controls
- **Trading Decision Agent**: Synthesizes inputs into a final trading decision

### 3. Decision Extraction and Validation

The system includes structured decision extraction and validation to ensure consistent, well-formatted trading decisions:

```json
{
  "decision": "BUY",
  "asset": "BTC",
  "entry_price": 45300,
  "stop_loss": 44800,
  "take_profit": 46800,
  "confidence_score": 0.85,
  "reasoning": "Bullish momentum confirmed by RSI and positive on-chain flows."
}
```

**Validation rules:**
- Required fields: decision, asset, entry_price, stop_loss, take_profit, confidence_score, reasoning
- Decision values: BUY, SELL, HOLD
- Numeric fields: entry_price, stop_loss, take_profit, confidence_score
- Confidence score range: 0.0-1.0

### 4. Database Integration

The system integrates with a SQL database for market data access, providing agents with:
- Latest price information
- Historical price data
- Technical indicators
- Support and resistance levels
- Volume analysis

### 5. Decision Logging and Audit Trail

All trading decisions are logged for future reference, auditing, and improvement:
- Session details and context
- Complete agent conversation history
- Final decision with timestamp
- Validation results

## Decision Session Flow

1. **Session Initialization**
   - Define trading objective
   - Specify target symbol
   - Generate unique session ID

2. **Market Analysis Phase**
   - Retrieve current market data
   - Perform technical analysis
   - Identify key support/resistance levels
   - Analyze market sentiment

3. **Strategy Formulation Phase**
   - Interpret market analysis
   - Identify potential trading opportunities
   - Formulate entry/exit strategy
   - Suggest position sizing

4. **Risk Assessment Phase**
   - Evaluate strategy risk profile
   - Validate stop-loss placement
   - Assess risk-reward ratio
   - Recommend risk controls

5. **Decision Making Phase**
   - Synthesize all inputs
   - Generate structured JSON decision
   - Validate decision format
   - Calculate confidence score

6. **Logging and Audit Phase**
   - Log complete decision
   - Record agent conversation history
   - Store session details
   - Enable future lookup and review

## Usage Examples

### Starting a Trading Decision Session

```python
from orchestration.decision_session import DecisionSession
import asyncio

async def run_trading_session():
    # Initialize session manager
    session_manager = DecisionSession()
    
    # Start a trading decision session
    result = await session_manager.start_decision_session(
        symbol="BTCUSDT",
        objective="Identify short-term trading opportunities based on current market conditions"
    )
    
    # Get session ID
    session_id = result["session_id"]
    
    # Wait for completion and get result
    # (In production, you would likely use a callback or webhook)
    while True:
        status = session_manager.get_session_status(session_id)
        if status["status"] == "completed":
            # Get decision
            session_info = status["session_info"]
            decision = session_info["result"]["decision"]
            print(f"Decision: {decision['decision']} {decision['asset']} at ${decision['entry_price']}")
            break
        await asyncio.sleep(5)

# Run the session
asyncio.run(run_trading_session())
```

### Using Predefined Sessions

```python
from orchestration.decision_session import DecisionSession
import asyncio

async def run_predefined_session():
    # Initialize session manager
    session_manager = DecisionSession()
    
    # Start a predefined session
    result = await session_manager.start_predefined_session(preset="btc_short_term")
    
    # Session is running in the background
    print(f"Session started: {result['session_id']}")

# Run the session
asyncio.run(run_predefined_session())
```

### Getting the Latest Decision

```python
from orchestration.decision_session import DecisionSession

# Initialize session manager
session_manager = DecisionSession()

# Get latest BTC decision
latest = session_manager.get_latest_decision(symbol="BTCUSDT")

if latest["status"] == "success":
    decision = latest["decision"]
    print(f"Latest decision: {decision['decision']} at ${decision['entry_price']}")
    print(f"Confidence: {decision['confidence_score']}")
    print(f"Reasoning: {decision['reasoning']}")
else:
    print(f"No decision found: {latest['message']}")
```

## Configuration Options

The system uses JSON configuration files for flexibility:

### 1. Agent Configuration (`config/agent_config.json`)

Controls the behavior and capabilities of the specialized agents:
- Agent role definitions
- Model selection
- Timeouts and limits
- Default parameters

### 2. Decision Session Configuration (`config/decision_session.json`)

Controls the decision session manager:
- Session timeouts
- Logging configuration
- Predefined session templates
- Decision format validation rules

## Best Practices

1. **Clear Objectives**
   - Define specific trading objectives for each session
   - Focus on one symbol and timeframe per session

2. **Structured Output**
   - Enforce strict JSON decision format
   - Validate all decisions before using them

3. **Logging and Auditing**
   - Keep comprehensive logs of all decisions
   - Review session histories to improve performance

4. **Risk Management**
   - Always include stop-loss and take-profit levels
   - Use confidence scores to filter low-conviction trades

5. **Automation Integration**
   - Parse decision JSON for automated execution
   - Implement additional sanity checks before execution

## Future Enhancements

1. **Multi-Symbol Analysis**
   - Enable analysis of multiple symbols in a single session
   - Compare correlations and sector performance

2. **Portfolio-Wide Decisions**
   - Make decisions considering the entire portfolio
   - Balance risk across multiple positions

3. **Performance Tracking**
   - Track decision performance over time
   - Use historical performance to improve future decisions

4. **Custom Agent Specializations**
   - Add specialized agents for specific markets or strategies
   - Create agents focused on fundamental analysis

5. **Integration with Execution Systems**
   - Direct connection to trading platforms
   - Real-time execution monitoring and reporting