#!/bin/bash
# Script to run a simple market data test on EC2

# Check if EC2_PUBLIC_IP and EC2_SSH_KEY are set
if [ -z "$EC2_PUBLIC_IP" ]; then
  echo "ERROR: EC2_PUBLIC_IP environment variable is not set"
  exit 1
fi

if [ -z "$EC2_SSH_KEY" ]; then
  echo "ERROR: EC2_SSH_KEY environment variable is not set"
  exit 1
fi

# Temporary file for SSH key with proper formatting
KEY_FILE=$(mktemp)
echo "Creating properly formatted SSH key..."
echo -e "-----BEGIN RSA PRIVATE KEY-----" > "$KEY_FILE"
echo "$EC2_SSH_KEY" | sed 's/-----BEGIN RSA PRIVATE KEY-----//g' | sed 's/-----END RSA PRIVATE KEY-----//g' | tr -d '\n' | fold -w 64 >> "$KEY_FILE"
echo -e "\n-----END RSA PRIVATE KEY-----" >> "$KEY_FILE"
chmod 600 "$KEY_FILE"

echo "Testing SSH connection..."
if ! ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "echo Connected successfully"; then
  echo "Error: Failed to connect to EC2 instance"
  rm "$KEY_FILE"
  exit 1
fi

echo "Connection successful!"
echo "Creating a simple market data test script on EC2..."

# Create a simple Python script to test market data functionality
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "cat > /home/ec2-user/aGENtrader/simple_market_test.py << 'PYEOF'
#!/usr/bin/env python3
'''
Simple Market Data Test

This script tests the basic market data functionalities without requiring AutoGen.
'''

import os
import sys
import logging
import json
import argparse
from datetime import datetime, timedelta
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_market_test')

# Make sure we can import from the aGENtrader directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    # Import required modules
    from utils.database_manager import DatabaseQueryManager
    logger.info('Successfully imported DatabaseQueryManager')
except ImportError as e:
    logger.error(f'Failed to import required modules: {str(e)}')
    sys.exit(1)

def parse_arguments():
    '''Parse command line arguments'''
    parser = argparse.ArgumentParser(description='Simple Market Data Test')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval (e.g., 1m, 15m, 1h, 4h, 1d)')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back')
    parser.add_argument('--format', type=str, default='text', choices=['text', 'json', 'markdown'], help='Output format')
    parser.add_argument('--output_file', type=str, help='Output file path (optional)')
    return parser.parse_args()

def main():
    '''Main function to test market data functionality'''
    args = parse_arguments()
    
    logger.info(f'Testing market data for {args.symbol} with {args.interval} interval, looking back {args.days} days')
    
    try:
        # Initialize the database query manager
        db_manager = DatabaseQueryManager()
        logger.info('Successfully initialized DatabaseQueryManager')
        
        # Test connection
        logger.info('Testing database connection...')
        if db_manager.is_connected():
            logger.info('Database connection successful')
        else:
            logger.error('Database connection failed')
            return False
        
        # Get the latest price
        logger.info(f'Getting latest price for {args.symbol}...')
        latest_price = db_manager.get_latest_price(args.symbol)
        logger.info(f'Latest price for {args.symbol}: {latest_price}')
        
        # Get market data
        logger.info(f'Getting market data for {args.symbol}...')
        market_data = db_manager.get_market_data(
            symbol=args.symbol,
            interval=args.interval,
            limit=24 * args.days  # Approximate number of candles for the specified days
        )
        logger.info(f'Retrieved {len(market_data)} market data points')
        
        # Calculate market statistics
        logger.info(f'Calculating market statistics for {args.symbol}...')
        stats = db_manager.get_price_statistics(
            symbol=args.symbol,
            interval=args.interval,
            days=args.days
        )
        logger.info('Market statistics calculated successfully')
        
        # Calculate volatility
        logger.info(f'Calculating volatility for {args.symbol}...')
        volatility = db_manager.calculate_volatility(
            symbol=args.symbol,
            interval=args.interval,
            days=args.days
        )
        logger.info(f'Volatility for {args.symbol}: {volatility}')
        
        # Prepare results
        results = {
            'timestamp': datetime.now().isoformat(),
            'symbol': args.symbol,
            'interval': args.interval,
            'days': args.days,
            'latest_price': latest_price,
            'market_data_count': len(market_data),
            'market_data_sample': market_data[:5] if market_data else [],
            'statistics': stats,
            'volatility': volatility
        }
        
        # Format and output results
        if args.format == 'json':
            output = json.dumps(results, indent=2)
        elif args.format == 'markdown':
            output = f'''# Market Data Test Results

## Overview
- **Symbol**: {args.symbol}
- **Interval**: {args.interval}
- **Period**: Last {args.days} days
- **Timestamp**: {results['timestamp']}

## Latest Price
{results['latest_price']}

## Statistics
- **Open**: {stats.get('open', 'N/A')}
- **High**: {stats.get('high', 'N/A')}
- **Low**: {stats.get('low', 'N/A')}
- **Close**: {stats.get('close', 'N/A')}
- **Volume**: {stats.get('volume', 'N/A')}
- **Price Change**: {stats.get('price_change', 'N/A')}
- **Price Change %**: {stats.get('price_change_percent', 'N/A')}%

## Volatility
{volatility}

## Data Points
Retrieved {results['market_data_count']} data points
'''
        else:  # text format
            output = f'''Market Data Test Results
=====================

Overview:
  Symbol:     {args.symbol}
  Interval:   {args.interval}
  Period:     Last {args.days} days
  Timestamp:  {results['timestamp']}

Latest Price: {results['latest_price']}

Statistics:
  Open:           {stats.get('open', 'N/A')}
  High:           {stats.get('high', 'N/A')}
  Low:            {stats.get('low', 'N/A')}
  Close:          {stats.get('close', 'N/A')}
  Volume:         {stats.get('volume', 'N/A')}
  Price Change:   {stats.get('price_change', 'N/A')}
  Price Change %: {stats.get('price_change_percent', 'N/A')}%

Volatility: {volatility}

Data Points: Retrieved {results['market_data_count']} data points
'''
        
        # Print to console
        print(output)
        
        # Save to file if specified
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(output)
            logger.info(f'Results saved to {args.output_file}')
        
        logger.info('Market data test completed successfully')
        return True
        
    except Exception as e:
        logger.error(f'Error in market data test: {str(e)}')
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
PYEOF"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "Error: Failed to create test script with exit code $EXIT_CODE"
  rm "$KEY_FILE"
  exit $EXIT_CODE
fi

echo "Test script created. Running simple market data test..."
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$EC2_PUBLIC_IP" "cd /home/ec2-user/aGENtrader && python3 simple_market_test.py --symbol BTCUSDT --interval 1h --days 7 --format text"
TEST_EXIT_CODE=$?

# Clean up the temporary key file
rm "$KEY_FILE"

if [ $TEST_EXIT_CODE -ne 0 ]; then
  echo "Error: Market data test failed with exit code $TEST_EXIT_CODE"
  exit $TEST_EXIT_CODE
fi

echo "Simple market data test completed successfully!"
