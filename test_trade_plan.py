#!/usr/bin/env python3
"""
Test script for the TradePlanAgent.

This script creates a TradePlanAgent instance and tests it with
a sample decision and market data.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_trade_plan')

# Import the TradePlanAgent
from agents.trade_plan_agent import TradePlanAgent

# Import the DecisionAgent for comparison
from agents.decision_agent import DecisionAgent

# Import a data provider for market data
from binance_data_provider import BinanceDataProvider

def test_trade_plan_agent():
    """Test the TradePlanAgent with sample data."""
    logger.info("Testing TradePlanAgent...")
    
    # Create a data provider
    data_provider = BinanceDataProvider()
    
    # Create a TradePlanAgent with custom configuration
    config = {
        "risk_reward_ratio": 1.5,
        "max_position_size": 1.0, 
        "min_position_size": 0.1,
        "low_confidence_threshold": 50,
        "medium_confidence_threshold": 65,
        "high_confidence_threshold": 80,
        "low_confidence_size": 0.3,
        "medium_confidence_size": 0.6,
        "high_confidence_size": 0.8
    }
    trade_plan_agent = TradePlanAgent(config=config)
    
    # Test symbol and interval
    symbol = "BTC/USDT"
    interval = "1h"
    
    try:
        # Try to get current price and depth data for realistic testing
        current_price = None
        liquidity_analysis = None
        
        try:
            # Fetch current price
            ticker = data_provider.fetch_ticker(symbol)
            current_price = ticker.get('last')
            logger.info(f"Current price for {symbol}: {current_price}")
            
            # Fetch market depth data
            depth = data_provider.fetch_market_depth(symbol.replace("/", ""))
            
            # Mock simplified liquidity analysis
            if depth and 'bids' in depth and 'asks' in depth:
                bids = depth['bids']
                asks = depth['asks']
                
                if bids and asks:
                    # Get top bid and ask
                    top_bid = float(bids[0][0])
                    top_ask = float(asks[0][0])
                    
                    # Simple support and resistance
                    support_level = top_bid * 0.99
                    resistance_level = top_ask * 1.01
                    
                    # Mock suggested entry and stop loss
                    suggested_entry = current_price
                    suggested_stop_loss = support_level if current_price > support_level else current_price * 0.98
                    
                    liquidity_analysis = {
                        "suggested_entry": suggested_entry,
                        "suggested_stop_loss": suggested_stop_loss,
                        "support_clusters": [support_level],
                        "resistance_clusters": [resistance_level],
                        "gaps": []
                    }
                    
                    logger.info(f"Created mock liquidity analysis with suggested entry: {suggested_entry}, stop loss: {suggested_stop_loss}")
            
        except Exception as e:
            logger.warning(f"Could not fetch real market data: {str(e)}")
            logger.warning("Using fallback test data")
            
            # Fallback to fixed test values if real data fetching fails
            current_price = 50000.0
        
        # Create sample decision
        sample_decision = {
            "signal": "BUY",
            "confidence": 76,
            "reasoning": "Strong technical signals with supportive sentiment",
            "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"]
        }
        
        # Create sample market data
        market_data = {
            "symbol": symbol,
            "interval": interval,
            "current_price": current_price,
            "data_provider": data_provider
        }
        
        # Generate trade plan from the sample decision
        trade_plan = trade_plan_agent.generate_trade_plan(
            decision=sample_decision,
            market_data=market_data,
            analyst_outputs={"liquidity_analysis": liquidity_analysis} if liquidity_analysis else {}
        )
        
        # Print the trade plan
        logger.info(f"Generated trade plan: {json.dumps(trade_plan, indent=2)}")
        
        # Also test the full make_decision workflow
        logger.info("Testing make_decision flow with multiple analyst outputs...")
        
        # Create sample analyst outputs
        analyst_outputs = {
            "technical_analysis": {
                "signal": "BUY",
                "confidence": 80,
                "explanation": ["Prices above all major MAs, MACD bullish"]
            },
            "sentiment_analysis": {
                "signal": "BUY",
                "confidence": 75,
                "explanation": ["Positive sentiment on social media"]
            },
            "liquidity_analysis": liquidity_analysis or {
                "signal": "NEUTRAL",
                "confidence": 60,
                "explanation": ["Balanced order book"]
            }
        }
        
        # Convert our dictionary of analyst outputs to a list for the make_decision method
        analyses_list = []
        for agent_name, analysis in analyst_outputs.items():
            # Add agent name to each analysis if not already there
            if 'agent' not in analysis:
                analysis['agent'] = agent_name
            
            # Add market data to each analysis for easier access
            if 'market_data' not in analysis and current_price is not None:
                analysis['market_data'] = {
                    'symbol': symbol,
                    'current_price': current_price
                }
                
            analyses_list.append(analysis)
            
        # Call the make_decision method
        full_decision = trade_plan_agent.make_decision(
            symbol=symbol,
            interval=interval,
            analyses=analyses_list
        )
        
        # Print the full decision with trade plan
        logger.info(f"Full decision with trade plan: {json.dumps(full_decision, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing TradePlanAgent: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_trade_plan_agent():
        logger.info("TradePlanAgent test completed successfully")
        sys.exit(0)
    else:
        logger.error("TradePlanAgent test failed")
        sys.exit(1)