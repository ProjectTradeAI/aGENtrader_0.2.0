"""
aGENtrader v0.2.2 - MarketContext Object

This module defines a standard MarketContext class for passing consistent 
market data between agents during decision cycles.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class MarketContext:
    """
    A centralized container for market data that's propagated to all agents
    in the decision-making process to ensure data consistency.
    """
    
    def __init__(
        self, 
        symbol: str, 
        timestamp: Optional[datetime] = None,
        price: float = 0.0,
        day_change: float = 0.0,
        hour_change: float = 0.0,
        volume: float = 0.0,
        volume_change: float = 0.0,
        volatility: float = 0.0,
        market_phase: str = "unknown",
        ohlcv: Optional[List[Dict[str, Any]]] = None,
        order_book: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the MarketContext with the provided market data.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            timestamp: Current timestamp (if None, current time will be used)
            price: Current price
            day_change: 24-hour price change percentage
            hour_change: 1-hour price change percentage
            volume: Trading volume (in quote currency)
            volume_change: 24-hour volume change percentage
            volatility: Current volatility percentage
            market_phase: Current market phase description ("accumulation", "bull", "distribution", "bear", etc.)
            ohlcv: Optional list of OHLCV candles
            order_book: Optional order book snapshot
        """
        self.symbol = symbol 
        self.timestamp = timestamp or datetime.now()
        self.price = float(price) if price else 0.0
        self.day_change = float(day_change)  # 24h percent change
        self.hour_change = float(hour_change)  # 1h percent change
        self.volume = float(volume) if volume else 0.0
        self.volume_change = float(volume_change)
        self.volatility = float(volatility) 
        self.market_phase = market_phase
        self.ohlcv = ohlcv or []
        self.order_book = order_book or {"bids": [], "asks": []}
        
        # Add conventional aliases for change percentages
        self.price_change_24h = self.day_change
        self.price_change_1h = self.hour_change
        self.volume_change_24h = self.volume_change
        
        # Store initialization time
        self._init_time = datetime.now()
        
        logger.debug(f"MarketContext initialized for {symbol} at {self.timestamp}")
        
    def as_dict(self) -> Dict[str, Any]:
        """
        Convert MarketContext to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the MarketContext
        """
        # Convert timestamp to ISO format for serialization
        timestamp_str = self.timestamp.isoformat() if self.timestamp else None
        
        return {
            "symbol": self.symbol,
            "timestamp": timestamp_str,
            "price": self.price,
            "day_change": self.day_change,
            "hour_change": self.hour_change,
            "price_change_24h": self.day_change,  # Alias
            "price_change_1h": self.hour_change,  # Alias
            "volume": self.volume,
            "volume_change": self.volume_change,
            "volume_change_24h": self.volume_change,  # Alias
            "volatility": self.volatility,
            "market_phase": self.market_phase,
            # Don't include large data structures by default
            # "ohlcv": self.ohlcv,
            # "order_book": self.order_book
        }
        
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update MarketContext from a dictionary.
        
        Args:
            data: Dictionary containing market data
        """
        # Only update if new data is available
        if not data:
            return
            
        # Update scalar fields if present
        if "price" in data and data["price"]:
            self.price = float(data["price"])
            
        # Update price changes with fallbacks
        for field, attr in [
            ("day_change", "day_change"),
            ("price_change_24h", "day_change"),
            ("24h_change", "day_change")
        ]:
            if field in data and data[field] is not None:
                setattr(self, attr, float(data[field]))
                
        for field, attr in [
            ("hour_change", "hour_change"),
            ("price_change_1h", "hour_change"),
            ("1h_change", "hour_change")
        ]:
            if field in data and data[field] is not None:
                setattr(self, attr, float(data[field]))
                
        # Update volume data
        if "volume" in data and data["volume"]:
            self.volume = float(data["volume"])
            
        for field, attr in [
            ("volume_change", "volume_change"),
            ("volume_change_24h", "volume_change")
        ]:
            if field in data and data[field] is not None:
                setattr(self, attr, float(data[field]))
                
        # Update volatility
        if "volatility" in data and data["volatility"] is not None:
            self.volatility = float(data["volatility"])
            
        # Update market phase
        if "market_phase" in data and data["market_phase"]:
            self.market_phase = data["market_phase"]
            
        # Update timestamp if provided
        if "timestamp" in data and data["timestamp"]:
            if isinstance(data["timestamp"], datetime):
                self.timestamp = data["timestamp"]
            elif isinstance(data["timestamp"], str):
                try:
                    self.timestamp = datetime.fromisoformat(data["timestamp"])
                except:
                    pass
                    
        # Update large data structures if needed
        if "ohlcv" in data and data["ohlcv"]:
            self.ohlcv = data["ohlcv"]
            
        if "order_book" in data and data["order_book"]:
            self.order_book = data["order_book"]
            
        # Look for timeframe-specific OHLCV data
        if "ohlcv_1h" in data and data["ohlcv_1h"]:
            # Store in a separate attribute
            self.ohlcv_1h = data["ohlcv_1h"]
                
        if "ohlcv_24h" in data and data["ohlcv_24h"]:
            # Store 24h data separately
            self.ohlcv_24h = data["ohlcv_24h"]
            
        # Update aliases
        self.price_change_24h = self.day_change
        self.price_change_1h = self.hour_change
        self.volume_change_24h = self.volume_change
            
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketContext':
        """
        Create a MarketContext from a dictionary.
        
        Args:
            data: Dictionary containing market data
            
        Returns:
            MarketContext instance
        """
        # Extract required symbol
        symbol = data.get("symbol", "BTC/USDT")
        
        # Extract timestamp
        timestamp = None
        if "timestamp" in data:
            if isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
            elif isinstance(data["timestamp"], str):
                try:
                    timestamp = datetime.fromisoformat(data["timestamp"])
                except:
                    pass
                    
        # Create instance with extracted data
        context = cls(
            symbol=symbol,
            timestamp=timestamp,
            price=data.get("price", 0.0),
            day_change=data.get("day_change", data.get("price_change_24h", 0.0)),
            hour_change=data.get("hour_change", data.get("price_change_1h", 0.0)),
            volume=data.get("volume", 0.0),
            volume_change=data.get("volume_change", data.get("volume_change_24h", 0.0)),
            volatility=data.get("volatility", 0.0),
            market_phase=data.get("market_phase", "unknown"),
            ohlcv=data.get("ohlcv", []),
            order_book=data.get("order_book", {"bids": [], "asks": []})
        )
        
        return context
        
    def enrich_with_ohlcv(self, ohlcv_1h=None, ohlcv_24h=None) -> None:
        """
        Add OHLCV data to the market context.
        
        Args:
            ohlcv_1h: Optional list of 1-hour OHLCV candles
            ohlcv_24h: Optional list of 24-hour OHLCV candles
        """
        # Update ohlcv_1h if provided
        if ohlcv_1h and isinstance(ohlcv_1h, list):
            self.ohlcv_1h = ohlcv_1h
            
            # If main ohlcv is empty, use this data
            if not self.ohlcv:
                self.ohlcv = ohlcv_1h
                
            # Try to extract price changes from OHLCV if not available
            if self.hour_change == 0.0 and len(ohlcv_1h) >= 2:
                try:
                    first_candle = ohlcv_1h[0]
                    last_candle = ohlcv_1h[-1]
                    
                    if 'close' in first_candle and 'close' in last_candle:
                        first_price = float(first_candle['close'])
                        last_price = float(last_candle['close'])
                        
                        if first_price > 0:
                            self.hour_change = ((last_price - first_price) / first_price) * 100
                            self.price_change_1h = self.hour_change
                except Exception as e:
                    logger.warning(f"Error calculating 1h price change from OHLCV: {e}")
        
        # Update ohlcv_24h if provided
        if ohlcv_24h and isinstance(ohlcv_24h, list):
            self.ohlcv_24h = ohlcv_24h
            
            # If main ohlcv is empty, use this data
            if not self.ohlcv:
                self.ohlcv = ohlcv_24h
                
            # Try to extract price changes from OHLCV if not available
            if self.day_change == 0.0 and len(ohlcv_24h) >= 2:
                try:
                    first_candle = ohlcv_24h[0]
                    last_candle = ohlcv_24h[-1]
                    
                    if 'close' in first_candle and 'close' in last_candle:
                        first_price = float(first_candle['close'])
                        last_price = float(last_candle['close'])
                        
                        if first_price > 0:
                            self.day_change = ((last_price - first_price) / first_price) * 100
                            self.price_change_24h = self.day_change
                except Exception as e:
                    logger.warning(f"Error calculating 24h price change from OHLCV: {e}")
                    
    def determine_market_phase(self) -> str:
        """
        Determine the current market phase based on price and volume changes.
        Updates the market_phase attribute.
        
        Returns:
            String description of the market phase
        """
        price_change = self.day_change
        volume_change = self.volume_change
        
        if price_change > 5 and volume_change > 10:
            market_phase = "bull_expansion"  # Strong uptrend with increasing volume
        elif price_change > 2 and -5 <= volume_change <= 5:
            market_phase = "bull_continuation"  # Ongoing uptrend with stable volume
        elif price_change > 0 and volume_change < -10:
            market_phase = "bull_exhaustion"  # Weakening uptrend with decreasing volume
        elif price_change < -5 and volume_change > 10:
            market_phase = "bear_expansion"  # Strong downtrend with increasing volume
        elif price_change < -2 and -5 <= volume_change <= 5:
            market_phase = "bear_continuation"  # Ongoing downtrend with stable volume
        elif price_change < 0 and volume_change < -10:
            market_phase = "bear_exhaustion"  # Weakening downtrend with decreasing volume
        elif -2 <= price_change <= 2 and volume_change < -15:
            market_phase = "accumulation"  # Sideways price with very low volume
        elif -2 <= price_change <= 2 and volume_change > 15:
            market_phase = "distribution"  # Sideways price with very high volume
        elif -2 <= price_change <= 2:
            market_phase = "consolidation"  # Sideways price with moderate volume
        else:
            market_phase = "transition"  # Unclear phase
            
        # Update the market_phase attribute
        self.market_phase = market_phase
        
        return market_phase

    def __str__(self) -> str:
        """
        Get a string representation of the MarketContext.
        
        Returns:
            String representation
        """
        return (f"MarketContext({self.symbol}, ${self.price:.2f}, "
                f"{self.day_change:+.2f}% 24h, {self.hour_change:+.2f}% 1h, "
                f"vol: {self.volume:.2f}, phase: {self.market_phase})")