# Risk Guard Agent Documentation

## Overview

The Risk Guard Agent serves as the final risk assessment checkpoint before trade execution in the aGENtrader v2 system. Its primary responsibility is to evaluate whether a proposed trade carries excessive risk based on market conditions and confidence metrics, vetoing high-risk trades before they can be executed.

The agent acts as a safety mechanism that complements the PortfolioManagerAgent by focusing on immediate market conditions and trade-specific risk factors rather than portfolio-level exposure concerns.

## Core Responsibilities

The Risk Guard Agent provides the following key functions:

1. **Comprehensive Risk Assessment**: Evaluates trades across multiple risk dimensions including volatility, liquidity, market movement, bid-ask spread, and confidence thresholds.

2. **Clear Approval/Rejection**: Provides binary decision-making with explicit "APPROVED" or "REJECTED" status for each trade.

3. **Detailed Rejection Logging**: Records rejected trades with comprehensive risk metrics to facilitate analysis of vetoed trades.

4. **Configurable Risk Thresholds**: Allows customization of acceptable risk parameters through the settings.yaml configuration.

## Risk Evaluation Metrics

The RiskGuardAgent evaluates trades based on these primary risk factors:

### 1. Volatility
- **Description**: Measures price fluctuations within a trading period
- **Calculation**: Typically calculated as (high - low) / close as a percentage
- **Default Threshold**: Maximum 5% volatility 
- **Rationale**: High volatility indicates unpredictable price movements and increased risk of rapid adverse moves

### 2. Liquidity
- **Description**: Measures market depth and ability to execute trades without significant price impact
- **Calculation**: Composite score (0-1) based on order book depth, trading volume, and bid-ask spread
- **Default Threshold**: Minimum 0.7 liquidity score
- **Rationale**: Low liquidity increases execution risk and potential slippage

### 3. Market Movement
- **Description**: Measures sudden price changes between trading periods
- **Calculation**: Absolute percentage change between consecutive periods
- **Default Threshold**: Maximum 3% movement
- **Rationale**: Sudden price jumps may indicate unstable market conditions

### 4. Bid-Ask Spread
- **Description**: Measures the gap between buying and selling prices
- **Calculation**: (ask - bid) / bid as a percentage
- **Default Threshold**: Maximum 1% spread
- **Rationale**: Wide spreads indicate poor liquidity and higher transaction costs

### 5. Confidence Level
- **Description**: Measures the algorithmic certainty in the trade recommendation
- **Calculation**: Confidence score directly from the decision agent (0-100%)
- **Default Threshold**: Minimum 65% confidence
- **Rationale**: Low confidence trades have higher uncertainty of success

## Configuration

The RiskGuardAgent is configured through the `settings.yaml` file:

```yaml
risk_guard:
  enabled: true
  max_volatility_pct: 5.0
  min_liquidity_score: 0.7
  min_confidence_threshold: 0.65
  max_market_movement_pct: 3.0
  max_spread_pct: 1.0
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `enabled` | Enables/disables the risk guard validation | `true` |
| `max_volatility_pct` | Maximum allowed volatility percentage | `5.0` |
| `min_liquidity_score` | Minimum required liquidity score (0-1) | `0.7` |
| `min_confidence_threshold` | Minimum required confidence level (0-1) | `0.65` |
| `max_market_movement_pct` | Maximum allowed recent market movement percentage | `3.0` |
| `max_spread_pct` | Maximum allowed bid-ask spread percentage | `1.0` |

## Integration

The RiskGuardAgent is integrated into the trade execution pipeline after portfolio validation but before actual trade execution:

1. TradeExecutorAgent receives a trade decision
2. PortfolioManagerAgent validates the trade against portfolio risk limits
3. RiskGuardAgent evaluates the trade's risk metrics
4. If approved, the trade proceeds to execution
5. If rejected, the trade is logged and execution is halted

## Rejection Logging

Rejected trades are logged to `aGENtrader_v2/logs/rejected_trades.jsonl` with detailed information:

```json
{
  "timestamp": "2025-04-19T14:32:10.123456",
  "pair": "BTC/USDT",
  "action": "BUY",
  "confidence": 75,
  "position_size": 0.1,
  "risk_metrics": {
    "volatility_pct": 6.5,
    "volatility_check": "FAILED",
    "liquidity_score": 0.8,
    "liquidity_check": "PASSED",
    "market_movement_pct": 1.2,
    "market_movement_check": "PASSED",
    "spread_pct": 0.4,
    "spread_check": "PASSED",
    "confidence_check": "PASSED"
  },
  "rejection_reason": "Volatility (6.50%) exceeds threshold (5.00%)"
}
```

## Viewing Rejected Trades

Use the `view_rejections.py` utility script to analyze rejected trades:

```bash
# View most recent rejections
python view_rejections.py

# Show detailed risk metrics
python view_rejections.py --detailed

# Filter by trading pair
python view_rejections.py --pair BTC/USDT

# Show oldest rejections first
python view_rejections.py --sort oldest
```

## Testing

Test the RiskGuardAgent using the provided test script:

```bash
python test_risk_guard_agent.py
```

This test script validates:
- Basic risk evaluation with various risk factors
- Integration with the TradeExecutorAgent
- Behavior with different risk thresholds

## Best Practices

1. **Calibrate Risk Thresholds**: Adjust thresholds based on asset volatility characteristics and market conditions.

2. **Analyze Rejections**: Regularly review rejected trades to identify patterns and refine risk parameters.

3. **Monitor False Positives**: Balance between rejecting truly risky trades and avoiding excessive rejections of potentially profitable trades.

4. **Market-Specific Settings**: Consider creating different risk profiles for different asset classes (e.g., higher volatility thresholds for altcoins vs. Bitcoin).

5. **Backtesting**: When adding new risk metrics, backtest against historical data to ensure they would have effectively identified risky trades.

## Extension Opportunities

The RiskGuardAgent can be extended in several ways:

1. **Asset-Specific Thresholds**: Implement per-asset risk thresholds to account for different volatility characteristics.

2. **Market Regime Detection**: Add intelligence to adjust thresholds based on detected market regimes (trending, ranging, volatile).

3. **Time-Based Risk Factors**: Incorporate time-of-day or market event calendar awareness to adjust risk tolerance.

4. **Machine Learning Risk Scoring**: Develop ML models to predict trade risk based on historical outcomes.

5. **Exchange-Specific Factors**: Add exchange health checks for additional risk evaluation.