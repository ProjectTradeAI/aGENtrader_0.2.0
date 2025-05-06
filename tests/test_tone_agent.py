"""
ToneAgent Test Script

This script tests the ToneAgent by simulating analysis results and decision data.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path to allow importing from sibling directories
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import required components
from agents.tone_agent import ToneAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToneAgentTest")

def main():
    """Run ToneAgent test with sample analysis and decision data."""
    logger.info("Starting ToneAgent test")
    
    # Create sample analysis results
    analysis_results = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 75,
            "reasoning": "Moving averages show bullish crossover and RSI indicates momentum. Price action shows bullish engulfing pattern."
        },
        "sentiment_analysis": {
            "signal": "BUY",
            "confidence": 80,
            "reasoning": "Social media sentiment has turned positive with increased mentions. News cycle trending towards bullish interpretations."
        },
        "liquidity_analysis": {
            "signal": "NEUTRAL",
            "confidence": 60,
            "reasoning": "Order book shows balanced buying and selling pressure. Market depth is moderate with no significant imbalances."
        },
        "funding_rate_analysis": {
            "signal": "SELL",
            "confidence": 65,
            "reasoning": "Funding rates turning negative, indicating potential market exhaustion. Longs potentially over-leveraged."
        },
        "open_interest_analysis": {
            "signal": "NEUTRAL",
            "confidence": 55,
            "reasoning": "Open interest has been flat over the past 24 hours with no significant change in market positions."
        }
    }
    
    # Create sample final decision
    final_decision = {
        "signal": "BUY",
        "confidence": 72,
        "directional_confidence": 65,
        "reason": "Bullish technical indicators with supportive sentiment, despite some caution from funding rates.",
        "position_size": 0.15,
        "risk_score": 65,
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USDT",
        "current_price": 49876.32,
        "validity_period_hours": 24,
        "conflict_score": 35,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
        "strategy_tags": ["momentum_driven", "sentiment_aligned", "countertrend_caution"],
        "risk_feedback": "Position size adjusted due to funding rate concerns"
    }
    
    # Initialize ToneAgent
    tone_agent = ToneAgent()
    
    # Generate summary
    logger.info("Generating summary with ToneAgent")
    summary = tone_agent.generate_summary(
        analysis_results=analysis_results,
        final_decision=final_decision,
        symbol="BTC/USDT",
        interval="4h"
    )
    
    # Display the results
    logger.info("===== TONE AGENT SUMMARY =====")
    if summary:
        for agent, comment in summary.get("agent_comments", {}).items():
            logger.info(f"- {agent}: \"{comment}\"")
        
        logger.info(f"\nSystem Summary: {summary.get('system_summary', 'No summary available')}")
        logger.info(f"Mood: {summary.get('mood', 'No mood detected')}")
    else:
        logger.error("No summary was generated")
    
    logger.info("ToneAgent test completed")

if __name__ == "__main__":
    main()