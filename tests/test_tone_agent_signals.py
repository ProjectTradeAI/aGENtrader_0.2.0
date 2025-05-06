#!/usr/bin/env python3
"""
Test script for ToneAgent signal validation

This script tests that the ToneAgent correctly represents each analyst's signal.
"""
import os
import sys
import json
import logging
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Import the ToneAgent
    from agents.tone_agent import ToneAgent
    
    # Create mock analysis results with different signals
    mock_analysis_results = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 95,
            "reasoning": "Strong bullish indicators across multiple timeframes."
        },
        "sentiment_analysis": {
            "signal": "NEUTRAL",
            "confidence": 70,
            "reasoning": "Mixed sentiment indicators with slight bullish bias."
        },
        "liquidity_analysis": {
            "signal": "NEUTRAL",
            "confidence": 50,
            "reasoning": "Normal liquidity conditions, no significant anomalies."
        },
        "funding_rate_analysis": {
            "signal": "NEUTRAL",
            "confidence": 65,
            "reasoning": "Funding rates within normal range, slight neutral bias."
        },
        "open_interest_analysis": {
            "signal": "BUY",
            "confidence": 50,
            "reasoning": "Increasing open interest with price, suggests bullish momentum."
        }
    }
    
    # Create a mock final decision
    mock_final_decision = {
        "signal": "BUY",
        "confidence": 75,
        "conflict_score": 25,
        "reasoning": "Technical indicators are strongly bullish, supported by open interest, despite neutral sentiment and funding."
    }
    
    # Test case 1: Create a ToneAgent instance
    logger.info(f"{Fore.CYAN}=== Testing ToneAgent Signal Validation ==={Style.RESET_ALL}")
    tone_agent = ToneAgent()
    
    # Test case 2: Generate summary
    logger.info(f"{Fore.CYAN}Generating summary from mock data...{Style.RESET_ALL}")
    summary = tone_agent.generate_summary(
        analysis_results=mock_analysis_results,
        final_decision=mock_final_decision,
        symbol="BTC/USDT",
        interval="1h"
    )
    
    # Test case 3: Validate that each agent's signal is correctly represented
    logger.info(f"{Fore.CYAN}=== Validating Signal Representation ==={Style.RESET_ALL}")
    
    # Expected signals from our mock data
    expected_signals = {
        "TechnicalAnalystAgent": "BUY",
        "SentimentAnalystAgent": "NEUTRAL",
        "LiquidityAnalystAgent": "NEUTRAL",
        "FundingRateAnalystAgent": "NEUTRAL",
        "OpenInterestAnalystAgent": "BUY"
    }
    
    # Count correct and incorrect representations
    correct_count = 0
    incorrect_count = 0
    
    for agent, comment in summary.get("agent_comments", {}).items():
        expected_signal = expected_signals.get(agent, "UNKNOWN")
        
        # Check if the expected signal is mentioned in the comment
        is_correct = expected_signal in comment
        
        if is_correct:
            logger.info(f"{Fore.GREEN}✅ {agent}: Signal {expected_signal} correctly represented")
            correct_count += 1
        else:
            logger.info(f"{Fore.RED}❌ {agent}: Signal {expected_signal} NOT found in comment: \"{comment}\"")
            incorrect_count += 1
    
    # Print summary
    logger.info(f"{Fore.CYAN}=== Test Results ==={Style.RESET_ALL}")
    logger.info(f"Total agents tested: {correct_count + incorrect_count}")
    logger.info(f"Correctly represented: {correct_count}")
    logger.info(f"Incorrectly represented: {incorrect_count}")
    
    if incorrect_count == 0:
        logger.info(f"{Fore.GREEN}All signals correctly represented! Test passed.{Style.RESET_ALL}")
    else:
        logger.info(f"{Fore.RED}Some signals were not correctly represented. Test failed.{Style.RESET_ALL}")
    
except ImportError as e:
    logger.error(f"{Fore.RED}Error importing required modules: {str(e)}{Style.RESET_ALL}")
except Exception as e:
    logger.error(f"{Fore.RED}Error during test: {str(e)}{Style.RESET_ALL}")