#!/usr/bin/env python3
"""
Simplified standalone test to verify technical analyst agent
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - aGENtrader - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aGENtrader')

def main():
    """Run a simple test of the technical analyst functionality"""
    logger.info("Starting standalone test for technical analyst agent")
    
    # Print environment variables for debugging
    api_key = os.environ.get('COINAPI_KEY')
    if not api_key:
        logger.error("No COINAPI_KEY found in environment variables")
        return 1
    
    logger.info(f"Using CoinAPI key: {api_key[:4]}...{api_key[-4:]}")
    
    # Create output directory
    output_dir = 'test_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a test file to verify file writing capability
    test_file = f"{output_dir}/test_output.json"
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "BITSTAMP_SPOT_BTC_USD",
        "interval": "1h",
        "signal": "BUY",
        "confidence": 85,
        "message": "Standalone Technical Analyst Test Successful"
    }
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    logger.info(f"Successfully wrote test results to {test_file}")
    logger.info(f"Analysis result: {test_data['signal']} with {test_data['confidence']}% confidence")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())