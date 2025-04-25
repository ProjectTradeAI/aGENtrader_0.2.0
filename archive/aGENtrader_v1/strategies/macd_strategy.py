
"""
MACD Strategy Module

Implements a trading strategy based on the Moving Average Convergence Divergence (MACD) indicator.
"""

import numpy as np
from typing import List, Dict, Any

class MACDStrategy:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        """Initialize the MACD Strategy"""
        self.name = "MACD Strategy"
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.prices = []
        self.last_signal = "hold"
        
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate the Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)
            
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
            
        return ema
        
    def calculate_macd(self, prices: List[float]) -> dict:
        """Calculate MACD line, signal line and histogram"""
        if len(prices) < self.slow_period:
            return {
                "macd_line": 0,
                "signal_line": 0,
                "histogram": 0
            }
            
        # Calculate EMAs
        fast_ema = self.calculate_ema(prices, self.fast_period)
        slow_ema = self.calculate_ema(prices, self.slow_period)
        
        # MACD Line = Fast EMA - Slow EMA
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line (EMA of MACD line)
        # For simplicity, we'll use a simple approach here
        if len(prices) < self.slow_period + self.signal_period:
            signal_line = macd_line
        else:
            # Create a list of MACD values
            macd_values = []
            for i in range(self.signal_period):
                price_window = prices[-(self.slow_period + self.signal_period - i):-i] if i > 0 else prices[-(self.slow_period + self.signal_period):]
                fast_ema = self.calculate_ema(price_window, self.fast_period)
                slow_ema = self.calculate_ema(price_window, self.slow_period)
                macd_values.append(fast_ema - slow_ema)
                
            signal_line = self.calculate_ema(macd_values, self.signal_period)
        
        # Histogram = MACD Line - Signal Line
        histogram = macd_line - signal_line
        
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram
        }
        
    def analyze(self, price: float) -> str:
        """Analyze the current price and return a trading signal"""
        self.prices.append(price)
        
        # Keep the price list at a reasonable size
        if len(self.prices) > self.slow_period * 3:
            self.prices = self.prices[-(self.slow_period * 3):]
            
        if len(self.prices) < self.slow_period:
            self.last_signal = "hold"
            return self.last_signal
            
        # Calculate MACD
        macd_data = self.calculate_macd(self.prices)
        
        # Generate signal based on MACD crossover
        # Buy when the MACD line crosses above the signal line
        # Sell when the MACD line crosses below the signal line
        
        # We need at least two points to detect a crossover
        if len(self.prices) > self.slow_period + 1:
            prev_prices = self.prices[:-1]
            prev_macd_data = self.calculate_macd(prev_prices)
            
            if (macd_data["macd_line"] > macd_data["signal_line"] and 
                prev_macd_data["macd_line"] <= prev_macd_data["signal_line"]):
                self.last_signal = "buy"
            elif (macd_data["macd_line"] < macd_data["signal_line"] and 
                  prev_macd_data["macd_line"] >= prev_macd_data["signal_line"]):
                self.last_signal = "sell"
            else:
                self.last_signal = "hold"
        else:
            self.last_signal = "hold"
            
        return self.last_signal
        
    def get_signal(self, context: Dict[str, Any]) -> str:
        """Get a signal based on market context"""
        # Use price from context if available
        price = context.get("price", self.prices[-1] if self.prices else 100)
        
        # Get base signal from MACD
        base_signal = self.analyze(price)
        
        # Adjust signal based on market trend and sentiment
        market_trend = context.get("market_trend", "neutral")
        sentiment = context.get("sentiment", "neutral")
        
        # If MACD and market trend agree, strengthen the signal
        if base_signal == "buy" and market_trend in ["bullish", "strongly_bullish"]:
            final_signal = "buy"
        elif base_signal == "sell" and market_trend in ["bearish", "strongly_bearish"]:
            final_signal = "sell"
        # If they disagree strongly, be more cautious
        elif base_signal != "hold" and (
            (base_signal == "buy" and market_trend == "strongly_bearish") or
            (base_signal == "sell" and market_trend == "strongly_bullish")
        ):
            final_signal = "hold"
        # Otherwise stick with MACD signal
        else:
            final_signal = base_signal
            
        self.last_signal = final_signal
        return final_signal
        
    def generate_signal(self, prices: List[float]) -> str:
        """Generate a signal based on a window of prices"""
        if not prices or len(prices) < self.slow_period + 1:
            return "hold"
            
        # Calculate current MACD
        current_macd = self.calculate_macd(prices)
        
        # Calculate previous MACD
        prev_prices = prices[:-1]
        prev_macd = self.calculate_macd(prev_prices)
        
        # Check for crossovers
        if (current_macd["macd_line"] > current_macd["signal_line"] and 
            prev_macd["macd_line"] <= prev_macd["signal_line"]):
            signal = "buy"
        elif (current_macd["macd_line"] < current_macd["signal_line"] and 
              prev_macd["macd_line"] >= prev_macd["signal_line"]):
            signal = "sell"
        else:
            signal = "hold"
            
        self.last_signal = signal
        return signal
