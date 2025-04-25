"""
Alpaca Data Agent

This module provides an interface for agents to access market data from Alpaca.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Import our Alpaca market data service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.alpaca_market_data import (
    get_historical_data,
    get_latest_price,
    get_market_statistics,
    test_connection
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlpacaDataAgent:
    """
    AlpacaDataAgent class that provides an interface for agents to access market data
    """
    
    def __init__(self):
        """Initialize the AlpacaDataAgent"""
        self.status = "initialized"
        
        # Test the connection to Alpaca API
        self.connected = test_connection()
        if self.connected:
            logger.info("Successfully connected to Alpaca API")
            self.status = "connected"
        else:
            logger.warning("Failed to connect to Alpaca API")
            self.status = "disconnected"
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the connection status
        
        Returns:
            Dictionary with connection status
        """
        return {
            "status": self.status,
            "connected": self.connected,
            "timestamp": datetime.now().isoformat()
        }
    
    def query_market_data(self, symbol: str, interval: str = '1h', limit: int = 24,
                         days: Optional[int] = None, format_type: str = 'json') -> Union[str, Dict, List]:
        """
        Query market data for a specific symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSD')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of data points to retrieve
            days: Number of days to look back (alternative to limit)
            format_type: Output format ('json', 'dict', 'csv')
            
        Returns:
            Market data in the specified format
        """
        try:
            # Check connection status
            if not self.connected:
                logger.warning("Not connected to Alpaca API")
                if format_type == 'json':
                    return json.dumps({"error": "Not connected to Alpaca API"})
                else:
                    return {"error": "Not connected to Alpaca API"}
            
            # Calculate start and end dates if days is specified
            start_date = None
            end_date = None
            
            if days is not None:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get historical data
            result = get_historical_data(
                symbol=symbol,
                interval=interval,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                format_type=format_type
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error querying market data: {e}")
            if format_type == 'json':
                return json.dumps({"error": str(e)})
            else:
                return {"error": str(e)}
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSD')
            
        Returns:
            Latest price or None if not available
        """
        try:
            # Check connection status
            if not self.connected:
                logger.warning("Not connected to Alpaca API")
                return None
            
            return get_latest_price(symbol)
            
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None
    
    def get_market_statistics(self, symbol: str, interval: str = '1d',
                             days: int = 30, format_type: str = 'json') -> Union[str, Dict]:
        """
        Get market statistics for a specific symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSD')
            interval: Time interval (e.g., '1h', '4h', '1d')
            days: Number of days to look back
            format_type: Output format ('json', 'dict')
            
        Returns:
            Market statistics in the specified format
        """
        try:
            # Check connection status
            if not self.connected:
                logger.warning("Not connected to Alpaca API")
                if format_type == 'json':
                    return json.dumps({"error": "Not connected to Alpaca API"})
                else:
                    return {"error": "Not connected to Alpaca API"}
            
            return get_market_statistics(
                symbol=symbol,
                interval=interval,
                days=days,
                format_type=format_type
            )
            
        except Exception as e:
            logger.error(f"Error getting market statistics: {e}")
            if format_type == 'json':
                return json.dumps({"error": str(e)})
            else:
                return {"error": str(e)}
    
    def format_response_for_agent(self, data: Any, format_type: str = 'text') -> str:
        """
        Format the response in a way that's easy for agents to understand
        
        Args:
            data: Data to format
            format_type: Output format ('text', 'json', 'markdown')
            
        Returns:
            Formatted response as a string
        """
        if format_type == 'json':
            if isinstance(data, str):
                return data  # Already JSON string
            else:
                return json.dumps(data, indent=2)
        
        elif format_type == 'markdown':
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return f"```\n{data}\n```"
            
            if isinstance(data, list):
                if not data:
                    return "*No data available*"
                
                # Create markdown table
                headers = data[0].keys()
                markdown = "| " + " | ".join(headers) + " |\n"
                markdown += "| " + " | ".join(["---" for _ in headers]) + " |\n"
                
                for item in data:
                    row = "| " + " | ".join([str(item.get(h, "")) for h in headers]) + " |"
                    markdown += row + "\n"
                
                return markdown
            
            elif isinstance(data, dict):
                if not data:
                    return "*No data available*"
                
                # Create markdown list
                markdown = ""
                for key, value in data.items():
                    markdown += f"**{key}**: {value}\n"
                
                return markdown
            
            else:
                return f"```\n{data}\n```"
        
        else:  # text format
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return data
            
            if isinstance(data, list):
                if not data:
                    return "No data available"
                
                text = ""
                for item in data:
                    text += "\n".join([f"{k}: {v}" for k, v in item.items()])
                    text += "\n---\n"
                
                return text
            
            elif isinstance(data, dict):
                if not data:
                    return "No data available"
                
                return "\n".join([f"{k}: {v}" for k, v in data.items()])
            
            else:
                return str(data)

# Create singleton instance
alpaca_data_agent = AlpacaDataAgent()

if __name__ == "__main__":
    # Test the AlpacaDataAgent
    agent = AlpacaDataAgent()
    
    # Check connection status
    status = agent.get_connection_status()
    print(f"Connection status: {status['status']}")
    
    if agent.connected:
        # Test querying market data
        symbol = "BTCUSD"
        data = agent.query_market_data(symbol, interval="1h", limit=5, format_type='dict')
        print(f"\nMarket data for {symbol}:")
        print(agent.format_response_for_agent(data, format_type='text'))
        
        # Test getting latest price
        price = agent.get_latest_price(symbol)
        print(f"\nLatest price for {symbol}: ${price:.2f}")
        
        # Test getting market statistics
        stats = agent.get_market_statistics(symbol, interval="1d", days=7, format_type='dict')
        print(f"\nMarket statistics for {symbol}:")
        print(agent.format_response_for_agent(stats, format_type='text'))
    else:
        print("Cannot run tests because not connected to Alpaca API")
        print("Please check your API key and secret in the environment variables:")