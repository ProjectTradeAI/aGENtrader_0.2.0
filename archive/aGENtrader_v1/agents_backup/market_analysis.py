"""
Market Analysis Agent

Responsible for analyzing real-time market data, identifying trends,
and providing signals to the trading system.
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
import ta
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumePriceTrendIndicator
import ccxt
import time
from enum import Enum, auto

class SignalStrength(Enum):
    STRONG_BUY = auto()
    BUY = auto()
    NEUTRAL = auto()
    SELL = auto()
    STRONG_SELL = auto()
    
class TimeFrame(Enum):
    MINUTES_5 = "5m"
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"

class MarketAnalysisAgent:
    def __init__(self, config_path="config/settings.json"):
        """Initialize the Market Analysis Agent"""
        self.name = "Market Analysis Agent"
        self.config = self._load_config(config_path)
        self.use_simulation = False
        
        # Setup data sources
        self._setup_coingecko_client()
        self._setup_exchange_clients()
        self._setup_database_connection()
        
        self.last_prices = {}  # For price simulation continuity
        self.signal_history = {}  # Track signal effectiveness
        self.candle_data = {}  # Store candle data by symbol and timeframe

        # CoinGecko ID mappings
        self.symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "MATIC": "matic-network"
        }
        
        # Exchange symbol mappings
        self.exchange_symbol_map = {
            "BTC": "BTC/USDT",
            "ETH": "ETH/USDT",
            "SOL": "SOL/USDT",
            "MATIC": "MATIC/USDT"
        }

    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Using default settings.")
            return {
                "analysis_window": 24,
                "data_sources": ["coingecko"],
                "symbols": ["BTC", "ETH", "SOL", "MATIC"]
            }

    def _setup_coingecko_client(self):
        """Setup CoinGecko API client"""
        try:
            self.cg_client = CoinGeckoAPI()
            # Test the connection
            self.cg_client.ping()
            print("Successfully connected to CoinGecko API")
            self.use_simulation = False
        except Exception as e:
            print(f"CoinGecko setup failed: {str(e)}")
            self.use_simulation = True
            
    def _setup_exchange_clients(self):
        """Setup exchange API clients"""
        self.exchanges = {}
        try:
            # Setup Binance client
            if "binance" in self.config.get("exchanges", []):
                self.exchanges["binance"] = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future'  # Use futures for better data
                    }
                })
                print("Successfully connected to Binance API")
                
            # Setup Coinbase client
            if "coinbase" in self.config.get("exchanges", []):
                self.exchanges["coinbase"] = ccxt.coinbasepro({
                    'enableRateLimit': True
                })
                print("Successfully connected to Coinbase API")
                
            # Setup Kraken client
            if "kraken" in self.config.get("exchanges", []):
                self.exchanges["kraken"] = ccxt.kraken({
                    'enableRateLimit': True
                })
                print("Successfully connected to Kraken API")
                
        except Exception as e:
            print(f"Exchange setup failed: {str(e)}")
            # Will fall back to CoinGecko or simulation

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
            self.conn = None

    def _simulate_market_data(self, symbol: str) -> Dict[str, Any]:
        """Generate realistic simulated market data"""
        if symbol not in self.last_prices:
            base_prices = {
                "BTC": 45000,
                "ETH": 2500,
                "SOL": 100,
                "MATIC": 1.5
            }
            self.last_prices[symbol] = base_prices.get(symbol, 1000)

        price_volatility = 0.02  # 2% volatility
        price_change = np.random.normal(0, price_volatility)
        new_price = float(self.last_prices[symbol] * (1 + price_change))

        # Store last price for next simulation
        last_price = float(self.last_prices[symbol])
        self.last_prices[symbol] = new_price

        # Generate realistic volume
        base_volume = new_price * 100
        volume = abs(np.random.normal(base_volume, base_volume * 0.3))

        price_change = new_price - last_price
        price_change_percent = (price_change / last_price) * 100

        return {
            "symbol": symbol,
            "price": new_price,
            "volume": float(volume),
            "timestamp": datetime.now(),
            "source": "simulation",
            "metadata": {
                "24h_high": float(new_price * 1.05),
                "24h_low": float(new_price * 0.95),
                "24h_volume": float(volume * 24),
                "price_change": float(price_change),
                "price_change_percent": float(price_change_percent)
            }
        }

    async def fetch_market_data(self, symbol: str = "BTC") -> Optional[Dict[str, Any]]:
        """Fetch market data from multiple sources with cascade fallback"""
        # Try primary exchange first (if available)
        if self.exchanges:
            try:
                exchange_name = next(iter(self.exchanges.keys()))  # Get first exchange
                exchange = self.exchanges[exchange_name]
                
                exchange_symbol = self.exchange_symbol_map.get(symbol)
                if not exchange_symbol:
                    raise ValueError(f"No exchange symbol mapping for {symbol}")
                
                ticker = exchange.fetch_ticker(exchange_symbol)
                orderbook = exchange.fetch_order_book(exchange_symbol, limit=20)
                
                # Calculate bid-ask spread
                best_bid = orderbook['bids'][0][0] if orderbook['bids'] else None
                best_ask = orderbook['asks'][0][0] if orderbook['asks'] else None
                spread = ((best_ask - best_bid) / best_bid) * 100 if best_bid and best_ask else None
                
                # Calculate order book imbalance (buy pressure vs. sell pressure)
                bid_volume = sum(bid[1] for bid in orderbook['bids'][:10])
                ask_volume = sum(ask[1] for ask in orderbook['asks'][:10])
                book_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
                
                processed_data = {
                    "symbol": symbol,
                    "price": float(ticker['last']),
                    "volume": float(ticker['quoteVolume'] if 'quoteVolume' in ticker else ticker['baseVolume']),
                    "timestamp": datetime.now(),
                    "source": exchange_name,
                    "metadata": {
                        "24h_high": float(ticker['high']),
                        "24h_low": float(ticker['low']),
                        "24h_volume": float(ticker['quoteVolume'] if 'quoteVolume' in ticker else ticker['baseVolume']),
                        "price_change": float(ticker['last'] - ticker['open']) if 'open' in ticker else None,
                        "price_change_percent": float(ticker['percentage']) if 'percentage' in ticker else None,
                        "bid": float(best_bid) if best_bid else None,
                        "ask": float(best_ask) if best_ask else None,
                        "spread": float(spread) if spread else None,
                        "book_imbalance": float(book_imbalance)
                    }
                }
                
                await self._store_market_data(processed_data)
                return processed_data
                
            except Exception as e:
                print(f"Error fetching from {exchange_name}, trying CoinGecko: {str(e)}")
        
        # Try CoinGecko as fallback
        if not self.use_simulation:
            try:
                coin_id = self.symbol_to_id.get(symbol)
                if not coin_id:
                    raise ValueError(f"No CoinGecko ID mapping for symbol: {symbol}")

                data = self.cg_client.get_coin_by_id(
                    coin_id,
                    localization=False,
                    tickers=True,
                    market_data=True,
                    community_data=False,
                    developer_data=False,
                    sparkline=False
                )

                market_data = data['market_data']
                price = float(market_data['current_price']['usd'])
                volume = float(market_data['total_volume']['usd'])

                processed_data = {
                    "symbol": symbol,
                    "price": price,
                    "volume": volume,
                    "timestamp": datetime.now(),
                    "source": "coingecko",
                    "metadata": {
                        "24h_high": float(market_data['high_24h']['usd']),
                        "24h_low": float(market_data['low_24h']['usd']),
                        "24h_volume": float(volume),
                        "price_change": float(market_data['price_change_24h']),
                        "price_change_percent": float(market_data['price_change_percentage_24h'])
                    }
                }

                await self._store_market_data(processed_data)
                return processed_data

            except Exception as e:
                print(f"Error fetching from CoinGecko, falling back to simulation: {str(e)}")
                
        # Use simulation as last resort
        data = self._simulate_market_data(symbol)
        if data:
            await self._store_market_data(data)
            
        return data

    async def _store_market_data(self, data: Dict[str, Any]):
        """Store market data in PostgreSQL database"""
        if not self.conn:
            print("Database connection not initialized")
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO market_data 
                    (symbol, price, volume, timestamp, source, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    data['symbol'],
                    float(data['price']),
                    float(data['volume']),
                    data['timestamp'],
                    data['source'],
                    json.dumps(data['metadata'])
                ))
            self.conn.commit()
        except Exception as e:
            print(f"Error storing market data: {str(e)}")
            self.conn.rollback()

    async def fetch_historical_data(self, symbol: str, timeframe: TimeFrame = TimeFrame.HOUR_1, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch historical candle data for a symbol from exchange or database"""
        try:
            # Try to get from exchange first
            if self.exchanges:
                exchange_name = next(iter(self.exchanges.keys()))
                exchange = self.exchanges[exchange_name]
                
                exchange_symbol = self.exchange_symbol_map.get(symbol)
                if not exchange_symbol:
                    raise ValueError(f"No exchange symbol mapping for {symbol}")
                
                # Convert timeframe to exchange format
                timeframe_str = timeframe.value
                
                candles = exchange.fetch_ohlcv(
                    exchange_symbol, 
                    timeframe=timeframe_str,
                    limit=limit
                )
                
                if candles:
                    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    # Cache the data
                    cache_key = f"{symbol}_{timeframe_str}"
                    self.candle_data[cache_key] = df
                    return df
            
            # Fall back to database
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, open, high, low, price as close, volume
                    FROM market_data 
                    WHERE symbol = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (symbol, limit))
                data = cur.fetchall()
                
                if data:
                    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    return df
                
            # If we reach here, we don't have data from any source
            return None
                
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return None
    
    async def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators on price data"""
        if df is None or len(df) < 20:
            return None
            
        # Make sure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            return None
            
        # Copy to avoid modifying original
        df_indicators = df.copy()
        
        # Trend indicators
        df_indicators['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
        df_indicators['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
        df_indicators['ema_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
        df_indicators['ema_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()
        
        # MACD
        macd = MACD(close=df['close'])
        df_indicators['macd'] = macd.macd()
        df_indicators['macd_signal'] = macd.macd_signal()
        df_indicators['macd_diff'] = macd.macd_diff()
        
        # Momentum indicators
        df_indicators['rsi'] = RSIIndicator(close=df['close']).rsi()
        
        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
        df_indicators['stoch_k'] = stoch.stoch()
        df_indicators['stoch_d'] = stoch.stoch_signal()
        
        # Volatility indicators
        bb = BollingerBands(close=df['close'])
        df_indicators['bb_high'] = bb.bollinger_hband()
        df_indicators['bb_low'] = bb.bollinger_lband()
        df_indicators['bb_mid'] = bb.bollinger_mavg()
        df_indicators['bb_width'] = (df_indicators['bb_high'] - df_indicators['bb_low']) / df_indicators['bb_mid']
        
        df_indicators['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
        
        # Volume indicators
        df_indicators['obv'] = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()
        df_indicators['vpt'] = VolumePriceTrendIndicator(close=df['close'], volume=df['volume']).volume_price_trend()
        
        # Add more indicators as needed
        
        return df_indicators

    async def analyze_trends(self, symbol: str = "BTC", timeframe: TimeFrame = TimeFrame.HOUR_1) -> Optional[Dict[str, Any]]:
        """Analyze market trends using technical indicators"""
        # Get latest market data
        market_data = await self.fetch_market_data(symbol)
        if not market_data:
            return None
            
        # Get historical data
        df = await self.fetch_historical_data(symbol, timeframe)
        if df is None or len(df) < 20:
            return {
                "symbol": symbol,
                "current_price": float(market_data['price']),
                "trend": "neutral",
                "confidence": 50.0,
                "support_level": float(market_data['price']) * 0.95,
                "resistance_level": float(market_data['price']) * 1.05,
                "timestamp": datetime.now().isoformat(),
                "message": "Insufficient historical data for analysis"
            }
        
        # Calculate indicators
        df_indicators = await self.calculate_technical_indicators(df)
        if df_indicators is None:
            return None
            
        current_price = float(market_data['price'])
        
        # Get latest indicator values
        latest = df_indicators.iloc[-1]
        
        # Calculate trend signals and scores
        signals = []
        
        # MACD signal (strong)
        if latest['macd_diff'] > 0 and df_indicators.iloc[-2]['macd_diff'] <= 0:
            signals.append({"indicator": "MACD", "signal": SignalStrength.BUY, "weight": 3})
        elif latest['macd_diff'] < 0 and df_indicators.iloc[-2]['macd_diff'] >= 0:
            signals.append({"indicator": "MACD", "signal": SignalStrength.SELL, "weight": 3})
        elif latest['macd_diff'] > 0:
            signals.append({"indicator": "MACD", "signal": SignalStrength.NEUTRAL, "weight": 1})
        else:
            signals.append({"indicator": "MACD", "signal": SignalStrength.NEUTRAL, "weight": 1})
        
        # RSI signals
        if latest['rsi'] < 30:
            signals.append({"indicator": "RSI", "signal": SignalStrength.STRONG_BUY, "weight": 2})
        elif latest['rsi'] < 40:
            signals.append({"indicator": "RSI", "signal": SignalStrength.BUY, "weight": 1})
        elif latest['rsi'] > 70:
            signals.append({"indicator": "RSI", "signal": SignalStrength.STRONG_SELL, "weight": 2})
        elif latest['rsi'] > 60:
            signals.append({"indicator": "RSI", "signal": SignalStrength.SELL, "weight": 1})
        else:
            signals.append({"indicator": "RSI", "signal": SignalStrength.NEUTRAL, "weight": 1})
        
        # Moving averages crossover
        if latest['sma_20'] > latest['sma_50'] and df_indicators.iloc[-2]['sma_20'] <= df_indicators.iloc[-2]['sma_50']:
            signals.append({"indicator": "SMA Cross", "signal": SignalStrength.BUY, "weight": 2})
        elif latest['sma_20'] < latest['sma_50'] and df_indicators.iloc[-2]['sma_20'] >= df_indicators.iloc[-2]['sma_50']:
            signals.append({"indicator": "SMA Cross", "signal": SignalStrength.SELL, "weight": 2})
        
        # Price relative to Bollinger Bands
        if current_price < latest['bb_low']:
            signals.append({"indicator": "Bollinger", "signal": SignalStrength.STRONG_BUY, "weight": 2})
        elif current_price > latest['bb_high']:
            signals.append({"indicator": "Bollinger", "signal": SignalStrength.STRONG_SELL, "weight": 2})
        
        # Stochastic oscillator
        if latest['stoch_k'] < 20 and latest['stoch_d'] < 20:
            signals.append({"indicator": "Stochastic", "signal": SignalStrength.BUY, "weight": 1})
        elif latest['stoch_k'] > 80 and latest['stoch_d'] > 80:
            signals.append({"indicator": "Stochastic", "signal": SignalStrength.SELL, "weight": 1})
        
        # Calculate weighted score
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        for signal in signals:
            weight = signal["weight"]
            total_weight += weight
            
            if signal["signal"] == SignalStrength.STRONG_BUY:
                buy_score += weight * 2
            elif signal["signal"] == SignalStrength.BUY:
                buy_score += weight
            elif signal["signal"] == SignalStrength.STRONG_SELL:
                sell_score += weight * 2
            elif signal["signal"] == SignalStrength.SELL:
                sell_score += weight
        
        # Normalize scores
        if total_weight > 0:
            buy_score = (buy_score / total_weight) * 100
            sell_score = (sell_score / total_weight) * 100
        
        # Calculate overall trend and confidence
        if buy_score > sell_score:
            confidence = buy_score
            if confidence > 70:
                trend = "strongly_bullish"
            else:
                trend = "bullish"
        elif sell_score > buy_score:
            confidence = sell_score
            if confidence > 70:
                trend = "strongly_bearish"
            else:
                trend = "bearish"
        else:
            trend = "neutral"
            confidence = 50
        
        # Calculate support and resistance levels using Bollinger Bands and recent price action
        support_level = max(latest['bb_low'], df['low'].rolling(10).min().iloc[-1])
        resistance_level = min(latest['bb_high'], df['high'].rolling(10).max().iloc[-1])
        
        # Calculate trading signal based on trend
        if trend == "strongly_bullish":
            signal = "strong_buy"
        elif trend == "bullish":
            signal = "buy"
        elif trend == "strongly_bearish":
            signal = "strong_sell"
        elif trend == "bearish":
            signal = "sell"
        else:
            signal = "hold"
            
        # Prepare detailed indicator analysis
        indicator_analysis = {}
        for key in ['macd', 'rsi', 'sma_20', 'sma_50', 'bb_high', 'bb_low', 'stoch_k', 'stoch_d']:
            if key in latest:
                indicator_analysis[key] = float(latest[key])
        
        analysis = {
            "symbol": symbol,
            "timeframe": timeframe.value,
            "current_price": current_price,
            "trend": trend,
            "confidence": round(confidence, 2),
            "signal": signal,
            "support_level": round(float(support_level), 2),
            "resistance_level": round(float(resistance_level), 2),
            "indicators": indicator_analysis,
            "signals": [{"indicator": s["indicator"], "signal": s["signal"].name} for s in signals],
            "timestamp": datetime.now().isoformat()
        }

        # Store the analysis and update signal history
        await self._store_technical_indicators(symbol, current_price, analysis)
        return analysis

    async def detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect common chart patterns in price data"""
        patterns = []
        
        if df is None or len(df) < 30:
            return patterns
            
        # Helper function to check if a series forms a peak or trough
        def is_peak(series, i):
            return series.iloc[i] > series.iloc[i-1] and series.iloc[i] > series.iloc[i+1]
            
        def is_trough(series, i):
            return series.iloc[i] < series.iloc[i-1] and series.iloc[i] < series.iloc[i+1]
        
        # Head and Shoulders pattern detection
        try:
            # Need at least 30 bars for this pattern
            if len(df) >= 30:
                close = df['close']
                peaks = []
                
                # Find the peaks
                for i in range(1, len(close)-1):
                    if is_peak(close, i):
                        peaks.append((i, close.iloc[i]))
                
                if len(peaks) >= 3:
                    # Look for head and shoulders pattern (3 peaks with middle one higher)
                    for i in range(len(peaks)-2):
                        left = peaks[i]
                        middle = peaks[i+1]
                        right = peaks[i+2]
                        
                        # Check if middle peak is higher
                        if middle[1] > left[1] and middle[1] > right[1]:
                            # Check if left and right are similar height (within 10%)
                            if abs(left[1] - right[1])/left[1] < 0.1:
                                patterns.append({
                                    "pattern": "head_and_shoulders",
                                    "signal": "bearish",
                                    "confidence": 70,
                                    "description": "Head and shoulders top pattern detected - bearish reversal signal"
                                })
                                break
        except Exception as e:
            print(f"Error in head and shoulders detection: {str(e)}")
        
        # Double Bottom pattern detection
        try:
            if len(df) >= 20:
                close = df['close']
                troughs = []
                
                # Find the troughs
                for i in range(1, len(close)-1):
                    if is_trough(close, i):
                        troughs.append((i, close.iloc[i]))
                
                if len(troughs) >= 2:
                    # Look for double bottom (two troughs at similar price levels)
                    for i in range(len(troughs)-1):
                        first = troughs[i]
                        second = troughs[i+1]
                        
                        # Check if both troughs are at similar levels (within 3%)
                        if abs(first[1] - second[1])/first[1] < 0.03:
                            # Make sure they're not too close together
                            if second[0] - first[0] >= 5:
                                patterns.append({
                                    "pattern": "double_bottom",
                                    "signal": "bullish",
                                    "confidence": 80,
                                    "description": "Double bottom pattern detected - bullish reversal signal"
                                })
                                break
        except Exception as e:
            print(f"Error in double bottom detection: {str(e)}")
        
        # Check for bullish engulfing pattern
        try:
            for i in range(1, len(df)-1):
                # Current bar must be green (close > open)
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    # Previous bar must be red (open > close)
                    if df['open'].iloc[i-1] > df['close'].iloc[i-1]:
                        # Current bar must engulf previous bar
                        if (df['open'].iloc[i] <= df['close'].iloc[i-1] and 
                            df['close'].iloc[i] >= df['open'].iloc[i-1]):
                            patterns.append({
                                "pattern": "bullish_engulfing",
                                "signal": "bullish",
                                "confidence": 65,
                                "description": "Bullish engulfing candle pattern detected"
                            })
                            break
        except Exception as e:
            print(f"Error in engulfing pattern detection: {str(e)}")
        
        return patterns
    
    async def _store_technical_indicators(self, symbol: str, current_price: float, analysis=None):
        """Store technical indicators and analysis in the database"""
        if not self.conn:
            return

        try:
            with self.conn.cursor() as cur:
                # Store basic SMA
                cur.execute("""
                    SELECT AVG(price::float) 
                    FROM (
                        SELECT price 
                        FROM market_data 
                        WHERE symbol = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 20
                    ) as recent_prices
                """, (symbol,))
                sma = cur.fetchone()[0]

                if sma is not None:
                    cur.execute("""
                        INSERT INTO technical_indicators 
                        (symbol, indicator, value, parameters, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        symbol,
                        'sma',
                        float(sma),
                        json.dumps({"period": 20}),
                        datetime.now()
                    ))
                    
                # Store full analysis if provided
                if analysis:
                    cur.execute("""
                        INSERT INTO analysis_results
                        (symbol, trend, confidence, signal, support_level, resistance_level, data, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        symbol,
                        analysis['trend'],
                        analysis['confidence'],
                        analysis['signal'],
                        analysis['support_level'],
                        analysis['resistance_level'],
                        json.dumps(analysis),
                        datetime.now()
                    ))

            self.conn.commit()
        except Exception as e:
            print(f"Error storing technical indicators: {str(e)}")
            self.conn.rollback()
    
    async def analyze_multiple_timeframes(self, symbol: str) -> Dict[str, Any]:
        """Analyze a symbol across multiple timeframes for a comprehensive view"""
        timeframes = [TimeFrame.MINUTES_15, TimeFrame.HOUR_1, TimeFrame.HOUR_4, TimeFrame.DAY_1]
        results = {}
        
        for tf in timeframes:
            analysis = await self.analyze_trends(symbol, tf)
            if analysis:
                results[tf.value] = analysis
        
        # Determine overall signal based on weighted timeframe analysis
        weights = {
            TimeFrame.MINUTES_15.value: 0.1,
            TimeFrame.HOUR_1.value: 0.2,
            TimeFrame.HOUR_4.value: 0.3,
            TimeFrame.DAY_1.value: 0.4
        }
        
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        for tf, analysis in results.items():
            if tf in weights:
                weight = weights[tf]
                total_weight += weight
                
                if analysis['signal'] == 'strong_buy':
                    buy_score += weight * 2
                elif analysis['signal'] == 'buy':
                    buy_score += weight
                elif analysis['signal'] == 'strong_sell':
                    sell_score += weight * 2
                elif analysis['signal'] == 'sell':
                    sell_score += weight
        
        # Normalize and determine overall signal
        if total_weight > 0:
            buy_score = buy_score / total_weight
            sell_score = sell_score / total_weight
            
            if buy_score > sell_score:
                if buy_score > 1.5:
                    overall_signal = 'strong_buy'
                else:
                    overall_signal = 'buy'
                confidence = buy_score * 50  # Scale to 0-100
            elif sell_score > buy_score:
                if sell_score > 1.5:
                    overall_signal = 'strong_sell'
                else:
                    overall_signal = 'sell'
                confidence = sell_score * 50  # Scale to 0-100
            else:
                overall_signal = 'hold'
                confidence = 50
        else:
            overall_signal = 'hold'
            confidence = 50
            
        # Format the final comprehensive result
        comprehensive_result = {
            "symbol": symbol,
            "overall_signal": overall_signal,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().isoformat(),
            "timeframe_analysis": results
        }
        
        return comprehensive_result

    async def get_latest_analysis(self, symbol: str = "BTC", multi_timeframe: bool = False) -> Optional[Dict[str, Any]]:
        """Get the latest analysis for a symbol"""
        if multi_timeframe:
            return await self.analyze_multiple_timeframes(symbol)
        else:
            return await self.analyze_trends(symbol)

async def main():
    """Test the agent"""
    agent = MarketAnalysisAgent()
    print("\n===== SINGLE TIMEFRAME ANALYSIS =====")
    for symbol in ["BTC", "ETH", "SOL", "MATIC"]:
        result = await agent.analyze_trends(symbol)
        print(f"\nAnalysis result for {symbol}:")
        print(f"  Price: ${result['current_price']:.2f}")
        print(f"  Trend: {result['trend']}")
        print(f"  Signal: {result['signal']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Support: ${result['support_level']}")
        print(f"  Resistance: ${result['resistance_level']}")
        print("  Indicator Signals:")
        for signal in result['signals']:
            print(f"    - {signal['indicator']}: {signal['signal']}")
    
    print("\n===== MULTI-TIMEFRAME ANALYSIS =====")
    symbol = "BTC"
    result = await agent.analyze_multiple_timeframes(symbol)
    print(f"\nComprehensive analysis for {symbol}:")
    print(f"  Overall Signal: {result['overall_signal']}")
    print(f"  Confidence: {result['confidence']}%")
    print("  Timeframe breakdown:")
    for tf, analysis in result['timeframe_analysis'].items():
        print(f"    - {tf}: {analysis['signal']} (confidence: {analysis['confidence']}%)")

if __name__ == "__main__":
    asyncio.run(main())
"""
Market Analysis Agent

Analyzes market data and technical indicators to generate trading signals.
"""

import json
import random
from datetime import datetime
import os

class MarketAnalysisAgent:
    def __init__(self, market_data=None):
        """Initialize the Market Analysis Agent"""
        self.name = "Market Analysis Agent"
        self.supported_indicators = ["RSI", "MACD", "Bollinger", "SMA", "EMA"]
        self.supported_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        self.data_cache = {}
        self.market_data = market_data
        
        # Create data directory if it doesn't exist
        os.makedirs("data/market_data", exist_ok=True)

    async def analyze_trends(self, symbol, timeframe="1h"):
        """
        Analyze market trends for a given symbol
        
        Args:
            symbol (str): The trading pair to analyze (e.g., "BTCUSDT")
            timeframe (str): Timeframe for analysis (e.g., "1h")
            
        Returns:
            dict: Analysis results including trend, support/resistance levels, and trading signals
        """
        # In a real implementation, this would fetch actual market data
        # For this demonstration, we'll generate simulated analysis
        
        print(f"Analyzing {symbol} on {timeframe} timeframe...")
        
        # Simulated trend analysis
        trends = ["bullish", "bearish", "neutral", "strongly_bullish", "strongly_bearish"]
        trend = random.choice(trends)
        
        # Confidence level (50-95%)
        confidence = random.randint(50, 95)
        
        # Generate support and resistance levels
        current_price = self._get_current_price(symbol)
        support_levels = [
            round(current_price * (1 - random.uniform(0.01, 0.05)), 2)
            for _ in range(3)
        ]
        resistance_levels = [
            round(current_price * (1 + random.uniform(0.01, 0.05)), 2)
            for _ in range(3)
        ]
        
        # Simulated indicators
        rsi = random.randint(0, 100)
        macd_line = random.uniform(-2, 2)
        signal_line = random.uniform(-2, 2)
        macd_histogram = macd_line - signal_line
        
        # Generate trading signal based on trend
        if trend in ["bullish", "strongly_bullish"]:
            signal = "buy"
        elif trend in ["bearish", "strongly_bearish"]:
            signal = "sell"
        else:
            signal = "hold"
        
        # Record the analysis
        analysis_result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "trend": trend,
            "confidence": confidence,
            "current_price": current_price,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "indicators": {
                "rsi": rsi,
                "macd": {
                    "line": macd_line,
                    "signal": signal_line,
                    "histogram": macd_histogram
                }
            },
            "signal": signal
        }
        
        # Cache the analysis
        self.data_cache[symbol] = analysis_result
        
        # Save to file for historical reference
        self._save_analysis(analysis_result)
        
        return analysis_result
    
    def _get_current_price(self, symbol):
        """Get the current price for a symbol (mock implementation)"""
        # This would normally call an exchange API
        base_prices = {
            "BTCUSDT": 30000,
            "ETHUSDT": 2000,
            "BNBUSDT": 300,
            "XRPUSDT": 0.5,
            "ADAUSDT": 0.4,
            "SOLUSDT": 100,
            "DOGEUSDT": 0.1
        }
        
        # Get base price or generate random if not in our list
        base_price = base_prices.get(symbol, random.uniform(10, 1000))
        
        # Add some randomness
        current_price = base_price * (1 + random.uniform(-0.05, 0.05))
        return round(current_price, 2)
    
    def _save_analysis(self, analysis):
        """Save analysis results to file"""
        filename = f"data/market_data/{analysis['symbol']}_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Load existing data if file exists
        data = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = []
        
        # Append new analysis
        data.append(analysis)
        
        # Write back to file
        with open(filename, 'w') as file:
            json.dump(data, file, indent=2)
    
    def get_technical_indicators(self, symbol, timeframe="1h"):
        """Get technical indicators for a symbol"""
        return self.analyze_trends(symbol, timeframe)["indicators"]
    
    def get_historical_trends(self, symbol, days=7):
        """Get historical trend data"""
        # This would normally fetch historical data from files or database
        return {
            "symbol": symbol,
            "days": days,
            "trends": ["bullish", "neutral", "bearish", "bullish", "bullish", "neutral", "bullish"]
        }
