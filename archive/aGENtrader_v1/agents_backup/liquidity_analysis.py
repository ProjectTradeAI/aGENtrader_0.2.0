
"""
Liquidity Analysis Agent

Analyzes market liquidity, order book depth, volume profiles, and market impact
to provide insights for optimal trade execution and risk management.
"""

import numpy as np
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
import requests
import ccxt
from typing import Dict, List, Optional, Tuple, Any

class LiquidityAnalysisAgent:
    def __init__(self, config_path="config/settings.json", market_data=None):
        """Initialize the Liquidity Analysis Agent"""
        self.name = "Liquidity Analysis Agent"
        self.config = self._load_config(config_path)
        self.market_data = market_data
        
        # Setup exchange connections
        self._setup_exchange_clients()
        
        # Exchange symbol mappings
        self.exchange_symbol_map = {
            "BTC": "BTC/USDT",
            "ETH": "ETH/USDT",
            "SOL": "SOL/USDT",
            "MATIC": "MATIC/USDT"
        }
        
        # Cache for order book and liquidity data
        self.order_book_cache = {}
        self.volume_profile_cache = {}
        self.last_update = {}
        
    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Using default settings.")
            return {
                "liquidity_refresh_interval": 60,  # seconds
                "order_book_depth": 20,
                "volume_profile_periods": 24,
                "exchanges": ["binance"],
                "symbols": ["BTC", "ETH", "SOL", "MATIC"]
            }
            
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
                
            # Setup additional exchanges as needed
            if "coinbase" in self.config.get("exchanges", []):
                self.exchanges["coinbase"] = ccxt.coinbasepro({
                    'enableRateLimit': True
                })
                
            if "kraken" in self.config.get("exchanges", []):
                self.exchanges["kraken"] = ccxt.kraken({
                    'enableRateLimit': True
                })
                
        except Exception as e:
            print(f"Exchange setup failed: {str(e)}")
            self.exchanges = {}  # Reset exchanges if setup fails
            
    async def fetch_order_book(self, symbol: str, depth: int = 20, exchange: str = None) -> Optional[Dict[str, Any]]:
        """Fetch order book data for a symbol"""
        if not exchange and self.exchanges:
            exchange = next(iter(self.exchanges.keys()))
            
        if not self.exchanges.get(exchange):
            return self._simulate_order_book(symbol, depth)
            
        try:
            exchange_symbol = self.exchange_symbol_map.get(symbol)
            if not exchange_symbol:
                raise ValueError(f"No exchange symbol mapping for {symbol}")
                
            # Check cache first
            cache_key = f"{symbol}_{exchange}"
            current_time = time.time()
            if (cache_key in self.order_book_cache and cache_key in self.last_update and 
                current_time - self.last_update[cache_key] < self.config.get("liquidity_refresh_interval", 60)):
                return self.order_book_cache[cache_key]
                
            # Fetch new data
            orderbook = self.exchanges[exchange].fetch_order_book(exchange_symbol, limit=depth)
            
            # Calculate bid-ask spread
            best_bid = orderbook['bids'][0][0] if orderbook['bids'] else None
            best_ask = orderbook['asks'][0][0] if orderbook['asks'] else None
            spread = ((best_ask - best_bid) / best_bid) * 100 if best_bid and best_ask else None
            
            # Calculate total liquidity at each price level
            bid_liquidity = {}
            ask_liquidity = {}
            
            cumulative_bid_volume = 0
            for price, volume in orderbook['bids']:
                cumulative_bid_volume += volume
                bid_liquidity[price] = cumulative_bid_volume
                
            cumulative_ask_volume = 0
            for price, volume in orderbook['asks']:
                cumulative_ask_volume += volume
                ask_liquidity[price] = cumulative_ask_volume
                
            # Calculate order book imbalance (buy pressure vs. sell pressure)
            bid_volume = sum(bid[1] for bid in orderbook['bids'])
            ask_volume = sum(ask[1] for ask in orderbook['asks'])
            
            book_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
            
            # Create depth profile
            depth_profile = {}
            mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else None
            
            if mid_price:
                # Calculate liquidity within percentage ranges of mid price
                ranges = [0.1, 0.5, 1.0, 2.0, 5.0]  # percentage ranges
                
                for pct in ranges:
                    lower_bound = mid_price * (1 - pct/100)
                    upper_bound = mid_price * (1 + pct/100)
                    
                    # Sum bid volume in range
                    bid_volume_in_range = sum(
                        bid[1] for bid in orderbook['bids'] 
                        if bid[0] >= lower_bound
                    )
                    
                    # Sum ask volume in range
                    ask_volume_in_range = sum(
                        ask[1] for ask in orderbook['asks'] 
                        if ask[0] <= upper_bound
                    )
                    
                    depth_profile[f"{pct}%"] = {
                        "bid_volume": bid_volume_in_range,
                        "ask_volume": ask_volume_in_range,
                        "total_volume": bid_volume_in_range + ask_volume_in_range,
                        "imbalance": (bid_volume_in_range - ask_volume_in_range) / (bid_volume_in_range + ask_volume_in_range) if (bid_volume_in_range + ask_volume_in_range) > 0 else 0
                    }
            
            # Market impact estimation
            market_impact = {}
            trade_sizes = [1, 5, 10, 25, 50, 100]  # in thousands USD
            
            for size in trade_sizes:
                size_usd = size * 1000
                
                # Estimate buy impact
                buy_impact = 0
                remaining_size = size_usd
                theoretical_price = best_ask
                
                for ask_price, ask_size in orderbook['asks']:
                    order_value = ask_price * ask_size
                    if remaining_size <= order_value:
                        proportion = remaining_size / order_value
                        buy_impact = (ask_price - best_ask) / best_ask * 100
                        break
                    remaining_size -= order_value
                    theoretical_price = ask_price
                
                # Estimate sell impact
                sell_impact = 0
                remaining_size = size_usd
                theoretical_price = best_bid
                
                for bid_price, bid_size in orderbook['bids']:
                    order_value = bid_price * bid_size
                    if remaining_size <= order_value:
                        proportion = remaining_size / order_value
                        sell_impact = (best_bid - bid_price) / best_bid * 100
                        break
                    remaining_size -= order_value
                    theoretical_price = bid_price
                
                market_impact[f"{size}k"] = {
                    "buy_impact_pct": buy_impact,
                    "sell_impact_pct": sell_impact
                }
            
            # Assemble the full order book analysis
            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "source": exchange,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread": spread,
                "book_imbalance": book_imbalance,
                "bid_volume": bid_volume,
                "ask_volume": ask_volume,
                "depth_profile": depth_profile,
                "market_impact": market_impact,
                "raw_data": {
                    "bids": orderbook['bids'][:10],  # Limit to save space
                    "asks": orderbook['asks'][:10]
                }
            }
            
            # Cache the result
            self.order_book_cache[cache_key] = result
            self.last_update[cache_key] = current_time
            
            return result
            
        except Exception as e:
            print(f"Error fetching order book for {symbol}: {str(e)}")
            return self._simulate_order_book(symbol, depth)
            
    def _simulate_order_book(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """Generate simulated order book data when exchange APIs are unavailable"""
        # Base prices for different symbols
        base_prices = {
            "BTC": 45000,
            "ETH": 2500,
            "SOL": 100,
            "MATIC": 1.5
        }
        
        # Get or create a base price
        base_price = base_prices.get(symbol, 1000)
        
        # Add some randomness
        current_price = base_price * (1 + np.random.uniform(-0.01, 0.01))
        
        # Generate bids (buy orders)
        bids = []
        for i in range(depth):
            price_decrease = np.random.uniform(0.0001, 0.001) * i
            price = current_price * (1 - price_decrease)
            volume = np.random.uniform(0.1, 10) * (1 - i/depth)  # More volume near the top of the book
            bids.append([price, volume])
        
        # Generate asks (sell orders)
        asks = []
        for i in range(depth):
            price_increase = np.random.uniform(0.0001, 0.001) * i
            price = current_price * (1 + price_increase)
            volume = np.random.uniform(0.1, 10) * (1 - i/depth)  # More volume near the top of the book
            asks.append([price, volume])
        
        # Calculate basic metrics
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        spread = ((best_ask - best_bid) / best_bid) * 100
        
        bid_volume = sum(bid[1] for bid in bids)
        ask_volume = sum(ask[1] for ask in asks)
        book_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        
        # Simulate depth profile and market impact
        depth_profile = {}
        market_impact = {}
        
        for pct in [0.1, 0.5, 1.0, 2.0, 5.0]:
            depth_profile[f"{pct}%"] = {
                "bid_volume": bid_volume * (1 - pct/10),
                "ask_volume": ask_volume * (1 - pct/10),
                "total_volume": (bid_volume + ask_volume) * (1 - pct/10),
                "imbalance": book_imbalance * (1 + np.random.uniform(-0.2, 0.2))
            }
            
        for size in [1, 5, 10, 25, 50, 100]:
            market_impact[f"{size}k"] = {
                "buy_impact_pct": 0.01 * size * (1 + np.random.uniform(-0.3, 0.3)),
                "sell_impact_pct": 0.01 * size * (1 + np.random.uniform(-0.3, 0.3))
            }
            
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "source": "simulation",
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "book_imbalance": book_imbalance,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "depth_profile": depth_profile,
            "market_impact": market_impact,
            "raw_data": {
                "bids": bids[:10],
                "asks": asks[:10]
            }
        }
    
    async def fetch_volume_profile(self, symbol: str, timeframe: str = "1h", periods: int = 24, exchange: str = None) -> Optional[Dict[str, Any]]:
        """Fetch and analyze volume profile data for a symbol"""
        if not exchange and self.exchanges:
            exchange = next(iter(self.exchanges.keys()))
            
        if not self.exchanges.get(exchange):
            return self._simulate_volume_profile(symbol, timeframe, periods)
            
        try:
            exchange_symbol = self.exchange_symbol_map.get(symbol)
            if not exchange_symbol:
                raise ValueError(f"No exchange symbol mapping for {symbol}")
                
            # Check cache first
            cache_key = f"{symbol}_{timeframe}_{periods}_{exchange}"
            current_time = time.time()
            if (cache_key in self.volume_profile_cache and cache_key in self.last_update and 
                current_time - self.last_update[cache_key] < self.config.get("liquidity_refresh_interval", 60) * 5):  # Longer cache for volume profile
                return self.volume_profile_cache[cache_key]
                
            # Fetch OHLCV data
            ohlcv = self.exchanges[exchange].fetch_ohlcv(
                exchange_symbol, 
                timeframe=timeframe, 
                limit=periods
            )
            
            if not ohlcv or len(ohlcv) < 5:  # Need enough data for meaningful analysis
                return self._simulate_volume_profile(symbol, timeframe, periods)
                
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate price ranges for volume profile
            price_min = df['low'].min()
            price_max = df['high'].max()
            
            # Create price bins (10-15 bins typically)
            num_bins = min(15, max(10, int(periods / 2)))
            price_range = np.linspace(price_min, price_max, num_bins + 1)
            
            # Initialize volume profile
            volume_profile = {}
            for i in range(len(price_range) - 1):
                lower = price_range[i]
                upper = price_range[i+1]
                midpoint = (lower + upper) / 2
                volume_profile[f"{midpoint:.2f}"] = 0
                
            # Distribute volume across price ranges (simplified approximation)
            for _, row in df.iterrows():
                # Calculate overlap with each bin
                low, high = row['low'], row['high']
                volume = row['volume']
                
                for i in range(len(price_range) - 1):
                    bin_low = price_range[i]
                    bin_high = price_range[i+1]
                    bin_mid = (bin_low + bin_high) / 2
                    
                    # Simple overlap calculation
                    if high >= bin_low and low <= bin_high:
                        # Calculate rough proportion of candle in this bin
                        price_range_total = high - low
                        if price_range_total > 0:
                            overlap_low = max(low, bin_low)
                            overlap_high = min(high, bin_high)
                            overlap_pct = (overlap_high - overlap_low) / price_range_total
                            volume_profile[f"{bin_mid:.2f}"] += volume * overlap_pct
                        else:
                            # Handle zero range (unlikely but possible)
                            if low >= bin_low and low <= bin_high:
                                volume_profile[f"{bin_mid:.2f}"] += volume / num_bins
            
            # Find POC (Point of Control) - price with highest volume
            poc_price = max(volume_profile.items(), key=lambda x: x[1])[0]
            
            # Calculate Value Area (70% of total volume)
            total_volume = sum(volume_profile.values())
            value_area_target = total_volume * 0.7
            
            # Sort by volume descending
            sorted_profile = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
            
            # Take prices until we reach 70% of volume
            value_area = []
            cumulative_volume = 0
            
            for price, volume in sorted_profile:
                value_area.append(float(price))
                cumulative_volume += volume
                if cumulative_volume >= value_area_target:
                    break
            
            # Calculate Value Area High and Low
            value_area_high = max(value_area) if value_area else None
            value_area_low = min(value_area) if value_area else None
            
            # Volume trend analysis
            volume_trend = {}
            if len(df) > 1:
                # Overall volume trend
                volume_change = (df['volume'].iloc[-1] - df['volume'].iloc[0]) / df['volume'].iloc[0] * 100
                
                # Volume moving average
                df['volume_ma'] = df['volume'].rolling(window=min(5, len(df))).mean()
                
                # Volume vs price correlation
                price_changes = df['close'].pct_change().dropna()
                volume_changes = df['volume'].pct_change().dropna()
                
                if len(price_changes) > 2 and len(volume_changes) > 2:
                    correlation = price_changes.corr(volume_changes)
                else:
                    correlation = 0
                    
                volume_trend = {
                    "change_pct": volume_change,
                    "trend": "increasing" if volume_change > 5 else "decreasing" if volume_change < -5 else "stable",
                    "price_correlation": correlation,
                    "last_vs_average": (df['volume'].iloc[-1] / df['volume_ma'].iloc[-1] - 1) * 100 if not pd.isna(df['volume_ma'].iloc[-1]) and df['volume_ma'].iloc[-1] > 0 else 0
                }
            
            # Calculate recent buy/sell volume pressure (approximation based on price movement)
            buy_pressure = 0
            sell_pressure = 0
            
            for _, row in df.iterrows():
                if row['close'] > row['open']:
                    # Up candle - more buying pressure
                    buy_pressure += row['volume']
                else:
                    # Down candle - more selling pressure
                    sell_pressure += row['volume']
            
            total_pressure = buy_pressure + sell_pressure
            if total_pressure > 0:
                buy_pressure_pct = (buy_pressure / total_pressure) * 100
                sell_pressure_pct = (sell_pressure / total_pressure) * 100
            else:
                buy_pressure_pct = 50
                sell_pressure_pct = 50
            
            # Assemble the result
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "periods": periods,
                "timestamp": datetime.now().isoformat(),
                "volume_profile": volume_profile,
                "point_of_control": poc_price,
                "value_area_high": value_area_high,
                "value_area_low": value_area_low,
                "volume_trend": volume_trend,
                "buy_pressure_pct": buy_pressure_pct,
                "sell_pressure_pct": sell_pressure_pct,
                "last_price": df['close'].iloc[-1],
                "total_volume": total_volume
            }
            
            # Cache the result
            self.volume_profile_cache[cache_key] = result
            self.last_update[cache_key] = current_time
            
            return result
            
        except Exception as e:
            print(f"Error fetching volume profile for {symbol}: {str(e)}")
            return self._simulate_volume_profile(symbol, timeframe, periods)
    
    def _simulate_volume_profile(self, symbol: str, timeframe: str = "1h", periods: int = 24) -> Dict[str, Any]:
        """Generate simulated volume profile when exchange APIs are unavailable"""
        # Base prices for different symbols
        base_prices = {
            "BTC": 45000,
            "ETH": 2500,
            "SOL": 100,
            "MATIC": 1.5
        }
        
        # Get or create a base price
        base_price = base_prices.get(symbol, 1000)
        
        # Simulate price range
        price_min = base_price * 0.95
        price_max = base_price * 1.05
        
        # Create volume profile with normal distribution around current price
        num_bins = 12
        price_range = np.linspace(price_min, price_max, num_bins + 1)
        
        # Current price will be near the middle
        current_price = base_price * (1 + np.random.uniform(-0.01, 0.01))
        
        # Generate volume profile with concentration around current price
        volume_profile = {}
        total_volume = 0
        
        for i in range(len(price_range) - 1):
            bin_low = price_range[i]
            bin_high = price_range[i+1]
            bin_mid = (bin_low + bin_high) / 2
            
            # Distance from current price (normalized)
            distance = abs(bin_mid - current_price) / (price_max - price_min)
            
            # Volume decreases with distance from current price
            volume = np.random.uniform(100, 1000) * (1 - distance) ** 2
            volume_profile[f"{bin_mid:.2f}"] = volume
            total_volume += volume
        
        # Find POC
        poc_price = max(volume_profile.items(), key=lambda x: x[1])[0]
        
        # Calculate Value Area
        sorted_profile = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
        
        value_area = []
        cumulative_volume = 0
        value_area_target = total_volume * 0.7
        
        for price, volume in sorted_profile:
            value_area.append(float(price))
            cumulative_volume += volume
            if cumulative_volume >= value_area_target:
                break
        
        value_area_high = max(value_area) if value_area else None
        value_area_low = min(value_area) if value_area else None
        
        # Simulate trends
        volume_trend = {
            "change_pct": np.random.uniform(-15, 15),
            "trend": np.random.choice(["increasing", "stable", "decreasing"]),
            "price_correlation": np.random.uniform(-0.8, 0.8),
            "last_vs_average": np.random.uniform(-20, 20)
        }
        
        # Simulate buy/sell pressure
        buy_pressure_pct = np.random.uniform(35, 65)
        sell_pressure_pct = 100 - buy_pressure_pct
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "periods": periods,
            "timestamp": datetime.now().isoformat(),
            "volume_profile": volume_profile,
            "point_of_control": poc_price,
            "value_area_high": value_area_high,
            "value_area_low": value_area_low,
            "volume_trend": volume_trend,
            "buy_pressure_pct": buy_pressure_pct,
            "sell_pressure_pct": sell_pressure_pct,
            "last_price": current_price,
            "total_volume": total_volume
        }
    
    async def analyze_liquidity(self, symbol: str) -> Dict[str, Any]:
        """Perform comprehensive liquidity analysis for a trading pair"""
        # Fetch order book data
        order_book = await self.fetch_order_book(symbol)
        
        # Fetch volume profile data
        volume_profile = await self.fetch_volume_profile(symbol)
        
        # Calculate liquidity score (0-100)
        liquidity_score = self._calculate_liquidity_score(order_book, volume_profile)
        
        # Determine trade size recommendations
        trade_size_recommendations = self._calculate_trade_size_recommendations(
            symbol, order_book, volume_profile
        )
        
        # Identify key liquidity zones
        liquidity_zones = self._identify_liquidity_zones(order_book, volume_profile)
        
        # Generate trading signals
        signal = self._generate_liquidity_signal(symbol, order_book, volume_profile, liquidity_score)
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "liquidity_score": liquidity_score,
            "trade_size_recommendations": trade_size_recommendations,
            "liquidity_zones": liquidity_zones,
            "signal": signal,
            "order_book_summary": {
                "spread": order_book["spread"],
                "book_imbalance": order_book["book_imbalance"],
                "market_impact": order_book["market_impact"]
            },
            "volume_profile_summary": {
                "point_of_control": volume_profile["point_of_control"],
                "value_area_high": volume_profile["value_area_high"],
                "value_area_low": volume_profile["value_area_low"],
                "buy_pressure_pct": volume_profile["buy_pressure_pct"],
                "volume_trend": volume_profile["volume_trend"]["trend"]
            }
        }
        
    def _calculate_liquidity_score(self, order_book: Dict[str, Any], volume_profile: Dict[str, Any]) -> float:
        """Calculate a liquidity score from 0-100 based on order book and volume profile data"""
        score = 50  # Start at neutral
        
        # Order book factors
        
        # 1. Spread (lower is better)
        spread = order_book.get("spread", 0)
        if spread < 0.05:  # Very tight spread
            score += 10
        elif spread < 0.1:
            score += 5
        elif spread > 0.5:
            score -= 10
        elif spread > 0.25:
            score -= 5
        
        # 2. Book depth/volume
        bid_volume = order_book.get("bid_volume", 0)
        ask_volume = order_book.get("ask_volume", 0)
        
        total_book_volume = bid_volume + ask_volume
        # These thresholds would be calibrated based on the specific asset
        if total_book_volume > 1000:  # Arbitrary threshold, should be adjusted per asset
            score += 10
        elif total_book_volume < 100:
            score -= 10
            
        # 3. Book imbalance (extreme imbalance suggests potential price movement)
        imbalance = abs(order_book.get("book_imbalance", 0))
        if imbalance > 0.7:  # Highly imbalanced
            score -= 10
        elif imbalance > 0.4:
            score -= 5
        
        # 4. Market impact (lower is better)
        market_impact_10k = order_book.get("market_impact", {}).get("10k", {})
        buy_impact = market_impact_10k.get("buy_impact_pct", 5)
        sell_impact = market_impact_10k.get("sell_impact_pct", 5)
        avg_impact = (buy_impact + sell_impact) / 2
        
        if avg_impact < 0.1:
            score += 10
        elif avg_impact < 0.25:
            score += 5
        elif avg_impact > 1.0:
            score -= 10
        elif avg_impact > 0.5:
            score -= 5
            
        # Volume profile factors
        
        # 5. Total volume
        total_volume = volume_profile.get("total_volume", 0)
        # Threshold depends on the asset and timeframe
        if total_volume > 5000:  # Arbitrary threshold
            score += 5
        elif total_volume < 500:
            score -= 5
            
        # 6. Buy/sell pressure ratio (extreme values suggest potential imbalance)
        buy_pressure = volume_profile.get("buy_pressure_pct", 50)
        sell_pressure = volume_profile.get("sell_pressure_pct", 50)
        pressure_ratio = abs(buy_pressure - sell_pressure)
        
        if pressure_ratio > 30:  # Highly imbalanced pressure
            score -= 5
            
        # 7. Volume trend
        volume_trend = volume_profile.get("volume_trend", {}).get("trend", "stable")
        if volume_trend == "increasing":
            score += 5
        elif volume_trend == "decreasing":
            score -= 5
            
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return score
        
    def _calculate_trade_size_recommendations(self, symbol: str, order_book: Dict[str, Any], volume_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal trade sizes based on liquidity analysis"""
        # Get market impact data
        market_impact = order_book.get("market_impact", {})
        
        # Current price
        current_price = (order_book.get("best_bid", 0) + order_book.get("best_ask", 0)) / 2
        
        # Calculate ideal max trade size (max size with less than 0.5% price impact)
        max_size_with_low_impact = None
        for size_key in ["1k", "5k", "10k", "25k", "50k", "100k"]:
            impact = market_impact.get(size_key, {})
            buy_impact = impact.get("buy_impact_pct", 999)
            sell_impact = impact.get("sell_impact_pct", 999)
            
            if buy_impact < 0.5 and sell_impact < 0.5:
                max_size_with_low_impact = size_key
            else:
                break
                
        # If we couldn't find a size with low impact, default to 1k
        if not max_size_with_low_impact:
            max_size_with_low_impact = "1k"
            
        # Convert size key to numeric (e.g., "10k" -> 10000)
        max_size_numeric = int(max_size_with_low_impact.replace("k", "")) * 1000
        
        # Calculate recommended sizes
        recommended_sizes = {
            "conservative": max_size_numeric * 0.2,  # 20% of max size
            "moderate": max_size_numeric * 0.5,     # 50% of max size
            "aggressive": max_size_numeric         # 100% of max size
        }
        
        # Convert to coin quantities based on current price
        if current_price > 0:
            quantity_recommendations = {
                strategy: round(usd / current_price, 8) 
                for strategy, usd in recommended_sizes.items()
            }
        else:
            quantity_recommendations = {
                "conservative": 0.01,
                "moderate": 0.05,
                "aggressive": 0.1
            }
            
        return {
            "usd_amounts": recommended_sizes,
            "quantity": quantity_recommendations,
            "slippage_estimates": {
                "conservative": market_impact.get("1k", {}).get("buy_impact_pct", 0),
                "moderate": market_impact.get("5k", {}).get("buy_impact_pct", 0),
                "aggressive": market_impact.get("10k", {}).get("buy_impact_pct", 0)
            }
        }
        
    def _identify_liquidity_zones(self, order_book: Dict[str, Any], volume_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Identify key liquidity zones for support and resistance"""
        zones = {
            "support": [],
            "resistance": [],
            "high_volume": []
        }
        
        # Current price
        best_bid = order_book.get("best_bid", 0)
        best_ask = order_book.get("best_ask", 0)
        current_price = (best_bid + best_ask) / 2
        
        # From volume profile
        poc_price = float(volume_profile.get("point_of_control", current_price))
        value_area_low = volume_profile.get("value_area_low", current_price * 0.95)
        value_area_high = volume_profile.get("value_area_high", current_price * 1.05)
        
        # First support/resistance from value area
        if poc_price < current_price:
            zones["support"].append({
                "price": poc_price,
                "strength": "high",
                "source": "volume_poc"
            })
        else:
            zones["resistance"].append({
                "price": poc_price,
                "strength": "high",
                "source": "volume_poc"
            })
            
        if value_area_low < current_price:
            zones["support"].append({
                "price": value_area_low,
                "strength": "medium",
                "source": "value_area_low"
            })
            
        if value_area_high > current_price:
            zones["resistance"].append({
                "price": value_area_high,
                "strength": "medium",
                "source": "value_area_high"
            })
            
        # Extract high volume zones
        volume_profile_data = volume_profile.get("volume_profile", {})
        if volume_profile_data:
            # Get top 3 volume price levels
            sorted_volumes = sorted(
                [(float(price), vol) for price, vol in volume_profile_data.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for price, volume in sorted_volumes:
                zones["high_volume"].append({
                    "price": price,
                    "volume": volume,
                    "type": "support" if price < current_price else "resistance"
                })
                
        # Add from order book (major bid/ask walls)
        bid_clusters = self._find_order_book_clusters(order_book.get("raw_data", {}).get("bids", []))
        ask_clusters = self._find_order_book_clusters(order_book.get("raw_data", {}).get("asks", []))
        
        for price, volume in bid_clusters:
            zones["support"].append({
                "price": price,
                "strength": "high" if volume > order_book.get("bid_volume", 0) * 0.2 else "medium",
                "source": "order_book_bids",
                "volume": volume
            })
            
        for price, volume in ask_clusters:
            zones["resistance"].append({
                "price": price,
                "strength": "high" if volume > order_book.get("ask_volume", 0) * 0.2 else "medium",
                "source": "order_book_asks",
                "volume": volume
            })
            
        # Sort the zones by price
        zones["support"] = sorted(zones["support"], key=lambda x: x["price"], reverse=True)[:3]  # Top 3 supports
        zones["resistance"] = sorted(zones["resistance"], key=lambda x: x["price"])[:3]  # Top 3 resistances
        
        return zones
        
    def _find_order_book_clusters(self, orders: List[List[float]]) -> List[Tuple[float, float]]:
        """Find clusters of liquidity in order book data"""
        if not orders:
            return []
            
        # Group nearby orders
        clusters = []
        current_cluster_price = orders[0][0]
        current_cluster_volume = orders[0][1]
        
        for i in range(1, len(orders)):
            price, volume = orders[i]
            
            # If price is close to current cluster, add to cluster
            if abs(price - current_cluster_price) / current_cluster_price < 0.01:  # Within 1%
                # Update cluster with weighted average price
                total_volume = current_cluster_volume + volume
                current_cluster_price = (current_cluster_price * current_cluster_volume + price * volume) / total_volume
                current_cluster_volume = total_volume
            else:
                # Save current cluster and start a new one
                clusters.append((current_cluster_price, current_cluster_volume))
                current_cluster_price = price
                current_cluster_volume = volume
                
        # Add the last cluster
        clusters.append((current_cluster_price, current_cluster_volume))
        
        # Sort by volume
        return sorted(clusters, key=lambda x: x[1], reverse=True)[:2]  # Return top 2 clusters
        
    def _generate_liquidity_signal(self, symbol: str, order_book: Dict[str, Any], volume_profile: Dict[str, Any], liquidity_score: float) -> Dict[str, Any]:
        """Generate a trading signal based on liquidity analysis"""
        # Default neutral signal
        signal = {
            "signal": "neutral",
            "confidence": 50,
            "reasoning": "No strong liquidity signal detected",
            "execution_advice": {}
        }
        
        # Current price
        best_bid = order_book.get("best_bid", 0)
        best_ask = order_book.get("best_ask", 0)
        mid_price = (best_bid + best_ask) / 2
        
        # 1. Analyze order book imbalance
        book_imbalance = order_book.get("book_imbalance", 0)
        imbalance_signal = "neutral"
        imbalance_confidence = 50
        
        if book_imbalance > 0.3:  # Strong buy bias
            imbalance_signal = "buy"
            imbalance_confidence = min(50 + book_imbalance * 100, 90)
        elif book_imbalance < -0.3:  # Strong sell bias
            imbalance_signal = "sell"
            imbalance_confidence = min(50 + abs(book_imbalance) * 100, 90)
            
        # 2. Analyze buy/sell pressure
        buy_pressure = volume_profile.get("buy_pressure_pct", 50)
        sell_pressure = volume_profile.get("sell_pressure_pct", 50)
        
        pressure_signal = "neutral"
        pressure_confidence = 50
        
        if buy_pressure > 60:
            pressure_signal = "buy"
            pressure_confidence = buy_pressure
        elif sell_pressure > 60:
            pressure_signal = "sell"
            pressure_confidence = sell_pressure
            
        # 3. Analyze volume trend
        volume_trend = volume_profile.get("volume_trend", {}).get("trend", "stable")
        volume_change = volume_profile.get("volume_trend", {}).get("change_pct", 0)
        
        volume_signal = "neutral"
        volume_confidence = 50
        
        if volume_trend == "increasing" and volume_change > 10:
            # Increasing volume is bullish if price is rising
            volume_signal = "stronger_moves"
            volume_confidence = min(50 + volume_change, 90)
            
        # 4. Analyze market impact
        market_impact_10k = order_book.get("market_impact", {}).get("10k", {})
        buy_impact = market_impact_10k.get("buy_impact_pct", 5)
        sell_impact = market_impact_10k.get("sell_impact_pct", 5)
        
        impact_bias = "neutral"
        if buy_impact < sell_impact * 0.5:  # Much easier to buy
            impact_bias = "buy"
        elif sell_impact < buy_impact * 0.5:  # Much easier to sell
            impact_bias = "sell"
            
        # 5. Check for liquidity traps (thin liquidity zones that price could slip through)
        traps = []
        bids = order_book.get("raw_data", {}).get("bids", [])
        asks = order_book.get("raw_data", {}).get("asks", [])
        
        if bids and len(bids) > 3:
            # Check for thin zones in the bids
            for i in range(len(bids) - 1):
                current_price = bids[i][0]
                next_price = bids[i+1][0]
                price_gap = (current_price - next_price) / current_price
                if price_gap > 0.01:  # More than 1% gap
                    traps.append({
                        "type": "support_gap",
                        "price": next_price,
                        "gap_pct": price_gap * 100
                    })
                    
        if asks and len(asks) > 3:
            # Check for thin zones in the asks
            for i in range(len(asks) - 1):
                current_price = asks[i][0]
                next_price = asks[i+1][0]
                price_gap = (next_price - current_price) / current_price
                if price_gap > 0.01:  # More than 1% gap
                    traps.append({
                        "type": "resistance_gap",
                        "price": next_price,
                        "gap_pct": price_gap * 100
                    })
        
        # Combine signals
        combined_signal = "neutral"
        combined_confidence = 50
        reasoning = []
        
        # Order book imbalance has highest weight
        if imbalance_signal != "neutral":
            combined_signal = imbalance_signal
            combined_confidence = imbalance_confidence
            reasoning.append(f"Order book shows {book_imbalance:.2f} imbalance towards {imbalance_signal}")
            
        # Pressure can reinforce or contradict
        if pressure_signal == combined_signal and pressure_signal != "neutral":
            combined_confidence = min(combined_confidence + 10, 90)
            reasoning.append(f"Volume pressure confirms with {buy_pressure:.0f}% buy vs {sell_pressure:.0f}% sell")
        elif pressure_signal != "neutral" and pressure_signal != combined_signal:
            combined_confidence = max(combined_confidence - 10, 10)
            reasoning.append(f"Volume pressure contradicts with {buy_pressure:.0f}% buy vs {sell_pressure:.0f}% sell")
            
        # Impact bias can reinforce
        if impact_bias == combined_signal and impact_bias != "neutral":
            combined_confidence = min(combined_confidence + 5, 90)
            reasoning.append(f"Market impact analysis suggests easier execution for {impact_bias} orders")
            
        # Adjust for overall liquidity
        if liquidity_score < 30:
            combined_confidence = max(combined_confidence - 20, 10)
            reasoning.append(f"Low liquidity score ({liquidity_score}) suggests caution")
        elif liquidity_score > 70:
            combined_confidence = min(combined_confidence + 10, 90)
            reasoning.append(f"High liquidity score ({liquidity_score}) suggests favorable conditions")
            
        # Check for liquidity traps
        if traps:
            reasoning.append(f"Detected {len(traps)} liquidity gaps that could lead to price slippage")
            
        # Create execution advice
        execution_advice = {
            "optimal_time": "now" if combined_confidence > 70 else "wait",
            "recommended_batch_sizing": "single" if liquidity_score > 70 else "multiple_batches",
            "liquidity_score": liquidity_score,
            "estimated_slippage": buy_impact if combined_signal == "buy" else sell_impact,
            "max_recommended_size": self._calculate_trade_size_recommendations(
                symbol, order_book, volume_profile
            )
        }
        
        if traps:
            execution_advice["caution"] = f"Potential slippage at {traps[0]['price']}"
            
        return {
            "signal": combined_signal,
            "confidence": combined_confidence,
            "reasoning": "; ".join(reasoning),
            "execution_advice": execution_advice,
            "liquidity_traps": traps
        }
        
    async def get_liquidity_trading_signal(self, symbol: str) -> Dict[str, Any]:
        """Generate a trading signal based on liquidity analysis"""
        liquidity_analysis = await self.analyze_liquidity(symbol)
        
        signal = liquidity_analysis["signal"]
        signal["symbol"] = symbol
        signal["timestamp"] = datetime.now().isoformat()
        signal["source"] = "liquidity_analysis"
        
        # Add support/resistance levels
        signal["levels"] = {
            "support": [level["price"] for level in liquidity_analysis["liquidity_zones"]["support"]],
            "resistance": [level["price"] for level in liquidity_analysis["liquidity_zones"]["resistance"]]
        }
        
        # Add volatility estimate based on spread and market impact
        spread = liquidity_analysis["order_book_summary"]["spread"]
        market_impact = liquidity_analysis["order_book_summary"]["market_impact"].get("10k", {})
        avg_impact = (market_impact.get("buy_impact_pct", 0) + market_impact.get("sell_impact_pct", 0)) / 2
        
        volatility_estimate = (spread + avg_impact) / 2
        signal["volatility_estimate"] = volatility_estimate
        
        return signal

async def main():
    """Test the agent"""
    agent = LiquidityAnalysisAgent()
    
    for symbol in ["BTC", "ETH", "SOL", "MATIC"]:
        print(f"\n===== LIQUIDITY ANALYSIS FOR {symbol} =====")
        signal = await agent.get_liquidity_trading_signal(symbol)
        
        print(f"Trading Signal: {signal['signal']}")
        print(f"Confidence: {signal['confidence']:.2f}")
        print(f"Reasoning: {signal['reasoning']}")
        
        print("\nRecommended Trade Execution:")
        advice = signal['execution_advice']
        print(f"  Optimal timing: {advice['optimal_time']}")
        print(f"  Recommended sizing: {advice['recommended_batch_sizing']}")
        print(f"  Liquidity score: {advice['liquidity_score']:.2f}")
        print(f"  Estimated slippage: {advice['estimated_slippage']:.2f}%")
        
        print("\nSupport/Resistance Levels:")
        print(f"  Support: {signal['levels']['support']}")
        print(f"  Resistance: {signal['levels']['resistance']}")
        
        if signal.get('liquidity_traps'):
            print("\nLiquidity Traps:")
            for trap in signal['liquidity_traps']:
                print(f"  {trap['type']} at {trap['price']} with {trap['gap_pct']:.2f}% gap")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
