
from typing import Optional
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_historical_market_data(symbol: str, interval: str = "1h", lookback_days: int = 30) -> str:
    """Get historical market data with technical indicators"""
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('PGDATABASE'),
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            host=os.environ.get('PGHOST'),
            port=os.environ.get('PGPORT')
        )

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT 
                    timestamp,
                    symbol,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    source,
                    interval
                FROM market_data 
                WHERE symbol = %s
                    AND interval = %s
                    AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            ''', (symbol, interval, lookback_days))

            data = cur.fetchall()

            if not data:
                return json.dumps({
                    "error": f"No data found for {symbol} with {interval} interval"
                })

            # Convert to DataFrame for calculations
            df = pd.DataFrame(data)

            # Calculate basic technical indicators
            # Moving averages
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma50'] = df['close'].rolling(window=50).mean()
            df['ma200'] = df['close'].rolling(window=200).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # Volume Analysis
            df['avg_volume'] = df['volume'].rolling(window=20).mean()
            df['volume_change'] = df['volume'].pct_change()

            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_upper'] = df['bb_middle'] + 2 * df['close'].rolling(window=20).std()
            df['bb_lower'] = df['bb_middle'] - 2 * df['close'].rolling(window=20).std()

            # Convert DataFrame back to dict format
            latest = df.iloc[-1].to_dict()
            historical = df.to_dict(orient='records')

            # Format response
            response = {
                "symbol": symbol,
                "interval": interval,
                "current_data": {
                    "timestamp": str(latest['timestamp']),
                    "price": float(latest['close']),
                    "open": float(latest['open']),
                    "high": float(latest['high']),
                    "low": float(latest['low']),
                    "volume": float(latest['volume'])
                },
                "technical_indicators": {
                    "moving_averages": {
                        "ma20": float(latest['ma20']) if not pd.isna(latest['ma20']) else None,
                        "ma50": float(latest['ma50']) if not pd.isna(latest['ma50']) else None,
                        "ma200": float(latest['ma200']) if not pd.isna(latest['ma200']) else None
                    },
                    "rsi": float(latest['rsi']) if not pd.isna(latest['rsi']) else None,
                    "volume_analysis": {
                        "current_volume": float(latest['volume']),
                        "average_volume": float(latest['avg_volume']) if not pd.isna(latest['avg_volume']) else None,
                        "volume_change": float(latest['volume_change']) if not pd.isna(latest['volume_change']) else None
                    },
                    "bollinger_bands": {
                        "upper": float(latest['bb_upper']) if not pd.isna(latest['bb_upper']) else None,
                        "middle": float(latest['bb_middle']) if not pd.isna(latest['bb_middle']) else None,
                        "lower": float(latest['bb_lower']) if not pd.isna(latest['bb_lower']) else None
                    }
                },
                "historical_data": [
                    {
                        "timestamp": str(row['timestamp']),
                        "close": float(row['close']),
                        "volume": float(row['volume'])
                    } for row in historical[-50:]  # Last 50 data points
                ]
            }

            return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error getting market data: {str(e)}"})
