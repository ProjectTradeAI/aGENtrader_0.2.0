#!/usr/bin/env python3
"""
Market Event Simulator

This module simulates market events for testing the aGENtrader v2 pipeline:
- Generates mock market data
- Creates market events with varying characteristics
- Allows testing the system without real market data
"""

import os
import sys
import json
import logging
import random
import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("market_simulator")


class MarketEventSimulator:
    """
    Market Event Simulator class.
    
    This class simulates various market events for testing the trading system.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the simulator.
        
        Args:
            seed: Random seed for reproducibility (optional)
        """
        self.logger = logging.getLogger("market_simulator")
        
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
            self.logger.info(f"Initialized with random seed: {seed}")
        else:
            self.logger.info("Initialized with random seed: None (using system time)")
        
        # Define price range for simulation
        self.base_price = 65000.0  # Base price for BTC
        self.volatility = 0.05     # 5% volatility
        
        # Define common symbols
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
        
        # Define intervals
        self.intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    def generate_price_action(self, 
                             symbol: str = "BTCUSDT", 
                             interval: str = "1h",
                             trend: str = "neutral",
                             volatility_factor: float = 1.0,
                             num_candles: int = 24) -> List[Dict[str, Any]]:
        """
        Generate simulated price candles.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            trend: Price trend ('bullish', 'bearish', or 'neutral')
            volatility_factor: Multiplier for volatility (1.0 = normal)
            num_candles: Number of candles to generate
            
        Returns:
            List of candle data dictionaries
        """
        # Set trend bias
        if trend == "bullish":
            bias = 0.55  # Slightly bullish
        elif trend == "bearish":
            bias = 0.45  # Slightly bearish
        else:
            bias = 0.5   # Neutral
        
        # Get base price from symbol
        if symbol == "BTCUSDT":
            price = self.base_price
        elif symbol == "ETHUSDT":
            price = self.base_price * 0.06  # ETH at ~6% of BTC price
        elif symbol == "SOLUSDT":
            price = self.base_price * 0.003  # SOL at ~0.3% of BTC price
        elif symbol == "BNBUSDT":
            price = self.base_price * 0.005  # BNB at ~0.5% of BTC price
        elif symbol == "XRPUSDT":
            price = self.base_price * 0.00001  # XRP at ~0.001% of BTC price
        else:
            price = self.base_price  # Default to BTC price
        
        # Calculate current timestamp and interval in seconds
        now = datetime.datetime.now()
        
        if interval == "1m":
            seconds = 60
        elif interval == "5m":
            seconds = 300
        elif interval == "15m":
            seconds = 900
        elif interval == "1h":
            seconds = 3600
        elif interval == "4h":
            seconds = 14400
        elif interval == "1d":
            seconds = 86400
        else:
            seconds = 3600  # Default to 1h
        
        # Generate candles
        candles = []
        
        for i in range(num_candles):
            # Calculate timestamp for this candle
            timestamp = now - datetime.timedelta(seconds=seconds * (num_candles - i))
            
            # Generate random price action
            price_change = random.uniform(-1, 1)
            
            # Apply bias
            if price_change > 0:
                price_change = price_change * (2 * bias)
            else:
                price_change = price_change * (2 * (1 - bias))
            
            # Apply volatility
            price_change = price_change * self.volatility * volatility_factor * price
            
            # Calculate high, low, open, close
            open_price = price
            close_price = price + price_change
            high_price = max(open_price, close_price) + random.uniform(0, 0.3 * abs(price_change))
            low_price = min(open_price, close_price) - random.uniform(0, 0.3 * abs(price_change))
            
            # Generate volume
            base_volume = price * 10  # Base volume relative to price
            volume = random.uniform(0.5, 1.5) * base_volume
            
            # Add candle
            candle = {
                "symbol": symbol,
                "interval": interval,
                "timestamp": timestamp.isoformat(),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            }
            candles.append(candle)
            
            # Update price for next candle
            price = close_price
        
        return candles
    
    def generate_market_depth(self,
                             symbol: str = "BTCUSDT",
                             price: Optional[float] = None,
                             depth_type: str = "balanced") -> Dict[str, Any]:
        """
        Generate simulated market depth data.
        
        Args:
            symbol: Trading symbol
            price: Current price (if None, uses symbol's base price)
            depth_type: Type of market depth to simulate
                        ('balanced', 'ask_wall', 'bid_wall', 'thin')
            
        Returns:
            Dictionary with market depth data
        """
        # Get price if not provided
        if price is None:
            # Get last candle close price
            candles = self.generate_price_action(symbol=symbol, num_candles=1)
            price = candles[0]["close"]
        
        # Generate asks and bids based on depth type
        asks = []
        bids = []
        
        # Number of price levels
        num_levels = 20
        
        # Price increments
        price_increment = price * 0.0001  # 0.01% of price
        
        # Generate ask and bid values based on depth type
        if depth_type == "balanced":
            # Balanced order book
            for i in range(num_levels):
                ask_price = price + (i + 1) * price_increment
                bid_price = price - (i + 1) * price_increment
                
                ask_quantity = random.uniform(0.8, 1.2) * (1 / (i + 1)) * price * 0.1
                bid_quantity = random.uniform(0.8, 1.2) * (1 / (i + 1)) * price * 0.1
                
                asks.append([ask_price, ask_quantity])
                bids.append([bid_price, bid_quantity])
        
        elif depth_type == "ask_wall":
            # Order book with an ask wall
            for i in range(num_levels):
                ask_price = price + (i + 1) * price_increment
                bid_price = price - (i + 1) * price_increment
                
                # Create a wall at a specific level
                if 4 <= i <= 6:
                    ask_quantity = random.uniform(2.5, 3.0) * (1 / (i + 1)) * price * 0.1
                else:
                    ask_quantity = random.uniform(0.8, 1.2) * (1 / (i + 1)) * price * 0.1
                
                bid_quantity = random.uniform(0.8, 1.2) * (1 / (i + 1)) * price * 0.1
                
                asks.append([ask_price, ask_quantity])
                bids.append([bid_price, bid_quantity])
        
        elif depth_type == "bid_wall":
            # Order book with a bid wall
            for i in range(num_levels):
                ask_price = price + (i + 1) * price_increment
                bid_price = price - (i + 1) * price_increment
                
                ask_quantity = random.uniform(0.8, 1.2) * (1 / (i + 1)) * price * 0.1
                
                # Create a wall at a specific level
                if 4 <= i <= 6:
                    bid_quantity = random.uniform(2.5, 3.0) * (1 / (i + 1)) * price * 0.1
                else:
                    bid_quantity = random.uniform(0.8, 1.2) * (1 / (i + 1)) * price * 0.1
                
                asks.append([ask_price, ask_quantity])
                bids.append([bid_price, bid_quantity])
        
        elif depth_type == "thin":
            # Thin order book (low liquidity)
            for i in range(num_levels):
                ask_price = price + (i + 1) * price_increment
                bid_price = price - (i + 1) * price_increment
                
                ask_quantity = random.uniform(0.3, 0.5) * (1 / (i + 1)) * price * 0.1
                bid_quantity = random.uniform(0.3, 0.5) * (1 / (i + 1)) * price * 0.1
                
                asks.append([ask_price, ask_quantity])
                bids.append([bid_price, bid_quantity])
        
        # Calculate total volume and bid/ask ratio
        total_ask_volume = sum(ask[1] for ask in asks)
        total_bid_volume = sum(bid[1] for bid in bids)
        
        # Create market depth data
        market_depth = {
            "symbol": symbol,
            "timestamp": datetime.datetime.now().isoformat(),
            "last_price": price,
            "asks": asks,
            "bids": bids,
            "total_ask_volume": total_ask_volume,
            "total_bid_volume": total_bid_volume,
            "bid_ask_ratio": total_bid_volume / total_ask_volume if total_ask_volume > 0 else 1.0
        }
        
        return market_depth
    
    def generate_funding_rates(self,
                              symbol: str = "BTCUSDT",
                              trend: str = "neutral",
                              num_periods: int = 12) -> List[Dict[str, Any]]:
        """
        Generate simulated funding rate data.
        
        Args:
            symbol: Trading symbol
            trend: Funding rate trend ('positive', 'negative', 'neutral')
            num_periods: Number of periods to generate
            
        Returns:
            List of funding rate data dictionaries
        """
        # Set base rate and bias based on trend
        if trend == "positive":
            base_rate = 0.0005  # 0.05% positive
            bias = 0.7  # 70% chance of positive rate
        elif trend == "negative":
            base_rate = -0.0005  # 0.05% negative
            bias = 0.3  # 30% chance of positive rate
        else:
            base_rate = 0.0  # Neutral
            bias = 0.5  # 50% chance either way
        
        # Calculate current timestamp and interval (8 hours for funding rate)
        now = datetime.datetime.now()
        seconds = 8 * 3600  # 8 hours
        
        # Generate funding rates
        funding_rates = []
        
        for i in range(num_periods):
            # Calculate timestamp for this period
            timestamp = now - datetime.timedelta(seconds=seconds * (num_periods - i))
            
            # Generate random value with bias
            rand = random.random()
            direction = 1 if rand < bias else -1
            
            # Calculate rate
            rate = base_rate + direction * random.uniform(0, 0.001)  # +/- 0.1% max variation
            
            # Add funding rate data
            funding_rate = {
                "symbol": symbol,
                "timestamp": timestamp.isoformat(),
                "funding_rate": rate,
                "funding_time": timestamp.isoformat()
            }
            funding_rates.append(funding_rate)
        
        return funding_rates
    
    def generate_volume_profile(self,
                               symbol: str = "BTCUSDT",
                               price: Optional[float] = None,
                               profile_type: str = "normal") -> Dict[str, Any]:
        """
        Generate simulated volume profile data.
        
        Args:
            symbol: Trading symbol
            price: Current price (if None, uses symbol's base price)
            profile_type: Type of volume profile
                         ('normal', 'accumulation', 'distribution', 'bimodal')
            
        Returns:
            Dictionary with volume profile data
        """
        # Get price if not provided
        if price is None:
            # Get last candle close price
            candles = self.generate_price_action(symbol=symbol, num_candles=1)
            price = candles[0]["close"]
        
        # Number of price levels
        num_levels = 20
        
        # Price range (percentage of price)
        price_range = price * 0.05  # 5% of price
        
        # Generate price levels
        min_price = price - price_range / 2
        max_price = price + price_range / 2
        
        price_levels = []
        for i in range(num_levels):
            level_price = min_price + (max_price - min_price) * i / (num_levels - 1)
            price_levels.append(level_price)
        
        # Generate volumes based on profile type
        volumes = []
        
        if profile_type == "normal":
            # Normal distribution centered at current price
            for level_price in price_levels:
                distance = abs(level_price - price) / price_range
                volume = (1 - distance) * price * random.uniform(0.8, 1.2) * 0.5
                volumes.append(max(0, volume))
        
        elif profile_type == "accumulation":
            # Higher volumes below current price (accumulation)
            for level_price in price_levels:
                if level_price < price:
                    # Higher volumes below current price
                    distance = abs(level_price - price) / price_range
                    volume = (1 - distance) * price * random.uniform(1.5, 2.0) * 0.5
                else:
                    distance = abs(level_price - price) / price_range
                    volume = (1 - distance) * price * random.uniform(0.5, 0.8) * 0.5
                volumes.append(max(0, volume))
        
        elif profile_type == "distribution":
            # Higher volumes above current price (distribution)
            for level_price in price_levels:
                if level_price > price:
                    # Higher volumes above current price
                    distance = abs(level_price - price) / price_range
                    volume = (1 - distance) * price * random.uniform(1.5, 2.0) * 0.5
                else:
                    distance = abs(level_price - price) / price_range
                    volume = (1 - distance) * price * random.uniform(0.5, 0.8) * 0.5
                volumes.append(max(0, volume))
        
        elif profile_type == "bimodal":
            # Bimodal distribution (two peaks)
            for level_price in price_levels:
                lower_peak = price - price_range * 0.3
                upper_peak = price + price_range * 0.3
                
                distance_lower = abs(level_price - lower_peak) / price_range
                distance_upper = abs(level_price - upper_peak) / price_range
                
                volume_lower = (1 - min(1, distance_lower * 2)) * price * random.uniform(0.8, 1.2) * 0.3
                volume_upper = (1 - min(1, distance_upper * 2)) * price * random.uniform(0.8, 1.2) * 0.3
                
                volume = max(volume_lower, volume_upper)
                volumes.append(max(0, volume))
        
        # Create volume profile data
        profile_data = {
            "symbol": symbol,
            "timestamp": datetime.datetime.now().isoformat(),
            "price_levels": price_levels,
            "volumes": volumes,
            "point_of_control": price_levels[volumes.index(max(volumes))],
            "value_area_low": price_levels[0],
            "value_area_high": price_levels[-1]
        }
        
        return profile_data
    
    def generate_market_event(self, 
                              symbol: Optional[str] = None,
                              interval: Optional[str] = None,
                              event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete market event with price action, depth, funding, etc.
        
        Args:
            symbol: Trading symbol (if None, randomly selected)
            interval: Time interval (if None, randomly selected)
            event_type: Type of event to simulate
                       ('normal', 'bullish', 'bearish', 'volatile', 'low_liquidity')
            
        Returns:
            Dictionary with complete market event data
        """
        # Select symbol if not provided
        if symbol is None:
            symbol = random.choice(self.symbols)
        
        # Select interval if not provided
        if interval is None:
            interval = random.choice(self.intervals)
        
        # Select event type if not provided
        if event_type is None:
            event_type = random.choice([
                "normal", "bullish", "bearish", "volatile", "low_liquidity"
            ])
        
        # Configure parameters based on event type
        if event_type == "normal":
            price_trend = "neutral"
            volatility_factor = 1.0
            depth_type = "balanced"
            funding_trend = "neutral"
            volume_profile_type = "normal"
            
        elif event_type == "bullish":
            price_trend = "bullish"
            volatility_factor = 1.2
            depth_type = "bid_wall"
            funding_trend = "positive"
            volume_profile_type = "accumulation"
            
        elif event_type == "bearish":
            price_trend = "bearish"
            volatility_factor = 1.2
            depth_type = "ask_wall"
            funding_trend = "negative"
            volume_profile_type = "distribution"
            
        elif event_type == "volatile":
            price_trend = random.choice(["bullish", "bearish"])
            volatility_factor = 2.0
            depth_type = "balanced"
            funding_trend = random.choice(["positive", "negative"])
            volume_profile_type = "bimodal"
            
        elif event_type == "low_liquidity":
            price_trend = "neutral"
            volatility_factor = 1.5
            depth_type = "thin"
            funding_trend = "neutral"
            volume_profile_type = "normal"
        
        # Generate price action
        price_action = self.generate_price_action(
            symbol=symbol, 
            interval=interval,
            trend=price_trend,
            volatility_factor=volatility_factor
        )
        
        # Get current price from last candle
        current_price = price_action[-1]["close"]
        
        # Generate market depth
        market_depth = self.generate_market_depth(
            symbol=symbol,
            price=current_price,
            depth_type=depth_type
        )
        
        # Generate funding rates
        funding_rates = self.generate_funding_rates(
            symbol=symbol,
            trend=funding_trend
        )
        
        # Generate volume profile
        volume_profile = self.generate_volume_profile(
            symbol=symbol,
            price=current_price,
            profile_type=volume_profile_type
        )
        
        # Create complete market event
        market_event = {
            "symbol": symbol,
            "interval": interval,
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "price_action": price_action,
            "market_depth": market_depth,
            "funding_rates": funding_rates,
            "volume_profile": volume_profile
        }
        
        return market_event
    
    def save_to_file(self, data: Dict[str, Any], filename: str) -> None:
        """
        Save data to JSON file.
        
        Args:
            data: Data to save
            filename: Filename to save to
        """
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Save data
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved data to: {filename}")


# Main function to demonstrate usage
def main():
    # Create simulator
    simulator = MarketEventSimulator(seed=42)
    
    # Generate a market event
    market_event = simulator.generate_market_event(
        symbol="BTCUSDT",
        interval="1h",
        event_type="bullish"
    )
    
    # Save to file
    output_dir = os.path.join(parent_dir, "data", "simulated")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"market_event_{market_event['symbol']}_{market_event['interval']}.json")
    simulator.save_to_file(market_event, output_file)
    
    # Print summary
    print(f"Generated {market_event['event_type']} market event for {market_event['symbol']} at {market_event['interval']} interval")
    print(f"Event timestamp: {market_event['timestamp']}")
    print(f"Last price: {market_event['price_action'][-1]['close']}")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()