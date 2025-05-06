#!/usr/bin/env python3
"""
aGENtrader v2 - Simple ToneAgent Test

This is a simplified test for the ToneAgent that doesn't rely on the complex test harness.
It directly instantiates the ToneAgent and tests its functionality.
"""

import sys
import os
import logging
import json
from datetime import datetime
from colorama import Fore, Style, init as colorama_init

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize colorama for cross-platform colored terminal output
colorama_init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Import required modules
try:
    from agents.tone_agent import ToneAgent
    logger.info("Successfully imported ToneAgent")
except ImportError as e:
    logger.error(f"Failed to import ToneAgent: {e}")
    sys.exit(1)

def print_banner(text, width=80, char='='):
    """Print a centered banner with the given text."""
    padding = char * ((width - len(text) - 2) // 2)
    banner = f"\n{padding} {text} {padding}"
    if len(banner) < width:
        banner += char  # Ensure the banner is exactly width characters
    print(banner)

def run_simple_tone_agent_test():
    """Run a simple test of the ToneAgent without the test harness."""
    print_banner("SIMPLE TONE AGENT TEST", width=80)
    
    # Initialize ToneAgent directly
    logger.info("Initializing ToneAgent...")
    tone_agent = ToneAgent()
    
    # Sample data for testing
    sample_analyses = {
        'technical_analysis': {
            'signal': 'BUY',
            'confidence': 85,
            'reasoning': 'Multiple bullish indicators including upward trending MACD, RSI at 62 (not overbought), and price above 50-day MA. Volume showing increasing buy pressure.',
            'data': {
                'indicators': {
                    'rsi': 62,
                    'macd': 0.35,
                    'ema_50': 48750,
                    'ema_200': 46200
                }
            }
        },
        'sentiment_analysis': {
            'signal': 'NEUTRAL',
            'confidence': 60,
            'reasoning': 'Mixed sentiment in news and social media. Regulation concerns balanced by institutional adoption news.',
            'data': {
                'sentiment_score': 0.52,
                'news_count': 32,
                'positive_mentions': 18,
                'negative_mentions': 14
            }
        },
        'liquidity_analysis': {
            'signal': 'HOLD',
            'confidence': 70,
            'reasoning': 'Order book depth is adequate but shows resistance at $51K level. Support is strong at $48K.',
            'data': {
                'buy_depth': 8500000,
                'sell_depth': 9200000,
                'resistance_level': 51000,
                'support_level': 48000
            }
        }
    }
    
    sample_decision = {
        'signal': 'BUY',
        'confidence': 75,
        'reasoning': 'Technical indicators show strong bullish momentum with acceptable risk profile. Liquidity adequate for position entry.',
        'contributing_agents': ['TechnicalAnalystAgent', 'LiquidityAnalystAgent'],
        'counter_signals': ['SentimentAnalystAgent (NEUTRAL)']
    }
    
    # Test ToneAgent with sample data
    logger.info("Testing ToneAgent with sample data...")
    tone_summary = tone_agent.generate_summary(
        analysis_results=sample_analyses,
        final_decision=sample_decision,
        symbol="BTC/USDT",
        interval="4h"
    )
    
    # Display the results
    print(f"\n{Fore.GREEN}Agent Comments:{Style.RESET_ALL}")
    for agent_name, comment in tone_summary.get('agent_comments', {}).items():
        print(f"\n{Fore.YELLOW}{agent_name}:{Style.RESET_ALL}")
        print(f"{comment}")
    
    print(f"\n{Fore.GREEN}System Summary:{Style.RESET_ALL}")
    print(tone_summary.get('system_summary', 'No system summary available'))
    
    # Save result as JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tone_agent_test_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(tone_summary, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return True

def main():
    """Run the test."""
    try:
        success = run_simple_tone_agent_test()
        if success:
            logger.info("ToneAgent test completed successfully")
            return 0
        else:
            logger.error("ToneAgent test failed")
            return 1
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())