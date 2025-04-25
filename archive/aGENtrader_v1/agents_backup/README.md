# AutoGen Database Integration

This module provides tools for integrating AutoGen agents with SQL database access, specifically optimized for cryptocurrency market data analysis. The implementation allows AutoGen agents to directly query and analyze market data through specially designed database retrieval functions.

## Components

### 1. Database Retrieval Tool (`database_retrieval_tool.py`)

A specialized tool for accessing market data stored in SQL databases. This module:
- Handles database connections and query execution
- Provides functions for common market data queries (latest prices, historical data, technical indicators)
- Includes built-in serialization for complex data types (datetime, Decimal)

### 2. AutoGen DB Integration (`autogen_db_integration.py`)

Integrates the database retrieval functionality with AutoGen agents by:
- Registering database access functions with AutoGen agents
- Providing a standardized function map for different query types
- Managing serialization of database results for agent consumption
- Handling error cases and validation

### 3. Market Data Manager (`market_data_manager.py`)

Manages access to market data with functions for:
- Retrieving real-time and historical price data
- Calculating technical indicators
- Performing time-series analysis
- Converting data to formats suitable for agent analysis

## Setup and Usage

### Prerequisites

1. A properly configured SQL database with market data tables
2. Access to the OpenAI API (with API key configured)
3. Required Python packages: `pyautogen`, `sqlalchemy`, `pandas`

### Basic Usage

```python
import os
from agents.autogen_db_integration import AutoGenDBIntegration
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

# Setup OpenAI API
os.environ["OPENAI_API_KEY"] = "your-api-key"
config_list = [
    {
        "model": "gpt-4",
        "api_key": os.environ.get("OPENAI_API_KEY")
    }
]

# Initialize the DB integration
db_integration = AutoGenDBIntegration()

# Create AutoGen agents with database access
market_analyst = AssistantAgent(
    name="market_analyst",
    system_message="You are a market analyst specializing in cryptocurrency analysis.",
    llm_config={
        "config_list": config_list,
        "function_map": db_integration.get_function_map()
    }
)

user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="TERMINATE",
    code_execution_config={"work_dir": "coding"}
)

# Start a conversation with database access
user_proxy.initiate_chat(
    market_analyst,
    message="Analyze the recent price trends for BTCUSDT using the latest market data."
)
```

## Data Retrieval Functions

The database retrieval tool provides these functions:

### 1. `get_latest_price(symbol: str)`

Retrieves the most recent price data for a given symbol.

```python
# Example usage by an agent
latest_price = get_latest_price("BTCUSDT")
serialized_price = serialize_results(latest_price)
print(serialized_price)
```

### 2. `get_price_history(symbol: str, interval: str, start_time: str, end_time: str, limit: int = 100)`

Retrieves historical price data for a symbol within a time range.

```python
# Example usage by an agent
history = get_price_history("BTCUSDT", "1h", "2025-03-18T00:00:00", "2025-03-25T00:00:00")
serialized_history = serialize_results(history)
print(serialized_history)
```

### 3. `get_moving_averages(symbol: str, interval: str, start_time: str, end_time: str, limit: int = 20)`

Calculates moving averages for a symbol within a time range.

```python
# Example usage by an agent
mas = get_moving_averages("BTCUSDT", "1h", "2025-03-18T00:00:00", "2025-03-25T00:00:00")
serialized_mas = serialize_results(mas)
print(serialized_mas)
```

### 4. `get_volume_analysis(symbol: str, interval: str, start_time: str, end_time: str, limit: int = 20)`

Analyzes trading volume for a symbol within a time range.

### 5. `get_support_resistance(symbol: str, interval: str, start_time: str, end_time: str)`

Identifies support and resistance levels for a symbol.

### 6. `get_available_symbols()`

Lists all available trading symbols in the database.

## Data Serialization

The system includes a robust serialization mechanism for handling complex data types:

```python
from datetime import datetime
from decimal import Decimal
from agents.database_retrieval_tool import serialize_results

# Data with complex types from database
data = {
    "symbol": "BTCUSDT",
    "timestamp": datetime.now(),
    "price": Decimal("87245.38"),
    "volume": Decimal("1532.45")
}

# Serialize for agent consumption
serialized_data = serialize_results(data)
print(serialized_data)
```

For more details on the serialization system, see [Serialization Documentation](../docs/serialization_system.md).

## Error Handling

The database retrieval tool includes comprehensive error handling:

1. **Database Connection Errors**: Gracefully handled with informative error messages
2. **Query Errors**: Properly logged with context about the failed query
3. **Data Type Errors**: Automatically handled by the serialization system
4. **Missing Data**: Returns empty results with appropriate structure rather than failing

## Example Agent Conversation

```
User: Analyze the recent price movements of BTCUSDT.

Market Analyst: I'll analyze the recent price movements for BTCUSDT.

First, let me get the latest price and some historical data.

```python
# Get latest price
latest_price = get_latest_price("BTCUSDT")
latest_price_data = serialize_results(latest_price)

# Get price history for the past week (hourly)
import datetime
end_time = datetime.datetime.now().isoformat()
start_time = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
price_history = get_price_history("BTCUSDT", "1h", start_time, end_time)
price_history_data = serialize_results(price_history)

# Get moving averages
moving_averages = get_moving_averages("BTCUSDT", "1h", start_time, end_time)
ma_data = serialize_results(moving_averages)

# Analyze the data
import json
latest = json.loads(latest_price_data)
history = json.loads(price_history_data)
mas = json.loads(ma_data)

# Print summary
print(f"Latest price: ${latest['price']:.2f}")
```

Latest price: $87245.38

Based on analyzing the hourly data from the past week, I can see that BTCUSDT has been in an upward trend with an increase of approximately 3.2% over the past 7 days.

The current price of $87,245.38 is above both the 20-hour moving average ($86,789.23) and the 50-hour moving average ($85,432.12), indicating bullish momentum in the short term.

Key observations:
1. The price has formed a strong support level around $85,000
2. There's resistance at approximately $88,000
3. Volume has been increasing on up-days, confirming buying pressure
4. RSI is at 62.75, showing strength but not yet overbought

Would you like me to perform a more detailed technical analysis or focus on a specific indicator?
```

## Additional Features

- **Caching**: Frequently accessed data is cached to improve performance
- **Rate Limiting**: Built-in protection against excessive database queries
- **Type Validation**: Input parameters are validated before executing queries
- **Logging**: Comprehensive logging for debugging and monitoring

## License

This project is licensed under the MIT License - see the LICENSE file for details.