# Binance Integration Technical Documentation

## Implementation Details

The aGENtrader v2 system integrates with Binance API for real-time and historical cryptocurrency market data. This document provides technical details for developers working on the codebase.

## Core Components

### 1. BinanceDataProvider (`binance_data_provider.py`)

This is the direct interface to Binance API with comprehensive handling for:
- Authentication with API keys
- Regional restrictions (451 errors)
- Rate limiting compliance
- Testnet/mainnet switching based on environment
- Symbol format conversion

```python
from binance_data_provider import BinanceDataProvider

# Create with API keys from environment variables
provider = BinanceDataProvider()

# Or explicitly specify testnet/mainnet mode
provider_testnet = BinanceDataProvider(use_testnet=True)
provider_mainnet = BinanceDataProvider(use_testnet=False)
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `fetch_ohlcv()` | Fetches candlestick data with flexible interval and limit options |
| `get_current_price()` | Gets the latest price for a symbol |
| `fetch_market_depth()` | Gets order book with specified depth |
| `fetch_futures_open_interest()` | Gets futures open interest data with fallbacks |

### 2. MarketDataProviderFactory (`market_data_provider_factory.py`)

Factory class that provides data provider selection and automatic fallbacks:
- Attempts Binance first, falls back to CoinAPI if available
- Handles various error conditions gracefully
- Ensures standardized data formats regardless of provider

```python
from market_data_provider_factory import MarketDataProviderFactory

factory = MarketDataProviderFactory()

# Get either Binance or CoinAPI provider based on availability
provider = factory.get_provider(preferred="binance")

# Or use helper methods that automatically handle provider selection
candles = factory.fetch_ohlcv("BTC/USDT", interval="4h")
```

## Data Format Standardization

All data providers implement consistent formats for interoperability:

### OHLCV Data Format

```json
[
  {
    "timestamp": 1620000000000,  
    "open": 50000.0,
    "high": 51000.0,
    "low": 49000.0,
    "close": 50500.0,
    "volume": 1200.5
  },
  ...
]
```

### Market Depth Format

```json
{
  "timestamp": 1620000000000,
  "bids": [[50000.0, 1.5], [49900.0, 2.3], ...],
  "asks": [[50100.0, 1.2], [50200.0, 3.1], ...],
  "bid_total": 230500.0,
  "ask_total": 245600.0
}
```

## Geographic Restriction Handling

The system implements multiple strategies to handle geographic API restrictions:

1. **Automatic Testnet Fallback**: When 451 errors are detected, the system falls back to testnet in development mode

2. **Environment-Based Configuration**:
   - `DEPLOY_ENV=dev`: Defaults to testnet
   - `DEPLOY_ENV=prod`: Attempts mainnet with fallback to testnet

3. **Error Detection and Reporting**:
   - Specific detection of 451 error codes
   - Clear logging of geographic restriction issues
   - Graceful fallback to alternative data sources

## Testing and Validation

Use the provided test script to verify API functionality:

```bash
# Test both testnet and mainnet connections
python test_binance_api.py
```

The test script (`test_binance_api.py`) will:
1. Test connectivity to testnet and mainnet
2. Fetch market data from both sources if available
3. Provide a detailed test summary report

## Implementation Notes

### Symbol Format Handling

The system handles both exchange-specific and standard symbol formats:
- Exchange format: "BTCUSDT" (without separator)
- Standard format: "BTC/USDT" (with separator)

All provider methods accept either format:

```python
# These are equivalent
provider.get_current_price("BTC/USDT")
provider.get_current_price("BTCUSDT")
```

### Error Handling Philosophy

The data providers follow a "fail gracefully" philosophy:
- Invalid symbols return empty data structures rather than exceptions
- Network errors are logged and appropriate fallbacks are attempted
- Clear error messages identify the specific issue

### Rate Limiting

The BinanceDataProvider implements time-based rate limiting to avoid API restrictions:
- Rate limiting is handled automatically
- Requests are spaced to comply with Binance's limits