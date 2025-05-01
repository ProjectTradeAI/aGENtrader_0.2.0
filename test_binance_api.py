"""
Test Binance API Connectivity in EC2 Environment

This script tests the connection to Binance API using our credentials,
and attempts to fetch real market data.
"""
import os
import logging
import json
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BinanceTest")

# Import the Binance data provider
from binance_data_provider import BinanceDataProvider

def test_binance_connection(use_testnet=None):
    """Test basic connectivity to Binance API."""
    logger.info(f"Testing Binance API connection with {'testnet' if use_testnet else 'mainnet'}...")
    
    # Create data provider with keys from environment, explicitly setting testnet mode
    binance_provider = BinanceDataProvider(use_testnet=use_testnet)
    
    # Try a simple ping request
    try:
        # Try to fetch exchange info as a ping test
        exchange_info = binance_provider._make_request("/api/v3/ping")
        logger.info(f"Binance API connection to {'testnet' if use_testnet else 'mainnet'} successful!")
        return True
    except Exception as e:
        logger.error(f"Binance API connection failed: {str(e)}")
        if "451" in str(e) or "Geographic restriction" in str(e):
            logger.error("Geographic restriction detected. EC2 instance may be in a restricted region.")
        return False

def test_market_data_fetch(symbol: str = "BTC/USDT", use_testnet=None):
    """Test fetching market data for a specific symbol."""
    logger.info(f"Testing market data fetch for {symbol} using {'testnet' if use_testnet else 'mainnet'}...")
    
    # Create data provider with keys from environment, explicitly setting testnet mode
    binance_provider = BinanceDataProvider(use_testnet=use_testnet)
    
    # Format symbol for display
    display_symbol = symbol.replace("/", "")
    
    try:
        # 1. Try to get current price
        current_price = binance_provider.get_current_price(symbol)
        logger.info(f"Current price for {display_symbol}: {current_price}")
        
        # 2. Try to get OHLCV data (recent candlesticks)
        candles = binance_provider.fetch_ohlcv(symbol, interval="1h", limit=5)
        logger.info(f"Retrieved {len(candles)} recent hourly candles for {display_symbol}")
        if candles:
            logger.info(f"Latest candle: Open={candles[-1]['open']}, Close={candles[-1]['close']}")
        
        # 3. Try to get market depth
        depth = binance_provider.fetch_market_depth(symbol, limit=10)
        bid_count = len(depth.get("bids", []))
        ask_count = len(depth.get("asks", []))
        logger.info(f"Market depth for {display_symbol}: {bid_count} bids, {ask_count} asks")
        
        return True
    except Exception as e:
        logger.error(f"Market data fetch failed: {str(e)}")
        if "451" in str(e) or "Geographic restriction" in str(e):
            logger.error("Geographic restriction detected. EC2 instance may be in a restricted region.")
        return False

def main():
    """Main function to run all tests."""
    logger.info("Starting Binance API tests in EC2 environment")
    
    # Check if we have API keys
    binance_key = os.environ.get("BINANCE_API_KEY")
    binance_secret = os.environ.get("BINANCE_API_SECRET")
    
    if not binance_key or not binance_secret:
        logger.error("Binance API credentials not found in environment!")
        return False
    
    logger.info("Binance API credentials found in environment")
    
    # Check EC2 environment
    deploy_env = os.environ.get("DEPLOY_ENV", "dev").lower()
    logger.info(f"Current deployment environment: {deploy_env}")
    
    # First test with testnet (safer option)
    logger.info("====== TESTNET TESTS ======")
    testnet_connection = test_binance_connection(use_testnet=True)
    testnet_data_success = False
    
    if testnet_connection:
        logger.info("Testnet connection successful, testing market data fetch...")
        testnet_data_success = test_market_data_fetch("BTC/USDT", use_testnet=True)
        
        if testnet_data_success:
            # If BTC worked, try a few other coins
            test_market_data_fetch("ETH/USDT", use_testnet=True)
            test_market_data_fetch("SOL/USDT", use_testnet=True)
    else:
        logger.warning("Testnet connection failed")
    
    # Now try with mainnet (real data)
    logger.info("\n====== MAINNET TESTS ======")
    mainnet_connection = test_binance_connection(use_testnet=False)
    mainnet_data_success = False
    
    if mainnet_connection:
        logger.info("Mainnet connection successful, testing market data fetch...")
        mainnet_data_success = test_market_data_fetch("BTC/USDT", use_testnet=False)
        
        if mainnet_data_success:
            # If BTC worked, try a few other coins
            test_market_data_fetch("ETH/USDT", use_testnet=False)
            test_market_data_fetch("SOL/USDT", use_testnet=False)
    else:
        logger.warning("Mainnet connection failed. This could be due to geographic restrictions.")
        logger.warning("Tests will continue to use testnet or mock data.")
    
    logger.info("\n====== TEST SUMMARY ======")
    logger.info(f"Testnet connection: {'SUCCESS' if testnet_connection else 'FAILED'}")
    logger.info(f"Mainnet connection: {'SUCCESS' if mainnet_connection else 'FAILED'}")
    logger.info(f"Testnet data access: {'SUCCESS' if testnet_data_success else 'FAILED'}")
    logger.info(f"Mainnet data access: {'SUCCESS' if mainnet_data_success else 'FAILED'}")
    
    # Either testnet or mainnet success is considered a test pass
    return testnet_connection or mainnet_connection

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)