"""
aGENtrader v2 - Simple Trade Plan Agent Test

This script provides a simplified test for the TradePlanAgent without external dependencies.
"""

import logging
import json
from typing import Dict, Any
from agents.trade_plan_agent import create_trade_plan_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

def create_mock_decision() -> Dict[str, Any]:
    """Create a mock decision for testing"""
    return {
        "signal": "BUY",
        "confidence": 75,
        "reasoning": "Technical and sentiment indicators suggest an upward movement",
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
    }

def create_mock_market_data() -> Dict[str, Any]:
    """Create mock market data for testing"""
    return {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
        "ohlcv": [
            {"timestamp": "2025-05-01T00:00:00", "open": 49000, "high": 51000, "low": 48500, "close": 50000, "volume": 1000},
            {"timestamp": "2025-05-01T01:00:00", "open": 50000, "high": 50500, "low": 49800, "close": 50200, "volume": 900},
            {"timestamp": "2025-05-01T02:00:00", "open": 50200, "high": 50800, "low": 50100, "close": 50500, "volume": 1100},
            {"timestamp": "2025-05-01T03:00:00", "open": 50500, "high": 51000, "low": 50400, "close": 50900, "volume": 1300},
            {"timestamp": "2025-05-01T04:00:00", "open": 50900, "high": 51200, "low": 50700, "close": 51000, "volume": 1200},
        ]
    }

def create_mock_analyst_outputs() -> Dict[str, Any]:
    """Create mock analyst outputs for testing"""
    return {
        "technical_analysis": {
            "agent": "TechnicalAnalystAgent",
            "signal": "BUY",
            "confidence": 70,
            "reasoning": "Multiple technical indicators show bullish signals"
        },
        "sentiment_analysis": {
            "agent": "SentimentAnalystAgent",
            "signal": "BUY",
            "confidence": 80,
            "reasoning": "Market sentiment is positive with strong social media activity"
        },
        "liquidity_analysis": {
            "agent": "LiquidityAnalystAgent",
            "signal": "NEUTRAL",
            "confidence": 60,
            "reasoning": "Liquidity is balanced with no significant imbalances",
            "suggested_entry": 49900,
            "suggested_stop_loss": 49500
        }
    }

def test_simple_trade_plan_generation():
    """Test simple trade plan generation with mock data"""
    try:
        # Create a trade plan agent
        trade_plan_agent = create_trade_plan_agent()
        
        # Create mock inputs
        decision = create_mock_decision()
        market_data = create_mock_market_data()
        analyst_outputs = create_mock_analyst_outputs()
        
        # Generate a trade plan
        trade_plan = trade_plan_agent.generate_trade_plan(
            decision=decision,
            market_data=market_data,
            analyst_outputs=analyst_outputs
        )
        
        # Print the result
        logger.info(f"Trade plan generated successfully for {decision['signal']} signal with {decision['confidence']}% confidence")
        logger.info(f"Entry price: {trade_plan.get('entry_price')}")
        logger.info(f"Stop loss: {trade_plan.get('stop_loss')}")
        logger.info(f"Take profit: {trade_plan.get('take_profit')}")
        logger.info(f"Position size: {trade_plan.get('position_size')}")
        logger.info(f"Trade type: {trade_plan.get('trade_type')}")
        logger.info(f"Valid until: {trade_plan.get('valid_until')}")
        
        # Save the result to a file for inspection
        with open('trade_plan_test_result.json', 'w') as f:
            json.dump(trade_plan, f, indent=2)
            
        logger.info("Trade plan saved to trade_plan_test_result.json")
        
        return True
    except Exception as e:
        logger.error(f"Error testing trade plan agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Running simplified TradePlanAgent test")
    success = test_simple_trade_plan_generation()
    if success:
        logger.info("Test completed successfully!")
    else:
        logger.error("Test failed!")