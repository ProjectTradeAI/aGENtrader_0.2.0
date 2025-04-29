#!/usr/bin/env python3
"""
aGENtrader Main Application

This script serves as the main entry point for the aGENtrader trading system
with real technical analysis and sentiment analysis via Grok API.
"""
# Import version information from centralized location
from core.version import VERSION, get_version_banner
import os
import sys
import logging
import argparse
import json
import time
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import dotenv for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")
    # Ensure we install it for future runs
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        from dotenv import load_dotenv
        load_dotenv()
        print("Installed python-dotenv successfully.")
    except:
        print("Could not auto-install python-dotenv. Continuing without it.")

# Import the data providers
from agents.data_providers.binance_data_provider import BinanceDataProvider

# Import the analyst agents
from agents.base_agent import BaseAnalystAgent
from agents.technical_analyst_agent import TechnicalAnalystAgent
from agents.sentiment_aggregator_agent import SentimentAggregatorAgent
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.funding_rate_analyst_agent import FundingRateAnalystAgent
from agents.open_interest_analyst_agent import OpenInterestAnalystAgent
from agents.decision_agent import DecisionAgent

# Import the decision logger
from core.logging.decision_logger import DecisionLogger, decision_logger

# Import the performance tracker
from analytics.performance_tracker import PerformanceTracker

def setup_logging(log_level=None):
    """Set up logging configuration."""
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/agentrader.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("aGENtrader")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=f"aGENtrader {VERSION} Trading System")
    
    # Check if we're in Docker, force test mode if true
    in_docker = os.environ.get("IN_DOCKER", "false").lower() == "true"
    default_mode = "test" if in_docker else os.getenv("MODE", "demo")
    
    parser.add_argument("--mode", type=str, default=default_mode, 
                        choices=["demo", "test", "live_simulation", "live"],
                        help="Trading mode (demo, test, live_simulation, or live)")
    parser.add_argument("--symbol", type=str, default=os.getenv("DEFAULT_SYMBOL", "BTC/USDT"),
                        help="Trading symbol (e.g., BTC/USDT)")
    parser.add_argument("--interval", type=str, default=os.getenv("DEFAULT_INTERVAL", "1h"),
                        help="Time interval for market data (e.g., 1h, 4h, 1d)")
    parser.add_argument("--sentiment", action="store_true",
                        help="Run sentiment analysis demo")
    
    args = parser.parse_args()
    
    # Force test mode in Docker environment regardless of command line arguments
    if in_docker and args.mode == "demo":
        print("WARNING: Demo mode not supported in Docker environment. Forcing test mode.")
        args.mode = "test"
        
    return args

class TradeBookManager:
    """
    Manages trade recording and performance tracking.
    """
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.trade_book_path = os.path.join(log_dir, "trade_book.jsonl")
        self.trade_performance_path = os.path.join(log_dir, "trade_performance.jsonl")
        self.rejected_trades_path = os.path.join(log_dir, "rejected_trades.jsonl")
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        self.open_trades = []
        self.closed_trades = []
        self.rejected_trades = []
        
        logging.info(f"TradeBookManager initialized with log dir: {log_dir}")
    
    def record_trade(self, trade_data):
        """Record a new trade."""
        if not isinstance(trade_data, dict):
            logging.error("Trade data must be a dictionary")
            return False
        
        # Add timestamp if not present
        if "timestamp" not in trade_data:
            trade_data["timestamp"] = datetime.now().isoformat()
        
        # Add to open trades
        self.open_trades.append(trade_data)
        
        # Record to trade book
        with open(self.trade_book_path, "a") as f:
            f.write(json.dumps(trade_data) + "\n")
        
        logging.info(f"Trade recorded: {trade_data['type']} {trade_data.get('symbol')} @ {trade_data.get('price')}")
        return True
    
    def record_performance(self, performance_data):
        """Record trade performance."""
        if not isinstance(performance_data, dict):
            logging.error("Performance data must be a dictionary")
            return False
        
        # Add timestamp if not present
        if "timestamp" not in performance_data:
            performance_data["timestamp"] = datetime.now().isoformat()
        
        # Record to performance log
        with open(self.trade_performance_path, "a") as f:
            f.write(json.dumps(performance_data) + "\n")
        
        logging.info(f"Performance recorded: {performance_data}")
        return True
    
    def record_rejected_trade(self, trade_data, rejection_reason):
        """Record a rejected trade."""
        if not isinstance(trade_data, dict):
            logging.error("Trade data must be a dictionary")
            return False
        
        # Add rejection information
        trade_data["rejected"] = True
        trade_data["rejection_reason"] = rejection_reason
        
        # Add timestamp if not present
        if "timestamp" not in trade_data:
            trade_data["timestamp"] = datetime.now().isoformat()
        
        # Add to rejected trades
        self.rejected_trades.append(trade_data)
        
        # Record to rejected trades log
        with open(self.rejected_trades_path, "a") as f:
            f.write(json.dumps(trade_data) + "\n")
        
        logging.info(f"Trade rejected: {trade_data['type']} {trade_data.get('symbol')} - Reason: {rejection_reason}")
        return True


class DecisionTriggerScheduler:
    """
    Manages scheduled decision triggers for different timeframes.
    """
    
    def __init__(self):
        self.scheduled_triggers = {}
        self.last_execution = {}
        
    def schedule_trigger(self, interval, callback, symbol=None):
        """Schedule a trigger for a specific interval."""
        if interval not in self.scheduled_triggers:
            self.scheduled_triggers[interval] = []
        
        trigger = {
            "callback": callback,
            "symbol": symbol
        }
        
        self.scheduled_triggers[interval].append(trigger)
        self.last_execution[interval] = 0
        
        logging.info(f"Scheduled trigger for interval {interval}")
        
    def check_triggers(self):
        """Check if any triggers should be executed."""
        current_time = time.time()
        
        for interval, triggers in self.scheduled_triggers.items():
            interval_seconds = self._interval_to_seconds(interval)
            
            if current_time - self.last_execution.get(interval, 0) >= interval_seconds:
                # Execute all triggers for this interval
                for trigger in triggers:
                    callback = trigger["callback"]
                    symbol = trigger["symbol"]
                    
                    try:
                        if symbol:
                            callback(symbol=symbol, interval=interval)
                        else:
                            callback(interval=interval)
                    except Exception as e:
                        logging.error(f"Error executing trigger for {interval}: {str(e)}")
                
                self.last_execution[interval] = current_time
                logging.info(f"Executed triggers for interval {interval}")
                
    def _interval_to_seconds(self, interval):
        """Convert interval string to seconds."""
        unit = interval[-1]
        value = int(interval[:-1])
        
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 60 * 60
        elif unit == 'd':
            return value * 24 * 60 * 60
        else:
            raise ValueError(f"Unsupported interval unit: {unit}")


class RiskGuardAgent:
    """
    Agent that evaluates trade risks and may reject trades based on risk parameters.
    """
    
    def __init__(self, config=None):
        self.name = "RiskGuardAgent"
        self.config = config or {}
        
        # Default risk parameters
        self.max_position_size = self.config.get("max_position_size", 0.1)  # 10% of capital
        self.max_open_positions = self.config.get("max_open_positions", 3)
        self.max_drawdown = self.config.get("max_drawdown", 0.05)  # 5% drawdown limit
        
        logging.info(f"RiskGuardAgent initialized with max position size: {self.max_position_size}, "
                  f"max open positions: {self.max_open_positions}")
    
    def evaluate_trade(self, trade_proposal, current_portfolio=None):
        """
        Evaluate a trade proposal and determine if it should be approved or rejected.
        
        Args:
            trade_proposal: The proposed trade
            current_portfolio: Current portfolio state
            
        Returns:
            Dictionary with approval status and reason
        """
        # Default to empty portfolio
        current_portfolio = current_portfolio or {"open_positions": [], "capital": 10000.0}
        
        # Check number of open positions
        if len(current_portfolio["open_positions"]) >= self.max_open_positions:
            return {
                "approved": False,
                "reason": f"Maximum number of open positions ({self.max_open_positions}) reached"
            }
        
        # Check position size
        position_size = trade_proposal.get("position_size", 0)
        if position_size > self.max_position_size:
            return {
                "approved": False,
                "reason": f"Position size ({position_size:.2%}) exceeds maximum allowed ({self.max_position_size:.2%})"
            }
        
        # More risk checks could be added here
        
        return {
            "approved": True,
            "reason": "Trade proposal meets risk parameters"
        }


def run_sentiment_demo(symbol="BTC/USDT"):
    """Run a demo of the sentiment analysis functionality."""
    print("=" * 60)
    print(f"aGENtrader {VERSION} - Sentiment Analysis Demo")
    print("=" * 60)
    
    # Check for XAI API key
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("Error: XAI_API_KEY environment variable not found.")
        print("Sentiment analysis requires a valid API key for Grok API.")
        return
    
    print(f"Running sentiment analysis for {symbol}...")
    
    # Create and run the SentimentAggregatorAgent
    sentiment_agent = SentimentAggregatorAgent()
    
    result = sentiment_agent.analyze(symbol=symbol)
    
    # Display results
    if result.get("status") == "error":
        print("⚠️ Error in sentiment analysis:")
        print(f"  Type: {result.get('error_type')}")
        print(f"  Message: {result.get('message')}")
        return
    
    print(f"📊 Sentiment Analysis for {result['symbol']}:")
    
    # Calculate sentiment tier based on score
    sentiment_score = result["sentiment_score"]
    if sentiment_score >= 4.5:
        sentiment_tier = "Extremely Bullish"
    elif sentiment_score >= 4:
        sentiment_tier = "Bullish"
    elif sentiment_score >= 3.5:
        sentiment_tier = "Slightly Bullish"
    elif sentiment_score >= 2.5:
        sentiment_tier = "Neutral"
    elif sentiment_score >= 2:
        sentiment_tier = "Slightly Bearish"  
    elif sentiment_score >= 1.5:
        sentiment_tier = "Bearish"
    else:
        sentiment_tier = "Extremely Bearish"
    
    print(f"  Sentiment Score: {sentiment_score} ({sentiment_tier})")
    print(f"  Confidence: {result['confidence']}%")
    print(f"  Analysis: {result['analysis_summary']}")
    
    if "sentiment_signals" in result:
        print("\n🔑 Key Signals:")
        for signal in result["sentiment_signals"]:
            print(f"  • {signal}")
    
    print("\nDemo completed successfully!")

def run_technical_analysis(symbol, interval, data_provider):
    """Run technical analysis and log the results."""
    try:
        # Initialize the technical analyst agent
        tech_agent = TechnicalAnalystAgent(data_fetcher=data_provider)
        
        # Get agent's configured timeframe from its initialization
        # We don't pass the system interval to respect the agent-specific timeframe
        logging.info(f"Running technical analysis for {symbol} using agent's configured timeframe")
        result = tech_agent.analyze(symbol=symbol)
        
        # Extract the actual interval used for logging purposes
        used_interval = result.get("interval", "unknown")
        logging.info(f"Technical analysis completed using {used_interval} timeframe")
        
        # Log the decision
        decision_logger.create_summary_from_result("TechnicalAnalystAgent", result, symbol)
        
        return result
    except Exception as e:
        logging.error(f"Error in technical analysis: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}

def run_sentiment_analysis(symbol, interval, data_provider=None):
    """Run sentiment analysis and log the results."""
    try:
        # Check for xAI API key
        if not os.environ.get("XAI_API_KEY"):
            logging.warning("XAI_API_KEY not found, sentiment analysis will be skipped")
            return {"status": "skipped", "reason": "XAI_API_KEY not found"}
        
        # Initialize the sentiment agent
        sentiment_agent = SentimentAggregatorAgent()
        
        # Get agent's configured timeframe from its initialization
        # We don't pass the system interval to respect the agent-specific timeframe
        logging.info(f"Running sentiment analysis for {symbol} using agent's configured timeframe")
        result = sentiment_agent.analyze(symbol=symbol)
        
        # Extract the actual interval used for logging purposes
        used_interval = result.get("interval", "unknown")
        logging.info(f"Sentiment analysis completed using {used_interval} timeframe")
        
        # Log the decision
        decision_logger.create_summary_from_result("SentimentAggregatorAgent", result, symbol)
        
        return result
    except Exception as e:
        logging.error(f"Error in sentiment analysis: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}

def run_liquidity_analysis(symbol, interval, data_provider):
    """Run liquidity analysis and log the results."""
    try:
        # Initialize the liquidity analyst agent - note that it doesn't need a data_provider in constructor
        liquidity_agent = LiquidityAnalystAgent()
        
        # Get agent's configured timeframe from its initialization
        # We don't pass the system interval to respect the agent-specific timeframe
        logging.info(f"Running liquidity analysis for {symbol} using agent's configured timeframe")
        result = liquidity_agent.analyze(symbol=symbol)
        
        # Extract the actual interval used for logging purposes
        used_interval = result.get("interval", "unknown")
        logging.info(f"Liquidity analysis completed using {used_interval} timeframe")
        
        # Log the decision
        decision_logger.create_summary_from_result("LiquidityAnalystAgent", result, symbol)
        
        return result
    except Exception as e:
        logging.error(f"Error in liquidity analysis: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}

def run_funding_rate_analysis(symbol, interval, data_provider):
    """Run funding rate analysis and log the results."""
    try:
        # Initialize the funding rate analyst agent
        funding_agent = FundingRateAnalystAgent()
        
        # Get agent's configured timeframe from its initialization
        # We don't pass the system interval to respect the agent-specific timeframe
        logging.info(f"Running funding rate analysis for {symbol} using agent's configured timeframe")
        result = funding_agent.analyze(symbol=symbol)
        
        # Extract the actual interval used for logging purposes
        used_interval = result.get("interval", "unknown")
        logging.info(f"Funding rate analysis completed using {used_interval} timeframe")
        
        # Log the decision
        decision_logger.create_summary_from_result("FundingRateAnalystAgent", result, symbol)
        
        return result
    except Exception as e:
        logging.error(f"Error in funding rate analysis: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}

def run_open_interest_analysis(symbol, interval, data_provider):
    """Run open interest analysis and log the results."""
    try:
        # Initialize the open interest analyst agent
        oi_agent = OpenInterestAnalystAgent()
        
        # Get agent's configured timeframe from its initialization
        # We don't pass the system interval to respect the agent-specific timeframe
        logging.info(f"Running open interest analysis for {symbol} using agent's configured timeframe")
        result = oi_agent.analyze(symbol=symbol)
        
        # Extract the actual interval used for logging purposes
        used_interval = result.get("interval", "unknown")
        logging.info(f"Open interest analysis completed using {used_interval} timeframe")
        
        # Log the decision
        decision_logger.create_summary_from_result("OpenInterestAnalystAgent", result, symbol)
        
        return result
    except Exception as e:
        logging.error(f"Error in open interest analysis: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}

def process_trading_decision(symbol, interval, data_provider, trade_book_manager, risk_guard, performance_tracker=None):
    """Process trading decisions from all agents and execute trades if approved."""
    try:
        # Log the start of the decision process for validation detection
        logging.info(f"Starting trading decision process for {symbol} at {interval}")
        
        # Get current price
        current_price = data_provider.get_current_price(symbol.replace("/", ""))
        
        # Run all analyst agents with explicit logging for validation detection
        logging.info("TechnicalAnalystAgent processing market data...")
        ta_result = run_technical_analysis(symbol, interval, data_provider)
        
        logging.info("SentimentAnalystAgent analyzing market sentiment...")
        sentiment_result = run_sentiment_analysis(symbol, interval, data_provider)
        
        logging.info("LiquidityAnalystAgent evaluating market depth...")
        liquidity_result = run_liquidity_analysis(symbol, interval, data_provider)
        
        logging.info("FundingRateAnalystAgent examining funding rates...")
        funding_rate_result = run_funding_rate_analysis(symbol, interval, data_provider)
        
        logging.info("OpenInterestAnalystAgent analyzing open interest...")
        open_interest_result = run_open_interest_analysis(symbol, interval, data_provider)
        
        # Combine all agent analyses into a single dictionary for the DecisionAgent
        agent_analyses = {
            "technical_analysis": ta_result,
            "sentiment_analysis": sentiment_result, 
            "liquidity_analysis": liquidity_result,
            "funding_rate_analysis": funding_rate_result,
            "open_interest_analysis": open_interest_result
        }
        
        # Log which agents are contributing to the decision
        active_agents = [key for key, value in agent_analyses.items() 
                         if isinstance(value, dict) and not value.get("error")]
        logging.info(f"✅ Decision using: {', '.join(active_agents)}")
        
        # Initialize the DecisionAgent and make a decision
        decision_agent = DecisionAgent()
        decision = decision_agent.make_decision(agent_analyses, symbol=symbol, interval=interval)
        
        # Create trade proposal based on the integrated decision
        confidence = decision.get("confidence", 0)
        if not isinstance(confidence, (int, float)):
            confidence = 0
        
        trade_proposal = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "interval": interval,
            "price": current_price,
            "type": decision.get("action", "HOLD"),
            "confidence": confidence,
            "position_size": float(confidence) / 100.0 * 0.1,  # Scale position size by confidence
            "reason": decision.get("reason", "No reason provided"),
            "technical_signals": ta_result.get("indicators", []),
            "sentiment_score": sentiment_result.get("sentiment_score", 3),
            "sentiment_signals": sentiment_result.get("sentiment_signals", []),
            "decision_method": decision.get("decision_method", "unknown")
        }
        
        # Evaluate trade with risk guard
        risk_evaluation = risk_guard.evaluate_trade(trade_proposal)
        
        # Prepare the decision data with agent analyses for performance tracking
        decision_data = {
            "symbol": symbol,
            "interval": interval,
            "price": current_price,
            "type": trade_proposal["type"],
            "confidence": trade_proposal["confidence"],
            "reason": trade_proposal["reason"],
            "agent_analyses": {
                "TechnicalAnalystAgent": {
                    "signal": ta_result.get("signal", "NEUTRAL"),
                    "confidence": ta_result.get("confidence", 0)
                },
                "SentimentAnalystAgent": {
                    "signal": sentiment_result.get("signal", "NEUTRAL"),
                    "confidence": sentiment_result.get("confidence", 0)
                },
                "LiquidityAnalystAgent": {
                    "signal": liquidity_result.get("signal", "NEUTRAL"),
                    "confidence": liquidity_result.get("confidence", 0)
                },
                "FundingRateAnalystAgent": {
                    "signal": funding_rate_result.get("signal", "NEUTRAL"),
                    "confidence": funding_rate_result.get("confidence", 0)
                },
                "OpenInterestAnalystAgent": {
                    "signal": open_interest_result.get("signal", "NEUTRAL"),
                    "confidence": open_interest_result.get("confidence", 0)
                }
            }
        }
        
        # Record the decision in the performance tracker if available
        trade_id = None
        if performance_tracker:
            trade_id = performance_tracker.record_decision(decision_data)
            logging.info(f"Decision recorded in performance tracker with ID: {trade_id}")
        
        if risk_evaluation["approved"] and trade_proposal["type"] in ["BUY", "SELL"]:
            # Record approved trade in trade book manager
            trade_book_manager.record_trade(trade_proposal)
            
            # Generate simulated performance (for legacy compatibility)
            performance_data = {
                "trade_id": trade_id or str(int(time.time())),
                "symbol": symbol,
                "entry_price": current_price,
                "entry_time": trade_proposal["timestamp"],
                "position_size": trade_proposal["position_size"],
                "simulated_exit_price": current_price * (1.01 if trade_proposal["type"] == "BUY" else 0.99),
                "simulated_profit_loss": 0.01 if trade_proposal["type"] == "BUY" else -0.01,
                "technical_confidence": ta_result.get("confidence", 50),
                "sentiment_score": sentiment_result.get("sentiment_score", 3),
                "contributing_agents": active_agents
            }
            
            # Record in legacy trade book
            trade_book_manager.record_performance(performance_data)
            
            logging.info(f"Trade executed: {trade_proposal['type']} {symbol} @ {current_price}")
            logging.info(f"Reasoning: {trade_proposal['reason']}")
            
        else:
            # Record rejected trade or HOLD decision
            if trade_proposal["type"] == "HOLD":
                logging.info(f"HOLD decision for {symbol} @ {current_price}")
                logging.info(f"Reasoning: {trade_proposal['reason']}")
            else:
                trade_book_manager.record_rejected_trade(trade_proposal, risk_evaluation["reason"])
                logging.info(f"Trade rejected: {trade_proposal['type']} {symbol} - Reason: {risk_evaluation['reason']}")
        
        # Update performance metrics if using performance tracker
        if performance_tracker and trade_id:
            max_hold_time = int(os.getenv("MAX_HOLD_TIME_MINUTES", "60"))
            performance_tracker.update_performance(data_provider, max_hold_time)
            
        return {
            "trade_proposal": trade_proposal,
            "decision": decision,
            "risk_evaluation": risk_evaluation,
            "agent_analyses": agent_analyses,
            "status": "success"
        }
        
    except Exception as e:
        logging.error(f"Error processing trading decision: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}

def main():
    """Initialize and run the trading system."""
    # Set up logging
    logger = setup_logging()
    
    # Check if we're running in Docker
    in_docker = os.environ.get("IN_DOCKER", "false").lower() == "true"
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Extra safety: Force test mode in Docker environment
    if in_docker and args.mode == "demo":
        logger.warning("Detected demo mode in Docker environment. Forcing test mode for container stability.")
        args.mode = "test"
        
    # Display version banner
    if os.isatty(sys.stdout.fileno()):  # Only show ASCII logo in interactive terminal
        print(get_version_banner(include_logo=True, mini=True))
    
    logger.info(f"Starting aGENtrader {VERSION} in {args.mode} mode {'(Docker environment)' if in_docker else ''}")
    
    # Run sentiment analysis demo if requested
    if args.sentiment:
        run_sentiment_demo(symbol=args.symbol)
        return
    
    # Regular system startup
    logger.info(f"Trading pair: {args.symbol}, Interval: {args.interval}")
    
    try:
        # Check API keys
        binance_key = os.getenv("BINANCE_API_KEY")
        binance_secret = os.getenv("BINANCE_API_SECRET")
        xai_key = os.getenv("XAI_API_KEY")
        
        # Handle missing keys
        if not binance_key or not binance_secret:
            logger.error("BINANCE_API_KEY and BINANCE_API_SECRET are required")
            return
        
        if not xai_key:
            logger.warning("XAI_API_KEY not found. Sentiment analysis will be disabled.")
        
        # Initialize components
        logger.info("Initializing system components...")
        
        # Initialize data provider
        try:
            # Determine if we should use testnet based on env
            use_testnet = os.getenv("BINANCE_USE_TESTNET", "false").lower() == "true"
            
            # If we're in Docker, we should be more resilient to startup issues
            if in_docker:
                # Docker environment - retry Binance connection a few times
                max_retries = 3
                retry_count = 0
                last_error = None
                
                while retry_count < max_retries:
                    try:
                        logger.info(f"Connecting to Binance API (attempt {retry_count+1}/{max_retries})...")
                        data_provider = BinanceDataProvider(api_key=binance_key, api_secret=binance_secret, use_testnet=use_testnet)
                        
                        # Test provider with a simple ping request
                        data_provider._make_request("/api/v3/ping")
                        logger.info(f"Initialized Binance Data Provider using {'testnet' if use_testnet else 'mainnet'}")
                        break
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Binance API connection failed (attempt {retry_count+1}): {str(e)}")
                        retry_count += 1
                        if retry_count < max_retries:
                            sleep_time = 5 * retry_count  # Increasing backoff
                            logger.info(f"Retrying in {sleep_time} seconds...")
                            time.sleep(sleep_time)
                
                if retry_count >= max_retries:
                    if args.mode == "demo":
                        logger.warning(f"Binance API access failed after {max_retries} attempts: {str(last_error)}")
                        logger.warning("Falling back to demo mode with simulated data")
                        from agents.data_providers.mock_data_provider import MockDataProvider
                        data_provider = MockDataProvider(symbol=args.symbol)
                        logger.info("Mock Data Provider initialized for demo mode")
                    else:
                        if last_error is not None:
                            raise last_error
                        else:
                            raise Exception("Failed to connect to Binance API after multiple attempts")
            else:
                # Normal environment - single attempt
                data_provider = BinanceDataProvider(api_key=binance_key, api_secret=binance_secret, use_testnet=use_testnet)
                
                # Test provider with a simple ping request
                data_provider._make_request("/api/v3/ping")
                logger.info(f"Initialized Binance Data Provider using {'testnet' if use_testnet else 'mainnet'}")
        except Exception as e:
            if args.mode == "demo":
                logger.warning(f"Binance API access failed: {str(e)}")
                logger.warning("Running in demo mode with simulated data")
                from agents.data_providers.mock_data_provider import MockDataProvider
                data_provider = MockDataProvider(symbol=args.symbol)
                logger.info("Mock Data Provider initialized for demo mode")
            else:
                raise
        
        # Initialize trade book manager
        trade_book_manager = TradeBookManager()
        logger.info("Trade Book Manager initialized")
        
        # Initialize performance tracker
        performance_tracker = PerformanceTracker()
        logger.info("Performance Tracker initialized")
        
        # Initialize risk guard
        risk_guard = RiskGuardAgent()
        logger.info("Risk Guard Agent initialized")
        
        # Initialize scheduler
        scheduler = DecisionTriggerScheduler()
        
        # Schedule triggers for the trading interval
        def trigger_callback(symbol=args.symbol, interval=args.interval):
            return process_trading_decision(
                symbol, 
                interval, 
                data_provider, 
                trade_book_manager, 
                risk_guard,
                performance_tracker
            )
        
        scheduler.schedule_trigger(args.interval, trigger_callback, args.symbol)
        logger.info(f"Decision trigger scheduled for {args.symbol} at {args.interval} interval")
        
        # Print system status
        logger.info("System initialization complete")
        logger.info(f"Running in {args.mode} mode with {args.symbol} at {args.interval} interval")
        
        # Main loop
        demo_override = os.environ.get("DEMO_OVERRIDE", "false").lower() == "true"
        continuous_run = os.environ.get("CONTINUOUS_RUN", "false").lower() == "true"
        
        # If running in Docker via docker_run.py, always force continuous mode
        if in_docker or continuous_run:
            if args.mode == "demo":
                logger.info("Demo mode detected in Docker environment. Forcing continuous mode.")
                args.mode = "test"
        
        if args.mode == "demo":
            # In demo mode, run once and exit
            logger.info("Demo mode active. Running one trading cycle.")
            result = process_trading_decision(
                args.symbol, 
                args.interval, 
                data_provider, 
                trade_book_manager, 
                risk_guard,
                performance_tracker
            )
            logger.info(f"Demo cycle completed with status: {result['status']}")
        else:
            # Force continuous mode if requested via environment
            if demo_override:
                logger.info("Demo mode behaviors disabled by DEMO_OVERRIDE.")
                args.mode = "test"
                
            # In all other modes, keep the system running
            logger.info(f"System running in {args.mode} mode. Press Ctrl+C to stop.")
            
            runtime_start = time.time()
            check_interval = 30  # seconds
            
            # Parse test duration
            duration_str = os.getenv("TEST_DURATION", "2h")
            duration_unit = duration_str[-1]
            duration_value = int(duration_str[:-1])
            
            if duration_unit == 'm':
                duration_seconds = duration_value * 60
            elif duration_unit == 'h':
                duration_seconds = duration_value * 60 * 60
            elif duration_unit == 'd':
                duration_seconds = duration_value * 24 * 60 * 60
            else:
                logger.warning(f"Unsupported duration unit: {duration_unit}. Using default of 2 hours.")
                duration_seconds = 2 * 60 * 60
                
            logger.info(f"Test will run for {duration_str} ({duration_seconds} seconds)")
            
            while time.time() - runtime_start < duration_seconds:
                # Check scheduled triggers
                scheduler.check_triggers()
                
                # Sleep
                time.sleep(check_interval)
                
                # Log activity
                elapsed = time.time() - runtime_start
                remaining = duration_seconds - elapsed
                logger.info(f"System active - elapsed: {int(elapsed/60)}m, remaining: {int(remaining/60)}m")
            
            logger.info(f"Test duration of {duration_str} completed")
                
    except KeyboardInterrupt:
        logger.info(f"Shutting down aGENtrader {VERSION}...")
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}", exc_info=True)
    finally:
        logger.info(f"aGENtrader {VERSION} shutdown complete")

if __name__ == "__main__":
    main()