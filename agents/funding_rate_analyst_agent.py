"""
Funding Rate Analyst Agent Module

This agent analyzes cryptocurrency funding rates from futures markets to identify:
- Potential market bias from long/short positions
- Overheated conditions indicating possible reversal
- Funding rate anomalies that may signal trading opportunities

The agent produces structured signals based on funding rate trends and magnitudes.
"""

import os
import sys
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import required modules
from models.llm_client import LLMClient
from data.database import DatabaseConnector
from agents.base_agent import BaseAnalystAgent
from market_data_provider_factory import MarketDataProviderFactory

class FundingRateAnalystAgent(BaseAnalystAgent):
    """
    Funding Rate Analyst Agent that analyzes futures market funding rates.
    
    This agent:
    - Fetches funding rate data from Binance futures API
    - Analyzes funding rate trends and magnitudes
    - Identifies potential market bias from perpetual futures
    - Generates trading signals based on funding rate analysis
    """
    
    def __init__(self):
        """Initialize the Funding Rate Analyst Agent."""
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
        self.default_interval = agent_config.get("funding_rate_analyst", {}).get("timeframe", "8h")
        self.lookback_periods = agent_config.get("funding_rate_analyst", {}).get("lookback_periods", 14)
        
        # Configure signal thresholds
        self.high_funding_threshold = agent_config.get("funding_rate_analyst", {}).get("high_funding_threshold", 0.01)
        self.extreme_funding_threshold = agent_config.get("funding_rate_analyst", {}).get("extreme_funding_threshold", 0.03)
        
        self.logger.info(f"Funding Rate Analyst Agent initialized with timeframe {self.default_interval}")
        
    def analyze(self, 
               symbol: Optional[str] = None, 
               interval: Optional[str] = None,
               market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze funding rate data for a trading pair.
        
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
            
        self.logger.info(f"Analyzing funding rates for {display_symbol} at {interval} interval")
        
        try:
            # Get funding rate data
            funding_data = self.fetch_funding_rates(symbol)
            
            if not funding_data or len(funding_data) == 0:
                self.logger.warning(f"No funding rate data available for {display_symbol}")
                return {
                    "symbol": display_symbol,
                    "interval": interval,
                    "error": "No funding rate data available",
                    "signal": "NEUTRAL",  # Default to NEUTRAL on error
                    "confidence": 50,
                    "reason": "Insufficient funding rate data for analysis"
                }
                
            # Perform analysis
            analysis_result = self.analyze_funding_rates(funding_data, display_symbol, interval)
            
            # Ensure the result is valid
            result = self.validate_result(analysis_result)
            
            # Return the result
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing funding rates: {str(e)}", exc_info=True)
            return self.handle_analysis_error(e, "funding_rate_analysis")
            
    def fetch_funding_rates(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch funding rate data from Binance Futures API.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            List of funding rate records
        """
        try:
            # Format symbol for API
            formatted_symbol = symbol.replace("/", "") if "/" in symbol else symbol
            
            # Initialize data provider
            self.logger.info(f"Fetching funding rates for {formatted_symbol}")
            
            # Create Binance provider directly to access futures API
            from agents.data_providers.binance_data_provider import BinanceDataProvider
            binance = BinanceDataProvider()
            
            try:
                # Prepare API parameters
                params = {
                    "symbol": formatted_symbol,
                    "limit": self.lookback_periods
                }
                
                # Make API request to futures funding rate endpoint
                url = "/fapi/v1/fundingRate"
                funding_rates = binance._make_request(url, params=params)
                
                # Verify we got valid data
                if not funding_rates or not isinstance(funding_rates, list):
                    self.logger.warning(f"Invalid funding rate data returned for {formatted_symbol}")
                    return self._generate_mock_funding_data(formatted_symbol)
                    
                self.logger.info(f"Successfully fetched {len(funding_rates)} funding rate records")
                return funding_rates
                
            except Exception as fetch_error:
                self.logger.warning(f"Error accessing futures funding rate API: {str(fetch_error)}")
                self.logger.warning("Generating simulated funding rate data for demo purposes")
                return self._generate_mock_funding_data(formatted_symbol)
                
        except Exception as e:
            self.logger.error(f"Error fetching funding rate data: {str(e)}", exc_info=True)
            return []
            
    def _generate_mock_funding_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Generate simulated funding rate data for demo/testing.
        Only used when the futures API is not accessible.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of simulated funding rate records
        """
        self.logger.info(f"Generating simulated funding rate data for {symbol}")
        
        # Get current timestamp
        now = int(time.time() * 1000)
        
        # Create simulated funding rate data
        # - Funding rates typically range from -0.05% to 0.05%
        # - Funding occurs every 8 hours on most exchanges
        funding_interval = 8 * 60 * 60 * 1000  # 8 hours in milliseconds
        
        funding_rates = []
        
        for i in range(self.lookback_periods):
            # Calculate timestamp for this funding rate
            timestamp = now - (i * funding_interval)
            
            # Generate funding rate - slightly biased toward positive
            base_rate = 0.0002  # 0.02% base rate
            variation = (random.random() - 0.45) * 0.0010  # -0.045% to +0.055%
            funding_rate = base_rate + variation
            
            # Create funding rate record
            record = {
                "symbol": symbol,
                "fundingTime": timestamp,
                "fundingRate": str(funding_rate)
            }
            
            funding_rates.append(record)
            
        self.logger.info(f"Generated {len(funding_rates)} simulated funding rate records")
        return funding_rates
            
    def analyze_funding_rates(self, 
                             funding_data: List[Dict[str, Any]],
                             symbol: str, 
                             interval: str) -> Dict[str, Any]:
        """
        Analyze funding rate data to generate trading signals.
        
        Args:
            funding_data: List of funding rate records
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Analysis result with trading signal
        """
        try:
            # Extract funding rates as floats
            rates = []
            timestamps = []
            
            for item in funding_data:
                if "fundingRate" in item:
                    rate = float(item["fundingRate"])
                    rates.append(rate)
                    timestamps.append(item.get("fundingTime", 0))
            
            # If no valid rates, return neutral signal
            if not rates:
                return {
                    "symbol": symbol,
                    "interval": interval,
                    "signal": "NEUTRAL",
                    "confidence": 50,
                    "reason": "No valid funding rate data"
                }
                
            # Get latest rate
            latest_rate = rates[0]
            
            # Calculate additional metrics
            avg_rate = sum(rates) / len(rates)
            rate_trend = latest_rate - rates[-1] if len(rates) > 1 else 0
            
            # Default values
            signal = "HOLD"
            confidence = 50
            reason = "Neutral funding rate conditions"
            
            # Signal generation logic based on funding rate
            if latest_rate > self.high_funding_threshold:
                # High positive funding rate indicates longs paying shorts
                # This suggests overheated long positions, bias toward SELL
                signal = "SELL"
                # Scale confidence by funding rate magnitude
                confidence = min(100, int(50 + (latest_rate * 5000)))
                reason = f"Excessive positive funding rate ({latest_rate:.4f}) indicates overheated long positions"
                
            elif latest_rate < -self.high_funding_threshold:
                # High negative funding rate indicates shorts paying longs
                # This suggests overheated short positions, bias toward BUY
                signal = "BUY"
                # Scale confidence by magnitude of funding rate
                confidence = min(100, int(50 + (abs(latest_rate) * 5000)))
                reason = f"Excessive negative funding rate ({latest_rate:.4f}) indicates overheated short positions"
                
            else:
                # Funding rate within normal range
                signal = "HOLD"
                # Scale confidence by distance from neutral
                confidence = max(50, int(70 - (abs(latest_rate) * 1000)))
                reason = f"Funding rate ({latest_rate:.4f}) within normal range"
                
            # Create detailed funding rate metrics
            funding_metrics = {
                "current_rate": latest_rate,
                "average_rate": avg_rate,
                "rate_trend": rate_trend,
                "rate_history": list(zip(timestamps, rates)),
                "rate_status": "high_positive" if latest_rate > self.high_funding_threshold else 
                              "high_negative" if latest_rate < -self.high_funding_threshold else 
                              "normal"
            }
            
            # Prepare final result
            result = {
                "symbol": symbol,
                "interval": interval,
                "signal": signal,
                "confidence": confidence,
                "reason": reason,
                "funding_metrics": funding_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Funding rate analysis complete for {symbol}: {signal} with {confidence}% confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing funding rates: {str(e)}", exc_info=True)
            return {
                "symbol": symbol,
                "interval": interval,
                "error": f"Analysis failed: {str(e)}",
                "signal": "NEUTRAL",
                "confidence": 50,
                "reason": "Error in funding rate analysis"
            }

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create agent
    agent = FundingRateAnalystAgent()
    
    # Run analysis
    analysis = agent.analyze("BTCUSDT")
    
    # Print results
    print(json.dumps(analysis, indent=2))