"""
AutoGen Database Integration

This module provides integration between AutoGen agents and the PostgreSQL database,
allowing agents to directly query market data for technical analysis and decision making.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("database_integration")

class DatabaseQueryManager:
    """
    Manager for database queries that allows agents to request data in a structured way.
    
    This class provides a set of formatted query templates that can be used by agents
    to retrieve market data and perform technical analysis.
    """
    
    def __init__(self):
        """Initialize the database query manager"""
        self.connection = None
        self._connect_to_database()
    
    def _connect_to_database(self) -> None:
        """Establish a connection to the PostgreSQL database"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                raise ValueError("DATABASE_URL environment variable not set")
            
            self.connection = psycopg2.connect(database_url)
            logger.info("Successfully connected to the database")
        
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def _ensure_connection(self) -> None:
        """Ensure the database connection is active, reconnect if needed"""
        try:
            # Check if connection is closed or in error state
            if not self.connection or self.connection.closed:
                logger.info("Database connection is closed, reconnecting...")
                self._connect_to_database()
                
            # Test connection with a simple query
            if not self.connection or self.connection.closed:
                raise ValueError("Failed to establish database connection")
                
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        
        except Exception as e:
            logger.warning(f"Connection check failed: {str(e)}. Attempting to reconnect...")
            self._connect_to_database()
            
            # Verify connection was established
            if not self.connection or self.connection.closed:
                raise ConnectionError("Could not establish a database connection after retry")
    
    def close(self) -> None:
        """Close the database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Database connection closed")
    
    def get_available_symbols(self) -> List[str]:
        """
        Get a list of available trading symbols in the database
        
        Returns:
            List of symbol strings
        """
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT symbol FROM market_data
                    ORDER BY symbol
                """)
                symbols = [row[0] for row in cursor.fetchall()]
            
            return symbols
        
        except Exception as e:
            logger.error(f"Error getting available symbols: {str(e)}")
            return []
    
    def get_available_intervals(self, symbol: Optional[str] = None) -> List[str]:
        """
        Get a list of available time intervals in the database
        
        Args:
            symbol: Optional symbol to filter intervals
            
        Returns:
            List of interval strings
        """
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                if symbol:
                    cursor.execute("""
                        SELECT DISTINCT interval FROM market_data
                        WHERE symbol = %s
                        ORDER BY interval
                    """, (symbol,))
                else:
                    cursor.execute("""
                        SELECT DISTINCT interval FROM market_data
                        ORDER BY interval
                    """)
                
                intervals = [row[0] for row in cursor.fetchall()]
            
            return intervals
        
        except Exception as e:
            logger.error(f"Error getting available intervals: {str(e)}")
            return []
    
    def get_market_data(
            self,
            symbol: str,
            interval: str,
            start_time: Optional[Union[str, datetime]] = None,
            end_time: Optional[Union[str, datetime]] = None,
            limit: int = 100
        ) -> List[Dict[str, Any]]:
        """
        Get historical market data for a symbol and interval
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            start_time: Start time (string or datetime)
            end_time: End time (string or datetime)
            limit: Maximum number of records to retrieve
            
        Returns:
            List of market data points
        """
        self._ensure_connection()
        
        # Convert datetime objects to ISO strings
        if isinstance(start_time, datetime):
            start_time = start_time.isoformat()
        
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM market_data
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
                
                cursor.execute(query, params)
                data = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(row) for row in data]
        
        except Exception as e:
            logger.error(f"Error retrieving market data: {str(e)}")
            return []
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Latest price or None if not found
        """
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT close FROM market_data
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (symbol,))
                
                result = cursor.fetchone()
                
                if result:
                    return float(result[0])
                else:
                    return None
        
        except Exception as e:
            logger.error(f"Error getting latest price: {str(e)}")
            return None
    
    def get_price_statistics(
            self,
            symbol: str,
            interval: str,
            days: int = 30
        ) -> Dict[str, Any]:
        """
        Get price statistics for a symbol over a time period
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            days: Number of days to look back
            
        Returns:
            Dictionary with price statistics
        """
        self._ensure_connection()
        
        # Ensure days is an integer
        if not isinstance(days, int):
            try:
                days = int(days)
                logger.warning(f"Converting days parameter from {type(days).__name__} to int: {days}")
            except (TypeError, ValueError):
                days = 30
                logger.warning(f"Failed to convert days parameter to int, using default: {days}")
        
        try:
            # Calculate start date
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        MIN(close) as min_price,
                        MAX(close) as max_price,
                        AVG(close) as avg_price,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY close) as median_price,
                        COUNT(*) as data_points
                    FROM market_data
                    WHERE symbol = %s 
                      AND interval = %s
                      AND timestamp >= %s
                """, (symbol, interval, start_date))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "min_price": float(result[0]) if result[0] else None,
                        "max_price": float(result[1]) if result[1] else None,
                        "avg_price": float(result[2]) if result[2] else None,
                        "median_price": float(result[3]) if result[3] else None,
                        "data_points": result[4],
                        "period_days": days,
                        "symbol": symbol,
                        "interval": interval
                    }
                else:
                    return {
                        "error": f"No data found for {symbol} with {interval} interval in the last {days} days"
                    }
        
        except Exception as e:
            logger.error(f"Error getting price statistics: {str(e)}")
            return {"error": str(e)}
    
    def calculate_volatility(
            self,
            symbol: str,
            interval: str,
            days: int = 14
        ) -> Dict[str, Any]:
        """
        Calculate volatility for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            days: Number of days to look back
            
        Returns:
            Dictionary with volatility metrics
        """
        self._ensure_connection()
        
        # Ensure days is an integer
        if not isinstance(days, int):
            try:
                days = int(days)
                logger.warning(f"Converting days parameter from {type(days).__name__} to int: {days}")
            except (TypeError, ValueError):
                days = 14
                logger.warning(f"Failed to convert days parameter to int, using default: {days}")
        
        try:
            # Get market data for the period
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT timestamp, close
                    FROM market_data
                    WHERE symbol = %s 
                      AND interval = %s
                      AND timestamp >= %s
                    ORDER BY timestamp
                """, (symbol, interval, start_date))
                
                data = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = [dict(row) for row in data]
            
            if not data:
                return {
                    "error": f"No data found for {symbol} with {interval} interval in the last {days} days"
                }
            
            # Calculate daily returns
            returns = []
            prev_price = None
            
            for point in data:
                if prev_price:
                    daily_return = (float(point['close']) / prev_price) - 1
                    returns.append(daily_return)
                prev_price = float(point['close'])
            
            # Calculate volatility as standard deviation of returns
            if returns:
                # Calculate volatility manually if numpy is not available
                try:
                    import numpy as np
                    volatility = np.std(returns)
                    annualized_volatility = volatility * np.sqrt(365 / days)
                except ImportError:
                    # Manual calculation
                    mean = sum(returns) / len(returns)
                    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
                    volatility = variance ** 0.5
                    annualized_volatility = volatility * (365 / days) ** 0.5
                
                return {
                    "daily_volatility": float(volatility),
                    "annualized_volatility": float(annualized_volatility),
                    "period_days": days,
                    "data_points": len(data),
                    "symbol": symbol,
                    "interval": interval
                }
            else:
                return {
                    "error": f"Not enough data points to calculate volatility for {symbol}"
                }
        
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return {"error": str(e)}
    
    def get_market_summary(
            self,
            symbol: str,
            interval: str = "1d",
            days: int = 7
        ) -> Dict[str, Any]:
        """
        Get a comprehensive market summary for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            days: Number of days to look back
            
        Returns:
            Dictionary with market summary
        """
        self._ensure_connection()
        
        # Ensure days is an integer
        if not isinstance(days, int):
            try:
                days = int(days)
                logger.warning(f"Converting days parameter from {type(days).__name__} to int: {days}")
            except (TypeError, ValueError):
                days = 7
                logger.warning(f"Failed to convert days parameter to int, using default: {days}")
        
        try:
            # Get recent market data first to ensure we have data to work with
            market_data = self.get_market_data(
                symbol=symbol,
                interval=interval,
                limit=min(days * 24, 100)  # Limit based on interval and days
            )
            
            if not market_data:
                return {
                    "error": f"No market data available for {symbol} with {interval} interval",
                    "symbol": symbol,
                    "interval": interval
                }
            
            # Get latest price
            try:
                latest_price = self.get_latest_price(symbol)
            except Exception as e:
                logger.warning(f"Error getting latest price: {str(e)}")
                latest_price = None
                if market_data:
                    try:
                        # Use most recent price from market data as fallback
                        latest_price = float(market_data[0].get('close', 0))
                    except:
                        pass
            
            # Get price statistics
            try:
                price_stats = self.get_price_statistics(symbol, interval, days)
            except Exception as e:
                logger.warning(f"Error getting price statistics: {str(e)}")
                price_stats = {"error": str(e)}
            
            # Get volatility metrics
            try:
                volatility = self.calculate_volatility(symbol, interval, days)
            except Exception as e:
                logger.warning(f"Error calculating volatility: {str(e)}")
                volatility = {"error": str(e)}
            
            # Calculate basic trend metrics
            trend = "unknown"
            trend_strength = 0.0
            price_change_pct = None
            
            if len(market_data) > 1:
                try:
                    # Simple trend calculation
                    oldest_price = float(market_data[-1]['close'])
                    newest_price = float(market_data[0]['close'])
                    
                    if oldest_price > 0:  # Prevent division by zero
                        price_change = newest_price - oldest_price
                        price_change_pct = (price_change / oldest_price) * 100
                        
                        if price_change_pct > 5:
                            trend = "strong_uptrend"
                            trend_strength = min(abs(price_change_pct) / 10, 1.0)
                        elif price_change_pct > 1:
                            trend = "uptrend"
                            trend_strength = min(abs(price_change_pct) / 5, 1.0)
                        elif price_change_pct < -5:
                            trend = "strong_downtrend"
                            trend_strength = min(abs(price_change_pct) / 10, 1.0)
                        elif price_change_pct < -1:
                            trend = "downtrend"
                            trend_strength = min(abs(price_change_pct) / 5, 1.0)
                        else:
                            trend = "sideways"
                            trend_strength = 0.5
                except Exception as e:
                    logger.warning(f"Error calculating trend metrics: {str(e)}")
            
            # Compile the market summary
            return {
                "symbol": symbol,
                "interval": interval,
                "latest_price": latest_price,
                "price_statistics": price_stats,
                "volatility": volatility,
                "trend": {
                    "direction": trend,
                    "strength": trend_strength,
                    "price_change_percent": price_change_pct
                },
                "data_period_days": days,
                "timestamp": datetime.now().isoformat(),
                "sample_size": len(market_data)
            }
        
        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}")
            return {
                "error": str(e),
                "symbol": symbol,
                "interval": interval
            }
    
    def execute_custom_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results as a list of dictionaries
        """
        self._ensure_connection()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or [])
                data = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(row) for row in data]
        
        except Exception as e:
            logger.error(f"Error executing custom query: {str(e)}")
            return [{"error": str(e)}]

    def find_support_resistance_levels(
            self,
            symbol: str,
            interval: str = "1d",
            days: int = 30,
            num_levels: int = 3
        ) -> Dict[str, Any]:
        """
        Find support and resistance levels for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            days: Number of days to look back
            num_levels: Number of support/resistance levels to find
            
        Returns:
            Dictionary with support and resistance levels
        """
        self._ensure_connection()
        
        # Ensure days is an integer
        if not isinstance(days, int):
            try:
                days = int(days)
                logger.warning(f"Converting days parameter from {type(days).__name__} to int: {days}")
            except (TypeError, ValueError):
                days = 30
                logger.warning(f"Failed to convert days parameter to int, using default: {days}")
                
        # Ensure num_levels is an integer
        if not isinstance(num_levels, int):
            try:
                num_levels = int(num_levels)
                logger.warning(f"Converting num_levels parameter from {type(num_levels).__name__} to int: {num_levels}")
            except (TypeError, ValueError):
                num_levels = 3
                logger.warning(f"Failed to convert num_levels parameter to int, using default: {num_levels}")
        
        try:
            # Get market data for the period
            market_data = self.get_market_data(
                symbol=symbol,
                interval=interval,
                limit=min(days * 24, 200)  # Limit based on interval and days
            )
            
            if not market_data:
                return {
                    "error": f"No data found for {symbol} with {interval} interval in the last {days} days"
                }
            
            # Extract high and low prices
            highs = [float(data['high']) for data in market_data]
            lows = [float(data['low']) for data in market_data]
            
            # Sort prices
            highs.sort()
            lows.sort()
            
            # Simple clustering to find key levels
            def find_clusters(prices, num_clusters):
                if not prices:
                    return []
                
                clusters = []
                step = max(1, len(prices) // (num_clusters + 1))
                
                for i in range(step, len(prices), step):
                    if len(clusters) >= num_clusters:
                        break
                    clusters.append(prices[i])
                
                return clusters
            
            # Find support and resistance levels
            support_levels = find_clusters(lows, num_levels)
            resistance_levels = find_clusters(highs, num_levels)
            
            # Get current price
            current_price = self.get_latest_price(symbol)
            
            return {
                "symbol": symbol,
                "interval": interval,
                "current_price": current_price,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "data_period_days": days,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error finding support/resistance levels: {str(e)}")
            return {"error": str(e)}
    
    def get_funding_rates(
            self,
            symbol: str,
            days: int = 7
        ) -> Dict[str, Any]:
        """
        Get funding rates for a symbol (if available)
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            days: Number of days to look back
            
        Returns:
            Dictionary with funding rate information
        """
        self._ensure_connection()
        
        # Ensure days is an integer
        if not isinstance(days, int):
            try:
                days = int(days)
                logger.warning(f"Converting days parameter from {type(days).__name__} to int: {days}")
            except (TypeError, ValueError):
                days = 7
                logger.warning(f"Failed to convert days parameter to int, using default: {days}")
        
        try:
            # Calculate start date
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Check if funding_rates table exists and has data
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'funding_rates'
                    )
                """)
                
                has_funding_rates = cursor.fetchone()[0]
            
            if not has_funding_rates:
                return {
                    "error": "Funding rates table not found in database"
                }
            
            # Get funding rates
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM funding_rates
                    WHERE symbol = %s
                      AND timestamp >= %s
                    ORDER BY timestamp DESC
                """, (symbol, start_date))
                
                data = cursor.fetchall()
            
            if not data:
                return {
                    "error": f"No funding rate data found for {symbol} in the last {days} days"
                }
            
            # Calculate average funding rate
            funding_rates = [float(rate['funding_rate']) for rate in data]
            avg_funding_rate = sum(funding_rates) / len(funding_rates)
            
            # Calculate annualized funding rate (assuming 3 funding events per day)
            annual_rate = avg_funding_rate * 3 * 365
            
            return {
                "symbol": symbol,
                "latest_funding_rate": float(data[0]['funding_rate']),
                "average_funding_rate": avg_funding_rate,
                "annualized_rate": annual_rate,
                "funding_events": len(data),
                "data_period_days": days,
                "timestamp": datetime.now().isoformat(),
                "data": [dict(rate) for rate in data[:10]]  # Include the 10 most recent entries
            }
        
        except Exception as e:
            logger.error(f"Error retrieving funding rates: {str(e)}")
            return {"error": str(e)}

class AgentDatabaseInterface:
    """
    Interface for AutoGen agents to interact with the database.
    
    This class provides a simplified interface for agents to request market data
    and analytics, with natural language processing capabilities to interpret
    agent queries into database operations.
    """
    
    def __init__(self):
        """Initialize the agent database interface"""
        self.query_manager = DatabaseQueryManager()
        self.cached_data = {}
    
    def process_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language query from an agent
        
        Args:
            query: Natural language query string
            params: Optional parameters for the query
            
        Returns:
            Response data
        """
        params = params or {}
        
        try:
            # Extract parameters from query and params
            symbol = params.get('symbol', 'BTCUSDT')
            interval = params.get('interval', '1h')
            days = params.get('days', 7)
            
            # Check for timeframe specifications in the query text
            query_lower = query.lower()
            if '4-hour' in query_lower or '4 hour' in query_lower or '4h' in query_lower:
                interval = '4h'
            elif '1-hour' in query_lower or '1 hour' in query_lower or '1h' in query_lower:
                interval = '1h'
            elif '15-minute' in query_lower or '15 minute' in query_lower or '15m' in query_lower:
                interval = '15m'
            elif '30-minute' in query_lower or '30 minute' in query_lower or '30m' in query_lower:
                interval = '30m'
            elif 'daily' in query_lower or 'day' in query_lower:
                interval = 'D'
                
            # Check for time period specifications
            if '2 weeks' in query_lower or 'two weeks' in query_lower:
                days = 14
            elif 'week' in query_lower:
                days = 7
            elif 'month' in query_lower:
                days = 30
            elif '3 days' in query_lower or 'three days' in query_lower:
                days = 3
            
            # Process different types of queries
            if any(keyword in query.lower() for keyword in ['available', 'symbols', 'list']):
                symbols = self.query_manager.get_available_symbols()
                return {
                    "query_type": "available_symbols",
                    "result": symbols,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['interval', 'timeframe']):
                intervals = self.query_manager.get_available_intervals(symbol)
                return {
                    "query_type": "available_intervals",
                    "symbol": symbol,
                    "result": intervals,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['price', 'latest', 'current']):
                price = self.query_manager.get_latest_price(symbol)
                return {
                    "query_type": "latest_price",
                    "symbol": symbol,
                    "price": price,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['statistic', 'stats', 'summary']):
                summary = self.query_manager.get_market_summary(symbol, interval, days)
                return {
                    "query_type": "market_summary",
                    "data": summary,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['volatility', 'risk']):
                volatility = self.query_manager.calculate_volatility(symbol, interval, days)
                return {
                    "query_type": "volatility",
                    "data": volatility,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['support', 'resistance', 'level']):
                levels = self.query_manager.find_support_resistance_levels(symbol, interval, days)
                return {
                    "query_type": "support_resistance",
                    "data": levels,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['funding', 'rate']):
                funding = self.query_manager.get_funding_rates(symbol, days)
                return {
                    "query_type": "funding_rates",
                    "data": funding,
                    "timestamp": datetime.now().isoformat()
                }
            
            elif any(keyword in query.lower() for keyword in ['market data', 'ohlc', 'candle']):
                limit = params.get('limit', 20)
                data = self.query_manager.get_market_data(symbol, interval, limit=limit)
                return {
                    "query_type": "market_data",
                    "symbol": symbol,
                    "interval": interval,
                    "count": len(data),
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                # Default to market summary
                summary = self.query_manager.get_market_summary(symbol, interval, days)
                return {
                    "query_type": "general_query",
                    "original_query": query,
                    "data": summary,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            return {
                "error": f"Failed to process query: {str(e)}",
                "original_query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_technical_analysis(self, symbol: str, interval: str = '1d', days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive technical analysis for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1h", "4h", "1d")
            days: Number of days to analyze
            
        Returns:
            Technical analysis report
        """
        try:
            # Get market data
            market_data = self.query_manager.get_market_data(
                symbol=symbol,
                interval=interval,
                limit=min(days * 24, 200)
            )
            
            if not market_data:
                return {
                    "error": f"No data found for {symbol} with {interval} interval in the last {days} days"
                }
            
            # Get support/resistance levels
            levels = self.query_manager.find_support_resistance_levels(symbol, interval, days)
            
            # Get market summary
            summary = self.query_manager.get_market_summary(symbol, interval, days)
            
            # Get volatility metrics
            volatility = self.query_manager.calculate_volatility(symbol, interval, days)
            
            # Check if funding rates are available
            try:
                funding = self.query_manager.get_funding_rates(symbol, days)
            except:
                funding = {"error": "Funding rate data not available"}
            
            # Compile technical analysis report
            analysis = {
                "symbol": symbol,
                "interval": interval,
                "data_period_days": days,
                "market_summary": summary,
                "support_resistance": levels,
                "volatility": volatility,
                "funding_rates": funding,
                "timestamp": datetime.now().isoformat()
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error generating technical analysis: {str(e)}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """Close database connections"""
        self.query_manager.close()