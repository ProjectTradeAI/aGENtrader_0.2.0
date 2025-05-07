"""
aGENtrader v0.2.2 - Market Context Helper Utilities

This module provides helper functions for working with the MarketContext class
to enable consistent market data access across all analyst agents.
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger("market_context_helper")

def extract_market_context(market_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extract the MarketContext from market_data dictionary if it exists.
    
    Args:
        market_data: Dictionary containing market data
        
    Returns:
        Market context dictionary if it exists, None otherwise
    """
    if not market_data or not isinstance(market_data, dict):
        return None
        
    if "market_context" in market_data and isinstance(market_data["market_context"], dict):
        return market_data["market_context"]
        
    return None

def get_symbol_from_context(market_data: Optional[Dict[str, Any]], default_symbol: str = "BTC/USDT") -> str:
    """
    Get the symbol from market context or the market_data.
    
    Args:
        market_data: Dictionary containing market data
        default_symbol: Default symbol to use if not found
        
    Returns:
        Trading symbol string
    """
    if not market_data or not isinstance(market_data, dict):
        return default_symbol
    
    # Try to get from market_context first
    market_context = extract_market_context(market_data)
    if market_context and "symbol" in market_context:
        return market_context["symbol"]
    
    # Try to get from market_data directly
    if "symbol" in market_data:
        return market_data["symbol"]
    
    return default_symbol

def get_price_from_context(market_data: Optional[Dict[str, Any]], default_price: float = 0.0) -> float:
    """
    Get the current price from market context or the market_data.
    
    Args:
        market_data: Dictionary containing market data
        default_price: Default price to use if not found
        
    Returns:
        Current price as float
    """
    if not market_data or not isinstance(market_data, dict):
        return default_price
    
    # Try to get from market_context first
    market_context = extract_market_context(market_data)
    if market_context:
        if "price" in market_context and market_context["price"] > 0:
            return market_context["price"]
    
    # Try standard price fields in market_data
    for field in ["price", "close", "last"]:
        if field in market_data and isinstance(market_data[field], (int, float)) and market_data[field] > 0:
            return market_data[field]
    
    # Try in ticker if available
    if "ticker" in market_data and isinstance(market_data["ticker"], dict):
        ticker = market_data["ticker"]
        for field in ["price", "close", "last"]:
            if field in ticker and isinstance(ticker[field], (int, float)) and ticker[field] > 0:
                return ticker[field]
    
    return default_price

def get_timestamp_from_context(market_data: Optional[Dict[str, Any]]) -> datetime:
    """
    Get the timestamp from market context or the market_data.
    
    Args:
        market_data: Dictionary containing market data
        
    Returns:
        Timestamp as datetime
    """
    if not market_data or not isinstance(market_data, dict):
        return datetime.now()
    
    # Try to get from market_context first
    market_context = extract_market_context(market_data)
    if market_context and "timestamp" in market_context:
        timestamp = market_context["timestamp"]
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp)
            except:
                pass
    
    # Try to get from market_data directly
    if "timestamp" in market_data:
        timestamp = market_data["timestamp"]
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp)
            except:
                pass
    
    return datetime.now()

def get_market_phase_from_context(market_data: Optional[Dict[str, Any]], default_phase: str = "unknown") -> str:
    """
    Get the market phase from market context.
    
    Args:
        market_data: Dictionary containing market data
        default_phase: Default phase to use if not found
        
    Returns:
        Market phase string
    """
    if not market_data or not isinstance(market_data, dict):
        return default_phase
    
    # Try to get from market_context first
    market_context = extract_market_context(market_data)
    if market_context and "market_phase" in market_context:
        return market_context["market_phase"]
    
    return default_phase

def get_price_change_from_context(
    market_data: Optional[Dict[str, Any]], 
    period: str = "24h",
    default_change: float = 0.0
) -> float:
    """
    Get the price change for a specific period from market context.
    
    Args:
        market_data: Dictionary containing market data
        period: Period for price change (1h, 24h)
        default_change: Default change to use if not found
        
    Returns:
        Price change as percentage (float)
    """
    if not market_data or not isinstance(market_data, dict):
        return default_change
    
    # Try to get from market_context first
    market_context = extract_market_context(market_data)
    if market_context:
        # Check for standard naming
        if f"{period}_change" in market_context:
            return market_context[f"{period}_change"]
            
        # Check for alternate naming
        if period == "24h" and "day_change" in market_context:
            return market_context["day_change"]
        elif period == "1h" and "hour_change" in market_context:
            return market_context["hour_change"]
    
    # Try from market_data directly
    field_options = [
        f"{period}_change",
        f"price_change_{period}",
        f"change_{period}"
    ]
    
    for field in field_options:
        if field in market_data:
            return market_data[field]
    
    return default_change

def enrich_context_for_agent(
    market_data: Optional[Dict[str, Any]],
    agent_type: str,
    default_symbol: str = "BTC/USDT"
) -> Dict[str, Any]:
    """
    Enrich market data with additional agent-specific context information.
    
    Args:
        market_data: Dictionary containing market data
        agent_type: Type of agent ("sentiment", "technical", "liquidity", etc.)
        default_symbol: Default symbol to use if not found
        
    Returns:
        Enriched market_data dictionary with agent-specific context
    """
    # Create a copy to avoid modifying the original
    if market_data and isinstance(market_data, dict):
        enriched_data = market_data.copy()
    else:
        enriched_data = {}
    
    # Get base information
    symbol = get_symbol_from_context(enriched_data, default_symbol)
    current_price = get_price_from_context(enriched_data)
    timestamp = get_timestamp_from_context(enriched_data)
    
    # Add base information if missing
    if "symbol" not in enriched_data:
        enriched_data["symbol"] = symbol
    if "price" not in enriched_data and current_price > 0:
        enriched_data["price"] = current_price
    if "timestamp" not in enriched_data:
        enriched_data["timestamp"] = timestamp
    
    # Add agent-specific enrichments
    if agent_type == "sentiment":
        # Add asset base information
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol
        enriched_data["base_asset"] = base_asset
        
        # Add sentiment-specific context
        price_change_24h = get_price_change_from_context(enriched_data, period="24h")
        price_change_1h = get_price_change_from_context(enriched_data, period="1h")
        market_phase = get_market_phase_from_context(enriched_data)
        
        # Format sentiment-friendly descriptions
        price_movement = f"{'up' if price_change_24h >= 0 else 'down'} {abs(price_change_24h):.2f}% in 24h"
        recent_movement = f"{'up' if price_change_1h >= 0 else 'down'} {abs(price_change_1h):.2f}% in 1h"
        
        # Add to enriched data
        enriched_data["price_movement_description"] = price_movement
        enriched_data["recent_movement_description"] = recent_movement
        enriched_data["market_phase"] = market_phase
        
    elif agent_type == "liquidity":
        # Add liquidity-specific context
        if "order_book" not in enriched_data and "orderbook" in enriched_data:
            enriched_data["order_book"] = enriched_data["orderbook"]
            
    elif agent_type == "technical":
        # Add technical-specific context
        if "indicators" not in enriched_data:
            enriched_data["indicators"] = {
                "rsi": None,
                "macd": None,
                "bollinger_bands": None
            }
    
    return enriched_data