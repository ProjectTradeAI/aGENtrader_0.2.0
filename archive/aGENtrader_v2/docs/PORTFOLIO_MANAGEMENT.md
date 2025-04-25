# Portfolio Management in aGENtrader v2

## Overview

The Portfolio Manager Agent is a crucial component of the aGENtrader v2 system, responsible for tracking portfolio allocations, monitoring open positions, and enforcing risk management rules. This agent works in conjunction with the Trade Executor Agent to ensure that trading decisions adhere to predefined risk limits and portfolio diversification guidelines.

## Features

- **Portfolio Tracking**: Monitors asset allocations and balances across different cryptocurrencies
- **Risk Management**: Enforces limits on total exposure, per-asset exposure, and maximum open trades
- **Position Monitoring**: Tracks all open positions and their performance metrics
- **Trade Validation**: Validates new trades against portfolio constraints before execution
- **Portfolio Analysis**: Provides comprehensive portfolio analysis with recommendations

## Configuration

The Portfolio Manager Agent is configured in the `settings.yaml` file under the `portfolio_manager` section:

```yaml
portfolio_manager:
  enabled: true
  starting_balance: 10000
  base_currency: "USDT"
  max_total_exposure_pct: 80
  max_per_asset_exposure_pct: 40
  max_open_trades: 10
  snapshot_interval_minutes: 60
```

### Configuration Parameters

- **enabled**: Enable or disable portfolio management functionality
- **starting_balance**: Initial portfolio balance in base currency
- **base_currency**: Base currency for the portfolio (e.g., "USDT")
- **max_total_exposure_pct**: Maximum percentage of the portfolio that can be exposed to the market
- **max_per_asset_exposure_pct**: Maximum percentage of the portfolio that can be allocated to a single asset
- **max_open_trades**: Maximum number of open trades allowed at any time
- **snapshot_interval_minutes**: Interval for taking portfolio snapshots for historical tracking

## Integration with Trade Executor

The Portfolio Manager Agent works in conjunction with the Trade Executor Agent to:

1. Validate trades before execution
2. Track portfolio state after trades are executed
3. Monitor open positions and their performance

```
Decision Agent ----> Trade Executor ----> Portfolio Manager
                         |                       |
                         v                       v
                    Execute Trade          Update Portfolio
                         |                       |
                         v                       v
                    Monitor Trade        Enforce Risk Limits
```

## Usage Example

```python
# Initialize the agents
portfolio_manager = PortfolioManagerAgent()
trade_executor = TradeExecutorAgent()

# When processing a trading decision
decision = decision_agent.analyze(market_data)
if decision["action"] != "HOLD":
    # Validate the trade against portfolio limits
    trade = create_trade_from_decision(decision)
    validation = portfolio_manager.validate_trade(trade)
    
    if validation["status"] == "APPROVED":
        # Execute the trade
        result = trade_executor.process_trade(trade)
```

## Portfolio Analysis

The Portfolio Manager Agent provides comprehensive analysis of the current portfolio state, including:

- Total portfolio value
- Asset allocations and exposure levels
- Risk assessment
- Performance metrics
- Recommendations for portfolio adjustments

This analysis can be obtained by calling the `analyze()` method, which returns a dictionary with all the relevant information.

## Risk Management

Risk management is a core function of the Portfolio Manager Agent, which enforces:

1. Maximum total exposure limit (percentage of portfolio invested)
2. Maximum per-asset exposure limit (percentage in any single asset)
3. Maximum number of open trades

When these limits are reached, the agent will reject new trades until positions are closed or market conditions change.

## Open Positions

Open positions are tracked with detailed information:

- Entry price and timestamp
- Current price and value
- Unrealized PnL (absolute and percentage)
- Stop-loss and take-profit levels
- Position size and allocation percentage

## Portfolio Snapshots

The agent periodically takes snapshots of the portfolio state for historical tracking and analysis. These snapshots include:

- Timestamp
- Portfolio value
- Asset allocations
- Open positions
- Exposure levels

Snapshots are stored in the `portfolio_snapshots.jsonl` file for later analysis.