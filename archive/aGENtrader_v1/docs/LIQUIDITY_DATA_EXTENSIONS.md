# Liquidity Data Extensions

This document outlines the database extensions required to support liquidity analysis capabilities in the trading system.

## New Database Tables

The following tables will be added to the PostgreSQL database to store liquidity-related data:

### 1. exchange_flows

Stores data about cryptocurrency movements in and out of exchanges:

```sql
CREATE TABLE exchange_flows (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL, 
    exchange TEXT NOT NULL,
    inflow NUMERIC NOT NULL,
    outflow NUMERIC NOT NULL,
    net_flow NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, interval)
);
```

**Purpose:** Tracks the flow of assets into and out of exchanges, which can signal accumulation or distribution patterns.

### 2. funding_rates

Stores funding rate data from perpetual futures markets:

```sql
CREATE TABLE funding_rates (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    funding_rate NUMERIC NOT NULL,
    next_funding_time TIMESTAMP,
    predicted_rate NUMERIC,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, interval)
);
```

**Purpose:** Tracks the cost of holding perpetual futures positions, which can indicate market sentiment and potential price movements.

### 3. market_depth

Stores order book depth data:

```sql
CREATE TABLE market_depth (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    depth_level NUMERIC NOT NULL,
    bid_depth NUMERIC NOT NULL,
    ask_depth NUMERIC NOT NULL,
    bid_ask_ratio NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, depth_level, interval)
);
```

**Purpose:** Provides insight into market liquidity and potential support/resistance levels based on order book data.

### 4. futures_basis

Stores the price difference between futures and spot markets:

```sql
CREATE TABLE futures_basis (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    expiry_date TIMESTAMP,
    basis_points NUMERIC NOT NULL,
    annualized_basis NUMERIC NOT NULL,
    interval TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, contract_type, interval)
);
```

**Purpose:** Tracks the premium or discount of futures contracts, which can indicate market sentiment and institutional positioning.

### 5. volume_profile

Stores volume distribution across price levels:

```sql
CREATE TABLE volume_profile (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    price_level NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    is_buying BOOLEAN NOT NULL,
    interval TEXT NOT NULL,
    time_period TEXT NOT NULL,
    UNIQUE(timestamp, symbol, exchange, price_level, interval, time_period)
);
```

**Purpose:** Provides insight into which price levels have attracted the most trading activity, helping identify value areas and potential support/resistance.

## Data Types

The system will track the following types of liquidity data:

### Exchange Flows
- **Inflow**: Amount of cryptocurrency deposited to exchanges
- **Outflow**: Amount of cryptocurrency withdrawn from exchanges
- **Net Flow**: Net change in exchange balances (Inflow - Outflow)
- **Exchange-specific flows**: Broken down by major exchanges (Binance, Coinbase, etc.)

### Funding Rates
- **Current Rate**: The current funding rate
- **Historical Rates**: Past funding rates for trend analysis
- **Predicted Rate**: Estimated next funding rate
- **Rate Divergence**: Differences in rates across exchanges

### Market Depth
- **Bid Depth**: Total order volume on buy side at various price levels
- **Ask Depth**: Total order volume on sell side at various price levels
- **Bid/Ask Ratio**: Ratio between bid and ask depths
- **Depth Change**: Changes in order book depth over time

### Futures Basis
- **Current Basis**: Current price difference between futures and spot
- **Annualized Basis**: Basis expressed as annualized percentage
- **Term Structure**: Basis across different contract expirations
- **Basis Change**: Changes in basis over time

### Volume Profile
- **Volume by Price**: Trading volume at different price levels
- **Value Area**: Price range containing specified percentage of volume
- **Point of Control**: Price level with highest trading volume
- **Volume Delta**: Difference between buying and selling volume

## Data Access Functions

New functions will be added to access this data:

### 1. get_exchange_flows(symbol, exchange, interval, limit)

Retrieves recent exchange flow data for a specific cryptocurrency and exchange.

### 2. get_funding_rates(symbol, exchange, interval, limit)

Retrieves recent funding rate data for a specific cryptocurrency and exchange.

### 3. get_market_depth(symbol, exchange, depth_level, interval, limit)

Retrieves market depth data for a specific cryptocurrency, exchange, and depth level.

### 4. get_futures_basis(symbol, exchange, contract_type, interval, limit)

Retrieves futures basis data for a specific cryptocurrency, exchange, and contract type.

### 5. get_volume_profile(symbol, exchange, time_period, interval, limit)

Retrieves volume profile data for a specific cryptocurrency, exchange, and time period.

### 6. get_liquidity_summary(symbol, interval="1d")

Returns a comprehensive summary of liquidity conditions for a specific cryptocurrency.

## Data Update Process

A new process will be established to regularly update these liquidity metrics:

1. **Data Sources**:
   - Exchange APIs for flow data (Binance, Coinbase, etc.)
   - Futures exchange APIs for funding rates and basis
   - Order book APIs for market depth
   - Trade APIs for volume profile

2. **Update Frequency**:
   - Hourly updates for funding rates and exchange flows
   - More frequent updates (5-15 min) for market depth and volume

3. **Update Script**:
   - `update_liquidity_data.py` will be created to handle the updates
   - Will be scheduled to run at appropriate intervals

## Data Serialization

The existing serialization functions will be extended to handle these new data types, ensuring proper formatting for agent consumption.

## Historical Data Backfilling

To populate historical data, a separate process will:

1. Fetch available historical data from APIs
2. Clean and normalize the data
3. Insert into appropriate tables
4. Verify data integrity and completeness

This will be implemented in a dedicated script: `backfill_liquidity_data.py`