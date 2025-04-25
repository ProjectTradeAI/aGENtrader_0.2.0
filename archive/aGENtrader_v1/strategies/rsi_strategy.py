
"""
RSI Strategy Module

Implements a trading strategy based on the Relative Strength Index (RSI) indicator.
"""

import numpy as np
from typing import List, Dict, Any

class RSIStrategy:
    def __init__(self, overbought=70, oversold=30, period=14):
        """Initialize the RSI Strategy"""
        self.name = "RSI Strategy"
        self.overbought = overbought
        self.oversold = oversold
        self.period = period
        self.prices = []
        self.last_signal = "hold"
        
    def calculate_rsi(self, prices: List[float]) -> float:
        """Calculate the RSI value from a list of prices"""
        if len(prices) < self.period + 1:
            return 50  # Default to neutral if not enough data
            
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Calculate gains and losses
        gains = np.copy(deltas)
        losses = np.copy(deltas)
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-self.period:])
        avg_loss = np.mean(losses[-self.period:])
        
        if avg_loss == 0:
            return 100  # If no losses, RSI is 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def analyze(self, price: float) -> str:
        """Analyze the current price and return a trading signal"""
        self.prices.append(price)
        
        # Keep the price list at a reasonable size
        if len(self.prices) > self.period * 3:
            self.prices = self.prices[-(self.period * 3):]
            
        if len(self.prices) < self.period + 1:
            self.last_signal = "hold"
            return self.last_signal
            
        # Calculate RSI
        rsi = self.calculate_rsi(self.prices)
        
        # Generate signal based on RSI value
        if rsi < self.oversold:
            self.last_signal = "buy"
        elif rsi > self.overbought:
            self.last_signal = "sell"
        else:
            self.last_signal = "hold"
            
        return self.last_signal
        
    def get_signal(self, context: Dict[str, Any]) -> str:
        """Get a signal based on market context"""
        # Use price from context if available
        price = context.get("price", self.prices[-1] if self.prices else 100)
        
        # Get base signal from RSI
        base_signal = self.analyze(price)
        
        # Adjust signal based on market trend
        market_trend = context.get("market_trend", "neutral")
        sentiment = context.get("sentiment", "neutral")
        
        # If RSI and market trend agree, strengthen the signal
        if base_signal == "buy" and market_trend in ["bullish", "strongly_bullish"]:
            final_signal = "buy"
        elif base_signal == "sell" and market_trend in ["bearish", "strongly_bearish"]:
            final_signal = "sell"
        # If they disagree, be more cautious
        elif base_signal != "hold" and (
            (base_signal == "buy" and market_trend in ["bearish", "strongly_bearish"]) or
            (base_signal == "sell" and market_trend in ["bullish", "strongly_bullish"])
        ):
            final_signal = "hold"
        else:
            final_signal = base_signal
            
        self.last_signal = final_signal
        return final_signal
        
    def generate_signal(self, prices: List[float]) -> str:
        """Generate a signal based on a window of prices"""
        if not prices or len(prices) < self.period + 1:
            return "hold"
            
        # Calculate RSI
        rsi = self.calculate_rsi(prices)
        
        # Generate signal based on RSI value
        if rsi < self.oversold:
            signal = "buy"
        elif rsi > self.overbought:
            signal = "sell"
        else:
            signal = "hold"
            
        self.last_signal = signal
        return signal
