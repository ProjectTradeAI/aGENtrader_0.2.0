#!/usr/bin/env python3
"""
aGENtrader v2 - Integrated ToneAgent Test

This script runs a more integrated test of the ToneAgent by directly calling
the analyst agents and decision agent with the correct parameters.
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
    from agents.technical_analyst_agent import TechnicalAnalystAgent
    from agents.sentiment_analyst_agent import SentimentAnalystAgent
    from agents.liquidity_analyst_agent import LiquidityAnalystAgent
    from agents.decision_agent import DecisionAgent
    from agents.tone_agent import ToneAgent
    from utils.mock_data_provider import MockDataProvider
    
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def print_banner(text, width=80, char='='):
    """Print a centered banner with the given text."""
    padding = char * ((width - len(text) - 2) // 2)
    banner = f"\n{padding} {text} {padding}"
    if len(banner) < width:
        banner += char  # Ensure the banner is exactly width characters
    print(banner)

def run_integrated_tone_agent_test(symbol="BTC/USDT", interval="4h"):
    """Run an integrated test with ToneAgent and real agent outputs."""
    print_banner(f"INTEGRATED TONE AGENT TEST - {symbol} ({interval})", width=80)
    
    # Initialize data provider
    logger.info(f"Initializing data provider for {symbol}...")
    data_provider = MockDataProvider(symbol=symbol)
    
    # Initialize agents with correct parameters
    logger.info("Initializing analyst agents...")
    technical_agent = TechnicalAnalystAgent(
        data_fetcher=data_provider,
        config={
            "symbol": symbol,
            "interval": interval,
            "use_cache": False
        }
    )
    
    sentiment_agent = SentimentAnalystAgent(
        config={
            "symbol": symbol,
            "interval": interval,
            "use_cache": False,
            "temperature": 0.7,
            "data_provider": data_provider  # Pass data provider in config
        }
    )
    
    liquidity_agent = LiquidityAnalystAgent(
        data_fetcher=data_provider,
        config={
            "symbol": symbol,
            "interval": interval,
            "use_cache": False
        }
    )
    
    # Run analysis with each agent
    logger.info("Running analysis with each agent...")
    
    try:
        technical_result = technical_agent.analyze(symbol=symbol, interval=interval)
        logger.info(f"Technical analysis: {technical_result['signal']} ({technical_result['confidence']}%)")
    except Exception as e:
        logger.error(f"Error running technical analysis: {e}")
        technical_result = {
            'signal': 'NEUTRAL',
            'confidence': 50,
            'reasoning': 'Technical analysis failed',
            'data': {}
        }
        
    try:
        sentiment_result = sentiment_agent.analyze(symbol=symbol, interval=interval)
        logger.info(f"Sentiment analysis: {sentiment_result['signal']} ({sentiment_result['confidence']}%)")
    except Exception as e:
        logger.error(f"Error running sentiment analysis: {e}")
        sentiment_result = {
            'signal': 'NEUTRAL',
            'confidence': 50,
            'reasoning': 'Sentiment analysis failed',
            'data': {}
        }
        
    try:
        liquidity_result = liquidity_agent.analyze(symbol=symbol, interval=interval)
        logger.info(f"Liquidity analysis: {liquidity_result['signal']} ({liquidity_result['confidence']}%)")
    except Exception as e:
        logger.error(f"Error running liquidity analysis: {e}")
        liquidity_result = {
            'signal': 'NEUTRAL',
            'confidence': 50,
            'reasoning': 'Liquidity analysis failed',
            'data': {}
        }
    
    # Combine all results
    agent_analyses = {
        'technical_analysis': technical_result,
        'sentiment_analysis': sentiment_result,
        'liquidity_analysis': liquidity_result
    }
    
    # Run decision agent
    logger.info("Running decision agent with analysis results...")
    decision_agent = DecisionAgent(allow_conflict_state=True)
    
    try:
        decision = decision_agent.make_decision(
            agent_analyses=agent_analyses,
            symbol=symbol,
            interval=interval
        )
        logger.info(f"Decision: {decision['signal']} ({decision['confidence']}%)")
    except Exception as e:
        logger.error(f"Error running decision agent: {e}")
        decision = {
            'signal': 'HOLD',
            'confidence': 50,
            'reasoning': 'Decision agent failed',
            'contributing_agents': []
        }
    
    # Run tone agent
    logger.info("Running tone agent to generate summary...")
    tone_agent = ToneAgent()
    
    try:
        tone_summary = tone_agent.generate_summary(
            analysis_results=agent_analyses,
            final_decision=decision,
            symbol=symbol,
            interval=interval
        )
    except Exception as e:
        logger.error(f"Error running tone agent: {e}")
        tone_summary = {
            'agent_comments': {},
            'system_summary': 'Tone agent failed to generate summary'
        }
    
    # Display the results
    print(f"\n{Fore.GREEN}Agent Comments:{Style.RESET_ALL}")
    for agent_name, comment in tone_summary.get('agent_comments', {}).items():
        print(f"\n{Fore.YELLOW}{agent_name}:{Style.RESET_ALL}")
        print(f"{comment}")
    
    print(f"\n{Fore.GREEN}System Summary:{Style.RESET_ALL}")
    print(tone_summary.get('system_summary', 'No system summary available'))
    
    # Save result as JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"integrated_tone_test_{symbol.replace('/', '')}_${interval}_{timestamp}.json"
    
    # Combine all results into a single report
    report = {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'interval': interval,
        'analysis_results': agent_analyses,
        'decision': decision,
        'tone_summary': tone_summary
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return True

def main():
    """Run the test."""
    try:
        success = run_integrated_tone_agent_test()
        if success:
            logger.info("Integrated ToneAgent test completed successfully")
            return 0
        else:
            logger.error("Integrated ToneAgent test failed")
            return 1
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())