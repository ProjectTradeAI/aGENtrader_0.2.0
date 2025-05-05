"""
Tests for the technical indicators module
"""

import unittest
import pandas as pd
import numpy as np
from utils.indicators import (
    calculate_sma, calculate_ema, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_stochastic_rsi, calculate_adx,
    calculate_vwma, calculate_parabolic_sar, calculate_donchian_channels,
    calculate_ichimoku_cloud, calculate_atr, calculate_all_indicators
)

class TestIndicators(unittest.TestCase):
    """Test suite for technical indicators module"""
    
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
    
    def test_sma(self):
        """Test SMA calculation"""
        sma = calculate_sma(self.df['close'], 20)
        self.assertEqual(len(sma), len(self.df))
        self.assertTrue(np.isnan(sma.iloc[0]))
        self.assertFalse(np.isnan(sma.iloc[-1]))
    
    def test_ema(self):
        """Test EMA calculation"""
        ema = calculate_ema(self.df['close'], 20)
        self.assertEqual(len(ema), len(self.df))
        self.assertFalse(np.isnan(ema.iloc[-1]))
    
    def test_rsi(self):
        """Test RSI calculation"""
        rsi = calculate_rsi(self.df['close'], 14)
        self.assertEqual(len(rsi), len(self.df))
        self.assertTrue(all(0 <= x <= 100 for x in rsi.dropna()))
    
    def test_macd(self):
        """Test MACD calculation"""
        macd_data = calculate_macd(self.df['close'])
        self.assertTrue('macd' in macd_data)
        self.assertTrue('signal' in macd_data)
        self.assertTrue('histogram' in macd_data)
        self.assertEqual(len(macd_data['macd']), len(self.df))
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        bb_data = calculate_bollinger_bands(self.df['close'])
        self.assertTrue('middle' in bb_data)
        self.assertTrue('upper' in bb_data)
        self.assertTrue('lower' in bb_data)
        self.assertTrue('percent_b' in bb_data)
        self.assertTrue('bandwidth' in bb_data)
        
        # Upper band should be higher than middle band
        self.assertTrue(all(bb_data['upper'].dropna() >= bb_data['middle'].dropna()))
        
        # Lower band should be lower than middle band
        self.assertTrue(all(bb_data['lower'].dropna() <= bb_data['middle'].dropna()))
    
    def test_stochastic_rsi(self):
        """Test Stochastic RSI calculation"""
        stoch_data = calculate_stochastic_rsi(self.df['close'])
        self.assertTrue('stoch_rsi' in stoch_data)
        self.assertTrue('k' in stoch_data)
        self.assertTrue('d' in stoch_data)
        
        # Values should be between 0 and 100
        self.assertTrue(all(0 <= x <= 100 for x in stoch_data['stoch_rsi'].dropna()))
    
    def test_adx(self):
        """Test ADX calculation"""
        adx_data = calculate_adx(self.df['high'], self.df['low'], self.df['close'])
        self.assertTrue('adx' in adx_data)
        self.assertTrue('pos_di' in adx_data)
        self.assertTrue('neg_di' in adx_data)
        
        # ADX should be between 0 and 100
        self.assertTrue(all(0 <= x <= 100 for x in adx_data['adx'].dropna()))
    
    def test_vwma(self):
        """Test VWMA calculation"""
        vwma = calculate_vwma(self.df['close'], self.df['volume'])
        self.assertEqual(len(vwma), len(self.df))
    
    def test_parabolic_sar(self):
        """Test Parabolic SAR calculation"""
        sar_data = calculate_parabolic_sar(self.df['high'], self.df['low'], self.df['close'])
        self.assertTrue('sar' in sar_data)
        self.assertTrue('trend' in sar_data)
    
    def test_donchian_channels(self):
        """Test Donchian Channels calculation"""
        dc_data = calculate_donchian_channels(self.df['high'], self.df['low'])
        self.assertTrue('upper' in dc_data)
        self.assertTrue('middle' in dc_data)
        self.assertTrue('lower' in dc_data)
        self.assertTrue('breakout' in dc_data)
        
        # Upper band should always be higher than lower band
        self.assertTrue(all(dc_data['upper'].dropna() >= dc_data['lower'].dropna()))
    
    def test_ichimoku_cloud(self):
        """Test Ichimoku Cloud calculation"""
        ichimoku_data = calculate_ichimoku_cloud(self.df['high'], self.df['low'], self.df['close'])
        self.assertTrue('tenkan_sen' in ichimoku_data)
        self.assertTrue('kijun_sen' in ichimoku_data)
        self.assertTrue('senkou_span_a' in ichimoku_data)
        self.assertTrue('senkou_span_b' in ichimoku_data)
        self.assertTrue('chikou_span' in ichimoku_data)
    
    def test_atr(self):
        """Test ATR calculation"""
        atr = calculate_atr(self.df['high'], self.df['low'], self.df['close'])
        self.assertEqual(len(atr), len(self.df))
        self.assertTrue(all(x >= 0 for x in atr.dropna()))
    
    def test_calculate_all_indicators(self):
        """Test calculation of all indicators"""
        indicators = calculate_all_indicators(self.df)
        
        # Check that key indicators are present
        self.assertTrue('rsi' in indicators)
        self.assertTrue('macd' in indicators)
        self.assertTrue('bb_percent_b' in indicators)
        self.assertTrue('adx' in indicators)
        self.assertTrue('vwma' in indicators)
        self.assertTrue('donchian_breakout' in indicators)
        
        # Check that signals summary is present
        self.assertTrue('signal_summary' in indicators)
        
        # Check signals have been calculated
        self.assertTrue('bullish' in indicators['signal_summary'])
        self.assertTrue('bearish' in indicators['signal_summary'])
        self.assertTrue('neutral' in indicators['signal_summary'])

if __name__ == '__main__':
    unittest.main()