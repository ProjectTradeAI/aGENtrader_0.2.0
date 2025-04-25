# Position Sizer Agent Documentation

## Overview

The Position Sizer Agent is responsible for dynamically calculating optimal position sizes for each trade in the aGENtrader v2 system. It achieves this by considering both the confidence of the trading decision and the recent market volatility, allowing the system to take larger positions when conditions are favorable and reduce risk when conditions are uncertain.

This agent adds a crucial risk management dimension to the trading system, ensuring that position sizes are proportional to the quality of the trading opportunity.

## Core Functionality

The Position Sizer Agent provides the following key capabilities:

1. **Dynamic Position Sizing**: Calculates position sizes based on decision confidence and market volatility.

2. **Confidence-Based Scaling**: Allocates larger positions to high-confidence trading signals.

3. **Volatility Adjustment**: Reduces position sizes during high-volatility market conditions to manage risk.

4. **Min/Max Constraints**: Enforces configurable minimum and maximum position size limits.

5. **Transparent Calculation**: Provides clear explanation of position sizing rationale and calculation.

6. **Position Sizing Logging**: Records all position sizing decisions for performance analysis.

## Calculation Methodology

The core position sizing formula is:

```
position_size = (base_position_usdt * confidence_factor) / volatility_factor
```

Where:

- **base_position_usdt**: The baseline position size (default: 1000 USDT)
- **confidence_factor**: A multiplier derived from trading decision confidence (0-1 range)
- **volatility_factor**: A divisor derived from recent market volatility

This formula ensures that:
- Higher confidence leads to proportionally larger positions
- Higher volatility leads to proportionally smaller positions

### Confidence Factor Calculation

The confidence factor is derived from the decision confidence score:

```python
confidence_factor = confidence * confidence_multiplier
```

This factor is capped between 0.1 and 1.0 to prevent extreme position sizes.

### Volatility Factor Calculation

The volatility factor is calculated from recent price volatility:

```python
volatility_factor = math.pow(capped_volatility / 2, volatility_sensitivity)
```

Where:
- **capped_volatility**: The market volatility percentage, capped between configurable min/max values
- **volatility_sensitivity**: A parameter that controls how strongly volatility affects position sizing

This factor is also constrained to be at least 0.1 to prevent division by very small numbers.

## Configuration

The Position Sizer Agent is configured through the `settings.yaml` file:

```yaml
position_sizing:
  enabled: true
  base_position_usdt: 1000
  min_position_usdt: 100
  max_position_usdt: 5000
  confidence_multiplier: 1.0
  volatility_lookback_period: 24h
  max_volatility_cap: 10.0
  min_volatility_floor: 0.5
  volatility_sensitivity: 1.0
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `enabled` | Enables/disables dynamic position sizing | `true` |
| `base_position_usdt` | Base position size in USDT | `1000` |
| `min_position_usdt` | Minimum position size in USDT | `100` |
| `max_position_usdt` | Maximum position size in USDT | `5000` |
| `confidence_multiplier` | Multiplier for confidence factor | `1.0` |
| `volatility_lookback_period` | Period for volatility calculation | `24h` |
| `max_volatility_cap` | Maximum volatility percentage to consider | `10.0` |
| `min_volatility_floor` | Minimum volatility percentage to consider | `0.5` |
| `volatility_sensitivity` | How strongly volatility affects sizing | `1.0` |

## Integration with Trading Pipeline

The Position Sizer Agent is integrated into the trading pipeline after the risk assessment phase but before trade execution:

1. DecisionAgent generates a trading decision with confidence score
2. PortfolioManagerAgent validates the trade against portfolio risk limits
3. RiskGuardAgent performs risk assessment of market conditions
4. PositionSizerAgent calculates the optimal position size
5. TradeExecutorAgent executes the trade with the calculated position size

## Position Sizing Log

The Position Sizer Agent logs all position sizing decisions to `aGENtrader_v2/logs/position_sizes.jsonl` with detailed information:

```json
{
  "timestamp": "2025-04-19T15:30:45.123456",
  "pair": "BTC/USDT",
  "action": "BUY",
  "position_size_usdt": 1250.0,
  "asset_quantity": 0.0147,
  "entry_price": 85000.0,
  "confidence": 80,
  "volatility_pct": 3.2,
  "confidence_factor": 0.8,
  "volatility_factor": 0.64
}
```

## Viewing Position Sizing Decisions

Use the `view_position_sizing.py` utility script to analyze position sizing decisions:

```bash
# View most recent position sizing decisions
python view_position_sizing.py

# Filter by trading pair
python view_position_sizing.py --pair BTC/USDT

# Filter by action type
python view_position_sizing.py --action BUY

# Filter by position size
python view_position_sizing.py --min-size 1000 --max-size 2000

# Show oldest decisions first
python view_position_sizing.py --sort oldest
```

## Testing

Test the PositionSizerAgent using the provided test script:

```bash
python test_position_sizer_agent.py
```

This test script validates:
- Basic position sizing under various conditions
- Effects of confidence and volatility on position sizes
- Integration with the TradeExecutorAgent

## Best Practices

1. **Tune Base Position Size**: Adjust the `base_position_usdt` parameter to align with your overall capital allocation strategy.

2. **Calibrate Min/Max Limits**: Set the min/max position size limits based on your risk tolerance and minimum viable trade sizes.

3. **Adjust Volatility Sensitivity**: Increase the `volatility_sensitivity` value to make position sizes more responsive to volatility changes.

4. **Review Position Logs**: Regularly analyze the position sizing logs to verify that the agent is operating as expected.

5. **Benchmark Performance**: Compare the performance of dynamically sized positions against fixed-size alternatives.

## Extension Opportunities

The PositionSizerAgent can be extended in several ways:

1. **Per-Asset Base Sizes**: Implement asset-specific base position sizes to account for different asset characteristics.

2. **Kelly Criterion Integration**: Incorporate the Kelly formula for optimal position sizing based on historical win/loss rates.

3. **Trend-Based Adjustments**: Modify position sizes based on trend strength or market regime.

4. **Portfolio-Aware Sizing**: Consider current portfolio allocations when determining position sizes to maintain balanced exposure.

5. **Machine Learning Optimization**: Train ML models to predict optimal position sizes based on historical performance data.