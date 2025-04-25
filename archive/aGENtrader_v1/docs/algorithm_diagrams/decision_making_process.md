# Decision Making Process

This document details the decision-making process in the trading system, focusing on how the different agents collaborate to produce trading decisions.

## Process Overview

The decision-making process involves multiple specialized agents working together in a structured session. The process is orchestrated by the `DecisionSession` class and uses AutoGen for agent collaboration.

## Detailed Algorithm

```
START
|
+----> Initialize DecisionSession with symbol and parameters
|      |
|      +----> Load configuration
|      |
|      +----> Create logging setup
|      |
|      +----> Initialize decision tracker (if tracking enabled)
|      |
|      +----> Get current price for the symbol
|
+----> Run decision session
|      |
|      +----> Check if symbol and price are available
|      |
|      +----> Gather market data
|      |      |
|      |      +----> Get latest price
|      |      |
|      |      +----> Get market summary
|      |      |
|      |      +----> Get recent market data
|      |      |
|      |      +----> Calculate technical indicators (SMA, RSI, etc.)
|      |      |
|      |      +----> Find support/resistance levels
|      |      |
|      |      +----> Detect patterns
|      |      |
|      |      +----> Calculate volatility
|      |      |
|      |      +----> IF GlobalMarketAnalyst available:
|      |      |      |
|      |      |      +----> Get macro market summary
|      |      |      |
|      |      |      +----> Get relevant correlations
|      |      |      |
|      |      |      +----> Get market indices data
|      |      |      |
|      |      |      +----> Get crypto market metrics
|      |      |
|      |      +----> IF LiquidityAnalyst available:
|      |             |
|      |             +----> Get exchange flow data
|      |             |
|      |             +----> Get funding rate data
|      |             |
|      |             +----> Get market depth data
|      |             |
|      |             +----> Get futures basis data
|      |             |
|      |             +----> Get volume profile data
|      |      
|      +----> Check if AutoGen is available
|             |
|             +----> If NOT available, run simulated session
|             |      |
|             |      +----> Extract RSI value if available
|             |      |
|             |      +----> Apply simple rule-based decision logic
|             |      |
|             |      +----> Format decision
|             |      |
|             |      +----> Track decision performance (if enabled)
|             |
|             +----> If available, run agent session
|                    |
|                    +----> Setup AutoGen configuration
|                    |
|                    +----> Enhance with database function specifications
|                    |
|                    +----> Format market data summary for initial message
|                    |
|                    +----> Create specialized agents:
|                    |      - MarketAnalyst (always present)
|                    |      - RiskManager (always present)
|                    |      - TradingStrategist (always present)
|                    |      - TradingAdvisor (always present)
|                    |      - GlobalMarketAnalyst (if data available)
|                    |      - LiquidityAnalyst (if data available)
|                    |
|                    +----> Create moderator agent with appropriate instructions
|                    |
|                    +----> Prepare initial message with market overview
|                    |      including global market and liquidity data if available
|                    |
|                    +----> Setup group chat with all available agents
|                    |      in optimized interaction order
|                    |
|                    +----> Start conversation via moderator
|                    |
|                    +----> Save chat history
|                    |
|                    +----> Extract decision from chat history
|                    |      |
|                    |      +----> If no clear decision found, use fallback
|                    |
|                    +----> Format decision to ensure consistent structure
|                    |
|                    +----> Save full session data
|                    |
|                    +----> Track decision performance (if enabled)
|
+----> Return decision data
|
END
```

## Agent Roles and Responsibilities

1. **MarketAnalyst**
   - Specializes in technical analysis of cryptocurrency markets
   - Analyzes price action, volume, and technical indicators
   - Identifies patterns and trends in the market data
   - Provides a clear analysis of recent market behavior

2. **GlobalMarketAnalyst**
   - Provides macro-economic and global market context
   - Analyzes DXY movements, market indices, and crypto dominance metrics
   - Identifies correlations between crypto and traditional markets
   - Evaluates broader market conditions impacting cryptocurrency prices

3. **LiquidityAnalyst**
   - Specializes in analyzing market liquidity characteristics
   - Evaluates exchange flows, funding rates, and market depth
   - Analyzes futures basis and volume profiles
   - Provides insights on liquidity structure and optimal entry/exit points

4. **RiskManager**
   - Focuses on risk assessment and management
   - Evaluates volatility, liquidity, and potential downside
   - Provides a risk rating (low/medium/high) for potential trades
   - Recommends appropriate position sizing based on risk

5. **TradingStrategist**
   - Specializes in strategy development and evaluation
   - Identifies appropriate strategies for current market conditions
   - Defines specific entry/exit criteria and timeframes
   - Proposes clear strategies matching current conditions

6. **TradingAdvisor**
   - Synthesizes information from all other agents
   - Weighs different perspectives and analyses
   - Makes final trading recommendations
   - Formats decisions in consistent JSON structure

7. **Moderator** (UserProxyAgent)
   - Facilitates productive conversation between specialists
   - Guides agents through analysis process in logical order
   - Keeps conversation focused on decision-making goal
   - Does not add analysis but ensures proper collaboration

## Decision Format

The final decision is structured as a JSON object with the following fields:

```json
{
  "symbol": "BTCUSDT",         // Trading symbol
  "action": "BUY",             // Action: BUY, SELL, or HOLD
  "confidence": 75.0,          // Confidence level (0-100)
  "price": 88000.0,            // Current price at decision time
  "risk_level": "medium",      // Risk assessment: low, medium, high
  "reasoning": "Price is...",  // Explanation for the decision
  "timestamp": "2025-03-27..." // ISO timestamp of decision
}
```

## Integration with Performance Tracking

If performance tracking is enabled (`track_performance=True`), the decision session will:

1. Create a complete session data record containing:
   - Session ID and timestamp
   - Symbol and current price
   - Market data and technical indicators
   - Final decision with all attributes

2. Track the decision using the DecisionTracker:
   - Record is stored in SQLite database
   - Decision ID is generated for future reference
   - Market conditions are recorded for context

3. This tracked data enables:
   - Historical performance analysis
   - Agent behavior evaluation
   - Prompt optimization suggestions

## Simulated vs. Agent-Based Sessions

The system can operate in two modes:

### Simulated Session
- Used when AutoGen is not available
- Applies simple rule-based logic (primarily based on RSI)
- Provides basic decision-making capability without agent interaction
- Marked as "simulated" in decision data

### Agent-Based Session
- Uses full AutoGen multi-agent collaboration
- Provides rich analysis through specialized agents
- Enables more nuanced and comprehensive decisions
- Requires OpenAI API key to function

## Error Handling

The decision process includes several error handling mechanisms:

1. If symbol or price is missing, returns appropriate error message
2. If market data gathering fails, returns error status
3. If AutoGen is unavailable, falls back to simulated session
4. If no clear decision is extracted, uses fallback default decision
5. Catches and logs all exceptions during the process

## Implementation

The main implementation of this algorithm is in the `DecisionSession` class in `orchestration/decision_session.py`. Key methods include:

- `__init__()`: Initializes the session with configuration and market data
- `run_session()`: Main entry point that orchestrates the decision process
- `_gather_market_data()`: Collects and organizes market data for analysis
- `_run_agent_session()`: Manages the agent-based decision process
- `_run_simulated_session()`: Provides rule-based decisions when needed
- `_extract_decision()`: Parses decision from agent conversation