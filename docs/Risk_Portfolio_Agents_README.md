# Risk and Portfolio Management Agents Documentation

This document provides detailed information about the RiskGuardAgent and PortfolioManagerAgent components of the aGENtrader v0.2.2 system.

## Overview

These two agents work together to provide risk assessment, portfolio management, and trading safety constraints for the aGENtrader system:

- **RiskGuardAgent**: Evaluates market conditions and trade decisions against risk management policies, adjusting trades when necessary to maintain safety constraints.
- **PortfolioManagerAgent**: Manages portfolio allocation, tracks open positions, validates trades against exposure limits, and provides portfolio state information for decision-making.

Together, these agents form a risk management layer that protects the trading system from excessive risk and ensures adherence to predefined risk management policies.

## RiskGuardAgent

### Purpose

The RiskGuardAgent serves as a safety mechanism within the aGENtrader system, assessing various risk factors and modifying or rejecting trade decisions that exceed acceptable risk thresholds.

### Key Functions

1. **Market Risk Assessment**
   - Evaluates volatility, volume trends, and liquidity metrics
   - Assigns risk levels: LOW, MEDIUM, HIGH, or EXTREME
   - Identifies specific risk factors (e.g., high volatility, volume anomalies)

2. **Position Risk Assessment**
   - Evaluates trade size relative to portfolio value
   - Checks exposure limits (total and per-asset)
   - Assesses impact on portfolio diversification

3. **Drawdown Risk Assessment**
   - Analyzes stop loss placement
   - Tracks cumulative daily drawdown
   - Prevents excessive daily losses

4. **Trade Plan Adjustment**
   - Modifies position sizes based on risk level
   - Adjusts stop loss placement for better risk management
   - Can override trade decisions in extreme risk conditions

### Usage

The RiskGuardAgent can be used in two primary ways:

1. **Direct Risk Assessment**:
   ```python
   risk_guard = RiskGuardAgent()
   market_risk = risk_guard.evaluate_market_risk(market_data)
   position_risk = risk_guard.evaluate_position_risk(trade_plan, portfolio_data)
   drawdown_risk = risk_guard.evaluate_drawdown_risk(trade_plan)
   ```

2. **Trade Plan Adjustment**:
   ```python
   risk_guard = RiskGuardAgent()
   result = risk_guard.run(
       trade_plan=trade_plan,
       market_data=market_data,
       portfolio_data=portfolio_data
   )
   adjusted_trade_plan = result.get('adjusted_trade_plan', {})
   ```

3. **BaseAnalystAgent Interface**:
   ```python
   risk_guard = RiskGuardAgent()
   analysis = risk_guard.analyze(symbol="BTC/USDT", market_data=market_data)
   # analysis contains signal, confidence, and reasoning
   ```

### Configuration

The RiskGuardAgent can be configured through the settings.yaml file in the config directory. Default values are used if the configuration is not provided.

```yaml
risk_guard:
  max_risk_per_trade_pct: 2.0
  max_daily_drawdown_pct: 5.0
  max_position_size_pct: 10.0
  volatility_multiplier: 1.5
```

## PortfolioManagerAgent

### Purpose

The PortfolioManagerAgent tracks portfolio allocations, open positions, and manages exposure risk for the aGENtrader system. It validates trades against risk limits and maintains the state of the trading portfolio.

### Key Functions

1. **Portfolio State Tracking**
   - Maintains current balances and holdings
   - Tracks open positions and their values
   - Calculates total portfolio value and exposure percentages

2. **Trade Validation**
   - Validates trades against portfolio limits
   - Ensures compliance with maximum exposure rules
   - Prevents excessive concentration in single assets

3. **Position Management**
   - Adds open positions to the portfolio
   - Processes closed trades and calculates realized profits/losses
   - Monitors stop loss and take profit levels

4. **Portfolio Analysis**
   - Provides detailed portfolio summaries
   - Analyzes asset allocations and exposure levels
   - Generates recommendations based on portfolio state

### Usage

The PortfolioManagerAgent can be used in the following ways:

1. **Portfolio State Monitoring**:
   ```python
   portfolio_manager = PortfolioManagerAgent()
   summary = portfolio_manager.get_portfolio_summary()
   portfolio_value = portfolio_manager.get_portfolio_value()
   total_exposure = portfolio_manager.get_total_exposure_pct()
   ```

2. **Trade Processing**:
   ```python
   portfolio_manager = PortfolioManagerAgent()
   validation = portfolio_manager.validate_trade(trade)
   result = portfolio_manager.run(trade_data=trade)
   ```

3. **Portfolio Analysis**:
   ```python
   portfolio_manager = PortfolioManagerAgent()
   analysis = portfolio_manager.analyze()
   # analysis contains portfolio state and recommendations
   ```

4. **State Persistence**:
   ```python
   portfolio_manager = PortfolioManagerAgent()
   # Save state
   portfolio_manager.save_portfolio_state()
   # Load state
   portfolio_manager.load_portfolio_state()
   ```

### Configuration

The PortfolioManagerAgent can be configured through the settings.yaml file in the config directory:

```yaml
portfolio_manager:
  base_currency: "USDT"
  max_total_exposure_pct: 85
  max_per_asset_exposure_pct: 35
  max_open_trades: 10
  snapshot_interval_minutes: 60
```

## Integration with Decision Pipeline

These agents integrate into the aGENtrader decision pipeline as follows:

1. **Analyst agents** (Technical, Sentiment, etc.) generate market analysis
2. **DecisionAgent** aggregates analyst signals and produces a trade decision
3. **TradePlanAgent** creates a detailed trade plan based on the decision
4. **RiskGuardAgent** assesses and adjusts the trade plan according to risk policies
5. **PortfolioManagerAgent** validates and executes the adjusted trade
6. **ToneAgent** generates a human-like styled summary of the entire process

This pipeline ensures that all trades comply with risk management policies and portfolio constraints, maintaining system safety.

## Benefits

Integrating these risk management agents provides several key benefits:

1. **Prevents Excessive Risk**: Automatically adjusts or rejects trades that present unacceptable levels of risk
2. **Portfolio Protection**: Maintains portfolio diversification and prevents overexposure to any single asset
3. **Systematic Risk Management**: Applies consistent risk management policies across all trading decisions
4. **Drawdown Control**: Limits daily losses and prevents cascade failures during market volatility
5. **Decision Enhancement**: Provides additional context for trading decisions through portfolio analysis

## Example Use Case

Consider a scenario where the technical analysis signals a BUY for BTC/USDT, but with high market volatility:

1. **DecisionAgent** generates a BUY signal with 75% confidence
2. **TradePlanAgent** creates a trade plan with a specific position size
3. **RiskGuardAgent** detects high volatility risk and adjusts the position size downward by 50%
4. **PortfolioManagerAgent** validates the adjusted trade against portfolio limits
5. **The adjusted trade is executed with reduced risk exposure**

This process ensures that the system capitalizes on the trading opportunity while managing risk appropriately for the current market conditions.

## Testing

A test script is provided in `tests/test_risk_portfolio_agents.py` to verify the functionality of both agents and their integration. Run this script to ensure proper operation:

```bash
python tests/test_risk_portfolio_agents.py
```

## Future Enhancements

Potential future enhancements for these agents include:

1. **Machine Learning Risk Models**: Implementing ML-based risk assessment for more adaptive risk management
2. **Additional Risk Metrics**: Incorporating VaR (Value at Risk), correlation measures, and tail risk assessments
3. **Scenario Analysis**: Adding stress testing and scenario-based risk assessment
4. **Historical Performance Analysis**: Enhancing portfolio analysis with historical performance metrics
5. **Dynamic Risk Thresholds**: Automatically adjusting risk thresholds based on market conditions and system performance

## Troubleshooting

Common issues and solutions:

1. **Missing Configuration**: If the config/settings.yaml file is missing, default values will be used. Create the file with appropriate values for better customization.
2. **Portfolio State Issues**: If portfolio state seems incorrect, try resetting it with `portfolio_manager._load_existing_trades()`.
3. **Risk Assessment Errors**: Check that market data contains valid volatility, volume, and liquidity information.
4. **Integration Problems**: Ensure that trade plans from TradePlanAgent contain all required fields (symbol, signal, entry_price, position_size).