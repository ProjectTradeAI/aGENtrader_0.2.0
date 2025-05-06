#!/usr/bin/env python3
"""
aGENtrader v2 - ToneAgent Test

This script runs a standalone test of the ToneAgent to verify its functionality.
"""

import os
import sys
import json
import logging
import colorama
from colorama import Fore, Style
from datetime import datetime

# Initialize colorama
colorama.init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/tone_agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import ToneAgent
from agents.tone_agent import ToneAgent


def print_banner(text, width=80, char='='):
    """Print a centered banner with the given text."""
    banner = char * width
    centered_text = f" {text} ".center(width, char)
    print(f"{Fore.GREEN}{banner}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{centered_text}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{banner}{Style.RESET_ALL}")


def test_tone_agent():
    """Run a standalone test for the ToneAgent with sample data."""
    
    print_banner("TONE AGENT TEST")
    
    # Sample analysis results
    analysis_results = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 75,
            "reasoning": "Moving averages show bullish crossover and RSI indicates momentum."
        },
        "sentiment_analysis": {
            "signal": "BUY", 
            "confidence": 80,
            "reasoning": "Social media sentiment has turned positive with increased mentions."
        },
        "liquidity_analysis": {
            "signal": "NEUTRAL",
            "confidence": 60,
            "reasoning": "Order book shows balanced buying and selling pressure."
        },
        "funding_rate_analysis": {
            "signal": "SELL",
            "confidence": 65,
            "reasoning": "Funding rates turning negative, indicating potential market exhaustion."
        },
        "open_interest_analysis": {
            "signal": "NEUTRAL",
            "confidence": 55,
            "reasoning": "Open interest has been flat over the past 24 hours."
        }
    }
    
    # Sample final decision
    final_decision = {
        "signal": "BUY",
        "confidence": 72,
        "directional_confidence": 65,
        "reason": "Bullish technical indicators with supportive sentiment.",
        "position_size": 0.15,
        "risk_score": 65,
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USDT",
        "current_price": 49876.32,
        "validity_period_hours": 24,
        "conflict_score": 35,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
        "strategy_tags": ["momentum_driven", "sentiment_aligned"],
        "risk_feedback": "Position size adjusted due to funding rate concerns"
    }
    
    # Initialize tone agent
    print(f"{Fore.YELLOW}Initializing ToneAgent...{Style.RESET_ALL}")
    tone_agent = ToneAgent()
    
    # Generate summary
    print(f"{Fore.YELLOW}Generating summary...{Style.RESET_ALL}")
    summary = tone_agent.generate_summary(
        analysis_results=analysis_results,
        final_decision=final_decision,
        symbol="BTC/USDT",
        interval="4h"
    )
    
    # Print styled summary
    tone_agent.print_styled_summary(summary, "BTC/USDT", "4h")
    
    # Save summary to file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results/tone_agent_output_{timestamp}.json"
    os.makedirs("test_results", exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"{Fore.GREEN}Test complete. Output saved to {output_file}{Style.RESET_ALL}")
    
    return summary


def main():
    """Run the tone agent test."""
    test_tone_agent()


if __name__ == "__main__":
    main()