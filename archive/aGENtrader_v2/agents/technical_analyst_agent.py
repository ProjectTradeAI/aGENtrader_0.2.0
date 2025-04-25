"""
aGENtrader v2 Technical Analyst Agent

This module implements the TechnicalAnalystAgent class, which analyzes
market data using various technical indicators and generates trading signals.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import math
from collections import defaultdict

# Technical analysis libraries
import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice

# Import base agent
from aGENtrader_v2.agents.base_agent import BaseAnalystAgent

logger = logging.getLogger('aGENtrader.agents.technical')

class TechnicalAnalystAgent(BaseAnalystAgent):
    """
    Agent responsible for technical analysis of market data.
    
    This agent calculates various technical indicators and generates
    trading signals based on indicator values and crossovers.
    """

    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the technical analyst agent.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            config: Configuration parameters for technical analysis
        """
        super().__init__(data_fetcher, config)
        
        # Extract indicator configuration
        self.indicator_config = self.config.get('agents', {}).get('technical', {}).get('indicators', {})
        
        # Set up signal thresholds
        signal_thresholds = self.config.get('agents', {}).get('technical', {}).get('signal_thresholds', {})
        self.signal_thresholds = {
            'strong_buy': signal_thresholds.get('strong_buy', 75),
            'buy': signal_thresholds.get('buy', 60),
            'neutral': signal_thresholds.get('neutral', 40),
            'sell': signal_thresholds.get('sell', 25),
            'strong_sell': signal_thresholds.get('strong_sell', 10)
        }
        
        self.logger.debug(f"Initialized with signal thresholds: {self.signal_thresholds}")

    def analyze(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Perform technical analysis on market data.
        
        Args:
            symbol: Trading symbol (e.g., BITSTAMP_SPOT_BTC_USD)
            interval: Time interval (e.g., 1d, 4h, 1h)
            **kwargs: Additional parameters
            
        Returns:
            Analysis results including trading signal and confidence
        """
        # Validate input parameters
        if not self.validate_input(symbol, interval):
            return self.build_error_response(
                "InvalidInput", 
                "Invalid input parameters provided for technical analysis"
            )
        
        # Use default values if not provided
        symbol = symbol or self.config.get('default_symbol', 'BITSTAMP_SPOT_BTC_USD')
        interval = interval or self.config.get('default_interval', '1h')
        
        try:
            # Fetch market data
            self.logger.info(f"Fetching market data for {symbol} at {interval} interval")
            
            # Get candle limit from config or use default
            limit = self.config.get('agents', {}).get('technical', {}).get('backtest', {}).get('periods', 100)
            
            # Fetch OHLCV data using the data provider factory if available
            if hasattr(self.data_fetcher, 'get_ohlcv'):
                # Use the new DataProviderFactory interface
                ohlcv_data = self.data_fetcher.get_ohlcv(symbol, interval, limit)
                self.logger.info(f"Using DataProviderFactory to fetch OHLCV data for {symbol}")
            else:
                # Fall back to legacy CoinAPIFetcher interface
                ohlcv_data = self.data_fetcher.fetch_ohlcv(symbol, interval, limit)
                self.logger.info(f"Using legacy data fetcher interface for {symbol}")
            
            # Convert to pandas DataFrame for technical analysis
            df = self._convert_to_dataframe(ohlcv_data)
            
            if df.empty:
                return self.build_error_response(
                    "NoDataAvailable", 
                    f"No market data available for {symbol} at {interval} interval"
                )
            
            # Calculate technical indicators
            self.logger.debug("Calculating technical indicators")
            indicators = self._calculate_indicators(df)
            
            # Generate signals from indicators
            self.logger.debug("Generating indicator signals")
            indicator_signals = self._generate_indicator_signals(indicators)
            
            # Calculate overall signal and confidence
            self.logger.debug("Calculating overall signal")
            signal, confidence, normalized_scores = self._calculate_overall_signal(indicator_signals)
            
            # Prepare the result
            result = {
                'symbol': symbol,
                'interval': interval,
                'timestamp': datetime.now().isoformat(),
                'signal': signal,
                'confidence': confidence,
                'indicators': indicators,
                'indicator_signals': indicator_signals,
                'normalized_scores': normalized_scores,
                'success': True
            }
            
            # Optionally include market data
            if kwargs.get('include_market_data', False):
                result['market_data'] = ohlcv_data
            
            self.logger.info(f"Analysis complete: Signal {signal} with {confidence}% confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during technical analysis: {str(e)}", exc_info=True)
            return self.handle_data_fetching_error(e)

    def _convert_to_dataframe(self, ohlcv_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert OHLCV data to pandas DataFrame.
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            DataFrame containing OHLCV data
        """
        if not ohlcv_data:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(ohlcv_data)
        
        # Rename columns to standard names if needed
        column_mapping = {
            'time_period_start': 'datetime',
            'price_open': 'open',
            'price_high': 'high',
            'price_low': 'low',
            'price_close': 'close',
            'volume_traded': 'volume'
        }
        
        # Rename only the columns that exist
        existing_columns = set(df.columns).intersection(set(column_mapping.keys()))
        rename_dict = {k: column_mapping[k] for k in existing_columns}
        df = df.rename(columns=rename_dict)
        
        # Ensure all required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            self.logger.warning(f"Missing required columns in OHLCV data: {missing_columns}")
            # Fill missing columns with NaN
            for col in missing_columns:
                df[col] = np.nan
        
        # Convert datetime to pandas datetime
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
        
        # Sort by index (datetime) in descending order (most recent first)
        df.sort_index(ascending=False, inplace=True)
        
        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators from OHLCV data.
        
        Args:
            df: DataFrame containing OHLCV data
            
        Returns:
            Dictionary of calculated indicators
        """
        indicators = {}
        
        # Get a copy of the dataframe with ascending order for TA calculations
        df_asc = df.sort_index(ascending=True).copy()
        
        # ====== Moving Averages ======
        if self.indicator_config.get('moving_averages', {}).get('enabled', True):
            ma_config = self.indicator_config.get('moving_averages', {})
            indicators['moving_averages'] = {}
            
            # EMA calculations
            ema_periods = ma_config.get('ema_periods', [9, 21, 50, 200])
            for period in ema_periods:
                ema = EMAIndicator(close=df_asc['close'], window=period)
                df_asc[f'ema_{period}'] = ema.ema_indicator()
            
            # Store the latest EMA values
            for period in ema_periods:
                indicators['moving_averages'][f'ema_{period}'] = df_asc[f'ema_{period}'].iloc[-1]
            
            # SMA calculations
            sma_periods = ma_config.get('sma_periods', [50, 200])
            for period in sma_periods:
                sma = SMAIndicator(close=df_asc['close'], window=period)
                df_asc[f'sma_{period}'] = sma.sma_indicator()
            
            # Store the latest SMA values
            for period in sma_periods:
                indicators['moving_averages'][f'sma_{period}'] = df_asc[f'sma_{period}'].iloc[-1]
            
            # Calculate EMA crossovers
            indicators['moving_averages']['crossovers'] = {}
            if len(ema_periods) >= 2:
                # Sort periods to ensure we're comparing short vs long periods
                ema_periods.sort()
                
                for i in range(len(ema_periods) - 1):
                    short_period = ema_periods[i]
                    for j in range(i + 1, len(ema_periods)):
                        long_period = ema_periods[j]
                        
                        # Current relationship
                        current_diff = df_asc[f'ema_{short_period}'].iloc[-1] - df_asc[f'ema_{long_period}'].iloc[-1]
                        
                        # Previous relationship (to detect crossover)
                        prev_diff = df_asc[f'ema_{short_period}'].iloc[-2] - df_asc[f'ema_{long_period}'].iloc[-2]
                        
                        crossover_key = f'ema_{short_period}_ema_{long_period}'
                        if prev_diff < 0 and current_diff > 0:
                            # Bullish crossover (short crosses above long)
                            indicators['moving_averages']['crossovers'][crossover_key] = 'bullish'
                        elif prev_diff > 0 and current_diff < 0:
                            # Bearish crossover (short crosses below long)
                            indicators['moving_averages']['crossovers'][crossover_key] = 'bearish'
                        else:
                            # No crossover
                            indicators['moving_averages']['crossovers'][crossover_key] = 'none'
        
        # ====== Oscillators ======
        if self.indicator_config.get('oscillators', {}).get('enabled', True):
            osc_config = self.indicator_config.get('oscillators', {})
            indicators['oscillators'] = {}
            
            # RSI calculation
            rsi_period = osc_config.get('rsi_period', 14)
            rsi = RSIIndicator(close=df_asc['close'], window=rsi_period)
            df_asc['rsi'] = rsi.rsi()
            indicators['oscillators']['rsi'] = df_asc['rsi'].iloc[-1]
            indicators['oscillators']['rsi_prev'] = df_asc['rsi'].iloc[-2]
            
            # RSI thresholds
            indicators['oscillators']['rsi_overbought'] = osc_config.get('rsi_overbought', 70)
            indicators['oscillators']['rsi_oversold'] = osc_config.get('rsi_oversold', 30)
            
            # MACD calculation
            macd_fast = osc_config.get('macd_fast', 12)
            macd_slow = osc_config.get('macd_slow', 26)
            macd_signal = osc_config.get('macd_signal', 9)
            
            macd_ind = MACD(
                close=df_asc['close'], 
                window_fast=macd_fast, 
                window_slow=macd_slow, 
                window_sign=macd_signal
            )
            
            df_asc['macd_line'] = macd_ind.macd()
            df_asc['macd_signal'] = macd_ind.macd_signal()
            df_asc['macd_histogram'] = macd_ind.macd_diff()
            
            indicators['oscillators']['macd_line'] = df_asc['macd_line'].iloc[-1]
            indicators['oscillators']['macd_signal'] = df_asc['macd_signal'].iloc[-1]
            indicators['oscillators']['macd_histogram'] = df_asc['macd_histogram'].iloc[-1]
            indicators['oscillators']['macd_histogram_prev'] = df_asc['macd_histogram'].iloc[-2]
        
        # ====== Volatility Indicators ======
        if self.indicator_config.get('volatility', {}).get('enabled', True):
            vol_config = self.indicator_config.get('volatility', {})
            indicators['volatility'] = {}
            
            # Bollinger Bands
            bb_period = vol_config.get('bollinger_period', 20)
            bb_std = vol_config.get('bollinger_std', 2)
            
            bollinger = BollingerBands(
                close=df_asc['close'], 
                window=bb_period, 
                window_dev=bb_std
            )
            
            df_asc['bb_upper'] = bollinger.bollinger_hband()
            df_asc['bb_middle'] = bollinger.bollinger_mavg()
            df_asc['bb_lower'] = bollinger.bollinger_lband()
            df_asc['bb_width'] = ((df_asc['bb_upper'] - df_asc['bb_lower']) / df_asc['bb_middle'])
            
            indicators['volatility']['bb_upper'] = df_asc['bb_upper'].iloc[-1]
            indicators['volatility']['bb_middle'] = df_asc['bb_middle'].iloc[-1]
            indicators['volatility']['bb_lower'] = df_asc['bb_lower'].iloc[-1]
            indicators['volatility']['bb_width'] = df_asc['bb_width'].iloc[-1]
            indicators['volatility']['bb_width_prev'] = df_asc['bb_width'].iloc[-2]
            
            # Calculate %B - position within Bollinger Bands (0 to 1)
            df_asc['bb_pct_b'] = (df_asc['close'] - df_asc['bb_lower']) / (df_asc['bb_upper'] - df_asc['bb_lower'])
            indicators['volatility']['bb_pct_b'] = df_asc['bb_pct_b'].iloc[-1]
            
            # ATR for volatility measurement
            atr_period = vol_config.get('atr_period', 14)
            atr = AverageTrueRange(
                high=df_asc['high'], 
                low=df_asc['low'], 
                close=df_asc['close'], 
                window=atr_period
            )
            
            df_asc['atr'] = atr.average_true_range()
            df_asc['atr_pct'] = (df_asc['atr'] / df_asc['close']) * 100  # ATR as percentage of price
            
            indicators['volatility']['atr'] = df_asc['atr'].iloc[-1]
            indicators['volatility']['atr_pct'] = df_asc['atr_pct'].iloc[-1]
        
        # ====== Volume Indicators ======
        if self.indicator_config.get('volume', {}).get('enabled', True):
            vol_config = self.indicator_config.get('volume', {})
            indicators['volume'] = {}
            
            # Current volume vs previous volumes
            volume_series = df_asc['volume'].iloc[-10:]  # Last 10 periods
            avg_volume = volume_series.mean()
            
            indicators['volume']['current'] = df_asc['volume'].iloc[-1]
            indicators['volume']['average_10'] = avg_volume
            indicators['volume']['volume_change'] = (df_asc['volume'].iloc[-1] / avg_volume) - 1  # as ratio change
            
            # On-Balance Volume
            if vol_config.get('obv_enabled', True):
                obv = OnBalanceVolumeIndicator(close=df_asc['close'], volume=df_asc['volume'])
                df_asc['obv'] = obv.on_balance_volume()
                
                # Calculate OBV momentum (10-period change)
                if len(df_asc) >= 10:
                    obv_momentum = (df_asc['obv'].iloc[-1] - df_asc['obv'].iloc[-10]) / abs(df_asc['obv'].iloc[-10])
                    indicators['volume']['obv_momentum'] = obv_momentum
                
                indicators['volume']['obv'] = df_asc['obv'].iloc[-1]
                indicators['volume']['obv_prev'] = df_asc['obv'].iloc[-2]
            
            # Volume Weighted Average Price
            if vol_config.get('vwap_enabled', True) and 'open' in df_asc.columns:
                try:
                    # Need high, low, close, and volume for VWAP
                    vwap = VolumeWeightedAveragePrice(
                        high=df_asc['high'],
                        low=df_asc['low'],
                        close=df_asc['close'],
                        volume=df_asc['volume']
                    )
                    df_asc['vwap'] = vwap.volume_weighted_average_price()
                    indicators['volume']['vwap'] = df_asc['vwap'].iloc[-1]
                except Exception as e:
                    self.logger.warning(f"Error calculating VWAP: {str(e)}")
        
        # ====== Trend Indicators ======
        if self.indicator_config.get('trend', {}).get('enabled', True):
            trend_config = self.indicator_config.get('trend', {})
            indicators['trend'] = {}
            
            # ADX (Average Directional Index) for trend strength
            adx_period = trend_config.get('adx_period', 14)
            adx = ADXIndicator(
                high=df_asc['high'], 
                low=df_asc['low'], 
                close=df_asc['close'], 
                window=adx_period
            )
            
            df_asc['adx'] = adx.adx()
            df_asc['adx_pos'] = adx.adx_pos()  # Positive directional indicator
            df_asc['adx_neg'] = adx.adx_neg()  # Negative directional indicator
            
            indicators['trend']['adx'] = df_asc['adx'].iloc[-1]
            indicators['trend']['adx_threshold'] = trend_config.get('adx_threshold', 25)
            indicators['trend']['adx_pos'] = df_asc['adx_pos'].iloc[-1]
            indicators['trend']['adx_neg'] = df_asc['adx_neg'].iloc[-1]
            
            # Determine trend direction
            if indicators['trend']['adx_pos'] > indicators['trend']['adx_neg']:
                indicators['trend']['direction'] = 'bullish'
            else:
                indicators['trend']['direction'] = 'bearish'
            
            # Determine trend strength
            if indicators['trend']['adx'] > indicators['trend']['adx_threshold']:
                indicators['trend']['strength'] = 'strong'
            else:
                indicators['trend']['strength'] = 'weak'
            
            # Price vs moving averages for trend confirmation
            if 'moving_averages' in indicators:
                ma_values = []
                
                # Check EMAs
                for period in [50, 200]:  # Common trend EMAs
                    key = f'ema_{period}'
                    if key in indicators['moving_averages']:
                        ma_values.append((key, indicators['moving_averages'][key]))
                
                # Check SMAs if EMAs not available
                if not ma_values:
                    for period in [50, 200]:
                        key = f'sma_{period}'
                        if key in indicators['moving_averages']:
                            ma_values.append((key, indicators['moving_averages'][key]))
                
                # Determine price position relative to moving averages
                if ma_values:
                    current_price = df_asc['close'].iloc[-1]
                    above_count = sum(1 for _, value in ma_values if current_price > value)
                    below_count = sum(1 for _, value in ma_values if current_price < value)
                    
                    indicators['trend']['price_vs_ma'] = {
                        'above_count': above_count,
                        'below_count': below_count,
                        'total_count': len(ma_values)
                    }
        
        return indicators

    def _generate_indicator_signals(self, indicators: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Generate trading signals from calculated indicators.
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            Dictionary of signals for each indicator
        """
        signals = {}
        
        # ====== Moving Averages Signal ======
        if 'moving_averages' in indicators:
            ma_indicators = indicators['moving_averages']
            ma_signal = {'signal': 'NEUTRAL', 'strength': 0, 'reasons': []}
            
            # Check for EMA crossovers
            if 'crossovers' in ma_indicators:
                bullish_crossovers = 0
                bearish_crossovers = 0
                
                for crossover, direction in ma_indicators['crossovers'].items():
                    if direction == 'bullish':
                        bullish_crossovers += 1
                        ma_signal['reasons'].append(f"Bullish {crossover} crossover")
                    elif direction == 'bearish':
                        bearish_crossovers += 1
                        ma_signal['reasons'].append(f"Bearish {crossover} crossover")
                
                # Stronger signal for multiple crossovers
                if bullish_crossovers > bearish_crossovers:
                    ma_signal['signal'] = 'BUY'
                    ma_signal['strength'] = min(50 + (bullish_crossovers * 10), 90)
                elif bearish_crossovers > bullish_crossovers:
                    ma_signal['signal'] = 'SELL'
                    ma_signal['strength'] = min(50 + (bearish_crossovers * 10), 90)
            
            # Check price relative to EMAs/SMAs if no crossover signal
            if ma_signal['signal'] == 'NEUTRAL':
                # Find short and long EMAs
                short_ema = None
                long_ema = None
                
                for key in ma_indicators:
                    if key.startswith('ema_'):
                        period = int(key.split('_')[1])
                        if period <= 50 and (short_ema is None or period < int(short_ema.split('_')[1])):
                            short_ema = key
                        elif period > 50 and (long_ema is None or period > int(long_ema.split('_')[1])):
                            long_ema = key
                
                # Compare short and long EMAs
                if short_ema and long_ema:
                    short_value = ma_indicators[short_ema]
                    long_value = ma_indicators[long_ema]
                    
                    if short_value > long_value:
                        ma_signal['signal'] = 'BUY'
                        ma_signal['strength'] = 60
                        ma_signal['reasons'].append(f"{short_ema} above {long_ema}")
                    else:
                        ma_signal['signal'] = 'SELL'
                        ma_signal['strength'] = 60
                        ma_signal['reasons'].append(f"{short_ema} below {long_ema}")
            
            signals['moving_averages'] = ma_signal
        
        # ====== Oscillators Signal ======
        if 'oscillators' in indicators:
            osc_indicators = indicators['oscillators']
            osc_signal = {'signal': 'NEUTRAL', 'strength': 0, 'reasons': []}
            
            # RSI signals
            if 'rsi' in osc_indicators:
                rsi = osc_indicators['rsi']
                rsi_prev = osc_indicators.get('rsi_prev', rsi)
                overbought = osc_indicators.get('rsi_overbought', 70)
                oversold = osc_indicators.get('rsi_oversold', 30)
                
                if rsi < oversold:
                    osc_signal['signal'] = 'BUY'
                    osc_signal['strength'] = 70
                    osc_signal['reasons'].append(f"RSI oversold ({rsi:.2f})")
                elif rsi > overbought:
                    osc_signal['signal'] = 'SELL'
                    osc_signal['strength'] = 70
                    osc_signal['reasons'].append(f"RSI overbought ({rsi:.2f})")
                elif rsi_prev < oversold and rsi > oversold:
                    osc_signal['signal'] = 'BUY'
                    osc_signal['strength'] = 60
                    osc_signal['reasons'].append(f"RSI exiting oversold ({rsi:.2f})")
                elif rsi_prev > overbought and rsi < overbought:
                    osc_signal['signal'] = 'SELL'
                    osc_signal['strength'] = 60
                    osc_signal['reasons'].append(f"RSI exiting overbought ({rsi:.2f})")
                else:
                    # RSI in the middle (30-70)
                    if rsi > 50 and rsi < 70:
                        osc_signal['signal'] = 'BUY'
                        osc_signal['strength'] = 40 + ((rsi - 50) * 2)  # 40-80
                        osc_signal['reasons'].append(f"RSI bullish ({rsi:.2f})")
                    elif rsi < 50 and rsi > 30:
                        osc_signal['signal'] = 'SELL'
                        osc_signal['strength'] = 40 + ((50 - rsi) * 2)  # 40-80
                        osc_signal['reasons'].append(f"RSI bearish ({rsi:.2f})")
            
            # MACD signals
            if all(k in osc_indicators for k in ['macd_line', 'macd_signal', 'macd_histogram']):
                macd_line = osc_indicators['macd_line']
                macd_signal_line = osc_indicators['macd_signal']
                macd_histogram = osc_indicators['macd_histogram']
                macd_histogram_prev = osc_indicators.get('macd_histogram_prev', 0)
                
                # MACD line crosses above signal line (bullish)
                if macd_line > macd_signal_line and macd_histogram > 0 and macd_histogram_prev <= 0:
                    new_signal = 'BUY'
                    new_strength = 75
                    reason = "MACD bullish crossover"
                # MACD line crosses below signal line (bearish)
                elif macd_line < macd_signal_line and macd_histogram < 0 and macd_histogram_prev >= 0:
                    new_signal = 'SELL'
                    new_strength = 75
                    reason = "MACD bearish crossover"
                # MACD positive and increasing (bullish)
                elif macd_histogram > 0 and macd_histogram > macd_histogram_prev:
                    new_signal = 'BUY'
                    new_strength = 60
                    reason = "MACD histogram increasing (bullish)"
                # MACD negative and decreasing (bearish)
                elif macd_histogram < 0 and macd_histogram < macd_histogram_prev:
                    new_signal = 'SELL'
                    new_strength = 60
                    reason = "MACD histogram decreasing (bearish)"
                else:
                    new_signal = 'NEUTRAL'
                    new_strength = 0
                    reason = None
                
                # Only update if MACD signal is stronger than current osc_signal or osc_signal is neutral
                if new_signal != 'NEUTRAL' and (osc_signal['signal'] == 'NEUTRAL' or new_strength > osc_signal['strength']):
                    osc_signal['signal'] = new_signal
                    osc_signal['strength'] = new_strength
                    if reason:
                        osc_signal['reasons'].append(reason)
            
            signals['oscillators'] = osc_signal
        
        # ====== Volatility Indicators Signal ======
        if 'volatility' in indicators:
            vol_indicators = indicators['volatility']
            vol_signal = {'signal': 'NEUTRAL', 'strength': 0, 'reasons': []}
            
            # Bollinger Bands signals
            if all(k in vol_indicators for k in ['bb_upper', 'bb_middle', 'bb_lower', 'bb_pct_b']):
                bb_upper = vol_indicators['bb_upper']
                bb_middle = vol_indicators['bb_middle']
                bb_lower = vol_indicators['bb_lower']
                bb_pct_b = vol_indicators['bb_pct_b']
                
                # Current price relative to Bollinger Bands (using %B)
                if bb_pct_b < 0.05:  # Price at or below lower band (oversold)
                    vol_signal['signal'] = 'BUY'
                    vol_signal['strength'] = 70
                    vol_signal['reasons'].append(f"Price at lower Bollinger Band (oversold)")
                elif bb_pct_b > 0.95:  # Price at or above upper band (overbought)
                    vol_signal['signal'] = 'SELL'
                    vol_signal['strength'] = 70
                    vol_signal['reasons'].append(f"Price at upper Bollinger Band (overbought)")
                elif bb_pct_b < 0.2:  # Price near lower band (potential buy)
                    vol_signal['signal'] = 'BUY'
                    vol_signal['strength'] = 60
                    vol_signal['reasons'].append(f"Price near lower Bollinger Band")
                elif bb_pct_b > 0.8:  # Price near upper band (potential sell)
                    vol_signal['signal'] = 'SELL'
                    vol_signal['strength'] = 60
                    vol_signal['reasons'].append(f"Price near upper Bollinger Band")
                elif bb_pct_b < 0.45:  # Price below middle band (slightly bearish)
                    vol_signal['signal'] = 'SELL'
                    vol_signal['strength'] = 40
                    vol_signal['reasons'].append(f"Price below Bollinger middle band")
                elif bb_pct_b > 0.55:  # Price above middle band (slightly bullish)
                    vol_signal['signal'] = 'BUY'
                    vol_signal['strength'] = 40
                    vol_signal['reasons'].append(f"Price above Bollinger middle band")
            
            # Bollinger Band width (volatility expansion/contraction)
            if 'bb_width' in vol_indicators and 'bb_width_prev' in vol_indicators:
                bb_width = vol_indicators['bb_width']
                bb_width_prev = vol_indicators['bb_width_prev']
                
                # Increasing volatility
                if bb_width > bb_width_prev * 1.05:  # 5% increase
                    # Don't change signal direction, but increase strength if expanding
                    if vol_signal['signal'] != 'NEUTRAL':
                        vol_signal['strength'] = min(vol_signal['strength'] + 10, 90)
                        vol_signal['reasons'].append(f"Increasing volatility (BB width expanding)")
            
            signals['volatility'] = vol_signal
        
        # ====== Volume Indicators Signal ======
        if 'volume' in indicators:
            vol_indicators = indicators['volume']
            vol_signal = {'signal': 'NEUTRAL', 'strength': 0, 'reasons': []}
            
            # Volume change signal
            if 'volume_change' in vol_indicators:
                volume_change = vol_indicators['volume_change']
                
                if volume_change > 0.5:  # 50% above average volume
                    # Significant volume increase, but need price direction to determine signal
                    vol_signal['strength'] = 60
                    vol_signal['reasons'].append(f"Volume surge ({volume_change*100:.1f}% above average)")
                    # Direction will be determined by other indicators
                
            # OBV momentum
            if 'obv_momentum' in vol_indicators:
                obv_momentum = vol_indicators['obv_momentum']
                
                if obv_momentum > 0.05:  # Positive momentum
                    vol_signal['signal'] = 'BUY'
                    vol_signal['strength'] = 50 + min(obv_momentum * 100, 40)  # 50-90
                    vol_signal['reasons'].append(f"Positive OBV momentum ({obv_momentum:.2f})")
                elif obv_momentum < -0.05:  # Negative momentum
                    vol_signal['signal'] = 'SELL'
                    vol_signal['strength'] = 50 + min(abs(obv_momentum) * 100, 40)  # 50-90
                    vol_signal['reasons'].append(f"Negative OBV momentum ({obv_momentum:.2f})")
            
            signals['volume'] = vol_signal
        
        # ====== Trend Indicators Signal ======
        if 'trend' in indicators:
            trend_indicators = indicators['trend']
            trend_signal = {'signal': 'NEUTRAL', 'strength': 0, 'reasons': []}
            
            # ADX and trend direction
            if all(k in trend_indicators for k in ['adx', 'direction', 'strength']):
                adx = trend_indicators['adx']
                direction = trend_indicators['direction']
                strength = trend_indicators['strength']
                
                if direction == 'bullish' and strength == 'strong':
                    trend_signal['signal'] = 'BUY'
                    trend_signal['strength'] = 70
                    trend_signal['reasons'].append(f"Strong bullish trend (ADX: {adx:.1f})")
                elif direction == 'bearish' and strength == 'strong':
                    trend_signal['signal'] = 'SELL'
                    trend_signal['strength'] = 70
                    trend_signal['reasons'].append(f"Strong bearish trend (ADX: {adx:.1f})")
                elif direction == 'bullish':
                    trend_signal['signal'] = 'BUY'
                    trend_signal['strength'] = 50
                    trend_signal['reasons'].append(f"Weak bullish trend (ADX: {adx:.1f})")
                elif direction == 'bearish':
                    trend_signal['signal'] = 'SELL'
                    trend_signal['strength'] = 50
                    trend_signal['reasons'].append(f"Weak bearish trend (ADX: {adx:.1f})")
            
            # Price position relative to moving averages
            if 'price_vs_ma' in trend_indicators:
                price_vs_ma = trend_indicators['price_vs_ma']
                above_ratio = price_vs_ma['above_count'] / price_vs_ma['total_count']
                
                if above_ratio == 1.0:  # Price above all MAs
                    new_signal = 'BUY'
                    new_strength = 80
                    reason = "Price above all moving averages"
                elif above_ratio == 0.0:  # Price below all MAs
                    new_signal = 'SELL'
                    new_strength = 80
                    reason = "Price below all moving averages"
                elif above_ratio > 0.5:  # Price above majority of MAs
                    new_signal = 'BUY'
                    new_strength = 60
                    reason = f"Price above {price_vs_ma['above_count']}/{price_vs_ma['total_count']} moving averages"
                elif above_ratio < 0.5:  # Price below majority of MAs
                    new_signal = 'SELL'
                    new_strength = 60
                    reason = f"Price below {price_vs_ma['below_count']}/{price_vs_ma['total_count']} moving averages"
                else:
                    new_signal = 'NEUTRAL'
                    new_strength = 0
                    reason = None
                
                # Only update if new signal is stronger or current signal is neutral
                if new_signal != 'NEUTRAL' and (trend_signal['signal'] == 'NEUTRAL' or new_strength > trend_signal['strength']):
                    trend_signal['signal'] = new_signal
                    trend_signal['strength'] = new_strength
                    if reason:
                        trend_signal['reasons'].append(reason)
            
            signals['trend'] = trend_signal
        
        return signals

    def _calculate_overall_signal(self, indicator_signals: Dict[str, Dict[str, Any]]) -> Tuple[str, int, Dict[str, float]]:
        """
        Calculate overall trading signal and confidence from individual indicator signals.
        
        Args:
            indicator_signals: Dictionary of signals for each indicator
            
        Returns:
            Tuple of (signal, confidence, normalized_scores)
        """
        # Define weights for each indicator category
        category_weights = {
            'moving_averages': self.indicator_config.get('moving_averages', {}).get('weight', 0.35),
            'oscillators': self.indicator_config.get('oscillators', {}).get('weight', 0.25),
            'volatility': self.indicator_config.get('volatility', {}).get('weight', 0.20),
            'volume': self.indicator_config.get('volume', {}).get('weight', 0.10),
            'trend': self.indicator_config.get('trend', {}).get('weight', 0.10)
        }
        
        # Normalize weights to sum to 1.0
        total_weight = sum(category_weights.values())
        if total_weight > 0:
            category_weights = {k: v / total_weight for k, v in category_weights.items()}
        
        # Calculate weighted scores for each signal type
        signal_scores = {'BUY': 0.0, 'NEUTRAL': 0.0, 'SELL': 0.0}
        signal_weights = {'BUY': 0.0, 'NEUTRAL': 0.0, 'SELL': 0.0}
        
        for category, signal_info in indicator_signals.items():
            weight = category_weights.get(category, 0.1)  # Default to 0.1 if category not in weights
            signal = signal_info.get('signal', 'NEUTRAL')
            strength = signal_info.get('strength', 0) / 100.0  # Convert to 0-1 scale
            
            signal_scores[signal] += weight * strength
            signal_weights[signal] += weight
        
        # Normalize scores by weights
        normalized_scores = {}
        for signal, score in signal_scores.items():
            if signal_weights[signal] > 0:
                normalized_scores[signal] = score / signal_weights[signal]
            else:
                normalized_scores[signal] = 0.0
        
        # Determine the overall signal based on the highest normalized score
        if normalized_scores['BUY'] > normalized_scores['SELL']:
            if normalized_scores['BUY'] > 0.7:
                overall_signal = 'STRONG_BUY'
            else:
                overall_signal = 'BUY'
        elif normalized_scores['SELL'] > normalized_scores['BUY']:
            if normalized_scores['SELL'] > 0.7:
                overall_signal = 'STRONG_SELL'
            else:
                overall_signal = 'SELL'
        else:
            overall_signal = 'HOLD'
        
        # Calculate confidence as a percentage (1-99)
        if overall_signal in ['BUY', 'STRONG_BUY']:
            confidence = max(1, min(99, int(normalized_scores['BUY'] * 100)))
        elif overall_signal in ['SELL', 'STRONG_SELL']:
            confidence = max(1, min(99, int(normalized_scores['SELL'] * 100)))
        else:
            # For HOLD, confidence represents certainty of the HOLD signal
            buy_sell_diff = abs(normalized_scores['BUY'] - normalized_scores['SELL'])
            confidence = max(1, min(99, int((1 - buy_sell_diff) * 100)))
        
        return overall_signal, confidence, normalized_scores