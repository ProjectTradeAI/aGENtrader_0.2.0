"""
Test Structured Decision Making with Database Integration

This script tests the integration between database retrieval tools and structured
agent decision-making for trading recommendations.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("structured_decision_test")

# Ensure agents directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database functions and serialization utilities
from agents.database_retrieval_tool import (
    get_latest_price,
    get_recent_market_data,
    get_price_history,
    calculate_moving_average,
    calculate_rsi,
    find_support_resistance,
    get_market_summary,
    detect_patterns,
    calculate_volatility,
    CustomJSONEncoder
)

# Structured trading decision format
TRADING_DECISION_SCHEMA = {
    "decision": "",       # "BUY", "SELL", or "HOLD"
    "symbol": "",         # Trading symbol (e.g., "BTCUSDT")
    "price": 0.0,         # Current price
    "entry_price": 0.0,   # Recommended entry price
    "stop_loss": 0.0,     # Recommended stop loss
    "take_profit": 0.0,   # Recommended take profit
    "confidence": 0.0,    # Confidence score (0-100)
    "risk_level": "",     # "low", "medium", or "high"
    "reasoning": "",      # Reasoning behind the decision
    "timestamp": "",      # Decision timestamp
    "indicators": {}      # Key technical indicators
}

class DecisionMaker:
    """
    Test implementation of a structured decision maker using database data
    """
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.last_decision = None
    
    def _get_market_data(self) -> Dict[str, Any]:
        """Get market data from database"""
        logger.info(f"Retrieving market data for {self.symbol}")
        
        # Retrieve basic market data
        latest_price_json = get_latest_price(self.symbol)
        recent_data_json = get_recent_market_data(self.symbol, 10)
        indicators_json = get_market_summary(self.symbol)
        
        # Parse responses
        try:
            latest_price = json.loads(latest_price_json) if latest_price_json else {}
            recent_data = json.loads(recent_data_json) if recent_data_json else {"data": []}
            indicators = json.loads(indicators_json) if indicators_json else {}
            
            return {
                "latest_price": latest_price,
                "recent_data": recent_data.get("data", []),
                "indicators": indicators
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing market data: {e}")
            return {
                "latest_price": {},
                "recent_data": [],
                "indicators": {}
            }
    
    def _analyze_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data and detect patterns"""
        logger.info("Analyzing market data")
        
        analysis = {}
        
        # Extract latest price
        latest_price = data.get("latest_price", {})
        price = latest_price.get("close", 0.0)
        
        # Calculate trend based on recent data
        recent_data = data.get("recent_data", [])
        if len(recent_data) >= 2:
            prices = [point.get("close", 0.0) for point in recent_data]
            uptrend_count = sum(1 for i in range(1, len(prices)) if prices[i] > prices[i-1])
            downtrend_count = sum(1 for i in range(1, len(prices)) if prices[i] < prices[i-1])
            
            if uptrend_count > downtrend_count:
                analysis["trend"] = "uptrend"
            elif downtrend_count > uptrend_count:
                analysis["trend"] = "downtrend"
            else:
                analysis["trend"] = "sideways"
        else:
            analysis["trend"] = "unknown"
        
        # Get additional indicators
        indicators = data.get("indicators", {})
        
        # Combine into analysis result
        analysis["price"] = price
        analysis["indicators"] = indicators
        
        # Get technical indicators
        rsi_json = calculate_rsi(self.symbol, 14)
        rsi_data = json.loads(rsi_json) if rsi_json else {"rsi": 50}
        analysis["rsi"] = rsi_data.get("rsi", 50)
        
        # Get support/resistance
        sr_json = find_support_resistance(self.symbol)
        sr_data = json.loads(sr_json) if sr_json else {"support": [], "resistance": []}
        analysis["support_levels"] = sr_data.get("support", [])
        analysis["resistance_levels"] = sr_data.get("resistance", [])
        
        # Detect patterns
        patterns_json = detect_patterns(self.symbol)
        if patterns_json:
            try:
                patterns_data = json.loads(patterns_json) if isinstance(patterns_json, str) else patterns_json
                # Ensure patterns is a list of strings
                if "patterns" in patterns_data:
                    patterns = patterns_data.get("patterns", [])
                    # Convert any non-string items to strings
                    patterns = [str(p) if not isinstance(p, str) else p for p in patterns]
                    analysis["patterns"] = patterns
                else:
                    analysis["patterns"] = []
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Could not parse patterns JSON: {patterns_json}")
                analysis["patterns"] = []
        else:
            analysis["patterns"] = []
        
        return analysis
    
    def _generate_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading decision based on analysis"""
        logger.info("Generating trading decision")
        
        # Start with default decision structure
        decision = TRADING_DECISION_SCHEMA.copy()
        decision["symbol"] = self.symbol
        decision["price"] = analysis.get("price", 0.0)
        decision["timestamp"] = datetime.now().isoformat()
        
        # Extract key indicators
        price = analysis.get("price", 0.0)
        trend = analysis.get("trend", "unknown")
        rsi = analysis.get("rsi", 50)
        support_levels = analysis.get("support_levels", [])
        resistance_levels = analysis.get("resistance_levels", [])
        patterns = analysis.get("patterns", [])
        
        # Store indicators in decision
        decision["indicators"] = {
            "trend": trend,
            "rsi": rsi,
            "patterns": patterns
        }
        
        # Basic decision logic based on indicators
        # Note: This is a simplified example; real trading systems would use more sophisticated algorithms
        
        # RSI-based signals
        if rsi > 70:
            decision["decision"] = "SELL"
            decision["reasoning"] = "RSI indicates overbought conditions"
            decision["confidence"] = 70
            decision["risk_level"] = "medium"
        elif rsi < 30:
            decision["decision"] = "BUY"
            decision["reasoning"] = "RSI indicates oversold conditions"
            decision["confidence"] = 70
            decision["risk_level"] = "medium"
        else:
            # Trend-based signals
            if trend == "uptrend":
                decision["decision"] = "BUY"
                decision["reasoning"] = "Market is in an uptrend"
                decision["confidence"] = 60
                decision["risk_level"] = "medium"
            elif trend == "downtrend":
                decision["decision"] = "SELL"
                decision["reasoning"] = "Market is in a downtrend"
                decision["confidence"] = 60
                decision["risk_level"] = "medium"
            else:
                decision["decision"] = "HOLD"
                decision["reasoning"] = "No clear trend detected"
                decision["confidence"] = 50
                decision["risk_level"] = "low"
        
        # Pattern-based adjustments
        if patterns:
            decision["reasoning"] += f". Detected patterns: {', '.join(patterns)}"
            decision["confidence"] += 10
        
        # Calculate entry and exit prices
        if decision["decision"] == "BUY":
            # If buying, entry slightly above current price, stop below nearest support, take profit at nearest resistance
            decision["entry_price"] = price * 1.005  # 0.5% above current price
            
            # Set stop loss at the nearest support level below current price
            lower_supports = [s for s in support_levels if s < price]
            if lower_supports:
                decision["stop_loss"] = max(lower_supports) * 0.99  # 1% below nearest support
            else:
                decision["stop_loss"] = price * 0.95  # 5% below current price
            
            # Set take profit at the nearest resistance level above current price
            higher_resistances = [r for r in resistance_levels if r > price]
            if higher_resistances:
                decision["take_profit"] = min(higher_resistances) * 1.01  # 1% above nearest resistance
            else:
                decision["take_profit"] = price * 1.1  # 10% above current price
                
        elif decision["decision"] == "SELL":
            # If selling, entry slightly below current price, stop above nearest resistance, take profit at nearest support
            decision["entry_price"] = price * 0.995  # 0.5% below current price
            
            # Set stop loss at the nearest resistance level above current price
            higher_resistances = [r for r in resistance_levels if r > price]
            if higher_resistances:
                decision["stop_loss"] = min(higher_resistances) * 1.01  # 1% above nearest resistance
            else:
                decision["stop_loss"] = price * 1.05  # 5% above current price
            
            # Set take profit at the nearest support level below current price
            lower_supports = [s for s in support_levels if s < price]
            if lower_supports:
                decision["take_profit"] = max(lower_supports) * 0.99  # 1% below nearest support
            else:
                decision["take_profit"] = price * 0.9  # 10% below current price
        else:
            # Hold decision doesn't need entry/exit prices
            decision["entry_price"] = price
            decision["stop_loss"] = price * 0.9
            decision["take_profit"] = price * 1.1
        
        return decision
    
    def make_decision(self) -> Dict[str, Any]:
        """Make a trading decision based on market data"""
        market_data = self._get_market_data()
        analysis = self._analyze_market_data(market_data)
        decision = self._generate_decision(analysis)
        
        self.last_decision = decision
        
        # Log the decision
        logger.info(f"Generated trading decision: {decision['decision']} {self.symbol}")
        
        return decision

def save_decision(decision: Dict[str, Any], output_dir: str = "data/decisions") -> str:
    """Save decision to file"""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename based on timestamp and symbol
    symbol = decision.get("symbol", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/decision_{symbol}_{timestamp}.json"
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(decision, f, cls=CustomJSONEncoder, indent=2)
    
    logger.info(f"Decision saved to {filename}")
    
    return filename

def display_trading_decision(decision: Dict[str, Any]) -> None:
    """Display formatted trading decision"""
    print("\n" + "=" * 80)
    print(f" TRADING DECISION: {decision.get('decision', 'UNKNOWN')} {decision.get('symbol', '')} ".center(80, "="))
    print("=" * 80)
    
    print(f"\nSymbol: {decision.get('symbol', 'UNKNOWN')}")
    print(f"Decision: {decision.get('decision', 'UNKNOWN')}")
    print(f"Current Price: ${decision.get('price', 0):.2f}")
    print(f"Confidence: {decision.get('confidence', 0):.2f}%")
    print(f"Risk Level: {decision.get('risk_level', 'unknown')}")
    
    if decision.get('decision') != 'HOLD':
        print(f"\nEntry Price: ${decision.get('entry_price', 0):.2f}")
        print(f"Stop Loss: ${decision.get('stop_loss', 0):.2f}")
        print(f"Take Profit: ${decision.get('take_profit', 0):.2f}")
    
    print("\nReasoning:")
    print("-" * 80)
    reasoning = decision.get('reasoning', 'No reasoning provided')
    # Format reasoning as multiple lines for better readability
    if isinstance(reasoning, str):
        for line in reasoning.split("\n"):
            print(f"  {line}")
    else:
        print(f"  {reasoning}")
    
    # Print indicators if available
    if "indicators" in decision and decision["indicators"]:
        print("\nKey Indicators:")
        print("-" * 80)
        for key, value in decision["indicators"].items():
            print(f"  {key}: {value}")

def test_structured_decision_db() -> None:
    """Run structured decision test with database integration"""
    print("\n" + "=" * 80)
    print(" STRUCTURED DECISION TEST WITH DATABASE INTEGRATION ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Parse symbol from command line
    symbol = "BTCUSDT"
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    
    print(f"Testing structured decision making with database integration for {symbol}")
    
    try:
        # Create decision maker
        decision_maker = DecisionMaker(symbol)
        
        # Make decision
        print("\nGenerating trading decision...")
        decision = decision_maker.make_decision()
        
        # Display decision
        display_trading_decision(decision)
        
        # Save decision
        save_path = save_decision(decision)
        print(f"\nDecision saved to: {save_path}")
        
        print("\nTest completed successfully")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        print(f"\nError during test: {str(e)}")

if __name__ == "__main__":
    test_structured_decision_db()