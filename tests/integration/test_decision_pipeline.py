#!/usr/bin/env python3
# Description: Tests the integration of analysts and decision agent in the trading pipeline

import sys
import os
import unittest
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required components
try:
    from agents import (
        TechnicalAnalystAgent,
        LiquidityAnalystAgent,
        FundingRateAnalystAgent,
        OpenInterestAnalystAgent,
        SentimentAggregatorAgent,
        DecisionAgent
    )
except ImportError as e:
    print(f"Error importing required agents: {str(e)}")
    print("Make sure all agent components are properly implemented.")
    sys.exit(1)

# Import mock data provider
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.test_technical_analyst import MockDataFetcher as TechnicalMockDataFetcher
from agents.test_liquidity_analyst import MockDataFetcher as LiquidityMockDataFetcher

class MockDataFetcher:
    """Comprehensive mock data fetcher for integration testing."""
    
    def __init__(self):
        """Initialize with data from specialized mock fetchers."""
        # Get technical data
        self.technical_data = TechnicalMockDataFetcher()._generate_default_mock_data()
        
        # Get liquidity data
        self.liquidity_data = LiquidityMockDataFetcher()._generate_default_mock_data()
        
        # Generate additional data types needed for all agent types
        self._generate_additional_data()
        
    def _generate_additional_data(self):
        """Generate funding rate and open interest data."""
        current_price = self.technical_data['current_price']
        timestamp_base = int(datetime.now().timestamp() * 1000)
        
        # Generate funding rate data
        funding_rates = []
        base_rate = 0.0001  # 0.01% per 8 hours
        for i in range(30):
            # Vary funding rate to simulate different market conditions
            if i < 10:
                # Positive funding rates (longs pay shorts)
                rate = base_rate * (1 + i * 0.1)
            elif i < 20:
                # Declining funding rates
                rate = base_rate * (1 - (i - 10) * 0.05)
            else:
                # Negative funding rates (shorts pay longs)
                rate = -base_rate * (1 + (i - 20) * 0.1)
                
            funding_rates.append({
                'symbol': 'BTCUSDT',
                'timestamp': timestamp_base - (30 - i) * 8 * 3600 * 1000,
                'rate': rate
            })
            
        # Generate open interest data
        open_interest = []
        base_oi = 100000000  # 100 million USD
        for i in range(30):
            # Create divergence pattern between price and OI
            if i < 15:
                # OI and price rising together
                factor = 1 + i * 0.01
            else:
                # Price falling but OI still rising (bearish divergence)
                factor = 1 + i * 0.015
                
            open_interest.append({
                'symbol': 'BTCUSDT',
                'timestamp': timestamp_base - (30 - i) * 4 * 3600 * 1000,
                'openInterest': base_oi * factor
            })
            
        # Generate sentiment data
        sentiment_data = {
            'news': [
                {'title': 'Bitcoin reaches new high', 'sentiment': 'positive', 'source': 'CryptoNews'},
                {'title': 'Regulatory concerns for crypto', 'sentiment': 'negative', 'source': 'FinanceDaily'},
                {'title': 'Institutional adoption continues', 'sentiment': 'positive', 'source': 'CoinDesk'}
            ],
            'social': [
                {'source': 'Twitter', 'sentiment': 'mixed', 'volume': 'high'},
                {'source': 'Reddit', 'sentiment': 'positive', 'volume': 'medium'},
                {'source': 'Telegram', 'sentiment': 'neutral', 'volume': 'low'}
            ]
        }
        
        # Store all the data
        self.funding_rates = funding_rates
        self.open_interest = open_interest
        self.sentiment_data = sentiment_data
        
    def fetch_ohlcv(self, symbol, interval='1h', limit=100):
        """Return mock OHLCV data."""
        return self.technical_data['ohlcv'][-limit:]
    
    def fetch_market_depth(self, symbol, limit=20):
        """Return mock order book data."""
        return self.liquidity_data['order_book_bid_heavy']
    
    def fetch_funding_rates(self, symbol, limit=30):
        """Return mock funding rate data."""
        return self.funding_rates[-limit:]
    
    def fetch_futures_open_interest(self, symbol, interval='4h', limit=30):
        """Return mock open interest data."""
        return self.open_interest[-limit:]
    
    def get_ticker(self, symbol):
        """Return mock ticker data."""
        price = self.technical_data['current_price']
        return {
            'symbol': symbol,
            'last': price,
            'bid': price * 0.999,
            'ask': price * 1.001
        }
    
    def get_current_price(self, symbol):
        """Return mock current price."""
        return self.technical_data['current_price']
    
    def fetch_sentiment_data(self, symbol):
        """Return mock sentiment data."""
        return self.sentiment_data

class TestTradingDecisionPipeline(unittest.TestCase):
    """Test suite for the full trading decision pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock data fetcher for all agents
        self.data_fetcher = MockDataFetcher()
        
        # Initialize all analyst agents
        self.technical_analyst = TechnicalAnalystAgent(data_fetcher=self.data_fetcher)
        self.liquidity_analyst = LiquidityAnalystAgent(data_fetcher=self.data_fetcher)
        self.funding_rate_analyst = FundingRateAnalystAgent(data_fetcher=self.data_fetcher)
        self.open_interest_analyst = OpenInterestAnalystAgent(data_fetcher=self.data_fetcher)
        self.sentiment_analyst = SentimentAggregatorAgent(data_fetcher=self.data_fetcher)
        
        # Initialize decision agent
        self.decision_agent = DecisionAgent()
        
    def test_end_to_end_decision_pipeline(self):
        """Test the end-to-end decision pipeline."""
        # Set test parameters
        symbol = "BTC/USDT"
        interval = "1h"
        
        # Run all analyst agents
        technical_analysis = self.technical_analyst.analyze(symbol=symbol, interval=interval)
        liquidity_analysis = self.liquidity_analyst.analyze(symbol=symbol, interval=interval)
        funding_rate_analysis = self.funding_rate_analyst.analyze(symbol=symbol, interval=interval)
        open_interest_analysis = self.open_interest_analyst.analyze(symbol=symbol, interval=interval)
        sentiment_analysis = self.sentiment_analyst.analyze(symbol=symbol, interval=interval)
        
        # Verify analyses
        self._verify_analysis_structure(technical_analysis, "TechnicalAnalystAgent")
        self._verify_analysis_structure(liquidity_analysis, "LiquidityAnalystAgent")
        self._verify_analysis_structure(funding_rate_analysis, "FundingRateAnalystAgent")
        self._verify_analysis_structure(open_interest_analysis, "OpenInterestAnalystAgent")
        self._verify_analysis_structure(sentiment_analysis, "SentimentAggregatorAgent")
        
        # Combine analyses
        analyses = [
            technical_analysis,
            liquidity_analysis,
            funding_rate_analysis,
            open_interest_analysis,
            sentiment_analysis
        ]
        
        # Run decision agent
        decision = self.decision_agent.make_decision(symbol=symbol, interval=interval, analyses=analyses)
        
        # Verify decision
        self._verify_decision_structure(decision)
        
        # Print decision results for debugging
        print(f"\nDecision: {decision['signal']} with {decision['confidence']}% confidence")
        print(f"Reasoning: {decision['reasoning']}")
        
        # Print contributing signals
        print("\nContributing signals:")
        for agent_name, contribution in decision.get('agent_contributions', {}).items():
            print(f"  {agent_name}: {contribution['signal']} ({contribution['confidence']}%)")
        
    def _verify_analysis_structure(self, analysis: Dict[str, Any], expected_agent: str):
        """Verify that an analysis has the correct structure."""
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get('agent'), expected_agent)
        self.assertIn('signal', analysis)
        self.assertIn('confidence', analysis)
        self.assertIn(analysis['signal'], ["BUY", "SELL", "NEUTRAL"])
        self.assertIsInstance(analysis['confidence'], int)
        self.assertTrue(0 <= analysis['confidence'] <= 100)
        
    def _verify_decision_structure(self, decision: Dict[str, Any]):
        """Verify that a decision has the correct structure."""
        self.assertIsInstance(decision, dict)
        self.assertIn('signal', decision)
        self.assertIn('confidence', decision)
        self.assertIn('reasoning', decision)
        self.assertIn('agent_contributions', decision)
        self.assertIn('timestamp', decision)
        
        self.assertIn(decision['signal'], ["BUY", "SELL", "NEUTRAL", "HOLD"])
        self.assertIsInstance(decision['confidence'], int)
        self.assertTrue(0 <= decision['confidence'] <= 100)
        
    def test_decision_with_missing_analyses(self):
        """Test decision-making with missing analyses."""
        # Set test parameters
        symbol = "BTC/USDT"
        interval = "1h"
        
        # Run only some analyst agents
        technical_analysis = self.technical_analyst.analyze(symbol=symbol, interval=interval)
        liquidity_analysis = self.liquidity_analyst.analyze(symbol=symbol, interval=interval)
        
        # Only include two analyses
        analyses = [technical_analysis, liquidity_analysis]
        
        # Run decision agent
        decision = self.decision_agent.make_decision(symbol=symbol, interval=interval, analyses=analyses)
        
        # Verify decision
        self._verify_decision_structure(decision)
        
        # Should still have valid decision with only partial data
        self.assertIn(decision['signal'], ["BUY", "SELL", "NEUTRAL", "HOLD"])
        
    def test_decision_with_conflicting_signals(self):
        """Test decision-making with conflicting signals."""
        # Set test parameters
        symbol = "BTC/USDT"
        interval = "1h"
        
        # Create mock analyses with conflicting signals
        conflicting_analyses = [
            {
                "agent": "TechnicalAnalystAgent",
                "signal": "BUY",
                "confidence": 80,
                "timestamp": datetime.now().isoformat()
            },
            {
                "agent": "LiquidityAnalystAgent",
                "signal": "SELL",
                "confidence": 80,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Run decision agent
        decision = self.decision_agent.make_decision(symbol=symbol, interval=interval, analyses=conflicting_analyses)
        
        # Verify decision
        self._verify_decision_structure(decision)
        
        # Confidence should be lower with conflicting signals
        self.assertTrue(decision['confidence'] < 80)
        
    def test_full_pipeline_with_different_symbols(self):
        """Test the pipeline with different symbols."""
        # Test symbols
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        interval = "1h"
        
        for symbol in symbols:
            # Run technical analyst (just as a representative)
            analysis = self.technical_analyst.analyze(symbol=symbol, interval=interval)
            
            # Verify analysis
            self.assertEqual(analysis.get('symbol'), symbol)
            self._verify_analysis_structure(analysis, "TechnicalAnalystAgent")

def main():
    """Run the test suite."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTradingDecisionPipeline))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())