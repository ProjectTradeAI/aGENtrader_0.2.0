# Market Data Flow

This document details the market data flow in the trading system, focusing on how data is stored, processed, and provided to agents for analysis and decision-making.

## Process Overview

The market data flow encompasses the entire process from data collection to analysis and use in decision-making. It ensures that agents have access to high-quality, properly formatted market data for effective trading decisions.

## Detailed Algorithm

```
START
|
+----> Data Storage Layer
|      |
|      +----> PostgreSQL Database
|             |
|             +----> market_data table
|             |      - timestamp
|             |      - symbol
|             |      - open, high, low, close, volume
|             |      - interval (1m, 15m, 30m, 1h, 4h, 1d)
|             |
|             +----> historical_market_data table
|                    - timestamp
|                    - symbol
|                    - open, high, low, close, volume
|                    - interval
|
+----> Data Access Layer
|      |
|      +----> database_retrieval_tool.py
|             |
|             +----> get_recent_market_data(symbol, interval, limit)
|             |      |
|             |      +----> Retrieve recent price data
|             |      |
|             |      +----> Format and serialize data
|             |
|             +----> get_price_history(symbol, interval, start_time, end_time)
|             |      |
|             |      +----> Retrieve price history for time range
|             |      |
|             |      +----> Format and serialize data
|             |
|             +----> get_latest_price(symbol)
|             |      |
|             |      +----> Get most recent price data point
|             |      |
|             |      +----> Extract and return close price
|             |
|             +----> calculate_volatility(symbol, interval, period)
|             |      |
|             |      +----> Get price history
|             |      |
|             |      +----> Calculate return standard deviation
|             |      |
|             |      +----> Convert to annualized volatility
|             |
|             +----> get_technical_indicators(symbol, interval, indicators)
|                    |
|                    +----> Get price history
|                    |
|                    +----> Calculate requested indicators:
|                           - Moving averages (SMA, EMA)
|                           - Oscillators (RSI, MACD)
|                           - Volatility indicators (Bollinger Bands)
|                           - Volume indicators
|                    |
|                    +----> Format and serialize results
|
+----> Data Processing Layer
|      |
|      +----> market_data_processor.py
|             |
|             +----> preprocess_data(data)
|             |      |
|             |      +----> Handle missing values
|             |      |
|             |      +----> Convert data types
|             |      |
|             |      +----> Sort by timestamp
|             |
|             +----> calculate_derived_metrics(data)
|             |      |
|             |      +----> Calculate returns
|             |      |
|             |      +----> Calculate price changes
|             |      |
|             |      +----> Add timestamp features (hour, day, etc.)
|             |
|             +----> detect_patterns(data)
|             |      |
|             |      +----> Identify common chart patterns
|             |      |
|             |      +----> Detect support/resistance levels
|             |      |
|             |      +----> Find trend lines
|             |
|             +----> generate_market_summary(data)
|                    |
|                    +----> Summarize recent price action
|                    |
|                    +----> Identify key levels
|                    |
|                    +----> Describe overall trend
|
+----> Agent Integration Layer
|      |
|      +----> autogen_db_integration.py
|             |
|             +----> register_market_data_functions()
|             |      |
|             |      +----> Create function specifications
|             |      |
|             |      +----> Format for AutoGen compatibility
|             |
|             +----> create_market_data_tools()
|             |      |
|             |      +----> Define tool interface
|             |      |
|             |      +----> Connect to database functions
|             |
|             +----> format_market_data(data)
|                    |
|                    +----> Serialize complex data types
|                    |
|                    +----> Format for agent consumption
|                    |
|                    +----> Handle datetime and Decimal values
|
+----> Decision Support Layer
       |
       +----> decision_session.py
              |
              +----> _gather_market_data()
              |      |
              |      +----> Collect market data for symbol
              |      |
              |      +----> Process and format data
              |      |
              |      +----> Organize for agent consumption
              |
              +----> _format_market_summary()
                     |
                     +----> Create concise market overview
                     |
                     +----> Format for initial agent message
                     |
                     +----> Include key metrics and indicators
END
```

## Database Schema

The market data is stored in a PostgreSQL database with the following schema:

### market_data Table

Stores recent market data for active trading:

| Column    | Type      | Description                               |
|-----------|-----------|-------------------------------------------|
| id        | INTEGER   | Primary key                               |
| timestamp | TIMESTAMP | Timestamp of the data point               |
| symbol    | TEXT      | Trading symbol (e.g., "BTCUSDT")          |
| open      | NUMERIC   | Opening price                             |
| high      | NUMERIC   | Highest price during interval             |
| low       | NUMERIC   | Lowest price during interval              |
| close     | NUMERIC   | Closing price                             |
| volume    | NUMERIC   | Trading volume                            |
| interval  | TEXT      | Time interval (1m, 15m, 30m, 1h, 4h, 1d)  |

### historical_market_data Table

Stores historical market data for backtesting and analysis:

| Column    | Type      | Description                               |
|-----------|-----------|-------------------------------------------|
| id        | INTEGER   | Primary key                               |
| timestamp | TIMESTAMP | Timestamp of the data point               |
| symbol    | TEXT      | Trading symbol (e.g., "BTCUSDT")          |
| open      | NUMERIC   | Opening price                             |
| high      | NUMERIC   | Highest price during interval             |
| low       | NUMERIC   | Lowest price during interval              |
| close     | NUMERIC   | Closing price                             |
| volume    | NUMERIC   | Trading volume                            |
| interval  | TEXT      | Time interval (1m, 15m, 30m, 1h, 4h, 1d)  |

## Data Retrieval Functions

The system provides several key functions for retrieving and processing market data:

### get_recent_market_data(symbol, interval, limit)

Retrieves the most recent market data:

- **Inputs**:
  - `symbol`: Trading symbol (e.g., "BTCUSDT")
  - `interval`: Time interval (e.g., "1h")
  - `limit`: Number of records to retrieve

- **Output**:
  - Array of OHLCV data points with timestamps

- **Usage**:
  ```python
  recent_data = get_recent_market_data("BTCUSDT", "1h", 24)
  ```

### get_price_history(symbol, interval, start_time, end_time)

Retrieves historical price data for a specific time range:

- **Inputs**:
  - `symbol`: Trading symbol
  - `interval`: Time interval
  - `start_time`: Start of time range (ISO format)
  - `end_time`: End of time range (ISO format)

- **Output**:
  - Array of OHLCV data points with timestamps

- **Usage**:
  ```python
  history = get_price_history(
      "BTCUSDT",
      "1d",
      "2025-03-01T00:00:00",
      "2025-03-27T00:00:00"
  )
  ```

### get_latest_price(symbol)

Gets the most recent price for a symbol:

- **Inputs**:
  - `symbol`: Trading symbol

- **Output**:
  - Current price (numeric)

- **Usage**:
  ```python
  current_price = get_latest_price("BTCUSDT")
  ```

### calculate_volatility(symbol, interval, period)

Calculates price volatility over a specific period:

- **Inputs**:
  - `symbol`: Trading symbol
  - `interval`: Time interval
  - `period`: Number of intervals to analyze

- **Output**:
  - Volatility value (standard deviation of returns)
  - Annualized volatility

- **Usage**:
  ```python
  volatility = calculate_volatility("BTCUSDT", "1d", 30)
  ```

### get_technical_indicators(symbol, interval, indicators)

Calculates technical indicators for a symbol:

- **Inputs**:
  - `symbol`: Trading symbol
  - `interval`: Time interval
  - `indicators`: List of indicators to calculate

- **Output**:
  - Dictionary of indicator values

- **Usage**:
  ```python
  indicators = get_technical_indicators(
      "BTCUSDT",
      "4h",
      ["sma_20", "rsi_14", "bollinger_20_2"]
  )
  ```

## Data Serialization

The system includes specialized serialization for market data:

### 1. Datetime Handling

Converts Python `datetime` objects to ISO format strings:

```python
def serialize_datetime(dt):
    """Convert datetime to ISO format string"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt
```

### 2. Decimal Handling

Converts Python `Decimal` objects to floats for JSON compatibility:

```python
def serialize_decimal(dec):
    """Convert Decimal to float"""
    if isinstance(dec, Decimal):
        return float(dec)
    return dec
```

### 3. Market Data Serialization

Formats market data for agent consumption:

```python
def format_market_data(data):
    """Format market data for agent consumption"""
    if isinstance(data, list):
        return [format_market_data(item) for item in data]
    elif isinstance(data, dict):
        return {k: format_market_data(v) for k, v in data.items()}
    elif isinstance(data, datetime):
        return serialize_datetime(data)
    elif isinstance(data, Decimal):
        return serialize_decimal(data)
    return data
```

## AutoGen Integration

The market data functions are integrated with AutoGen through function specifications:

### 1. Function Registration

Market data functions are registered with AutoGen:

```python
def register_market_data_functions():
    """Register market data functions with AutoGen"""
    function_map = {
        "get_recent_market_data": get_recent_market_data,
        "get_price_history": get_price_history,
        "get_latest_price": get_latest_price,
        "calculate_volatility": calculate_volatility,
        "get_technical_indicators": get_technical_indicators
    }
    
    function_specs = [
        {
            "name": "get_recent_market_data",
            "description": "Get recent market data for a symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "interval": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["symbol"]
            }
        },
        # Additional function specifications...
    ]
    
    return function_map, function_specs
```

### 2. Agent Usage

Agents can access market data through registered functions:

```
As a Market Analyst, I need to examine recent price action.

I'll use the get_recent_market_data function to retrieve historical data.

get_recent_market_data(symbol="BTCUSDT", interval="1h", limit=24)

Based on this data, I can see that Bitcoin has been in an uptrend over the past 24 hours with significant volume on the upward moves...
```

## Implementation

The main implementation of this algorithm is in:

- `agents/database_retrieval_tool.py`: Contains the database access functions
- `agents/autogen_db_integration.py`: Provides AutoGen integration
- `utils/market_data_processor.py`: Contains data processing functions
- `orchestration/decision_session.py`: Uses market data in decision process

Key methods include:

- `get_recent_market_data()`: Retrieves recent market data
- `get_price_history()`: Retrieves historical price data
- `calculate_volatility()`: Calculates price volatility
- `format_market_data()`: Serializes market data for agent use
- `register_market_data_functions()`: Registers functions with AutoGen
- `DecisionSession._gather_market_data()`: Gathers data for decision process