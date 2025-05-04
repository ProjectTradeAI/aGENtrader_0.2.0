"""
aGENtrader v2 - Trade Plan Testing with Mock Data

This script tests the TradePlanAgent with mock data to ensure it functions correctly
without requiring real-time market data access.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import trade plan agent module
from agents.trade_plan_agent import create_trade_plan_agent

def generate_mock_market_data() -> Dict[str, Any]:
    """Generate mock market data for testing"""
    # Current time
    now = datetime.now()
    
    # Generate mock candles for the last 30 periods
    mock_candles = []
    base_price = 50000.0
    for i in range(30, 0, -1):
        candle_time = now - timedelta(hours=i)
        open_price = base_price * (1 + (i % 5 - 2) * 0.01)
        high_price = open_price * 1.02
        low_price = open_price * 0.98
        close_price = open_price * (1 + (i % 7 - 3) * 0.005)
        volume = 100 + i * 10
        
        mock_candles.append({
            'timestamp': int(candle_time.timestamp() * 1000),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
        
        # Update base price for next candle
        base_price = close_price
    
    # Create mock market data
    mock_data = {
        'symbol': 'BTC/USDT',
        'interval': '1h',
        'current_price': mock_candles[-1]['close'],
        'ohlcv': mock_candles
    }
    
    return mock_data

def generate_mock_analyst_outputs() -> Dict[str, Dict[str, Any]]:
    """Generate mock analyst outputs for testing"""
    # Mock technical analysis
    technical_analysis = {
        'agent': 'TechnicalAnalystAgent',
        'signal': 'BUY',
        'confidence': 75,
        'indicators': {
            'rsi': 65,
            'macd': 'bullish',
            'ema': 'uptrend'
        },
        'reasoning': 'Strong bullish momentum with positive MACD crossover'
    }
    
    # Mock sentiment analysis
    sentiment_analysis = {
        'agent': 'SentimentAnalystAgent',
        'signal': 'BUY',
        'confidence': 68,
        'sentiment_score': 0.78,
        'reasoning': 'Positive market sentiment with bullish news coverage'
    }
    
    # Mock liquidity analysis
    liquidity_analysis = {
        'agent': 'LiquidityAnalystAgent',
        'signal': 'NEUTRAL',
        'confidence': 60,
        'support_levels': [48500, 47800, 47000],
        'resistance_levels': [51200, 52500, 54000],
        'suggested_entry': 50200,
        'suggested_stop_loss': 48400,
        'reasoning': 'Multiple liquidity clusters identified with strong support at 48500'
    }
    
    return {
        'technical_analysis': technical_analysis,
        'sentiment_analysis': sentiment_analysis,
        'liquidity_analysis': liquidity_analysis
    }

def generate_mock_decision() -> Dict[str, Any]:
    """Generate a mock trading decision"""
    return {
        'signal': 'BUY',
        'confidence': 72.5,
        'contributing_agents': ['TechnicalAnalystAgent', 'SentimentAnalystAgent'],
        'reasoning': 'Technical and sentiment indicators suggesting bullish momentum',
        'timestamp': datetime.now().isoformat()
    }

def test_trade_plan_agent():
    """Test the TradePlanAgent with mock data"""
    logger.info("Testing TradePlanAgent with mock data")
    
    # Generate mock data
    market_data = generate_mock_market_data()
    analyst_outputs = generate_mock_analyst_outputs()
    decision = generate_mock_decision()
    
    # Configuration for TradePlanAgent
    config = {
        'risk_reward_ratio': 2.0,
        'portfolio_risk_per_trade': 0.02,  # 2% risk per trade
        'default_tags': ['test', 'mock_data']
    }
    
    # Create trade plan agent
    trade_plan_agent = create_trade_plan_agent(config)
    
    # Generate trade plan
    logger.info(f"Generating trade plan for {decision['signal']} decision with {decision['confidence']}% confidence")
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs=analyst_outputs
    )
    
    # Log the trade plan
    if not trade_plan.get('error', False):
        logger.info("===== ENHANCED TRADE PLAN =====")
        logger.info(f"Signal: {trade_plan.get('signal')}")
        logger.info(f"Entry Price: {trade_plan.get('entry_price')}")
        logger.info(f"Stop Loss: {trade_plan.get('stop_loss')}")
        logger.info(f"Take Profit: {trade_plan.get('take_profit')}")
        logger.info(f"Position Size: {trade_plan.get('position_size')}")
        logger.info(f"Trade Type: {trade_plan.get('trade_type')}")
        logger.info(f"Valid Until: {trade_plan.get('valid_until')}")
        
        # Risk metrics
        if 'risk_snapshot' in trade_plan:
            risk = trade_plan['risk_snapshot']
            logger.info("===== RISK METRICS =====")
            logger.info(f"R:R Ratio: {risk.get('risk_reward_ratio')}")
            logger.info(f"Portfolio Risk: {risk.get('portfolio_risk_percent')}%")
            logger.info(f"Portfolio Exposure: {risk.get('portfolio_exposure_percent')}%")
        
        # Fallback info
        logger.info(f"Used Fallback: {trade_plan.get('fallback_plan', False)}")
        
        # Save to file for inspection
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"mock_trade_plan_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(trade_plan, f, indent=2)
        
        logger.info(f"Trade plan saved to {output_file}")
        return trade_plan
    else:
        logger.error(f"Error generating trade plan: {trade_plan.get('message')}")
        return None

if __name__ == "__main__":
    try:
        result = test_trade_plan_agent()
        if result:
            logger.info("TradePlanAgent test completed successfully!")
    except Exception as e:
        logger.error(f"Error testing TradePlanAgent: {str(e)}", exc_info=True)