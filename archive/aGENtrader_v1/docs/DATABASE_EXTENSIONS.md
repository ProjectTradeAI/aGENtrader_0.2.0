# Database Extensions for Global Market Analysis

This document outlines the database extensions required to support global market analysis capabilities in the trading system.

## New Database Tables

The following tables will be added to the PostgreSQL database to store macro market indicators:

### 1. global_market_indicators

Stores key global market indicators:

```sql
CREATE TABLE global_market_indicators (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    indicator_name TEXT NOT NULL,
    value NUMERIC NOT NULL,
    source TEXT NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, indicator_name, interval)
);
```

**Purpose:** Stores general market indicators like DXY, S&P 500, VIX, etc.

### 2. crypto_market_metrics

Stores cryptocurrency market-wide metrics:

```sql
CREATE TABLE crypto_market_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    metric_name TEXT NOT NULL,
    value NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, metric_name, interval)
);
```

**Purpose:** Stores crypto-specific metrics like total market cap, volumes, etc.

### 3. dominance_metrics

Stores cryptocurrency dominance metrics:

```sql
CREATE TABLE dominance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    dominance_percentage NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, interval)
);
```

**Purpose:** Tracks relative dominance of major cryptocurrencies within the overall market.

### 4. market_correlations

Stores correlation data between different markets:

```sql
CREATE TABLE market_correlations (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    base_symbol TEXT NOT NULL,
    correlated_symbol TEXT NOT NULL,
    correlation_coefficient NUMERIC NOT NULL,
    period TEXT NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, base_symbol, correlated_symbol, period, interval)
);
```

**Purpose:** Tracks how different assets/indicators correlate with each other.

## Indicator Types

The system will track the following types of indicators:

### Global Market Indicators
- **DXY** (US Dollar Index)
- **SPX** (S&P 500 Index)
- **VIX** (Volatility Index)
- **GOLD** (Gold price)
- **BONDS** (Bond yields - 10Y Treasury)
- **FED_RATE** (Federal Reserve interest rate)

### Crypto Market Metrics
- **TOTAL_MCAP** (Total crypto market capitalization)
- **TOTAL1** (Total market cap excluding BTC)
- **TOTAL2** (Total market cap excluding BTC and ETH)
- **TOTAL_VOLUME** (Total 24h trading volume)
- **TOTAL_DEFI** (Total DeFi market capitalization)
- **TOTAL_STABLES** (Total stablecoin market capitalization)

### Dominance Metrics
- **BTC.D** (Bitcoin dominance)
- **ETH.D** (Ethereum dominance)
- **STABLES.D** (Stablecoins dominance)
- **ALTS.D** (Altcoins dominance)

### Market Correlations
- BTC-SPX (Bitcoin to S&P 500)
- BTC-GOLD (Bitcoin to Gold)
- BTC-DXY (Bitcoin to Dollar Index)
- ETH-BTC (Ethereum to Bitcoin)
- ALTS-BTC (Altcoins to Bitcoin)

## Data Access Functions

New functions will be added to `database_retrieval_tool.py` to access this data:

### 1. get_global_indicator(indicator_name, interval, limit)

Retrieves recent values for a specific global market indicator.

### 2. get_crypto_market_metric(metric_name, interval, limit)

Retrieves recent values for a specific cryptocurrency market metric.

### 3. get_dominance_data(symbol, interval, limit)

Retrieves dominance data for a specific cryptocurrency.

### 4. get_market_correlation(base_symbol, correlated_symbol, period, interval, limit)

Retrieves correlation data between two assets/indicators.

### 5. get_macro_market_summary(interval="1d", limit=30)

Returns a comprehensive summary of global market conditions.

## Data Update Process

A new process will be established to regularly update these indicators:

1. **Data Sources**:
   - APIs for global market data (Yahoo Finance, Alpha Vantage, etc.)
   - Cryptocurrency data APIs (CoinGecko, CoinMarketCap, etc.)

2. **Update Frequency**:
   - Daily updates for most indicators
   - Hourly updates for more volatile metrics (when available)

3. **Update Script**:
   - `update_global_market_data.py` will be created to handle the updates
   - Will be scheduled to run at regular intervals

## Data Serialization

The existing serialization functions will be extended to handle these new data types, ensuring proper formatting for agent consumption.