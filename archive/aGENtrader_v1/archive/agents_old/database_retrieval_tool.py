"""
Database Retrieval Tool for AutoGen Agents

This module provides the functions for retrieving market data from the database
to be used by AutoGen agents.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Store database connection globally to avoid reconnecting
_db_connection = None

# Define DatabaseRetrievalTool class for testing and compatibility
class DatabaseRetrievalTool:
    """Wrapper class for database retrieval functions"""
    def __init__(self):
        pass
        
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in the database"""
        try:
            conn = get_db_connection()
            if not conn:
                return ["BTCUSDT"]  # Default fallback
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT symbol 
                    FROM market_data 
                    ORDER BY symbol
                """)
                
                results = cur.fetchall()
                if not results:
                    return ["BTCUSDT"]  # Default fallback
                return [row["symbol"] for row in results]
        except Exception as e:
            logger.error(f"Error retrieving available symbols: {str(e)}")
            return ["BTCUSDT"]  # Default fallback
        finally:
            if conn:
                conn.close()
    
    def get_latest_price(self, symbol: str) -> Union[str, None]:
        """Get the latest price for a symbol (wrapper for module function)"""
        return get_latest_price(symbol)
    
    def get_recent_market_data(self, symbol: str, limit: int = 10) -> Union[str, None]:
        """Get recent market data (wrapper for module function)"""
        return get_recent_market_data(symbol, limit)
    
    def get_market_data_range(self, symbol: str, start_time: str, end_time: str) -> Union[str, None]:
        """Get market data range (wrapper for module function)"""
        return get_market_data_range(symbol, start_time, end_time)
    
    def calculate_moving_average(self, symbol: str, period: int = 14, ma_type: str = "SMA") -> Union[str, None]:
        """Calculate moving average (wrapper for module function)"""
        return calculate_moving_average(symbol, period)
    
    def calculate_rsi(self, symbol: str, period: int = 14) -> Union[str, None]:
        """Calculate RSI (wrapper for module function)"""
        return calculate_rsi(symbol, period)
    
    def get_market_summary(self, symbol: str) -> Union[str, None]:
        """Get market summary (wrapper for module function)"""
        return get_market_summary(symbol)
    
    def get_price_history(self, symbol: str, interval: str = "1h", days: int = 7) -> Union[str, None]:
        """Get price history (wrapper for module function)"""
        return get_price_history(symbol, days)
    
    def find_support_resistance(self, symbol: str) -> Union[str, None]:
        """Find support and resistance levels (wrapper for module function)"""
        return find_support_resistance(symbol)
    
    def detect_patterns(self, symbol: str) -> Union[str, None]:
        """Detect chart patterns (wrapper for module function)"""
        return detect_patterns(symbol)
    
    def calculate_volatility(self, symbol: str, days: int = 7) -> Union[str, None]:
        """Calculate price volatility (wrapper for module function)"""
        return calculate_volatility(symbol, days)
        
def get_db_tool():
    """Return a DatabaseRetrievalTool instance for backward compatibility"""
    return DatabaseRetrievalTool()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_retrieval")

# Define database connection string
DATABASE_URL = os.environ.get("DATABASE_URL")

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and Decimal objects"""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def get_db_connection():
    """Get a connection to the database"""
    try:
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable not set")
            return None
        
        logger.info(f"Database retrieval tool initialized with {DATABASE_URL[:35]}...")
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_latest_price(symbol: str) -> Union[str, None]:
    """
    Get the latest price for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Latest price data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Query the latest price entry
            cur.execute("""
                SELECT symbol, timestamp, open, high, low, close, volume, interval
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol,))
            
            result = cur.fetchone()
            if result:
                # Convert to JSON string
                return json.dumps(dict(result), cls=CustomJSONEncoder)
            return None
    except Exception as e:
        logger.error(f"Error retrieving latest price: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_recent_market_data(symbol: str, limit: int = 10) -> Union[str, None]:
    """
    Get recent market data for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        limit: Number of data points to retrieve (default: 10)
        
    Returns:
        Recent market data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Query recent market data
            cur.execute("""
                SELECT *
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (symbol, limit))
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "data": [dict(row) for row in results],
                    "count": len(results),
                    "latest_timestamp": results[0]["timestamp"].isoformat() if results and "timestamp" in results[0] else None
                }
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({"symbol": symbol, "data": [], "count": 0})
    except Exception as e:
        logger.error(f"Error retrieving recent market data: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_market_data_range(symbol: str, start_time: str, end_time: str) -> Union[str, None]:
    """
    Get market data for a symbol within a time range.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        start_time: Start time in ISO format
        end_time: End time in ISO format
        
    Returns:
        Market data within the time range as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Query market data within time range
            cur.execute("""
                SELECT *
                FROM market_data
                WHERE symbol = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp ASC
            """, (symbol, start_time, end_time))
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "start_time": start_time,
                    "end_time": end_time,
                    "data": [dict(row) for row in results],
                    "count": len(results)
                }
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({"symbol": symbol, "data": [], "count": 0, "start_time": start_time, "end_time": end_time})
    except Exception as e:
        logger.error(f"Error retrieving market data range: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def calculate_moving_average(symbol: str, window: int = 14) -> Union[str, None]:
    """
    Calculate the simple moving average for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        window: Number of periods for the moving average
        
    Returns:
        Moving average data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Get recent closing prices
            cur.execute("""
                SELECT timestamp, close
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (symbol, window))
            
            results = cur.fetchall()
            if len(results) < window:
                return json.dumps({
                    "symbol": symbol,
                    "window": window,
                    "moving_average": None,
                    "error": f"Insufficient data: need {window} points but only {len(results)} available"
                })
            
            # Calculate SMA
            closing_prices = [float(row["close"]) for row in results]
            sma = sum(closing_prices) / len(closing_prices)
            
            response = {
                "symbol": symbol,
                "window": window,
                "moving_average": sma,
                "timestamp": datetime.now().isoformat(),
                "data_points": len(results)
            }
            
            # Convert to JSON string
            return json.dumps(response, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error calculating moving average: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def calculate_rsi(symbol: str, period: int = 14) -> Union[str, None]:
    """
    Calculate the Relative Strength Index (RSI) for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        period: Number of periods for the RSI calculation
        
    Returns:
        RSI data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Get enough data points for the calculation
            cur.execute("""
                SELECT timestamp, close
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (symbol, period + 1))
            
            results = cur.fetchall()
            if len(results) < period + 1:
                return json.dumps({
                    "symbol": symbol,
                    "period": period,
                    "rsi": None,
                    "error": f"Insufficient data: need {period + 1} points but only {len(results)} available"
                })
            
            # Calculate price changes
            results.reverse()  # oldest first for calculation
            price_changes = [float(results[i+1]["close"]) - float(results[i]["close"]) for i in range(len(results)-1)]
            
            # Calculate gains and losses
            gains = [max(0, change) for change in price_changes]
            losses = [max(0, -change) for change in price_changes]
            
            # Calculate average gain and average loss
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            # Calculate RS and RSI
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            response = {
                "symbol": symbol,
                "period": period,
                "rsi": rsi,
                "timestamp": datetime.now().isoformat(),
                "interpretation": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
            }
            
            # Convert to JSON string
            return json.dumps(response, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_market_summary(symbol: str) -> Union[str, None]:
    """
    Get a summary of current market conditions for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Market summary as a JSON string or None if error
    """
    try:
        # Get latest price
        latest_price_json = get_latest_price(symbol)
        if not latest_price_json:
            return None
        
        latest_price = json.loads(latest_price_json)
        
        # Get recent data for price change calculation
        recent_data_json = get_recent_market_data(symbol, 2)
        if not recent_data_json:
            return None
        
        recent_data = json.loads(recent_data_json)
        
        # Calculate price change
        if len(recent_data["data"]) >= 2:
            current_price = float(recent_data["data"][0]["close"])
            previous_price = float(recent_data["data"][1]["close"])
            price_change = current_price - previous_price
            percent_change = (price_change / previous_price) * 100
        else:
            price_change = 0
            percent_change = 0
        
        # Calculate indicators
        sma_json = calculate_moving_average(symbol)
        rsi_json = calculate_rsi(symbol)
        
        sma = json.loads(sma_json) if sma_json else {"moving_average": None}
        rsi = json.loads(rsi_json) if rsi_json else {"rsi": None}
        
        # Create summary
        summary = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": latest_price["close"],
            "price_change": price_change,
            "percent_change": percent_change,
            "sma": sma.get("moving_average"),
            "rsi": rsi.get("rsi"),
            "market_condition": "bullish" if percent_change > 0 else "bearish",
            "latest_data_timestamp": latest_price["timestamp"]
        }
        
        # Convert to JSON string
        return json.dumps(summary, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error generating market summary: {str(e)}")
        return None

# Additional functions for more complex analysis
def get_price_history(symbol: str, days: int = 7) -> Union[str, None]:
    """
    Get price history for a symbol for a number of days.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        days: Number of days of history to retrieve
        
    Returns:
        Price history as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Calculate start time based on days
            cur.execute("""
                SELECT *
                FROM market_data
                WHERE symbol = %s AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (symbol, days))
            
            results = cur.fetchall()
            if results:
                # Format response
                response = {
                    "symbol": symbol,
                    "days": days,
                    "data": [dict(row) for row in results],
                    "count": len(results),
                    "start_date": results[0]["timestamp"].isoformat() if results else None,
                    "end_date": results[-1]["timestamp"].isoformat() if results else None
                }
                
                # Convert to JSON string
                return json.dumps(response, cls=CustomJSONEncoder)
            
            return json.dumps({"symbol": symbol, "days": days, "data": [], "count": 0})
    except Exception as e:
        logger.error(f"Error retrieving price history: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def find_support_resistance(symbol: str) -> Union[str, None]:
    """
    Find support and resistance levels for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Support and resistance levels as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Get price data for analysis
            cur.execute("""
                SELECT timestamp, high, low, close
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT 100
            """, (symbol,))
            
            results = cur.fetchall()
            if not results:
                return json.dumps({
                    "symbol": symbol,
                    "support_levels": [],
                    "resistance_levels": [],
                    "error": "Insufficient data for analysis"
                })
            
            # Extract highs and lows
            highs = [float(row["high"]) for row in results]
            lows = [float(row["low"]) for row in results]
            
            # Simple approach: find local maxima and minima
            # This is a simplified approach - real support/resistance would use more complex methods
            resistance_points = []
            support_points = []
            
            # Get current price
            current_price = float(results[0]["close"])
            
            # Find points significantly higher/lower than neighbors
            for i in range(1, len(results) - 1):
                # Resistance (local maxima)
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    resistance_points.append(highs[i])
                
                # Support (local minima)
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    support_points.append(lows[i])
            
            # Filter for significant levels (reduce noise)
            # Group close values together
            def group_levels(levels, tolerance=0.01):
                if not levels:
                    return []
                
                levels.sort()
                grouped = []
                current_group = [levels[0]]
                
                for i in range(1, len(levels)):
                    if abs(levels[i] - current_group[0]) / current_group[0] <= tolerance:
                        current_group.append(levels[i])
                    else:
                        grouped.append(sum(current_group) / len(current_group))
                        current_group = [levels[i]]
                
                if current_group:
                    grouped.append(sum(current_group) / len(current_group))
                
                return grouped
            
            support_levels = group_levels(support_points)
            resistance_levels = group_levels(resistance_points)
            
            # Filter for levels near current price
            relevant_supports = [level for level in support_levels if level < current_price]
            relevant_resistances = [level for level in resistance_levels if level > current_price]
            
            # Sort by proximity to current price
            relevant_supports.sort(key=lambda x: current_price - x)
            relevant_resistances.sort(key=lambda x: x - current_price)
            
            response = {
                "symbol": symbol,
                "current_price": current_price,
                "support_levels": relevant_supports[:3],  # Top 3 closest support levels
                "resistance_levels": relevant_resistances[:3],  # Top 3 closest resistance levels
                "timestamp": datetime.now().isoformat()
            }
            
            # Convert to JSON string
            return json.dumps(response, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error finding support/resistance: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def detect_patterns(symbol: str) -> Union[str, None]:
    """
    Detect common chart patterns in the price action.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        
    Returns:
        Detected patterns as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Get price data for analysis
            cur.execute("""
                SELECT timestamp, open, high, low, close
                FROM market_data
                WHERE symbol = %s
                ORDER BY timestamp ASC
                LIMIT 30
            """, (symbol,))
            
            results = cur.fetchall()
            if len(results) < 10:
                return json.dumps({
                    "symbol": symbol,
                    "patterns": [],
                    "error": "Insufficient data for pattern detection"
                })
            
            # Extract price series
            closes = [float(row["close"]) for row in results]
            highs = [float(row["high"]) for row in results]
            lows = [float(row["low"]) for row in results]
            
            # Simplified pattern detection
            # Note: Real pattern detection would use more sophisticated techniques
            patterns = []
            
            # Check for uptrend
            if all(closes[i] <= closes[i+1] for i in range(len(closes)-3, len(closes)-1)):
                patterns.append({
                    "name": "Uptrend",
                    "confidence": 0.7,
                    "description": "Price showing consistent higher highs and higher lows"
                })
            
            # Check for downtrend
            if all(closes[i] >= closes[i+1] for i in range(len(closes)-3, len(closes)-1)):
                patterns.append({
                    "name": "Downtrend",
                    "confidence": 0.7,
                    "description": "Price showing consistent lower highs and lower lows"
                })
            
            # Check for potential double top
            if len(highs) > 10:
                recent_high = max(highs[-10:])
                # Find indices of peaks close to the recent high
                peaks = [i for i in range(len(highs)-10, len(highs)) 
                        if highs[i] > 0.98 * recent_high]
                if len(peaks) >= 2 and peaks[-1] - peaks[0] >= 3:  # At least 3 bars between peaks
                    patterns.append({
                        "name": "Double Top",
                        "confidence": 0.6,
                        "description": "Two distinct peaks at similar price levels indicating resistance"
                    })
            
            # Check for potential double bottom
            if len(lows) > 10:
                recent_low = min(lows[-10:])
                # Find indices of troughs close to the recent low
                troughs = [i for i in range(len(lows)-10, len(lows)) 
                          if lows[i] < 1.02 * recent_low]
                if len(troughs) >= 2 and troughs[-1] - troughs[0] >= 3:  # At least 3 bars between troughs
                    patterns.append({
                        "name": "Double Bottom",
                        "confidence": 0.6,
                        "description": "Two distinct bottoms at similar price levels indicating support"
                    })
            
            response = {
                "symbol": symbol,
                "patterns": patterns,
                "timestamp": datetime.now().isoformat(),
                "analysis_window": {
                    "start": results[0]["timestamp"].isoformat(),
                    "end": results[-1]["timestamp"].isoformat()
                }
            }
            
            # Convert to JSON string
            return json.dumps(response, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error detecting patterns: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def calculate_volatility(symbol: str, days: int = 7) -> Union[str, None]:
    """
    Calculate price volatility over a specified period.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        days: Number of days for the calculation
        
    Returns:
        Volatility data as a JSON string or None if error
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        with conn.cursor() as cur:
            # Get price data for volatility calculation
            cur.execute("""
                SELECT timestamp, close
                FROM market_data
                WHERE symbol = %s AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (symbol, days))
            
            results = cur.fetchall()
            if len(results) < 2:
                return json.dumps({
                    "symbol": symbol,
                    "volatility": None,
                    "error": "Insufficient data for volatility calculation"
                })
            
            # Calculate daily returns
            closes = [float(row["close"]) for row in results]
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            
            # Calculate standard deviation of returns (volatility)
            import math
            mean_return = sum(returns) / len(returns)
            squared_diffs = [(r - mean_return) ** 2 for r in returns]
            variance = sum(squared_diffs) / len(squared_diffs)
            volatility = math.sqrt(variance)
            
            # Annualize the volatility (standard practice)
            # Assuming we have daily data
            annualized_volatility = volatility * math.sqrt(365)
            
            # Get latest price
            latest_price = closes[-1]
            
            # Create volatility bands (for visualization)
            upper_band = latest_price * (1 + volatility)
            lower_band = latest_price * (1 - volatility)
            
            response = {
                "symbol": symbol,
                "period_days": days,
                "data_points": len(results),
                "volatility": volatility,
                "annualized_volatility": annualized_volatility,
                "current_price": latest_price,
                "volatility_bands": {
                    "upper": upper_band,
                    "lower": lower_band
                },
                "interpretation": "high" if volatility > 0.03 else "medium" if volatility > 0.01 else "low",
                "timestamp": datetime.now().isoformat()
            }
            
            # Convert to JSON string
            return json.dumps(response, cls=CustomJSONEncoder)
    except Exception as e:
        logger.error(f"Error calculating volatility: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()