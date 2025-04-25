# API Response Schemas for aGENtrader v2

This document outlines the expected schema formats for various API responses used in the aGENtrader v2 system. These schemas are used for validation to ensure data integrity and consistency across the system.

## Schema Types

The system uses the following basic types for validation:

- `STRING`: A text string
- `NUMBER`: Any numeric value (integer or float)
- `INTEGER`: A whole number
- `FLOAT`: A floating-point number
- `BOOLEAN`: A boolean value (true/false)
- `ARRAY`: A list of values
- `OBJECT`: A dictionary/object with key-value pairs
- `NULL`: A null/None value
- `ISO8601_TIMESTAMP`: A timestamp in ISO 8601 format (e.g., "2025-04-20T12:00:00.0000000Z")

Multiple allowed types are indicated with a pipe character, e.g., `FLOAT|INTEGER`.

## OHLCV (Candle) Schema

This schema is used for validating Open-High-Low-Close-Volume candle data.

```json
{
    "time_period_start": "ISO8601_TIMESTAMP",
    "time_period_end": "ISO8601_TIMESTAMP",
    "time_open": "ISO8601_TIMESTAMP",
    "time_close": "ISO8601_TIMESTAMP",
    "price_open": "FLOAT|INTEGER",
    "price_high": "FLOAT|INTEGER",
    "price_low": "FLOAT|INTEGER",
    "price_close": "FLOAT|INTEGER",
    "volume_traded": "FLOAT|INTEGER",
    "trades_count": "INTEGER|NULL"
    // Note: symbol_id is optional in CoinAPI responses
}
```

## Ticker Schema

This schema is used for validating current price ticker data.

```json
{
    "symbol_id": "STRING",
    "time": "ISO8601_TIMESTAMP",
    "price": "FLOAT|INTEGER",
    "last_trade": "OBJECT|NULL",
    "volume_1h": "FLOAT|INTEGER|NULL",
    "volume_24h": "FLOAT|INTEGER|NULL",
    "price_change_pct_24h": "FLOAT|NULL"
}
```

## Order Book Schema

This schema is used for validating order book (market depth) data.

```json
{
    "symbol_id": "STRING",
    "time_exchange": "ISO8601_TIMESTAMP",
    "time_coinapi": "ISO8601_TIMESTAMP",
    "asks": "ARRAY",
    "bids": "ARRAY"
}
```

Each entry in the `asks` and `bids` arrays should have the following structure:

```json
{
    "price": "FLOAT|INTEGER",
    "size": "FLOAT|INTEGER"
}
```

## Market Event Schema

This schema is used for validating the comprehensive market events that combine multiple data types.

```json
{
    "type": "STRING",
    "symbol": "STRING",
    "timestamp": "STRING|ISO8601_TIMESTAMP",
    "ticker": "OBJECT|NULL",
    "ohlcv": "OBJECT|NULL",
    "orderbook": "OBJECT|NULL"
}
```

The nested `ticker`, `ohlcv`, and `orderbook` objects are validated against their respective schemas.

## Formatted Market Event

After processing through the aGENtrader v2 pipeline, market events are formatted with additional metadata:

```json
{
    "type": "market_update",
    "symbol": "BTC/USDT",
    "timestamp": "2025-04-20T12:00:00.0000000Z",
    "ticker": {
        "symbol": "BTC/USDT",
        "timestamp": "2025-04-20T12:00:00.0000000Z",
        "price": 50000.0,
        "bid": 49990.0,
        "ask": 50010.0,
        "bid_size": 1.5,
        "ask_size": 2.1
    },
    "ohlcv": {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "timestamp": "2025-04-20T12:00:00.0000000Z",
        "open": 49800.0,
        "high": 50200.0,
        "low": 49700.0,
        "close": 50000.0,
        "volume": 150.5
    },
    "orderbook": {
        "symbol": "BTC/USDT",
        "timestamp": "2025-04-20T12:00:00.0000000Z",
        "bids": [
            {"price": 49990.0, "size": 1.5},
            {"price": 49980.0, "size": 2.3},
            {"price": 49970.0, "size": 4.1}
        ],
        "asks": [
            {"price": 50010.0, "size": 2.1},
            {"price": 50020.0, "size": 3.4},
            {"price": 50030.0, "size": 5.0}
        ],
        "bid_total": 7.9,
        "ask_total": 10.5,
        "bid_ask_ratio": 0.75
    },
    "_meta": {
        "components": {
            "ticker": true,
            "ohlcv": true,
            "orderbook": true
        },
        "success": true,
        "errors": null,
        "source": "coinapi",
        "fetch_time": "2025-04-20T12:00:05.0000000Z"
    }
}
```

## Error Response Schema

When an API error occurs, a standardized error response is returned:

```json
{
    "type": "market_update_error",
    "symbol": "BTC/USDT",
    "timestamp": "2025-04-20T12:00:00.0000000Z",
    "error": "Error message describing what went wrong",
    "_meta": {
        "success": false,
        "source": "coinapi",
        "error_type": "DataFetchingError"
    }
}
```

## Validation Process

1. When data is received from an external API, it's first validated against these schemas
2. If validation passes, the data is processed normally
3. If validation fails:
   - The error is logged with detailed information
   - The invalid data is saved to a log file for inspection
   - A structured error response is returned
   - In some cases, the system may continue with partial data or fallback values

## Validation Options

The schema validation system supports the following options:

- `ignore_extra`: When `true`, extra fields in the data that aren't in the schema won't cause validation failures
- `partial`: When `true`, missing fields in the data that are in the schema won't cause validation failures

These options allow for flexibility in validation, especially when dealing with third-party APIs that may include additional fields or when only certain parts of the response are needed.

## Special Handling for Timestamp Formats

The ISO8601_TIMESTAMP validator has been enhanced to support various timestamp formats encountered in third-party APIs:

- Standard ISO8601: `2025-04-20T12:00:00Z`
- CoinAPI-specific format: `2025-04-20T12:00:00.0000000Z` (with trailing zeros)
- Formats with different precision in fractional seconds
- Formats with timezone offsets: `2025-04-20T12:00:00+00:00`

This ensures flexible validation of timestamp fields across different data sources and API responses.