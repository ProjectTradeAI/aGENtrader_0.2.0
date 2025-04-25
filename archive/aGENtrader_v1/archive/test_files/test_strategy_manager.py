
"""
Test script for the Strategy Manager Agent
"""

import asyncio
import json
from agents.strategy_manager import StrategyManagerAgent
from agents.market_analysis import MarketAnalysisAgent

async def test_strategy_manager():
    """Test the Strategy Manager Agent"""
    # Initialize agents
    market_agent = MarketAnalysisAgent()
    strategy_agent = StrategyManagerAgent()
    
    print("Testing Strategy Manager Agent...")
    
    # Test symbols
    symbols = ["BTC", "ETH", "SOL", "MATIC"]
    
    # Get market analysis for each symbol
    market_results = {}
    for symbol in symbols:
        analysis = await market_agent.analyze_trends(symbol)
        market_results[symbol] = analysis
        print(f"\nMarket analysis for {symbol}:")
        print(f"  Trend: {analysis['trend']}")
        print(f"  Confidence: {analysis['confidence']}%")
        print(f"  Signal: {analysis['signal']}")
    
    # Simulate sentiment data
    sentiment_results = {
        "BTC": {
            "sentiment": "positive",
            "score": 0.65,
            "signal": {"signal": "buy", "confidence": 70}
        },
        "ETH": {
            "sentiment": "neutral",
            "score": 0.1,
            "signal": {"signal": "hold", "confidence": 55}
        },
        "SOL": {
            "sentiment": "negative",
            "score": -0.3,
            "signal": {"signal": "sell", "confidence": 60}
        },
        "MATIC": {
            "sentiment": "positive",
            "score": 0.4,
            "signal": {"signal": "buy", "confidence": 65}
        }
    }
    
    # Test strategy library functions
    print("\nStrategy library risk profiles:")
    risk_profiles = strategy_agent.strategy_library.get("risk_profiles", {})
    for profile, settings in risk_profiles.items():
        print(f"  {profile.upper()}: max position {settings.get('max_position_size_pct')}%, " +
              f"SL {settings.get('stop_loss_pct')}%, TP {settings.get('take_profit_pct')}%")
    
    # Analyze strategy performance
    strategy_agent.analyze_strategy_performance(market_results, sentiment_results)
    
    # Process each symbol
    print("\nStrategy decisions:")
    for symbol in symbols:
        decision = strategy_agent.process_market_update(
            symbol, 
            market_results.get(symbol, {}),
            sentiment_results.get(symbol, {})
        )
        
        print(f"\n{symbol} decision:")
        print(f"  Signal: {decision['signal']}")
        print(f"  Strategy: {decision['strategy']}")
        print(f"  Risk profile: {decision['risk_profile']}")
        print(f"  Confidence: {decision['confidence']}%")
        print(f"  Reason: {decision['reason']}")
    
    # Test parameter optimization for RSI strategy
    print("\nOptimizing RSI strategy parameters for BTC:")
    params = strategy_agent.optimize_strategy_parameters("RSIStrategy", "BTC")
    if params:
        print(f"  Optimized parameters: {params}")
    
    # Get strategy performance metrics
    performance = strategy_agent.get_strategy_performance()
    print("\nStrategy performance metrics:")
    print(json.dumps(performance, indent=2))

if __name__ == "__main__":
    asyncio.run(test_strategy_manager())
