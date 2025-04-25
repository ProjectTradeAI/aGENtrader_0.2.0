#!/usr/bin/env python3
"""
Test script for the actual TechnicalAnalystAgent
"""

import os
import sys
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - aGENtrader - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aGENtrader')

def main():
    """Test the TechnicalAnalystAgent with simplified dependencies"""
    logger.info("Testing TechnicalAnalystAgent with simplified dependencies")
    
    # Check for API key
    api_key = os.environ.get('COINAPI_KEY')
    if not api_key:
        logger.error("No COINAPI_KEY found in environment variables")
        return 1
    
    logger.info(f"Using CoinAPI key: {api_key[:4]}...{api_key[-4:]}")
    
    # Import components
    from coinapi_fetcher import CoinAPIFetcher
    from technical_analyst_agent import TechnicalAnalystAgent
    
    # Initialize data fetcher
    fetcher = CoinAPIFetcher(api_key=api_key)
    
    # Test symbol and interval
    symbol = "BITSTAMP_SPOT_BTC_USD"
    interval = "1h"
    
    # Initialize technical analyst
    technical_analyst = TechnicalAnalystAgent(data_fetcher=fetcher)
    
    # Perform analysis
    logger.info(f"Analyzing {symbol} at {interval} interval")
    analysis_result = technical_analyst.analyze(symbol, interval)
    
    # Display the result
    logger.info(f"Analysis result: {json.dumps(analysis_result, indent=2)}")
    signal = analysis_result.get('signal', 'UNKNOWN')
    confidence = analysis_result.get('confidence', 0)
    logger.info(f"Signal: {signal} with {confidence}% confidence")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())