#!/usr/bin/env python3
# Description: Tests the TechnicalAnalystAgent functionality and signal generation

import sys
import os
import unittest
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from agents import TechnicalAnalystAgent
except ImportError:
    print("Error: TechnicalAnalystAgent not found. Make sure the agent is properly implemented.")
    sys.exit(1)

class MockDataFetcher:
    """Mock data fetcher for testing without API calls."""
    
    def __init__(self, mock_data_path=None):
        """Initialize with optional mock data path."""
        self.mock_data = self._load_mock_data(mock_data_path)
    
    def _load_mock_data(self, mock_data_path) -> Dict[str, Any]:
        """Load mock data from file or generate default data."""
        if mock_data_path and os.path.exists(mock_data_path):
            try:
                with open(mock_data_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse mock data file {mock_data_path}")
                
        # Generate default mock data
        return self._generate_default_mock_data()
    
    def _generate_default_mock_data(self) -> Dict[str, Any]:
        """Generate default mock data for testing."""
        # Generate OHLCV data for test - includes a pattern that should trigger signals
        ohlcv_data = []
        base_price = 50000.0
        
        # Create price trends that will generate clear signals:
        # - First section: rising trend
        # - Middle section: peak and start of downtrend
        # - End section: oversold condition (low RSI)
        
        # Rising trend - 20 candles
        for i in range(20):
            price = base_price * (1.0 + i * 0.005)  # 0.5% increase per candle
            ohlcv_data.append({
                'timestamp': int(datetime.now().timestamp() * 1000) - (100 - i) * 3600 * 1000,
                'open': price * 0.998,
                'high': price * 1.005,
                'low': price * 0.995,
                'close': price,
                'volume': 1000000 * (1 + (i % 5) * 0.1)
            })
        
        # Peak and downtrend - 40 candles
        for i in range(40):
            if i < 5:
                # Peaking
                factor = 1.10 + (5-i) * 0.005  # Slowly decreasing growth
            else:
                # Declining
                factor = 1.10 - (i-5) * 0.01  # Faster decline than growth
            
            price = base_price * factor
            ohlcv_data.append({
                'timestamp': int(datetime.now().timestamp() * 1000) - (80 - i) * 3600 * 1000,
                'open': price * 1.002,
                'high': price * 1.01,
                'low': price * 0.99,
                'close': price,
                'volume': 1500000 * (1 + (i % 10) * 0.15)
            })
        
        # Oversold condition - 40 candles
        for i in range(40):
            # Sharp decline followed by bottoming pattern
            if i < 20:
                factor = 0.70 - (i * 0.005)  # Continuing decline
            else: 
                factor = 0.60 + ((i-20) * 0.002)  # Slight recovery
                
            price = base_price * factor
            ohlcv_data.append({
                'timestamp': int(datetime.now().timestamp() * 1000) - (40 - i) * 3600 * 1000,
                'open': price * 0.99,
                'high': price * 1.005,
                'low': price * 0.985,
                'close': price,
                'volume': 2000000 * (1 + (i % 8) * 0.3)
            })
        
        return {
            'ohlcv': ohlcv_data,
            'current_price': ohlcv_data[-1]['close'],
            'symbol': 'BTC/USDT'
        }
    
    def fetch_ohlcv(self, symbol, interval='1h', limit=100):
        """Return mock OHLCV data."""
        return self.mock_data['ohlcv'][-limit:]
    
    def get_ticker(self, symbol):
        """Return mock ticker data."""
        price = self.mock_data['current_price']
        return {
            'symbol': symbol,
            'last': price,
            'bid': price * 0.999,
            'ask': price * 1.001
        }
    
    def get_current_price(self, symbol):
        """Return mock current price."""
        return self.mock_data['current_price']

class TestTechnicalAnalystAgent(unittest.TestCase):
    """Test suite for the TechnicalAnalystAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.data_fetcher = MockDataFetcher()
        self.agent = TechnicalAnalystAgent(data_fetcher=self.data_fetcher)
        
    def test_initialization(self):
        """Test if agent initializes correctly."""
        self.assertEqual(self.agent.name, "TechnicalAnalystAgent")
        self.assertTrue(hasattr(self.agent, 'data_fetcher'))
        
    def test_analyze_method_exists(self):
        """Test if analyze method exists and is callable."""
        self.assertTrue(hasattr(self.agent, 'analyze'))
        self.assertTrue(callable(getattr(self.agent, 'analyze')))
        
    def test_analyze_returns_valid_result(self):
        """Test if analyze returns a valid result structure."""
        result = self.agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Check result structure
        self.assertIsInstance(result, dict)
        self.assertIn('signal', result)
        self.assertIn('confidence', result)
        self.assertIn('explanation', result)
        self.assertIn('current_price', result)
        
        # Check signal value
        self.assertIn(result['signal'], ["BUY", "SELL", "NEUTRAL"])
        
        # Check confidence value
        self.assertIsInstance(result['confidence'], int)
        self.assertTrue(0 <= result['confidence'] <= 100)
        
    def test_analyze_with_oversold_data(self):
        """Test analyze method with data showing oversold conditions."""
        # Our mock data should include an oversold pattern at the end
        result = self.agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Expect a BUY signal due to oversold conditions
        self.assertEqual(result['signal'], "BUY", 
                         f"Expected BUY signal but got {result['signal']} with explanation: {result.get('explanation')}")
        self.assertTrue(result['confidence'] > 70, 
                        f"Expected confidence > 70 but got {result['confidence']}")
        
    def test_indicator_calculation(self):
        """Test if technical indicators are properly calculated."""
        result = self.agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Check if indicators exist in the result
        self.assertIn('indicators', result)
        indicators = result['indicators']
        
        # Check for essential indicators
        expected_indicators = ['rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower']
        for indicator in expected_indicators:
            self.assertIn(indicator, indicators, f"Missing indicator: {indicator}")
            self.assertIsInstance(indicators[indicator], (int, float), 
                                f"Indicator {indicator} is not a number")

def main():
    """Run the test suite."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTechnicalAnalystAgent))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())