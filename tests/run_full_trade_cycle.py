#!/usr/bin/env python3
"""
aGENtrader v2 - Full Trade Cycle Test with ToneAgent Integration

This script runs a full trade cycle test with all analyst agents, DecisionAgent,
TradePlanAgent, and the new ToneAgent to generate human-like styled summaries.
"""

import os
import sys
import time
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
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/trade_cycle_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import agent classes
from agents.technical_analyst_agent import TechnicalAnalystAgent
from agents.sentiment_analyst_agent import SentimentAnalystAgent
from agents.sentiment_aggregator_agent import SentimentAggregatorAgent
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.funding_rate_analyst_agent import FundingRateAnalystAgent
from agents.open_interest_analyst_agent import OpenInterestAnalystAgent
from agents.decision_agent import DecisionAgent
from agents.trade_plan_agent import TradePlanAgent
from agents.tone_agent import ToneAgent


# Attempt to import mock data provider (for testing mode)
try:
    from utils.mock_data_provider import MockDataProvider
    DATA_PROVIDER_AVAILABLE = True
except ImportError:
    logger.warning("MockDataProvider not available, will attempt to use Binance API")
    DATA_PROVIDER_AVAILABLE = False
    
# Attempt to import Binance data provider (for live data)
try:
    from binance_data_provider import BinanceDataProvider
    BINANCE_PROVIDER_AVAILABLE = True
except ImportError:
    logger.warning("BinanceDataProvider not available")
    BINANCE_PROVIDER_AVAILABLE = False


def print_banner(text, width=80, char='='):
    """Print a centered banner with the given text."""
    padding = char * ((width - len(text) - 2) // 2)
    banner = f"{padding} {text} {padding}"
    if len(banner) < width:
        banner += char  # Ensure the banner is exactly width characters
    print(f"\n{banner}\n")


def run_full_trade_cycle(symbol="BTC/USDT", interval="1h", use_api=True, mock_data=True):
    """
    Run a full trade cycle test with all agents including the new ToneAgent.
    
    Args:
        symbol: Trading symbol (e.g., "BTC/USDT")
        interval: Time interval (e.g., "1h", "4h", "1d")
        use_api: Whether to use the API or fallback to local generation
        mock_data: Whether to use mock data or live API data
    """
    print_banner("FULL TRADE CYCLE TEST", char='*')
    print(f"{Fore.CYAN}Running FULL TRADE CYCLE TEST: All Agents + ToneAgent{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Symbol: {symbol}, Interval: {interval}{Style.RESET_ALL}")
    
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    # Initialize data provider
    data_provider = None
    if mock_data:
        if DATA_PROVIDER_AVAILABLE:
            logger.info("Using MockDataProvider for test data")
            data_provider = MockDataProvider()
        else:
            logger.error("MockDataProvider not available and mock_data=True")
            return False
    else:
        if BINANCE_PROVIDER_AVAILABLE:
            # Check if we have the API keys
            binance_api_key = os.environ.get("BINANCE_API_KEY")
            binance_api_secret = os.environ.get("BINANCE_API_SECRET")
            
            if binance_api_key and binance_api_secret:
                logger.info("Using Binance API for live market data")
                data_provider = BinanceDataProvider(
                    api_key=binance_api_key,
                    api_secret=binance_api_secret
                )
            else:
                logger.error("Binance API keys not available in environment")
                return False
        else:
            logger.error("BinanceDataProvider not available and mock_data=False")
            return False
    
    # Initialize all analyst agents
    technical_analyst = TechnicalAnalystAgent(data_fetcher=data_provider)
    sentiment_analyst = SentimentAnalystAgent()
    sentiment_aggregator = SentimentAggregatorAgent()
    liquidity_analyst = LiquidityAnalystAgent(data_fetcher=data_provider)
    funding_rate_analyst = FundingRateAnalystAgent(data_fetcher=data_provider)
    open_interest_analyst = OpenInterestAnalystAgent(data_fetcher=data_provider)
    
    # Run each analyst agent
    logger.info(f"{Fore.CYAN}Running analysis with each agent...{Style.RESET_ALL}")
    
    # Store analysis results
    analyses = {}
    
    # Run technical analysis
    print(f"\n{Fore.MAGENTA}Running TechnicalAnalystAgent analysis...{Style.RESET_ALL}")
    technical_result = technical_analyst.analyze(symbol=symbol, interval=interval)
    analyses["technical_analysis"] = technical_result
    print(f"{Fore.GREEN}Technical analysis: {technical_result.get('signal', 'UNKNOWN')} with {technical_result.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    
    # Run sentiment analysis
    print(f"\n{Fore.MAGENTA}Running SentimentAnalystAgent analysis...{Style.RESET_ALL}")
    sentiment_result = sentiment_analyst.analyze(symbol=symbol, interval=interval)
    analyses["sentiment_analysis"] = sentiment_result
    print(f"{Fore.GREEN}Sentiment analysis: {sentiment_result.get('signal', 'UNKNOWN')} with {sentiment_result.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    
    # Run sentiment aggregator
    print(f"\n{Fore.MAGENTA}Running SentimentAggregatorAgent analysis...{Style.RESET_ALL}")
    sentiment_agg_result = sentiment_aggregator.analyze(symbol=symbol, interval=interval)
    analyses["sentiment_aggregator"] = sentiment_agg_result
    print(f"{Fore.GREEN}Sentiment aggregator: {sentiment_agg_result.get('signal', 'UNKNOWN')} with {sentiment_agg_result.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    
    # Run liquidity analysis
    print(f"\n{Fore.MAGENTA}Running LiquidityAnalystAgent analysis...{Style.RESET_ALL}")
    liquidity_result = liquidity_analyst.analyze(symbol=symbol, interval=interval)
    analyses["liquidity_analysis"] = liquidity_result
    print(f"{Fore.GREEN}Liquidity analysis: {liquidity_result.get('signal', 'UNKNOWN')} with {liquidity_result.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    
    # Run funding rate analysis
    print(f"\n{Fore.MAGENTA}Running FundingRateAnalystAgent analysis...{Style.RESET_ALL}")
    funding_result = funding_rate_analyst.analyze(symbol=symbol, interval=interval)
    analyses["funding_rate_analysis"] = funding_result
    print(f"{Fore.GREEN}Funding rate analysis: {funding_result.get('signal', 'UNKNOWN')} with {funding_result.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    
    # Run open interest analysis
    print(f"\n{Fore.MAGENTA}Running OpenInterestAnalystAgent analysis...{Style.RESET_ALL}")
    open_interest_result = open_interest_analyst.analyze(symbol=symbol, interval=interval)
    analyses["open_interest_analysis"] = open_interest_result
    print(f"{Fore.GREEN}Open interest analysis: {open_interest_result.get('signal', 'UNKNOWN')} with {open_interest_result.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    
    # Create and run decision agent
    print(f"\n{Fore.MAGENTA}Running DecisionAgent to make final decision...{Style.RESET_ALL}")
    decision_agent = DecisionAgent()
    
    # Add analysis results to the decision agent
    decision_agent.add_analyst_result("technical_analysis", technical_result)
    decision_agent.add_analyst_result("sentiment_analysis", sentiment_result)
    decision_agent.add_analyst_result("sentiment_aggregator", sentiment_agg_result)
    decision_agent.add_analyst_result("liquidity_analysis", liquidity_result)
    decision_agent.add_analyst_result("funding_rate_analysis", funding_result)
    decision_agent.add_analyst_result("open_interest_analysis", open_interest_result)
    
    # Set symbol and price
    decision_agent.symbol = symbol
    current_price = data_provider.get_current_price(symbol)
    decision_agent.current_price = current_price
    
    # Make decision
    decision = decision_agent.make_decision()
    
    print(f"{Fore.GREEN}Final decision: {decision.get('signal', 'UNKNOWN')} with {decision.get('confidence', 0)}% confidence{Style.RESET_ALL}")
    print(f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
    print(f"Contributing agents: {', '.join(decision.get('contributing_agents', []))}")
    
    # Generate trade plan
    print(f"\n{Fore.MAGENTA}Running TradePlanAgent to generate trade plan...{Style.RESET_ALL}")
    trade_plan_agent = TradePlanAgent()
    
    # Get current price from data provider
    current_price = data_provider.get_current_price(symbol)
    
    market_data = {
        "symbol": symbol,
        "interval": interval,
        "current_price": current_price,
        "data_provider": data_provider
    }
    
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs=analyses
    )
    
    print(f"{Fore.GREEN}Trade plan generated: {trade_plan.get('action', 'UNKNOWN')}{Style.RESET_ALL}")
    print(f"Entry price: {trade_plan.get('entry_price', 0)}")
    print(f"Stop loss: {trade_plan.get('stop_loss', 0)}")
    print(f"Take profit: {trade_plan.get('take_profit', 0)}")
    print(f"Position size: {trade_plan.get('position_size', 0)}")
    print(f"Risk per trade: {trade_plan.get('risk_per_trade', 0)}")
    
    # Generate tone summary
    print(f"\n{Fore.MAGENTA}Running ToneAgent to generate styled summary...{Style.RESET_ALL}")
    tone_agent = ToneAgent(config={"use_api": use_api})
    
    tone_summary = tone_agent.generate_summary(
        analysis_results=analyses,
        final_decision=decision,
        symbol=symbol,
        interval=interval
    )
    
    # Display the tone summary
    tone_agent.print_styled_summary(tone_summary, symbol, interval)
    
    # Save all data to file
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/full_trade_cycle_{symbol.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Function to recursively sanitize dictionaries for JSON serialization
    def sanitize_for_json(obj):
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items() 
                    if not k == "data_provider" and not callable(v)}
        elif isinstance(obj, list):
            return [sanitize_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Convert objects to string representation
            return str(obj)
        else:
            # Keep basic types and return None for unparseable objects
            try:
                json.dumps(obj)
                return obj
            except (TypeError, OverflowError):
                return str(obj)
    
    # Create sanitized versions of all data for JSON serialization
    sanitized_market_data = sanitize_for_json(market_data)
    sanitized_trade_plan = sanitize_for_json(trade_plan)
    sanitized_decision = sanitize_for_json(decision)
    sanitized_analyses = sanitize_for_json(analyses)
    sanitized_tone_summary = sanitize_for_json(tone_summary)
    
    # Create complete log with all data
    full_data = {
        "trade_plan": sanitized_trade_plan,
        "decision": sanitized_decision,
        "analyses": sanitized_analyses,
        "market_data": sanitized_market_data,
        "tone_summary": sanitized_tone_summary,
        "symbol": symbol,
        "interval": interval,
        "timestamp": timestamp
    }
    
    try:
        with open(log_file, 'w') as f:
            json.dump(full_data, f, indent=2)
            
        logger.info(f"{Fore.GREEN}Full trade cycle log saved to: {log_file}{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}Error saving full trade cycle log: {str(e)}{Style.RESET_ALL}")
    
    # Calculate elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\n{Fore.GREEN}Full trade cycle test completed in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
    return True


def main():
    """Run the full trade cycle test with all agents."""
    parser = argparse.ArgumentParser(description="Test full trade cycle with all agents including ToneAgent")
    parser.add_argument('--no-api', action='store_true', help='Disable API usage and use local generation for ToneAgent')
    parser.add_argument('--live-data', action='store_true', help='Use live data from Binance API instead of mock data')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol to use')
    parser.add_argument('--interval', default='4h', help='Trading interval to use')
    args = parser.parse_args()
    
    # Check if XAI_API_KEY is available for ToneAgent
    if not args.no_api:
        xai_key = os.environ.get("XAI_API_KEY")
        if not xai_key:
            print(f"{Fore.YELLOW}Warning: XAI_API_KEY not found in environment. Falling back to local generation for ToneAgent.{Style.RESET_ALL}")
            args.no_api = True
    
    # Check if Binance API keys are available if using live data
    if args.live_data:
        binance_api_key = os.environ.get("BINANCE_API_KEY")
        binance_api_secret = os.environ.get("BINANCE_API_SECRET")
        
        if not binance_api_key or not binance_api_secret:
            print(f"{Fore.YELLOW}Warning: Binance API keys not found in environment. Falling back to mock data.{Style.RESET_ALL}")
            args.live_data = False
    
    # Run the test
    success = run_full_trade_cycle(
        symbol=args.symbol,
        interval=args.interval,
        use_api=not args.no_api,
        mock_data=not args.live_data
    )
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()