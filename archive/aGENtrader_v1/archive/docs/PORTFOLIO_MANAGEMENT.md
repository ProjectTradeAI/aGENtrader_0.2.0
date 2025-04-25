# Portfolio Management and Risk Analysis

This document provides an overview of the portfolio management and risk analysis features that have been added to the multi-agent trading system.

## Overview

The portfolio management and risk analysis components enhance the trading system with sophisticated position sizing algorithms, risk metrics, and portfolio optimization techniques. These components help ensure that trades are properly sized according to risk parameters, improving the overall risk-adjusted performance of the trading system.

## Core Components

### 1. Risk Analyzer

The `RiskAnalyzer` class in `agents/portfolio_management.py` provides a set of risk analysis tools, including:

- **Value at Risk (VaR)** - Calculates the potential loss of a position with a given confidence level based on historical volatility.
- **Maximum Position Size** - Calculates the maximum position size based on a defined risk per trade (e.g., 2% of portfolio) and stop loss level.
- **Kelly Criterion** - Calculates optimal position size based on win probability and risk:reward ratio.
- **Volatility-Adjusted Position Sizing** - Sizes positions based on asset volatility to maintain consistent risk levels.
- **Portfolio Risk Analysis** - Analyzes overall portfolio risk including concentration, diversification, and cash ratios.

### 2. Portfolio Manager

The `PortfolioManager` class in `agents/portfolio_management.py` builds on the risk analyzer to provide portfolio-level management, including:

- **Optimal Position Sizing** - Combines multiple sizing methods (risk-based, Kelly, volatility) for optimal trade sizing.
- **Position Adjustments** - Calculates position adjustments needed to reach target allocations.
- **Portfolio Optimization** - Recommends portfolio adjustments based on risk profiles (conservative, moderate, aggressive).

### 3. Risk Optimizer

The `RiskOptimizer` class in `orchestration/risk_optimizer.py` integrates risk analysis with the trading decision process:

- **Decision Enhancement** - Adds risk parameters (stop loss, take profit) to trading decisions.
- **Position Sizing** - Adds optimal position size calculations to decisions.
- **Portfolio Impact Analysis** - Analyzes how a potential trade would impact overall portfolio risk.

### 4. Integration with Paper Trading

The paper trading system (`agents/paper_trading.py`) has been enhanced to use risk management:

- Metadata support for trades (stop loss, take profit)
- Risk-optimized trade execution
- Position tracking with risk parameters

### 5. AutoGen Agent Integration

Two specialized agents have been added to the AutoGen-based multi-agent system:

- **Risk Analysis Agent** - Specialized in portfolio risk analysis and position sizing
- **Portfolio Manager Agent** - Specialized in portfolio allocation and optimization

## How to Use

### Basic Risk Analysis

```python
from agents.portfolio_management import RiskAnalyzer

# Create a risk analyzer with 2% risk tolerance
risk_analyzer = RiskAnalyzer(risk_tolerance=0.02)

# Calculate Value at Risk
var_result = risk_analyzer.calculate_value_at_risk(
    symbol="BTCUSDT",
    position_value=10000,  # Position value in quote currency
    lookback_days=30,
    interval="1h"
)
print(f"VaR (95%): ${var_result['value_at_risk']:.2f}")

# Calculate maximum position size
max_position = risk_analyzer.calculate_max_position_size(
    symbol="BTCUSDT",
    entry_price=60000,
    stop_loss=57000,  # 5% stop loss
    portfolio_value=100000
)
print(f"Max position size: ${max_position['max_position_size']:.2f}")
```

### Portfolio Optimization

```python
from agents.portfolio_management import PortfolioManager

# Create a portfolio manager
portfolio_manager = PortfolioManager(risk_tolerance=0.02)

# Current portfolio state
portfolio = {
    "cash_balance": 50000,
    "positions": [
        {
            "symbol": "BTCUSDT",
            "quantity": 0.5,
            "avg_price": 58000,
            "current_price": 60000,
            "value": 30000
        },
        {
            "symbol": "ETHUSDT",
            "quantity": 5,
            "avg_price": 3800,
            "current_price": 4000,
            "value": 20000
        }
    ],
    "total_equity": 100000
}

# Get portfolio optimization recommendations
optimization = portfolio_manager.optimize_portfolio(
    portfolio=portfolio,
    risk_profile="moderate"  # Options: conservative, moderate, aggressive
)

# Display recommendations
print(f"Current cash ratio: {optimization['current_cash_ratio']*100:.1f}%")
print(f"Target cash ratio: {optimization['target_cash_ratio']*100:.1f}%")
print("\nRecommendations:")
for rec in optimization["recommendations"]:
    print(f"- {rec['message']}")
```

### AutoGen Integration

To use the risk management agents in the AutoGen-based decision process:

```python
# Import agent definitions
from agents.portfolio_management import (
    risk_analysis_agent_definition,
    portfolio_manager_agent_definition
)

# Set up risk analysis agent
risk_analyst_agent = autogen.AssistantAgent(
    name="RiskAnalysisAgent",
    system_message=risk_analysis_agent_definition()["system_message"],
    llm_config={
        "config_list": openai_config["config_list"],
        "functions": risk_analysis_agent_definition()["functions"]
    }
)

# Set up portfolio manager agent
portfolio_manager_agent = autogen.AssistantAgent(
    name="PortfolioManagerAgent",
    system_message=portfolio_manager_agent_definition()["system_message"],
    llm_config={
        "config_list": openai_config["config_list"],
        "functions": portfolio_manager_agent_definition()["functions"]
    }
)

# Add agents to your group chat
groupchat = autogen.GroupChat(
    agents=[user_proxy, market_analyst, risk_analyst_agent, portfolio_manager_agent, strategist],
    messages=[]
)
```

### Risk-Optimized Paper Trading

To execute trades with risk optimization:

```python
from agents.paper_trading import PaperTradingSystem

# Create trading system
trading_system = PaperTradingSystem()

# Create a trading decision
decision = {
    "symbol": "BTCUSDT",
    "action": "buy",
    "entry_price": 60000,
    "confidence": 0.8,  # 80% confidence
    "stop_loss": 57000,  # 5% stop loss
    "take_profit": 66000  # 10% take profit
}

# Execute the decision with risk optimization
result = trading_system.execute_from_decision(
    decision=decision,
    use_risk_optimizer=True
)

# Check the results
if result["status"] == "success":
    print(f"Trade executed: {result['message']}")
    if "risk_optimization" in result:
        print(f"Stop Loss: ${result['risk_optimization']['stop_loss']}")
        print(f"Take Profit: ${result['risk_optimization']['take_profit']}")
else:
    print(f"Trade failed: {result['message']}")
```

## Testing

Two test scripts have been provided to demonstrate the risk management features:

1. **test_portfolio_risk_management.py** - Tests the basic risk analysis and portfolio management functions.
2. **test_risk_decision_agent.py** - Tests the integration of risk analysis agents in the AutoGen-based decision process.

To run the tests:

```bash
# Basic risk management test
python test_portfolio_risk_management.py --symbol BTCUSDT --risk_tolerance 0.02 --risk_profile moderate

# AutoGen integration test
python test_risk_decision_agent.py --symbol BTCUSDT --risk_tolerance 0.02
```

## Configuration Options

The risk management system offers several configuration options:

- **Risk Tolerance** - Percentage of portfolio to risk per trade (default: 2%)
- **Risk Profile** - Conservative, moderate, or aggressive allocation profile
- **Confidence Level** - Confidence level for VaR calculations (default: 95%)
- **Target Volatility** - Target daily volatility for volatility-adjusted sizing

These can be adjusted to match different trading styles and risk preferences.

## Extending the System

The risk management system is designed to be extensible. Additional risk metrics or position sizing algorithms can be added to the `RiskAnalyzer` and `PortfolioManager` classes.

To add a new risk metric:

1. Add the new method to the appropriate class in `agents/portfolio_management.py`
2. Add the corresponding function definition to the agent definition methods
3. Implement the function handler in `test_risk_decision_agent.py`

## Best Practices

- **Always use stop losses** - The risk management system relies on stop loss levels to calculate proper position sizes.
- **Diversify across assets** - The portfolio optimization functions work best with multiple positions.
- **Regularly rebalance** - Use the portfolio optimization recommendations regularly to keep risk levels balanced.
- **Adjust risk tolerance based on market conditions** - Lower risk tolerance in high-volatility markets.
- **Combine multiple sizing methods** - The system uses a weighted average of different methods for more robust sizing.