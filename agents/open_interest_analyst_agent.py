"""
Open Interest Analyst Agent Module

This agent analyzes cryptocurrency open interest data to identify:
- Market participation trends
- Potential price reversal points
- Trend strength confirmations

The agent produces structured signals based on open interest changes
in relation to price movements.
"""

import os
import sys
import json
import logging
import time
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import required modules
from models.llm_client import LLMClient
from data.database import DatabaseConnector
from agents.base_agent import BaseAnalystAgent
from market_data_provider_factory import MarketDataProviderFactory

class OpenInterestAnalystAgent(BaseAnalystAgent):
    """
    Open Interest Analyst Agent that analyzes futures market open interest.
    
    This agent:
    - Fetches open interest data from Binance futures API
    - Analyzes open interest trends in relation to price movements
    - Identifies potential market continuation or reversal points
    - Generates trading signals based on OI and price correlation
    """
    
    def __init__(self):
        """Initialize the Open Interest Analyst Agent."""
        super().__init__()
        
        # Set up logger
        self.logger = logging.getLogger(f"aGENtrader.agents.{self.__class__.__name__}")
        
        # Initialize components
        self.db = DatabaseConnector()
        self.llm_client = LLMClient()
        
        # Load agent-specific configuration
        agent_config = self.get_agent_config()
        
        # Set default parameters
        self.default_symbol = "BTCUSDT"
        self.default_interval = agent_config.get("open_interest_analyst", {}).get("timeframe", "4h")
        self.lookback_periods = agent_config.get("open_interest_analyst", {}).get("lookback_periods", 20)
        
        # Configure signal thresholds
        self.oi_change_threshold = agent_config.get("open_interest_analyst", {}).get("oi_change_threshold", 0.05)  # 5%
        self.price_change_threshold = agent_config.get("open_interest_analyst", {}).get("price_change_threshold", 0.02)  # 2%
        
        self.logger.info(f"Open Interest Analyst Agent initialized with timeframe {self.default_interval}")
        
    def analyze(self, 
               symbol: Optional[str] = None, 
               interval: Optional[str] = None,
               market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze open interest data for a trading pair.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            interval: Time interval for analysis
            market_data: Pre-fetched market data (optional)
            
        Returns:
            Dictionary with analysis results
        """
        # Validate inputs and set defaults
        symbol = symbol or self.default_symbol
        interval = interval or self.default_interval
        
        # Format symbol for display
        display_symbol = symbol
        if "/" not in symbol:
            display_symbol = f"{symbol[:3]}/{symbol[3:]}" if len(symbol) > 3 else symbol
        
        # Validate input parameters
        if not self.validate_input(symbol, interval):
            return self.build_error_response(
                "INVALID_INPUT",
                f"Invalid input parameters: symbol={symbol}, interval={interval}"
            )
            
        self.logger.info(f"Analyzing open interest for {display_symbol} at {interval} interval")
        
        try:
            # Get open interest data
            oi_data = self.fetch_open_interest(symbol, interval)
            
            if not oi_data or len(oi_data) == 0:
                self.logger.warning(f"No open interest data available for {display_symbol}")
                return {
                    "symbol": display_symbol,
                    "interval": interval,
                    "error": "No open interest data available",
                    "signal": "NEUTRAL",  # Default to NEUTRAL on error
                    "confidence": 50,
                    "reason": "Insufficient open interest data for analysis"
                }
                
            # Perform analysis
            analysis_result = self.analyze_open_interest(oi_data, display_symbol, interval)
            
            # Ensure the result is valid
            result = self.validate_result(analysis_result)
            
            # Return the result
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing open interest: {str(e)}", exc_info=True)
            return self.handle_analysis_error(e, "open_interest_analysis")
            
    def fetch_open_interest(self, symbol: str, interval: str) -> List[Dict[str, Any]]:
        """
        Fetch open interest data from Binance Futures API.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "4h")
            
        Returns:
            List of open interest records with price data
        """
        try:
            # Format symbol for API
            formatted_symbol = symbol.replace("/", "") if "/" in symbol else symbol
            
            # Initialize data provider
            self.logger.info(f"Fetching open interest for {formatted_symbol} at {interval} interval")
            
            # Create Binance provider directly to access futures API with API keys
            # Import from root directory as it's located there
            import sys
            import os
            # Add project root to path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            if project_root not in sys.path:
                sys.path.append(project_root)
            from binance_data_provider import BinanceDataProvider
            
            api_key = os.environ.get('BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_API_SECRET')
            
            if not api_key or not api_secret:
                self.logger.warning("Binance API keys not found in environment, using unauthorized access")
                binance = BinanceDataProvider()
            else:
                self.logger.info("Using Binance API with authentication")
                binance = BinanceDataProvider(api_key=api_key, api_secret=api_secret)
            
            try:
                # Use the specialized method to get futures open interest data
                oi_history = binance.fetch_futures_open_interest(
                    symbol=formatted_symbol,
                    interval=interval,
                    limit=self.lookback_periods
                )
                
                # Verify we got valid data
                if not oi_history or not isinstance(oi_history, list):
                    self.logger.warning(f"Invalid open interest data returned for {formatted_symbol}")
                    return self._generate_mock_oi_data(formatted_symbol, interval)
                
                # Fetch price data to correlate with open interest
                price_data = self.fetch_price_data(formatted_symbol, interval)
                
                # Merge open interest data with corresponding price data
                merged_data = self.merge_oi_with_price(oi_history, price_data)
                    
                self.logger.info(f"Successfully fetched and merged {len(merged_data)} open interest records")
                return merged_data
                
            except Exception as fetch_error:
                self.logger.warning(f"Error accessing futures open interest API: {str(fetch_error)}")
                self.logger.warning("Generating simulated open interest data for demo purposes")
                return self._generate_mock_oi_data(formatted_symbol, interval)
                
        except Exception as e:
            self.logger.error(f"Error fetching open interest data: {str(e)}", exc_info=True)
            return []
            
    def _generate_mock_oi_data(self, symbol: str, interval: str) -> List[Dict[str, Any]]:
        """
        Generate simulated open interest data for demo/testing.
        Only used when the futures API is not accessible.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            List of simulated open interest records with price data
        """
        self.logger.info(f"Generating simulated open interest data for {symbol} at {interval}")
        
        # Get current timestamp
        now = int(time.time() * 1000)
        
        # Create simulated open interest data
        # Map interval to milliseconds
        interval_map = {
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "2h": 2 * 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "6h": 6 * 60 * 60 * 1000,
            "12h": 12 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000
        }
        interval_ms = interval_map.get(interval, 4 * 60 * 60 * 1000)  # Default to 4h
        
        # Generate price data as well
        mock_data = []
        base_price = 95000.0  # Base BTC price around $95k
        base_oi = 5000000.0   # Base open interest value
        
        for i in range(self.lookback_periods):
            # Calculate timestamp for this record
            timestamp = now - (i * interval_ms)
            
            # Generate price with some randomness and trend
            trend_factor = 0.0001  # Slight upward trend
            random_factor = (random.random() - 0.5) * 0.01  # -0.5% to +0.5%
            price = base_price * (1 + (trend_factor * i) + random_factor)
            
            # Generate open interest with correlation to price and some randomness
            oi_trend = 0.0005  # Slight increasing open interest
            oi_random = (random.random() - 0.5) * 0.02  # -1% to +1%
            price_correlation = 0.7  # Positive correlation with price
            oi_factor = 1 + (oi_trend * i) + oi_random + (price_correlation * random_factor)
            open_interest = base_oi * oi_factor
            
            # Create record
            record = {
                "timestamp": timestamp,
                "open_interest": open_interest,
                "open_interest_value": open_interest * price / 1000,  # Scaled value
                "price": price
            }
            
            mock_data.append(record)
            
        self.logger.info(f"Generated {len(mock_data)} simulated open interest records")
        return mock_data
    
    def fetch_price_data(self, symbol: str, interval: str) -> List[Dict[str, Any]]:
        """
        Fetch price data to correlate with open interest.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            List of price data records
        """
        try:
            # Use market data provider factory to get price data
            factory = MarketDataProviderFactory()
            price_data = factory.fetch_ohlcv(symbol, interval, limit=self.lookback_periods)
            
            return price_data
        except Exception as e:
            self.logger.error(f"Error fetching price data: {str(e)}", exc_info=True)
            return []
    
    def merge_oi_with_price(self, 
                          oi_data: List[Dict[str, Any]], 
                          price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge open interest data with price data by timestamp.
        
        Args:
            oi_data: Open interest data
            price_data: Price data
            
        Returns:
            List of merged records
        """
        merged_data = []
        
        # Create a dictionary of price data keyed by timestamp for quick lookup
        price_dict = {}
        for price_record in price_data:
            timestamp = price_record.get("timestamp")
            if timestamp:
                price_dict[timestamp] = price_record
        
        # For each OI record, find the closest price record by timestamp
        for oi_record in oi_data:
            oi_timestamp = oi_record.get("timestamp")
            if not oi_timestamp:
                continue
                
            # Find the closest price record (exact or nearest)
            if oi_timestamp in price_dict:
                price_record = price_dict[oi_timestamp]
            else:
                # Find the nearest timestamp
                nearest_timestamp = min(price_dict.keys(), key=lambda x: abs(x - oi_timestamp), default=None)
                if nearest_timestamp:
                    price_record = price_dict[nearest_timestamp]
                else:
                    continue  # Skip if no price data found
            
            # Merge the records
            merged_record = {
                "timestamp": oi_timestamp,
                "open_interest": float(oi_record.get("sumOpenInterest", 0)),
                "open_interest_value": float(oi_record.get("sumOpenInterestValue", 0)),
                "price": price_record.get("close", 0)
            }
            
            merged_data.append(merged_record)
        
        return merged_data
            
    def analyze_open_interest(self, 
                             oi_data: List[Dict[str, Any]],
                             symbol: str, 
                             interval: str) -> Dict[str, Any]:
        """
        Analyze open interest data to generate trading signals.
        
        Args:
            oi_data: List of open interest records with price data
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Analysis result with trading signal
        """
        try:
            # Extract data series
            timestamps = []
            oi_values = []
            prices = []
            
            for item in oi_data:
                timestamps.append(item.get("timestamp", 0))
                oi_values.append(item.get("open_interest", 0))
                prices.append(item.get("price", 0))
            
            # Calculate changes in OI and price
            oi_changes = []
            price_changes = []
            
            for i in range(1, len(oi_values)):
                oi_change = (oi_values[i-1] - oi_values[i]) / oi_values[i] if oi_values[i] > 0 else 0
                price_change = (prices[i-1] - prices[i]) / prices[i] if prices[i] > 0 else 0
                
                oi_changes.append(oi_change)
                price_changes.append(price_change)
            
            # If insufficient data, return neutral signal
            if len(oi_changes) < 3 or len(price_changes) < 3:
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "signal": "NEUTRAL",
                    "confidence": 50,
                    "reason": "Insufficient data points for meaningful analysis"
                }
            
            # Determine trends
            oi_trend = self.determine_trend(oi_values[:5])
            price_trend = self.determine_trend(prices[:5])
            
            # Get latest values
            latest_oi = oi_values[0] if oi_values else 0
            latest_price = prices[0] if prices else 0
            
            # Calculate percentage changes for recent periods
            recent_oi_change = (oi_values[0] - oi_values[min(4, len(oi_values)-1)]) / oi_values[min(4, len(oi_values)-1)] if len(oi_values) > 4 and oi_values[min(4, len(oi_values)-1)] > 0 else 0
            recent_price_change = (prices[0] - prices[min(4, len(prices)-1)]) / prices[min(4, len(prices)-1)] if len(prices) > 4 and prices[min(4, len(prices)-1)] > 0 else 0
            
            # Default values
            signal = "HOLD"
            confidence = 50
            reason = "Neutral open interest conditions"
            
            # Signal generation logic based on OI and price trends
            if oi_trend == "rising" and price_trend == "rising" and recent_oi_change > self.oi_change_threshold:
                # Rising OI + rising price = strong trend continuation
                signal = "BUY"
                confidence = min(95, int(50 + (recent_oi_change * 100) + (recent_price_change * 100)))
                reason = f"Rising open interest (+{recent_oi_change:.2%}) with rising price (+{recent_price_change:.2%}) confirms bullish trend"
                
            elif oi_trend == "rising" and price_trend == "falling" and recent_oi_change > self.oi_change_threshold:
                # Rising OI + falling price = strong bearish momentum
                signal = "SELL"
                confidence = min(95, int(50 + (recent_oi_change * 100) + (abs(recent_price_change) * 100)))
                reason = f"Rising open interest (+{recent_oi_change:.2%}) with falling price ({recent_price_change:.2%}) indicates bearish momentum"
                
            elif oi_trend == "falling" and price_trend == "rising" and abs(recent_oi_change) > self.oi_change_threshold:
                # Falling OI + rising price = weakening bullish trend
                signal = "HOLD"
                confidence = min(85, int(60 - (abs(recent_oi_change) * 50)))
                reason = f"Falling open interest ({recent_oi_change:.2%}) with rising price (+{recent_price_change:.2%}) indicates weakening trend"
                
            elif oi_trend == "falling" and price_trend == "falling" and abs(recent_oi_change) > self.oi_change_threshold:
                # Falling OI + falling price = weakening bearish trend, possible reversal
                signal = "HOLD"
                confidence = min(85, int(60 - (abs(recent_oi_change) * 50)))
                reason = f"Falling open interest ({recent_oi_change:.2%}) with falling price ({recent_price_change:.2%}) indicates exhausted selling"
                
            else:
                # No clear signal
                signal = "HOLD"
                confidence = 60
                reason = f"No significant correlation between open interest ({recent_oi_change:.2%}) and price ({recent_price_change:.2%})"
            
            # Create detailed metrics
            oi_metrics = {
                "current_oi": latest_oi,
                "oi_trend": oi_trend,
                "price_trend": price_trend,
                "recent_oi_change": recent_oi_change,
                "recent_price_change": recent_price_change,
                "oi_price_correlation": self.calculate_correlation(oi_values[:min(10, len(oi_values))], prices[:min(10, len(prices))]),
                "data_points": list(zip(timestamps, oi_values, prices))
            }
            
            # Prepare final result
            result = {
                "symbol": symbol,
                "interval": interval,
                "signal": signal,
                "confidence": confidence,
                "reason": reason,
                "oi_metrics": oi_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Open interest analysis complete for {symbol}: {signal} with {confidence}% confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing open interest: {str(e)}", exc_info=True)
            return {
                "symbol": symbol,
                "interval": interval,
                "error": f"Analysis failed: {str(e)}",
                "signal": "NEUTRAL",
                "confidence": 50,
                "reason": "Error in open interest analysis"
            }
    
    def determine_trend(self, values: List[float]) -> str:
        """
        Determine the trend direction from a series of values.
        
        Args:
            values: List of values to analyze
            
        Returns:
            Trend direction as string ("rising", "falling", "flat")
        """
        if not values or len(values) < 2:
            return "flat"
            
        # Simple linear regression to determine slope
        x = list(range(len(values)))
        y = values
        
        if len(x) != len(y):
            return "flat"
            
        n = len(x)
        
        # Calculate slope using least squares method
        if n < 2:
            return "flat"
            
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_val * y_val for x_val, y_val in zip(x, y))
        sum_xx = sum(x_val ** 2 for x_val in x)
        
        # Avoid division by zero
        if (n * sum_xx - sum_x ** 2) == 0:
            return "flat"
            
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
        
        # Determine trend based on slope
        if slope > 0.001:
            return "rising"
        elif slope < -0.001:
            return "falling"
        else:
            return "flat"
    
    def calculate_correlation(self, series1: List[float], series2: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient between two series.
        
        Args:
            series1: First data series
            series2: Second data series
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        # Ensure both series have the same length
        min_len = min(len(series1), len(series2))
        if min_len < 2:
            return 0.0
            
        series1 = series1[:min_len]
        series2 = series2[:min_len]
        
        # Calculate means
        mean1 = sum(series1) / min_len
        mean2 = sum(series2) / min_len
        
        # Calculate correlation coefficient
        numerator = sum((series1[i] - mean1) * (series2[i] - mean2) for i in range(min_len))
        denominator1 = sum((x - mean1) ** 2 for x in series1)
        denominator2 = sum((x - mean2) ** 2 for x in series2)
        
        # Avoid division by zero
        if denominator1 == 0 or denominator2 == 0:
            return 0.0
            
        correlation = numerator / ((denominator1 ** 0.5) * (denominator2 ** 0.5))
        
        # Clamp to [-1, 1] range
        return max(-1.0, min(1.0, correlation))

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create agent
    agent = OpenInterestAnalystAgent()
    
    # Run analysis
    analysis = agent.analyze("BTCUSDT", "4h")
    
    # Print results
    print(json.dumps(analysis, indent=2))