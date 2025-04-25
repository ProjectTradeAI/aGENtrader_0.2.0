#!/usr/bin/env python3
"""
Run script for aGENtrader v2

This script implements the entry point for the aGENtrader v2 system
for the 24-hour test run with enhanced technical analysis.
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/agentrader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger('aGENtrader')


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='aGENtrader v2 Trading System')
    
    parser.add_argument('--mode', type=str, default='test',
                       choices=['test', 'live'],
                       help='Trading mode (test or live)')
    
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                       help='Trading symbol (e.g., BTC/USDT)')
    
    parser.add_argument('--interval', type=str, default='1h',
                       help='Time interval for market data (e.g., 1h, 4h, 1d)')
    
    parser.add_argument('--config', type=str, default='config/default.json',
                       help='Path to configuration file')
    
    parser.add_argument('--duration', type=str, default='24h',
                       help='Test duration (e.g., 1h, 24h, 7d), only used in test mode')
    
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}


def setup_environment(args, config: Dict[str, Any]):
    """Set up the environment based on arguments and configuration."""
    # Set up logging level
    if args.verbose:
        for handler in logging.root.handlers[:]:
            handler.setLevel(logging.DEBUG)
        logging.root.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    else:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        logging.root.setLevel(getattr(logging, log_level))
    
    # Log startup information
    logger.info(f"Starting aGENtrader v2 in {args.mode} mode")
    logger.info(f"Symbol: {args.symbol}, Interval: {args.interval}")
    
    if args.mode == 'test':
        logger.info(f"Test duration: {args.duration}")
    
    # Get API keys from environment if not in config
    if 'api' in config and 'coinapi' in config['api']:
        if not config['api']['coinapi']['key'] and 'COINAPI_KEY' in os.environ:
            logger.info("Using CoinAPI key from environment")
            config['api']['coinapi']['key'] = os.environ.get('COINAPI_KEY')


def run_test(args, config: Dict[str, Any]):
    """Run the system in test mode."""
    from aGENtrader_v2.data.feed.coinapi_fetcher import CoinAPIFetcher
    from aGENtrader_v2.agents.technical_analyst_agent import TechnicalAnalystAgent
    
    logger.info("Initializing components for test run...")
    
    # Get CoinAPI key
    coinapi_key = None
    if 'api' in config and 'coinapi' in config['api']:
        coinapi_key = config['api']['coinapi']['key']
    
    if not coinapi_key and 'COINAPI_KEY' in os.environ:
        coinapi_key = os.environ.get('COINAPI_KEY')
    
    if not coinapi_key:
        logger.error("No CoinAPI key found. Please set it in the configuration or environment.")
        return
    
    # Initialize data fetcher
    data_fetcher = CoinAPIFetcher(api_key=coinapi_key)
    
    # Initialize technical analyst
    technical_config = config.get('agents', {}).get('technical', {})
    technical_analyst = TechnicalAnalystAgent(data_fetcher=data_fetcher, config=technical_config)
    
    # Parse duration
    duration_str = args.duration
    duration = None
    
    if duration_str.endswith('h'):
        hours = int(duration_str[:-1])
        duration = timedelta(hours=hours)
    elif duration_str.endswith('d'):
        days = int(duration_str[:-1])
        duration = timedelta(days=days)
    else:
        logger.error(f"Invalid duration format: {duration_str}. Using default 24h.")
        duration = timedelta(hours=24)
    
    # Calculate end time
    start_time = datetime.now()
    end_time = start_time + duration
    
    logger.info(f"Starting test run at {start_time.isoformat()}")
    logger.info(f"Test will run until {end_time.isoformat()} ({duration})")
    
    # Run the test loop
    interval_seconds = 3600  # Default to 1 hour
    if args.interval.endswith('m'):
        interval_seconds = int(args.interval[:-1]) * 60
    elif args.interval.endswith('h'):
        interval_seconds = int(args.interval[:-1]) * 3600
    elif args.interval.endswith('d'):
        interval_seconds = int(args.interval[:-1]) * 86400
    
    # Add some jitter to interval to avoid API rate limits
    import random
    interval_seconds = interval_seconds + random.randint(0, 60)
    
    cycle_count = 0
    total_cycles = int(duration.total_seconds() / interval_seconds)
    
    try:
        while datetime.now() < end_time:
            cycle_count += 1
            logger.info(f"Test cycle {cycle_count}/{total_cycles} - Elapsed: {datetime.now() - start_time}")
            
            # Run technical analysis
            logger.info(f"Running technical analysis for {args.symbol} at {args.interval} interval")
            analysis_result = technical_analyst.analyze(args.symbol, args.interval)
            
            # Log the result
            result_file = f"logs/technical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(result_file, 'w') as f:
                json.dump(analysis_result, f, indent=2)
            
            logger.info(f"Technical analysis result: {analysis_result['signal']} with confidence {analysis_result['confidence']}%")
            
            # Calculate time until next cycle
            next_cycle_time = datetime.now() + timedelta(seconds=interval_seconds)
            if next_cycle_time > end_time:
                break
            
            # Sleep until next cycle
            sleep_seconds = (next_cycle_time - datetime.now()).total_seconds()
            if sleep_seconds > 0:
                logger.info(f"Sleeping for {int(sleep_seconds)} seconds until next cycle")
                import time
                time.sleep(sleep_seconds)
    
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
    
    # Log test completion
    logger.info(f"Test completed after {cycle_count} cycles")
    logger.info(f"Total run time: {datetime.now() - start_time}")


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up environment
    setup_environment(args, config)
    
    # Run in appropriate mode
    if args.mode == 'test':
        run_test(args, config)
    else:
        logger.error("Live mode not implemented for this test")


if __name__ == "__main__":
    main()