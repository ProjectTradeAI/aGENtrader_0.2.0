# Binance API Integration Guide

## Overview

This document outlines the Binance API integration for the aGENtrader v2 trading system. The system uses Binance as its primary market data provider with fallbacks to ensure reliable data access regardless of geographic location.

## Setup Requirements

1. **API Keys**: You need Binance API keys to access market data
   - BINANCE_API_KEY - Your Binance API key
   - BINANCE_API_SECRET - Your Binance API secret

2. **Environment Variables**: Add these to your `.env` file:
   ```
   BINANCE_API_KEY=your_api_key_here
   BINANCE_API_SECRET=your_api_secret_here
   DEPLOY_ENV=dev  # Use 'prod' for production deployments
   ```

## Handling Geographic Restrictions

Binance blocks API access from certain regions (Error 451). Our system handles this in multiple ways:

1. **Testnet Fallback**: When geographic restrictions are detected, the system automatically falls back to the Binance testnet.
   - In development mode (`DEPLOY_ENV=dev`), testnet is used by default
   - In production mode (`DEPLOY_ENV=prod`), the system attempts mainnet first, then falls back

2. **VPN Recommendation**: For production systems in restricted regions, consider:
   - Deploying to EC2 instances in non-restricted regions
   - Using a proxy service (ensure compliance with Binance ToS)

## Testing API Access

Use the provided test script to verify connectivity:

```bash
python test_binance_api.py
```

The script tests both testnet and mainnet connections and reports detailed results.

## Integration Components

The Binance integration consists of:

1. **BinanceDataProvider**: Direct interface to Binance API with robust error handling
   - Located in `binance_data_provider.py`
   
2. **MarketDataProviderFactory**: Manages data provider selection and fallbacks
   - Located in `market_data_provider_factory.py`
   
3. **Test script**: Verifies connectivity to Binance APIs
   - Located in `test_binance_api.py`

## Using in the Trading System

The MarketDataProviderFactory abstracts away the complexity:

```python
from market_data_provider_factory import MarketDataProviderFactory

# Create factory
factory = MarketDataProviderFactory()

# Get current price
price = factory.get_current_price("BTC/USDT")

# Get OHLCV data
candles = factory.fetch_ohlcv("BTC/USDT", interval="4h", limit=50)

# Get market depth
depth = factory.fetch_market_depth("BTC/USDT")
```

## Troubleshooting

1. **451 Geographic Restriction Errors**:
   - Verify your EC2 region and consider alternatives
   - The system will log clear error messages when these occur
   
2. **API Key Issues**:
   - Ensure keys have proper permissions (read-only is sufficient for data access)
   - Verify keys are correctly stored in environment variables

3. **Testing**:
   - Run the test script regularly to verify API connectivity
   - The system will default to testnet in development environments