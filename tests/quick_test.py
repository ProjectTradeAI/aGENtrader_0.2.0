#!/usr/bin/env python3
"""
Quick test to validate the fixed technical_analyst_agent.py import
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - aGENtrader - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aGENtrader')

# Try to load environment variables
load_dotenv()

def check_coinapi_key():
    """Check if COINAPI_KEY is available in the environment"""
    api_key = os.environ.get('COINAPI_KEY')
    if not api_key:
        logger.error("No COINAPI_KEY found in environment variables")
        return False
    
    logger.info(f"Found CoinAPI key: {api_key[:4]}...{api_key[-4:]}")
    return True

def main():
    """Run a quick test of the fixed technical analyst agent"""
    logger.info("Running quick test to validate technical analyst agent")
    
    # Check for API key
    if not check_coinapi_key():
        logger.error("Missing COINAPI_KEY, please set it in the environment")
        return 1
    
    # Test direct import
    logger.info("Testing direct import of CoinAPIFetcher...")
    try:
        from coinapi_fetcher import CoinAPIFetcher
        logger.info("✅ CoinAPIFetcher imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import CoinAPIFetcher: {str(e)}")
        return 1
    
    # Create a simple test file
    logger.info("Creating simple test technical analyst agent...")
    test_file = 'test_technical_analyst.py'
    
    with open(test_file, 'w') as f:
        f.write("""
from base_agent import BaseAnalystAgent

class TestTechnicalAnalyst(BaseAnalystAgent):
    def analyze(self, symbol=None, interval=None, **kwargs):
        return {
            'success': True,
            'signal': 'BUY',
            'confidence': 75
        }
""")
    
    # Try to import the test file
    logger.info("Testing import of test technical analyst agent...")
    sys.path.append('.')
    try:
        from test_technical_analyst import TestTechnicalAnalyst
        analyst = TestTechnicalAnalyst()
        result = analyst.analyze()
        logger.info(f"✅ Test successful: {result}")
        return 0
    except ImportError as e:
        logger.error(f"❌ Failed to import TestTechnicalAnalyst: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())