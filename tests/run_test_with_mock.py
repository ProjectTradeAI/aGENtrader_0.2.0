#!/usr/bin/env python3
"""
aGENtrader v2.1 Mock Test Script

This script tests the aGENtrader v2.1 system with mock data without relying on API access.
It's useful for validating the flow and structure of the system when API access is limited.
"""

import os
import sys
import json
import logging
import datetime
import time
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/mock_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("aGENtrader-Mock-Test")

def load_module_from_path(file_path, module_name):
    """Load a Python module from a file path dynamically."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        logger.error(f"Failed to load module spec from {file_path}")
        return None
        
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to execute module {module_name}: {e}")
        return None

def mock_binance_data():
    """Create mock Binance market data."""
    current_time = int(time.time() * 1000)  # Current time in milliseconds
    
    # Mock OHLCV data (1 hour candles for the last 24 hours)
    ohlcv_data = []
    base_price = 60000.0  # Base BTC price
    
    for i in range(24):
        # Create some price variation
        open_price = base_price * (1 + ((i % 6) - 3) / 100)
        high_price = open_price * 1.01
        low_price = open_price * 0.99
        close_price = open_price * (1 + ((i % 7) - 3) / 200)
        volume = 100 + (i * 10)
        
        # Calculate timestamp (hours ago)
        timestamp = current_time - ((24 - i) * 3600 * 1000)
        
        candle = {
            "open_time": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "close_time": timestamp + 3600 * 1000 - 1,
            "quote_asset_volume": volume * close_price,
            "number_of_trades": 500 + (i * 20),
            "taker_buy_base_asset_volume": volume * 0.4,
            "taker_buy_quote_asset_volume": volume * close_price * 0.4,
            "timestamp": timestamp
        }
        ohlcv_data.append(candle)
    
    return {
        "ohlcv": ohlcv_data,
        "current_price": base_price * (1 + (hash(str(current_time)) % 100) / 10000)
    }

def run_mock_test():
    """Run the mock test against aGENtrader components."""
    logger.info("Starting aGENtrader v2.1 Mock Test")
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Check if we can locate the required modules
    base_paths = [
        "./aGENtrader_v2",  # Direct path
        "../aGENtrader_v2",  # One level up
        "~/aGENtrader_v2",  # Home directory
    ]
    
    # Files we need to locate
    required_files = {
        "technical_analyst": "agents/technical_analyst_agent.py",
        "sentiment_aggregator": "agents/sentiment_aggregator_agent.py",
        "decision_logger": "decision_logger.py"
    }
    
    found_modules = {}
    for base_path in base_paths:
        base_path = os.path.expanduser(base_path)
        if os.path.exists(base_path):
            for module_name, file_path in required_files.items():
                full_path = os.path.join(base_path, file_path)
                if os.path.exists(full_path):
                    found_modules[module_name] = full_path
    
    if len(found_modules) != len(required_files):
        missing = set(required_files.keys()) - set(found_modules.keys())
        logger.error(f"Could not locate all required modules. Missing: {missing}")
        return False
    
    # Load the modules
    modules = {}
    for module_name, file_path in found_modules.items():
        logger.info(f"Loading module {module_name} from {file_path}")
        modules[module_name] = load_module_from_path(file_path, module_name)
        if modules[module_name] is None:
            logger.error(f"Failed to load module {module_name}")
            return False
    
    # Create a mock data provider
    class MockDataProvider:
        def fetch_ohlcv(self, symbol, interval="1h", limit=24):
            mock_data = mock_binance_data()
            return mock_data["ohlcv"]
            
        def get_current_price(self, symbol):
            mock_data = mock_binance_data()
            return mock_data["current_price"]
    
    mock_provider = MockDataProvider()
    
    # Create instances of the agents
    try:
        technical_analyst = modules["technical_analyst"].TechnicalAnalystAgent(mock_provider)
        
        # Mock system for sentiment aggregator since it requires the xAI API
        class MockSystemAdapter:
            def send_message(self, message):
                return {"content": json.dumps({"rating": 3.7, "confidence": 0.85})}
        
        sentiment_aggregator = modules["sentiment_aggregator"].SentimentAggregatorAgent(mock_provider)
        # Inject the mock system adapter
        sentiment_aggregator._system = MockSystemAdapter()
        
        # Create a decision logger
        decision_logger = modules["decision_logger"].DecisionLogger("logs/mock_decision_summary.logl")
        
    except Exception as e:
        logger.error(f"Failed to create agent instances: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # Run tests for different symbols
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    intervals = ["1h", "4h", "1d"]
    
    for symbol in symbols:
        logger.info(f"Testing analysis for {symbol}")
        
        for interval in intervals:
            logger.info(f"  Interval: {interval}")
            
            # Technical analysis
            try:
                ta_result = technical_analyst.analyze(symbol, interval)
                logger.info(f"  Technical Analysis: {json.dumps(ta_result, indent=2)}")
                
                # Log decision
                decision_logger.create_summary_from_result(
                    agent_name="TechnicalAnalyst", 
                    result=ta_result,
                    symbol=symbol,
                    price=mock_provider.get_current_price(symbol)
                )
            except Exception as e:
                logger.error(f"Technical analysis failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Sentiment analysis
            try:
                sentiment_result = sentiment_aggregator.analyze(symbol, interval)
                logger.info(f"  Sentiment Analysis: {json.dumps(sentiment_result, indent=2)}")
                
                # Log decision
                decision_logger.create_summary_from_result(
                    agent_name="SentimentAggregator", 
                    result=sentiment_result,
                    symbol=symbol,
                    price=mock_provider.get_current_price(symbol)
                )
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    logger.info("Mock test completed")
    return True

if __name__ == "__main__":
    success = run_mock_test()
    sys.exit(0 if success else 1)