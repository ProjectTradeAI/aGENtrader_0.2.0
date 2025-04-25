#!/usr/bin/env python
"""
PositionSizerAgent for aGENtrader v2.1

This agent calculates appropriate position sizes for trades based on
confidence level, market volatility, or a combination of both factors.
"""

import logging
import math
import os
import statistics
from typing import Dict, Any, Optional, List
import yaml

# Setup logger
logger = logging.getLogger("aGENtrader.position_sizer")

class PositionSizerAgent:
    """
    Agent responsible for determining appropriate position sizes.
    
    Supports multiple sizing strategies:
    - Confidence-based: Position size determined by trading confidence
    - Volatility-based: Position size inversely proportional to volatility
    - Combined: Weighted combination of confidence and volatility
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize the position sizer agent.
        
        Args:
            config_path: Path to settings file
        """
        self.config = self._load_config(config_path)
        
        # Extract position sizing settings
        self.strategy = self.config.get("position_sizing", {}).get("strategy", "confidence")
        self.min_size = self.config.get("position_sizing", {}).get("min_size", 0.05)
        self.max_size = self.config.get("position_sizing", {}).get("max_size", 0.25)
        
        # Confidence mapping
        self.confidence_map = self.config.get("position_sizing", {}).get("confidence_map", {
            50: 0.05,
            60: 0.10,
            70: 0.15,
            80: 0.20,
            90: 0.25
        })
        
        # Sort confidence map by confidence level for interpolation
        self.confidence_levels = sorted(self.confidence_map.keys())
        
        # Volatility settings
        self.volatility_settings = self.config.get("position_sizing", {}).get("volatility", {
            "lookback_periods": 14,
            "risk_per_trade": 0.01,
            "volatility_multiplier": 2.0,
            "max_volatility": 0.05
        })
        
        # Combined strategy weights
        self.combined_weights = self.config.get("position_sizing", {}).get("combined_weights", {
            "confidence_weight": 0.7,
            "volatility_weight": 0.3
        })
        
        logger.info(f"PositionSizerAgent initialized with strategy: {self.strategy}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    return yaml.safe_load(file)
            else:
                logger.warning(f"Configuration file {config_path} not found. Using defaults.")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def calculate_position_size(
        self, 
        symbol: str, 
        confidence: float, 
        volatility: Optional[float] = None,
        price_data: Optional[List[Dict[str, float]]] = None
    ) -> float:
        """
        Calculate the appropriate position size based on the configured strategy.
        
        Args:
            symbol: Trading symbol
            confidence: Confidence level (0-100)
            volatility: Pre-calculated volatility (optional)
            price_data: Historical price data for volatility calculation (optional)
            
        Returns:
            Position size as a proportion of capital (0.01-1.0)
        """
        logger.debug(f"Calculating position size for {symbol} with confidence {confidence}")
        
        # Ensure confidence is within bounds
        confidence = max(0, min(100, confidence))
        
        # Calculate position size based on selected strategy
        if self.strategy == "confidence":
            position_size = self._confidence_based_size(confidence)
            calculation_note = f"confidence-based sizing: {confidence}% confidence"
        
        elif self.strategy == "volatility":
            # Calculate volatility if not provided
            if volatility is None and price_data is not None:
                volatility = self._calculate_volatility(price_data)
            
            # Default volatility if still None
            volatility = volatility if volatility is not None else 0.02  # 2% default
            
            position_size = self._volatility_based_size(volatility)
            calculation_note = f"volatility-based sizing: {volatility:.2%} volatility"
        
        elif self.strategy == "combined":
            # Calculate volatility if not provided
            if volatility is None and price_data is not None:
                volatility = self._calculate_volatility(price_data)
            
            # Default volatility if still None
            volatility = volatility if volatility is not None else 0.02  # 2% default
            
            confidence_size = self._confidence_based_size(confidence)
            volatility_size = self._volatility_based_size(volatility)
            
            # Weighted combination
            confidence_weight = self.combined_weights.get("confidence_weight", 0.7)
            volatility_weight = self.combined_weights.get("volatility_weight", 0.3)
            
            position_size = (confidence_size * confidence_weight) + (volatility_size * volatility_weight)
            calculation_note = f"combined sizing: {confidence}% confidence, {volatility:.2%} volatility"
        
        else:
            # Default to confidence-based if unknown strategy
            position_size = self._confidence_based_size(confidence)
            calculation_note = f"default confidence-based sizing: {confidence}% confidence"
        
        # Ensure position size is within bounds
        position_size = max(self.min_size, min(self.max_size, position_size))
        
        logger.info(
            f"Calculated position size for {symbol}: {position_size:.2%} "
            f"using {calculation_note}"
        )
        
        return position_size
    
    def _confidence_based_size(self, confidence: float) -> float:
        """
        Calculate position size based on confidence level using the confidence map.
        Uses linear interpolation between mapped confidence levels.
        
        Args:
            confidence: Confidence level (0-100)
            
        Returns:
            Position size as a proportion of capital
        """
        # If confidence is at or below the lowest mapped confidence level
        if confidence <= self.confidence_levels[0]:
            return self.confidence_map[self.confidence_levels[0]]
        
        # If confidence is at or above the highest mapped confidence level
        if confidence >= self.confidence_levels[-1]:
            return self.confidence_map[self.confidence_levels[-1]]
        
        # Find the two confidence levels to interpolate between
        for i in range(len(self.confidence_levels) - 1):
            lower_conf = self.confidence_levels[i]
            upper_conf = self.confidence_levels[i + 1]
            
            if lower_conf <= confidence < upper_conf:
                lower_size = self.confidence_map[lower_conf]
                upper_size = self.confidence_map[upper_conf]
                
                # Linear interpolation
                return lower_size + (confidence - lower_conf) * (upper_size - lower_size) / (upper_conf - lower_conf)
        
        # Should never reach here, but return min_size as fallback
        return self.min_size
    
    def _volatility_based_size(self, volatility: float) -> float:
        """
        Calculate position size based on market volatility.
        Higher volatility results in smaller position sizes.
        
        Args:
            volatility: Market volatility (e.g., 0.02 for 2%)
            
        Returns:
            Position size as a proportion of capital
        """
        # Ensure volatility is positive
        volatility = max(0.001, volatility)  # Minimum 0.1% volatility to avoid division by zero
        
        # Cap volatility at max_volatility
        volatility = min(volatility, self.volatility_settings.get("max_volatility", 0.05))
        
        # Inverse relationship: higher volatility → lower position size
        risk_per_trade = self.volatility_settings.get("risk_per_trade", 0.01)  # 1% risk per trade
        multiplier = self.volatility_settings.get("volatility_multiplier", 2.0)
        
        # Formula: risk_per_trade / (volatility * multiplier)
        position_size = risk_per_trade / (volatility * multiplier)
        
        return position_size
    
    def _calculate_volatility(self, price_data: List[Dict[str, float]]) -> float:
        """
        Calculate market volatility from historical price data.
        Uses standard deviation of log returns.
        
        Args:
            price_data: List of price dictionaries with 'close' key
            
        Returns:
            Volatility as a decimal (e.g., 0.02 for 2%)
        """
        lookback = self.volatility_settings.get("lookback_periods", 14)
        
        # Ensure we have enough data
        if len(price_data) < lookback + 1:
            logger.warning(f"Insufficient price data for volatility calculation. Need {lookback + 1}, got {len(price_data)}")
            return 0.02  # Default 2% volatility
        
        try:
            # Calculate daily log returns
            closes = [candle["close"] for candle in price_data[-lookback-1:]]
            log_returns = [math.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
            
            # Calculate standard deviation of log returns
            volatility = statistics.stdev(log_returns)
            
            # Convert to annualized volatility if needed (for daily data: * sqrt(252))
            # For hourly data: * sqrt(24 * 365)
            # Here we're assuming the volatility is already properly scaled for the timeframe
            
            return volatility
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.02  # Default 2% volatility