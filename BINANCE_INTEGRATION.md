# Binance API Integration in aGENtrader v2

This document describes the Binance API integration in aGENtrader v2, including the environment-based API selection mechanism.

## Overview

The aGENtrader v2 system uses Binance as its primary market data provider with the following features:

1. Environment-aware endpoint selection (testnet vs mainnet)
2. Robust error handling and rate limiting
3. Full support for authenticated endpoints
4. Comprehensive market data retrieval
5. Fallback to alternative data sources when necessary

## Environment-Based API Selection

The system intelligently selects between Binance's testnet and mainnet APIs based on the deployment environment:

| Environment | Default API Endpoint | Purpose |
|-------------|---------------------|---------|
| `dev`       | Testnet             | Local development to avoid hitting real API limits |
| `replit`    | Testnet             | Development in Replit environment |
| `ec2`       | Mainnet             | Production deployment on EC2 |

## Configuration

The API selection is configured through environment variables in the `.env` file:

```
# Deployment Environment (dev, replit, ec2)
DEPLOY_ENV=dev

# Binance API Configuration
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_USE_TESTNET=true  # Can override environment-based selection
```

## Implementation Details

The BinanceDataProvider class in `agents/data_providers/binance_data_provider.py` implements the environment-based selection logic:

```python
def __init__(
    self, 
    api_key: Optional[str] = None, 
    api_secret: Optional[str] = None,
    use_testnet: Optional[bool] = None
):
    """
    Initialize the Binance API provider.
    
    Args:
        api_key: Binance API key
        api_secret: Binance API secret
        use_testnet: Override environment setting for testnet (if provided)
    """
    # Load environment variables if keys not provided
    self.api_key = api_key or os.environ.get("BINANCE_API_KEY")
    self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET")
    
    # Determine whether to use testnet based on environment
    deploy_env = os.environ.get("DEPLOY_ENV", "dev").lower()
    
    # Default to testnet for development and replit, mainnet for EC2
    # Unless explicitly overridden by BINANCE_USE_TESTNET or constructor argument
    if use_testnet is not None:
        # Constructor argument takes highest precedence
        self.use_testnet = use_testnet
    elif os.environ.get("BINANCE_USE_TESTNET") is not None:
        # Environment variable takes second precedence
        self.use_testnet = os.environ.get("BINANCE_USE_TESTNET").lower() in ["true", "1", "yes"]
    else:
        # Default based on deployment environment
        self.use_testnet = deploy_env in ["dev", "replit"]
    
    # Set the base URL based on testnet or mainnet
    if self.use_testnet:
        self.base_url = self.TESTNET_URL
        self.logger.info(f"Initialized Binance Data Provider using testnet ({self.base_url})")
    else:
        self.base_url = self.BASE_URL
        if deploy_env == "ec2":
            self.logger.info("Using real Binance API for EC2 deployment")
        self.logger.info(f"Initialized Binance Data Provider using mainnet ({self.base_url})")
```

## Available Endpoints

The BinanceDataProvider implements these primary methods:

- `fetch_ohlcv`: Retrieve OHLCV (candlestick) data
- `get_ticker`: Get current ticker information
- `get_current_price`: Get the current price of a symbol
- `get_account_info`: Get account balance information (authenticated)
- `fetch_market_depth`: Get order book data
- `get_exchange_info`: Get exchange information and trading rules

## Error Handling

The provider implements robust error handling for various failure scenarios:

1. Rate limiting with automatic retry
2. Network error handling with exponential backoff
3. API error parsing and appropriate responses
4. Logging of errors for debugging purposes

## Testing Environment Selection

A test script (`test_binance_endpoint.py`) is provided to verify the environment-based API selection mechanism:

```bash
# Run the test script to verify environment-based selection
python test_binance_endpoint.py
```

## Using with the Market Data Provider Factory

The BinanceDataProvider is integrated with the MarketDataProviderFactory to provide fallback capability:

```python
from market_data_provider_factory import MarketDataProviderFactory

# Create the factory
factory = MarketDataProviderFactory()

# Get the appropriate provider (defaults to Binance)
provider = factory.get_provider()

# Or explicitly request Binance
provider = factory.get_provider("binance")

# Fetch data using the factory (with automatic fallback)
ohlcv_data = factory.fetch_ohlcv("BTC/USDT", interval="1h", limit=100)
```

## Adding New Endpoints

To add support for additional Binance API endpoints, extend the BinanceDataProvider class with new methods following the established pattern of making authenticated or unauthenticated requests.