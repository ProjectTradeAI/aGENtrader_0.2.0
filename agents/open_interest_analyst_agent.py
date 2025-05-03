"""
aGENtrader v2 Open Interest Analyst Agent

This module provides an agent for analyzing open interest data from futures markets
to identify potential market reversals and trend strength.
"""

import os
import time
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from agents.base_agent import BaseAnalystAgent
from core.logging import decision_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('open_interest_analyst')

class OpenInterestAnalystAgent(BaseAnalystAgent):
    """
    Agent that analyzes open interest in futures markets.
    
    This agent evaluates changes in open interest alongside price movements
    to identify potential market reversals and assess trend strength.
    """
    
    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the open interest analyst agent.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            config: Configuration parameters
        """
        super().__init__(agent_name="open_interest_analyst")
        self.name = "OpenInterestAnalystAgent"
        self.description = "Analyzes open interest in futures markets"
        self.data_fetcher = data_fetcher
        self.config = config or {}
        
        # Initialize LLM client with agent-specific configuration
        from models.llm_client import LLMClient
        self.llm_client = LLMClient(agent_name="open_interest_analyst")
        
        # Get agent config
        self.agent_config = self.get_agent_config()
        self.trading_config = self.get_trading_config()
        
        # Use agent-specific timeframe from config if available
        oi_config = self.agent_config.get("open_interest_analyst", {})
        self.default_interval = oi_config.get("timeframe", self.trading_config.get("default_interval", "4h"))
        
        # Number of periods to analyze
        self.lookback_periods = self.config.get('lookback_periods', 30)
        
        # Set confidence thresholds
        self.high_confidence = 80   # For strong divergence/confirmation signals
        self.medium_confidence = 65 # For moderate signals
        self.low_confidence = 50    # For weak signals
        
    def analyze(
        self, 
        symbol: Optional[Union[str, Dict[str, Any]]] = None, 
        market_data: Optional[Dict[str, Any]] = None,
        interval: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze open interest data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            market_data: Pre-fetched market data (optional)
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Open interest analysis results
        """
        start_time = time.time()
        
        # Handle case where market_data is passed as first parameter (common in test harness)
        if isinstance(symbol, dict) and 'symbol' in symbol:
            # First parameter is actually market_data
            market_data = symbol
            symbol = market_data.get('symbol')
            if 'interval' in market_data and not interval:
                interval = market_data.get('interval')
                
        # Use agent-specific timeframe if none provided
        interval = interval or self.default_interval
        
        # Custom validation - skip parent class validation which expects only string symbols
            
        # Convert symbol to string if it's still a dict (safety check)
        if isinstance(symbol, dict):
            if 'symbol' in symbol:
                symbol = symbol['symbol']
            else:
                return self.build_error_response(
                    "INVALID_INPUT", 
                    "Invalid symbol format"
                )
            
        try:
            # Check if we have pre-fetched market data or need to fetch it
            oi_data = None
            price_data = None
            
            if market_data and isinstance(market_data, dict):
                if market_data.get("open_interest"):
                    oi_data = market_data.get("open_interest")
                    logger.info(f"Using pre-fetched open interest data with {len(oi_data)} records")
                
                if market_data.get("ohlcv"):
                    price_data = market_data.get("ohlcv")
                    logger.info(f"Using pre-fetched price data with {len(price_data)} records")
            
            # Fetch data if not provided
            if not oi_data or not price_data:
                # Fetch market data using data fetcher
                if not self.data_fetcher:
                    return self.build_error_response(
                        "DATA_FETCHER_MISSING",
                        "Data fetcher not provided"
                    )
                
                # Format symbol for futures market if needed
                # Ensure proper format for Binance futures API by converting any format to BASE+USDT
                if isinstance(symbol, str) and "/" in symbol:
                    base_asset = symbol.split("/")[0]
                    futures_symbol = f"{base_asset}USDT"
                else:
                    futures_symbol = symbol
                
                logger.info(f"Using futures symbol: {futures_symbol} (converted from {symbol})")
                
                try:
                    # Fetch open interest data
                    if not oi_data:
                        logger.info(f"Fetching open interest data for {futures_symbol}")
                        oi_data = self.data_fetcher.fetch_futures_open_interest(
                            symbol=futures_symbol, 
                            interval=interval,
                            limit=self.lookback_periods
                        )
                        
                    # Fetch price data
                    if not price_data:
                        logger.info(f"Fetching price data for {symbol}")
                        price_data = self.data_fetcher.fetch_ohlcv(
                            symbol=symbol, 
                            interval=interval,
                            limit=self.lookback_periods
                        )
                except Exception as e:
                    logger.warning(f"Error fetching data: {str(e)}")
                    # Don't use mock data - maintain data integrity
                    oi_data = []
                    price_data = []
                    logger.error(f"Failed to get real market data: {str(e)}")
            
            # Check if we have valid data
            if not oi_data:
                logger.warning(f"No open interest data for {symbol}")
                return self.build_error_response(
                    "INSUFFICIENT_DATA",
                    f"No open interest data available for {symbol}. This might be due to geographic restrictions or the pair not being available on futures markets."
                )
                
            if not price_data:
                logger.warning(f"No price data for {symbol}")
                return self.build_error_response(
                    "INSUFFICIENT_DATA",
                    f"No price data available for {symbol}. This might be due to API rate limits or connectivity issues."
                )
                
            # Check for minimum data points needed (more lenient check)
            min_data_points = 10
            if isinstance(oi_data, list) and len(oi_data) < min_data_points:
                logger.warning(f"Limited open interest data for {symbol}: {len(oi_data)} points available, {min_data_points} recommended")
                if len(oi_data) < 3:  # Absolute minimum for meaningful analysis
                    return self.build_error_response(
                        "INSUFFICIENT_DATA",
                        f"Only {len(oi_data)} open interest data points available for {symbol}, need at least 3 for minimal analysis."
                    )
                # If we have between 3 and min_data_points, we proceed but log a warning
            
            if isinstance(price_data, list) and len(price_data) < min_data_points:
                logger.warning(f"Limited price data for {symbol}: {len(price_data)} points available, {min_data_points} recommended")
                if len(price_data) < 3:  # Absolute minimum for meaningful analysis
                    return self.build_error_response(
                        "INSUFFICIENT_DATA",
                        f"Only {len(price_data)} price data points available for {symbol}, need at least 3 for minimal analysis."
                    )
                # If we have between 3 and min_data_points, we proceed but log a warning
            
            # Analyze the data
            analysis_result = self._analyze_open_interest(oi_data, price_data)
            
            # Get the current price
            current_price = 0
            if isinstance(price_data[-1], dict) and 'close' in price_data[-1]:
                current_price = float(price_data[-1]['close'])
            elif isinstance(price_data[-1], list) and len(price_data[-1]) >= 5:
                # Assuming [timestamp, open, high, low, close, volume] format
                current_price = float(price_data[-1][4])
            
            # Generate a trading signal
            signal, confidence, explanation = self._generate_signal(analysis_result)
            
            execution_time = time.time() - start_time
            
            # Prepare results
            results = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "interval": interval,
                "current_price": current_price,
                "signal": signal,
                "confidence": confidence,
                "explanation": [explanation],
                "metrics": analysis_result,
                "execution_time_seconds": execution_time,
                "status": "success"
            }
            
            # Log decision summary
            try:
                # Initialize decision logger
                from core.logging.decision_logger import DecisionLogger
                decision_logger_instance = DecisionLogger()
                
                # Ensure symbol is a string, not None or dict
                symbol_str = symbol if isinstance(symbol, str) else str(symbol)
                
                # Log the decision
                decision_logger_instance.log_decision(
                    agent_name=self.name,
                    signal=signal,
                    confidence=confidence,
                    reason=explanation,
                    symbol=symbol_str,
                    price=float(current_price),
                    timestamp=results["timestamp"],
                    additional_data={
                        "interval": interval,
                        "metrics": analysis_result
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to log decision: {str(e)}")
            
            # Return results
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing open interest: {str(e)}", exc_info=True)
            return self.build_error_response(
                "OPEN_INTEREST_ANALYSIS_ERROR",
                f"Error analyzing open interest: {str(e)}"
            )
    
    def _analyze_open_interest(self, oi_data: List[Any], price_data: List[Any]) -> Dict[str, Any]:
        """
        Analyze open interest data alongside price data.
        
        Args:
            oi_data: List of open interest records
            price_data: List of price data records
            
        Returns:
            Dictionary of open interest analysis metrics
        """
        # Extract open interest values and prices
        oi_values = []
        prices = []
        timestamps = []
        
        # Process open interest data
        for item in oi_data:
            if isinstance(item, dict):
                oi = None
                timestamp = None
                
                # Handle different field names used by different exchanges
                if 'openInterest' in item:
                    oi = item['openInterest']
                elif 'open_interest' in item:
                    oi = item['open_interest']
                elif 'value' in item:
                    oi = item['value']
                    
                if 'timestamp' in item:
                    timestamp = item['timestamp']
                elif 'time' in item:
                    timestamp = item['time']
                
                if oi is not None:
                    try:
                        oi_values.append(float(oi))
                        timestamps.append(timestamp)
                    except ValueError:
                        continue
            
            elif isinstance(item, list) and len(item) >= 2:
                # [timestamp, value] format
                try:
                    timestamps.append(item[0])
                    oi_values.append(float(item[1]))
                except (ValueError, IndexError):
                    continue
        
        # Process price data
        for item in price_data:
            if isinstance(item, dict) and 'close' in item:
                try:
                    prices.append(float(item['close']))
                except ValueError:
                    continue
            elif isinstance(item, list) and len(item) >= 5:
                # [timestamp, open, high, low, close, ...] format
                try:
                    prices.append(float(item[4]))  # Close price
                except (ValueError, IndexError):
                    continue
        
        # Ensure we have data for analysis
        # Works even with just 2 data points for basic delta analysis
        if len(oi_values) < 2 or len(prices) < 2:
            logger.warning("Insufficient data points for even basic analysis")
            return {
                "oi_change": 0,
                "price_change": 0,
                "divergence": False,
                "confirmation": False,
                "trend_strength": 0,
                "oi_trend": "neutral",
                "data_points": len(oi_values)
            }
            
        # Ensure equal lengths by taking the minimum of both datasets
        length = min(len(oi_values), len(prices))
        oi_values = oi_values[-length:]
        prices = prices[-length:]
        
        # Calculate period-by-period percentage changes for each data point
        oi_pct_changes = []
        price_pct_changes = []
        
        for i in range(1, len(oi_values)):
            # Calculate OI percent change, handling zero values
            if oi_values[i-1] != 0:
                oi_pct = (oi_values[i] - oi_values[i-1]) / oi_values[i-1] * 100
            else:
                oi_pct = 0 if oi_values[i] == 0 else 100  # Assume 100% increase if from zero to non-zero
                
            # Calculate price percent change, handling zero values
            if prices[i-1] != 0:
                price_pct = (prices[i] - prices[i-1]) / prices[i-1] * 100
            else:
                price_pct = 0 if prices[i] == 0 else 100  # Assume 100% increase if from zero to non-zero
                
            oi_pct_changes.append(oi_pct)
            price_pct_changes.append(price_pct)
        
        # Calculate overall changes from start to end
        if oi_values[0] != 0:
            recent_oi_change = ((oi_values[-1] - oi_values[0]) / oi_values[0]) * 100
        else:
            recent_oi_change = 0 if oi_values[-1] == 0 else 100
            
        if prices[0] != 0:
            recent_price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
        else:
            recent_price_change = 0 if prices[-1] == 0 else 100
        
        # Calculate very short term changes (last 3 periods or fewer if less data available)
        lookback = min(3, len(oi_values)-1)
        if lookback > 0:
            if oi_values[-lookback-1] != 0:
                short_term_oi_change = ((oi_values[-1] - oi_values[-lookback-1]) / oi_values[-lookback-1]) * 100
            else:
                short_term_oi_change = 0 if oi_values[-1] == 0 else 100
                
            if prices[-lookback-1] != 0:
                short_term_price_change = ((prices[-1] - prices[-lookback-1]) / prices[-lookback-1]) * 100
            else:
                short_term_price_change = 0 if prices[-1] == 0 else 100
        else:
            # Fall back to overall change if we don't have enough data points
            short_term_oi_change = recent_oi_change
            short_term_price_change = recent_price_change
        
        # Check for divergence/confirmation (delta-based analysis)
        divergence = (recent_oi_change * recent_price_change < 0)  # OI and price moving in opposite directions
        confirmation = (recent_oi_change * recent_price_change > 0)  # OI and price moving in same direction
        
        # Calculate correlation between OI and price changes if we have enough data
        correlation = 0
        if len(oi_pct_changes) >= 2 and len(price_pct_changes) >= 2:
            try:
                correlation = np.corrcoef(oi_pct_changes, price_pct_changes)[0, 1]
            except Exception as e:
                logger.debug(f"Error calculating correlation: {str(e)}")
                correlation = 0
        
        # Calculate trend strength (normalized to 0-1 range)
        trend_strength = min(abs(recent_price_change) / 100, 1.0)
        
        # Determine OI trend direction and magnitude
        if recent_oi_change > 5:
            oi_trend = "increasing"
            oi_strength = min(abs(recent_oi_change) / 20, 1.0)  # Normalize strength: 20% change = full strength
        elif recent_oi_change < -5:
            oi_trend = "decreasing"
            oi_strength = min(abs(recent_oi_change) / 20, 1.0)
        else:
            oi_trend = "neutral"
            oi_strength = 0
            
        # Determine price trend direction and magnitude
        if recent_price_change > 2:
            price_trend = "increasing"
            price_strength = min(abs(recent_price_change) / 10, 1.0)  # Normalize strength: 10% change = full strength
        elif recent_price_change < -2:
            price_trend = "decreasing"
            price_strength = min(abs(recent_price_change) / 10, 1.0)
        else:
            price_trend = "neutral"
            price_strength = 0
            
        # Create summary of OI and price changes for recent periods
        recent_oi_changes = [f"{oi_pct_changes[-i] if i <= len(oi_pct_changes) else 0:.2f}%" for i in range(min(8, len(oi_pct_changes)), 0, -1)]
        recent_price_changes = [f"{price_pct_changes[-i] if i <= len(price_pct_changes) else 0:.2f}%" for i in range(min(8, len(price_pct_changes)), 0, -1)]
        
        # Identify specific patterns
        # Rising OI + Rising Price = Strong bullish trend (longs building positions)
        # Rising OI + Falling Price = Strong bearish trend (shorts building positions)
        # Falling OI + Rising Price = Weak bullish trend (shorts covering)
        # Falling OI + Falling Price = Weak bearish trend (longs closing positions)
        pattern = "none"
        if recent_oi_change > 5 and recent_price_change > 2:
            pattern = "strong_bullish"  # Longs building up
        elif recent_oi_change > 5 and recent_price_change < -2:
            pattern = "strong_bearish"  # Shorts building up
        elif recent_oi_change < -5 and recent_price_change > 2:
            pattern = "weak_bullish"  # Shorts covering
        elif recent_oi_change < -5 and recent_price_change < -2:
            pattern = "weak_bearish"  # Longs liquidating
        elif abs(recent_oi_change) < 3:
            pattern = "position_equilibrium"  # Little change in positions
            
        return {
            "current_oi": oi_values[-1] if oi_values else 0,
            "oi_change": recent_oi_change,
            "oi_change_short_term": short_term_oi_change,
            "price_change": recent_price_change,
            "price_change_short_term": short_term_price_change,
            "divergence": divergence,
            "confirmation": confirmation,
            "trend_strength": trend_strength,
            "oi_trend": oi_trend,
            "oi_strength": oi_strength,
            "price_trend": price_trend,
            "price_strength": price_strength,
            "correlation": correlation,
            "pattern": pattern,
            "recent_oi_changes": recent_oi_changes,
            "recent_price_changes": recent_price_changes,
            "oi_price_ratio": oi_values[-1] / prices[-1] if prices[-1] > 0 else 0,
            "data_points": len(oi_values)
        }
    
    def _generate_signal(self, metrics: Dict[str, Any]) -> Tuple[str, int, str]:
        """
        Generate a trading signal based on open interest analysis.
        
        Args:
            metrics: Open interest analysis metrics
            
        Returns:
            Tuple of (signal, confidence, explanation)
        """
        # Extract key metrics
        oi_change = metrics.get('oi_change', 0)
        oi_change_short_term = metrics.get('oi_change_short_term', 0)
        price_change = metrics.get('price_change', 0)
        price_change_short_term = metrics.get('price_change_short_term', 0)
        divergence = metrics.get('divergence', False)
        confirmation = metrics.get('confirmation', False)
        trend_strength = metrics.get('trend_strength', 0)
        pattern = metrics.get('pattern', 'none')
        oi_trend = metrics.get('oi_trend', 'neutral')
        price_trend = metrics.get('price_trend', 'neutral')
        oi_strength = metrics.get('oi_strength', 0)
        price_strength = metrics.get('price_strength', 0)
        correlation = metrics.get('correlation', 0)
        recent_oi_changes = metrics.get('recent_oi_changes', [])
        recent_price_changes = metrics.get('recent_price_changes', [])
        data_points = metrics.get('data_points', 0)
        
        # Format recent changes for explanation
        oi_changes_str = ', '.join(recent_oi_changes) if recent_oi_changes else "N/A"
        price_changes_str = ', '.join(recent_price_changes) if recent_price_changes else "N/A"
        
        # Default to neutral, but with variable confidence based on data quality
        signal = "NEUTRAL"
        # Higher base confidence with more data points
        base_confidence = min(50 + int(data_points/2), 65) if data_points > 0 else 50
        confidence = base_confidence
        explanation = f"Open interest analysis based on {data_points} data points shows balanced market conditions"
        
        # Primary delta-based signal generation using pattern detection
        # These patterns take priority over other signals as they provide clearer directional bias
        if pattern == "strong_bullish":  # Rising OI + Rising Price = Longs building up
            signal = "BUY"
            confidence = self.high_confidence if oi_change > 10 and price_change > 5 else self.medium_confidence
            explanation = (f"Strong bullish pattern: Open interest increasing ({oi_change:.2f}%) with rising price ({price_change:.2f}%) "
                          f"indicates long positions are accumulating (bullish sentiment)")
            
        elif pattern == "strong_bearish":  # Rising OI + Falling Price = Shorts building up
            signal = "SELL"
            confidence = self.high_confidence if oi_change > 10 and price_change < -5 else self.medium_confidence
            explanation = (f"Strong bearish pattern: Open interest increasing ({oi_change:.2f}%) with falling price ({price_change:.2f}%) "
                          f"indicates short positions are accumulating (bearish sentiment)")
            
        elif pattern == "weak_bullish":  # Falling OI + Rising Price = Shorts covering
            signal = "BUY"
            confidence = self.medium_confidence
            explanation = (f"Weak bullish pattern: Open interest decreasing ({oi_change:.2f}%) with rising price ({price_change:.2f}%) "
                          f"indicates short positions are being covered (moderately bullish)")
            
        elif pattern == "weak_bearish":  # Falling OI + Falling Price = Longs liquidating
            signal = "SELL"
            confidence = self.medium_confidence
            explanation = (f"Weak bearish pattern: Open interest decreasing ({oi_change:.2f}%) with falling price ({price_change:.2f}%) "
                          f"indicates long positions are being liquidated (moderately bearish)")
                          
        elif pattern == "position_equilibrium" and abs(price_change) > 2:
            # Price is moving but OI isn't changing much
            if price_change > 2:
                signal = "BUY"
                confidence = self.low_confidence
                explanation = (f"Price increasing ({price_change:.2f}%) with little change in open interest ({oi_change:.2f}%) "
                              f"suggests natural demand rather than new position building")
            elif price_change < -2:
                signal = "SELL"
                confidence = self.low_confidence
                explanation = (f"Price decreasing ({price_change:.2f}%) with little change in open interest ({oi_change:.2f}%) "
                              f"suggests natural selling rather than new position building")
        
        # If we still don't have a signal from pattern analysis, check for traditional divergence or confirmation
        if signal == "NEUTRAL":
            if divergence:
                if price_change > 5 and oi_change < -3:
                    # Price up, OI down = potential reversal of uptrend
                    signal = "SELL"
                    confidence = self.high_confidence if abs(oi_change) > 10 else self.medium_confidence
                    explanation = (f"Bearish divergence: Price increased by {price_change:.2f}% while open interest "
                                   f"decreased by {abs(oi_change):.2f}%, suggesting potential reversal of uptrend")
                
                elif price_change < -5 and oi_change > 3:
                    # Price down, OI up = potential reversal of downtrend
                    signal = "BUY"
                    confidence = self.high_confidence if abs(oi_change) > 10 else self.medium_confidence
                    explanation = (f"Bullish divergence: Price decreased by {abs(price_change):.2f}% while open interest "
                                   f"increased by {oi_change:.2f}%, suggesting potential reversal of downtrend")
            
            # Check for confirmation signals
            elif confirmation:
                if price_change > 2 and oi_change > 5:
                    # Price up, OI up = strong uptrend continuation
                    signal = "BUY"
                    confidence = self.medium_confidence
                    explanation = (f"Uptrend confirmation: Price increased by {price_change:.2f}% with "
                                   f"open interest also rising by {oi_change:.2f}%, indicating trend strength")
                
                elif price_change < -2 and oi_change < -5:
                    # Price down, OI down = strong downtrend continuation
                    signal = "SELL"
                    confidence = self.medium_confidence
                    explanation = (f"Downtrend confirmation: Price decreased by {abs(price_change):.2f}% with "
                                   f"open interest also falling by {abs(oi_change):.2f}%, indicating trend strength")
        
        # If we still don't have a signal, check for short-term momentum
        if signal == "NEUTRAL" and abs(oi_change_short_term) > 3:
            if oi_change_short_term > 0 and price_change_short_term > 0:
                signal = "BUY"
                confidence = self.low_confidence
                explanation = (f"Short-term bullish momentum: Open interest increased by {oi_change_short_term:.2f}% "
                               f"with price up {price_change_short_term:.2f}% in recent periods")
            
            elif oi_change_short_term < 0 and price_change_short_term < 0:
                signal = "SELL"
                confidence = self.low_confidence
                explanation = (f"Short-term bearish momentum: Open interest decreased by {abs(oi_change_short_term):.2f}% "
                               f"with price down {abs(price_change_short_term):.2f}% in recent periods")
        
        # Add information about recent changes to the explanation
        explanation += f". Recent OI changes: [{oi_changes_str}], price changes: [{price_changes_str}]"
        
        # Consider correlation
        if abs(correlation) > 0.7:
            if signal != "NEUTRAL":
                explanation += f", strong correlation ({correlation:.2f}) between price and open interest"
                confidence = min(95, confidence + 10)
            else:
                explanation += f", strong correlation ({correlation:.2f}) between price and open interest, but no clear directional bias"
        
        # Consider trend strength to adjust confidence
        if trend_strength > 0.7:
            if signal != "NEUTRAL":
                explanation += f", with strong trend intensity"
                confidence = min(95, confidence + 5)
        
        # Check if we have very limited data and should indicate lower confidence
        if data_points < 5 and signal != "NEUTRAL":
            explanation += f" (based on limited data set of {data_points} points)"
            confidence = max(self.low_confidence, confidence - 10)
        
        return signal, confidence, explanation
        
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for open interest analysis.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data dictionary
        """
        if not self.data_fetcher:
            logger.warning("No data fetcher provided, cannot fetch market data")
            return {}
            
        interval = kwargs.get('interval', self.default_interval)
        
        try:
            # Format symbol for futures market if needed
            futures_symbol = f"{symbol}:USDT" if "/" in symbol else symbol
            
            # Fetch open interest data
            open_interest = self.data_fetcher.fetch_futures_open_interest(
                symbol=futures_symbol, 
                interval=interval,
                limit=self.lookback_periods
            )
            
            # Fetch OHLCV data
            ohlcv_data = self.data_fetcher.fetch_ohlcv(
                symbol=symbol, 
                interval=interval,
                limit=self.lookback_periods
            )
            
            # Try to fetch current ticker if available
            ticker = {}
            try:
                ticker = self.data_fetcher.get_ticker(symbol)
            except:
                pass
                
            market_data = {
                "open_interest": open_interest,
                "ohlcv": ohlcv_data,
                "ticker": ticker,
                "symbol": symbol,
                "interval": interval
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}
            
    def _generate_mock_data(self, symbol: str, interval: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate mock data for testing purposes.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Tuple of (open_interest_data, price_data)
        """
        current_time = datetime.now()
        
        # Determine interval in hours
        interval_hours = 1
        if interval.endswith('h'):
            interval_hours = int(interval[:-1])
        elif interval.endswith('d'):
            interval_hours = int(interval[:-1]) * 24
            
        # Generate data points
        oi_data = []
        price_data = []
        
        # Base values on the symbol
        if "BTC" in symbol.upper():
            base_oi = 100000000  # 100M for BTC
            base_price = 50000
        elif "ETH" in symbol.upper():
            base_oi = 50000000  # 50M for ETH
            base_price = 3000
        else:
            base_oi = 10000000  # 10M for others
            base_price = 100
            
        # Generate time series with some realistic patterns
        for i in range(self.lookback_periods):
            timestamp = int((current_time - timedelta(hours=interval_hours * (self.lookback_periods - i))).timestamp() * 1000)
            
            # Create some trending patterns
            if i < self.lookback_periods // 3:
                # First third: uptrend
                oi_factor = 1 + (i / self.lookback_periods * 0.2) + (np.random.random() - 0.5) * 0.05
                price_factor = 1 + (i / self.lookback_periods * 0.15) + (np.random.random() - 0.5) * 0.03
            elif i < 2 * self.lookback_periods // 3:
                # Middle third: sideways
                oi_factor = 1.2 + (np.random.random() - 0.5) * 0.05
                price_factor = 1.15 + (np.random.random() - 0.5) * 0.03
            else:
                # Last third: divergence (price up, OI down)
                oi_factor = 1.2 - ((i - 2 * self.lookback_periods // 3) / (self.lookback_periods // 3) * 0.1) + (np.random.random() - 0.5) * 0.05
                price_factor = 1.15 + ((i - 2 * self.lookback_periods // 3) / (self.lookback_periods // 3) * 0.1) + (np.random.random() - 0.5) * 0.03
                
            oi = base_oi * oi_factor
            price = base_price * price_factor
            
            oi_data.append({
                'symbol': symbol,
                'timestamp': timestamp,
                'openInterest': oi
            })
            
            price_data.append({
                'timestamp': timestamp,
                'open': price * (1 - 0.01 * np.random.random()),
                'high': price * (1 + 0.02 * np.random.random()),
                'low': price * (1 - 0.02 * np.random.random()),
                'close': price,
                'volume': base_oi * 0.1 * (0.8 + 0.4 * np.random.random())
            })
            
        logger.warning(f"Using mock data for {symbol} with {len(oi_data)} records")
        return oi_data, price_data