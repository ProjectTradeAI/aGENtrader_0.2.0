# Algorithm Diagrams

This directory contains detailed algorithm diagrams for the main components of the trading system. The diagrams are designed to provide a clear visual representation of how each process works.

## Available Diagrams

1. [Decision Making Process](decision_making_process.md)
2. [Performance Tracking Cycle](performance_tracking_cycle.md)
3. [Paper Trading Simulation](paper_trading_simulation.md)
4. [Agent Prompt Optimization](agent_prompt_optimization.md)
5. [Market Data Flow](market_data_flow.md)
6. [Global Market Analysis](global_market_analysis.md)
7. [Liquidity Analysis](liquidity_analysis.md)

## How to Read the Diagrams

Each diagram follows a standard flowchart notation:

- Rectangles represent processes or actions
- Diamonds represent decision points
- Arrows indicate the flow direction
- Databases are represented by cylinder shapes
- Dotted lines indicate optional flows
- Color coding is used to indicate related components

## Key Components Overview

### Decision Session

The Decision Session is the central orchestration mechanism that coordinates multi-agent interactions. It manages the conversation between specialized agents and extracts the final trading decision.

### Agent Framework

The Agent Framework provides infrastructure for specialized trading agents. Each agent has a specific role and expertise, contributing to the collaborative decision-making process.

### Performance Tracking

The Performance Tracking system records and analyzes agent decisions over time. It helps identify patterns, measure consistency, and generate prompt improvement suggestions.

### Paper Trading Simulation

The Paper Trading Simulation allows testing trading strategies with real market data without risking real assets. It simulates trade execution, portfolio management, and performance tracking.

### Market Data Management

The Market Data Management system handles the storage, retrieval, and processing of market data. It provides processed data to agents for analysis and decision-making.

## Integration Points

The diagrams highlight key integration points between different components of the system:

1. **Decision Session ↔ Performance Tracking**: Decisions are automatically tracked for analysis
2. **Performance Tracking ↔ Agent Prompt Optimization**: Performance data drives prompt improvements
3. **Decision Session ↔ Paper Trading**: Trading decisions flow into paper trading simulations
4. **Market Data ↔ Decision Session**: Market data provides the foundation for analysis
5. **Agent Framework ↔ Decision Session**: Agents collaborate within the session structure

## Implementation Details

For detailed implementation of these algorithms, refer to the corresponding code files:

- `orchestration/decision_session.py`: Main orchestration logic
- `utils/decision_tracker.py`: Performance tracking implementation
- `utils/agent_prompt_optimizer.py`: Prompt optimization logic
- `agents/paper_trading.py`: Paper trading simulation
- `agents/database_retrieval_tool.py`: Market data access functions