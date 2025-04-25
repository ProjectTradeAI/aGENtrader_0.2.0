# Trading System API Documentation

## Overview

This API provides access to the trading system's capabilities, including generating trading decisions, running backtests, and retrieving system status information.

## Base URL

When running locally: `http://localhost:5050`
When deployed to EC2: `http://<EC2_PUBLIC_IP>:5050`

## Authentication

Authentication is currently not implemented. In a production environment, proper API key authentication should be added.

## Endpoints

### Health Check

**Endpoint:** `GET /api/health`

**Description:** Checks if the API is running correctly.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-04-17T13:45:30.123Z"
}
```

### System Information

**Endpoint:** `GET /api/system`

**Description:** Retrieves information about the trading system.

**Response:**
```json
{
  "status": "ok",
  "system_info": {
    "version": "1.0.0",
    "uptime": "2h 15m",
    "python_version": "3.11.5",
    "components": [
      "decision_engine",
      "backtest_engine",
      "data_provider"
    ],
    "available_symbols": ["BTCUSDT", "ETHUSDT", "LTCUSDT"]
  }
}
```

### Generate Trading Decision

**Endpoint:** `POST /api/decision`

**Description:** Generates a trading decision for the specified symbol and timeframe.

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "analysis_type": "full"
}
```

**Parameters:**
- `symbol` (required): Trading symbol to analyze (e.g., "BTCUSDT")
- `interval` (optional): Time interval for analysis (default: "1h", options: "5m", "15m", "1h", "4h", "1d")
- `analysis_type` (optional): Type of analysis to perform (default: "full", options: "full", "technical", "fundamental")

**Response:**
```json
{
  "status": "success",
  "timestamp": "2025-04-17T14:30:45.789Z",
  "symbol": "BTCUSDT",
  "interval": "1h",
  "decision": {
    "action": "BUY",
    "confidence": 0.82,
    "entry_price": 98750.45,
    "stop_loss": 97500.00,
    "take_profit": 101000.00,
    "timeframe": "short-term",
    "reasoning": "Bullish pattern identified with strong support at $97,500",
    "analysis_summary": "Multiple technical indicators suggest upward momentum",
    "risk_assessment": {
      "risk_level": "moderate",
      "position_size_recommendation": "2% of portfolio",
      "market_conditions": "moderate volatility"
    }
  },
  "market_data": {
    "current_price": 98750.45,
    "24h_change_percent": 1.8,
    "24h_volume": 12500000000,
    "market_cap": 1950000000000
  }
}
```

### Run Backtest

**Endpoint:** `POST /api/backtest`

**Description:** Runs a backtest for the specified parameters.

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31", 
  "strategy": "default"
}
```

**Parameters:**
- `symbol` (required): Trading symbol to analyze (e.g., "BTCUSDT")
- `interval` (optional): Time interval for backtest (default: "1h", options: "5m", "15m", "1h", "4h", "1d")
- `start_date` (required): Start date for backtest in "YYYY-MM-DD" format
- `end_date` (required): End date for backtest in "YYYY-MM-DD" format
- `strategy` (optional): Strategy to use for backtest (default: "default")

**Response:**
```json
{
  "status": "success",
  "backtest_results": {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "strategy": "default",
    "performance": {
      "total_return": 28.5,
      "annualized_return": 124.2, 
      "max_drawdown": 12.4,
      "sharpe_ratio": 1.8,
      "win_rate": 62.5,
      "profit_factor": 2.1,
      "total_trades": 48,
      "profitable_trades": 30,
      "losing_trades": 18
    },
    "trades": [
      {
        "entry_time": "2025-01-15T09:00:00Z",
        "exit_time": "2025-01-17T14:00:00Z", 
        "entry_price": 85420.50,
        "exit_price": 87900.25,
        "direction": "LONG",
        "profit_percent": 2.9,
        "profit_absolute": 2479.75
      },
      // Additional trades...
    ],
    "equity_curve": [
      // Array of [timestamp, equity] points
    ]
  }
}
```

## Error Responses

**Standard Error Format:**
```json
{
  "status": "error",
  "message": "Description of the error",
  "error": "Error details or code"
}
```

**Common Error Codes:**
- 400: Bad Request - Missing required parameters
- 404: Not Found - Resource not found
- 500: Internal Server Error - Something went wrong on the server

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Monetary values are in USD unless otherwise specified
- This API is currently in development and may change without notice