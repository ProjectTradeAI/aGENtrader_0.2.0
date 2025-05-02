"""
aGENtrader v2 Technical Indicators Module

This module provides a comprehensive collection of technical indicators for market analysis.
All functions are stateless, accepting price/volume data and returning computed indicators.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Tuple, Any

# Configure logging
logger = logging.getLogger('technical_indicators')

def calculate_sma(data: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA)
    
    Args:
        data: Price data series
        period: Period for SMA calculation
        
    Returns:
        Series containing SMA values
    """
    return data.rolling(window=period).mean()

def calculate_ema(data: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA)
    
    Args:
        data: Price data series
        period: Period for EMA calculation
        
    Returns:
        Series containing EMA values
    """
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        data: Price data series
        period: Period for RSI calculation
        
    Returns:
        Series containing RSI values
    """
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Avoid division by zero
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(
    data: pd.Series, 
    fast_period: int = 12, 
    slow_period: int = 26, 
    signal_period: int = 9
) -> Dict[str, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD)
    
    Args:
        data: Price data series
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period
        
    Returns:
        Dictionary containing MACD line, signal line, and histogram
    """
    fast_ema = calculate_ema(data, fast_period)
    slow_ema = calculate_ema(data, slow_period)
    
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_bollinger_bands(
    data: pd.Series, 
    period: int = 20, 
    std_dev: float = 2.0
) -> Dict[str, pd.Series]:
    """
    Calculate Bollinger Bands
    
    Args:
        data: Price data series
        period: Period for moving average
        std_dev: Number of standard deviations
        
    Returns:
        Dictionary containing middle band, upper band, lower band, %B, and bandwidth
    """
    middle_band = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    # Calculate %B (position within bands, 0-1)
    percent_b = (data - lower_band) / (upper_band - lower_band)
    
    # Calculate bandwidth (volatility indicator)
    bandwidth = (upper_band - lower_band) / middle_band * 100
    
    return {
        'middle': middle_band,
        'upper': upper_band,
        'lower': lower_band,
        'percent_b': percent_b,
        'bandwidth': bandwidth
    }

def calculate_stochastic_rsi(
    data: pd.Series, 
    rsi_period: int = 14, 
    stoch_period: int = 14, 
    k_period: int = 3, 
    d_period: int = 3
) -> Dict[str, pd.Series]:
    """
    Calculate Stochastic RSI
    
    Args:
        data: Price data series
        rsi_period: Period for RSI calculation
        stoch_period: Period for stochastic calculation
        k_period: K smoothing period
        d_period: D smoothing period
        
    Returns:
        Dictionary containing Stochastic RSI K%, D%, and raw values
    """
    # Calculate RSI
    rsi = calculate_rsi(data, rsi_period)
    
    # Calculate Stochastic RSI
    min_rsi = rsi.rolling(window=stoch_period).min()
    max_rsi = rsi.rolling(window=stoch_period).max()
    
    # Avoid division by zero
    stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi).replace(0, 1e-9)
    
    # Calculate K% and D%
    k = stoch_rsi.rolling(window=k_period).mean() * 100
    d = k.rolling(window=d_period).mean()
    
    return {
        'stoch_rsi': stoch_rsi * 100,  # Scale to 0-100
        'k': k,
        'd': d
    }

def calculate_adx(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    period: int = 14
) -> Dict[str, pd.Series]:
    """
    Calculate Average Directional Index (ADX)
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        period: Period for ADX calculation
        
    Returns:
        Dictionary containing ADX, +DI, and -DI values
    """
    # Step 1: Calculate True Range (TR)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Step 2: Calculate Directional Movement (+DM and -DM)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    pos_dm_series = pd.Series(pos_dm, index=close.index)
    neg_dm_series = pd.Series(neg_dm, index=close.index)
    
    # Step 3: Calculate Smoothed Averages of TR, +DM, and -DM
    smoothed_tr = calculate_ema(tr, period)
    smoothed_pos_dm = calculate_ema(pos_dm_series, period)
    smoothed_neg_dm = calculate_ema(neg_dm_series, period)
    
    # Step 4: Calculate +DI and -DI
    pos_di = (smoothed_pos_dm / smoothed_tr) * 100
    neg_di = (smoothed_neg_dm / smoothed_tr) * 100
    
    # Step 5: Calculate DX
    dx = abs(pos_di - neg_di) / (pos_di + neg_di) * 100
    
    # Step 6: Calculate ADX
    adx = calculate_ema(dx, period)
    
    return {
        'adx': adx,
        'pos_di': pos_di,
        'neg_di': neg_di
    }

def calculate_vwma(
    close: pd.Series, 
    volume: pd.Series, 
    period: int = 20
) -> pd.Series:
    """
    Calculate Volume-Weighted Moving Average (VWMA)
    
    Args:
        close: Close prices series
        volume: Volume series
        period: Period for VWMA calculation
        
    Returns:
        Series containing VWMA values
    """
    vwma = (close * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
    return vwma

def calculate_parabolic_sar(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series,
    af_start: float = 0.02, 
    af_step: float = 0.02, 
    af_max: float = 0.2
) -> Dict[str, pd.Series]:
    """
    Calculate Parabolic SAR
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        af_start: Starting acceleration factor
        af_step: Acceleration factor step
        af_max: Maximum acceleration factor
        
    Returns:
        Dictionary containing SAR values and trend direction
    """
    length = len(close)
    
    # Initialize SAR and EP arrays
    sar = np.zeros(length)
    trend = np.zeros(length)  # 1 for uptrend, -1 for downtrend
    ep = np.zeros(length)     # Extreme point
    af = np.zeros(length)     # Acceleration factor
    
    # Initialize with a basic trend assumption
    if length <= 1:
        return {
            'sar': pd.Series(sar, index=close.index),
            'trend': pd.Series(trend, index=close.index)
        }
    
    # Determine initial trend (1 = up, -1 = down)
    trend[0] = 1 if close.iloc[1] > close.iloc[0] else -1
    
    # Set initial extreme point
    ep[0] = high.iloc[0] if trend[0] == 1 else low.iloc[0]
    
    # Set initial SAR
    sar[0] = low.iloc[0] if trend[0] == 1 else high.iloc[0]
    
    # Set initial acceleration factor
    af[0] = af_start
    
    # Calculate SAR values
    for i in range(1, length):
        # Previous SAR
        sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
        
        # Adjust SAR to ensure it doesn't penetrate previous price bars
        if trend[i-1] == 1:  # Uptrend
            sar[i] = min(sar[i], low.iloc[i-1], low.iloc[max(0, i-2)])
        else:  # Downtrend
            sar[i] = max(sar[i], high.iloc[i-1], high.iloc[max(0, i-2)])
        
        # Determine if trend changes
        if (trend[i-1] == 1 and low.iloc[i] < sar[i]) or (trend[i-1] == -1 and high.iloc[i] > sar[i]):
            # Trend changes
            trend[i] = -trend[i-1]
            sar[i] = ep[i-1]
            ep[i] = high.iloc[i] if trend[i] == 1 else low.iloc[i]
            af[i] = af_start
        else:
            # Trend continues
            trend[i] = trend[i-1]
            
            # Update extreme point if needed
            if trend[i] == 1 and high.iloc[i] > ep[i-1]:
                ep[i] = high.iloc[i]
                af[i] = min(af[i-1] + af_step, af_max)
            elif trend[i] == -1 and low.iloc[i] < ep[i-1]:
                ep[i] = low.iloc[i]
                af[i] = min(af[i-1] + af_step, af_max)
            else:
                ep[i] = ep[i-1]
                af[i] = af[i-1]
    
    return {
        'sar': pd.Series(sar, index=close.index),
        'trend': pd.Series(trend, index=close.index)
    }

def calculate_donchian_channels(
    high: pd.Series, 
    low: pd.Series, 
    period: int = 20
) -> Dict[str, pd.Series]:
    """
    Calculate Donchian Channels
    
    Args:
        high: High prices series
        low: Low prices series
        period: Period for Donchian Channels calculation
        
    Returns:
        Dictionary containing upper, middle, and lower bands,
        and a breakout signal if price reaches upper or lower band
    """
    upper = high.rolling(window=period).max()
    lower = low.rolling(window=period).min()
    middle = (upper + lower) / 2
    
    # Create a simple breakout indicator
    # 1 = upper band breakout, -1 = lower band breakout, 0 = no breakout
    current_high = high.iloc[-1] if not high.empty else None
    current_low = low.iloc[-1] if not low.empty else None
    current_upper = upper.iloc[-1] if not upper.empty else None
    current_lower = lower.iloc[-1] if not lower.empty else None
    
    if current_high is not None and current_upper is not None and current_high >= current_upper:
        breakout = 1  # Upper breakout
    elif current_low is not None and current_lower is not None and current_low <= current_lower:
        breakout = -1  # Lower breakout
    else:
        breakout = 0  # No breakout
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'breakout': breakout
    }

def calculate_ichimoku_cloud(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series,
    tenkan_period: int = 9, 
    kijun_period: int = 26, 
    senkou_span_b_period: int = 52, 
    displacement: int = 26
) -> Dict[str, pd.Series]:
    """
    Calculate Ichimoku Cloud
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        tenkan_period: Tenkan-sen (Conversion Line) period
        kijun_period: Kijun-sen (Base Line) period
        senkou_span_b_period: Senkou Span B period
        displacement: Displacement period for Senkou Span
        
    Returns:
        Dictionary containing Ichimoku Cloud components
    """
    # Tenkan-sen (Conversion Line)
    tenkan_high = high.rolling(window=tenkan_period).max()
    tenkan_low = low.rolling(window=tenkan_period).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    
    # Kijun-sen (Base Line)
    kijun_high = high.rolling(window=kijun_period).max()
    kijun_low = low.rolling(window=kijun_period).min()
    kijun_sen = (kijun_high + kijun_low) / 2
    
    # Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    
    # Senkou Span B (Leading Span B)
    senkou_high = high.rolling(window=senkou_span_b_period).max()
    senkou_low = low.rolling(window=senkou_span_b_period).min()
    senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)
    
    # Chikou Span (Lagging Span)
    chikou_span = close.shift(-displacement)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }

def calculate_atr(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series, 
    period: int = 14
) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        period: Period for ATR calculation
        
    Returns:
        Series containing ATR values
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_all_indicators(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate all technical indicators in a single function
    
    Args:
        df: DataFrame with OHLCV data
        config: Configuration dictionary with indicator parameters
        
    Returns:
        Dictionary containing all calculated indicators
    """
    if df.empty:
        logger.warning("Empty dataframe provided to calculate_all_indicators")
        return {}
        
    # Default configuration
    default_config = {
        'sma_short': 20,
        'sma_long': 50,
        'ema_short': 12,
        'ema_long': 26,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bollinger_period': 20, 
        'bollinger_std': 2,
        'stoch_rsi_period': 14,
        'stoch_period': 14,
        'adx_period': 14,
        'vwma_period': 20,
        'donchian_period': 20,
        'atr_period': 14
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    config = default_config
    
    # Check required columns
    required_columns = ['close', 'high', 'low', 'volume']
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        logger.warning(f"Missing columns in dataframe: {missing_columns}")
        logger.warning(f"Available columns: {list(df.columns)}")
        for col in missing_columns:
            df[col] = 0  # Add placeholder columns
    
    # Get the most recent candle for point values
    current = df.iloc[-1] if len(df) > 0 else None
    
    # Calculate all indicators
    result = {}
    
    # Simple Moving Averages
    sma_short = calculate_sma(df['close'], config['sma_short'])
    sma_long = calculate_sma(df['close'], config['sma_long'])
    result['sma_short'] = sma_short.iloc[-1] if not sma_short.empty else None
    result['sma_long'] = sma_long.iloc[-1] if not sma_long.empty else None
    result['sma_trend'] = 'bullish' if result['sma_short'] > result['sma_long'] else 'bearish'
    
    # Exponential Moving Averages
    ema_short = calculate_ema(df['close'], config['ema_short'])
    ema_long = calculate_ema(df['close'], config['ema_long'])
    result['ema_short'] = ema_short.iloc[-1] if not ema_short.empty else None
    result['ema_long'] = ema_long.iloc[-1] if not ema_long.empty else None
    result['ema_trend'] = 'bullish' if result['ema_short'] > result['ema_long'] else 'bearish'
    
    # RSI
    rsi = calculate_rsi(df['close'], config['rsi_period'])
    result['rsi'] = rsi.iloc[-1] if not rsi.empty else None
    if result['rsi'] is not None:
        if result['rsi'] > 70:
            result['rsi_signal'] = 'overbought'
        elif result['rsi'] < 30:
            result['rsi_signal'] = 'oversold'
        else:
            result['rsi_signal'] = 'neutral'
    
    # MACD
    macd_data = calculate_macd(
        df['close'], 
        config['macd_fast'], 
        config['macd_slow'], 
        config['macd_signal']
    )
    result['macd'] = macd_data['macd'].iloc[-1] if not macd_data['macd'].empty else None
    result['macd_signal'] = macd_data['signal'].iloc[-1] if not macd_data['signal'].empty else None
    result['macd_histogram'] = macd_data['histogram'].iloc[-1] if not macd_data['histogram'].empty else None
    
    # MACD trend
    if result['macd'] is not None and result['macd_signal'] is not None:
        if result['macd'] > result['macd_signal']:
            result['macd_trend'] = 'bullish'
        else:
            result['macd_trend'] = 'bearish'
        
        # Check for crossover
        if len(df) > 1:
            prev_macd = macd_data['macd'].iloc[-2] if len(macd_data['macd']) > 1 else None
            prev_signal = macd_data['signal'].iloc[-2] if len(macd_data['signal']) > 1 else None
            
            if prev_macd is not None and prev_signal is not None:
                if prev_macd < prev_signal and result['macd'] > result['macd_signal']:
                    result['macd_crossover'] = 'bullish'
                elif prev_macd > prev_signal and result['macd'] < result['macd_signal']:
                    result['macd_crossover'] = 'bearish'
                else:
                    result['macd_crossover'] = 'none'
    
    # Bollinger Bands
    bb_data = calculate_bollinger_bands(
        df['close'], 
        config['bollinger_period'], 
        config['bollinger_std']
    )
    result['bb_upper'] = bb_data['upper'].iloc[-1] if not bb_data['upper'].empty else None
    result['bb_middle'] = bb_data['middle'].iloc[-1] if not bb_data['middle'].empty else None
    result['bb_lower'] = bb_data['lower'].iloc[-1] if not bb_data['lower'].empty else None
    result['bb_percent_b'] = bb_data['percent_b'].iloc[-1] if not bb_data['percent_b'].empty else None
    result['bb_bandwidth'] = bb_data['bandwidth'].iloc[-1] if not bb_data['bandwidth'].empty else None
    
    # BB signals
    if result['bb_percent_b'] is not None:
        if result['bb_percent_b'] > 1:
            result['bb_signal'] = 'overbought'
        elif result['bb_percent_b'] < 0:
            result['bb_signal'] = 'oversold'
        elif result['bb_percent_b'] > 0.8:
            result['bb_signal'] = 'high'
        elif result['bb_percent_b'] < 0.2:
            result['bb_signal'] = 'low'
        else:
            result['bb_signal'] = 'middle'
    
    # Stochastic RSI
    stoch_data = calculate_stochastic_rsi(
        df['close'], 
        config['stoch_rsi_period'], 
        config['stoch_period']
    )
    result['stoch_rsi'] = stoch_data['stoch_rsi'].iloc[-1] if not stoch_data['stoch_rsi'].empty else None
    result['stoch_k'] = stoch_data['k'].iloc[-1] if not stoch_data['k'].empty else None
    result['stoch_d'] = stoch_data['d'].iloc[-1] if not stoch_data['d'].empty else None
    
    # Stochastic RSI signal
    if result['stoch_rsi'] is not None:
        if result['stoch_rsi'] > 80:
            result['stoch_rsi_signal'] = 'overbought'
        elif result['stoch_rsi'] < 20:
            result['stoch_rsi_signal'] = 'oversold'
        else:
            result['stoch_rsi_signal'] = 'neutral'
    
    # ADX
    adx_data = calculate_adx(df['high'], df['low'], df['close'], config['adx_period'])
    result['adx'] = adx_data['adx'].iloc[-1] if not adx_data['adx'].empty else None
    result['adx_pos_di'] = adx_data['pos_di'].iloc[-1] if not adx_data['pos_di'].empty else None
    result['adx_neg_di'] = adx_data['neg_di'].iloc[-1] if not adx_data['neg_di'].empty else None
    
    # ADX trend strength and direction
    if result['adx'] is not None:
        if result['adx'] < 20:
            result['adx_strength'] = 'weak'
        elif result['adx'] < 40:
            result['adx_strength'] = 'moderate'
        elif result['adx'] < 60:
            result['adx_strength'] = 'strong'
        else:
            result['adx_strength'] = 'very_strong'
            
        if result['adx_pos_di'] > result['adx_neg_di']:
            result['adx_trend'] = 'bullish'
        else:
            result['adx_trend'] = 'bearish'
    
    # VWMA
    vwma = calculate_vwma(df['close'], df['volume'], config['vwma_period'])
    result['vwma'] = vwma.iloc[-1] if not vwma.empty else None
    
    # VWMA trend
    if result['vwma'] is not None and current is not None:
        if current['close'] > result['vwma']:
            result['vwma_trend'] = 'bullish'
        else:
            result['vwma_trend'] = 'bearish'
    
    # Parabolic SAR
    sar_data = calculate_parabolic_sar(df['high'], df['low'], df['close'])
    result['sar'] = sar_data['sar'].iloc[-1] if not sar_data['sar'].empty else None
    
    # SAR trend
    if result['sar'] is not None and current is not None:
        if current['close'] > result['sar']:
            result['sar_trend'] = 'bullish'
        else:
            result['sar_trend'] = 'bearish'
    
    # Donchian Channels
    dc_data = calculate_donchian_channels(df['high'], df['low'], config['donchian_period'])
    result['donchian_upper'] = dc_data['upper'].iloc[-1] if not dc_data['upper'].empty else None
    result['donchian_middle'] = dc_data['middle'].iloc[-1] if not dc_data['middle'].empty else None
    result['donchian_lower'] = dc_data['lower'].iloc[-1] if not dc_data['lower'].empty else None
    result['donchian_breakout'] = dc_data['breakout']
    
    # Ichimoku Cloud (if enough data points)
    if len(df) > 52:  # Need at least senkou_span_b_period points
        ichimoku_data = calculate_ichimoku_cloud(df['high'], df['low'], df['close'])
        result['ichimoku_tenkan'] = ichimoku_data['tenkan_sen'].iloc[-1] if not ichimoku_data['tenkan_sen'].empty else None
        result['ichimoku_kijun'] = ichimoku_data['kijun_sen'].iloc[-1] if not ichimoku_data['kijun_sen'].empty else None
        result['ichimoku_senkou_a'] = ichimoku_data['senkou_span_a'].iloc[-1] if not ichimoku_data['senkou_span_a'].empty else None
        result['ichimoku_senkou_b'] = ichimoku_data['senkou_span_b'].iloc[-1] if not ichimoku_data['senkou_span_b'].empty else None
        
        # Ichimoku signals
        if all(x is not None for x in [result['ichimoku_tenkan'], result['ichimoku_kijun']]):
            if result['ichimoku_tenkan'] > result['ichimoku_kijun']:
                result['ichimoku_signal'] = 'bullish_tk_cross'
            elif result['ichimoku_tenkan'] < result['ichimoku_kijun']:
                result['ichimoku_signal'] = 'bearish_tk_cross'
            else:
                result['ichimoku_signal'] = 'neutral'
                
        if all(x is not None for x in [result['ichimoku_senkou_a'], result['ichimoku_senkou_b']]) and current is not None:
            if current['close'] > result['ichimoku_senkou_a'] and current['close'] > result['ichimoku_senkou_b']:
                result['ichimoku_cloud'] = 'above_cloud'
            elif current['close'] < result['ichimoku_senkou_a'] and current['close'] < result['ichimoku_senkou_b']:
                result['ichimoku_cloud'] = 'below_cloud'
            else:
                result['ichimoku_cloud'] = 'in_cloud'
    
    # ATR
    atr = calculate_atr(df['high'], df['low'], df['close'], config['atr_period'])
    result['atr'] = atr.iloc[-1] if not atr.empty else None
    
    # ATR as percentage of price
    if result['atr'] is not None and current is not None and current['close'] > 0:
        result['atr_percent'] = (result['atr'] / current['close']) * 100
    
    # Overall signals summary
    signals = {
        'bullish': 0,
        'bearish': 0,
        'neutral': 0
    }
    
    # Count signals from various indicators
    for key in result:
        if '_trend' in key and result[key] == 'bullish':
            signals['bullish'] += 1
        elif '_trend' in key and result[key] == 'bearish':
            signals['bearish'] += 1
        elif '_signal' in key:
            if result[key] == 'overbought':
                signals['bearish'] += 1
            elif result[key] == 'oversold':
                signals['bullish'] += 1
    
    # MACD crossover has higher weight
    if 'macd_crossover' in result:
        if result['macd_crossover'] == 'bullish':
            signals['bullish'] += 2
        elif result['macd_crossover'] == 'bearish':
            signals['bearish'] += 2
    
    # Donchian breakout has higher weight
    if result['donchian_breakout'] == 1:
        signals['bullish'] += 2
    elif result['donchian_breakout'] == -1:
        signals['bearish'] += 2
        
    # Add signal summary to results
    result['signal_summary'] = signals
    
    return result