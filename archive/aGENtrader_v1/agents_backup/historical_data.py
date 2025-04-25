"""
Historical Data Collection Agent

Responsible for fetching and storing historical market data
across multiple timeframes within CoinGecko's API limitations.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np
from decimal import Decimal
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import time

class HistoricalDataCollector:
    def __init__(self):
        """Initialize the Historical Data Collector"""
        self.name = "Historical Data Collector"
        self._setup_coingecko_client()
        self._setup_database_connection()

        # Define timeframes and their configurations
        self.timeframes = {
            "1h": {"days": "90"},  # Maximum days for hourly data
            "4h": {"days": "90"},  # Will be resampled from hourly
            "1d": {"days": "365"}, # Maximum days for daily data
            "1w": {"days": "365"}  # Will be resampled from daily
        }

    def _setup_coingecko_client(self):
        """Setup CoinGecko API client"""
        try:
            self.cg_client = CoinGeckoAPI()
            # Test the connection
            self.cg_client.ping()
            print("Successfully connected to CoinGecko API")
        except Exception as e:
            print(f"CoinGecko setup failed: {str(e)}")
            raise

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
            print("Successfully connected to PostgreSQL database")
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise

    async def fetch_historical_data(self, coin_id: str = "bitcoin", timeframe: str = "1d") -> Optional[List[Dict]]:
        """
        Fetch historical data from CoinGecko with proper handling of API limitations

        Args:
            coin_id: CoinGecko coin ID (default: "bitcoin")
            timeframe: Data timeframe ("1h", "4h", "1d", "1w")
        """
        try:
            # Respect rate limits
            time.sleep(1.2)  # CoinGecko rate limit: 50 calls/minute

            config = self.timeframes.get(timeframe)
            if not config:
                print(f"Invalid timeframe: {timeframe}")
                return None

            # For hourly data (including 4h which we'll resample)
            if timeframe in ["1h", "4h"]:
                data = self.cg_client.get_coin_market_chart_by_id(
                    id=coin_id,
                    vs_currency="usd",
                    days=config["days"]
                )
            # For daily and weekly data
            else:
                data = self.cg_client.get_coin_market_chart_by_id(
                    id=coin_id,
                    vs_currency="usd",
                    days=config["days"],
                    interval="daily"
                )

            if not data:
                print(f"No data returned for {coin_id}")
                return None

            # Process the data into a structured format
            processed_data = []
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            total_volumes = data.get('total_volumes', [])

            for i in range(len(prices)):
                timestamp = datetime.fromtimestamp(prices[i][0] / 1000)  # Convert milliseconds to datetime
                processed_data.append({
                    'timestamp': timestamp,
                    'price': float(prices[i][1]),
                    'market_cap': float(market_caps[i][1]) if i < len(market_caps) else None,
                    'volume': float(total_volumes[i][1]) if i < len(total_volumes) else None
                })

            # For 4h timeframe, resample hourly data
            if timeframe == "4h":
                df = pd.DataFrame(processed_data)
                df.set_index('timestamp', inplace=True)
                df = df.resample('4H').agg({
                    'price': 'last',
                    'market_cap': 'last',
                    'volume': 'sum'
                }).reset_index()
                processed_data = df.to_dict('records')
            # For weekly timeframe, resample daily data
            elif timeframe == "1w":
                df = pd.DataFrame(processed_data)
                df.set_index('timestamp', inplace=True)
                df = df.resample('W').agg({
                    'price': 'last',
                    'market_cap': 'last',
                    'volume': 'sum'
                }).reset_index()
                processed_data = df.to_dict('records')

            return processed_data

        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return None

    async def store_historical_data(self, data: List[Dict], symbol: str, timeframe: str):
        """Store historical data in PostgreSQL database"""
        if not self.conn:
            print("Database connection not initialized")
            return

        try:
            with self.conn.cursor() as cur:
                # Store the raw historical data
                execute_batch(cur, """
                    INSERT INTO historical_market_data 
                    (timestamp, symbol, price, volume, market_cap, timeframe)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (timestamp, symbol, timeframe) DO UPDATE
                    SET price = EXCLUDED.price,
                        volume = EXCLUDED.volume,
                        market_cap = EXCLUDED.market_cap
                """, [
                    (
                        entry['timestamp'],
                        symbol,
                        entry['price'],
                        entry['volume'],
                        entry['market_cap'],
                        timeframe
                    )
                    for entry in data
                ])

            self.conn.commit()
            print(f"Successfully stored {len(data)} records for timeframe {timeframe}")
        except Exception as e:
            print(f"Error storing historical data: {str(e)}")
            self.conn.rollback()

    async def collect_btc_history(self):
        """Collect BTC historical data for all timeframes"""
        for timeframe in self.timeframes.keys():
            print(f"\nFetching {timeframe} data...")
            data = await self.fetch_historical_data(
                coin_id="bitcoin",
                timeframe=timeframe
            )

            if data:
                await self.store_historical_data(data, "BTC", timeframe)
            else:
                print(f"No data available for timeframe {timeframe}")

            # Respect rate limits
            time.sleep(2)

    def get_available_data_info(self):
        """Get information about available historical data"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT timeframe, 
                           MIN(timestamp) as earliest_date,
                           MAX(timestamp) as latest_date,
                           COUNT(*) as record_count
                    FROM historical_market_data
                    WHERE symbol = 'BTC'
                    GROUP BY timeframe
                    ORDER BY timeframe
                """)
                results = cur.fetchall()

                print("\nAvailable Historical Data:")
                for row in results:
                    print(f"Timeframe: {row[0]}")
                    print(f"  Earliest Date: {row[1]}")
                    print(f"  Latest Date: {row[2]}")
                    print(f"  Total Records: {row[3]}\n")

        except Exception as e:
            print(f"Error getting data info: {str(e)}")

if __name__ == "__main__":
    import asyncio

    async def main():
        collector = HistoricalDataCollector()
        await collector.collect_btc_history()
        collector.get_available_data_info()

    asyncio.run(main())