#!/usr/bin/env python3
# Description: Tests the SentimentAggregatorAgent's ability to analyze news and social sentiment

import sys
import os
import unittest
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from agents import SentimentAggregatorAgent
    from core.logging import decision_logger
    from tests.helpers.test_utils import TestCase, DecisionLoggerExtensions
except ImportError as e:
    print(f"Error: {e}. Make sure the required modules are properly implemented.")
    sys.exit(1)

# Patch the decision_logger with the create_summary_from_result method
decision_logger.create_summary_from_result = lambda *args, **kwargs: DecisionLoggerExtensions.create_summary_from_result(decision_logger, *args, **kwargs)

class MockDataFetcher:
    """Mock data fetcher for testing SentimentAggregatorAgent."""
    
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
        """Generate default mock data for sentiment testing."""
        # Mock current price
        current_price = 45000.0
        
        # Generate sentiment data with mixed signals
        sentiment_data = {
            'news': [
                {'title': 'Bitcoin reaches new high', 'sentiment': 'positive', 'source': 'CryptoNews'},
                {'title': 'Regulatory concerns for crypto', 'sentiment': 'negative', 'source': 'FinanceDaily'},
                {'title': 'Institutional adoption continues', 'sentiment': 'positive', 'source': 'CoinDesk'},
                {'title': 'Market volatility increases', 'sentiment': 'neutral', 'source': 'TokenInsider'},
                {'title': 'Bitcoin ETF inflows slow down', 'sentiment': 'negative', 'source': 'CoinTelegraph'}
            ],
            'social': [
                {'source': 'Twitter', 'sentiment': 'mixed', 'volume': 'high'},
                {'source': 'Reddit', 'sentiment': 'positive', 'volume': 'medium'},
                {'source': 'Telegram', 'sentiment': 'neutral', 'volume': 'low'},
                {'source': 'Discord', 'sentiment': 'negative', 'volume': 'medium'},
                {'source': 'TikTok', 'sentiment': 'positive', 'volume': 'high'}
            ]
        }
        
        # Generate positive-biased sentiment data
        positive_sentiment_data = {
            'news': [
                {'title': 'Bitcoin reaches all-time high', 'sentiment': 'positive', 'source': 'CryptoNews'},
                {'title': 'Major bank adopts crypto payments', 'sentiment': 'positive', 'source': 'FinanceDaily'},
                {'title': 'Institutional adoption accelerates', 'sentiment': 'positive', 'source': 'CoinDesk'},
                {'title': 'New crypto-friendly regulations', 'sentiment': 'positive', 'source': 'TokenInsider'},
                {'title': 'Bitcoin ETF sees record inflows', 'sentiment': 'positive', 'source': 'CoinTelegraph'}
            ],
            'social': [
                {'source': 'Twitter', 'sentiment': 'positive', 'volume': 'high'},
                {'source': 'Reddit', 'sentiment': 'positive', 'volume': 'high'},
                {'source': 'Telegram', 'sentiment': 'positive', 'volume': 'medium'},
                {'source': 'Discord', 'sentiment': 'positive', 'volume': 'medium'},
                {'source': 'TikTok', 'sentiment': 'positive', 'volume': 'high'}
            ]
        }
        
        # Generate negative-biased sentiment data
        negative_sentiment_data = {
            'news': [
                {'title': 'Bitcoin crashes below support', 'sentiment': 'negative', 'source': 'CryptoNews'},
                {'title': 'Major country bans crypto', 'sentiment': 'negative', 'source': 'FinanceDaily'},
                {'title': 'Exchange hack causes panic', 'sentiment': 'negative', 'source': 'CoinDesk'},
                {'title': 'Strict regulations proposed', 'sentiment': 'negative', 'source': 'TokenInsider'},
                {'title': 'Institutional investors exit positions', 'sentiment': 'negative', 'source': 'CoinTelegraph'}
            ],
            'social': [
                {'source': 'Twitter', 'sentiment': 'negative', 'volume': 'high'},
                {'source': 'Reddit', 'sentiment': 'negative', 'volume': 'high'},
                {'source': 'Telegram', 'sentiment': 'negative', 'volume': 'medium'},
                {'source': 'Discord', 'sentiment': 'negative', 'volume': 'medium'},
                {'source': 'TikTok', 'sentiment': 'negative', 'volume': 'high'}
            ]
        }
        
        return {
            'sentiment_data': sentiment_data,
            'positive_sentiment_data': positive_sentiment_data,
            'negative_sentiment_data': negative_sentiment_data,
            'current_price': current_price,
            'symbol': 'BTC/USDT'
        }
    
    def fetch_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Return mock sentiment data."""
        return self.mock_data['sentiment_data']
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Return mock ticker data."""
        price = self.mock_data['current_price']
        return {
            'symbol': symbol,
            'last': price,
            'bid': price * 0.999,
            'ask': price * 1.001
        }
    
    def get_current_price(self, symbol: str) -> float:
        """Return mock current price."""
        return self.mock_data['current_price']

class MockPositiveSentimentFetcher(MockDataFetcher):
    """Mock data fetcher that returns positive sentiment data."""
    def fetch_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        return self.mock_data['positive_sentiment_data']

class MockNegativeSentimentFetcher(MockDataFetcher):
    """Mock data fetcher that returns negative sentiment data."""
    def fetch_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        return self.mock_data['negative_sentiment_data']

class TestSentimentAggregatorAgent(TestCase):
    """Test suite for the SentimentAggregatorAgent class."""
    
    def test_initialization(self):
        """Test if agent initializes correctly."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        self.assertEqual(agent.name, "SentimentAggregatorAgent")
        self.assertTrue(hasattr(agent, 'data_fetcher'))
        
    def test_analyze_method_exists(self):
        """Test if analyze method exists and is callable."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        self.assertTrue(hasattr(agent, 'analyze'))
        self.assertTrue(callable(getattr(agent, 'analyze')))
        
    def test_analyze_returns_valid_result(self):
        """Test if analyze returns a valid result structure."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Use the enhanced TestCase assertion
        self.assertIsValidAgentAnalysis(result, "SentimentAggregatorAgent")
        
        # Additional checks
        self.assertIn('current_price', result)
        self.assertIn('analysis_summary', result)
        
    def test_analyze_with_positive_sentiment(self):
        """Test analysis results with positive sentiment data."""
        agent = SentimentAggregatorAgent(data_fetcher=MockPositiveSentimentFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Expect a BUY signal due to positive sentiment
        self.assertEqual(result['signal'], "BUY", 
                        f"Expected BUY signal but got {result['signal']} with explanation: {result.get('analysis_summary')}")
        self.assertTrue(result['confidence'] > 65, 
                       f"Expected confidence > 65 but got {result['confidence']}")
        
    def test_analyze_with_negative_sentiment(self):
        """Test analysis results with negative sentiment data."""
        agent = SentimentAggregatorAgent(data_fetcher=MockNegativeSentimentFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Expect a SELL signal due to negative sentiment
        self.assertEqual(result['signal'], "SELL", 
                        f"Expected SELL signal but got {result['signal']} with explanation: {result.get('analysis_summary')}")
        self.assertTrue(result['confidence'] > 65, 
                       f"Expected confidence > 65 but got {result['confidence']}")
        
    def test_analyze_with_mixed_sentiment(self):
        """Test analysis results with mixed sentiment data."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Mixed sentiment typically gives neutral signal, but check the structure
        self.assertIn(result['signal'], ["BUY", "SELL", "NEUTRAL"], 
                     f"Signal {result['signal']} is not a valid signal")
        
    def test_different_timeframes(self):
        """Test if the agent handles different timeframes correctly."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        
        # Try different timeframes
        timeframes = ["1h", "4h", "1d"]
        
        for timeframe in timeframes:
            result = agent.analyze(symbol="BTC/USDT", interval=timeframe)
            self.assertIsValidAgentAnalysis(result, "SentimentAggregatorAgent")
            self.assertEqual(result.get('interval', None), timeframe, 
                           f"Expected interval {timeframe} but got {result.get('interval')}")
            
    def test_different_symbols(self):
        """Test if the agent handles different symbols correctly."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        
        # Try different symbols
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        
        for symbol in symbols:
            result = agent.analyze(symbol=symbol, interval="1h")
            self.assertIsValidAgentAnalysis(result, "SentimentAggregatorAgent")
            self.assertEqual(result.get('symbol', None), symbol, 
                           f"Expected symbol {symbol} but got {result.get('symbol')}")
            
    def test_decision_logging_extension(self):
        """Test if the decision logging extension works."""
        agent = SentimentAggregatorAgent(data_fetcher=MockDataFetcher())
        result = agent.analyze(symbol="BTC/USDT", interval="1h")
        
        # Test the create_summary_from_result extension
        summary = decision_logger.create_summary_from_result(
            "SentimentAggregatorAgent", 
            result, 
            "BTC/USDT"
        )
        
        # Check that the summary was created
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['agent'], "SentimentAggregatorAgent")
        self.assertEqual(summary['signal'], result['signal'])
        self.assertEqual(summary['confidence'], result['confidence'])

def main():
    """Run the test suite."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSentimentAggregatorAgent))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())