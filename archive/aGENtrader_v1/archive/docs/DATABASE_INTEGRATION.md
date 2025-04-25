# AutoGen Database Integration

This document describes the integration between AutoGen agents and the SQL database for market data analysis.

## Overview

The database integration architecture enables AutoGen agents to:

1. Access real-time and historical market data directly from a PostgreSQL database
2. Perform technical analysis functions with optimized data structures
3. Identify market patterns and trends based on stored data
4. Collaborate effectively using a shared data source
5. Generate structured trading recommendations based on data analysis

## Architecture

The integration follows a modular approach with the following components:

```
┌─────────────────┐         ┌───────────────────┐         ┌────────────────┐
│  AutoGen Agents │ ◄─────► │  DB Retrieval Tool │ ◄─────► │  PostgreSQL DB │
└─────────────────┘         └───────────────────┘         └────────────────┘
        ▲                            ▲
        │                            │
        ▼                            ▼
┌─────────────────┐         ┌───────────────────┐
│ Trading Decisions│         │ Data Serialization│
└─────────────────┘         └───────────────────┘
```

### Key Components

1. **Database Retrieval Tool**: Provides functions to access market data with proper error handling and results formatting
2. **AutoGen Integration Layer**: Maps DB functions to AutoGen function calling format
3. **Serialization Utilities**: Handles proper serialization of complex data types like datetime and Decimal
4. **Technical Analysis Functions**: Implements common TA functions using database data

## Database Schema

The database contains the following key tables:

- `market_data`: Real-time market data with OHLCV information
- `historical_market_data`: Historical price and volume data with various intervals
- `technical_indicators`: Pre-calculated technical indicators

## Integration APIs

The integration provides the following primary functions:

### Market Data Access

- `get_latest_price(symbol)`: Retrieves the latest price for a specific trading pair
- `get_recent_market_data(symbol, limit)`: Gets the most recent N market data points
- `get_price_history(symbol, interval, days)`: Retrieves price history for a specified timeframe
- `get_market_data_range(symbol, start_time, end_time)`: Gets data within a specific time range

### Technical Analysis

- `calculate_moving_average(symbol, period)`: Calculates simple moving average
- `calculate_rsi(symbol, period)`: Calculates the Relative Strength Index
- `find_support_resistance(symbol)`: Identifies key support and resistance levels
- `detect_patterns(symbol)`: Detects common chart patterns in the price action

### Market Analysis

- `get_market_summary(symbol)`: Generates an overall market summary
- `calculate_volatility(symbol, days)`: Calculates market volatility metrics
- `identify_trend(symbol, interval)`: Identifies the current market trend

## Data Serialization

The integration handles special data types by using a custom JSON encoder:

```python
class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and Decimal objects"""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)
```

This ensures proper serialization between database results and AutoGen agent communications.

## Testing Framework

The integration is tested through several dedicated test scripts:

1. `test_db_basic.py`: Basic database connectivity tests
2. `test_db_retrieval_only.py`: Tests database retrieval without AutoGen
3. `test_database_retrieval_tool.py`: Tests the retrieval tool directly
4. `verify_market_data.py`: Verifies market data availability and accuracy
5. `test_autogen_db_integration.py`: Tests AutoGen integration with database
6. `test_collaborative_integration.py`: Tests collaborative agents with database

The test system is organized into shell scripts for easy execution:

- `run_db_test.sh`: Runs basic database tests
- `run_collaborative_integration.sh`: Tests agent collaboration with DB integration

## Example Usage

To test the database integration:

```bash
./run_db_test.sh --test retrieval --symbol BTCUSDT
```

To run collaborative agents with database integration:

```bash
./run_collaborative_integration.sh --symbol BTCUSDT --output-dir data/logs/integration_tests
```

## Data Flow

1. **Data Request**: AutoGen agent initiates a market data request
2. **Function Call**: Request is mapped to appropriate database function
3. **Database Query**: SQL query retrieves data from PostgreSQL
4. **Serialization**: Results are serialized to JSON with proper type handling
5. **Agent Processing**: Agent receives and processes the market data
6. **Collaborative Analysis**: Multiple agents collaborate using the shared data
7. **Decision Generation**: Agents generate trading decisions based on analysis

## Error Handling

The integration implements robust error handling:

- Database connection failures are gracefully handled with informative messages
- Query errors return structured error responses
- Data serialization errors are caught and reported
- Empty result sets are properly handled with appropriate status codes

## Performance Considerations

To ensure optimal performance:

1. Database connections are pooled for efficiency
2. Large result sets are paginated to avoid memory issues
3. Common technical indicators are pre-calculated where possible
4. Queries are optimized with appropriate indexes
5. JSON serialization is optimized for large datasets

## Available Market Data

The current integration supports BTCUSDT market data with the following specifications:

- Timeframe: 2024-03-20 to 2025-03-24
- Available intervals: 1m, 15m, 30m, 1h, 4h, daily
- Data points: ~6000 records
- Price range: $51,340.00 to $106,143.82

## Future Enhancements

Planned improvements to the database integration:

1. Support for additional trading pairs and markets
2. Real-time data updates with WebSocket integration
3. Advanced sentiment analysis integration
4. Machine learning model integration for predictive analytics
5. Enhanced caching layer for improved performance
6. Expanded technical indicator library