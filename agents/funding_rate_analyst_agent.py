"""
aGENtrader v2 Funding Rate Analyst Agent

This module provides a funding rate analysis agent that evaluates perpetual futures 
funding rates to identify market sentiment and potential entry/exit signals.
"""

import os
import time
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from agents.base_agent import BaseAnalystAgent
from core.logging import decision_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('funding_rate_analyst')

class FundingRateAnalystAgent(BaseAnalystAgent):
    """
    Agent that analyzes funding rates in perpetual futures markets.
    
    This agent evaluates historical funding rates and their trends to
    identify market sentiment and potential entry/exit opportunities.
    """
    
    def __init__(self, data_fetcher=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the funding rate analyst agent.
        
        Args:
            data_fetcher: Data fetcher instance for retrieving market data
            config: Configuration parameters
        """
        super().__init__(agent_name="funding_rate_analyst")
        self.name = "FundingRateAnalystAgent"
        self.description = "Analyzes funding rates in perpetual futures markets"
        self.data_fetcher = data_fetcher
        
        # Initialize LLM client with agent-specific configuration
        from models.llm_client import LLMClient
        self.llm_client = LLMClient(agent_name="funding_rate_analyst")
        
        # Get agent config
        self.agent_config = self.get_agent_config()
        self.trading_config = self.get_trading_config()
        
        # Use agent-specific timeframe from config if available
        funding_config = self.agent_config.get("funding_rate_analyst", {})
        self.default_interval = funding_config.get("timeframe", self.trading_config.get("default_interval", "1h"))
        
        # Configure thresholds for funding rate analysis
        self.config = config or {}
        self.thresholds = self.config.get('thresholds', {
            'high_positive': 0.01,     # 0.01% per funding interval is considered high positive
            'moderate_positive': 0.005, # 0.005% is moderate positive
            'neutral': 0.001,          # Between -0.001% and 0.001% is considered neutral
            'moderate_negative': -0.005, # -0.005% is moderate negative
            'high_negative': -0.01      # -0.01% or below is considered high negative
        })
        
        # Number of funding periods to analyze
        self.lookback_periods = self.config.get('lookback_periods', 30)
        
        # Set confidence thresholds
        self.high_confidence = 80   # For extreme funding rate values
        self.medium_confidence = 65 # For moderate funding rate values
        self.low_confidence = 50    # For weak funding rate signals
        
    def analyze(
        self, 
        symbol: Optional[str] = None, 
        interval: Optional[str] = None,
        market_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze funding rates for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            interval: Time interval (mainly used for consistency with other agents)
            market_data: Pre-fetched market data (optional)
            **kwargs: Additional parameters
            
        Returns:
            Funding rate analysis results
        """
        start_time = time.time()
        
        # Use agent-specific timeframe if none provided
        interval = interval or self.default_interval
        
        # Validate input
        if not self.validate_input(symbol, interval):
            return self.build_error_response(
                "INVALID_INPUT", 
                f"Invalid input parameters: symbol={symbol}, interval={interval}"
            )
            
        try:
            # Check if we have pre-fetched market data or need to fetch it
            funding_data = None
            if market_data and isinstance(market_data, dict) and market_data.get("funding_rates"):
                funding_data = market_data.get("funding_rates")
                logger.info(f"Using pre-fetched funding rate data with {len(funding_data)} records")
            else:
                # Fetch market data using data fetcher
                if not self.data_fetcher:
                    return self.build_error_response(
                        "DATA_FETCHER_MISSING",
                        "Data fetcher not provided"
                    )
                
                # Format symbol for futures market if needed
                futures_symbol = f"{symbol}:USDT" if "/" in symbol else symbol
                
                try:
                    logger.info(f"Fetching funding rate data for {futures_symbol}")
                    # Try to fetch historical funding rates
                    funding_data = self.data_fetcher.fetch_funding_rates(
                        symbol=futures_symbol, 
                        limit=self.lookback_periods
                    )
                except Exception as e:
                    logger.warning(f"Error fetching funding rates: {str(e)}")
                    logger.info("Attempting mock funding rate data for isolated testing")
                    # For isolated testing when actual data isn't available
                    funding_data = self._generate_mock_funding_data(symbol)
            
            if not funding_data or len(funding_data) == 0:
                return self.build_error_response(
                    "INSUFFICIENT_DATA",
                    "No funding rate data available"
                )
                
            # Analyze the funding rate data
            analysis_result = self._analyze_funding_rates(funding_data)
            
            # Get the current price if available
            current_price = 0
            try:
                if self.data_fetcher:
                    current_price = self.data_fetcher.get_current_price(symbol)
            except Exception as e:
                logger.warning(f"Unable to fetch current price: {str(e)}")
                if market_data and market_data.get("ticker") and market_data.get("ticker").get("last"):
                    current_price = float(market_data.get("ticker").get("last"))
            
            # Generate a trading signal based on the funding rate analysis
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
                decision_logger.log_decision(
                    agent_name=self.name,
                    signal=signal,
                    confidence=confidence,
                    reason=explanation,
                    symbol=symbol,
                    price=current_price,
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
            logger.error(f"Error analyzing funding rates: {str(e)}", exc_info=True)
            return self.build_error_response(
                "FUNDING_RATE_ANALYSIS_ERROR",
                f"Error analyzing funding rates: {str(e)}"
            )
    
    def _analyze_funding_rates(self, funding_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze funding rate data.
        
        Args:
            funding_data: List of funding rate records
            
        Returns:
            Dictionary of funding rate metrics
        """
        # Extract funding rates
        rates = []
        timestamps = []
        
        for item in funding_data:
            # Handle different data formats
            if isinstance(item, dict):
                # Format from exchange API
                rate = item.get('rate', None)
                if rate is None and 'fundingRate' in item:
                    rate = item.get('fundingRate')
                
                # Convert from percentage or string if needed
                if isinstance(rate, str):
                    try:
                        rate = float(rate)
                    except ValueError:
                        continue
                        
                # Some APIs provide the rate as a percentage
                if rate and abs(rate) > 1:
                    rate = rate / 100  # Convert percentage to decimal
                
                timestamp = item.get('timestamp', None)
                if timestamp is None and 'time' in item:
                    timestamp = item.get('time')
                    
            # It could also be a list [timestamp, rate]
            elif isinstance(item, list) and len(item) >= 2:
                timestamp = item[0]
                rate = item[1]
            else:
                continue
                
            if rate is not None:
                rates.append(float(rate))
                timestamps.append(timestamp)
        
        # Check if we have valid data
        if not rates:
            logger.warning("No valid funding rate data found")
            return {
                "current_rate": 0,
                "average_rate": 0,
                "rate_trend": 0,
                "volatility": 0,
                "is_extreme": False,
                "direction": "neutral"
            }
        
        # Calculate metrics
        current_rate = rates[-1]
        average_rate = sum(rates) / len(rates)
        
        # Calculate the trend (positive means increasing funding rate)
        if len(rates) >= 3:
            rate_trend = rates[-1] - rates[0]
        else:
            rate_trend = 0
            
        # Calculate volatility
        if len(rates) >= 2:
            diffs = [abs(rates[i] - rates[i-1]) for i in range(1, len(rates))]
            volatility = sum(diffs) / len(diffs)
        else:
            volatility = 0
            
        # Determine if the current rate is extreme
        is_extreme = (current_rate > self.thresholds['high_positive'] or 
                      current_rate < self.thresholds['high_negative'])
                      
        # Determine direction based on current rate
        if current_rate > self.thresholds['high_positive']:
            direction = "strongly_positive"
        elif current_rate > self.thresholds['moderate_positive']:
            direction = "moderately_positive"
        elif current_rate < self.thresholds['high_negative']:
            direction = "strongly_negative"
        elif current_rate < self.thresholds['moderate_negative']:
            direction = "moderately_negative"
        else:
            direction = "neutral"
        
        return {
            "current_rate": current_rate,
            "average_rate": average_rate,
            "rate_trend": rate_trend,
            "volatility": volatility,
            "is_extreme": is_extreme,
            "direction": direction,
            "rates": rates[-10:],  # Include the last 10 rates for reference
            "rate_count": len(rates)
        }
    
    def _generate_signal(self, metrics: Dict[str, Any]) -> Tuple[str, int, str]:
        """
        Generate a trading signal based on funding rate analysis.
        
        Args:
            metrics: Funding rate metrics
            
        Returns:
            Tuple of (signal, confidence, explanation)
        """
        # Extract key metrics
        current_rate = metrics.get('current_rate', 0)
        average_rate = metrics.get('average_rate', 0)
        rate_trend = metrics.get('rate_trend', 0)
        volatility = metrics.get('volatility', 0)
        is_extreme = metrics.get('is_extreme', False)
        direction = metrics.get('direction', 'neutral')
        
        # Default to neutral
        signal = "NEUTRAL"
        confidence = 50
        explanation = "Funding rates are within normal range"
        
        # Generate signal based on funding rate direction
        if direction == "strongly_positive":
            # High positive funding rates indicate longs are paying shorts
            # This often suggests the market is overly bullish, potential for reversal
            signal = "SELL"
            confidence = self.high_confidence if is_extreme else self.medium_confidence
            explanation = (f"High positive funding rate ({current_rate:.4f}) indicates market is overly bullish, "
                           f"potential for short-term reversal (contrarian signal)")
                           
        elif direction == "moderately_positive":
            signal = "NEUTRAL"
            confidence = self.medium_confidence
            explanation = (f"Moderately positive funding rate ({current_rate:.4f}) suggests some bullish bias, "
                           f"but not extreme enough for a strong contrarian signal")
                           
        elif direction == "strongly_negative":
            # High negative funding rates indicate shorts are paying longs
            # This often suggests the market is overly bearish, potential for reversal
            signal = "BUY"
            confidence = self.high_confidence if is_extreme else self.medium_confidence
            explanation = (f"High negative funding rate ({current_rate:.4f}) indicates market is overly bearish, "
                           f"potential for short-term reversal (contrarian signal)")
                           
        elif direction == "moderately_negative":
            signal = "NEUTRAL"
            confidence = self.medium_confidence
            explanation = (f"Moderately negative funding rate ({current_rate:.4f}) suggests some bearish bias, "
                           f"but not extreme enough for a strong contrarian signal")
                           
        else:  # neutral
            signal = "NEUTRAL"
            confidence = self.low_confidence
            explanation = f"Neutral funding rate ({current_rate:.4f}) indicates balanced market sentiment"
            
        # Consider the trend in funding rates
        if abs(rate_trend) > 0.005:
            # Significant change in funding rates
            trend_direction = "increasing" if rate_trend > 0 else "decreasing"
            explanation += f", with {trend_direction} trend over the analysis period"
            
            # Adjust confidence based on trend confirmation or contradiction
            if (signal == "BUY" and rate_trend < 0) or (signal == "SELL" and rate_trend > 0):
                confidence = min(95, confidence + 10)  # Strengthen confidence if trend confirms signal
            elif (signal == "BUY" and rate_trend > 0) or (signal == "SELL" and rate_trend < 0):
                confidence = max(self.low_confidence, confidence - 15)  # Reduce confidence if trend contradicts
                
        # Consider volatility
        if volatility > 0.005:
            explanation += f", high volatility in funding rates indicates unstable market conditions"
            confidence = max(self.low_confidence, confidence - 10)  # Reduce confidence in volatile conditions
            
        return signal, confidence, explanation
        
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for funding rate analysis.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data dictionary
        """
        if not self.data_fetcher:
            logger.warning("No data fetcher provided, cannot fetch market data")
            return {}
            
        try:
            # Format symbol for futures market if needed
            futures_symbol = f"{symbol}:USDT" if "/" in symbol else symbol
            
            # Fetch funding rate data
            funding_rates = self.data_fetcher.fetch_funding_rates(
                symbol=futures_symbol, 
                limit=self.lookback_periods
            )
            
            # Try to fetch current ticker if available
            ticker = {}
            try:
                ticker = self.data_fetcher.get_ticker(symbol)
            except:
                pass
                
            market_data = {
                "funding_rates": funding_rates,
                "ticker": ticker,
                "symbol": symbol
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}
            
    def _generate_mock_funding_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Generate mock funding rate data for testing purposes.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of mock funding rate records
        """
        # Start from 30 periods ago
        current_time = datetime.now()
        funding_data = []
        
        # Base funding rate on the symbol's sentiment
        if "BTC" in symbol.upper():
            base_rate = 0.0001  # Slightly positive
        elif "ETH" in symbol.upper():
            base_rate = -0.0002  # Slightly negative
        else:
            base_rate = 0  # Neutral
            
        # Generate funding rate data
        for i in range(self.lookback_periods):
            timestamp = int((current_time - timedelta(hours=8 * (self.lookback_periods - i))).timestamp() * 1000)
            
            # Add some randomness and trend
            if i < self.lookback_periods // 3:
                # First third: trend in one direction
                rate = base_rate + (0.0002 * i) + (np.random.random() - 0.5) * 0.0001
            elif i < 2 * self.lookback_periods // 3:
                # Middle third: consolidation
                rate = base_rate + (0.0002 * self.lookback_periods // 3) + (np.random.random() - 0.5) * 0.0001
            else:
                # Last third: reversal
                rate = base_rate + (0.0002 * self.lookback_periods // 3) - (0.0003 * (i - 2 * self.lookback_periods // 3)) + (np.random.random() - 0.5) * 0.0001
                
            funding_data.append({
                'symbol': symbol,
                'timestamp': timestamp,
                'rate': rate
            })
            
        logger.warning("Using mock funding rate data for testing")
        return funding_data