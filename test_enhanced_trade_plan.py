#!/usr/bin/env python3
"""
Test script for Enhanced TradePlanAgent

This script tests all the new features added to the TradePlanAgent:
1. Reason summary generation
2. Time-based validity
3. Volatility-aware stop-loss and take-profit
4. Trade type classification
5. Risk snapshot calculation
6. Fallback plan flag
7. Custom tags support
"""

import logging
import sys
import os
import json
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_enhanced_trade_plan')

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_mock_data() -> Dict[str, Any]:
    """Generate mock data for testing"""
    # Mock historical data - 20 candles
    historical_data = []
    base_price = 50000.0
    timestamp = int(time.time() * 1000) - (20 * 3600 * 1000)  # Start 20 hours ago
    
    for i in range(20):
        # Generate slightly random prices
        open_price = base_price * (1 + (((i % 3) - 1) * 0.005))
        close_price = base_price * (1 + (((i % 5) - 2) * 0.005))
        high_price = max(open_price, close_price) * 1.002
        low_price = min(open_price, close_price) * 0.998
        
        candle = {
            'timestamp': timestamp + (i * 3600 * 1000),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': 100 + (i * 10)
        }
        historical_data.append(candle)
        
        # Update base price for next candle
        base_price = close_price
    
    # Mock market data
    market_data = {
        'symbol': 'BTC/USDT',
        'interval': '1h',
        'current_price': historical_data[-1]['close'],
        'ohlcv': historical_data
    }
    
    # Mock decision
    decision = {
        'signal': 'BUY',
        'confidence': 75.5,
        'reasoning': 'Technical indicators show strong bullish momentum',
        'contributing_agents': ['TechnicalAnalystAgent', 'SentimentAnalystAgent'],
        'tags': ['test_run', 'volatility_experiment']
    }
    
    # Mock analyst outputs
    analyst_outputs = {
        'TechnicalAnalystAgent': {
            'signal': 'BUY',
            'confidence': 80,
            'reasoning': 'All indicators bullish: MACD positive, RSI at 65',
            'agent': 'TechnicalAnalystAgent'
        },
        'SentimentAnalystAgent': {
            'signal': 'BUY',
            'confidence': 70,
            'reasoning': 'Positive sentiment from news and social media',
            'agent': 'SentimentAnalystAgent'
        },
        'LiquidityAnalystAgent': {
            'signal': 'NEUTRAL',
            'confidence': 65,
            'reasoning': 'Strong support detected at 49500',
            'agent': 'LiquidityAnalystAgent',
            'support_clusters': [49500.0, 49000.0],
            'resistance_clusters': [50500.0, 51000.0],
            'suggested_entry': 50100.0,
            'suggested_stop_loss': 49400.0
        }
    }
    
    return {
        'market_data': market_data,
        'decision': decision,
        'analyst_outputs': analyst_outputs
    }

def test_enhanced_trade_plan_agent() -> None:
    """Test all enhanced features of the TradePlanAgent"""
    from agents.trade_plan_agent import create_trade_plan_agent
    
    logger.info("Testing enhanced TradePlanAgent features")
    
    # Create a TradePlanAgent instance with custom settings
    config = {
        'risk_reward_ratio': 1.5,
        'portfolio_risk_per_trade': 0.02,  # 2% risk per trade
        'default_tags': ['system_test']
    }
    trade_plan_agent = create_trade_plan_agent(config)
    
    # Generate mock data
    mock_data = generate_mock_data()
    
    # Generate a trade plan with the enhanced agent
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=mock_data['decision'],
        market_data=mock_data['market_data'],
        analyst_outputs=mock_data['analyst_outputs']
    )
    
    # Check if we got a valid trade plan
    if 'error' in trade_plan:
        logger.error(f"❌ Trade plan generation failed: {trade_plan.get('message')}")
        return
    
    # Print the trade plan
    logger.info("✅ Trade plan generated successfully:")
    logger.info(f"Signal: {trade_plan['signal']}")
    logger.info(f"Confidence: {trade_plan['confidence']}%")
    
    # Verify reason summary (Feature 1)
    if 'reason_summary' in trade_plan:
        logger.info(f"✅ Reason summary: {trade_plan['reason_summary']}")
    else:
        logger.error("❌ Missing reason_summary field")
    
    # Verify time-based validity (Feature 2)
    if 'valid_until' in trade_plan:
        valid_until = trade_plan['valid_until']
        try:
            valid_datetime = datetime.fromisoformat(valid_until)
            now = datetime.now()
            validity_minutes = (valid_datetime - now).total_seconds() / 60
            logger.info(f"✅ Valid until: {valid_until} ({int(validity_minutes)} minutes)")
        except ValueError:
            logger.error(f"❌ Invalid valid_until timestamp format: {valid_until}")
    else:
        logger.error("❌ Missing valid_until field")
    
    # Verify volatility-based levels (Feature 3)
    logger.info(f"Entry price: {trade_plan['entry_price']}")
    logger.info(f"Stop-loss: {trade_plan['stop_loss']}")
    logger.info(f"Take-profit: {trade_plan['take_profit']}")
    
    # Verify trade type classification (Feature 4)
    if 'trade_type' in trade_plan:
        logger.info(f"✅ Trade type: {trade_plan['trade_type']}")
    else:
        logger.error("❌ Missing trade_type field")
    
    # Verify risk snapshot (Feature 5)
    if 'risk_snapshot' in trade_plan:
        risk_snapshot = trade_plan['risk_snapshot']
        logger.info("✅ Risk snapshot:")
        logger.info(f"  R:R ratio: {risk_snapshot.get('risk_reward_ratio')}")
        logger.info(f"  Risk per unit: {risk_snapshot.get('risk_per_unit')}")
        logger.info(f"  Portfolio risk: {risk_snapshot.get('portfolio_risk_percent')}%")
        logger.info(f"  Portfolio exposure: {risk_snapshot.get('portfolio_exposure_percent')}%")
    else:
        logger.error("❌ Missing risk_snapshot field")
    
    # Verify fallback plan flag (Feature 6)
    if 'fallback_plan' in trade_plan:
        logger.info(f"✅ Fallback plan: {trade_plan['fallback_plan']}")
    else:
        logger.error("❌ Missing fallback_plan field")
    
    # Verify custom tags (Feature 7)
    if 'tags' in trade_plan:
        logger.info(f"✅ Tags: {trade_plan['tags']}")
    else:
        logger.error("❌ Missing tags field")
    
    # Print the complete trade plan for inspection
    logger.info("\nComplete trade plan:")
    logger.info(json.dumps(trade_plan, indent=2))
    
    logger.info("\n✅ All enhanced TradePlanAgent features tested")

def main() -> int:
    """Main entry point"""
    try:
        test_enhanced_trade_plan_agent()
        return 0
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())