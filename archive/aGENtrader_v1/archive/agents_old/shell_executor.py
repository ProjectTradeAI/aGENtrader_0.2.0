"""
Shell Command Executor Agent

Responsible for executing shell commands and database queries,
providing a centralized interface for other agents.
"""

import json
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class ShellExecutorAgent:
    """Agent responsible for executing shell commands and database queries"""

    def __init__(self):
        """Initialize the Shell Executor Agent"""
        self.name = "Shell Executor Agent"
        self._setup_database_connection()
        self.timeframe_map = {
            "1h": "INTERVAL '1 hour'",
            "4h": "INTERVAL '4 hours'",
            "12h": "INTERVAL '12 hours'",
            "24h": "INTERVAL '24 hours'",
            "7d": "INTERVAL '7 days'"
        }

    def _setup_database_connection(self):
        """Setup PostgreSQL database connection"""
        try:
            self.conn = psycopg2.connect(
                dbname=os.environ.get('PGDATABASE'),
                user=os.environ.get('PGUSER'),
                password=os.environ.get('PGPASSWORD'),
                host=os.environ.get('PGHOST'),
                port=os.environ.get('PGPORT')
            )
            logger.info("Successfully connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            self.conn = None

    def decimal_to_float(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        return str(obj)

    def get_market_data(self, symbol: str, timeframe: str = "24h", target_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market data for a specific symbol and timeframe using a time-window approach.

        This method uses a ±1 hour window around the target timestamp to calculate statistics,
        which provides more accurate real-time data by considering multiple price points.
        The stats may differ slightly from single-point database queries but offer better
        price movement visibility.

        Args:
            symbol: Trading pair symbol (e.g. "BTCUSDT")
            timeframe: Data timeframe ("1h", "4h", etc.)
            target_time: Optional specific timestamp to query
        """
        if target_time:
            query = """
                WITH time_window AS (
                    SELECT 
                        *,
                        ABS(EXTRACT(EPOCH FROM (timestamp - %s::timestamp))) as time_diff
                    FROM market_data 
                    WHERE symbol = %s
                    AND source = 'coinapi'
                    AND interval = %s
                    AND timestamp >= %s::timestamp - INTERVAL '1 hour'
                    AND timestamp <= %s::timestamp + INTERVAL '1 hour'
                    ORDER BY time_diff ASC
                )
                SELECT 
                    symbol, 
                    open, 
                    high, 
                    low, 
                    close, 
                    volume, 
                    timestamp,
                    interval,
                    source,
                    time_diff
                FROM time_window
                ORDER BY time_diff ASC;
            """
            params = (target_time, symbol, timeframe, target_time, target_time)
            logger.info(f"Executing timestamp query for {symbol} at {target_time} with {timeframe} interval")
        else:
            query = """
                SELECT 
                    symbol, 
                    open, 
                    high, 
                    low, 
                    close, 
                    volume, 
                    timestamp,
                    interval,
                    source
                FROM market_data 
                WHERE symbol = %s
                AND source = 'coinapi'
                AND interval = %s
                AND timestamp >= NOW() - {interval}
                ORDER BY timestamp DESC
            """.format(interval=interval)
            params = (symbol, timeframe)

        try:
            if not self.conn:
                self._setup_database_connection()

            if not self.conn:
                return {
                    "success": False,
                    "error": "Database connection not available",
                    "timestamp": datetime.now().isoformat()
                }

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Log the actual query being executed
                cur.execute("EXPLAIN " + query, params)
                explain_output = cur.fetchall()
                logger.info(f"Query plan:\n{json.dumps(explain_output, indent=2)}")

                # Execute the actual query
                cur.execute(query, params)
                data = cur.fetchall()

                # Log raw query results
                logger.info(f"Raw query results: {json.dumps(data, default=self.decimal_to_float, indent=2)}")

                if not data:
                    return {
                        "success": True,
                        "data": [],
                        "message": f"No data found for {symbol} at specified time",
                        "timestamp": datetime.now().isoformat()
                    }

                # Convert data to JSON-serializable format
                formatted_data = []
                for row in data:
                    formatted_row = {k: self.decimal_to_float(v) for k, v in dict(row).items()}
                    formatted_data.append(formatted_row)

                # Get the closest record to target time (first record due to time_diff sorting)
                closest_record = formatted_data[0]

                # Calculate statistics using all records in the time window
                highs = [float(row['high']) for row in formatted_data]
                lows = [float(row['low']) for row in formatted_data]
                closes = [float(row['close']) for row in formatted_data]
                volumes = [float(row['volume']) for row in formatted_data]

                stats = {
                    "latest_price": float(closest_record['close']),
                    "price_high": max(highs),
                    "price_low": min(lows),
                    "price_change": closes[0] - closes[-1] if len(closes) > 1 else 0.0,
                    "price_change_percent": ((closes[0] - closes[-1]) / closes[-1] * 100) if len(closes) > 1 else 0.0,
                    "avg_volume": sum(volumes) / len(volumes),
                    "timestamp": closest_record['timestamp'],
                    "interval": closest_record['interval'],
                    "window_size": len(formatted_data)  # Added to show how many records were used
                }

                logger.info(f"Calculated stats from {len(formatted_data)} {timeframe} records in time window")
                logger.info(f"Time window: ±1 hour around {target_time if target_time else 'now'}")
                logger.info(f"Calculated stats: {json.dumps(stats, indent=2)}")

                return {
                    "success": True,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": formatted_data,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            error_msg = f"Error fetching market data: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Test the agent
    agent = ShellExecutorAgent()

    try:
        # Test market data query with specific timestamp
        print("\nTesting market data query with specific timestamp...")
        target_timestamp = "2025-03-20 08:10:00"
        result = agent.get_market_data("BTCUSDT", "1h", target_timestamp)
        print(json.dumps(result, indent=2))

        # Test market data query without specific timestamp
        print("\nTesting market data query without specific timestamp...")
        result = agent.get_market_data("BTCUSDT", "1h")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error during test: {str(e)}")
    finally:
        agent.close()