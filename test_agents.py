"""
Test script for individual agent testing.

This script allows testing of individual analyst agents in isolation to
ensure they are properly implemented before integrating into the full system.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_agents')

# Import the agent classes
try:
    from agents import (
        BaseAgent,
        BaseAnalystAgent,
        BaseDecisionAgent,
        TechnicalAnalystAgent,
        LiquidityAnalystAgent,
        FundingRateAnalystAgent,
        OpenInterestAnalystAgent,
        SentimentAggregatorAgent
    )
    
    # Create a mock data fetcher for testing
    class MockDataFetcher:
        """Mock data fetcher for testing agents without real API calls."""
        
        def __init__(self):
            self.mock_data = self._generate_mock_data()
            
        def _generate_mock_data(self) -> Dict[str, Any]:
            """Generate mock data for various data types."""
            # Mock OHLCV data
            ohlcv_data = []
            base_price = 50000.0
            for i in range(100):
                # Create some price movement
                factor = 1.0 + (i % 10) * 0.01 * (1 if i % 20 < 10 else -1)
                price = base_price * factor
                
                ohlcv_data.append({
                    'timestamp': int(datetime.now().timestamp() * 1000) - (100 - i) * 3600 * 1000,
                    'open': price * 0.99,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': 1000000 * (1 + (i % 5) * 0.2)
                })
                
            # Mock order book data
            order_book = {
                'bids': [
                    [str(base_price * 0.99), "10.5"],
                    [str(base_price * 0.98), "25.3"],
                    [str(base_price * 0.97), "30.1"],
                    [str(base_price * 0.96), "42.8"],
                    [str(base_price * 0.95), "50.2"]
                ],
                'asks': [
                    [str(base_price * 1.01), "8.3"],
                    [str(base_price * 1.02), "15.7"],
                    [str(base_price * 1.03), "22.4"],
                    [str(base_price * 1.04), "35.1"],
                    [str(base_price * 1.05), "48.6"]
                ]
            }
            
            # Mock funding rate data
            funding_data = []
            base_rate = 0.0001  # 0.01% per 8 hours
            for i in range(30):
                # Create some oscillation in funding rate
                rate = base_rate * (1 + (i % 15) * 0.2 * (1 if i % 30 < 15 else -1))
                
                funding_data.append({
                    'symbol': 'BTCUSDT',
                    'timestamp': int(datetime.now().timestamp() * 1000) - (30 - i) * 8 * 3600 * 1000,
                    'rate': rate
                })
                
            # Mock open interest data
            open_interest_data = []
            base_oi = 100000000  # 100 million USD
            for i in range(30):
                # Create some trend in open interest
                oi = base_oi * (1 + i * 0.005)
                
                open_interest_data.append({
                    'symbol': 'BTCUSDT',
                    'timestamp': int(datetime.now().timestamp() * 1000) - (30 - i) * 4 * 3600 * 1000,
                    'openInterest': oi
                })
                
            # Mock ticker data
            ticker = {
                'symbol': 'BTCUSDT',
                'last': base_price,
                'bid': base_price * 0.999,
                'ask': base_price * 1.001,
                'volume': 10000,
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            
            # News and social media sentiment data
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
            
            return {
                'ohlcv': ohlcv_data,
                'order_book': order_book,
                'funding_rates': funding_data,
                'open_interest': open_interest_data,
                'ticker': ticker,
                'sentiment': sentiment_data
            }
            
        def fetch_ohlcv(self, symbol, interval='1h', limit=100):
            """Return mock OHLCV data."""
            return self.mock_data['ohlcv'][-limit:]
            
        def fetch_market_depth(self, symbol, limit=20):
            """Return mock order book data."""
            return self.mock_data['order_book']
            
        def fetch_funding_rates(self, symbol, limit=30):
            """Return mock funding rate data."""
            return self.mock_data['funding_rates'][-limit:]
            
        def fetch_futures_open_interest(self, symbol, interval='4h', limit=30):
            """Return mock open interest data."""
            return self.mock_data['open_interest'][-limit:]
            
        def get_ticker(self, symbol):
            """Return mock ticker data."""
            return self.mock_data['ticker']
            
        def get_current_price(self, symbol):
            """Return mock current price."""
            return self.mock_data['ticker']['last']
            
        def fetch_sentiment_data(self, symbol):
            """Return mock sentiment data."""
            return self.mock_data['sentiment']
    
    def test_analyst_agent(agent_class, agent_name: str, symbol: str = "BTC/USDT", interval: str = "1h"):
        """Test a specific analyst agent with mock data."""
        logger.info(f"Testing {agent_name}...")
        
        # Create a mock data fetcher
        data_fetcher = MockDataFetcher()
        
        # Create the agent
        agent = agent_class(data_fetcher=data_fetcher)
        
        # Run the agent's analysis
        try:
            result = agent.analyze(symbol=symbol, interval=interval)
            
            # Print the results
            logger.info(f"Signal: {result.get('signal')}")
            logger.info(f"Confidence: {result.get('confidence')}%")
            
            explanation = result.get('explanation', [])
            if isinstance(explanation, list):
                for exp in explanation:
                    logger.info(f"Explanation: {exp}")
            else:
                logger.info(f"Explanation: {explanation}")
                
            # Print metrics (truncated for readability)
            metrics = result.get('metrics', {})
            if metrics:
                logger.info("Key metrics:")
                for key, value in list(metrics.items())[:5]:
                    logger.info(f"  {key}: {value}")
                    
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Execution time: {result.get('execution_time_seconds', 0):.4f} seconds")
            logger.info("-" * 80)
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing {agent_name}: {str(e)}")
            return None
    
    def run_all_tests():
        """Run tests for all available analyst agents."""
        logger.info("Starting agent tests...")
        
        # Define the test cases
        agents_to_test = [
            (TechnicalAnalystAgent, "TechnicalAnalystAgent"),
            (LiquidityAnalystAgent, "LiquidityAnalystAgent"),
            (FundingRateAnalystAgent, "FundingRateAnalystAgent"),
            (OpenInterestAnalystAgent, "OpenInterestAnalystAgent"),
            (SentimentAggregatorAgent, "SentimentAggregatorAgent")
        ]
        
        results = {}
        for agent_class, agent_name in agents_to_test:
            try:
                logger.info("=" * 80)
                logger.info(f"Testing {agent_name}")
                logger.info("=" * 80)
                
                result = test_analyst_agent(agent_class, agent_name)
                if result:
                    results[agent_name] = {
                        "signal": result.get("signal"),
                        "confidence": result.get("confidence"),
                        "status": result.get("status")
                    }
            except Exception as e:
                logger.error(f"Failed to test {agent_name}: {str(e)}")
                results[agent_name] = {"status": "error", "error": str(e)}
                
        logger.info("=" * 80)
        logger.info("Summary of Results:")
        logger.info("=" * 80)
        
        for name, result in results.items():
            status = "✅" if result.get("status") == "success" else "❌"
            signal = result.get("signal", "N/A")
            confidence = result.get("confidence", "N/A")
            logger.info(f"{status} {name}: {signal} ({confidence}% confidence)")
            
        logger.info("=" * 80)
        logger.info("Agent testing completed.")
        
        return results

except ImportError as e:
    logger.error(f"Error importing agents: {str(e)}")
    logger.error("Make sure all agent classes are properly implemented and accessible")
    sys.exit(1)

if __name__ == "__main__":
    run_all_tests()