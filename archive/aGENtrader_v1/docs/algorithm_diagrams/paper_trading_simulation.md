# Paper Trading Simulation

This document details the paper trading simulation process, which allows testing of trading strategies with real market data without risking actual assets.

## Process Overview

The paper trading simulation creates a virtual trading environment where strategies can be tested against historical or real-time market data. It tracks a simulated portfolio, executes trades based on agent decisions, and provides performance metrics.

## Detailed Algorithm

```
START
|
+----> Initialize paper trading simulation
|      |
|      +----> Set initial parameters:
|      |      - Starting balance
|      |      - Trading symbols
|      |      - Time period (for backtesting)
|      |      - Risk parameters
|      |
|      +----> Create portfolio object
|      |      |
|      |      +----> Set starting cash balance
|      |      |
|      |      +----> Initialize empty positions array
|      |      |
|      |      +----> Set performance tracking variables
|      |
|      +----> Connect to market data source
|      |
|      +----> Create trade executor
|      |
|      +----> Initialize performance tracker
|
+----> Configure simulation type
|      |
|      +----> Option 1: Backtesting
|      |      |
|      |      +----> Load historical market data for time period
|      |      |
|      |      +----> Set time progression mechanism
|      |
|      +----> Option 2: Forward testing
|             |
|             +----> Connect to real-time market data feed
|             |
|             +----> Set up data streaming mechanism
|
+----> Set up agent decision process
|      |
|      +----> Create DecisionSession
|      |
|      +----> Configure session parameters
|      |
|      +----> Connect to agent system
|
+----> Run simulation loop
|      |
|      +----> For each time step in simulation:
|             |
|             +----> Update market data
|             |
|             +----> Update portfolio values
|             |
|             +----> Get current prices
|             |
|             +----> [Decision Point] Check if decision is needed
|             |      |
|             |      +----> If YES, request agent decision
|             |      |      |
|             |      |      +----> Run DecisionSession
|             |      |      |
|             |      |      +----> Process decision result
|             |      |
|             |      +----> If NO, continue
|             |
|             +----> [Trade Execution] If decision requires action
|             |      |
|             |      +----> Calculate position size
|             |      |      |
|             |      |      +----> Consider risk parameters
|             |      |      |
|             |      |      +----> Consider portfolio balance
|             |      |      |
|             |      |      +----> Apply position sizing algorithm
|             |      |
|             |      +----> Execute paper trade
|             |             |
|             |             +----> Record trade details
|             |             |
|             |             +----> Update portfolio
|             |             |
|             |             +----> Calculate fees
|             |
|             +----> Update performance metrics
|                    |
|                    +----> Update portfolio value
|                    |
|                    +----> Calculate returns
|                    |
|                    +----> Update drawdown metrics
|                    |
|                    +----> Calculate risk metrics
|
+----> Generate simulation results
|      |
|      +----> Compile trading history
|      |
|      +----> Calculate performance summary
|      |      |
|      |      +----> Total return
|      |      |
|      |      +----> Risk-adjusted return
|      |      |
|      |      +----> Maximum drawdown
|      |      |
|      |      +----> Win/loss ratio
|      |      |
|      |      +----> Sharpe ratio
|      |
|      +----> Generate equity curve
|      |
|      +----> Create trade analysis report
|
END
```

## Simulation Types

The paper trading system supports two main simulation types:

### 1. Backtesting

- Uses historical market data from the database
- Processes data sequentially to simulate passage of time
- Allows testing strategies against known historical market behavior
- Configuration includes:
  - Start date and end date
  - Time step interval (e.g., 1h, 4h, 1d)
  - Initial portfolio balance

### 2. Forward Testing

- Uses real-time or near-real-time market data
- Executes simulation as new data becomes available
- Tests strategies under current market conditions
- Configuration includes:
  - Start date (usually present)
  - Update interval
  - Initial portfolio balance
  - Maximum run time

## Portfolio Management

The portfolio component tracks:

1. **Cash Balance**: Available funds not currently invested
2. **Positions**: Currently held assets
   - Symbol
   - Entry price
   - Quantity
   - Current value
   - Unrealized P&L
3. **Trade History**: Log of all executed trades
   - Timestamp
   - Symbol
   - Action (BUY/SELL)
   - Price
   - Quantity
   - Fees
   - Total value
4. **Performance Metrics**:
   - Total value (cash + positions)
   - Total return
   - Daily/weekly/monthly returns
   - Maximum drawdown
   - Volatility

## Position Sizing

Position sizing is a critical component determining how much to invest in each trade:

1. **Fixed Percentage**:
   - Invests a fixed percentage of portfolio in each trade
   - Simplest approach but doesn't account for volatility

2. **Risk-Based**:
   - Sets position size based on stop loss and risk tolerance
   - Example: Risk 1% of portfolio on each trade

3. **Volatility-Adjusted**:
   - Adjusts position size based on asset volatility
   - Higher volatility leads to smaller position size

4. **Portfolio Balance**:
   - Considers existing positions when sizing new ones
   - Aims to maintain appropriate diversification

## Trade Execution

The trade execution process involves:

1. **Decision Processing**:
   - Parse decision from agent system
   - Extract action, symbol, and confidence

2. **Order Creation**:
   - Determine order type (market, limit)
   - Calculate position size
   - Set entry price (current market price for simulation)

3. **Order Execution**:
   - Record order details
   - Update portfolio cash balance
   - Add new position or update existing one
   - Calculate and deduct simulated fees

4. **Order Confirmation**:
   - Log trade in trade history
   - Update portfolio metrics
   - Trigger any necessary follow-up actions

## Performance Analysis

The simulation generates detailed performance analysis:

1. **Equity Curve**:
   - Shows portfolio value over time
   - Indicates compounding effects

2. **Return Metrics**:
   - Absolute return
   - Annualized return
   - Risk-adjusted return (Sharpe ratio)
   - Maximum drawdown

3. **Trade Analysis**:
   - Win/loss ratio
   - Average winning trade
   - Average losing trade
   - Profit factor
   - Expectancy

4. **Risk Metrics**:
   - Portfolio volatility
   - Value at Risk (VaR)
   - Beta to market (for multi-asset simulations)

## Integration with Decision Session

The paper trading simulation integrates with the `DecisionSession` to get trading decisions:

```python
# Initialize simulation
simulation = PaperTradingSimulation(
    initial_balance=10000.0,
    symbols=["BTCUSDT"],
    risk_percentage=1.0  # Risk 1% per trade
)

# Initialize decision session
decision_session = DecisionSession(
    symbol="BTCUSDT",
    track_performance=True
)

# Main simulation loop
while simulation.is_running():
    # Update market data
    simulation.update_market_data()
    
    # Check if we need a new decision
    if simulation.needs_decision():
        # Run decision session
        decision = decision_session.run_session()
        
        # Process the decision
        simulation.process_decision(decision)
    
    # Update portfolio and performance metrics
    simulation.update_portfolio()
    
    # Move to next time step
    simulation.next_step()

# Generate final results
results = simulation.generate_results()
```

## Implementation

The main implementation of this algorithm is in:

- `agents/paper_trading.py`: Contains the `PaperTradingSimulation` class
- `agents/paper_trading_portfolio.py`: Contains the `Portfolio` class
- `agents/trade_executor.py`: Contains the `TradeExecutor` class

Key methods include:

- `PaperTradingSimulation.run_simulation()`: Main entry point for the simulation
- `PaperTradingSimulation.process_decision()`: Processes agent decisions
- `PaperTradingSimulation.execute_trade()`: Executes paper trades
- `Portfolio.update_positions()`: Updates position values
- `Portfolio.calculate_metrics()`: Calculates performance metrics
- `TradeExecutor.execute_order()`: Simulates order execution