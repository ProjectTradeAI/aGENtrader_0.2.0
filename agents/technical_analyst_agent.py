"""
aGENtrader v2 Technical Analyst Agent

This module provides a technical analysis agent that generates trading signals
based on common technical indicators like moving averages, RSI, MACD, etc.
"""

import os
import time
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from base_agent import BaseAnalystAgent
from decision_logger import decision_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('technical_analyst')

class TechnicalAnalystAgent(BaseAnalystAgent):
    """
    Agent that performs technical analysis on market data.
    
    This agent analyzes price charts using various technical indicators
    to generate trading signals and determine market trends.
    """
    
    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the technical analyst agent.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            config: Configuration parameters
        """
        super().__init__(data_fetcher, config)
        self.name = "TechnicalAnalystAgent"
        self.description = "Analyzes price action using technical indicators"
        
        # Configure trading signal indicators
        self.config = config or {}
        self.indicators = self.config.get('indicators', {
            'sma': {
                'short_period': 9,
                'long_period': 20,
                'weight': 1.0
            },
            'ema': {
                'short_period': 12,
                'long_period': 26,
                'weight': 1.5  # EMA given higher weight than SMA
            },
            'rsi': {
                'period': 14,
                'overbought': 70,
                'oversold': 30,
                'weight': 1.0
            },
            'macd': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'weight': 1.2
            },
            'bollinger_bands': {
                'period': 20,
                'std_dev': 2,
                'weight': 0.9
            },
            'volume': {
                'period': 20,
                'weight': 0.7  # Volume given lower weight than price-based indicators
            }
        })
        
        # Set confidence thresholds
        self.strong_signal_threshold = 75  # Confidence above this is considered a strong signal
        self.weak_signal_threshold = 30    # Confidence below this is considered a weak signal
    
    def analyze(
        self, 
        symbol: Optional[str] = None, 
        interval: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform technical analysis on market data.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Technical analysis results
        """
        start_time = time.time()
        
        # Validate input
        if not self.validate_input(symbol, interval):
            return self.build_error_response(
                "INVALID_INPUT", 
                f"Invalid input parameters: symbol={symbol}, interval={interval}"
            )
            
        try:
            # Fetch market data
            if not self.data_fetcher:
                return self.build_error_response(
                    "DATA_FETCHER_MISSING",
                    "Data fetcher not provided"
                )
            
            # Get OHLCV data
            ohlcv_data = self.data_fetcher.fetch_ohlcv(symbol, interval)
            
            if not ohlcv_data or len(ohlcv_data) < 30:  # Need enough data for analysis
                return self.build_error_response(
                    "INSUFFICIENT_DATA",
                    f"Insufficient data points for analysis. Got {len(ohlcv_data) if ohlcv_data else 0}, need at least 30."
                )
                
            # Convert data to DataFrame for easier analysis
            df = self._prepare_dataframe(ohlcv_data)
            
            # Calculate technical indicators
            indicators_df = self._calculate_indicators(df)
            
            # Generate trading signals from indicators
            signals, confidence, explanation = self._generate_signals(indicators_df)
            
            # Get current price
            current_price = float(df['close'].iloc[-1])
            
            execution_time = time.time() - start_time
            
            # Prepare results
            results = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "interval": interval,
                "current_price": current_price,
                "signal": signals,
                "confidence": confidence,
                "explanation": explanation,
                "indicators": self._get_indicator_values(indicators_df),
                "execution_time_seconds": execution_time,
                "status": "success"
            }
            
            # Log decision summary
            try:
                # Create a concise reason from the first explanation
                reason = explanation[0] if explanation else "Technical analysis signals"
                
                # Log the decision
                decision_logger.log_decision(
                    agent_name=self.name,
                    signal=signals,
                    confidence=confidence,
                    reason=reason,
                    symbol=symbol,
                    price=current_price,
                    timestamp=results["timestamp"],
                    additional_data={
                        "interval": interval,
                        "indicators": self._get_indicator_values(indicators_df)
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log decision: {str(e)}")
            
            # Return results
            return results
            
        except Exception as e:
            logger.error(f"Error performing technical analysis: {str(e)}", exc_info=True)
            return self.build_error_response(
                "TECHNICAL_ANALYSIS_ERROR",
                f"Error performing technical analysis: {str(e)}"
            )
    
    def _prepare_dataframe(self, ohlcv_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert OHLCV data to a pandas DataFrame.
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        # Create DataFrame
        df = pd.DataFrame(ohlcv_data)
        
        # Ensure the correct columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' missing from OHLCV data")
        
        # Convert string values to float if needed
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added technical indicators
        """
        # Create a copy to avoid modifying the original
        result_df = df.copy()
        
        # Calculate Simple Moving Averages (SMA)
        sma_config = self.indicators['sma']
        result_df[f'sma_{sma_config["short_period"]}'] = result_df['close'].rolling(window=sma_config['short_period']).mean()
        result_df[f'sma_{sma_config["long_period"]}'] = result_df['close'].rolling(window=sma_config['long_period']).mean()
        
        # Calculate Exponential Moving Averages (EMA)
        ema_config = self.indicators['ema']
        result_df[f'ema_{ema_config["short_period"]}'] = result_df['close'].ewm(span=ema_config['short_period'], adjust=False).mean()
        result_df[f'ema_{ema_config["long_period"]}'] = result_df['close'].ewm(span=ema_config['long_period'], adjust=False).mean()
        
        # Calculate Relative Strength Index (RSI)
        rsi_config = self.indicators['rsi']
        delta = result_df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=rsi_config['period']).mean()
        avg_loss = loss.rolling(window=rsi_config['period']).mean()
        rs = avg_gain / avg_loss
        result_df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        macd_config = self.indicators['macd']
        fast_ema = result_df['close'].ewm(span=macd_config['fast_period'], adjust=False).mean()
        slow_ema = result_df['close'].ewm(span=macd_config['slow_period'], adjust=False).mean()
        result_df['macd'] = fast_ema - slow_ema
        result_df['macd_signal'] = result_df['macd'].ewm(span=macd_config['signal_period'], adjust=False).mean()
        result_df['macd_histogram'] = result_df['macd'] - result_df['macd_signal']
        
        # Calculate Bollinger Bands
        bb_config = self.indicators['bollinger_bands']
        result_df['bb_middle'] = result_df['close'].rolling(window=bb_config['period']).mean()
        result_df['bb_std'] = result_df['close'].rolling(window=bb_config['period']).std()
        result_df['bb_upper'] = result_df['bb_middle'] + bb_config['std_dev'] * result_df['bb_std']
        result_df['bb_lower'] = result_df['bb_middle'] - bb_config['std_dev'] * result_df['bb_std']
        
        # Calculate Volume indicators
        vol_config = self.indicators['volume']
        result_df['volume_sma'] = result_df['volume'].rolling(window=vol_config['period']).mean()
        result_df['volume_ratio'] = result_df['volume'] / result_df['volume_sma']
        
        return result_df
    
    def _generate_signals(self, df: pd.DataFrame) -> Tuple[str, int, List[str]]:
        """
        Generate trading signals based on technical indicators.
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            Tuple of (signal, confidence, explanation)
        """
        # Make sure we have the latest data
        df = df.dropna().tail(5)
        
        if len(df) == 0:
            return "NEUTRAL", 50, ["Insufficient data for signal generation"]
        
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        signals = []
        explanations = []
        
        # Calculate SMA signals
        sma_config = self.indicators['sma']
        sma_short_name = f'sma_{sma_config["short_period"]}'
        sma_long_name = f'sma_{sma_config["long_period"]}'
        
        if latest[sma_short_name] > latest[sma_long_name] and previous[sma_short_name] <= previous[sma_long_name]:
            signals.append(("BUY", sma_config['weight'], f"SMA {sma_config['short_period']} crossed above SMA {sma_config['long_period']}"))
        elif latest[sma_short_name] < latest[sma_long_name] and previous[sma_short_name] >= previous[sma_long_name]:
            signals.append(("SELL", sma_config['weight'], f"SMA {sma_config['short_period']} crossed below SMA {sma_config['long_period']}"))
        
        # Calculate EMA signals
        ema_config = self.indicators['ema']
        ema_short_name = f'ema_{ema_config["short_period"]}'
        ema_long_name = f'ema_{ema_config["long_period"]}'
        
        if latest[ema_short_name] > latest[ema_long_name] and previous[ema_short_name] <= previous[ema_long_name]:
            signals.append(("BUY", ema_config['weight'], f"EMA {ema_config['short_period']} crossed above EMA {ema_config['long_period']}"))
        elif latest[ema_short_name] < latest[ema_long_name] and previous[ema_short_name] >= previous[ema_long_name]:
            signals.append(("SELL", ema_config['weight'], f"EMA {ema_config['short_period']} crossed below EMA {ema_config['long_period']}"))
            
        # Calculate RSI signals
        rsi_config = self.indicators['rsi']
        if latest['rsi'] < rsi_config['oversold']:
            signals.append(("BUY", rsi_config['weight'], f"RSI below oversold threshold ({rsi_config['oversold']})"))
        elif latest['rsi'] > rsi_config['overbought']:
            signals.append(("SELL", rsi_config['weight'], f"RSI above overbought threshold ({rsi_config['overbought']})"))
            
        # Calculate MACD signals
        if latest['macd'] > latest['macd_signal'] and previous['macd'] <= previous['macd_signal']:
            signals.append(("BUY", self.indicators['macd']['weight'], "MACD crossed above signal line"))
        elif latest['macd'] < latest['macd_signal'] and previous['macd'] >= previous['macd_signal']:
            signals.append(("SELL", self.indicators['macd']['weight'], "MACD crossed below signal line"))
            
        # Calculate Bollinger Band signals
        bb_config = self.indicators['bollinger_bands']
        if latest['close'] < latest['bb_lower']:
            signals.append(("BUY", bb_config['weight'], "Price below lower Bollinger Band"))
        elif latest['close'] > latest['bb_upper']:
            signals.append(("SELL", bb_config['weight'], "Price above upper Bollinger Band"))
            
        # Calculate Volume signals
        vol_config = self.indicators['volume']
        if latest['volume_ratio'] > 1.5 and latest['close'] > previous['close']:
            signals.append(("BUY", vol_config['weight'], "High volume on price increase"))
        elif latest['volume_ratio'] > 1.5 and latest['close'] < previous['close']:
            signals.append(("SELL", vol_config['weight'], "High volume on price decrease"))
            
        # Make a decision based on weighted signals
        if not signals:
            return "NEUTRAL", 50, ["No clear trading signals detected"]
            
        # Calculate weighted decision
        buy_weight = sum(weight for signal, weight, _ in signals if signal == "BUY")
        sell_weight = sum(weight for signal, weight, _ in signals if signal == "SELL")
        
        # Collect explanations
        explanations = [explanation for _, _, explanation in signals]
        
        # Determine final signal and confidence
        total_weights = sum(self.indicators[k]['weight'] for k in self.indicators)
        max_possible_confidence = 99  # Cap confidence at 99%
        
        if buy_weight > sell_weight:
            confidence = int(min(max_possible_confidence, (buy_weight / total_weights) * 100))
            return "BUY", confidence, explanations
        elif sell_weight > buy_weight:
            confidence = int(min(max_possible_confidence, (sell_weight / total_weights) * 100))
            return "SELL", confidence, explanations
        else:
            return "NEUTRAL", 50, explanations
    
    def _get_indicator_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract the latest values of all calculated indicators.
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            Dictionary of indicator values
        """
        if df.empty:
            return {}
            
        latest = df.iloc[-1]
        
        # Extract relevant indicators
        sma_config = self.indicators['sma']
        ema_config = self.indicators['ema']
        
        return {
            "price": {
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "close": float(latest['close']),
                "volume": float(latest['volume'])
            },
            "sma": {
                f"{sma_config['short_period']}": float(latest[f'sma_{sma_config["short_period"]}']),
                f"{sma_config['long_period']}": float(latest[f'sma_{sma_config["long_period"]}'])
            },
            "ema": {
                f"{ema_config['short_period']}": float(latest[f'ema_{ema_config["short_period"]}']),
                f"{ema_config['long_period']}": float(latest[f'ema_{ema_config["long_period"]}'])
            },
            "rsi": float(latest['rsi']),
            "macd": {
                "value": float(latest['macd']),
                "signal": float(latest['macd_signal']),
                "histogram": float(latest['macd_histogram'])
            },
            "bollinger_bands": {
                "upper": float(latest['bb_upper']),
                "middle": float(latest['bb_middle']),
                "lower": float(latest['bb_lower'])
            },
            "volume": {
                "current": float(latest['volume']),
                "average": float(latest['volume_sma']),
                "ratio": float(latest['volume_ratio'])
            }
        }