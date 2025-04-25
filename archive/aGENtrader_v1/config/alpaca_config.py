"""
Alpaca API Configuration

This file contains configuration settings for the Alpaca API integration.
"""

import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Alpaca API settings
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY', '')
ALPACA_API_SECRET = os.environ.get('ALPACA_API_SECRET', '')
ALPACA_API_BASE_URL = os.environ.get('ALPACA_API_BASE_URL', 'https://paper-api.alpaca.markets')  # Paper trading by default
ALPACA_API_DATA_URL = os.environ.get('ALPACA_API_DATA_URL', 'https://data.alpaca.markets')

# Check if API keys are available
if not ALPACA_API_KEY or not ALPACA_API_SECRET:
    logger.warning("Alpaca API key or secret not found in environment variables.")
    logger.info("Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")

# Timeframe mapping from our system to Alpaca format
TIMEFRAME_MAPPING = {
    '1m': '1Min',
    '5m': '5Min',
    '15m': '15Min',
    '30m': '30Min',
    '1h': '1Hour',
    '2h': '2Hour',
    '4h': '4Hour',
    '1d': '1Day',
}

# Market data settings
DEFAULT_LIMIT = 1000  # Default number of bars to fetch
DEFAULT_TIMEFRAME = '1h'  # Default timeframe
DEFAULT_SYMBOL = 'BTCUSD'  # Default symbol

# Trading settings
DEFAULT_MARKET = 'crypto'  # Default market (crypto, stocks, etc.)
SUPPORTED_MARKETS = ['crypto', 'stocks']
SUPPORTED_ASSETS = {
    'crypto': ['BTCUSD', 'ETHUSD', 'SOLUSD', 'AVAXUSD', 'ADAUSD', 'DOGEUSD', 'SHIBUSD'],
    'stocks': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
}