# Paper Trading System

The paper trading system is a module that allows the multi-agent trading system to execute simulated trades based on its decisions without risking real funds. This provides a way to test and evaluate the trading strategies and agent decision quality in a realistic but risk-free environment.

## Overview

The paper trading system is implemented in `agents/paper_trading.py` and consists of two main classes:

1. **PaperTradingAccount**: Manages a simulated trading account with balances, positions, and trade history.
2. **PaperTradingSystem**: Provides an interface for the multi-agent system to execute trades based on its decisions.

## Features

- Simulated trading with realistic execution mechanics
- Portfolio tracking with positions, balances, and equity
- Trade history recording and reporting
- Performance metrics calculation (returns, drawdowns, win rate)
- Integration with the multi-agent decision-making process
- Market data retrieval from the database for accurate pricing

## Usage

### Basic Usage

```python
from agents.paper_trading import PaperTradingSystem

# Initialize paper trading system
trading_system = PaperTradingSystem(
    data_dir="data/paper_trading",
    default_account_id="test_account",
    initial_balance=10000.0
)

# Execute a trade based on a decision
decision = {
    "action": "buy",
    "symbol": "BTCUSDT",
    "confidence": 80,
    "reasoning": "Strong support detected with increasing volume"
}

result = trading_system.execute_from_decision(decision)

# Get portfolio status
portfolio = trading_system.get_portfolio()
print(f"Total equity: ${portfolio['total_equity']}")
print(f"Cash balance: ${portfolio['cash_balance']}")

# Get trade history
trades = trading_system.get_trade_history()
for trade in trades:
    print(f"{trade['timestamp']}: {trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']}")

# Get performance metrics
metrics = trading_system.get_performance_metrics()
print(f"Returns: {metrics['returns']}%")
print(f"Max drawdown: {metrics['max_drawdown']}%")
print(f"Win rate: {metrics['win_rate']}%")
```

### Integration with Multi-Agent Decision Session

The paper trading system can be integrated with the existing agent decision session to execute trades based on agent recommendations:

```python
from orchestration.decision_session import DecisionSession
from agents.paper_trading import PaperTradingSystem

# Initialize paper trading system
trading_system = PaperTradingSystem(
    data_dir="data/paper_trading",
    default_account_id="agent_trading",
    initial_balance=10000.0
)

# Initialize decision session
decision_session = DecisionSession(
    symbol="BTCUSDT",
    session_id="trading_session_1",
    config_path="config/decision_session.json"
)

# Run decision session
result = decision_session.run_session()
decision = result.get("decision")

if decision:
    # Execute the decision
    execution_result = trading_system.execute_from_decision(decision)
    
    # Check execution result
    if execution_result["status"] == "success":
        trade = execution_result["trade"]
        print(f"Trade executed: {trade['side']} {trade['quantity']} {trade['symbol']} at ${trade['price']}")
    else:
        print(f"Trade failed: {execution_result['message']}")
```

## Testing and Simulation

The paper trading system includes several test scripts for validation and simulation:

1. **test_paper_trading.py**: Tests basic paper trading functionality and integration with agent decisions.
2. **test_trading_with_execution.py**: Tests the full trading system with agent decision making and paper trade execution.
3. **run_paper_trading_simulation.py**: Runs a complete paper trading simulation with multiple trading cycles.

### Running Tests

You can run the paper trading tests using the provided shell script:

```bash
# Run all paper trading tests
./run_paper_trading_tests.sh

# Run specific tests
./run_paper_trading_tests.sh --basic     # Run basic paper trading test
./run_paper_trading_tests.sh --agent     # Run paper trading with agent decisions
./run_paper_trading_tests.sh --integration  # Run integration test with decision session
./run_paper_trading_tests.sh --execution # Run trading with execution test
./run_paper_trading_tests.sh --simulation # Run paper trading simulation

# Run tests with a specific symbol
./run_paper_trading_tests.sh --symbol ETHUSDT
```

### Running Simulations

You can run a paper trading simulation with multiple trading cycles using the simulation script:

```bash
# Run a basic simulation
python run_paper_trading_simulation.py

# Customize the simulation
python run_paper_trading_simulation.py --symbol BTCUSDT --initial-balance 20000 --cycles 5 --cycle-interval 120
```

## Data Storage

The paper trading system stores account data, trades, and orders in JSON files in the specified data directory:

- **account.json**: Contains account balances, positions, and equity history.
- **trades.json**: Contains a record of all executed trades.
- **orders.json**: Contains a record of all orders, including pending orders.

Each simulation or test run creates a separate directory with these files to maintain isolation between different runs.

## Performance Metrics

The paper trading system calculates the following performance metrics:

- **Returns**: Percentage return on the initial account balance.
- **Max Drawdown**: Maximum percentage decline from a peak to a trough.
- **Win Rate**: Percentage of profitable trades.
- **Profit Factor**: Ratio of gross profits to gross losses.
- **Average Trade**: Average profit/loss per trade.

These metrics can be used to evaluate the performance of the trading strategy and the quality of the agent decisions.

## Future Enhancements

Potential future enhancements for the paper trading system include:

1. Support for limit and stop orders
2. More sophisticated position sizing based on risk management rules
3. Support for margin trading and leverage
4. Integration with external market data sources for more realistic backtesting
5. Enhanced visualization of trading performance and equity curves