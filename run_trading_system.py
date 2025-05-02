#!/usr/bin/env python3
"""
aGENtrader v2 - Trading System Runner

This script runs the entire aGENtrader v2 system with multiple agents
and demonstrates the full decision pipeline from market data to trading decision.
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/aGENtrader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger('aGENtrader')

def load_environment():
    """Load environment variables from .env file if available"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
    except ImportError:
        logger.warning("dotenv package not found, skipping .env loading")
    except Exception as e:
        logger.error(f"Error loading .env file: {str(e)}")

def create_data_provider(provider_type="binance"):
    """Create and return a data provider based on type"""
    if provider_type == "binance":
        try:
            from binance_data_provider import BinanceDataProvider
            
            # Check for API keys
            api_key = os.environ.get('BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_API_SECRET')
            
            if api_key and api_secret:
                logger.info("Using authenticated Binance API")
                return BinanceDataProvider(api_key=api_key, api_secret=api_secret)
            else:
                logger.info("Using public Binance API (limited functionality)")
                return BinanceDataProvider()
                
        except ImportError:
            logger.error("Failed to import BinanceDataProvider")
            return None
    else:
        logger.error(f"Unsupported data provider type: {provider_type}")
        return None

def run_technical_analysis(market_data_or_symbol, interval=None, data_provider=None):
    """Run technical analysis and log the results"""
    try:
        from agents.technical_analyst_agent import TechnicalAnalystAgent
        
        # Standardize market_data format
        if isinstance(market_data_or_symbol, dict):
            market_data = market_data_or_symbol
            symbol = market_data.get("symbol")
            interval = market_data.get("interval") or interval
            data_provider = market_data.get("data_provider") or data_provider
            logger.info(f"Technical analysis: Received market_data dictionary. symbol={symbol}, interval={interval}, data_provider={'Available' if data_provider else 'None'}")
        else:
            symbol = market_data_or_symbol
            market_data = {
                "symbol": symbol,
                "interval": interval,
                "data_provider": data_provider
            }
            logger.info(f"Technical analysis: Created market_data dictionary. symbol={symbol}, interval={interval}, data_provider={'Available' if data_provider else 'None'}")
        
        # Initialize the technical analyst agent
        logger.info(f"Initializing TechnicalAnalystAgent with data_provider type: {type(data_provider).__name__ if data_provider else 'None'}")
        tech_agent = TechnicalAnalystAgent(data_fetcher=data_provider)
        
        # Run analysis with market_data using standardized parameter signature
        logger.info(f"Running technical analysis for {symbol} at {interval} interval with market_data keys: {list(market_data.keys())}")
        result = tech_agent.analyze(symbol=symbol, market_data=market_data, interval=interval)
        
        # Log the result
        if 'error' in result:
            logger.warning(f"Technical analysis error: {result.get('error_type', 'Unknown')} - {result.get('message', 'No message')}")
            return result
            
        logger.info(f"Technical analysis result: {result.get('signal', 'UNKNOWN')} with {result.get('confidence', 0)}% confidence")
        
        # Log explanation if available
        if 'explanation' in result and result['explanation']:
            if isinstance(result['explanation'], list):
                logger.info(f"Explanation: {' '.join(result['explanation'])}")
            else:
                logger.info(f"Explanation: {result['explanation']}")
                
        return result
    except Exception as e:
        logger.error(f"Error in technical analysis: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def run_sentiment_analysis(market_data_or_symbol, data_provider=None, interval=None):
    """Run sentiment analysis and log the results"""
    try:
        from agents.sentiment_analyst_agent import SentimentAnalystAgent
        
        # Standardize market_data format
        if isinstance(market_data_or_symbol, dict):
            market_data = market_data_or_symbol
            symbol = market_data.get("symbol")
            interval = market_data.get("interval") or interval
            data_provider = market_data.get("data_provider") or data_provider
        else:
            symbol = market_data_or_symbol
            market_data = {
                "symbol": symbol,
                "interval": interval,
                "data_provider": data_provider
            }
        
        # Initialize the sentiment analyst agent
        sentiment_agent = SentimentAnalystAgent()
        
        # Run analysis with standardized parameter signature
        logger.info(f"Running sentiment analysis for {symbol}")
        result = sentiment_agent.analyze(symbol=symbol, market_data=market_data, interval=interval)
        
        # Log the result
        if 'error' in result:
            logger.warning(f"Sentiment analysis error: {result.get('error_type', 'Unknown')} - {result.get('message', 'No message')}")
            return result
            
        logger.info(f"Sentiment analysis result: {result.get('signal', 'UNKNOWN')} with {result.get('confidence', 0)}% confidence")
        
        # Log reasoning if available
        if 'reasoning' in result:
            logger.info(f"Reasoning: {result['reasoning']}")
                
        return result
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def run_liquidity_analysis(market_data_or_symbol, interval=None, data_provider=None):
    """Run liquidity analysis and log the results"""
    try:
        # Standardize market_data format
        if isinstance(market_data_or_symbol, dict):
            market_data = market_data_or_symbol
            symbol = market_data.get("symbol")
            interval = market_data.get("interval") or interval
            data_provider = market_data.get("data_provider") or data_provider
        else:
            symbol = market_data_or_symbol
            market_data = {
                "symbol": symbol,
                "interval": interval,
                "data_provider": data_provider
            }
            
        # The actual LiquidityAnalystAgent will be implemented later
        # For now, return a structured error that the DecisionAgent will understand
        if not data_provider:
            return {
                "error": True, 
                "error_type": "DATA_FETCHER_MISSING", 
                "message": "Data fetcher not provided"
            }
            
        logger.info(f"Liquidity analysis not fully implemented yet for {symbol}")
        return {
            "signal": "HOLD",
            "confidence": 0,
            "reasoning": "Liquidity analysis not implemented yet"
        }
    except Exception as e:
        logger.error(f"Error in liquidity analysis: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def run_funding_rate_analysis(market_data_or_symbol, interval=None, data_provider=None):
    """Run funding rate analysis and log the results"""
    try:
        # Standardize market_data format
        if isinstance(market_data_or_symbol, dict):
            market_data = market_data_or_symbol
            symbol = market_data.get("symbol")
            interval = market_data.get("interval") or interval
            data_provider = market_data.get("data_provider") or data_provider
        else:
            symbol = market_data_or_symbol
            market_data = {
                "symbol": symbol,
                "interval": interval,
                "data_provider": data_provider
            }
            
        # The actual FundingRateAnalystAgent will be implemented later
        # For now, return a structured error that the DecisionAgent will understand
        if not data_provider:
            return {
                "error": True, 
                "error_type": "DATA_FETCHER_MISSING", 
                "message": "Data fetcher not provided"
            }
        
        logger.info(f"Funding rate analysis not fully implemented yet for {symbol}")
        return {
            "signal": "HOLD",
            "confidence": 0,
            "reasoning": "Funding rate analysis not implemented yet"
        }
    except Exception as e:
        logger.error(f"Error in funding rate analysis: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def run_open_interest_analysis(market_data_or_symbol, interval=None, data_provider=None):
    """Run open interest analysis and log the results"""
    try:
        # Standardize market_data format
        if isinstance(market_data_or_symbol, dict):
            market_data = market_data_or_symbol
            symbol = market_data.get("symbol")
            interval = market_data.get("interval") or interval
            data_provider = market_data.get("data_provider") or data_provider
        else:
            symbol = market_data_or_symbol
            market_data = {
                "symbol": symbol,
                "interval": interval,
                "data_provider": data_provider
            }
            
        # The actual OpenInterestAnalystAgent will be implemented later
        # For now, return a structured error that the DecisionAgent will understand
        if not data_provider:
            return {
                "error": True, 
                "error_type": "DATA_FETCHER_MISSING", 
                "message": "Data fetcher not provided"
            }
        
        logger.info(f"Open interest analysis not fully implemented yet for {symbol}")
        return {
            "signal": "HOLD",
            "confidence": 0,
            "reasoning": "Open interest analysis not implemented yet"
        }
    except Exception as e:
        logger.error(f"Error in open interest analysis: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def make_trading_decision(analyses, market_data_or_symbol, interval=None, data_provider=None):
    """Make a trading decision based on agent analyses"""
    try:
        from agents.decision_agent import DecisionAgent
        
        # Standardize market_data format
        if isinstance(market_data_or_symbol, dict):
            market_data = market_data_or_symbol
            symbol = market_data.get("symbol")
            interval = market_data.get("interval") or interval
            data_provider = market_data.get("data_provider") or data_provider
        else:
            symbol = market_data_or_symbol
            market_data = {
                "symbol": symbol,
                "interval": interval,
                "data_provider": data_provider
            }
        
        # Initialize the decision agent
        decision_agent = DecisionAgent()
        
        # Log market_data contents
        logger.info(f"Decision making: market_data contains symbol={market_data.get('symbol')}, interval={market_data.get('interval')}, data_provider={'Available' if market_data.get('data_provider') else 'None'}")
        logger.info(f"Decision making: analyses keys: {list(analyses.keys())}")
        
        # Make decision
        logger.info(f"Making trading decision for {symbol} at {interval} interval")
        decision = decision_agent.make_decision(
            agent_analyses=analyses,
            symbol=symbol,
            interval=interval,
            market_data=market_data
        )
        
        # Log the decision
        signal = decision.get('signal', 'UNKNOWN')
        confidence = decision.get('confidence', 0)
        reasoning = decision.get('reasoning', 'No reasoning provided')
        
        logger.info(f"Decision: {signal} with {confidence}% confidence")
        logger.info(f"Reasoning: {reasoning}")
        
        return decision
    except Exception as e:
        logger.error(f"Error making trading decision: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def run_demo_cycle(symbol="BTC/USDT", interval="1h"):
    """Run a complete demo cycle of the trading system"""
    logger.info(f"===== Starting aGENtrader 0.2.0 demo cycle =====")
    logger.info(f"Symbol: {symbol}, Interval: {interval}")
    
    # Create data provider
    data_provider = create_data_provider("binance")
    if not data_provider:
        logger.error("Failed to create data provider, exiting")
        return {"status": "failure", "reason": "data_provider_creation_failed"}
    
    # Get market data (price)
    current_price = None
    try:
        # Try to get current price
        ticker_data = data_provider.fetch_ticker(symbol)
        if ticker_data and 'last' in ticker_data:
            current_price = ticker_data['last']
            logger.info(f"Current price for {symbol}: {current_price}")
    except Exception as e:
        logger.warning(f"Could not fetch current price: {str(e)}")
    
    # Create market data dictionary to pass to all analyses
    market_data = {
        "symbol": symbol,
        "interval": interval,
        "data_provider": data_provider
    }
    
    # Log the market_data for debugging
    logger.info(f"Created market_data dictionary: symbol={market_data.get('symbol')}, interval={market_data.get('interval')}, data_provider={'Available' if market_data.get('data_provider') else 'None'}")
    
    # Run analyses
    analyses = {}
    
    # Run technical analysis
    logger.info("✅ Running technical analysis")
    technical_result = run_technical_analysis(market_data)
    if not technical_result.get('error', False):
        analyses['technical_analysis'] = technical_result
    
    # Run sentiment analysis
    logger.info("✅ Running sentiment analysis")
    sentiment_result = run_sentiment_analysis(market_data)
    if not sentiment_result.get('error', False):
        analyses['sentiment_analysis'] = sentiment_result
    
    # Run liquidity analysis
    logger.info("✅ Running liquidity analysis")
    liquidity_result = run_liquidity_analysis(market_data)
    if not liquidity_result.get('error', False):
        analyses['liquidity_analysis'] = liquidity_result
    
    # Run funding rate analysis
    logger.info("✅ Running funding rate analysis")
    funding_rate_result = run_funding_rate_analysis(market_data)
    if not funding_rate_result.get('error', False):
        analyses['funding_rate_analysis'] = funding_rate_result
    
    # Run open interest analysis
    logger.info("✅ Running open interest analysis")
    open_interest_result = run_open_interest_analysis(market_data)
    if not open_interest_result.get('error', False):
        analyses['open_interest_analysis'] = open_interest_result
    
    # Make decision using available analyses
    logger.info("✅ Making decision using: " + ", ".join(analyses.keys()))
    decision = make_trading_decision(analyses, market_data)
    
    # Return results
    return {
        "status": "success",
        "symbol": symbol,
        "interval": interval,
        "timestamp": datetime.now().isoformat(),
        "analyses": analyses,
        "decision": decision,
        "price": current_price
    }

def save_results(results, filename=None):
    """Save results to a JSON file"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/agentrader_results_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        return False

def main():
    """Main entry point"""
    # Load environment variables
    load_environment()
    
    # Parse command line arguments if needed
    import argparse
    parser = argparse.ArgumentParser(description='aGENtrader v2 Demo Runner')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='1h', help='Time interval')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    
    args = parser.parse_args()
    
    # Run the demo cycle
    try:
        results = run_demo_cycle(args.symbol, args.interval)
        
        # Save results if requested
        if args.save:
            save_results(results)
        
        # Display final decision
        if results["status"] == "success" and "decision" in results:
            decision = results["decision"]
            if not decision.get('error', False):
                signal = decision.get('signal', 'UNKNOWN')
                confidence = decision.get('confidence', 0)
                logger.info(f"===== FINAL DECISION =====")
                logger.info(f"{signal} {args.symbol} with {confidence}% confidence")
                logger.info(f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
            else:
                logger.error(f"Decision error: {decision.get('message', 'Unknown error')}")
        
        logger.info("aGENtrader 0.2.0 shutdown complete")
        return 0
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())