"""
aGENtrader v2 - Trade Plan Integration with Grok Sentiment

This script tests the integration between TradePlanAgent and
the SentimentAggregatorAgent using Grok's xAI API for enhanced
market sentiment analysis.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import agent modules
from agents.trade_plan_agent import create_trade_plan_agent

def create_mock_grok_sentiment() -> Dict[str, Any]:
    """Create a mock SentimentAggregatorAgent response with Grok sentiment"""
    return {
        "agent": "SentimentAggregatorAgent",
        "signal": "BUY",
        "confidence": 78,
        "grok_sentiment_summary": "Market sentiment is bullish with institutional investors accumulating BTC. Recent regulatory clarity has improved overall market outlook. Altcoins are showing strong momentum.",
        "sentiment_rating": 4.2,
        "market_drivers": [
            "Positive regulatory developments",
            "Institutional accumulation",
            "Technical breakout from key resistance"
        ],
        "market_risks": [
            "Macroeconomic uncertainty",
            "Potential profit-taking at resistance levels"
        ],
        "time_horizon": "medium-term",
        "timestamp": datetime.now().isoformat()
    }

def create_mock_technical_analysis() -> Dict[str, Any]:
    """Create a mock TechnicalAnalystAgent response"""
    return {
        "agent": "TechnicalAnalystAgent",
        "signal": "BUY",
        "confidence": 82,
        "reasoning": "Multiple indicators showing bullish divergence with strong uptrend",
        "indicators": [
            {"name": "MACD", "value": 0.35, "signal": "BUY"},
            {"name": "RSI", "value": 62, "signal": "BUY"},
            {"name": "MA Crossover", "value": "Positive", "signal": "BUY"}
        ]
    }

def create_mock_liquidity_analysis() -> Dict[str, Any]:
    """Create a mock LiquidityAnalystAgent response"""
    return {
        "agent": "LiquidityAnalystAgent",
        "signal": "NEUTRAL",
        "confidence": 65,
        "reasoning": "Liquidity zones identified at 49500 and 51200",
        "support_clusters": [49500, 48900, 47800],
        "resistance_clusters": [51200, 52500, 54000]
    }

def create_mock_funding_rate_analysis() -> Dict[str, Any]:
    """Create a mock FundingRateAnalystAgent response"""
    return {
        "agent": "FundingRateAnalystAgent",
        "signal": "BUY",
        "confidence": 70,
        "reasoning": "Funding rates neutral to slightly positive, bullish long-term",
        "funding_summary": "Neutral funding suggests balanced market without overleveraging"
    }

def create_mock_open_interest_analysis() -> Dict[str, Any]:
    """Create a mock OpenInterestAnalystAgent response"""
    return {
        "agent": "OpenInterestAnalystAgent",
        "signal": "BUY",
        "confidence": 75,
        "reasoning": "Rising open interest with price increase confirms trend strength",
        "oi_summary": "Growing OI supports uptrend continuation"
    }

def test_trade_plan_with_grok_sentiment():
    """
    Test TradePlanAgent integration with Grok sentiment analysis
    """
    logger.info("Testing TradePlanAgent with Grok sentiment analysis")
    
    # Create the trade plan agent
    trade_plan_agent = create_trade_plan_agent()
    
    # Create analyst outputs
    analyst_outputs = {
        "SentimentAggregatorAgent": create_mock_grok_sentiment(),
        "TechnicalAnalystAgent": create_mock_technical_analysis(),
        "LiquidityAnalystAgent": create_mock_liquidity_analysis(),
        "FundingRateAnalystAgent": create_mock_funding_rate_analysis(),
        "OpenInterestAnalystAgent": create_mock_open_interest_analysis()
    }
    
    # Create decision based on analyst outputs
    decision = {
        "signal": "BUY",
        "confidence": 80,
        "contributing_agents": [
            "SentimentAggregatorAgent",
            "TechnicalAnalystAgent",
            "FundingRateAnalystAgent",
            "OpenInterestAnalystAgent"
        ],
        "reasoning": "Strong bullish consensus across multiple analysis dimensions"
    }
    
    # Create market data
    market_data = {
        "symbol": "BTC/USDT",
        "interval": "4h",
        "current_price": 50800.42,
        "ohlcv": [
            {"timestamp": "2022-01-01T00:00:00", "open": 49500, "high": 51200, "low": 49200, "close": 50900, "volume": 1200},
            {"timestamp": "2022-01-01T04:00:00", "open": 50900, "high": 51500, "low": 50500, "close": 51000, "volume": 950},
            {"timestamp": "2022-01-01T08:00:00", "open": 51000, "high": 51200, "low": 50400, "close": 50800, "volume": 800}
        ]
    }
    
    # Generate trade plan
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs=analyst_outputs
    )
    
    # Display the results
    logger.info(f"Trade plan generated successfully for {trade_plan['signal']} signal with {trade_plan['confidence']}% confidence")
    logger.info(f"Entry price: {trade_plan['entry_price']}")
    logger.info(f"Stop loss: {trade_plan['stop_loss']}")
    logger.info(f"Take profit: {trade_plan['take_profit']}")
    logger.info(f"Position size: {trade_plan['position_size']}")
    logger.info(f"Trade type: {trade_plan['trade_type']}")
    logger.info(f"Valid until: {trade_plan['valid_until']}")
    logger.info(f"Reason summary: {trade_plan['reason_summary']}")
    
    # Save to file for inspection
    with open("grok_sentiment_trade_plan.json", "w") as f:
        json.dump(trade_plan, f, indent=2)
    
    logger.info("Trade plan saved to grok_sentiment_trade_plan.json")
    logger.info("Test completed successfully!")
    
    return trade_plan

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
    except ImportError:
        logger.warning("dotenv package not found, skipping .env loading")
    
    # Run the test
    test_trade_plan_with_grok_sentiment()