#!/usr/bin/env python3
"""
Test script for Binance Data Provider

This script tests the BinanceDataProvider implementation,
verifying connectivity and proper data retrieval.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("binance_test")

# Add project root to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.append(project_root)

# Import the providers
from aGENtrader_v2.data.feed.binance_data_provider import BinanceDataProvider
from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory
from aGENtrader_v2.utils.error_handler import DataFetchingError, ValidationError

def test_basic_functionality(provider: BinanceDataProvider, symbol: str = "BTC/USDT"):
    """Test basic BinanceDataProvider functionality."""
    logger.info("Testing BinanceDataProvider basic functionality")
    
    try:
        # Test current price fetching
        logger.info(f"Fetching current price for {symbol}")
        price = provider.get_current_price(symbol)
        logger.info(f"Current price for {symbol}: {price}")
        
        # Test OHLCV fetching
        logger.info(f"Fetching OHLCV data for {symbol} at 1h interval")
        ohlcv_data = provider.get_ohlcv(symbol, "1h", limit=5)
        logger.info(f"Successfully fetched {len(ohlcv_data)} OHLCV records")
        
        # Print the first candle
        if ohlcv_data:
            first_candle = ohlcv_data[0]
            logger.info(f"Sample OHLCV data: Open={first_candle['price_open']}, "
                       f"High={first_candle['price_high']}, Low={first_candle['price_low']}, "
                       f"Close={first_candle['price_close']}, Volume={first_candle['volume_traded']}")
        
        # Test order book fetching
        logger.info(f"Fetching order book for {symbol}")
        order_book = provider.get_order_book(symbol, limit=5)
        logger.info(f"Order book has {len(order_book.get('bids', []))} bids and {len(order_book.get('asks', []))} asks")
        
        # Try to fetch futures data (this might fail for spot symbols)
        try:
            logger.info(f"Fetching funding rate for {symbol}")
            funding_rate = provider.get_funding_rate(symbol)
            logger.info(f"Current funding rate for {symbol}: {funding_rate}")
        except Exception as e:
            logger.warning(f"Failed to fetch funding rate (might not be a futures symbol): {str(e)}")
        
        try:
            logger.info(f"Fetching open interest for {symbol}")
            open_interest = provider.get_open_interest(symbol)
            logger.info(f"Current open interest for {symbol}: {open_interest}")
        except Exception as e:
            logger.warning(f"Failed to fetch open interest (might not be a futures symbol): {str(e)}")
        
        # Test market event creation
        logger.info(f"Creating market event for {symbol}")
        market_event = provider.create_market_event(symbol)
        logger.info(f"Successfully created market event with components: {market_event.get('_meta', {}).get('components', [])}")
        
        return True
    except DataFetchingError as e:
        logger.error(f"Data fetching error: {e}")
        return False
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def test_error_handling(provider: BinanceDataProvider):
    """Test various error scenarios with BinanceDataProvider."""
    logger.info("Testing BinanceDataProvider error handling")
    
    # Test with invalid symbol
    logger.info("Testing with invalid symbol")
    try:
        provider.get_current_price("INVALID#SYMBOL")
        logger.error("Expected error for invalid symbol, but none was raised")
    except ValidationError as e:
        logger.info(f"✓ Correctly caught validation error for invalid symbol: {e}")
    except Exception as e:
        logger.error(f"Unexpected error type for invalid symbol: {e}")
    
    # Test with invalid interval
    logger.info("Testing with invalid interval")
    try:
        provider.get_ohlcv("BTC/USDT", "invalid")
        logger.error("Expected error for invalid interval, but none was raised")
    except ValidationError as e:
        logger.info(f"✓ Correctly caught validation error for invalid interval: {e}")
    except Exception as e:
        logger.error(f"Unexpected error type for invalid interval: {e}")
    
    # Test with extreme limit value
    logger.info("Testing with excessive limit")
    try:
        provider.get_ohlcv("BTC/USDT", "1h", 5001)
        logger.error("Expected error for excessive limit, but none was raised")
    except ValidationError as e:
        logger.info(f"✓ Correctly caught validation error for excessive limit: {e}")
    except Exception as e:
        logger.error(f"Unexpected error type for excessive limit: {e}")
    
    return True

def test_factory_fallback(symbol: str = "BTC/USDT"):
    """Test the DataProviderFactory with fallback support."""
    logger.info("Testing DataProviderFactory with fallback support")
    
    # Initialize factory with Binance as primary and CoinAPI as fallback
    factory = DataProviderFactory(
        primary_provider='binance',
        fallback_provider='coinapi'
    )
    
    try:
        # Test current price with automatic fallback
        logger.info(f"Fetching current price for {symbol} with factory")
        price = factory.get_current_price(symbol)
        logger.info(f"Current price for {symbol} (via factory): {price}")
        
        # Test OHLCV with automatic fallback
        logger.info(f"Fetching OHLCV data for {symbol} at 1h interval with factory")
        ohlcv_data = factory.get_ohlcv(symbol, "1h", limit=5)
        logger.info(f"Successfully fetched {len(ohlcv_data)} OHLCV records via factory")
        
        return True
    except DataFetchingError as e:
        logger.error(f"Factory data fetching error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected factory error: {e}")
        return False

def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test Binance Data Provider")
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading symbol to test with')
    parser.add_argument('--api-key', type=str, help='Binance API key (optional for public endpoints)')
    parser.add_argument('--api-secret', type=str, help='Binance API secret (optional for public endpoints)')
    args = parser.parse_args()
    
    # Get API keys from args or environment
    api_key = args.api_key or os.environ.get('BINANCE_API_KEY')
    api_secret = args.api_secret or os.environ.get('BINANCE_API_SECRET')
    
    # Initialize the Binance data provider
    provider = BinanceDataProvider(api_key, api_secret)
    
    # Run the tests
    logger.info(f"Starting Binance data provider tests with symbol {args.symbol}")
    
    basic_test_result = test_basic_functionality(provider, args.symbol)
    if basic_test_result:
        logger.info("✅ Basic functionality tests passed")
    else:
        logger.error("❌ Basic functionality tests failed")
    
    error_test_result = test_error_handling(provider)
    if error_test_result:
        logger.info("✅ Error handling tests passed")
    else:
        logger.error("❌ Error handling tests failed")
    
    factory_test_result = test_factory_fallback(args.symbol)
    if factory_test_result:
        logger.info("✅ Factory fallback tests passed")
    else:
        logger.error("❌ Factory fallback tests failed")
    
    # Overall result
    if basic_test_result and error_test_result and factory_test_result:
        logger.info("🎉 All tests passed successfully")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())