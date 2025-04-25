# Binance API Integration

This document provides an overview of the Binance API integration in the aGENtrader v2 system.

## Overview

The Binance API has been implemented as the primary market data provider for the aGENtrader v2 system, with CoinAPI available as a fallback option.

Key components:
- `BinanceDataProvider`: Main class for interacting with Binance API
- `DataProviderFactory`: Factory pattern implementation for selecting and managing providers
- `DataProviderAdapter`: Adapter for backward compatibility with legacy code

## Setup

### API Keys

To use the Binance API integration, you'll need to set the following environment variables:

```
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
```

For public endpoints (price, OHLCV data), API keys are optional but recommended to avoid rate limiting.

### Configuration

The system is configured to use Binance as the primary data provider with CoinAPI as the fallback. This can be customized in `config/default.json`:

```json
"market_data": {
  "provider": "binance",
  "fallback": "coinapi",
  "retry_attempts": 3
}
```

## Usage

### Basic Example

Here's a basic example of using the Binance data provider:

```python
from aGENtrader_v2.data.feed.binance_data_provider import BinanceDataProvider

# Initialize the provider
provider = BinanceDataProvider()

# Get current price
price = provider.get_current_price("BTC/USDT")
print(f"BTC/USDT price: {price}")

# Get OHLCV data
ohlcv_data = provider.get_ohlcv("BTC/USDT", interval="1h", limit=10)
print(f"Retrieved {len(ohlcv_data)} OHLCV candles")
```

### Using the Factory Pattern

```python
from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory

# Create the factory with Binance as primary and CoinAPI as fallback
factory = DataProviderFactory(
    primary_provider="binance",
    fallback_provider="coinapi"
)

# Get data (will use Binance and fallback to CoinAPI if needed)
price = factory.get_current_price("BTC/USDT")
ohlcv_data = factory.get_ohlcv("BTC/USDT", interval="1h", limit=10)
```

### Legacy Compatibility

For existing code that expects the CoinAPIFetcher interface:

```python
from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory
from aGENtrader_v2.data.feed.provider_adapter import DataProviderAdapter

# Create the factory
factory = DataProviderFactory(primary_provider="binance")

# Wrap it in the adapter for backward compatibility
adapter = DataProviderAdapter(factory)

# Use the legacy interface
ohlcv_data = adapter.fetch_ohlcv("BTC/USDT", "1h", 10)
price_data = adapter.fetch_current_price("BTC/USDT")
```

## Testing

You can test the Binance integration using the provided scripts:

```bash
# Test basic functionality
./run_binance_test.sh

# Test with the TechnicalAnalystAgent
./run_binance_technical_test.py --symbol BTC/USDT --interval 1h

# Interactive wrapper with API key prompts
./run_binance_test_wrapper.sh
```

## Data Provider Methods

The Binance data provider supports the following methods:

- `get_current_price(symbol)`: Get the current price of a trading pair
- `get_ohlcv(symbol, interval, limit)`: Get OHLCV (candlestick) data
- `get_order_book(symbol, limit)`: Get the order book (market depth)
- `get_funding_rate(symbol)`: Get the current funding rate (futures only)
- `get_open_interest(symbol)`: Get the current open interest (futures only)
- `create_market_event(symbol)`: Create a comprehensive market event with multiple data points

## Error Handling

The implementation includes comprehensive error handling:

- Rate limit management with exponential backoff
- Automatic retries for transient errors
- Fallback to alternate provider when primary provider fails
- Detailed error logging and reporting

## Symbol Format

The system supports standard trading symbols in these formats:
- With slash: `BTC/USDT`
- With underscore: `BTC_USDT`
- Direct Binance format: `BTCUSDT`

These will all be automatically converted to the required format.

## Intervals

Supported time intervals:
- Minutes: `1m`, `3m`, `5m`, `15m`, `30m`
- Hours: `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- Days: `1d`, `3d`
- Other: `1w` (week), `1mo` (month)