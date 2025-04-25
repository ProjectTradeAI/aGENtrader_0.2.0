# System Architecture

This document provides a comprehensive overview of the trading system architecture, including key components, data flows, and integration points.

## System Components

The trading system consists of several integrated components:

1. **Agent Framework**: Specialized agents for market analysis and trading decisions
2. **Market Data System**: Database storage and retrieval of cryptocurrency market data
3. **Decision System**: Orchestration of agent collaboration for trading decisions
4. **Performance Tracking**: Tracking and analysis of agent decision quality
5. **Paper Trading Simulation**: Simulated trading for strategy testing
6. **Portfolio Management**: Risk-based position sizing and portfolio optimization

## Architecture Diagrams

Detailed algorithm diagrams for key system processes:

1. [Decision Making Process](docs/algorithm_diagrams/decision_making_process.md): How agents collaborate to make trading decisions
2. [Performance Tracking Cycle](docs/algorithm_diagrams/performance_tracking_cycle.md): How agent decisions are tracked and analyzed
3. [Paper Trading Simulation](docs/algorithm_diagrams/paper_trading_simulation.md): How trading strategies are tested
4. [Agent Prompt Optimization](docs/algorithm_diagrams/agent_prompt_optimization.md): How agent prompts are improved over time
5. [Market Data Flow](docs/algorithm_diagrams/market_data_flow.md): How market data is stored, processed, and used

## Component Integration

The system uses a modular architecture with well-defined integration points:

```
+--------------------+         +----------------------+
| Market Data System |<------->| Decision System      |
+--------------------+         +----------------------+
          ^                              ^
          |                              |
          v                              v
+--------------------+         +----------------------+
| Agent Framework    |<------->| Performance Tracking |
+--------------------+         +----------------------+
          ^                              ^
          |                              |
          v                              v
+--------------------+         +----------------------+
| Paper Trading      |<------->| Portfolio Management |
+--------------------+         +----------------------+
```

### Key Integration Points

1. **Market Data ↔ Decision System**
   - Decision system requests market data for analysis
   - Market data provides formatted data for agent consumption

2. **Decision System ↔ Agent Framework**
   - Decision system orchestrates agent collaboration
   - Agents provide specialized expertise for decisions

3. **Decision System ↔ Performance Tracking**
   - Decision system logs decisions for tracking
   - Performance tracking analyzes decision quality

4. **Agent Framework ↔ Performance Tracking**
   - Performance tracking analyzes agent behavior
   - Performance data drives agent prompt optimization

5. **Decision System ↔ Paper Trading**
   - Trading decisions flow into paper trading simulation
   - Simulation results provide feedback on decision quality

6. **Paper Trading ↔ Portfolio Management**
   - Portfolio management calculates position sizes
   - Paper trading executes simulated trades

## Database Schema

The system uses two main databases:

### 1. Market Data Database (PostgreSQL)

Stores cryptocurrency market data:

- `market_data`: Recent market data for active trading
- `historical_market_data`: Historical data for backtesting

### 2. Performance Tracking Database (SQLite)

Tracks agent decisions and performance:

- `decisions`: Trading decisions made by agents
- `outcomes`: Outcomes of trading decisions
- `performance_metrics`: Calculated performance metrics

## Agent Architecture

The system uses a multi-agent architecture with specialized roles:

1. **GlobalMarketAnalyst**: Macro-economic and global market analysis
2. **MarketAnalyst**: Technical analysis of cryptocurrency markets
3. **RiskManager**: Risk assessment and management
4. **TradingStrategist**: Strategy development and evaluation
5. **TradingAdvisor**: Decision synthesis and recommendation
6. **Moderator**: Conversation facilitation and coordination

Each agent has:
- Defined role and expertise
- Specialized system prompt
- Access to appropriate tools and functions
- Integration with performance tracking

### Global Market Analyst

The Global Market Analyst is a specialized agent responsible for analyzing macro-economic factors and global market conditions that may impact cryptocurrency prices. This agent provides critical context about broader market dynamics, including:

- Dollar strength (DXY) and its impact on crypto assets
- Overall crypto market capitalization trends
- Bitcoin dominance and sector rotation patterns
- Correlations between crypto and traditional markets
- Macro-economic risk factors

Adding this layer of analysis enhances decision quality by incorporating a wider range of factors beyond technical indicators specific to individual cryptocurrencies.

## Process Workflows

The system supports several key workflows:

### 1. Trading Decision Workflow

```
Market Data → Decision Session → Agent Collaboration → Trading Decision
```

### 2. Performance Tracking Workflow

```
Trading Decision → Decision Tracking → Outcome Tracking → Performance Analysis
```

### 3. Prompt Optimization Workflow

```
Performance Data → Pattern Analysis → Improvement Suggestions → Improved Prompts
```

### 4. Paper Trading Workflow

```
Trading Decision → Position Sizing → Trade Execution → Performance Monitoring
```

## Technology Stack

The system is built with:

- **Python**: Primary programming language
- **PostgreSQL**: Market data storage including global market indicators
- **SQLite**: Performance tracking database
- **AutoGen**: Multi-agent AI framework
- **NumPy/Pandas**: Data processing and analysis
- **OpenAI API**: Large language model integration
- **Financial Data APIs**: For global market indicators (DXY, SPX, etc.)
- **Crypto Market APIs**: For market cap and dominance metrics

## Implementation Structure

Key implementation files:

### Agent Framework
- `agents/trading_agents.py`: Agent definitions and configuration
- `agents/global_market_analyst.py`: Global Market Analyst agent
- `agents/autogen_db_integration.py`: Database integration for agents

### Market Data System
- `agents/database_retrieval_tool.py`: Database access functions
- `agents/global_market_data.py`: Global market data access functions
- `utils/market_data_processor.py`: Data processing utilities
- `update_global_market_data.py`: Script for updating global market data

### Decision System
- `orchestration/decision_session.py`: Decision session orchestration
- `orchestration/decision_session_updated.py`: Updated with Global Market Analyst integration
- `orchestration/agent_moderator.py`: Agent conversation moderation

### Performance Tracking
- `utils/decision_tracker.py`: Decision tracking and analysis
- `utils/agent_prompt_optimizer.py`: Agent prompt optimization

### Paper Trading
- `agents/paper_trading.py`: Paper trading simulation
- `agents/portfolio_management.py`: Portfolio management and risk control

### Testing and Analysis
- `analyze_agent_performance.py`: Performance analysis tool
- `optimize_agent_prompts.py`: Interactive prompt optimization tool
- `run_paper_trading_simulation.py`: Paper trading runner
- `test_global_market_analyst.py`: Tests for the Global Market Analyst

## Future Enhancements

Planned system enhancements:

1. **Enhanced Market Analysis**
   - Integration of sentiment analysis
   - Support for multi-timeframe analysis
   - Advanced pattern recognition

2. **Improved Agent Collaboration**
   - Formalized agent debate mechanism
   - Expanded agent specialization roles
   - Self-criticism and reflection capabilities

3. **Advanced Performance Tracking**
   - Fine-grained attribution of decision outcomes
   - Agent contribution analysis
   - Continuous learning framework

4. **Extended Risk Management**
   - Sophisticated risk modeling
   - Dynamic position sizing
   - Drawdown management strategies

5. **Portfolio Optimization**
   - Multi-asset portfolio management
   - Correlation-based position sizing
   - Rebalancing strategies

## Conclusion

The trading system architecture provides a robust framework for agent-based trading decisions with continuous performance improvement. The modular design allows for component evolution while maintaining system integrity. The detailed algorithm diagrams provide a clear understanding of key processes and their implementation.