#!/usr/bin/env python3
"""
aGENtrader v2 - ToneAgent Standalone Test Runner

This script runs the ToneAgent in a standalone mode, testing its ability to generate
human-like styled summaries for agent analyses and decisions.
"""

import os
import sys
import json
import logging
import argparse
import colorama
from colorama import Fore, Style
from datetime import datetime

# Initialize colorama
colorama.init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import ToneAgent
try:
    from agents.tone_agent import ToneAgent
    TONEAGENT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import ToneAgent: {str(e)}")
    TONEAGENT_AVAILABLE = False

def print_banner(text, width=80, char='='):
    """Print a centered banner with the given text."""
    padding = char * ((width - len(text) - 2) // 2)
    banner = f"{padding} {text} {padding}"
    if len(banner) < width:
        banner += char  # Ensure the banner is exactly width characters
    print(f"\n{banner}\n")

def run_tone_agent_test(use_api=True, symbol="BTC/USDT", interval="4h"):
    """
    Run the ToneAgent test with sample data.
    
    Args:
        use_api: Whether to use the API or fallback to local generation
        symbol: Trading symbol to use in the test
        interval: Time interval to use in the test
    """
    if not TONEAGENT_AVAILABLE:
        print(f"{Fore.RED}Error: ToneAgent is not available. Cannot run test.{Style.RESET_ALL}")
        return False

    print_banner("TONE AGENT TEST", char='*')
    print(f"{Fore.CYAN}Testing ToneAgent with symbol: {symbol}, interval: {interval}{Style.RESET_ALL}")

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
        "symbol": symbol,
        "current_price": 49876.32,
        "validity_period_hours": 24,
        "conflict_score": 35,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
        "strategy_tags": ["momentum_driven", "sentiment_aligned", "countertrend_caution"],
        "risk_feedback": "Position size adjusted due to funding rate concerns"
    }
    
    # Initialize ToneAgent with specific configuration
    tone_agent = ToneAgent(
        config={
            "use_api": use_api,
            "symbol": symbol,
            "interval": interval
        }
    )
    
    # Generate summary
    print(f"\n{Fore.CYAN}Generating summary with ToneAgent...{Style.RESET_ALL}")
    summary = tone_agent.generate_summary(
        analysis_results=analysis_results,
        final_decision=final_decision,
        symbol=symbol,
        interval=interval
    )
    
    # Display the results
    print_banner("TONE AGENT SUMMARY", char='-')
    if summary:
        agent_comments = summary.get("agent_comments", {})
        system_summary = summary.get("system_summary", "No system summary available")
        mood = summary.get("mood", "neutral")
        
        # Display agent comments
        if agent_comments:
            print(f"{Fore.GREEN}=== Agent Voices ==={Style.RESET_ALL}")
            for agent, comment in agent_comments.items():
                print(f"\n{Fore.MAGENTA}[{agent}]{Style.RESET_ALL}")
                print(f"{Fore.WHITE}\"{comment}\"{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No agent comments available{Style.RESET_ALL}")
        
        # Display system summary
        if system_summary:
            print(f"\n{Fore.GREEN}=== Overall Market View ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE}{system_summary}{Style.RESET_ALL}")
        
        # Display mood
        print(f"\n{Fore.GREEN}=== Market Mood ==={Style.RESET_ALL}")
        mood_color = Fore.YELLOW
        if mood.lower() in ["bullish", "very bullish", "optimistic"]:
            mood_color = Fore.GREEN
        elif mood.lower() in ["bearish", "very bearish", "pessimistic"]:
            mood_color = Fore.RED
        print(f"{Fore.WHITE}Current mood: {mood_color}{mood}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✓ ToneAgent test completed successfully!{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}✗ Failed to generate summary with ToneAgent{Style.RESET_ALL}")
        return False

def main():
    """Run the ToneAgent test."""
    parser = argparse.ArgumentParser(description="Test ToneAgent functionality")
    parser.add_argument('--no-api', action='store_true', help='Disable API usage and use local generation only')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol to use')
    parser.add_argument('--interval', default='4h', help='Trading interval to use')
    args = parser.parse_args()
    
    # Check if key environment variables are available
    if not args.no_api:
        xai_key = os.environ.get("XAI_API_KEY")
        if not xai_key:
            print(f"{Fore.YELLOW}Warning: XAI_API_KEY not found in environment. Falling back to local generation.{Style.RESET_ALL}")
            args.no_api = True
    
    # Run the test
    success = run_tone_agent_test(
        use_api=not args.no_api,
        symbol=args.symbol,
        interval=args.interval
    )
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()