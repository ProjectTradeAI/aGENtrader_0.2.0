"""
Structured Trading Decision Example

This script demonstrates the structure and format of a trading decision
without running the full agent-based decision process.
"""

import json
from datetime import datetime
from typing import Dict, Any

def create_example_decision() -> Dict[str, Any]:
    """
    Create an example of a structured trading decision.
    
    Returns:
        Example decision dictionary
    """
    # Example trading decision
    decision = {
        "decision": "BUY",
        "asset": "BTCUSDT",
        "entry_price": 88100,
        "stop_loss": 87500,
        "take_profit": 89200,
        "position_size_percent": 5.0,
        "confidence_score": 0.75,
        "reasoning": "Recent consolidation at support suggests a potential upward breakout. Price action indicates a bullish reversal pattern with positive RSI divergence.",
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTCUSDT",
        "price_at_analysis": 88081.87,
        "risk_reward_ratio": 2.1,
        "additional_metrics": {
            "volatility_24h": 2.3,
            "market_trend": "Bullish consolidation",
            "key_support_levels": [87500, 86000, 84000],
            "key_resistance_levels": [89000, 90000, 92000]
        },
        "technical_indicators": {
            "rsi_14": 58,
            "ma_50": 85400,
            "ma_200": 81200,
            "macd": {
                "signal": "positive crossover",
                "histogram": 0.35
            }
        }
    }
    
    return decision

def calculate_risk_metrics(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate risk metrics for a trading decision.
    
    Args:
        decision: Trading decision dictionary
        
    Returns:
        Updated decision with risk metrics
    """
    # Make a copy of the decision
    updated_decision = decision.copy()
    
    # Extract values
    entry = decision.get("entry_price", 0)
    stop = decision.get("stop_loss", 0)
    target = decision.get("take_profit", 0)
    position_size = decision.get("position_size_percent", 0)
    
    # Calculate risk
    if entry and stop and entry != stop:
        if decision["decision"] == "BUY":
            risk = (entry - stop) / entry
            reward = (target - entry) / entry
        elif decision["decision"] == "SELL":
            risk = (stop - entry) / entry
            reward = (entry - target) / entry
        else:  # HOLD
            risk = 0
            reward = 0
            
        if risk > 0:
            risk_reward_ratio = reward / risk
            updated_decision["risk_reward_ratio"] = risk_reward_ratio
            
            # Calculate risk amount
            account_size = 10000  # Example account size
            risk_amount = account_size * position_size / 100 * risk
            updated_decision["risk_amount"] = risk_amount
            updated_decision["potential_profit"] = risk_amount * risk_reward_ratio
    
    return updated_decision

def generate_decision_report(decision: Dict[str, Any]) -> str:
    """
    Generate a readable report from a trading decision.
    
    Args:
        decision: Trading decision dictionary
        
    Returns:
        Formatted report string
    """
    # Format report
    report = [
        f"{'=' * 50}",
        f"TRADING DECISION REPORT - {decision['asset']}",
        f"{'=' * 50}",
        f"Action:          {decision['decision']}",
        f"Timestamp:       {decision.get('timestamp', 'N/A')}",
        f"Current Price:   ${decision.get('price_at_analysis', 0):,.2f}",
        f"",
        f"--- TRADE PARAMETERS ---",
        f"Entry Price:     ${decision.get('entry_price', 0):,.2f}",
        f"Stop Loss:       ${decision.get('stop_loss', 0):,.2f}",
        f"Take Profit:     ${decision.get('take_profit', 0):,.2f}",
        f"Position Size:   {decision.get('position_size_percent', 0)}%",
        f"Risk-Reward:     {decision.get('risk_reward_ratio', 0):.2f}",
        f"Confidence:      {decision.get('confidence_score', 0) * 100:.1f}%",
        f"",
        f"--- REASONING ---",
        f"{decision.get('reasoning', 'No reasoning provided.')}",
        f"",
    ]
    
    # Add technical indicators if available
    if "technical_indicators" in decision:
        indicators = decision["technical_indicators"]
        report.extend([
            f"--- TECHNICAL INDICATORS ---",
            f"RSI (14):        {indicators.get('rsi_14', 'N/A')}",
            f"MA (50):         ${indicators.get('ma_50', 0):,.2f}",
            f"MA (200):        ${indicators.get('ma_200', 0):,.2f}",
            f"MACD Signal:     {indicators.get('macd', {}).get('signal', 'N/A')}",
            f""
        ])
    
    # Add risk metrics if available
    if "risk_amount" in decision:
        report.extend([
            f"--- RISK ANALYSIS ---",
            f"Risk Amount:     ${decision.get('risk_amount', 0):,.2f}",
            f"Potential Profit: ${decision.get('potential_profit', 0):,.2f}",
            f""
        ])
    
    return "\n".join(report)

def main():
    """Demonstrate structured trading decisions"""
    # Create example decision
    decision = create_example_decision()
    
    # Calculate risk metrics
    decision = calculate_risk_metrics(decision)
    
    # Display the decision in JSON format
    print("Structured Trading Decision (JSON format):")
    print(json.dumps(decision, indent=2))
    print("\n")
    
    # Generate and display a report
    report = generate_decision_report(decision)
    print("Trading Decision Report:")
    print(report)
    
    # Save to file
    with open("example_trading_decision.json", "w") as f:
        json.dump(decision, f, indent=2)
    
    print("\nExample decision saved to 'example_trading_decision.json'")

if __name__ == "__main__":
    main()