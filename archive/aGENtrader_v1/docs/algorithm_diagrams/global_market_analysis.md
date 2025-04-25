# Global Market Analysis Algorithm

This document details the global market analysis process, focusing on how macro-economic and broader market indicators are incorporated into the trading decision framework.

## Process Overview

The global market analysis process analyzes macro-economic indicators, cryptocurrency market metrics, and inter-market correlations to provide a comprehensive context for trading decisions. This analysis is performed by the Global Market Analyst agent in collaboration with other specialized agents.

## Detailed Algorithm

```
START
|
+----> Gather Global Market Data
|      |
|      +----> Retrieve global market indicators
|      |      |
|      |      +----> Get DXY (US Dollar Index) data
|      |      |
|      |      +----> Get SPX (S&P 500) data
|      |      |
|      |      +----> Get VIX (Volatility Index) data
|      |      |
|      |      +----> Get other traditional market indicators
|      |
|      +----> Retrieve cryptocurrency market metrics
|      |      |
|      |      +----> Get total market capitalization
|      |      |
|      |      +----> Get altcoin market cap (TOTAL1)
|      |      |
|      |      +----> Get non-BTC/ETH market cap (TOTAL2)
|      |      |
|      |      +----> Get total trading volume
|      |
|      +----> Retrieve dominance metrics
|      |      |
|      |      +----> Get Bitcoin dominance
|      |      |
|      |      +----> Get Ethereum dominance
|      |      |
|      |      +----> Get stablecoin dominance
|      |
|      +----> Retrieve correlation data
|             |
|             +----> Get BTC-DXY correlation
|             |
|             +----> Get BTC-SPX correlation
|             |
|             +----> Get relevant inter-market correlations
|
+----> Process Global Market Data
|      |
|      +----> Calculate trends for each indicator
|      |      |
|      |      +----> Compare current values with historical averages
|      |      |
|      |      +----> Determine trend direction and strength
|      |
|      +----> Identify market state
|      |      |
|      |      +----> Assess if market is risk-on or risk-off
|      |      |
|      |      +----> Evaluate dollar strength influence
|      |      |
|      |      +----> Assess market sentiment indicators
|      |
|      +----> Detect sector rotation patterns
|      |      |
|      |      +----> Analyze shifts in dominance metrics
|      |      |
|      |      +----> Identify capital flow directions
|      |
|      +----> Evaluate correlation strengths
|             |
|             +----> Calculate correlation significance
|             |
|             +----> Identify changing correlation patterns
|
+----> Generate Market Context
|      |
|      +----> Formulate global market summary
|      |      |
|      |      +----> Describe overall market environment
|      |      |
|      |      +----> Highlight key indicator movements
|      |
|      +----> Develop crypto market structure analysis
|      |      |
|      |      +----> Assess market cap distribution
|      |      |
|      |      +----> Identify sector trends
|      |
|      +----> Map correlation influences
|      |      |
|      |      +----> Document primary correlation drivers
|      |      |
|      |      +----> Explain correlation implications
|      |
|      +----> Create macro outlook
|             |
|             +----> Project influence of macro factors
|             |
|             +----> Identify potential shifts or catalysts
|
+----> Integrate with Trading Decision Process
|      |
|      +----> Provide global context to specialized agents
|      |      |
|      |      +----> Share with MarketAnalyst
|      |      |
|      |      +----> Share with RiskManager
|      |      |
|      |      +----> Share with TradingStrategist
|      |
|      +----> Contribute to asset-specific analysis
|      |      |
|      |      +----> Apply global factors to target asset
|      |      |
|      |      +----> Identify specific correlation influences
|      |
|      +----> Inform risk assessment
|             |
|             +----> Highlight macro-level risks
|             |
|             +----> Provide global volatility context
|
END
```

## Data Sources and Metrics

The global market analysis relies on several key data sources and metrics:

### Global Market Indicators

1. **DXY (US Dollar Index)**
   - Tracks the strength of the US dollar against a basket of currencies
   - Typically shows inverse correlation with Bitcoin and crypto assets
   - Data points: current value, trend, rate of change

2. **SPX (S&P 500 Index)**
   - Represents the broader US equity market
   - Often shows correlation with crypto during risk-on/risk-off shifts
   - Data points: current value, trend, volatility

3. **VIX (Volatility Index)**
   - Measures expected market volatility
   - High VIX can signal market uncertainty and risk-off sentiment
   - Data points: current value, trend, historical percentile

4. **Bond Yields**
   - Indicators of monetary conditions and inflation expectations
   - Rising yields can pressure growth assets including crypto
   - Data points: 10-year treasury yield, yield curve shape

### Cryptocurrency Market Metrics

1. **Total Market Capitalization**
   - Overall size of the cryptocurrency market
   - Growth rate indicates new capital inflows or asset appreciation
   - Data points: current value, trend, growth rate

2. **TOTAL1 (Altcoin Market Cap)**
   - Total market cap excluding Bitcoin
   - Relative strength vs. BTC indicates altcoin market cycles
   - Data points: current value, trend, BTC ratio

3. **TOTAL2 (Non-BTC/ETH Market Cap)**
   - Market cap excluding Bitcoin and Ethereum
   - Strength indicates "alt season" or small-cap rotations
   - Data points: current value, trend, percentage of total

4. **Market Volumes**
   - Total trading activity across crypto markets
   - Volume trends provide insight into market participation
   - Data points: 24h volume, volume trends, volume by market segment

### Dominance Metrics

1. **Bitcoin Dominance (BTC.D)**
   - Bitcoin's percentage of total crypto market cap
   - Decreasing dominance often indicates altcoin rotation
   - Data points: current percentage, trend, historical context

2. **Ethereum Dominance (ETH.D)**
   - Ethereum's percentage of total crypto market cap
   - Indicates strength of the smart contract platform sector
   - Data points: current percentage, trend, BTC.D ratio

3. **Stablecoin Dominance (STABLES.D)**
   - Stablecoins' percentage of total crypto market cap
   - High values can indicate capital waiting on sidelines
   - Data points: current percentage, trend, velocity metrics

### Correlation Metrics

1. **BTC-DXY Correlation**
   - Relationship between Bitcoin and US Dollar Index
   - Historically negative correlation (-0.4 to -0.8 range)
   - Data points: coefficient, trend, significance

2. **BTC-SPX Correlation**
   - Relationship between Bitcoin and S&P 500
   - Positive during risk-on/risk-off environments
   - Data points: coefficient, trend, significance

3. **BTC-GOLD Correlation**
   - Relationship between Bitcoin and gold prices
   - Tests "digital gold" narrative in different conditions
   - Data points: coefficient, trend, significance

## Analysis Methods

The global market analysis employs several analytical methods:

### 1. Trend Analysis

- **Simple Moving Averages**: For identifying trend direction
- **Rate of Change**: For measuring momentum
- **Historical Percentiles**: For contextualizing current values

### 2. Correlation Analysis

- **Pearson Correlation Coefficient**: Measures linear relationship strength
- **Rolling Correlation**: Tracks correlation changes over time
- **Conditional Correlation**: Examines correlations under specific conditions

### 3. Market State Classification

- **Risk-On/Risk-Off Detection**: Based on multiple indicators
- **Regime Identification**: Market phase classification (accumulation, uptrend, distribution, downtrend)
- **Liquidity Assessment**: Analysis of global liquidity conditions

### 4. Sector Rotation Analysis

- **Dominance Ratio Analysis**: Examining shifts between asset classes
- **Flow Tracking**: Identifying capital movements between sectors
- **Relative Strength Comparison**: Measuring performance of sectors against benchmarks

## Integration with Decision Process

The global market analysis integrates with the decision-making process in several ways:

### 1. Initial Context Setting

The Global Market Analyst provides the first analysis in the agent conversation, establishing the macro context for all subsequent discussion:

```
[Moderator]: We need to make a trading decision for BTCUSDT. GlobalMarketAnalyst, please begin with macro analysis.

[GlobalMarketAnalyst]: Current market conditions show a weakening dollar (DXY -1.2% WoW) and rising risk appetite (SPX +0.8% WoW, VIX at 14.32). Total crypto market cap is in a bullish trend (+5.3% WoW) with Bitcoin dominance at 48.5% (-0.8% WoW), indicating modest capital rotation to altcoins. Key correlations remain consistent with BTC-DXY at -0.72 and BTC-SPX at +0.65. This represents a "risk-on" market environment that typically supports crypto asset appreciation.
```

### 2. Risk Factor Identification

The global analysis highlights specific macro risks to be considered:

```
[GlobalMarketAnalyst]: While the overall environment is supportive, three macro risk factors to monitor: (1) FOMC meeting next week could signal hawkish policy; (2) DXY is approaching technical support which could trigger a bounce; (3) SPX showing some divergence between price and volume, suggesting potential weakness.
```

### 3. Correlation-Based Position Sizing

The analysis informs position sizing based on correlation risks:

```
[RiskManager]: Based on the strong negative correlation with DXY (-0.72) identified by GlobalMarketAnalyst, we should consider the dollar as a primary risk factor. If taking a long BTC position, I recommend limiting position size to 2% of portfolio given potential volatility if DXY strengthens unexpectedly.
```

### 4. Strategy Selection

The market state helps determine appropriate trading strategies:

```
[TradingStrategist]: The "risk-on" environment identified by GlobalMarketAnalyst suggests trend-following strategies are more likely to succeed than counter-trend approaches. The weakening dollar trend supports a bullish bias for BTC, suggesting longer holding periods for trades.
```

## Example Output Format

The Global Market Analyst typically provides analysis in the following format:

```
## Global Market Summary
- DXY: 104.25 (-1.2% WoW) - BEARISH trend
- SPX: 5234.42 (+0.8% WoW) - BULLISH trend
- VIX: 14.32 (-5.1% WoW) - Low volatility environment
- 10Y Yield: 4.22% (+3bps WoW) - Modest upward pressure
- Market State: RISK-ON with weakening dollar

## Crypto Market Structure
- Total Market Cap: $2.46T (+5.3% WoW) - BULLISH trend
- BTC Dominance: 48.5% (-0.8% WoW) - Mild rotation to altcoins
- ETH Dominance: 16.8% (+0.3% WoW) - Slight outperformance
- Stablecoin Dominance: 7.2% (-0.5% WoW) - Capital deployment

## Key Correlations
- BTC-DXY: -0.72 (30d) - Strong negative correlation
- BTC-SPX: +0.65 (30d) - Strong positive correlation
- BTC-GOLD: +0.22 (30d) - Weak positive correlation

## Macro Outlook for BTC
The macro environment is currently supportive for Bitcoin with dollar weakness providing tailwinds. The risk-on sentiment in traditional markets is flowing into crypto assets. Based on current correlations, continued weakness in DXY would likely support BTC appreciation.

## Risk Assessment
- PRIMARY RISK: FOMC meeting next week could signal hawkish policy
- SECONDARY RISK: DXY approaching technical support level
- MONITORING: SPX showing divergence between price and volume
```

## Implementation

The main implementation of this algorithm is in:

- `agents/global_market_analyst.py`: Global Market Analyst agent
- `agents/global_market_data.py`: Global market data access functions
- `update_global_market_data.py`: Data update script

Key methods include:

- `get_global_indicator()`: Retrieves global market indicators
- `get_crypto_market_metric()`: Retrieves cryptocurrency market metrics
- `get_dominance_data()`: Retrieves dominance percentages
- `get_market_correlation()`: Retrieves correlation data
- `get_macro_market_summary()`: Generates market summary
- `GlobalMarketAnalyst.analyze_macro_conditions()`: Performs analysis