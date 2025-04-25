"""
Standalone Database Test with AutoGen Integration

This module provides a standalone test for database integration with AutoGen
without requiring imports from the agents module, avoiding import errors.
"""

import os
import sys
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

# Standalone database access functions
class StandaloneDBManager:
    """
    Standalone Database Manager that doesn't rely on agent imports
    """
    def __init__(self):
        """Initialize database connection from environment variables"""
        self.conn = None
        try:
            # Get database connection string from environment
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL environment variable not found")
                return
            
            # Connect to the database
            self.conn = psycopg2.connect(db_url)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            self.conn = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.conn is not None
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available trading symbols"""
        if not self.is_connected():
            return []
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT symbol FROM market_data
                    ORDER BY symbol
                """)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return []
    
    def get_available_intervals(self, symbol: Optional[str] = None) -> List[str]:
        """Get list of available time intervals"""
        if not self.is_connected():
            return []
        
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT DISTINCT interval FROM market_data
                """
                if symbol:
                    query += " WHERE symbol = %s"
                    cur.execute(query, (symbol,))
                else:
                    cur.execute(query)
                    
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting intervals: {str(e)}")
            return []
    
    def get_latest_price(self, symbol: str) -> float:
        """Get the latest price for a symbol"""
        if not self.is_connected():
            return 0.0
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT close, timestamp
                    FROM market_data
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (symbol,))
                result = cur.fetchone()
                if result:
                    return float(result[0])
                return 0.0
        except Exception as e:
            logger.error(f"Error getting latest price: {str(e)}")
            return 0.0
    
    def get_market_data(self, symbol: str, interval: str = '1h', 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get market data for a symbol and interval
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            start_time: Start time for data retrieval
            end_time: End time for data retrieval
            limit: Maximum number of records to retrieve
            
        Returns:
            List of market data points
        """
        if not self.is_connected():
            return []
        
        try:
            # Build the query
            query = """
                SELECT open, high, low, close, volume, timestamp
                FROM market_data
                WHERE symbol = %s AND interval = %s
            """
            params = [symbol, interval]
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= %s"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            # Execute the query
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                results = []
                
                for row in cur.fetchall():
                    result_dict = {}
                    for i, col in enumerate(columns):
                        if col == 'timestamp':
                            result_dict[col] = row[i].isoformat()
                        else:
                            result_dict[col] = float(row[i])
                    results.append(result_dict)
                
                return results
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return []
    
    def calculate_volatility(self, symbol: str, interval: str = '1d', days: int = 14) -> float:
        """
        Calculate price volatility for a symbol
        
        Args:
            symbol: Trading pair symbol
            interval: Time interval
            days: Number of days to calculate volatility for
            
        Returns:
            Volatility as a percentage
        """
        if not self.is_connected():
            return 0.0
        
        try:
            # Get market data for the volatility calculation
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            data = self.get_market_data(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=days
            )
            
            if not data or len(data) < 2:
                return 0.0
            
            # Calculate daily returns
            closes = [d['close'] for d in data]
            returns = []
            
            for i in range(1, len(closes)):
                daily_return = (closes[i-1] / closes[i]) - 1
                returns.append(daily_return)
            
            # Calculate standard deviation of returns (volatility)
            if not returns:
                return 0.0
                
            mean_return = sum(returns) / len(returns)
            squared_diff = [(r - mean_return) ** 2 for r in returns]
            variance = sum(squared_diff) / len(returns)
            std_dev = variance ** 0.5
            
            # Convert to percentage
            return std_dev * 100
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return 0.0

# Initialize standalone database manager
db_manager = StandaloneDBManager()

# Function to get Bitcoin price
def get_bitcoin_price() -> str:
    """
    Get the latest Bitcoin price information from the database.
    """
    try:
        if not db_manager.is_connected():
            return "Database not available - cannot retrieve current Bitcoin price."
        
        # Get the latest price from the database
        symbol = "BTCUSDT"
        latest_price = db_manager.get_latest_price(symbol)
        
        # Get market data for the last 24 hours
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        market_data = db_manager.get_market_data(
            symbol=symbol,
            interval="1h",
            start_time=yesterday,
            limit=24
        )
        
        result = f"## Bitcoin Price Information\n\n"
        result += f"**Symbol**: {symbol}\n"
        result += f"**Current Price**: ${latest_price:.2f}\n"
        
        # Calculate 24h change if we have enough data
        if market_data and len(market_data) > 0:
            earliest_close = market_data[-1].get('close', 0)
            if earliest_close > 0:
                change_24h = (latest_price - earliest_close) / earliest_close * 100
                result += f"**24h Change**: {change_24h:.2f}%\n"
        
        result += f"**Timestamp**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return result
    
    except Exception as e:
        logger.error(f"Error in get_bitcoin_price: {str(e)}")
        return f"Error retrieving Bitcoin price: {str(e)}"

# Function that gets technical indicators
def get_technical_indicators(symbol: str = "BTCUSDT") -> str:
    """
    Get technical indicators for a cryptocurrency.
    """
    try:
        if not db_manager.is_connected():
            return "Database not available - cannot retrieve technical indicators."
        
        # Get technical indicator data from the database
        result = f"## Technical Indicators for {symbol}\n\n"
        
        # Get the latest price
        latest_price = db_manager.get_latest_price(symbol)
        result += f"**Current Price**: ${latest_price:.2f}\n\n"
        
        # Get volatility
        try:
            volatility = db_manager.calculate_volatility(symbol, "1d", days=14)
            result += f"**Volatility (14D)**: {volatility:.2f}%\n"
            
            if volatility > 4.0:
                result += "Interpretation: High volatility, suggesting significant price swings\n\n"
            elif volatility > 2.0:
                result += "Interpretation: Moderate volatility, normal market conditions\n\n"
            else:
                result += "Interpretation: Low volatility, potential breakout ahead\n\n"
        except Exception as e:
            logger.warning(f"Could not calculate volatility: {str(e)}")
        
        # Get directional indicators from recent price action
        try:
            # Get recent price data to determine trend
            now = datetime.now()
            two_weeks_ago = now - timedelta(days=14)
            market_data = db_manager.get_market_data(
                symbol=symbol,
                interval="1d",
                start_time=two_weeks_ago,
                limit=14
            )
            
            if market_data and len(market_data) >= 10:
                # Simple trend calculation
                first_price = market_data[-1].get('close', 0)
                last_price = market_data[0].get('close', 0)
                
                if first_price > 0:
                    price_change = (last_price - first_price) / first_price * 100
                    
                    result += f"**14-Day Price Change**: {price_change:.2f}%\n"
                    if price_change > 10:
                        result += "Interpretation: Strong bullish trend\n\n"
                    elif price_change > 5:
                        result += "Interpretation: Moderate bullish trend\n\n"
                    elif price_change > 0:
                        result += "Interpretation: Slight bullish bias\n\n"
                    elif price_change > -5:
                        result += "Interpretation: Slight bearish bias\n\n"
                    elif price_change > -10:
                        result += "Interpretation: Moderate bearish trend\n\n"
                    else:
                        result += "Interpretation: Strong bearish trend\n\n"
        except Exception as e:
            logger.warning(f"Could not calculate trend indicators: {str(e)}")
        
        # Get available symbols as a bonus
        available_symbols = db_manager.get_available_symbols()
        if available_symbols:
            result += f"**Available Symbols**: {', '.join(available_symbols)}\n\n"
        
        return result
    
    except Exception as e:
        logger.error(f"Error in get_technical_indicators: {str(e)}")
        return f"Error retrieving technical indicators: {str(e)}"

def get_market_data(symbol: str = "BTCUSDT", interval: str = "1h", days: int = 1) -> str:
    """
    Get market data for a specific symbol and interval.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        days: Number of days to look back
        
    Returns:
        A formatted string with market data
    """
    try:
        if not db_manager.is_connected():
            return "Database not available - cannot retrieve market data."
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Get market data
        data = db_manager.get_market_data(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=1000  # Set a reasonable limit
        )
        
        if not data:
            return f"No market data available for {symbol} with interval {interval} in the last {days} days."
        
        # Format as markdown table
        result = f"## Market Data: {symbol} ({interval})\n\n"
        result += "| Time | Open | High | Low | Close | Volume |\n"
        result += "|------|------|------|-----|-------|--------|\n"
        
        # Add rows (limit to 20 for readability)
        for i, point in enumerate(data[:20]):
            time_str = point.get('timestamp', '').split('T')[0]
            result += f"| {time_str} | ${point.get('open', 0):.2f} | ${point.get('high', 0):.2f} | "
            result += f"${point.get('low', 0):.2f} | ${point.get('close', 0):.2f} | {point.get('volume', 0):.2f} |\n"
        
        if len(data) > 20:
            result += f"\n*Note: Showing 20 of {len(data)} data points*\n"
        
        # Add a summary
        first_point = data[-1] if data else {}
        last_point = data[0] if data else {}
        
        if first_point and last_point:
            first_close = first_point.get('close', 0)
            last_close = last_point.get('close', 0)
            
            if first_close > 0:
                price_change = (last_close - first_close) / first_close * 100
                result += f"\n**Price Change**: {price_change:.2f}% over the selected period\n"
        
        return result
    
    except Exception as e:
        logger.error(f"Error in get_market_data: {str(e)}")
        return f"Error retrieving market data: {str(e)}"

def run_standalone_test():
    """Run a test with AutoGen and our standalone database functions"""
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return "No OpenAI API key found. Please set the OPENAI_API_KEY environment variable."
    
    # Show that we have an API key (first/last 4 chars only)
    logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Test database connection
    if not db_manager.is_connected():
        logger.error("Database connection failed. Check DATABASE_URL environment variable.")
        return "Database connection failed. Cannot continue with the test."
    
    # Define functions to register with the assistant
    function_map = {
        "get_bitcoin_price": get_bitcoin_price,
        "get_technical_indicators": get_technical_indicators,
        "get_market_data": get_market_data
    }
    
    # Create the assistant agent
    assistant = AssistantAgent(
        name="CryptoAnalyst",
        system_message="""You are an expert cryptocurrency market analyst. 
        You can analyze Bitcoin price data and technical indicators to provide
        market insights and trading recommendations. Always provide thorough
        analysis and explain your reasoning.""",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.2,
            "functions": [
                {
                    "name": "get_bitcoin_price",
                    "description": "Get the latest Bitcoin price information",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_technical_indicators",
                    "description": "Get technical indicators for a cryptocurrency",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., 'BTCUSDT')"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "get_market_data",
                    "description": "Get detailed market data for a specific symbol and interval",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., 'BTCUSDT')"
                            },
                            "interval": {
                                "type": "string",
                                "description": "Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back"
                            }
                        },
                        "required": []
                    }
                }
            ]
        }
    )
    
    # Register functions
    assistant.register_function(function_map=function_map)
    
    # Create the user proxy agent
    user = UserProxyAgent(
        name="User",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=10
    )
    
    # Start the conversation
    user.initiate_chat(
        assistant,
        message="What is the current Bitcoin price and what do the technical indicators suggest about market direction? Based on that, what trading strategy would you recommend?"
    )
    
    return "Test completed successfully"

if __name__ == "__main__":
    try:
        result = run_standalone_test()
        logger.info(result)
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")