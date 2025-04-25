# Market Data Solution

## Overview

This solution provides a robust system for accessing market data, designed to work with both Alpaca API and the local PostgreSQL database. It includes a graceful fallback mechanism that allows the system to continue functioning when API access is limited or unavailable.

## Components

### 1. Database Market Data Provider

Located in `utils/database_market_data.py`, this module provides direct access to market data stored in the PostgreSQL database. It includes functions for:

- Getting historical price data
- Retrieving the latest price
- Calculating market statistics
- Checking data age

### 2. Integrated Market Data Provider

Located in `utils/integrated_market_data.py`, this module provides a unified interface that attempts to use the Alpaca API first, then falls back to the database when needed. It handles error cases gracefully and provides clear source attribution.

### 3. AutoGen Query Functions

Located in `agents/query_market_data.py`, these functions are specifically designed to work with AutoGen agents. They provide formatted output in various formats (JSON, Markdown, text) suitable for different agent needs.

### 4. AutoGen Registration Functions

Located in `agents/register_market_data_functions.py`, these functions help register the market data query capabilities with AutoGen agents, making them available through the function calling API.

## Current Status

- **Database Connection**: ✅ Working correctly
- **Historical Data Access**: ✅ Successfully retrieving data
- **Latest Price Access**: ✅ Successfully retrieving latest price
- **Market Analysis**: ⚠️ Basic analysis working, but some advanced features limited due to data age
- **AutoGen Integration**: ✅ Functions defined and ready to use with AutoGen agents

## Data Age

The current data in the database is approximately 17 days old. This is due to limitations in the Alpaca API subscription level (crypto_tier:0) which doesn't allow access to cryptocurrency market data. The system is using historical database data as a fallback.

## Example Usage

### 1. Direct Module Access

```python
from utils.database_market_data import get_historical_data, get_latest_price

# Get the latest Bitcoin price
price = get_latest_price("BTCUSDT")
print(f"Latest BTC price: ${price}")

# Get historical data
history = get_historical_data("BTCUSDT", interval="1h", limit=24, format_type="dataframe")
print(history.head())
```

### 2. With AutoGen Agents

```python
from agents.register_market_data_functions import register_market_data_functions

# Set up your AutoGen agent
assistant = AssistantAgent(
    name="CryptoAdvisor",
    system_message="You are a cryptocurrency advisor...",
    llm_config={"function_map": {...}}
)

# Register market data functions with the agent
register_market_data_functions(assistant)

# Now your agent can use these functions
user_proxy.initiate_chat(
    assistant,
    message="What's the current price of Bitcoin and how has it been performing?"
)
```

## Testing

You can test the database access solution directly with:

```bash
python examples/test_market_data_functions.py
```

This will demonstrate the core functionality without requiring AutoGen to be installed.

## Upgrading to Real-Time Data

To access real-time cryptocurrency data, you would need to upgrade your Alpaca API subscription to a tier that includes cryptocurrency market data (crypto_tier > 0). Once upgraded, the system will automatically start using the API for real-time data without requiring any code changes.

## Implementation Details

The solution follows these design principles:

1. **Authentic Data Only**: Only real market data is used, never synthetic or placeholder data.
2. **Clear Source Attribution**: All data responses include information about the data source and age.
3. **Graceful Degradation**: The system continues to function with older data when real-time data is unavailable.
4. **User Notification**: Clear warnings are shown when data is outdated.
5. **Seamless Upgrade Path**: The system is designed to work with real-time data once API access is upgraded.

## Files

- `utils/database_market_data.py`: Core database access functions
- `utils/integrated_market_data.py`: Combined Alpaca API and database provider
- `agents/query_market_data.py`: AutoGen-specific query functions
- `agents/register_market_data_functions.py`: AutoGen function registration
- `examples/test_market_data_functions.py`: Simple test script
- `examples/autogen_database_integration.py`: Example AutoGen integration