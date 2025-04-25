"""
Technical Analysis Agent Module

This module defines the TechnicalAnalysisAgent class, which is responsible
for analyzing market data using technical indicators and making trading recommendations.
"""
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import pandas as pd
    import numpy as np
except ImportError:
    logger.warning("Required libraries not installed. Install with: pip install pandas numpy")

class TechnicalAnalysisAgent:
    """
    Agent that performs technical analysis on market data to generate trading recommendations.
    Uses a structured decision-making approach based on technical indicators.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the technical analysis agent.
        
        Args:
            config: Optional configuration for the agent
        """
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            "indicators": [
                "SMA", "EMA", "RSI", "MACD", "BB",
                "ATR", "StochRSI", "OBV", "VWAP"
            ],
            "timeframes": ["short", "medium", "long"],
            "confidence_threshold": 0.6,
            "trend_strength_weight": 0.3,
            "momentum_weight": 0.25,
            "volatility_weight": 0.2, 
            "volume_weight": 0.15,
            "support_resistance_weight": 0.1
        }
        
        # Merge with provided config
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data and generate a trading recommendation.
        
        Args:
            symbol: Trading symbol
            data: Market data DataFrame with technical indicators
            
        Returns:
            Analysis result with trading recommendation
        """
        if data.empty:
            logger.warning(f"No data available for {symbol}")
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": "hold",
                "confidence": 0.0,
                "reasoning": "No technical data available for analysis",
                "indicators": {}
            }
        
        try:
            # Calculate indicator signals
            signals = self._calculate_signals(data)
            
            # Calculate component scores
            trend_score = self._analyze_trend(data, signals)
            momentum_score = self._analyze_momentum(data, signals)
            volatility_score = self._analyze_volatility(data, signals)
            volume_score = self._analyze_volume(data, signals)
            support_resistance_score = self._analyze_support_resistance(data)
            
            # Combine scores into a final decision
            weighted_score = (
                trend_score * self.config["trend_strength_weight"] +
                momentum_score * self.config["momentum_weight"] +
                volatility_score * self.config["volatility_weight"] +
                volume_score * self.config["volume_weight"] +
                support_resistance_score * self.config["support_resistance_weight"]
            )
            
            # Determine direction
            if weighted_score > self.config["confidence_threshold"]:
                direction = "buy"
                confidence = weighted_score
            elif weighted_score < -self.config["confidence_threshold"]:
                direction = "sell"
                confidence = abs(weighted_score)
            else:
                direction = "hold"
                confidence = 1 - abs(weighted_score)
            
            # Create reasoning explanation
            reasoning = self._generate_reasoning(
                symbol, direction, confidence, trend_score, momentum_score,
                volatility_score, volume_score, support_resistance_score, signals
            )
            
            # Compile result
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": direction,
                "confidence": min(1.0, abs(confidence)),  # Ensure confidence is between 0 and 1
                "reasoning": reasoning,
                "scores": {
                    "trend": trend_score,
                    "momentum": momentum_score,
                    "volatility": volatility_score,
                    "volume": volume_score,
                    "support_resistance": support_resistance_score,
                    "weighted": weighted_score
                },
                "indicators": signals
            }
            
            logger.info(f"Technical analysis for {symbol}: {direction} with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": "hold",
                "confidence": 0.0,
                "reasoning": f"Technical analysis error: {str(e)}",
                "indicators": {}
            }
    
    def _calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate signals from technical indicators"""
        signals = {}
        
        # Use only the most recent data for signals
        recent_data = data.iloc[-20:] if len(data) > 20 else data
        latest = recent_data.iloc[-1]
        
        # Moving Averages (SMA, EMA)
        if 'SMA_20' in recent_data.columns and 'SMA_50' in recent_data.columns:
            signals['sma_cross'] = 1 if latest['SMA_20'] > latest['SMA_50'] else -1
        
        if 'EMA_12' in recent_data.columns and 'EMA_26' in recent_data.columns:
            signals['ema_cross'] = 1 if latest['EMA_12'] > latest['EMA_26'] else -1
        
        # MACD
        if 'MACD' in recent_data.columns and 'MACD_Signal' in recent_data.columns:
            signals['macd'] = 1 if latest['MACD'] > latest['MACD_Signal'] else -1
            signals['macd_histogram'] = latest['MACD'] - latest['MACD_Signal']
            
            # MACD trend
            recent_hist = recent_data['MACD'] - recent_data['MACD_Signal']
            signals['macd_trend'] = 1 if recent_hist.diff().mean() > 0 else -1
        
        # RSI
        if 'RSI' in recent_data.columns:
            rsi = latest['RSI']
            signals['rsi'] = rsi
            signals['rsi_signal'] = 1 if rsi < 30 else (-1 if rsi > 70 else 0)
            signals['rsi_trend'] = 1 if recent_data['RSI'].diff().mean() > 0 else -1
        
        # Bollinger Bands
        if 'BB_Upper' in recent_data.columns and 'BB_Lower' in recent_data.columns:
            close = latest['close']
            upper = latest['BB_Upper']
            lower = latest['BB_Lower']
            middle = latest['BB_Middle']
            
            signals['bb_position'] = (close - lower) / (upper - lower) if (upper - lower) != 0 else 0.5
            signals['bb_signal'] = 1 if close < lower * 1.02 else (-1 if close > upper * 0.98 else 0)
            signals['bb_width'] = (upper - lower) / middle
        
        # Average True Range (ATR) - Volatility
        if 'ATR' in recent_data.columns:
            signals['atr'] = latest['ATR']
            signals['atr_percent'] = latest['ATR'] / latest['close'] * 100
        
        # Volume indicators - can be added when available
        
        return signals
    
    def _analyze_trend(self, data: pd.DataFrame, signals: Dict[str, Any]) -> float:
        """
        Analyze the market trend.
        
        Returns a score between -1 (strong downtrend) and 1 (strong uptrend)
        """
        trend_signals = []
        
        # Moving average trends
        if 'sma_cross' in signals:
            trend_signals.append(signals['sma_cross'] * 0.7)  # SMA cross is a strong signal
        
        if 'ema_cross' in signals:
            trend_signals.append(signals['ema_cross'] * 0.8)  # EMA cross is a stronger signal
        
        # Price vs Moving Averages
        if 'SMA_20' in data.columns:
            latest = data.iloc[-1]
            price_vs_sma = 1 if latest['close'] > latest['SMA_20'] else -1
            trend_signals.append(price_vs_sma * 0.5)
        
        # Linear regression slope or other trend measures
        if len(data) >= 20:
            # Simple slope calculation
            recent_close = data['close'].iloc[-20:].values
            slope = (recent_close[-1] - recent_close[0]) / recent_close[0]
            normalized_slope = min(max(slope * 10, -1), 1)  # Scale and bound the slope
            trend_signals.append(normalized_slope)
        
        # Average the signals, if any
        if trend_signals:
            return sum(trend_signals) / len(trend_signals)
        else:
            return 0.0
    
    def _analyze_momentum(self, data: pd.DataFrame, signals: Dict[str, Any]) -> float:
        """
        Analyze market momentum.
        
        Returns a score between -1 (strong negative momentum) and 1 (strong positive momentum)
        """
        momentum_signals = []
        
        # MACD signals
        if 'macd' in signals:
            momentum_signals.append(signals['macd'] * 0.7)
        
        if 'macd_trend' in signals:
            momentum_signals.append(signals['macd_trend'] * 0.8)
        
        # RSI signals
        if 'rsi' in signals:
            rsi = signals['rsi']
            # Convert RSI to a momentum score between -1 and 1
            if rsi < 30:
                # Oversold - positive momentum potential
                momentum_signals.append(min((30 - rsi) / 15, 1.0))
            elif rsi > 70:
                # Overbought - negative momentum potential
                momentum_signals.append(max((70 - rsi) / 15, -1.0))
            else:
                # Neutral zone - slight bias based on position in the range
                momentum_signals.append((rsi - 50) / 40)  # Scaled to be smaller
        
        if 'rsi_trend' in signals:
            momentum_signals.append(signals['rsi_trend'] * 0.5)
        
        # Rate of change (if we had it)
        
        # Average the signals, if any
        if momentum_signals:
            return sum(momentum_signals) / len(momentum_signals)
        else:
            return 0.0
    
    def _analyze_volatility(self, data: pd.DataFrame, signals: Dict[str, Any]) -> float:
        """
        Analyze market volatility.
        
        Returns a score between -1 (high volatility - bearish) and 1 (low volatility - bullish or neutral)
        """
        volatility_signals = []
        
        # Bollinger Band width
        if 'bb_width' in signals:
            bb_width = signals['bb_width']
            # Convert to a score: narrower bands are more positive for trend continuation
            normalized_width = min(bb_width * 2, 1.0)  # Scale appropriately
            volatility_signals.append(1.0 - normalized_width)  # Invert so low volatility is positive
        
        # ATR as percentage of price
        if 'atr_percent' in signals:
            atr_pct = signals['atr_percent']
            # Convert to a score: lower ATR % is generally more positive
            normalized_atr = min(atr_pct / 5.0, 1.0)  # 5% ATR is considered high
            volatility_signals.append(1.0 - normalized_atr * 2.0)  # Invert and scale
        
        # Bollinger Band position
        if 'bb_position' in signals:
            bb_pos = signals['bb_position'] 
            # Score based on position within the bands
            if bb_pos < 0.2:  # Near lower band
                volatility_signals.append(0.7)  # Potentially positive
            elif bb_pos > 0.8:  # Near upper band
                volatility_signals.append(-0.7)  # Potentially negative
            else:
                volatility_signals.append((0.5 - bb_pos) * 0.5)  # Small signal based on position
        
        # Average the signals, if any
        if volatility_signals:
            return sum(volatility_signals) / len(volatility_signals)
        else:
            return 0.0
    
    def _analyze_volume(self, data: pd.DataFrame, signals: Dict[str, Any]) -> float:
        """
        Analyze trading volume patterns.
        
        Returns a score between -1 (bearish volume) and 1 (bullish volume)
        """
        volume_signals = []
        
        # Check if volume data is available
        if 'volume' in data.columns and len(data) > 1:
            recent_data = data.iloc[-10:]
            
            # Volume trend
            vol_change = recent_data['volume'].pct_change()
            price_change = recent_data['close'].pct_change()
            
            # Calculate correlation between volume and price changes
            if len(vol_change) > 3:
                # Volume increasing with price is bullish
                corr = vol_change.corr(price_change)
                if not pd.isna(corr):  # Make sure we don't have NaN
                    volume_signals.append(corr)
            
            # Volume relative to moving average
            if len(data) >= 20:
                latest_volume = recent_data['volume'].iloc[-1]
                avg_volume = data['volume'].iloc[-20:].mean()
                vol_ratio = latest_volume / avg_volume if avg_volume > 0 else 1.0
                
                # Normalize and convert to signal
                vol_ratio_signal = min(vol_ratio - 1, 1.0) if vol_ratio > 1 else max(vol_ratio - 1, -1.0)
                
                # Higher than average volume is generally positive
                volume_signals.append(vol_ratio_signal * 0.5)
        
        # Average the signals, if any
        if volume_signals:
            return sum(volume_signals) / len(volume_signals)
        else:
            return 0.0  # Neutral if no volume data
    
    def _analyze_support_resistance(self, data: pd.DataFrame) -> float:
        """
        Analyze support and resistance levels.
        
        Returns a score between -1 (at strong resistance) and 1 (at strong support)
        """
        if len(data) < 20 or 'close' not in data.columns:
            return 0.0  # Not enough data
        
        try:
            recent_data = data.iloc[-50:] if len(data) >= 50 else data
            
            # Identify potential support/resistance levels
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            closes = recent_data['close'].values
            latest_close = closes[-1]
            
            # Very simple approach: check if price is near recent highs or lows
            recent_high = max(highs)
            recent_low = min(lows)
            range_size = recent_high - recent_low
            
            if range_size == 0:  # Avoid division by zero
                return 0.0
            
            # Relative position in the range
            position = (latest_close - recent_low) / range_size
            
            # Convert to a signal: near lows is bullish, near highs is bearish
            if position < 0.2:  # Near support
                return 0.8  # Strong bullish signal
            elif position > 0.8:  # Near resistance
                return -0.8  # Strong bearish signal
            else:
                # Linear interpolation between bullish and bearish
                return 0.8 - (position * 1.6)  # Scales from 0.8 to -0.8
                
        except Exception as e:
            logger.error(f"Error in support/resistance analysis: {str(e)}")
            return 0.0
    
    def _generate_reasoning(self, symbol: str, direction: str, confidence: float,
                          trend_score: float, momentum_score: float, volatility_score: float,
                          volume_score: float, support_resistance_score: float,
                          signals: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the trading decision"""
        if direction == "buy":
            decision_text = "bullish"
        elif direction == "sell":
            decision_text = "bearish"
        else:
            decision_text = "neutral"
        
        # Start with the overall conclusion
        reasoning = [f"Technical analysis for {symbol} is {decision_text} with {confidence:.1%} confidence."]
        
        # Add trend analysis
        if abs(trend_score) > 0.2:
            trend_text = "uptrend" if trend_score > 0 else "downtrend"
            strength = "strong" if abs(trend_score) > 0.7 else "moderate" if abs(trend_score) > 0.4 else "weak"
            reasoning.append(f"Price is in a {strength} {trend_text} (score: {trend_score:.2f}).")
            
            # Add moving average details if available
            if 'sma_cross' in signals:
                cross_text = "above" if signals['sma_cross'] > 0 else "below"
                reasoning.append(f"The short-term SMA is {cross_text} the long-term SMA.")
        
        # Add momentum analysis
        if abs(momentum_score) > 0.2:
            momentum_text = "positive" if momentum_score > 0 else "negative"
            strength = "strong" if abs(momentum_score) > 0.7 else "moderate" if abs(momentum_score) > 0.4 else "weak"
            reasoning.append(f"Momentum indicators show {strength} {momentum_text} momentum (score: {momentum_score:.2f}).")
            
            # Add MACD details if available
            if 'macd' in signals:
                macd_text = "bullish" if signals['macd'] > 0 else "bearish"
                reasoning.append(f"MACD shows a {macd_text} signal.")
            
            # Add RSI details if available
            if 'rsi' in signals:
                rsi_value = signals['rsi']
                if rsi_value < 30:
                    reasoning.append(f"RSI at {rsi_value:.1f} indicates oversold conditions.")
                elif rsi_value > 70:
                    reasoning.append(f"RSI at {rsi_value:.1f} indicates overbought conditions.")
                else:
                    reasoning.append(f"RSI at {rsi_value:.1f} is in neutral territory.")
        
        # Add volatility analysis
        if abs(volatility_score) > 0.3:
            vol_text = "low" if volatility_score > 0 else "high"
            reasoning.append(f"Market volatility is {vol_text} (score: {volatility_score:.2f}).")
            
            # Add ATR details if available
            if 'atr_percent' in signals:
                reasoning.append(f"ATR is {signals['atr_percent']:.2f}% of price.")
        
        # Add support/resistance analysis
        if abs(support_resistance_score) > 0.3:
            sr_text = "near support" if support_resistance_score > 0 else "near resistance"
            reasoning.append(f"Price is {sr_text} (score: {support_resistance_score:.2f}).")
        
        # Add volume analysis if significant
        if abs(volume_score) > 0.3:
            vol_text = "supporting the trend" if volume_score > 0 else "contradicting the trend"
            reasoning.append(f"Volume analysis is {vol_text} (score: {volume_score:.2f}).")
        
        # Combine all reasoning points
        return " ".join(reasoning)

# If executed as a script, run a simple demonstration
if __name__ == "__main__":
    # Mock data for testing
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(100, 5, 100),
            'high': np.random.normal(105, 5, 100),
            'low': np.random.normal(95, 5, 100),
            'close': np.random.normal(100, 10, 100),
            'volume': np.random.normal(1000000, 200000, 100),
            'SMA_5': np.random.normal(100, 8, 100),
            'SMA_20': np.random.normal(100, 5, 100),
            'SMA_50': np.random.normal(100, 3, 100),
            'EMA_12': np.random.normal(100, 7, 100),
            'EMA_26': np.random.normal(100, 4, 100),
            'MACD': np.random.normal(0, 2, 100),
            'MACD_Signal': np.random.normal(0, 1, 100),
            'RSI': np.random.normal(50, 15, 100),
            'BB_Upper': np.random.normal(110, 5, 100),
            'BB_Lower': np.random.normal(90, 5, 100),
            'BB_Middle': np.random.normal(100, 2, 100),
            'ATR': np.random.normal(2, 0.5, 100)
        })
        
        # Ensure some values make sense
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['RSI'] = data['RSI'].clip(0, 100)
        
        # Create and test the agent
        agent = TechnicalAnalysisAgent()
        result = agent.analyze("BTCUSDT", data)
        
        print(json.dumps(result, indent=2))
        
    except ImportError:
        print("Cannot run demonstration: required libraries not installed.")
        print("Install with: pip install pandas numpy")