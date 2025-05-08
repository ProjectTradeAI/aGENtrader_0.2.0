#!/usr/bin/env python3
# Description: Tests the LiquidityAnalystAgent for order book analysis

import sys
import os
import unittest
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from agents import LiquidityAnalystAgent
except ImportError:
    print("Error: LiquidityAnalystAgent not found. Make sure the agent is properly implemented.")
    sys.exit(1)

class MockDataFetcher:
    """Mock data fetcher for testing LiquidityAnalystAgent without API calls."""
    
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
        # Mock current price
        current_price = 45000.0
        
        # Generate order book with bid-ask imbalance (more bids than asks)
        # This should result in a BUY signal with high confidence
        order_book_bid_heavy = {
            'bids': [
                [str(current_price * 0.999), "15.5"],  # Close to mid price, significant size
                [str(current_price * 0.998), "25.3"],
                [str(current_price * 0.997), "30.2"],
                [str(current_price * 0.996), "40.1"],
                [str(current_price * 0.995), "55.5"],
                [str(current_price * 0.994), "65.8"],
                [str(current_price * 0.993), "75.4"],
                [str(current_price * 0.992), "85.2"],
                [str(current_price * 0.991), "90.5"],
                [str(current_price * 0.990), "100.7"]
            ],
            'asks': [
                [str(current_price * 1.001), "10.3"],  # Smaller sizes on the ask side
                [str(current_price * 1.002), "12.7"],
                [str(current_price * 1.003), "15.4"],
                [str(current_price * 1.004), "18.1"],
                [str(current_price * 1.005), "20.6"],
                [str(current_price * 1.006), "22.9"],
                [str(current_price * 1.007), "25.3"],
                [str(current_price * 1.008), "27.8"],
                [str(current_price * 1.009), "30.2"],
                [str(current_price * 1.010), "32.5"]
            ]
        }
        
        # Generate balanced order book
        # This should result in a NEUTRAL signal
        order_book_balanced = {
            'bids': [
                [str(current_price * 0.999), "15.5"],
                [str(current_price * 0.998), "18.3"],
                [str(current_price * 0.997), "20.2"],
                [str(current_price * 0.996), "22.1"],
                [str(current_price * 0.995), "25.5"]
            ],
            'asks': [
                [str(current_price * 1.001), "15.3"],
                [str(current_price * 1.002), "18.7"],
                [str(current_price * 1.003), "20.4"],
                [str(current_price * 1.004), "22.1"],
                [str(current_price * 1.005), "25.6"]
            ]
        }
        
        # Generate ask-heavy order book for testing sell signals
        # This should result in a SELL signal with high confidence
        order_book_ask_heavy = {
            'bids': [
                [str(current_price * 0.999), "10.5"],
                [str(current_price * 0.998), "12.3"],
                [str(current_price * 0.997), "15.2"],
                [str(current_price * 0.996), "18.1"],
                [str(current_price * 0.995), "20.5"]
            ],
            'asks': [
                [str(current_price * 1.001), "20.3"],
                [str(current_price * 1.002), "25.7"],
                [str(current_price * 1.003), "30.4"],
                [str(current_price * 1.004), "40.1"],
                [str(current_price * 1.005), "50.6"],
                [str(current_price * 1.006), "60.9"],
                [str(current_price * 1.007), "70.3"],
                [str(current_price * 1.008), "80.8"],
                [str(current_price * 1.009), "90.2"],
                [str(current_price * 1.010), "100.5"]
            ]
        }
        
        return {
            'order_book_bid_heavy': order_book_bid_heavy,
            'order_book_balanced': order_book_balanced,
            'order_book_ask_heavy': order_book_ask_heavy,
            'current_price': current_price,
            'symbol': 'BTC/USDT'
        }
    
    def fetch_market_depth(self, symbol, limit=20):
        """Return mock order book data based on test scenario."""
        # We'll return the bid-heavy order book by default
        # Test methods can override this method for different test cases
        return self.mock_data['order_book_bid_heavy']
    
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

class MockBidHeavyDataFetcher(MockDataFetcher):
    """Mock data fetcher that returns bid-heavy order book."""
    def fetch_market_depth(self, symbol, limit=20):
        return self.mock_data['order_book_bid_heavy']

class MockAskHeavyDataFetcher(MockDataFetcher):
    """Mock data fetcher that returns ask-heavy order book."""
    def fetch_market_depth(self, symbol, limit=20):
        return self.mock_data['order_book_ask_heavy']

class MockBalancedDataFetcher(MockDataFetcher):
    """Mock data fetcher that returns balanced order book."""
    def fetch_market_depth(self, symbol, limit=20):
        return self.mock_data['order_book_balanced']

class TestLiquidityAnalystAgent(unittest.TestCase):
    """Test suite for the LiquidityAnalystAgent class."""
    
    def test_initialization(self):
        """Test if agent initializes correctly."""
        agent = LiquidityAnalystAgent(data_fetcher=MockDataFetcher())
        self.assertEqual(agent.name, "LiquidityAnalystAgent")
        self.assertTrue(hasattr(agent, 'data_fetcher'))
        
    def test_analyze_method_exists(self):
        """Test if analyze method exists and is callable."""
        agent = LiquidityAnalystAgent(data_fetcher=MockDataFetcher())
        self.assertTrue(hasattr(agent, 'analyze'))
        self.assertTrue(callable(getattr(agent, 'analyze')))
        
    def test_analyze_returns_valid_result(self):
        """Test if analyze returns a valid result structure."""
        agent = LiquidityAnalystAgent(data_fetcher=MockDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Check result structure
        self.assertIsInstance(result, dict)
        self.assertIn('signal', result)
        self.assertIn('confidence', result)
        self.assertIn('explanation', result)
        self.assertIn('current_price', result)
        self.assertIn('metrics', result)
        
        # Check signal value
        self.assertIn(result['signal'], ["BUY", "SELL", "NEUTRAL"])
        
        # Check confidence value
        self.assertIsInstance(result['confidence'], int)
        self.assertTrue(0 <= result['confidence'] <= 100)
        
    def test_analysis_with_bid_heavy_orderbook(self):
        """Test analysis results with bid-heavy order book."""
        agent = LiquidityAnalystAgent(data_fetcher=MockBidHeavyDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Expect a BUY signal due to bid-heavy order book
        self.assertEqual(result['signal'], "BUY",
                        f"Expected BUY signal but got {result['signal']} with explanation: {result.get('explanation')}")
        self.assertTrue(result['confidence'] >= 65,
                       f"Expected confidence >= 65 but got {result['confidence']}")
        
        # Check the metrics
        metrics = result['metrics']
        self.assertIn('bid_ask_ratio', metrics)
        self.assertTrue(metrics['bid_ask_ratio'] > 1.5, 
                       f"Expected bid_ask_ratio > 1.5 but got {metrics['bid_ask_ratio']}")
        
        # Check for direction-aware details in macro mode
        if result.get('analysis_mode') == 'macro':
            self.assertIn('trade_direction', metrics)
            self.assertEqual(metrics['trade_direction'], "BUY")
            
            # Check for SL/TP descriptions
            self.assertIn('sl_description', metrics)
            self.assertIn('tp_description', metrics)
            self.assertEqual(metrics['sl_description'], "below entry")
            self.assertEqual(metrics['tp_description'], "above entry")
            
            # Check risk-reward ratio exists
            self.assertIn('risk_reward_ratio', metrics)
            self.assertIsInstance(metrics['risk_reward_ratio'], (int, float))
        
    def test_analysis_with_ask_heavy_orderbook(self):
        """Test analysis results with ask-heavy order book."""
        agent = LiquidityAnalystAgent(data_fetcher=MockAskHeavyDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Expect a SELL signal due to ask-heavy order book
        self.assertEqual(result['signal'], "SELL",
                        f"Expected SELL signal but got {result['signal']} with explanation: {result.get('explanation')}")
        self.assertTrue(result['confidence'] >= 65,
                       f"Expected confidence >= 65 but got {result['confidence']}")
        
        # Check the metrics
        metrics = result['metrics']
        self.assertIn('bid_ask_ratio', metrics)
        self.assertTrue(metrics['bid_ask_ratio'] < 0.67,
                       f"Expected bid_ask_ratio < 0.67 but got {metrics['bid_ask_ratio']}")
        
        # Check for direction-aware details in macro mode
        if result.get('analysis_mode') == 'macro':
            self.assertIn('trade_direction', metrics)
            self.assertEqual(metrics['trade_direction'], "SELL")
            
            # Check for SL/TP descriptions
            self.assertIn('sl_description', metrics)
            self.assertIn('tp_description', metrics)
            self.assertEqual(metrics['sl_description'], "above entry")
            self.assertEqual(metrics['tp_description'], "below entry")
            
            # Check risk-reward ratio exists
            self.assertIn('risk_reward_ratio', metrics)
            self.assertIsInstance(metrics['risk_reward_ratio'], (int, float))
        
    def test_analysis_with_balanced_orderbook(self):
        """Test analysis results with balanced order book."""
        agent = LiquidityAnalystAgent(data_fetcher=MockBalancedDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Expect a NEUTRAL signal due to balanced order book
        self.assertEqual(result['signal'], "NEUTRAL",
                        f"Expected NEUTRAL signal but got {result['signal']} with explanation: {result.get('explanation')}")
        
        # Check the metrics
        metrics = result['metrics']
        self.assertIn('bid_ask_ratio', metrics)
        self.assertTrue(0.9 <= metrics['bid_ask_ratio'] <= 1.1,
                       f"Expected bid_ask_ratio between 0.9 and 1.1 but got {metrics['bid_ask_ratio']}")
        
    def test_spread_calculation(self):
        """Test if spread is calculated correctly."""
        agent = LiquidityAnalystAgent(data_fetcher=MockDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Check spread metrics
        metrics = result['metrics']
        self.assertIn('spread', metrics)
        self.assertIn('spread_pct', metrics)
        self.assertIsInstance(metrics['spread'], (int, float))
        self.assertIsInstance(metrics['spread_pct'], (int, float))
        
    def test_direction_aware_sl_tp(self):
        """Test if SL/TP are properly direction-aware in macro mode."""
        # Test with ask-heavy (SELL) data
        agent = LiquidityAnalystAgent(data_fetcher=MockAskHeavyDataFetcher())
        # Force macro mode with 4h interval
        sell_result = agent.analyze(symbol="BTC/USDT", interval="4h")
        
        # Test with bid-heavy (BUY) data
        agent = LiquidityAnalystAgent(data_fetcher=MockBidHeavyDataFetcher())
        # Force macro mode with 4h interval
        buy_result = agent.analyze(symbol="BTC/USDT", interval="4h") 
        
        # Check if both results use macro mode
        self.assertEqual(sell_result.get('analysis_mode'), 'macro', 
                        "SELL test should use macro mode with 4h interval")
        self.assertEqual(buy_result.get('analysis_mode'), 'macro',
                        "BUY test should use macro mode with 4h interval")
        
        # For SELL signals, SL should be above entry and TP below entry
        if sell_result['signal'] == 'SELL':
            self.assertEqual(sell_result['metrics'].get('trade_direction'), 'SELL')
            self.assertEqual(sell_result['metrics'].get('sl_description'), 'above entry')
            self.assertEqual(sell_result['metrics'].get('tp_description'), 'below entry')
            # Stop loss should be numerically greater than entry for SELL
            self.assertGreater(sell_result.get('stop_loss_zone', 0), 
                              sell_result.get('entry_zone', 0))
            # Take profit should be numerically less than entry for SELL
            self.assertLess(sell_result['metrics'].get('suggested_take_profit', 999999), 
                           sell_result.get('entry_zone', 999999))
        
        # For BUY signals, SL should be below entry and TP above entry
        if buy_result['signal'] == 'BUY':
            self.assertEqual(buy_result['metrics'].get('trade_direction'), 'BUY')
            self.assertEqual(buy_result['metrics'].get('sl_description'), 'below entry')
            self.assertEqual(buy_result['metrics'].get('tp_description'), 'above entry')
            # Stop loss should be numerically less than entry for BUY
            self.assertLess(buy_result.get('stop_loss_zone', 999999), 
                           buy_result.get('entry_zone', 0))
            # Take profit should be numerically greater than entry for BUY
            self.assertGreater(buy_result['metrics'].get('suggested_take_profit', 0), 
                              buy_result.get('entry_zone', 999999))

def main():
    """Run the test suite."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLiquidityAnalystAgent))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())