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
        # Import the LiquidityAnalystAgent
        from agents.liquidity_analyst_agent import LiquidityAnalystAgent
        
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
            
        # Return structured error if data_fetcher is missing
        if not data_provider:
            return {
                "error": True, 
                "error_type": "DATA_FETCHER_MISSING", 
                "message": "Data fetcher not provided"
            }
        
        # Create and initialize the LiquidityAnalystAgent with data_fetcher
        liquidity_agent = LiquidityAnalystAgent(data_fetcher=data_provider)
        
        # Run the analysis
        logger.info(f"Running liquidity analysis for {symbol} at {interval} interval")
        
        # Fetch order book data from provider if not in market_data
        if "order_book" not in market_data:
            try:
                order_book = data_provider.fetch_market_depth(symbol)
                market_data["order_book"] = order_book
            except Exception as e:
                logger.warning(f"Error fetching order book data: {str(e)}")
                # Continue with analysis, agent will handle missing order book
        
        # Analyze liquidity with order book data
        result = liquidity_agent.analyze(symbol, market_data, interval)
        
        # Check for errors
        if result.get("status") != "success":
            error_msg = result.get("message", "Unknown error in liquidity analysis")
            return {
                "error": True,
                "error_type": result.get("error_type", "ANALYSIS_FAILED"),
                "message": error_msg
            }
            
        # Extract entry and stop-loss zones
        entry_zone = result.get("entry_zone")
        stop_loss_zone = result.get("stop_loss_zone")
        
        # Log detected liquidity zones
        liquidity_zones = result.get("liquidity_zones", {})
        support_clusters = liquidity_zones.get("support_clusters", [])
        resistance_clusters = liquidity_zones.get("resistance_clusters", [])
        
        if support_clusters:
            logger.info(f"Detected support clusters: {support_clusters}")
        if resistance_clusters:
            logger.info(f"Detected resistance clusters: {resistance_clusters}")
        if entry_zone:
            logger.info(f"Suggested entry zone: {entry_zone}")
        if stop_loss_zone:
            logger.info(f"Suggested stop-loss zone: {stop_loss_zone}")
        
        # If successful, return the analysis result
        return {
            "signal": result.get("signal", "NEUTRAL"),
            "confidence": result.get("confidence", 50),
            "reasoning": result.get("explanation", ["Liquidity analysis complete"])[0],
            "entry_zone": entry_zone,
            "stop_loss_zone": stop_loss_zone,
            "liquidity_zones": liquidity_zones
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
            
        # Return structured error if data_fetcher is missing
        if not data_provider:
            return {
                "error": True, 
                "error_type": "DATA_FETCHER_MISSING", 
                "message": "Data fetcher not provided"
            }
        
        try:
            # Import here to avoid circular imports
            from agents.funding_rate_analyst_agent import FundingRateAnalystAgent
        except ImportError as e:
            logger.error(f"Could not import FundingRateAnalystAgent: {str(e)}")
            return {
                "error": True, 
                "error_type": "IMPORT_ERROR", 
                "message": f"Could not import FundingRateAnalystAgent: {str(e)}"
            }
            
        # Create and initialize the FundingRateAnalystAgent with data_fetcher
        logger.info(f"Creating FundingRateAnalystAgent with data provider")
        fr_agent = FundingRateAnalystAgent(data_fetcher=data_provider)
        
        # Run the analysis
        logger.info(f"Running funding rate analysis for {symbol} with interval {interval}")
        analysis_result = fr_agent.analyze(symbol=symbol, market_data=None, interval=interval)
        
        logger.info(f"Funding rate analysis complete: {analysis_result.get('signal')} with confidence {analysis_result.get('confidence')}")
        
        return analysis_result
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
            
        # Return structured error if data_fetcher is missing
        if not data_provider:
            return {
                "error": True, 
                "error_type": "DATA_FETCHER_MISSING", 
                "message": "Data fetcher not provided"
            }
        
        try:
            # Import here to avoid circular imports
            from agents.open_interest_analyst_agent import OpenInterestAnalystAgent
        except ImportError as e:
            logger.error(f"Could not import OpenInterestAnalystAgent: {str(e)}")
            return {
                "error": True, 
                "error_type": "IMPORT_ERROR", 
                "message": f"Could not import OpenInterestAnalystAgent: {str(e)}"
            }
            
        # Create and initialize the OpenInterestAnalystAgent with data_fetcher
        logger.info(f"Creating OpenInterestAnalystAgent with data provider")
        oi_agent = OpenInterestAnalystAgent(data_fetcher=data_provider)
        
        # Run the analysis
        logger.info(f"Running open interest analysis for {symbol} with interval {interval}")
        analysis_result = oi_agent.analyze(symbol=symbol, market_data=None, interval=interval)
        
        logger.info(f"Open interest analysis complete: {analysis_result.get('signal')} with confidence {analysis_result.get('confidence')}")
        
        return analysis_result
    except Exception as e:
        logger.error(f"Error in open interest analysis: {str(e)}", exc_info=True)
        return {"error": True, "error_type": "Exception", "message": str(e)}

def generate_trade_plan(decision, market_data, analyses=None):
    """
    Generate a detailed trade plan based on a trading decision using the enhanced TradePlanAgent.
    
    The trade plan includes:
    - Entry, stop-loss, and take-profit levels based on volatility and liquidity
    - Position sizing based on confidence
    - Risk management metrics
    - Trade classification (scalp, swing, trend following, etc.)
    - Time-based validity period
    - Detailed reason summary from contributing agents
    """
    try:
        # Import the enhanced trade plan agent function
        from agents.trade_plan_agent import create_trade_plan_agent
        
        # Get configuration from environment or default
        config = {
            'risk_reward_ratio': float(os.environ.get('TRADE_PLAN_RISK_REWARD', '1.5')),
            'portfolio_risk_per_trade': float(os.environ.get('TRADE_PLAN_RISK_PERCENT', '0.02')),  # 2% risk per trade
            'allow_fallback_on_hold': False,  # Ensure TradePlanAgent respects HOLD & CONFLICTED signals
            'default_tags': ['production']
        }
        
        # Create the enhanced trade plan agent
        trade_plan_agent = create_trade_plan_agent(config)
        
        # Extract necessary data from market_data
        symbol = market_data.get("symbol", "BTC/USDT")
        current_price = market_data.get("current_price", None)
        
        # Prepare analyst outputs for trade plan generation
        analyst_outputs = {}
        
        # Add all available analyses for comprehensive trade plan generation
        if analyses:
            # Add liquidity analysis for optimal entry and stop-loss levels
            if "liquidity_analysis" in analyses:
                analyst_outputs["liquidity_analysis"] = analyses["liquidity_analysis"]
            
            # Add technical analysis for volatility assessment
            if "technical_analysis" in analyses:
                analyst_outputs["technical_analysis"] = analyses["technical_analysis"]
            
            # Add other analyses that might be useful
            for analysis_type in ["sentiment_analysis", "open_interest_analysis", "funding_rate_analysis"]:
                if analysis_type in analyses:
                    analyst_outputs[analysis_type] = analyses[analysis_type]
            
        # Generate enhanced trade plan
        logger.info(f"Generating enhanced trade plan for {decision.get('signal')} decision on {symbol}")
        trade_plan = trade_plan_agent.generate_trade_plan(
            decision=decision,
            market_data=market_data,
            analyst_outputs=analyst_outputs
        )
        
        # Log additional details from enhanced plan
        if not trade_plan.get('error', False):
            logger.info(f"Trade type: {trade_plan.get('trade_type', 'unknown')}")
            logger.info(f"Valid until: {trade_plan.get('valid_until', 'not specified')}")
            
            # Log risk metrics if available
            if 'risk_snapshot' in trade_plan:
                risk = trade_plan['risk_snapshot']
                logger.info(f"Risk metrics - R:R: {risk.get('risk_reward_ratio', 'N/A')}, "
                           f"Portfolio risk: {risk.get('portfolio_risk_percent', 'N/A')}%, "
                           f"Portfolio exposure: {risk.get('portfolio_exposure_percent', 'N/A')}%")
        
        return trade_plan
    except Exception as e:
        logger.error(f"Error generating trade plan: {str(e)}", exc_info=True)
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
    
    # Generate a trade plan if a trading decision is valid (including HOLD/CONFLICTED)
    if decision and not decision.get('error', False):
        logger.info("✅ Generating enhanced trade plan")
        trade_plan = generate_trade_plan(decision, market_data, analyses)
        
        # Combine the decision and trade plan
        if trade_plan and not trade_plan.get('error', False):
            decision.update(trade_plan)
            logger.info(f"Enhanced trade plan generated:")
            logger.info(f"Entry: {trade_plan.get('entry_price')}, SL: {trade_plan.get('stop_loss')}, TP: {trade_plan.get('take_profit')}")
            logger.info(f"Position Size: {trade_plan.get('position_size')}, Trade Type: {trade_plan.get('trade_type', 'unknown')}")
            
            # Log enhanced metrics if available
            if 'risk_snapshot' in trade_plan:
                risk = trade_plan['risk_snapshot']
                logger.info(f"Risk metrics - R:R: {risk.get('risk_reward_ratio', 'N/A')}, "
                           f"Portfolio risk: {risk.get('portfolio_risk_percent', 'N/A')}%, "
                           f"Exposure: {risk.get('portfolio_exposure_percent', 'N/A')}%")
                
            logger.info(f"Valid until: {trade_plan.get('valid_until', 'not specified')}")
    
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
        
        # Sanitize the results for JSON serialization
        sanitized_results = sanitize_for_json(results)
        
        with open(filename, 'w') as f:
            json.dump(sanitized_results, f, indent=2)
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
                logger.info(f"===== FINAL DECISION & TRADE PLAN =====")
                logger.info(f"{signal} {args.symbol} with {confidence}% confidence")
                logger.info(f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
                
                # Display enhanced trade plan details if available
                if 'trade_plan_generated' in decision or ('entry_price' in decision and signal in ['BUY', 'SELL']):
                    logger.info(f"===== ENHANCED TRADE PLAN DETAILS =====")
                    logger.info(f"Entry Price: {decision.get('entry_price')}")
                    logger.info(f"Stop-Loss: {decision.get('stop_loss')}")
                    logger.info(f"Take-Profit: {decision.get('take_profit')}")
                    logger.info(f"Position Size: {decision.get('position_size')}")
                    
                    # Display enhanced features
                    if 'trade_type' in decision:
                        logger.info(f"Trade Type: {decision.get('trade_type', 'unknown')}")
                    if 'valid_until' in decision:
                        logger.info(f"Valid Until: {decision.get('valid_until', 'not specified')}")
                    if 'reason_summary' in decision:
                        logger.info(f"Reason Summary: {decision.get('reason_summary', 'N/A')}")
                    
                    # Display risk metrics if available
                    if 'risk_snapshot' in decision:
                        risk = decision.get('risk_snapshot', {})
                        logger.info(f"===== RISK METRICS =====")
                        logger.info(f"Risk/Reward Ratio: {risk.get('risk_reward_ratio', 'N/A')}")
                        logger.info(f"Portfolio Risk: {risk.get('portfolio_risk_percent', 'N/A')}%")
                        logger.info(f"Portfolio Exposure: {risk.get('portfolio_exposure_percent', 'N/A')}%")
                        
                    # Display fallback usage
                    fallback = decision.get('fallback_plan', False)
                    if fallback:
                        logger.info(f"Note: Trade levels were calculated using fallback methods due to insufficient data")
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