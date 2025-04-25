"""
Alpaca Query Agent for AutoGen

This module provides a query agent for AutoGen that retrieves market data from Alpaca.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta

# Import our Alpaca data agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.alpaca_data_agent import alpaca_data_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlpacaQueryAgent:
    """
    AlpacaQueryAgent class for retrieving market data from Alpaca API
    """
    
    def __init__(self):
        """Initialize AlpacaQueryAgent"""
        self.data_agent = alpaca_data_agent
        logger.info("AlpacaQueryAgent initialized")
    
    def register_functions(self) -> Dict[str, Callable]:
        """
        Register functions for AutoGen
        
        Returns:
            Dictionary of functions for AutoGen to register
        """
        return {
            "get_market_data": self.get_market_data,
            "get_latest_price": self.get_latest_price,
            "get_market_statistics": self.get_market_statistics,
            "get_connection_status": self.get_connection_status
        }
    
    def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 24,
                       days: Optional[int] = None, format_type: str = 'markdown') -> str:
        """
        Get market data for a specific symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSD')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of data points to retrieve
            days: Number of days to look back (alternative to limit)
            format_type: Output format ('text', 'json', 'markdown')
            
        Returns:
            Market data formatted as a string
        """
        try:
            # Query market data
            data = self.data_agent.query_market_data(
                symbol=symbol,
                interval=interval,
                limit=limit,
                days=days,
                format_type='dict'  # Always get as dict and format later
            )
            
            # Format the response for agent
            return self.data_agent.format_response_for_agent(data, format_type=format_type)
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return f"Error getting market data: {e}"
    
    def get_latest_price(self, symbol: str) -> str:
        """
        Get the latest price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSD')
            
        Returns:
            Latest price as a string
        """
        try:
            # Get latest price
            price = self.data_agent.get_latest_price(symbol)
            
            if price is not None:
                return f"Latest price for {symbol}: ${price:.2f}"
            else:
                return f"Failed to get latest price for {symbol}"
            
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return f"Error getting latest price: {e}"
    
    def get_market_statistics(self, symbol: str, interval: str = '1d',
                             days: int = 30, format_type: str = 'markdown') -> str:
        """
        Get market statistics for a specific symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSD')
            interval: Time interval (e.g., '1h', '4h', '1d')
            days: Number of days to look back
            format_type: Output format ('text', 'json', 'markdown')
            
        Returns:
            Market statistics formatted as a string
        """
        try:
            # Get market statistics
            stats = self.data_agent.get_market_statistics(
                symbol=symbol,
                interval=interval,
                days=days,
                format_type='dict'  # Always get as dict and format later
            )
            
            # Format the response for agent
            return self.data_agent.format_response_for_agent(stats, format_type=format_type)
            
        except Exception as e:
            logger.error(f"Error getting market statistics: {e}")
            return f"Error getting market statistics: {e}"
    
    def get_connection_status(self) -> str:
        """
        Get connection status to Alpaca API
        
        Returns:
            Connection status as a string
        """
        try:
            # Get connection status
            status = self.data_agent.get_connection_status()
            
            return f"Alpaca API connection status: {status['status']}"
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return f"Error getting connection status: {e}"

# Create singleton instance
alpaca_query_agent = AlpacaQueryAgent()

if __name__ == "__main__":
    # Test the AlpacaQueryAgent
    agent = AlpacaQueryAgent()
    
    # Check connection status
    status = agent.get_connection_status()
    print(status)
    
    # Test getting market data
    symbol = "BTCUSD"
    data = agent.get_market_data(symbol, interval="1h", limit=5, format_type='markdown')
    print(f"\nMarket data for {symbol}:")
    print(data)
    
    # Test getting latest price
    price = agent.get_latest_price(symbol)
    print(f"\n{price}")
    
    # Test getting market statistics
    stats = agent.get_market_statistics(symbol, interval="1d", days=7, format_type='markdown')
    print(f"\nMarket statistics for {symbol}:")
    print(stats)