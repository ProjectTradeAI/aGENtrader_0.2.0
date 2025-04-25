import requests  # Add this import at the top with other imports
import logging
import asyncio
import json
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for CoinAPI requests"""
    def __init__(self, requests_per_second: float = 5):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire rate limit token"""
        async with self.lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            self.last_request_time = time.time()

class MarketDataManager:
    def __init__(self):
        """Initialize the Market Data Manager"""
        try:
            self.api_key = os.getenv("COINAPI_KEY")
            if not self.api_key:
                raise ValueError("COINAPI_KEY environment variable not found")

            self.database_url = os.getenv("DATABASE_URL")
            if not self.database_url:
                raise ValueError("DATABASE_URL environment variable not found")

            self.base_url = "https://rest.coinapi.io/v1"
            self.rate_limiter = RateLimiter(requests_per_second=5)
            self.retry_count = 5
            self.base_retry_delay = 3.0

            # Initialize PostgreSQL connection
            self.engine = create_engine(self.database_url)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

            # Define timeframe configurations
            self.timeframe_config = {
                # High granularity - 7 days
                '1m': {'retention_days': 7, 'coinapi_code': '1MIN'},
                '5m': {'retention_days': 7, 'coinapi_code': '5MIN'},

                # Medium granularity - 30 days
                '15m': {'retention_days': 30, 'coinapi_code': '15MIN'},
                '30m': {'retention_days': 30, 'coinapi_code': '30MIN'},
                '1h': {'retention_days': 30, 'coinapi_code': '1HRS'},

                # Low granularity - 365 days
                '4h': {'retention_days': 365, 'coinapi_code': '4HRS'},
                'D': {'retention_days': 365, 'coinapi_code': '1DAY'}
            }

            logger.info("Market Data Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Market Data Manager: {str(e)}")
            raise

    def _format_symbol(self, symbol: str) -> str:
        """Convert trading pair format for CoinAPI"""
        if symbol != "BTCUSDT":
            raise ValueError("Currently only BTCUSDT is supported")
        return "BINANCE_SPOT_BTC_USDT"

    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp for CoinAPI"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()

    def _validate_market_data(self, data: Dict) -> bool:
        """Validate market data before storage"""
        required_fields = ['time_period_start', 'price_open', 'price_high', 'price_low', 'price_close', 'volume_traded']
        return all(field in data for field in required_fields)

    async def fetch_historical_data(self, symbol: str, interval: str, start_time: datetime, end_time: Optional[datetime] = None) -> bool:
        """Fetch historical kline data with rate limiting and pagination"""
        if not self.api_key:
            raise ValueError("COINAPI_KEY environment variable not found")

        if end_time is None:
            end_time = datetime.now(timezone.utc)

        try:
            # Ensure timezone-aware dates
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            if symbol != "BTCUSDT":
                raise ValueError("Currently only BTCUSDT is supported")

            if interval not in self.timeframe_config:
                raise ValueError(f"Unsupported interval: {interval}")

            formatted_symbol = self._format_symbol(symbol)
            formatted_start = self._format_timestamp(start_time)
            formatted_end = self._format_timestamp(end_time)

            # Log the data fetch attempt
            logger.info(f"Fetching {symbol} {interval} data from {start_time} to {end_time}")

            # Prepare request
            endpoint = f"{self.base_url}/ohlcv/{formatted_symbol}/history"
            headers = {
                'X-CoinAPI-Key': self.api_key,
                'Accept': 'application/json'
            }
            params = {
                'period_id': self.timeframe_config[interval]['coinapi_code'],
                'time_start': formatted_start,
                'time_end': formatted_end,
                'limit': 1000
            }

            retry_count = 0
            while retry_count < self.retry_count:
                try:
                    await self.rate_limiter.acquire()
                    response = requests.get(endpoint, headers=headers, params=params)
                    logger.info(f"Response status: {response.status_code}")

                    if response.status_code == 200:
                        data = response.json()
                        if not data:
                            logger.warning(f"No data returned for {symbol}")
                            return False

                        logger.info(f"Received {len(data)} records")

                        stored_count = 0
                        error_count = 0

                        for ohlcv in data:
                            try:
                                if not self._validate_market_data(ohlcv):
                                    logger.warning(f"Invalid data record: {ohlcv}")
                                    error_count += 1
                                    continue

                                # Parse timestamp with timezone awareness
                                timestamp = datetime.fromisoformat(ohlcv['time_period_start'].replace('Z', '+00:00'))
                                if timestamp.tzinfo is None:
                                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                                # Skip if timestamp is outside our range
                                if timestamp < start_time or timestamp > end_time:
                                    continue

                                try:
                                    # Use SQLAlchemy text() for proper SQL query formatting
                                    insert_query = text("""
                                        INSERT INTO market_data (symbol, interval, timestamp, open, high, low, close, volume, source)
                                        VALUES (:symbol, :interval, :timestamp, :open, :high, :low, :close, :volume, :source)
                                        ON CONFLICT (symbol, interval, timestamp) DO UPDATE SET 
                                            open = EXCLUDED.open,
                                            high = EXCLUDED.high,
                                            low = EXCLUDED.low,
                                            close = EXCLUDED.close,
                                            volume = EXCLUDED.volume,
                                            source = EXCLUDED.source
                                    """)

                                    # Add debug logging
                                    logger.info(f"Inserting record: timestamp={timestamp}, price={float(ohlcv['price_close'])}")

                                    self.session.execute(
                                        insert_query,
                                        {
                                            "symbol": symbol,
                                            "interval": interval,
                                            "timestamp": timestamp,
                                            "open": float(ohlcv['price_open']),
                                            "high": float(ohlcv['price_high']),
                                            "low": float(ohlcv['price_low']),
                                            "close": float(ohlcv['price_close']),
                                            "volume": float(ohlcv['volume_traded']),
                                            "source": "coinapi"
                                        }
                                    )

                                    # Commit after each successful insert
                                    self.session.commit()
                                    stored_count += 1

                                except Exception as e:
                                    # Add error logging
                                    logger.error(f"Error storing record: {str(e)}")
                                    logger.error(f"Failed record data: {json.dumps(ohlcv, default=str)}")
                                    self.session.rollback()
                                    error_count += 1
                                    continue

                            except Exception as e:
                                logger.error(f"Error processing record: {str(e)}")
                                error_count += 1
                                continue

                        # Log detailed results
                        logger.info(f"Processing complete for {symbol} {interval}:")
                        logger.info(f"- Stored: {stored_count} records")
                        logger.info(f"- Errors: {error_count} records")

                        if stored_count > 0:
                            return True
                        elif error_count == len(data):
                            logger.error("All records had errors")
                            return False
                        else:
                            logger.warning("No new records stored")
                            return True

                    elif response.status_code == 429:
                        retry_count += 1
                        retry_delay = self.base_retry_delay * (2 ** retry_count)
                        logger.warning(f"Rate limit hit, waiting {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue

                    else:
                        logger.error(f"API Error: {response.status_code} - {response.text}")
                        return False

                except Exception as e:
                    logger.error(f"Request error: {str(e)}")
                    retry_count += 1
                    if retry_count < self.retry_count:
                        retry_delay = self.base_retry_delay * (2 ** retry_count)
                        logger.warning(f"Request failed, retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Failed after {self.retry_count} attempts")
                        return False

            return False

        except Exception as e:
            logger.error(f"Error in fetch_historical_data: {str(e)}")
            raise

    def get_market_data(self, symbol: str, interval: str, start_time: datetime, end_time: Optional[datetime] = None, optimized: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve market data from database in optimized format.

        Args:
            symbol: Trading pair symbol
            interval: Time interval
            start_time: Start time for data retrieval
            end_time: Optional end time
            optimized: Whether to return data in optimized format (default: True)
        """
        try:
            # Ensure timezone-aware comparison
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time and end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            # Query data
            query = text("""
                SELECT timestamp, open, high, low, close, volume 
                FROM market_data 
                WHERE symbol = :symbol 
                AND interval = :interval 
                AND timestamp >= :start_time
                """ + (" AND timestamp <= :end_time" if end_time else "") + """
                ORDER BY timestamp
            """)

            params = {
                'symbol': symbol,
                'interval': interval,
                'start_time': start_time,
                'end_time': end_time
            } if end_time else {
                'symbol': symbol,
                'interval': interval,
                'start_time': start_time
            }

            result = self.session.execute(query, params)
            rows = result.fetchall()

            if not rows:
                logger.warning(f"No data found for {symbol} {interval} between {start_time} and {end_time}")
                return None

            # Create DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': row[0],
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': float(row[5])
                } for row in rows
            ])

            # Set index and sort
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

            logger.info(f"Retrieved {len(df)} records for {symbol} {interval}")

            if not optimized:
                return df

            # Calculate key metrics for optimized format
            current_price = float(df['close'].iloc[-1])
            daily_change = float(df['close'].pct_change().iloc[-1] * 100)

            # Calculate moving averages
            ma20 = float(df['close'].rolling(window=20).mean().iloc[-1])
            ma50 = float(df['close'].rolling(window=50).mean().iloc[-1])
            ma200 = float(df['close'].rolling(window=200).mean().iloc[-1])

            # Calculate RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = float(100 - (100 / (1 + rs)).iloc[-1])

            # Volume analysis
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume'].rolling(window=20).mean().iloc[-1])
            volume_trend = float(df['volume'].pct_change().rolling(window=20).mean().iloc[-1] * 100)

            # Price channels
            high_channel = float(df['high'].rolling(window=20).max().iloc[-1])
            low_channel = float(df['low'].rolling(window=20).min().iloc[-1])

            # Return optimized format
            return {
                "symbol": symbol,
                "timestamp": df.index[-1].isoformat(),
                "price_metrics": {
                    "current": current_price,
                    "daily_change_percent": daily_change,
                    "high_24h": float(df['high'].tail(24).max()),
                    "low_24h": float(df['low'].tail(24).min())
                },
                "technical_signals": {
                    "trend": {
                        "ma20": ma20,
                        "ma50": ma50,
                        "ma200": ma200,
                        "price_vs_ma20": current_price / ma20 - 1,
                        "ma20_vs_ma50": ma20 / ma50 - 1
                    },
                    "momentum": {
                        "rsi": rsi,
                        "price_channels": {
                            "upper": high_channel,
                            "lower": low_channel
                        }
                    },
                    "volume": {
                        "current": current_volume,
                        "average": avg_volume,
                        "trend": volume_trend
                    }
                },
                "key_levels": {
                    "support": [
                        float(low_channel),
                        float(df['low'].quantile(0.25))
                    ],
                    "resistance": [
                        float(high_channel),
                        float(df['high'].quantile(0.75))
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Error retrieving market data: {str(e)}")
            return None

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.session:
                self.session.close()
            logger.info("Cleaned up resources")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")