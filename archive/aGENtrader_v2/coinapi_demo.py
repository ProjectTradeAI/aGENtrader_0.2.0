"""
CoinAPI Integration Demo

This script demonstrates the integration with CoinAPI.io for fetching live market data.
It shows how the MarketDataFetcher can be used to fetch real-time data and process it
through the aGENtrader v2 agent pipeline.
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Import components
from aGENtrader_v2.data.feed import MarketDataFetcher
from aGENtrader_v2.orchestrator.core_orchestrator import CoreOrchestrator
from aGENtrader_v2.utils.logger import get_logger
from aGENtrader_v2.utils.config import get_config

def run_with_fake_api_key():
    """Run with a fake API key to demonstrate the expected flow."""
    # Set fake API key for demonstration
    os.environ["COINAPI_KEY"] = "YOUR_API_KEY_HERE"
    
    # Create logger and config
    logger = get_logger("coinapi_demo")
    config = get_config()
    
    # Get market data configuration
    market_config = config.get_section("market_data")
    symbol = market_config.get("default_pair", "BTC/USDT")
    interval = market_config.get("default_interval", "1h")
    
    # Print banner
    print("\n" + "=" * 60)
    print("CoinAPI Integration Demo (SIMULATION MODE)")
    print("=" * 60)
    print(f"Fetching market data for {symbol} at {interval} interval")
    print("NOTE: This is running with a placeholder API key and will not fetch real data")
    print("=" * 60 + "\n")
    
    print("You need to provide a real CoinAPI key to fetch real data.")
    print("Please sign up at https://www.coinapi.io/ and get a free API key.")
    print("Once you have the key, set it using either:")
    print("1. Add to config/secrets.yaml as coinapi_key: YOUR_KEY")
    print("2. Set as an environment variable: export COINAPI_KEY=YOUR_KEY")
    print("\nThis demo will continue with simulated responses.")
    
    # This is a simulated market event that would be similar to what CoinAPI returns
    simulated_event = {
        "type": "market_update",
        "symbol": symbol,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": {
            "symbol": symbol,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "price": 50000.0,
            "bid": 49990.0,
            "ask": 50010.0,
            "bid_size": 1.5,
            "ask_size": 2.1
        },
        "ohlcv": {
            "symbol": symbol,
            "interval": interval,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "open": 49800.0,
            "high": 50200.0,
            "low": 49700.0,
            "close": 50000.0,
            "volume": 150.5
        },
        "orderbook": {
            "symbol": symbol,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bids": [
                {"price": 49990.0, "size": 1.5},
                {"price": 49980.0, "size": 2.3},
                {"price": 49970.0, "size": 4.1}
            ],
            "asks": [
                {"price": 50010.0, "size": 2.1},
                {"price": 50020.0, "size": 3.4},
                {"price": 50030.0, "size": 5.0}
            ],
            "bid_total": 7.9,
            "ask_total": 10.5,
            "bid_ask_ratio": 0.75
        }
    }
    
    # Process through the orchestrator
    logger.info("Creating CoreOrchestrator")
    orchestrator = CoreOrchestrator()
    
    logger.info("Processing simulated market event")
    results = orchestrator.process_market_event(simulated_event)
    
    # Print results
    if results and "decision" in results and results["decision"]:
        print("\nTrading Decision:")
        print(f"Action: {results['decision']['action']}")
        print(f"Pair: {results['decision']['pair']}")
        print(f"Confidence: {results['decision']['confidence']}%")
        print(f"Reason: {results['decision']['reason']}")
    else:
        print("\nNo valid trading decision generated.")
    
    print("\nNOTE: This was a simulation. For real data, please provide a valid CoinAPI key.")
    print("=" * 60)

def run_with_real_api():
    """Run with a real API key to fetch live data."""
    # Create logger
    logger = get_logger("coinapi_demo")
    
    # Print banner
    print("\n" + "=" * 60)
    print("CoinAPI Integration Demo (LIVE MODE)")
    print("=" * 60)
    
    # Import error handling utilities
    try:
        from aGENtrader_v2.utils.error_handler import (
            check_api_keys, request_api_key, DataFetchingError, ValidationError
        )
        error_utils_available = True
    except ImportError:
        error_utils_available = False
    
    # Check if COINAPI_KEY exists using enhanced error handler if available
    api_key_exists = False
    if error_utils_available:
        api_key_exists = check_api_keys('coinapi_key', 'COINAPI_KEY')
        if not api_key_exists:
            print("No CoinAPI key found. Please provide a valid API key.")
            request_api_key('coinapi_key', 'COINAPI_KEY')
            print("The demo will switch to simulation mode.")
            run_with_fake_api_key()
            return
    else:
        # Fallback method for checking API key
        api_key = os.environ.get("COINAPI_KEY", "")
        if not api_key:
            try:
                # Try to load from secrets file
                with open(os.path.join(script_dir, "config/secrets.yaml"), "r") as f:
                    import yaml
                    secrets = yaml.safe_load(f)
                    api_key = secrets.get("coinapi_key", "")
            except Exception:
                api_key = ""
        
        if not api_key:
            print("No CoinAPI key found. Please provide a valid API key.")
            print("The demo will switch to simulation mode.")
            run_with_fake_api_key()
            return
        else:
            api_key_exists = True
    
    # Demonstrate error handling capabilities
    print("Demonstrating error handling capabilities...")
    
    # Create fetcher and orchestrator
    try:
        logger.info("Creating MarketDataFetcher")
        fetcher = MarketDataFetcher()
        
        logger.info("Creating CoreOrchestrator")
        orchestrator = CoreOrchestrator()
        
        # Get configuration
        config = get_config()
        market_config = config.get_section("market_data")
        symbol = market_config.get("default_pair", "BTC/USDT")
        
        print(f"Fetching real-time market data for {symbol}")
        print("This may take a few seconds...")
        
        # Highlight error handling
        print("\n1. Demonstrating input validation:")
        try:
            # Try an invalid symbol to show validation error handling
            invalid_symbol = "Invalid/Symbol!"
            print(f"   Attempting to fetch data for invalid symbol: {invalid_symbol}")
            invalid_event = fetcher.fetch_market_event(invalid_symbol)
            print("   This should not execute due to validation error")
        except ValidationError as e:
            print(f"   ✓ Validation Error properly caught: {e}")
        except Exception as e:
            print(f"   ✗ Unexpected error type: {type(e).__name__}: {e}")
            
        print("\n2. Demonstrating API error recovery:")
        # Fetch a single market event with proper error handling
        logger.info(f"Fetching market event for {symbol}")
        
        try:
            print(f"   Attempting to fetch data for {symbol}")
            # Use the proper symbol for real data
            market_event = fetcher.fetch_market_event(symbol)
            
            if not market_event:
                print("   Failed to fetch market data")
                raise Exception("Empty market event returned")
                
            if market_event.get("type") == "market_update_error":
                print(f"   ✓ Error response properly formatted: {market_event.get('error')}")
                print(f"   Error type: {market_event.get('_meta', {}).get('error_type', 'Unknown')}")
                # We'll continue processing anyway in this demo
            else:
                print("   ✓ Successfully fetched market data")
        except Exception as e:
            print(f"   ✗ Error fetching market data: {e}")
            print("   The demo will switch to simulation mode.")
            run_with_fake_api_key()
            return
            
        # Print market data summary
        print("\nMarket Data Summary:")
        print(f"Symbol: {market_event.get('symbol')}")
        print(f"Timestamp: {market_event.get('timestamp')}")
        if "ticker" in market_event and market_event["ticker"]:
            print(f"Current Price: {market_event['ticker'].get('price', 'N/A')}")
            
        # Show metadata if available
        if "_meta" in market_event:
            print("\nMetadata:")
            meta = market_event.get("_meta", {})
            for key, value in meta.items():
                if key != "errors" and not isinstance(value, dict):
                    print(f"  {key}: {value}")
            
            # If there are component statuses, show them
            if "components" in meta:
                print("\nComponent Status:")
                for comp, status in meta["components"].items():
                    status_icon = "✓" if status else "✗"
                    print(f"  {status_icon} {comp}")
                    
            # If there are errors, show them
            if meta.get("errors"):
                print("\nErrors:")
                for error in meta["errors"]:
                    print(f"  - {error}")
        
        # Process through the orchestrator
        logger.info("Processing market event through CoreOrchestrator")
        print("\n3. Demonstrating decision agent error handling:")
        try:
            print("   Processing market event through the agent pipeline")
            results = orchestrator.process_market_event(market_event)
            
            # Print results
            if results and "decision" in results and results["decision"]:
                decision = results["decision"]
                print("\n   ✓ Trading Decision Generated:")
                print(f"     Action: {decision['action']}")
                print(f"     Pair: {decision['pair']}")
                print(f"     Confidence: {decision['confidence']}%")
                print(f"     Reason: {decision['reason']}")
                
                # Check if this is an error-derived decision
                if decision.get("error"):
                    print(f"     Note: This decision was generated from an error state")
                    print(f"     Error Type: {decision.get('error_type', 'Unknown')}")
            else:
                print("\n   ✗ No valid trading decision generated")
        except Exception as e:
            print(f"\n   ✗ Error in decision pipeline: {e}")
            
        # Save the full market event for reference
        output_dir = os.path.join(script_dir, "logs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "latest_market_event.json")
        
        with open(output_path, "w") as f:
            json.dump(market_event, f, indent=2)
        
        print(f"\nFull market data saved to: {output_path}")
        print("=" * 60)
        
    except DataFetchingError as e:
        logger.error(f"Data fetching error in CoinAPI demo: {e}")
        print(f"Data fetching error: {e}")
        print("The demo will switch to simulation mode.")
        run_with_fake_api_key()
    except Exception as e:
        logger.error(f"Error in CoinAPI demo: {e}")
        print(f"Error: {str(e)}")
        print("The demo will switch to simulation mode.")
        run_with_fake_api_key()

def main():
    """Main entry point for the CoinAPI demo."""
    parser = argparse.ArgumentParser(description="CoinAPI Integration Demo")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (no API calls)")
    
    args = parser.parse_args()
    
    if args.simulate:
        run_with_fake_api_key()
    else:
        run_with_real_api()

if __name__ == "__main__":
    main()