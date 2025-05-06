#!/usr/bin/env python3
"""
Test script for Grok integration in the aGENtrader v0.2.2 system.
"""

import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_grok_client():
    """Test the GrokClient directly"""
    try:
        from models.grok_client import GrokClient
        
        client = GrokClient()
        
        if not client.is_available():
            logger.error("GrokClient is not available. Please check XAI_API_KEY environment variable.")
            return False
            
        logger.info("GrokClient is available. Testing text summarization...")
        
        # Test text summarization
        text = """
        Bitcoin's price action has been consolidating in a tight range between $45,000 and $50,000 for the past week,
        with decreasing volatility. Trading volume has dropped by 15% compared to the previous week, suggesting
        trader uncertainty. Technical indicators show a slight bullish bias with RSI at
        58 and MACD histogram showing minimal positive momentum.
        """
        
        summary = client.summarize_text(text)
        logger.info(f"Summary: {summary}")
        
        # Test sentiment analysis
        sentiment = client.analyze_sentiment(text)
        logger.info(f"Sentiment analysis: {sentiment}")
        
        # Test trade summary formatting
        trade_plan = {
            "symbol": "BTC/USDT",
            "interval": "1h",
            "signal": "BUY",
            "confidence": 85,
            "entry_price": 48750.25,
            "stop_loss": 47500.00,
            "take_profit": 51000.00,
            "position_size": 0.2,
            "risk_reward_ratio": 1.5
        }
        
        agent_analyses = [
            {
                "agent_name": "TechnicalAnalystAgent",
                "signal": "BUY",
                "confidence": 80,
                "reasoning": "Price broke above key resistance with increasing volume and bullish MACD crossover."
            },
            {
                "agent_name": "SentimentAnalystAgent",
                "signal": "NEUTRAL",
                "confidence": 65,
                "reasoning": "Social sentiment indicators show mixed signals with slight positive bias."
            },
            {
                "agent_name": "LiquidityAnalystAgent",
                "signal": "BUY",
                "confidence": 75,
                "reasoning": "Order book shows strong support and thin resistance, suggesting upward path of least resistance."
            }
        ]
        
        trade_summary = client.format_trade_summary(
            trade_plan=trade_plan,
            agent_analyses=agent_analyses,
            style="formal"
        )
        
        logger.info(f"Trade summary:\n{json.dumps(trade_summary, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing GrokClient: {str(e)}", exc_info=True)
        return False
        
def test_tone_agent():
    """Test the ToneAgent with GrokClient integration"""
    try:
        from agents.tone_agent import ToneAgent
        
        # Create a sample analysis results dict
        analysis_results = {
            "technical_analysis": {
                "signal": "BUY",
                "confidence": 80,
                "reasoning": "Price broke above key resistance with increasing volume and bullish MACD crossover."
            },
            "sentiment_analysis": {
                "signal": "NEUTRAL",
                "confidence": 65,
                "reasoning": "Social sentiment indicators show mixed signals with slight positive bias."
            },
            "liquidity_analysis": {
                "signal": "BUY",
                "confidence": 75,
                "reasoning": "Order book shows strong support and thin resistance, suggesting upward path of least resistance."
            }
        }
        
        # Create a sample final decision
        final_decision = {
            "signal": "BUY",
            "confidence": 85,
            "directional_confidence": 82,
            "conflict_score": 15,
            "current_price": 48750.25,
            "entry_price": 48750.25,
            "stop_loss": 47500.00,
            "take_profit": 51000.00,
            "position_size": 0.2,
            "risk_reward_ratio": 1.5
        }
        
        # Create ToneAgent instance
        tone_agent = ToneAgent()
        
        # Generate summary
        start_time = datetime.now()
        summary = tone_agent.generate_summary(
            analysis_results=analysis_results,
            final_decision=final_decision,
            symbol="BTC/USDT",
            interval="1h"
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"ToneAgent generate_summary completed in {duration:.2f} seconds")
        logger.info(f"Summary:\n{json.dumps(summary, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing ToneAgent: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Testing Grok integration in aGENtrader v0.2.2")
    
    # Test GrokClient
    if test_grok_client():
        logger.info("GrokClient test completed successfully")
    else:
        logger.error("GrokClient test failed")
        
    # Test ToneAgent
    if test_tone_agent():
        logger.info("ToneAgent test completed successfully")
    else:
        logger.error("ToneAgent test failed")