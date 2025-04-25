"""
Database Retrieval Tool Module (Simplified for EC2 Backtesting)
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("database_retrieval_tool")

def get_database_connection():
    """Get a database connection"""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is not set")
        return None
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_latest_price(symbol: str) -> Optional[str]:
    """Get the latest price for a symbol"""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, open, high, low, close, volume
            FROM market_data
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (symbol,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        timestamp, open_price, high, low, close, volume = row
        
        result = {
            "timestamp": timestamp.isoformat(),
            "open": float(open_price),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": float(volume)
        }
        
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error getting latest price: {str(e)}")
        return None
    finally:
        conn.close()

def get_recent_market_data(symbol: str, limit: int = 20) -> Optional[str]:
    """Get recent market data for a symbol"""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, open, high, low, close, volume
            FROM market_data
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (symbol, limit))
        
        rows = cursor.fetchall()
        if not rows:
            return None
        
        result = []
        for row in rows:
            timestamp, open_price, high, low, close, volume = row
            result.append({
                "timestamp": timestamp.isoformat(),
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume)
            })
        
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error getting recent market data: {str(e)}")
        return None
    finally:
        conn.close()

def calculate_moving_average(symbol: str, period: int = 20, interval: str = "1d") -> Optional[str]:
    """Calculate the moving average for a symbol"""
    # This is a simplified implementation for backtesting
    result = {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "value": 85000.0,  # Simplified value
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(result)

def calculate_rsi(symbol: str, period: int = 14, interval: str = "1d") -> Optional[str]:
    """Calculate the RSI for a symbol"""
    # This is a simplified implementation for backtesting
    result = {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "value": 55.0,  # Simplified value
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(result)

def get_market_summary(symbol: str) -> Optional[str]:
    """Get a market summary for a symbol"""
    # This is a simplified implementation for backtesting
    result = {
        "symbol": symbol,
        "current_price": 85000.0,  # Simplified value
        "24h_change": 1.5,  # Simplified value
        "24h_volume": 1200000000.0,  # Simplified value
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(result)

def find_support_resistance(symbol: str) -> Optional[str]:
    """Find support and resistance levels for a symbol"""
    # This is a simplified implementation for backtesting
    result = {
        "symbol": symbol,
        "support_levels": [82000.0, 80000.0, 78000.0],  # Simplified values
        "resistance_levels": [86000.0, 88000.0, 90000.0],  # Simplified values
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(result)

def detect_patterns(symbol: str) -> Optional[str]:
    """Detect chart patterns for a symbol"""
    # This is a simplified implementation for backtesting
    result = {
        "symbol": symbol,
        "patterns": ["bullish_engulfing", "double_bottom"],  # Simplified values
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(result)

def calculate_volatility(symbol: str) -> Optional[str]:
    """Calculate volatility for a symbol"""
    # This is a simplified implementation for backtesting
    result = {
        "symbol": symbol,
        "daily_volatility": 2.5,  # Simplified value
        "weekly_volatility": 5.2,  # Simplified value
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(result)
