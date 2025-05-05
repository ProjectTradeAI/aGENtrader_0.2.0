"""
aGENtrader v2 - Integrated Trade Plan Generation Test

This module tests the full integration of the enhanced TradePlanAgent
with the trading decision pipeline.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_trading_system import run_technical_analysis, run_sentiment_analysis
from run_trading_system import run_liquidity_analysis, run_funding_rate_analysis
from run_trading_system import run_open_interest_analysis, make_trading_decision
from run_trading_system import generate_trade_plan, create_data_provider

def test_enhanced_trade_plan_integration():
    """Test the enhanced trade plan agent integration"""
    symbol = "BTC/USDT"
    interval = "1h"
    
    logger.info(f"Testing enhanced trade plan integration for {symbol} at {interval} interval")
    
    # Create data provider
    data_provider = create_data_provider("binance")
    if not data_provider:
        logger.error("Failed to create data provider")
        return {"error": True, "message": "Failed to create data provider"}
    
    # Get current price
    try:
        ticker = data_provider.fetch_ticker(symbol)
        current_price = ticker.get('last', 0)
        logger.info(f"Current price for {symbol}: {current_price}")
    except Exception as e:
        logger.error(f"Error fetching current price: {str(e)}")
        current_price = 0
    
    # Create market data
    market_data = {
        "symbol": symbol,
        "interval": interval,
        "current_price": current_price,
        "data_provider": data_provider
    }
    
    # Step 1: Run all analyses
    analyses = {}
    
    logger.info("Running technical analysis...")
    technical_result = run_technical_analysis(market_data)
    if not technical_result.get('error', False):
        analyses['technical_analysis'] = technical_result
    
    logger.info("Running sentiment analysis...")
    sentiment_result = run_sentiment_analysis(market_data)
    if not sentiment_result.get('error', False):
        analyses['sentiment_analysis'] = sentiment_result
    
    logger.info("Running liquidity analysis...")
    liquidity_result = run_liquidity_analysis(market_data)
    if not liquidity_result.get('error', False):
        analyses['liquidity_analysis'] = liquidity_result
    
    logger.info("Running funding rate analysis...")
    funding_result = run_funding_rate_analysis(market_data)
    if not funding_result.get('error', False):
        analyses['funding_rate_analysis'] = funding_result
    
    logger.info("Running open interest analysis...")
    open_interest_result = run_open_interest_analysis(market_data)
    if not open_interest_result.get('error', False):
        analyses['open_interest_analysis'] = open_interest_result
        
    logger.info(f"Completed analyses: {', '.join(analyses.keys())}")
    
    # Step 2: Make a trading decision
    logger.info("Making trading decision...")
    decision = make_trading_decision(analyses, market_data)
    
    if decision.get('error', False):
        logger.error(f"Error making decision: {decision.get('message', 'Unknown error')}")
        return decision
    
    logger.info(f"Decision: {decision.get('signal')} with {decision.get('confidence')}% confidence")
    
    # Step 3: Generate an enhanced trade plan
    if decision.get('signal') in ['BUY', 'SELL']:
        logger.info("Generating enhanced trade plan...")
        trade_plan = generate_trade_plan(decision, market_data, analyses)
        
        # Log detailed trade plan information
        logger.info(f"Signal: {trade_plan.get('signal')}")
        logger.info(f"Entry Price: {trade_plan.get('entry_price')}")
        logger.info(f"Stop Loss: {trade_plan.get('stop_loss')}")
        logger.info(f"Take Profit: {trade_plan.get('take_profit')}")
        logger.info(f"Position Size: {trade_plan.get('position_size')}")
        logger.info(f"Trade Type: {trade_plan.get('trade_type')}")
        logger.info(f"Valid Until: {trade_plan.get('valid_until')}")
        
        # Enhanced metrics
        if 'risk_snapshot' in trade_plan:
            risk = trade_plan['risk_snapshot']
            logger.info(f"Risk: R:R Ratio: {risk.get('risk_reward_ratio')}")
            logger.info(f"Risk: Portfolio Risk: {risk.get('portfolio_risk_percent')}%")
            logger.info(f"Risk: Exposure: {risk.get('portfolio_exposure_percent')}%")
            
        logger.info(f"Used Fallback Calculation: {trade_plan.get('fallback_plan', False)}")
        
        # Save to file for inspection
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"enhanced_trade_plan_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(trade_plan, f, indent=2)
            
        logger.info(f"Enhanced trade plan saved to {output_file}")
        return trade_plan
    else:
        logger.info(f"No trade plan generated for {decision.get('signal')} signal")
        return decision

if __name__ == "__main__":
    try:
        result = test_enhanced_trade_plan_integration()
        if not result.get('error', False):
            logger.info("Enhanced trade plan integration test completed successfully!")
        else:
            logger.error(f"Enhanced trade plan integration test failed: {result.get('message')}")
    except Exception as e:
        logger.error(f"Unhandled exception in trade plan test: {str(e)}", exc_info=True)