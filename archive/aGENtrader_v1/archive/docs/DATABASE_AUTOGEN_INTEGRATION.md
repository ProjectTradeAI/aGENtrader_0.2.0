# AutoGen Database Integration

This document outlines the integration of the PostgreSQL database with AutoGen agents for market data access.

## Overview

The AutoGen Database Integration provides agents with direct access to cryptocurrency market data stored in the PostgreSQL database. This solution serves as both a primary data source and a fallback mechanism when API access is limited or unavailable.

## Components

### 1. Market Data Query Functions

Located in `agents/query_market_data.py`, these functions provide formatted market data for AutoGen agents:

- `query_market_data(symbol, interval, limit, days, format_type)`: Retrieves historical price data
- `get_market_price(symbol)`: Gets the latest market price
- `get_market_analysis(symbol, interval, days, format_type)`: Performs basic market analysis

### 2. Function Registration Module

Located in `agents/register_market_data_functions.py`, this module registers the market data functions with AutoGen agents:

- `register_market_data_functions(agent)`: Registers functions with an agent
- `register_with_autogen()`: Returns a function mapping for AutoGen
- `create_function_mapping()`: Creates a JSON function configuration

## Usage with AutoGen

### Basic Integration

```python
import autogen
from agents.register_market_data_functions import register_market_data_functions

# Create your AutoGen agent
assistant = autogen.AssistantAgent(
    name="CryptoAnalyst",
    system_message="You are a cryptocurrency market analyst..."
)

# Register market data functions
register_market_data_functions(assistant)

# Now your agent can use the market data functions
```

### Example Conversation

```python
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="TERMINATE"
)

user_proxy.initiate_chat(
    assistant,
    message="What's the current price of Bitcoin and how has it been trending?"
)
```

### Agent Response Example

```
I'll check the current Bitcoin price and recent trends for you.

The current price of Bitcoin (BTCUSDT) is $88,081.87 as of my last data update.

Note: This data is from our database and is approximately 17 days old. 
The Alpaca API subscription tier doesn't currently allow access to real-time 
cryptocurrency data.

Here's the recent price trend (last 5 hours of available data):

Timestamp                  Open       High        Low      Close     Volume
---------------------------------------------------------------------------
2025-03-24 15:00:00    87961.90   88372.00   87678.06   88350.01    1848.33
2025-03-24 16:00:00    88350.01   88499.98   87690.59   88057.54    1817.54
2025-03-24 17:00:00    88057.53   88486.55   87941.06   88461.88    1471.11
2025-03-24 18:00:00    88461.88   88536.00   88123.11   88464.38     915.45
2025-03-24 19:00:00    88464.38   88508.00   87967.82   88081.87    1027.70

Based on this data, Bitcoin was showing moderate volatility with a slight 
upward trend before ending with a downturn in the last hour.
```

## Data Considerations

### Data Age

The current database contains cryptocurrency market data that is approximately 17 days old. This is due to limitations in the Alpaca API subscription tier (crypto_tier:0) which doesn't allow access to cryptocurrency market data endpoints.

### Data Quality

The data in the database is authentic historical market data with natural price variations. Verification has confirmed the data includes natural volatility and accurate price relationships.

### Upgrading to Real-Time Data

To access real-time cryptocurrency data, the Alpaca API subscription would need to be upgraded to a tier that includes cryptocurrency market data (crypto_tier > 0). Once upgraded, the system will automatically start using the API for real-time data without requiring code changes.

## Testing

### Direct Function Testing

You can test the market data functions directly without AutoGen:

```bash
python examples/test_market_data_functions.py
```

### AutoGen Integration Testing

To test with AutoGen (requires AutoGen to be installed):

```bash
python examples/autogen_database_integration.py
```

## Technical Details

### Function Parameters

#### query_market_data

- `symbol` (string): Trading symbol (e.g., 'BTCUSDT')
- `interval` (string): Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `limit` (integer): Number of data points to retrieve
- `days` (integer, optional): Number of days to look back
- `format_type` (string): Output format (json, markdown, text)

#### get_market_price

- `symbol` (string): Trading symbol (e.g., 'BTCUSDT')

#### get_market_analysis

- `symbol` (string): Trading symbol (e.g., 'BTCUSDT')
- `interval` (string): Time interval (1h, 4h, 1d)
- `days` (integer): Number of days to look back
- `format_type` (string): Output format (json, markdown, text)

### Database Schema

The market data is stored in tables with the following structure:

- `market_data`: Contains OHLCV (Open, High, Low, Close, Volume) data at various time intervals
- `symbols`: Contains information about available trading symbols

### Implementation Notes

- The system prioritizes data integrity, only using authentic market data
- Clear attribution of data source and age in all responses
- Graceful fallback between API and database sources
- Designed for seamless operation when API access is upgraded