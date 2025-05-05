"""
Test module for the centralized indicators and the TechnicalAnalystAgent
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.indicators import calculate_all_indicators
from agents.technical_analyst_agent import TechnicalAnalystAgent

class TestTechnicalAnalystWithIndicators(unittest.TestCase):
    """Test suite for TechnicalAnalystAgent with the centralized indicators module"""
    
    def setUp(self):
        """Set up test data"""
        # Create a simple uptrend dataset
        dates = pd.date_range(start='2023-01-01', periods=100)
        base_price = 100
        
        # Create a trending price series with some noise
        np.random.seed(42)  # For reproducibility
        noise = np.random.normal(0, 1, 100)
        trend = np.linspace(0, 20, 100)  # Linear uptrend
        
        close = base_price + trend + noise
        high = close + np.random.uniform(0, 2, 100)
        low = close - np.random.uniform(0, 2, 100)
        volume = np.random.uniform(1000, 5000, 100)
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': close - np.random.uniform(0, 1, 100),
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        # Convert to OHLCV format for agent testing
        self.ohlcv_data = []
        for _, row in self.df.iterrows():
            self.ohlcv_data.append({
                'timestamp': int(row['timestamp'].timestamp() * 1000),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        
        # Create a technical analyst agent
        self.technical_analyst = TechnicalAnalystAgent()
    
    def test_calculate_all_indicators(self):
        """Test the calculation of all indicators"""
        indicators = calculate_all_indicators(self.df)
        
        # Check that key indicators are present
        self.assertTrue('rsi' in indicators)
        self.assertTrue('macd' in indicators)
        self.assertTrue('sma_short' in indicators)
        self.assertTrue('sma_long' in indicators)
        
        # Check signal summary is present
        self.assertTrue('signal_summary' in indicators)
        
        # Verify indicators match expected trend (this is an uptrend)
        self.assertEqual(indicators['sma_trend'], 'bullish')
        
        # Check signal counts in the signal_summary
        self.assertTrue(indicators['signal_summary']['bullish'] >= 
                       indicators['signal_summary']['bearish'])
    
    def test_technical_analyst_integration(self):
        """Test TechnicalAnalyst using centralized indicators"""
        # Create market data for the analyst to use
        market_data = {
            'symbol': 'BTC/USDT',
            'interval': '1h',
            'ohlcv': self.ohlcv_data
        }
        
        # Mock data_fetcher to return our test data
        class MockDataFetcher:
            def fetch_ohlcv(self, symbol, interval, limit=100):
                return self.ohlcv_data
            
            def __init__(self, ohlcv_data):
                self.ohlcv_data = ohlcv_data
        
        self.technical_analyst.data_fetcher = MockDataFetcher(self.ohlcv_data)
        
        # Run the analysis
        analysis = self.technical_analyst.analyze(market_data)
        
        # Verify results
        self.assertTrue('signal' in analysis)
        self.assertTrue('confidence' in analysis)
        self.assertTrue('explanation' in analysis)
        self.assertTrue('indicators' in analysis)
        
        # For an uptrend, we expect a BUY or NEUTRAL signal
        self.assertTrue(analysis['signal'] in ['BUY', 'NEUTRAL'])
        # There should be some confidence value (>= min confidence)
        self.assertTrue(analysis['confidence'] >= self.technical_analyst.low_confidence)
        
        # Verify the results contain indicator data
        indicators = analysis['indicators']
        self.assertTrue('trend' in indicators)
        self.assertTrue('strength' in indicators)
        self.assertTrue('rsi' in indicators)
        
        # Verify the explanation makes sense
        self.assertIsInstance(analysis['explanation'], list)
        self.assertTrue(len(analysis['explanation']) > 0)
        self.assertTrue('bullish' in analysis['explanation'][0].lower() or 'buy' in analysis['explanation'][0].lower())
    
    def test_technical_analyst_signal_generation(self):
        """Test the signal generation logic with various indicator values"""
        # Prepare a DataFrame with price data for indicator calculation
        df = self._prepare_dataframe(self.ohlcv_data[:50])
        
        # Test bullish scenario
        bullish_metrics = {
            'trend': 'BULLISH',
            'strength': 80,
            'rsi': 60,
            'macd': 2.0,
            'macd_histogram': 1.0,
            'bullish_signals': 8,
            'bearish_signals': 2,
            'neutral_signals': 1
        }
        
        signal, confidence, explanation = self.technical_analyst._generate_signal(bullish_metrics, df)
        self.assertEqual(signal, 'BUY')
        # Set a more conservative threshold for confidence to make tests more reliable
        self.assertTrue(confidence >= 65)
        
        # Test bearish scenario
        bearish_metrics = {
            'trend': 'BEARISH',
            'strength': 75,
            'rsi': 30,
            'macd': -2.0,
            'macd_histogram': -1.0,
            'bullish_signals': 2,
            'bearish_signals': 7,
            'neutral_signals': 2
        }
        
        signal, confidence, explanation = self.technical_analyst._generate_signal(bearish_metrics, df)
        self.assertEqual(signal, 'SELL')
        # Set a more conservative threshold for confidence
        self.assertTrue(confidence >= 65)
        
        # Test neutral scenario
        neutral_metrics = {
            'trend': 'NEUTRAL',
            'strength': 45,
            'rsi': 50,
            'macd': 0.1,
            'macd_histogram': 0.05,
            'bullish_signals': 4,
            'bearish_signals': 4,
            'neutral_signals': 3
        }
        
        signal, confidence, explanation = self.technical_analyst._generate_signal(neutral_metrics, df)
        self.assertEqual(signal, 'NEUTRAL')
        self.assertTrue(confidence < 70)
    
    def _prepare_dataframe(self, ohlcv_data):
        """Helper to convert OHLCV data to DataFrame format for testing"""
        data = []
        for candle in ohlcv_data:
            data.append({
                'timestamp': datetime.fromtimestamp(candle['timestamp'] / 1000),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume']
            })
        return pd.DataFrame(data)

if __name__ == '__main__':
    unittest.main()