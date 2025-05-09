"""
aGENtrader v2 Live Trading System

This module implements the core trading functionality for the aGENtrader v2 system.
It integrates all the specialist agents to make trading decisions.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from aGENtrader_v2.core.trigger_scheduler import DecisionTriggerScheduler

# Setup logger
logger = logging.getLogger("aGENtrader.live_trading")

class LiveTradingSystem:
    """The main trading system for aGENtrader v2."""
    
    def __init__(
        self,
        symbol: str = "BTC/USDT",
        interval: str = "1h",
        config_path: str = "config/default.json",
        mode: str = "test",
        duration: Optional[str] = "24h",
        align_to_clock: bool = True
    ):
        """
        Initialize the live trading system.
        
        Args:
            symbol: Trading symbol (e.g., BTC/USDT)
            interval: Time interval for market data (e.g., 1h, 4h, 1d)
            config_path: Path to configuration file
            mode: Trading mode ('test' or 'live')
            duration: Test duration (e.g., '24h', '7d'), only used in test mode
            align_to_clock: Whether to align trading decisions to clock boundaries
        """
        self.symbol = symbol
        self.interval = interval
        self.mode = mode
        self.duration = self._parse_duration(duration) if duration and mode == "test" else None
        self.start_time = datetime.now()
        self.align_to_clock = align_to_clock
        
        # Initialize the scheduler
        self.scheduler = DecisionTriggerScheduler(
            interval=interval,
            align_to_clock=align_to_clock,
            log_file="logs/trading_triggers.jsonl"
        )
        
        # Load configuration
        self.config = self._load_config(config_path)
        logger.info(f"Loaded configuration from {config_path}")
        
        # Initialize trading components
        self._initialize_components()
        
        # Trade tracking
        self.open_trades = {}
        self.closed_trades = []
        
        logger.info(f"LiveTradingSystem initialized for {symbol} on {interval} interval")
        
    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse duration string to timedelta object."""
        try:
            value = int(duration_str[:-1])
            unit = duration_str[-1].lower()
            
            if unit == 'h':
                return timedelta(hours=value)
            elif unit == 'd':
                return timedelta(days=value)
            elif unit == 'w':
                return timedelta(weeks=value)
            else:
                raise ValueError(f"Unsupported duration unit: {unit}")
        except (ValueError, IndexError):
            logger.warning(f"Invalid duration format: {duration_str}, defaulting to 24h")
            return timedelta(hours=24)
            
    def _parse_interval(self, interval_str: str) -> int:
        """
        Parse an interval string (e.g., '1h', '4h', '1d') to seconds.
        
        Args:
            interval_str: Interval string (e.g., '1h', '4h', '1d')
            
        Returns:
            Number of seconds
        """
        try:
            value = int(interval_str[:-1])
            unit = interval_str[-1].lower()
            
            if unit == 'm':
                return value * 60
            elif unit == 'h':
                return value * 3600
            elif unit == 'd':
                return value * 86400
            else:
                logger.warning(f"Unknown interval unit {unit}, defaulting to 1 hour")
                return 3600
        except (ValueError, IndexError):
            logger.warning(f"Invalid interval format {interval_str}, defaulting to 1 hour")
            return 3600
            
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            logger.info("Using default configuration")
            return {
                "risk_tolerance": "moderate",
                "max_position_size_pct": 10.0,
                "stop_loss_pct": 5.0,
                "take_profit_pct": 10.0,
                "api": {
                    "coinapi": {
                        "key": os.environ.get("COINAPI_KEY", "")
                    }
                },
                "agents": {
                    "technical": {"confidence_threshold": 60},
                    "sentiment": {"confidence_threshold": 60},
                    "fundamental": {"confidence_threshold": 60},
                    "risk_guard": {"max_risk_score": 80}
                }
            }
    
    def _initialize_components(self):
        """Initialize all trading system components."""
        # Import here to avoid circular dependencies
        from aGENtrader_v2.agents.technical_analyst_agent import TechnicalAnalystAgent
        from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory
        from aGENtrader_v2.agents.trade_book_manager import TradeBookManager
        from aGENtrader_v2.agents.trade_executor_agent import TradeExecutorAgent
        
        # Initialize data provider factory
        api_config = {}
        
        # Get CoinAPI key from config or environment
        coinapi_key = self.config.get("api", {}).get("coinapi", {}).get("key")
        if not coinapi_key:
            coinapi_key = os.environ.get("COINAPI_KEY", "")
            if not coinapi_key:
                logger.warning("No CoinAPI key provided. Data fetching may fall back to limited/unauthenticated access.")
        
        # Set up config for data provider factory
        api_config = {
            "coinapi": {
                "key": coinapi_key
            },
            # Binance keys would be configured here too
            "use_binance": False  # Set to True once Binance implementation is completed
        }
        
        # Create the data provider factory
        self.data_provider_factory = DataProviderFactory(config=api_config)
        logger.info("Initialized DataProviderFactory")
        
        # Create a direct data fetcher from the factory for components that don't support factory pattern
        self.data_fetcher = self.data_provider_factory.create_provider()
        logger.info(f"Created direct data fetcher from factory")
        
        # Initialize trade book manager for tracking positions
        self.trade_book = TradeBookManager(
            trade_log_path=f"logs/trade_book_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        logger.info("Initialized TradeBookManager")
        
        # Initialize trade executor 
        self.trade_executor = TradeExecutorAgent(
            config=self.config,
            trade_book_manager=self.trade_book,
            data_provider_factory=self.data_provider_factory
        )
        logger.info("Initialized TradeExecutorAgent")
        
        # Initialize analyst agents
        self.technical_agent = TechnicalAnalystAgent(data_fetcher=self.data_fetcher)
        logger.info("Initialized Technical Analyst Agent")
        
        # More agents will be initialized here as they are implemented
    
    def run(self):
        """Run the trading system."""
        logger.info(f"Starting trading system in {self.mode} mode")
        
        if self.mode == "test":
            self._run_test_mode()
        else:
            self._run_live_mode()
        
        logger.info("Trading system execution completed")
    
    def _run_test_mode(self):
        """Run the system in test mode for a fixed duration."""
        if self.duration is None:
            self.duration = timedelta(hours=24)
            
        end_time = self.start_time + self.duration
        logger.info(f"Test mode will run until {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create a test-specific scheduler with faster intervals
        # We'll make it 4x faster for testing
        test_interval = f"{max(1, int(self._parse_interval(self.interval) / 4))}{self.interval[-1]}"
        logger.info(f"Using accelerated test interval: {test_interval} (4x faster than {self.interval})")
        
        test_scheduler = DecisionTriggerScheduler(
            interval=test_interval,
            align_to_clock=self.align_to_clock,
            log_file="logs/test_triggers.jsonl"
        )
        
        iteration = 1
        while datetime.now() < end_time:
            cycle_start_time = datetime.now()
            logger.info(f"Test iteration {iteration} started at {cycle_start_time.isoformat()}")
            
            try:
                # Get market data
                market_data = self._fetch_market_data()
                
                # Run analysis
                analysis_results = self._run_analysis(market_data)
                
                # Make trading decision
                decision = self._make_decision(analysis_results)
                
                # Log the decision
                self._log_decision(decision)
                
                # Calculate cycle duration
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                logger.info(f"Cycle {iteration} completed in {cycle_duration:.2f} seconds")
                
                # Wait for next scheduled time using the scheduler
                trigger_time, wait_duration = test_scheduler.wait_for_next_tick()
                logger.info(f"Test iteration {iteration} completed, next iteration at {trigger_time.isoformat()}")
                
            except Exception as e:
                logger.error(f"Error in test iteration {iteration}: {e}")
                logger.exception("Exception details:")
                # Still use the scheduler for consistency, but with a shorter emergency interval
                emergency_scheduler = DecisionTriggerScheduler(interval="1m", align_to_clock=False)
                emergency_scheduler.wait_for_next_tick()
            
            iteration += 1
    
    def _run_live_mode(self):
        """Run the system in live trading mode."""
        logger.info("Starting live trading mode")
        
        # Initialize the precision scheduler for live trading
        logger.info(f"Using scheduler with interval {self.interval} and clock alignment {self.align_to_clock}")
        
        iteration = 1
        while True:
            cycle_start_time = datetime.now()
            logger.info(f"Live trading iteration {iteration} started at {cycle_start_time.isoformat()}")
            
            try:
                # Get market data
                market_data = self._fetch_market_data()
                
                # Run analysis
                analysis_results = self._run_analysis(market_data)
                
                # Make trading decision
                decision = self._make_decision(analysis_results)
                
                # Execute the decision if action is required
                if decision["action"] in ["BUY", "SELL"]:
                    self._execute_trade(decision)
                
                # Log the decision
                self._log_decision(decision)
                
                # Calculate cycle duration
                cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
                logger.info(f"Cycle {iteration} completed in {cycle_duration:.2f} seconds")
                
                # Wait for next scheduled time using the scheduler
                trigger_time, wait_duration = self.scheduler.wait_for_next_tick()
                logger.info(f"Live iteration {iteration} completed, next iteration at {trigger_time.isoformat()}")
                
            except Exception as e:
                logger.error(f"Error in live iteration {iteration}: {e}")
                logger.exception("Exception details:")
                
                # Still use a scheduler for recovery, but with a shorter emergency interval
                emergency_scheduler = DecisionTriggerScheduler(interval="5m", align_to_clock=False)
                emergency_scheduler.wait_for_next_tick()
            
            iteration += 1
    
    def _fetch_market_data(self) -> Dict[str, Any]:
        """Fetch current market data for the specified symbol and interval."""
        logger.info(f"Fetching market data for {self.symbol} on {self.interval} interval")
        
        try:
            # Convert symbol format if needed (BTC/USDT -> BTCUSDT)
            symbol_for_api = self.symbol.replace("/", "")
            
            # Fetch OHLCV data
            ohlcv_data = self.data_fetcher.fetch_ohlcv(
                symbol=symbol_for_api,
                interval=self.interval,
                limit=100  # Get enough historical data for technical analysis
            )
            
            # Get current market prices
            ticker = self.data_fetcher.fetch_ticker(symbol_for_api)
            
            # Combine all market data
            market_data = {
                "symbol": self.symbol,
                "interval": self.interval,
                "timestamp": datetime.now().isoformat(),
                "ohlcv": ohlcv_data,
                "ticker": ticker
            }
            
            logger.debug(f"Fetched market data successfully")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            # Return minimal data to continue operation
            return {
                "symbol": self.symbol,
                "interval": self.interval,
                "timestamp": datetime.now().isoformat(),
                "ohlcv": [],
                "ticker": {"last": None}
            }
    
    def _run_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all analysis agents on the market data."""
        results = {}
        
        # Run technical analysis
        try:
            logger.info("Running technical analysis")
            technical_analysis = self.technical_agent.analyze(
                symbol=self.symbol,
                interval=self.interval,
                market_data=market_data
            )
            results["technical"] = technical_analysis
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            results["technical"] = {"error": str(e)}
        
        # More analysis agents will be added here
        
        return results
    
    def _make_decision(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Make a trading decision based on analysis results."""
        logger.info("Making trading decision")
        
        # For now, just use technical analysis as the sole decision maker
        if "technical" in analysis_results and "action" in analysis_results["technical"]:
            tech_analysis = analysis_results["technical"]
            
            decision = {
                "timestamp": datetime.now().isoformat(),
                "symbol": self.symbol,
                "action": tech_analysis["action"],
                "confidence": tech_analysis.get("confidence", 0),
                "reason": tech_analysis.get("reasoning", "Based on technical analysis"),
                "analysis": analysis_results
            }
            
            logger.info(f"Decision: {decision['action']} with confidence {decision['confidence']}")
            return decision
        else:
            # Default to HOLD if no analysis available
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": self.symbol,
                "action": "HOLD",
                "confidence": 0,
                "reason": "Insufficient analysis data",
                "analysis": analysis_results
            }
    
    def _execute_trade(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade based on the decision."""
        logger.info(f"Executing {decision['action']} trade for {self.symbol}")
        
        # Import here to avoid circular imports
        from aGENtrader_v2.agents.trade_executor_agent import TradeExecutorAgent
        
        # Initialize trade executor if it doesn't exist yet
        if not hasattr(self, 'trade_executor'):
            # Import the factory if needed
            from aGENtrader_v2.data.feed.data_provider_factory import DataProviderFactory
            
            # Create a new factory if one doesn't exist
            if not hasattr(self, 'data_provider_factory'):
                coinapi_key = os.environ.get("COINAPI_KEY", "")
                self.data_provider_factory = DataProviderFactory(config={"coinapi": {"key": coinapi_key}})
            
            # Create trade book manager if it doesn't exist
            if not hasattr(self, 'trade_book'):
                from aGENtrader_v2.agents.trade_book_manager import TradeBookManager
                self.trade_book = TradeBookManager()
            
            self.trade_executor = TradeExecutorAgent(
                config=self.config,
                trade_book_manager=self.trade_book,
                data_provider_factory=self.data_provider_factory
            )
            logger.info("Initialized TradeExecutorAgent")
        
        # Get current market data
        market_data = self._fetch_market_data()
        
        # Let the trade executor handle the decision
        result = self.trade_executor.execute_decision(decision, market_data)
        
        if result["status"] == "success" and result["action"] != "HOLD":
            logger.info(
                f"Trade executed: {result['action']} {self.symbol} "
                f"at {result.get('entry_price', 'unknown price')}"
            )
        elif result["status"] == "hold":
            logger.info(f"Position already open, holding: {result['reason']}")
        elif result["status"] == "skipped":
            logger.info(f"Trade skipped: {result['reason']}")
        else:
            logger.warning(f"Trade execution result: {result}")
        
        return result
    
    def _log_decision(self, decision: Dict[str, Any]):
        """Log a trading decision to a file."""
        try:
            decisions_dir = "logs/decisions"
            os.makedirs(decisions_dir, exist_ok=True)
            
            filename = f"{decisions_dir}/{self.symbol.replace('/', '')}_decisions.jsonl"
            with open(filename, 'a') as f:
                f.write(json.dumps(decision) + '\n')
        except Exception as e:
            logger.error(f"Error logging decision: {e}")
    
    def _get_current_price(self) -> float:
        """Get the current price of the trading pair."""
        try:
            # Convert symbol format if needed (BTC/USDT -> BTCUSDT)
            symbol_for_api = self.symbol.replace("/", "")
            
            # Fetch current ticker data
            ticker = self.data_fetcher.fetch_ticker(symbol_for_api)
            return ticker.get("last", 0.0)
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return 0.0
    
    def _get_interval_seconds(self) -> int:
        """Convert interval string to seconds."""
        try:
            value = int(self.interval[:-1])
            unit = self.interval[-1].lower()
            
            if unit == 'm':
                return value * 60
            elif unit == 'h':
                return value * 3600
            elif unit == 'd':
                return value * 86400
            else:
                logger.warning(f"Unknown interval unit {unit}, defaulting to 1 hour")
                return 3600
        except (ValueError, IndexError):
            logger.warning(f"Invalid interval format {self.interval}, defaulting to 1 hour")
            return 3600