"""
aGENtrader v2 Technical Analyst Agent

This module provides a technical analysis agent that evaluates price patterns,
indicators, and chart patterns to generate trading signals.
"""

import os
import time
import json
import logging
import math
# Try to import required packages, but continue with warnings if not available
try:
    import numpy as np
except ImportError:
    try:
        import sys
        import subprocess
        print("Attempting to install numpy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np
    except Exception as e:
        print(f"Warning: Could not import or install numpy: {str(e)}")
        print("Will use minimal functionality without numpy")
        # Define a minimal numpy substitute that supports the operations we need
        class NumpySubstitute:
            def sqrt(self, x):
                return x ** 0.5
        np = NumpySubstitute()

try:
    import pandas as pd
except ImportError:
    try:
        import sys
        import subprocess
        print("Attempting to install pandas...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
        import pandas as pd
    except Exception as e:
        print(f"Warning: Could not import or install pandas: {str(e)}")
        print("Cannot continue without pandas. Using basic implementation.")
        # Define a very basic DataFrame implementation for essential functionality
        class DataFrame:
            def __init__(self, data=None, columns=None):
                self.data = data or {}
                self.columns = columns or []
                self.empty = not bool(data)
                
            def iloc(self, idx):
                # Very simplified indexer that just returns values 
                return self.data.get(idx, {})
                
        pd = type('mock_pandas', (), {
            'DataFrame': DataFrame,
            'to_numeric': lambda x, errors='raise': x,
        })

# Import the centralized indicator module
from utils.indicators import calculate_all_indicators
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from agents.base_agent import BaseAnalystAgent
from core.logging import decision_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('technical_analyst')

class TechnicalAnalystAgent(BaseAnalystAgent):
    """
    Agent that analyzes market data using technical analysis.
    
    This agent evaluates price patterns, technical indicators, and chart patterns
    to determine market conditions and generate trading signals.
    """
    
    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the technical analyst agent.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            config: Configuration parameters
        """
        super().__init__(agent_name="technical_analyst")
        self.name = "TechnicalAnalystAgent"
        self.description = "Analyzes market data using technical analysis"
        self.data_fetcher = data_fetcher
        
        # Set up logger
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM client with agent-specific configuration
        from models.llm_client import LLMClient
        self.llm_client = LLMClient(agent_name="technical_analyst")
        
        # Get agent config
        self.agent_config = self.get_agent_config()
        self.trading_config = self.get_trading_config()
        
        # Use agent-specific timeframe from config if available
        technical_config = self.agent_config.get("technical_analyst", {})
        self.default_interval = technical_config.get("timeframe", self.trading_config.get("default_interval", "1h"))
        
        # Configure technical analysis parameters
        self.config = config or {}
        self.indicator_config = self.config.get('indicators', {
            'sma_short': 20,       # Short-term simple moving average period
            'sma_long': 50,        # Long-term simple moving average period
            'ema_short': 12,       # Short-term exponential moving average period
            'ema_long': 26,        # Long-term exponential moving average period
            'rsi_period': 14,      # Relative Strength Index period
            'macd_fast': 12,       # MACD fast period
            'macd_slow': 26,       # MACD slow period
            'macd_signal': 9,      # MACD signal period
            'bollinger_period': 20, # Bollinger Bands period
            'bollinger_std': 2,    # Bollinger Bands standard deviation
            'atr_period': 14,      # Average True Range period
            'support_resistance_lookback': 30 # Lookback period for support/resistance detection
        })
        
        # Set confidence thresholds
        self.high_confidence = 80   # For very clear signals
        self.medium_confidence = 65 # For moderate signals
        self.low_confidence = 50    # For weak signals
        
    def analyze(
        self, 
        symbol: Optional[str] = None, 
        market_data: Optional[Dict[str, Any]] = None,
        interval: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze market data using technical analysis.
        
        Args:
            symbol: Trading symbol
            market_data: Pre-fetched market data (optional)
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Technical analysis results
        """
        start_time = time.time()
        
        # Handle parameter flexibility with the new signature
        self.logger.info(f"TechnicalAnalystAgent analyze called with symbol type: {type(symbol)}, market_data type: {type(market_data)}")
        
        # Extract data provider from market_data if available
        data_provider = None
        if market_data and isinstance(market_data, dict):
            # Get data provider from market_data
            data_provider = market_data.get('data_provider')
            if data_provider:
                self.data_fetcher = data_provider
                self.logger.info(f"Using data_provider from market_data: {type(data_provider).__name__}")
                
            # Extract other parameters from market_data if not provided directly
            if not symbol and 'symbol' in market_data:
                symbol = market_data.get('symbol')
            if not interval and 'interval' in market_data:
                interval = market_data.get('interval')
            
            self.logger.info(f"Parameters from market_data: symbol={symbol}, interval={interval}, data_provider={'Available' if data_provider else 'None'}")
            
        # Use agent-specific timeframe if none provided
        interval = interval or self.default_interval
        
        # Validate input
        if not symbol:
            if market_data and 'symbol' in market_data:
                symbol = market_data['symbol']
            else:
                return self.build_error_response(
                    "MISSING_SYMBOL",
                    "Symbol not provided in parameters or market_data"
                )
                
        # Validate interval
        if not interval:
            if market_data and 'interval' in market_data:
                interval = market_data['interval']
            else:
                interval = self.default_interval
            
        try:
            # Check if we have pre-fetched market data or need to fetch it
            price_data = None
            if market_data and isinstance(market_data, dict) and market_data.get("ohlcv"):
                price_data = market_data.get("ohlcv")
                logger.info(f"Using pre-fetched price data")
            else:
                # Fetch market data using data fetcher
                if not self.data_fetcher:
                    logger.error(f"Data fetcher missing in {self.name}. Class: {self.__class__.__name__}, Module: {__name__}")
                    # Create a mock data provider as a fallback
                    try:
                        from agents.data_providers.mock_data_provider import MockDataProvider
                        logger.warning(f"Creating fallback MockDataProvider in {self.name}")
                        self.data_fetcher = MockDataProvider(symbol=symbol)
                        logger.info(f"Successfully created MockDataProvider fallback")
                    except Exception as e:
                        logger.error(f"Failed to create fallback MockDataProvider: {str(e)}")
                        return self.build_error_response(
                            "DATA_FETCHER_MISSING",
                            "Data fetcher not provided and fallback creation failed"
                        )
                else:
                    logger.info(f"Using data fetcher in {self.name}: {type(self.data_fetcher).__name__}")
                
                logger.info(f"Fetching price data for {symbol} at {interval} interval")
                try:
                    limit = kwargs.get('limit', 100)  # Default to 100 candles
                    # Handle different symbol formats
                    fetch_symbol = symbol
                    if '/' in fetch_symbol:
                        # Some providers (like MockDataProvider) might not handle '/' correctly
                        # Try with the symbol as is first, then fallback to modified format
                        try:
                            price_data = self.data_fetcher.fetch_ohlcv(fetch_symbol, interval, limit=limit)
                        except Exception as first_error:
                            logger.warning(f"Failed to fetch with '{fetch_symbol}', trying without '/'")
                            fetch_symbol = fetch_symbol.replace('/', '')
                            price_data = self.data_fetcher.fetch_ohlcv(fetch_symbol, interval, limit=limit)
                    else:
                        price_data = self.data_fetcher.fetch_ohlcv(fetch_symbol, interval, limit=limit)
                except Exception as e:
                    logger.error(f"Error fetching price data: {str(e)}")
                    return self.build_error_response(
                        "PRICE_DATA_FETCH_ERROR",
                        f"Error fetching price data: {str(e)}"
                    )
            
            if not price_data or not isinstance(price_data, list) or len(price_data) < 30:
                return self.build_error_response(
                    "INSUFFICIENT_PRICE_DATA",
                    f"Insufficient price data for analysis: {len(price_data) if price_data else 0} candles"
                )
                
            # Convert price data to DataFrame for easier analysis
            df = self._prepare_dataframe(price_data)
            
            # Calculate key technical indicators
            df = self._calculate_indicators(df)
            
            # Perform technical analysis
            analysis_result = self._analyze_indicators(df)
            
            # Get the current price from the most recent candle
            current_price = df['close'].iloc[-1] if not df.empty else None
            
            # Generate a trading signal based on the technical analysis
            signal, confidence, explanation = self._generate_signal(analysis_result, df)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            results = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "interval": interval,
                "current_price": current_price,
                "signal": signal,  # This field is used by DecisionAgent to determine action
                "confidence": confidence,  # This field is used by DecisionAgent for weighting
                "action": signal,  # Add explicit action field to match DecisionAgent expectations
                "explanation": [explanation],
                "indicators": analysis_result,
                "execution_time_seconds": execution_time,
                "status": "success"
            }
            
            # Log decision summary
            try:
                decision_logger.create_summary_from_result(
                    agent_name=self.name,
                    result=results,
                    symbol=symbol,
                    price=current_price
                )
            except Exception as e:
                logger.warning(f"Failed to log decision: {str(e)}")
            
            # Return results
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing technical indicators: {str(e)}", exc_info=True)
            return self.build_error_response(
                "TECHNICAL_ANALYSIS_ERROR",
                f"Error analyzing technical indicators: {str(e)}"
            )
    
    def _prepare_dataframe(self, price_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert OHLCV data to a pandas DataFrame.
        
        Args:
            price_data: List of OHLCV data points
            
        Returns:
            DataFrame with OHLCV data
        """
        # Check the format of price_data and convert accordingly
        if not price_data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
        # Handle different formats from different data providers
        if isinstance(price_data[0], dict):
            # Dictionary format (e.g., from Binance)
            df = pd.DataFrame(price_data)
            # Ensure required columns are present
            required_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
            missing_cols = required_cols - set(df.columns)
            
            # Try to infer columns if names are different
            if missing_cols and 'time' in df.columns and 'timestamp' in missing_cols:
                df = df.rename(columns={'time': 'timestamp'})
                missing_cols.remove('timestamp')
                
            if missing_cols:
                logger.warning(f"Missing columns in price data: {missing_cols}")
                for col in missing_cols:
                    df[col] = None
                    
        elif isinstance(price_data[0], list):
            # List format (e.g., [timestamp, open, high, low, close, volume])
            df = pd.DataFrame(price_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
        else:
            logger.error(f"Unsupported price data format: {type(price_data[0])}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Ensure numeric types for price and volume columns
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators on price data using the centralized indicators module.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicator columns
        """
        if df.empty:
            return df
            
        # Use the centralized calculate_all_indicators function to compute all indicators
        indicators_result = calculate_all_indicators(df, self.indicator_config)
        
        # Store indicators directly in the dataframe for backward compatibility
        # with existing code that might expect these columns
        
        # Simple Moving Averages
        sma_short = self.indicator_config['sma_short']
        sma_long = self.indicator_config['sma_long']
        df[f'sma_{sma_short}'] = df['close'].rolling(window=sma_short).mean()
        df[f'sma_{sma_long}'] = df['close'].rolling(window=sma_long).mean()
        
        # Exponential Moving Averages
        ema_short = self.indicator_config['ema_short']
        ema_long = self.indicator_config['ema_long']
        df[f'ema_{ema_short}'] = df['close'].ewm(span=ema_short, adjust=False).mean()
        df[f'ema_{ema_long}'] = df['close'].ewm(span=ema_long, adjust=False).mean()
        
        # MACD (already calculated in indicators_result, just store values)
        if 'macd' in indicators_result:
            df['macd'] = indicators_result['macd']
            df['macd_signal'] = indicators_result['macd_signal']
            df['macd_histogram'] = indicators_result['macd_histogram']
        
        # RSI
        if 'rsi' in indicators_result:
            df['rsi'] = indicators_result['rsi']
        
        # Bollinger Bands
        if all(k in indicators_result for k in ['bb_upper', 'bb_middle', 'bb_lower']):
            df['bb_middle'] = indicators_result['bb_middle']
            df['bb_upper'] = indicators_result['bb_upper']
            df['bb_lower'] = indicators_result['bb_lower']
            df['bb_percent_b'] = indicators_result['bb_percent_b']
            df['bb_bandwidth'] = indicators_result['bb_bandwidth']
        
        # ATR
        if 'atr' in indicators_result:
            df['atr'] = indicators_result['atr']
            
        # Store all indicator results in a dictionary that we'll attach to the DataFrame
        # Since we can't modify the DataFrame directly with new attributes, we'll use a separate variable
        # that will be accessed in the _analyze_indicators method
        self._cached_indicator_results = indicators_result
        
        return df
    
    def _analyze_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze technical indicators to extract insights.
        
        Args:
            df: DataFrame with price data and indicators
            
        Returns:
            Dictionary of technical analysis insights
        """
        if df.empty or len(df) < 2:
            return {
                "trend": "UNKNOWN",
                "strength": 0,
                "support": None,
                "resistance": None,
                "volatility": None
            }
            
        # Check if we have indicator results from the centralized calculation
        if hasattr(self, '_cached_indicator_results') and self._cached_indicator_results:
            # We already have calculated indicators from the indicators module
            indicators = self._cached_indicator_results
            
            # Get most recent values from the dataframe
            current = df.iloc[-1]
            current_price = current['close']
            
            # Extract trend information
            trend = "NEUTRAL"
            if indicators.get('sma_trend') == 'bullish' and indicators.get('ema_trend') == 'bullish':
                trend = "BULLISH"
            elif indicators.get('sma_trend') == 'bearish' and indicators.get('ema_trend') == 'bearish':
                trend = "BEARISH"
            elif indicators.get('sma_trend') == 'bullish' or indicators.get('ema_trend') == 'bullish':
                # When moving averages disagree, use MACD as tiebreaker
                if indicators.get('macd_trend') == 'bullish':
                    trend = "BULLISH"
            elif indicators.get('sma_trend') == 'bearish' or indicators.get('ema_trend') == 'bearish':
                # When moving averages disagree, use MACD as tiebreaker
                if indicators.get('macd_trend') == 'bearish':
                    trend = "BEARISH"
                
            # Calculate trend strength based on various factors
            strength = 50  # Neutral starting point
            
            # Factor 1: Relative position of fast MA to slow MA
            sma_short = indicators.get('sma_short', 0)
            sma_long = indicators.get('sma_long', 0)
            
            if sma_long > 0:
                # Measure the percentage difference between short and long MAs
                ma_diff_pct = ((sma_short / sma_long) - 1) * 100
                
                if trend == "BULLISH":
                    # In bullish trend, higher difference means stronger trend
                    strength += min(25, max(0, int(ma_diff_pct * 5)))
                elif trend == "BEARISH":
                    # In bearish trend, lower (more negative) difference means stronger trend
                    strength += min(25, max(0, int(abs(ma_diff_pct) * 5)))
            
            # Factor 2: RSI confirmation/contradiction
            rsi = indicators.get('rsi', 50)
            if trend == "BULLISH":
                if rsi > 60:  # Strong RSI in bullish trend
                    strength += 10
                elif rsi < 30:  # Oversold in bullish trend (contradiction)
                    strength -= 10
            elif trend == "BEARISH":
                if rsi < 40:  # Weak RSI in bearish trend
                    strength += 10
                elif rsi > 70:  # Overbought in bearish trend (contradiction)
                    strength -= 10
            
            # Factor 3: MACD confirmation
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            macd_hist = indicators.get('macd_histogram', 0)
            
            # MACD above zero line in bullish trend or below in bearish trend
            if (trend == "BULLISH" and macd > 0) or (trend == "BEARISH" and macd < 0):
                strength += 10
            
            # MACD crossover recently occurred (indicated by 'macd_crossover' in indicators)
            if indicators.get('macd_crossover') == 'bullish' and trend == "BULLISH":
                strength += 15
            elif indicators.get('macd_crossover') == 'bearish' and trend == "BEARISH":
                strength += 15
            
            # Ensure strength is within valid range
            strength = min(100, max(0, strength))
            
            # Calculate support and resistance levels
            lookback = self.indicator_config.get('support_resistance_lookback', 30)
            recent_df = df.tail(lookback)
            
            # Simple method: use recent lows as support and highs as resistance
            support = recent_df['low'].min()
            resistance = recent_df['high'].max()
            
            # Adjust to find more relevant levels
            # Find the highest low in the recent lookback period
            recent_lows = recent_df[recent_df['low'] < current_price]['low']
            if not recent_lows.empty:
                support = recent_lows.max()
                
            # Find the lowest high in the recent lookback period
            recent_highs = recent_df[recent_df['high'] > current_price]['high']
            if not recent_highs.empty:
                resistance = recent_highs.min()
            
            # Determine Bollinger Band position
            bb_position = indicators.get('bb_signal', 'MIDDLE')
            if bb_position == 'overbought':
                bb_position = "UPPER"
            elif bb_position == 'oversold':
                bb_position = "LOWER"
            elif bb_position == 'high':
                bb_position = "UPPER_80%"
            elif bb_position == 'low':
                bb_position = "LOWER_20%"
            
            # Prepare the result
            result = {
                "trend": trend,
                "strength": strength,
                "current_price": current_price,
                "support": support,
                "resistance": resistance,
                "bb_position": bb_position,
            }
            
            # Add all calculated indicators to the result
            # Include only scalars, not Series objects
            for key, value in indicators.items():
                if not isinstance(value, pd.Series) and key not in result and key != 'signal_summary':
                    result[key] = value
            
            # Add signal summary statistics
            if 'signal_summary' in indicators:
                result['bullish_signals'] = indicators['signal_summary'].get('bullish', 0)
                result['bearish_signals'] = indicators['signal_summary'].get('bearish', 0)
                result['neutral_signals'] = indicators['signal_summary'].get('neutral', 0)
            
            return result
            
        else:
            # Fallback to traditional calculation if the centralized indicators are not available
            # Get most recent values
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Extract key indicator values
            sma_short = self.indicator_config['sma_short']
            sma_long = self.indicator_config['sma_long']
            
            current_price = current['close']
            sma_short_value = current[f'sma_{sma_short}']
            sma_long_value = current[f'sma_{sma_long}']
            
            rsi = current['rsi']
            macd = current['macd']
            macd_signal = current['macd_signal']
            macd_histogram = current['macd_histogram']
            
            # Determine trend based on moving averages
            if sma_short_value > sma_long_value:
                trend = "BULLISH"
            elif sma_short_value < sma_long_value:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"
                
            # Determine trend strength (0-100)
            if trend == "BULLISH":
                # Higher values mean stronger bullish trend
                strength = min(100, max(0, int(50 + 50 * ((sma_short_value / sma_long_value) - 1) * 10)))
            elif trend == "BEARISH":
                # Higher values mean stronger bearish trend
                strength = min(100, max(0, int(50 + 50 * (1 - (sma_short_value / sma_long_value)) * 10)))
            else:
                strength = 50
                
            # Adjust strength based on RSI
            if rsi > 70:
                # Overbought
                if trend == "BULLISH":
                    strength = max(strength - 20, 0)  # Reduce bullish strength
                elif trend == "BEARISH":
                    strength = min(strength + 10, 100)  # Increase bearish strength
            elif rsi < 30:
                # Oversold
                if trend == "BEARISH":
                    strength = max(strength - 20, 0)  # Reduce bearish strength
                elif trend == "BULLISH":
                    strength = min(strength + 10, 100)  # Increase bullish strength
                    
            # Adjust strength based on MACD
            if macd > 0 and macd_histogram > 0:
                # Bullish MACD
                if trend == "BULLISH":
                    strength = min(strength + 15, 100)
                elif trend == "BEARISH":
                    strength = max(strength - 10, 0)
            elif macd < 0 and macd_histogram < 0:
                # Bearish MACD
                if trend == "BEARISH":
                    strength = min(strength + 15, 100)
                elif trend == "BULLISH":
                    strength = max(strength - 10, 0)
                    
            # Find support and resistance levels
            lookback = self.indicator_config['support_resistance_lookback']
            recent_df = df.tail(lookback)
            
            # Simple method: use recent lows as support and highs as resistance
            support = recent_df['low'].min()
            resistance = recent_df['high'].max()
            
            # Adjust to find more relevant levels
            # Find the highest low in the recent lookback period
            recent_lows = recent_df[recent_df['low'] < current_price]['low']
            if not recent_lows.empty:
                support = recent_lows.max()
                
            # Find the lowest high in the recent lookback period
            recent_highs = recent_df[recent_df['high'] > current_price]['high']
            if not recent_highs.empty:
                resistance = recent_highs.min()
                
            # Calculate volatility score (0-100)
            volatility = min(100, int(current.get('volatility', 0) * 100))
            
            # Bollinger Band width as percentage of price
            if all(key in current for key in ['bb_upper', 'bb_lower', 'close']):
                bb_width = (current['bb_upper'] - current['bb_lower']) / current['close'] * 100
            else:
                bb_width = None
            
            # ATR as percentage of price
            if all(key in current for key in ['atr', 'close']) and current['close'] > 0:
                atr_pct = current['atr'] / current['close'] * 100
            else:
                atr_pct = None
            
            # Determine if price is at significant BB level
            bb_position = None
            if all(key in current for key in ['close', 'bb_upper', 'bb_lower', 'bb_middle']):
                if current['close'] >= current['bb_upper']:
                    bb_position = "UPPER"
                elif current['close'] <= current['bb_lower']:
                    bb_position = "LOWER"
                else:
                    # Calculate relative position between middle and upper/lower bands
                    middle_to_price = current['close'] - current['bb_middle']
                    if middle_to_price > 0:
                        upper_range = current['bb_upper'] - current['bb_middle']
                        rel_position = middle_to_price / upper_range if upper_range > 0 else 0
                        bb_position = f"UPPER_{int(rel_position * 100)}%"
                    else:
                        lower_range = current['bb_middle'] - current['bb_lower']
                        rel_position = abs(middle_to_price) / lower_range if lower_range > 0 else 0
                        bb_position = f"LOWER_{int(rel_position * 100)}%"
            
            return {
                "trend": trend,
                "strength": strength,
                "current_price": current_price,
                "sma_short": sma_short_value,
                "sma_long": sma_long_value,
                "rsi": rsi,
                "macd": macd,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram,
                "support": support,
                "resistance": resistance,
                "volatility": volatility,
                "atr": current.get('atr'),
                "atr_pct": atr_pct,
                "bb_position": bb_position,
                "bb_width": bb_width
            }
    
    def _generate_signal(self, metrics: Dict[str, Any], df: pd.DataFrame) -> Tuple[str, int, str]:
        """
        Generate a trading signal based on technical analysis.
        
        Args:
            metrics: Technical analysis metrics
            df: DataFrame with price data and indicators
            
        Returns:
            Tuple of (signal, confidence, explanation)
        """
        # Extract key metrics
        trend = metrics.get('trend', 'NEUTRAL')
        strength = metrics.get('strength', 50)
        rsi = metrics.get('rsi', 50)
        macd = metrics.get('macd', 0)
        macd_histogram = metrics.get('macd_histogram', 0)
        bb_position = metrics.get('bb_position', None)
        
        # Check if we have signal summary data from the indicators module
        bullish_signals = metrics.get('bullish_signals', 0)
        bearish_signals = metrics.get('bearish_signals', 0)
        
        # Default to neutral
        signal = "NEUTRAL"
        confidence = 50
        explanation = "Technical indicators show balanced conditions"
        
        # Generate signal based on signal summary if available
        if bullish_signals > 0 or bearish_signals > 0:
            # Calculate the total number of signals
            total_signals = bullish_signals + bearish_signals + metrics.get('neutral_signals', 0)
            total_signals = max(1, total_signals)  # Avoid division by zero
            
            # Calculate the percentage of bullish vs bearish signals
            bullish_pct = (bullish_signals / total_signals) * 100
            bearish_pct = (bearish_signals / total_signals) * 100
            
            # Determine signal based on the dominant sentiment
            if bullish_pct > bearish_pct and bullish_pct > 50:
                signal = "BUY"
                # Scale confidence based on signal percentage and trend strength
                confidence = min(self.high_confidence, int(bullish_pct * 0.8 + strength * 0.2))
                explanation = f"Bullish signals ({bullish_pct:.1f}%) with trend strength {strength}/100"
            elif bearish_pct > bullish_pct and bearish_pct > 50:
                signal = "SELL"
                # Scale confidence based on signal percentage and trend strength
                confidence = min(self.high_confidence, int(bearish_pct * 0.8 + strength * 0.2))
                explanation = f"Bearish signals ({bearish_pct:.1f}%) with trend strength {strength}/100"
            else:
                # If signals are mixed or neutral
                signal = "NEUTRAL"
                confidence = self.low_confidence + int((max(bullish_pct, bearish_pct) - 50) * 0.6)
                explanation = f"Mixed signals with {bullish_pct:.1f}% bullish and {bearish_pct:.1f}% bearish"
        else:
            # Fall back to the traditional trend-based signal approach
            # Generate signal based on trend strength
            if trend == "BULLISH" and strength > 70:
                signal = "BUY"
                confidence = self.high_confidence
                explanation = f"Strong bullish trend with strength {strength}/100"
            elif trend == "BEARISH" and strength > 70:
                signal = "SELL"
                confidence = self.high_confidence
                explanation = f"Strong bearish trend with strength {strength}/100"
            elif trend == "BULLISH" and strength > 50:
                signal = "BUY"
                confidence = self.medium_confidence
                explanation = f"Moderate bullish trend with strength {strength}/100"
            elif trend == "BEARISH" and strength > 50:
                signal = "SELL"
                confidence = self.medium_confidence
                explanation = f"Moderate bearish trend with strength {strength}/100"
            else:
                signal = "NEUTRAL"
                confidence = self.low_confidence
                explanation = f"Neutral or weak trend with strength {strength}/100"
            
        # Adjust based on RSI
        if rsi > 70:
            if signal == "BUY":
                confidence = max(self.low_confidence, confidence - 20)
                explanation += f", but RSI is overbought at {rsi:.1f}"
            elif signal == "SELL":
                confidence = min(95, confidence + 10)
                explanation += f", confirmed by overbought RSI at {rsi:.1f}"
            elif signal == "NEUTRAL":
                signal = "SELL"
                confidence = self.medium_confidence
                explanation = f"Overbought conditions with RSI at {rsi:.1f}"
        elif rsi < 30:
            if signal == "SELL":
                confidence = max(self.low_confidence, confidence - 20)
                explanation += f", but RSI is oversold at {rsi:.1f}"
            elif signal == "BUY":
                confidence = min(95, confidence + 10)
                explanation += f", confirmed by oversold RSI at {rsi:.1f}"
            elif signal == "NEUTRAL":
                signal = "BUY"
                confidence = self.medium_confidence
                explanation = f"Oversold conditions with RSI at {rsi:.1f}"
                
        # Check for MACD crossover
        # First see if we have it in the metrics (from indicators module)
        macd_crossover = metrics.get('macd_crossover')
        
        if macd_crossover:
            # Use the pre-calculated crossover from the indicators module
            if macd_crossover == 'bullish':
                if signal == "BUY":
                    confidence = min(95, confidence + 15)
                    explanation += ", with recent bullish MACD crossover"
                elif signal == "NEUTRAL":
                    signal = "BUY"
                    confidence = self.medium_confidence
                    explanation = "Bullish MACD crossover detected"
                elif signal == "SELL":
                    confidence = max(self.low_confidence, confidence - 10)
                    explanation += ", but there's a conflicting bullish MACD crossover"
            elif macd_crossover == 'bearish':
                if signal == "SELL":
                    confidence = min(95, confidence + 15)
                    explanation += ", with recent bearish MACD crossover"
                elif signal == "NEUTRAL":
                    signal = "SELL"
                    confidence = self.medium_confidence
                    explanation = "Bearish MACD crossover detected"
                elif signal == "BUY":
                    confidence = max(self.low_confidence, confidence - 10)
                    explanation += ", but there's a conflicting bearish MACD crossover"
                    
        # Alternatively, calculate the crossover manually if not available from indicators
        elif df is not None and len(df) > 2:
            prev = df.iloc[-2]
            curr = df.iloc[-1]
            
            # Check for MACD crossover
            if 'macd' in prev and 'macd_signal' in prev and 'macd' in curr and 'macd_signal' in curr:
                macd_cross_up = prev['macd'] < prev['macd_signal'] and curr['macd'] > curr['macd_signal']
                macd_cross_down = prev['macd'] > prev['macd_signal'] and curr['macd'] < curr['macd_signal']
                
                if macd_cross_up:
                    if signal == "BUY":
                        confidence = min(95, confidence + 15)
                        explanation += ", with recent bullish MACD crossover"
                    elif signal == "NEUTRAL":
                        signal = "BUY"
                        confidence = self.medium_confidence
                        explanation = "Bullish MACD crossover detected"
                    elif signal == "SELL":
                        confidence = max(self.low_confidence, confidence - 10)
                        explanation += ", but there's a conflicting bullish MACD crossover"
                elif macd_cross_down:
                    if signal == "SELL":
                        confidence = min(95, confidence + 15)
                        explanation += ", with recent bearish MACD crossover"
                    elif signal == "NEUTRAL":
                        signal = "SELL"
                        confidence = self.medium_confidence
                        explanation = "Bearish MACD crossover detected"
                    elif signal == "BUY":
                        confidence = max(self.low_confidence, confidence - 10)
                        explanation += ", but there's a conflicting bearish MACD crossover"
        
        # Adjust based on Bollinger Bands
        if bb_position:
            if isinstance(bb_position, str):  # Ensure bb_position is a string
                if bb_position == "UPPER" or bb_position.startswith("UPPER_"):
                    if signal == "BUY":
                        confidence = max(self.low_confidence, confidence - 15)
                        explanation += ", but price is at upper Bollinger Band, suggesting caution"
                    elif signal == "SELL":
                        confidence = min(95, confidence + 10)
                        explanation += ", confirmed by price at upper Bollinger Band"
                elif bb_position == "LOWER" or bb_position.startswith("LOWER_"):
                    if signal == "SELL":
                        confidence = max(self.low_confidence, confidence - 15)
                        explanation += ", but price is at lower Bollinger Band, suggesting caution"
                    elif signal == "BUY":
                        confidence = min(95, confidence + 10)
                        explanation += ", confirmed by price at lower Bollinger Band"
        
        # Check for special indicator patterns
        # 1. Donchian Channel breakout
        donchian_breakout = metrics.get('donchian_breakout')
        if donchian_breakout:
            if donchian_breakout == 1:  # Bullish breakout
                if signal == "BUY":
                    confidence = min(95, confidence + 15)
                    explanation += ", with upper Donchian Channel breakout"
                elif signal == "NEUTRAL":
                    signal = "BUY"
                    confidence = self.medium_confidence
                    explanation = "Upper Donchian Channel breakout detected"
            elif donchian_breakout == -1:  # Bearish breakout
                if signal == "SELL":
                    confidence = min(95, confidence + 15)
                    explanation += ", with lower Donchian Channel breakout"
                elif signal == "NEUTRAL":
                    signal = "SELL"
                    confidence = self.medium_confidence
                    explanation = "Lower Donchian Channel breakout detected"
        
        # 2. ADX trend strength if available
        adx = metrics.get('adx')
        adx_trend = metrics.get('adx_trend')
        adx_strength = metrics.get('adx_strength')
        
        if adx and adx_trend and adx_strength:
            # Strong trend confirmation
            if adx > 30:  # ADX above 30 indicates a strong trend
                if (adx_trend == 'bullish' and signal == "BUY") or (adx_trend == 'bearish' and signal == "SELL"):
                    confidence = min(95, confidence + 10)
                    explanation += f", confirmed by strong {adx_trend} ADX at {adx:.1f}"
        
        # Cap confidence at a reasonable range
        confidence = min(95, max(self.low_confidence, confidence))
        
        # Log the signal generation
        logger.info(f"Generated {signal} signal for {metrics.get('current_price')} with {confidence}% confidence: {explanation}")
        
        return signal, confidence, explanation
        
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for technical analysis.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data dictionary
        """
        if not self.data_fetcher:
            logger.error(f"Data fetcher missing in {self.name}._fetch_market_data. Class: {self.__class__.__name__}")
            # Create a mock data provider as a fallback
            try:
                from agents.data_providers.mock_data_provider import MockDataProvider
                logger.warning(f"Creating fallback MockDataProvider in {self.name}._fetch_market_data")
                self.data_fetcher = MockDataProvider(symbol=symbol)
                logger.info(f"Successfully created MockDataProvider fallback")
            except Exception as e:
                logger.error(f"Failed to create fallback MockDataProvider: {str(e)}")
                return {
                    "symbol": symbol,
                    "error": "Data fetcher not available and fallback creation failed"
                }
            
        try:
            # Use interval from kwargs or default
            interval = kwargs.get('interval', self.default_interval)
            
            # Fetch OHLCV data
            limit = kwargs.get('limit', 100)
            ohlcv = self.data_fetcher.fetch_ohlcv(symbol, interval, limit=limit)
            
            # Try to fetch current ticker if available
            ticker = {}
            try:
                ticker = self.data_fetcher.get_ticker(symbol)
            except:
                pass
                
            market_data = {
                "ohlcv": ohlcv,
                "ticker": ticker,
                "symbol": symbol,
                "interval": interval
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}