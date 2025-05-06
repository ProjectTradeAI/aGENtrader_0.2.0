#!/usr/bin/env python3
"""
aGENtrader v2 Test Harness Utility

This script allows testing of individual analyst agents in isolation with:
- Controlled input data (real or mock)
- Full visibility into decision processes
- Deterministic testing for reproducibility
- Flexible agent selection via CLI
- Full decision cycle testing with multiple agents
- Styled agent voice outputs via ToneAgent

Usage:
  python3 tests/test_harness.py \
    --agent TechnicalAnalystAgent \
    --symbol BTC/USDT \
    --interval 4h \
    --mock-data \
    --temperature 0.0 \
    --explain \
    --repeat 3
"""

import os
import sys
import argparse
import importlib
import inspect
import json
import re
import time
import logging
from datetime import datetime

# Try to import required packages, but continue with warnings if not available
try:
    import numpy as np
except ImportError:
    try:
        import subprocess
        print("Attempting to install numpy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np
    except Exception as e:
        print(f"Warning: Could not import or install numpy: {str(e)}")
        print("Will use minimal functionality without numpy")
        # Define a minimal numpy substitute that supports the operations we need
        class NumpySubstitute:
            def sqrt(self, x):
                return x ** 0.5
        np = NumpySubstitute()

try:
    import pandas as pd
except ImportError:
    try:
        import subprocess
        print("Attempting to install pandas...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
        import pandas as pd
    except Exception as e:
        print(f"Warning: Could not import or install pandas: {str(e)}")
        print("Using minimum functionality without pandas")
        # This is a very minimal stub, actual usage will likely fail
        pd = None
from typing import Dict, Any, List, Type, Optional, Union, Tuple
import colorama
from colorama import Fore, Style

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize colorama for cross-platform color support
colorama.init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format for testing output
)
logger = logging.getLogger('agent_test')

# Import necessary modules
try:
    # Import agent interfaces and base classes
    from agents.agent_interface import AgentInterface, AnalystAgentInterface, DecisionAgentInterface
    from agents.base_agent import BaseAgent, BaseAnalystAgent, BaseDecisionAgent
    
    # Import specialist agents (these may not all exist yet)
    # If any are missing, they will be set to None in AVAILABLE_AGENTS
    try:
        from agents.technical_analyst_agent import TechnicalAnalystAgent
        logger.info(f"{Fore.GREEN}Successfully imported TechnicalAnalystAgent{Style.RESET_ALL}")
    except ImportError as e:
        logger.error(f"{Fore.RED}ImportError for TechnicalAnalystAgent: {str(e)}{Style.RESET_ALL}")
        TechnicalAnalystAgent = None
        
    try:
        from agents.sentiment_analyst_agent import SentimentAnalystAgent
    except ImportError:
        SentimentAnalystAgent = None
        
    try:
        from agents.sentiment_aggregator_agent import SentimentAggregatorAgent
    except ImportError:
        SentimentAggregatorAgent = None
        
    try:
        from agents.liquidity_analyst_agent import LiquidityAnalystAgent
    except ImportError:
        LiquidityAnalystAgent = None
        
    try:
        from agents.funding_rate_analyst_agent import FundingRateAnalystAgent
    except ImportError:
        FundingRateAnalystAgent = None
        
    try:
        from agents.open_interest_analyst_agent import OpenInterestAnalystAgent
    except ImportError:
        OpenInterestAnalystAgent = None
        
    try:
        from agents.decision_agent import DecisionAgent
    except ImportError:
        DecisionAgent = None
        
    try:
        from agents.trade_plan_agent import TradePlanAgent, create_trade_plan_agent
    except ImportError:
        TradePlanAgent = None
        create_trade_plan_agent = None
        
    try:
        from agents.portfolio_manager_agent import PortfolioManagerAgent
    except ImportError:
        PortfolioManagerAgent = None
    
    # Import ToneAgent for styled agent voices
    try:
        from agents.tone_agent import ToneAgent
        logger.info(f"{Fore.GREEN}Successfully imported ToneAgent{Style.RESET_ALL}")
    except ImportError as e:
        logger.error(f"{Fore.RED}ImportError for ToneAgent: {str(e)}{Style.RESET_ALL}")
        ToneAgent = None
    
    # Import data providers
    try:
        from agents.data_providers.mock_data_provider import MockDataProvider
    except ImportError:
        try:
            from utils.mock_data_provider import MockDataProvider
        except ImportError:
            # Create a simple mock provider if the imported one is not available
            logger.warning(f"{Fore.YELLOW}Mock data provider not found. Using simplified version.{Style.RESET_ALL}")
        
        class MockDataProvider:
            def __init__(self, symbol="BTC/USDT", **kwargs):
                self.symbol = symbol
                
            def get_current_price(self, symbol=None):
                return 50000.0
                
            def fetch_ohlcv(self, symbol=None, interval="1h", limit=100, **kwargs):
                # Generate simple mock candlestick data
                import time
                from datetime import datetime, timedelta
                
                symbol = symbol or self.symbol
                now = int(time.time() * 1000)
                result = []
                
                for i in range(limit):
                    timestamp = now - ((limit - i) * 3600 * 1000)  # Go back in time
                    result.append({
                        "timestamp": timestamp,
                        "datetime": datetime.fromtimestamp(timestamp / 1000).isoformat(),
                        "open": 50000.0 + (i * 100),
                        "high": 50000.0 + (i * 100) + 500,
                        "low": 50000.0 + (i * 100) - 500,
                        "close": 50000.0 + (i * 100) + 200,
                        "volume": 100.0 + (i * 10)
                    })
                    
                return result
                
            def fetch_market_depth(self, symbol=None, limit=100):
                return {
                    "bids": [[49900.0, 1.0], [49800.0, 2.0]],
                    "asks": [[50100.0, 1.0], [50200.0, 2.0]]
                }
    
    try:
        from binance_data_provider import BinanceDataProvider
    except ImportError:
        BinanceDataProvider = None
    
    # Other necessary imports
    try:
        from models.llm_client import LLMClient
    except ImportError:
        # Create minimal LLM client for testing if not available
        logger.warning(f"{Fore.YELLOW}LLMClient not found. Using mock version.{Style.RESET_ALL}")
        
        class LLMClient:
            def __init__(self, provider="mock", model="mock-model"):
                self.provider = provider
                self.model = model
                self.temperature = 0.0
                
            def query(self, prompt, **kwargs):
                return {
                    "content": "This is a mock response for testing purposes.",
                    "model": self.model,
                    "provider": self.provider
                }
    
    IMPORTED_SUCCESSFULLY = True
except ImportError as e:
    logger.error(f"{Fore.RED}Error importing agent modules: {str(e)}{Style.RESET_ALL}")
    logger.error(f"{Fore.YELLOW}Make sure you're running this script from the project root directory.{Style.RESET_ALL}")
    IMPORTED_SUCCESSFULLY = False

# Map of available agent classes
AVAILABLE_AGENTS = {
    # Base classes
    'BaseAgent': BaseAgent if IMPORTED_SUCCESSFULLY else None,
    'BaseAnalystAgent': BaseAnalystAgent if IMPORTED_SUCCESSFULLY else None,
    'BaseDecisionAgent': BaseDecisionAgent if IMPORTED_SUCCESSFULLY else None,
    
    # Specialized agents
    'TechnicalAnalystAgent': TechnicalAnalystAgent if IMPORTED_SUCCESSFULLY else None,
    'SentimentAnalystAgent': SentimentAnalystAgent if IMPORTED_SUCCESSFULLY else None,
    'SentimentAggregatorAgent': SentimentAggregatorAgent if IMPORTED_SUCCESSFULLY else None,
    'LiquidityAnalystAgent': LiquidityAnalystAgent if IMPORTED_SUCCESSFULLY else None,
    'FundingRateAnalystAgent': FundingRateAnalystAgent if IMPORTED_SUCCESSFULLY else None,
    'OpenInterestAnalystAgent': OpenInterestAnalystAgent if IMPORTED_SUCCESSFULLY else None,
    'DecisionAgent': DecisionAgent if IMPORTED_SUCCESSFULLY else None,
    'TradePlanAgent': TradePlanAgent if IMPORTED_SUCCESSFULLY else None,
    'PortfolioManagerAgent': PortfolioManagerAgent if IMPORTED_SUCCESSFULLY else None,
    'ToneAgent': ToneAgent if IMPORTED_SUCCESSFULLY else None
}

class AgentTestHarness:
    """
    Test harness for running individual agent tests with controlled parameters.
    """
    
    def __init__(
        self,
        agent_name: str,
        symbol: str = 'BTC/USDT',
        interval: str = '1h',
        use_mock_data: bool = False,
        temperature: float = 0.0,
        explain: bool = False,
        data_override: Optional[Dict[str, Any]] = None,
        log_conflict_traces: bool = True,
        interactive: bool = False
    ):
        """
        Initialize the test harness.
        
        Args:
            agent_name: Name of the agent class to test
            symbol: Trading symbol (e.g., BTC/USDT)
            interval: Time interval for analysis (e.g., 1h, 4h)
            use_mock_data: Whether to use mock data instead of real API
            temperature: Temperature setting for LLM to control randomness
            explain: Whether to print detailed explanations
            data_override: Override input data for the agent
            log_conflict_traces: Whether to enable structured logging of CONFLICTED decisions
            interactive: Whether to run in interactive mode with prompts for user input
        """
        # Initialize test results storage
        self.test_results = []
        self.agent_name = agent_name
        self.symbol = symbol
        self.interval = interval
        self.use_mock_data = use_mock_data
        self.temperature = temperature
        self.explain = explain
        self.data_override = data_override or {}
        self.full_cycle = False  # Whether to run full decision cycle with all agents
        self.trade_cycle = False  # Whether to run full trade cycle (including TradePlanAgent)
        self.trade_log = False  # Whether to save full JSON output of trade cycle test
        self.log_conflict_traces = log_conflict_traces  # Enable conflict logging by default in test mode
        self.interactive = interactive  # Whether to run in interactive mode
        
        # Check if agent is valid
        if agent_name not in AVAILABLE_AGENTS:
            valid_agents = sorted(AVAILABLE_AGENTS.keys())
            raise ValueError(
                f"Invalid agent name: {agent_name}. "
                f"Available agents are: {', '.join(valid_agents)}"
            )
            
        self.agent_class = AVAILABLE_AGENTS[agent_name]
        
        # Initialize data provider
        self._init_data_provider()
        
        # Monkey-patch LLMClient for capturing prompts and responses
        self._setup_llm_capture()
        
        # Prepare for ToneAgent initialization
        self.tone_agent = None  # Will be initialized after data_provider setup
        if ToneAgent:
            logger.info(f"{Fore.CYAN}ToneAgent will be initialized after data provider setup{Style.RESET_ALL}")
        else:
            logger.warning(f"{Fore.YELLOW}ToneAgent not available. Will use default reasoning output.{Style.RESET_ALL}")
    
    def _init_data_provider(self):
        """Initialize data provider based on configuration."""
        if self.use_mock_data:
            logger.info(f"{Fore.CYAN}Using mock data provider for {self.symbol}{Style.RESET_ALL}")
            self.data_provider = MockDataProvider(symbol=self.symbol)
        else:
            # Check for API keys
            binance_key = os.environ.get("BINANCE_API_KEY")
            binance_secret = os.environ.get("BINANCE_API_SECRET")
            
            if not binance_key or not binance_secret:
                logger.warning(
                    f"{Fore.YELLOW}Warning: BINANCE_API_KEY or BINANCE_API_SECRET not set. "
                    f"Falling back to mock data.{Style.RESET_ALL}"
                )
                self.data_provider = MockDataProvider(symbol=self.symbol)
                self.use_mock_data = True  # Update flag
            else:
                logger.info(f"{Fore.CYAN}Using Binance data provider for {self.symbol}{Style.RESET_ALL}")
                self.data_provider = BinanceDataProvider(
                    api_key=binance_key,
                    api_secret=binance_secret
                )
                
        # Now that data_provider is initialized, set up ToneAgent if needed
        if not hasattr(self, 'tone_agent') or self.tone_agent is None:
            if ToneAgent:
                try:
                    logger.info(f"{Fore.CYAN}Initializing ToneAgent with data provider...{Style.RESET_ALL}")
                    self.tone_agent = ToneAgent(
                        config={
                            "symbol": self.symbol,
                            "interval": self.interval,
                            "data_provider": self.data_provider
                        }
                    )
                    logger.info(f"{Fore.GREEN}ToneAgent successfully initialized{Style.RESET_ALL}")
                except Exception as e:
                    logger.error(f"{Fore.RED}Error initializing ToneAgent: {str(e)}{Style.RESET_ALL}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    self.tone_agent = None

    def _setup_llm_capture(self):
        """
        Set up LLM client capture for displaying prompts and responses.
        This monkey-patches the LLMClient.query method to capture I/O.
        """
        if not hasattr(self, '_original_llm_query'):
            self._original_llm_query = LLMClient.query
            self.captured_prompts = []
            self.captured_responses = []
            
            def captured_query(
                self_llm, 
                prompt, 
                provider=None, 
                system_prompt=None, 
                model=None, 
                json_response=False, 
                max_tokens=1000, 
                temperature=None
            ):
                # Override temperature if specified
                if temperature is None and hasattr(self, 'temperature'):
                    temperature = self.temperature
                
                # Capture the prompt
                capture_data = {
                    'prompt': prompt,
                    'system_prompt': system_prompt,
                    'provider': provider or self_llm.provider,
                    'model': model or self_llm.model,
                    'temperature': temperature,
                    'timestamp': datetime.now().isoformat()
                }
                self.captured_prompts.append(capture_data)
                
                # Call original method
                result = self._original_llm_query(
                    self_llm, 
                    prompt, 
                    provider, 
                    system_prompt, 
                    model, 
                    json_response, 
                    max_tokens, 
                    temperature
                )
                
                # Capture the response
                capture_data = {
                    'response': result,
                    'timestamp': datetime.now().isoformat()
                }
                self.captured_responses.append(capture_data)
                
                return result
                
            # Replace the method
            LLMClient.query = captured_query
    
    def _restore_llm_client(self):
        """Restore original LLM client functionality."""
        if hasattr(self, '_original_llm_query'):
            LLMClient.query = self._original_llm_query
            
    def _run_interactive_mode(self):
        """
        Run interactive mode by prompting the user for inputs and parameters.
        """
        print(f"\n{Fore.CYAN}=== Interactive Mode ===={Style.RESET_ALL}")
        print(f"Current configuration:")
        print(f"  Agent: {Fore.YELLOW}{self.agent_name}{Style.RESET_ALL}")
        print(f"  Symbol: {Fore.YELLOW}{self.symbol}{Style.RESET_ALL}")
        print(f"  Interval: {Fore.YELLOW}{self.interval}{Style.RESET_ALL}")
        print(f"  Using mock data: {Fore.YELLOW}{self.use_mock_data}{Style.RESET_ALL}")
        print(f"  Temperature: {Fore.YELLOW}{self.temperature}{Style.RESET_ALL}")
        print("")
        
        # Ask for symbol modification
        new_symbol = input(f"Enter a new symbol (or press Enter to keep {self.symbol}): ")
        if new_symbol.strip():
            self.symbol = new_symbol.strip()
            print(f"Symbol updated to: {Fore.GREEN}{self.symbol}{Style.RESET_ALL}")
        
        # Ask for interval modification
        new_interval = input(f"Enter a new interval (or press Enter to keep {self.interval}): ")
        if new_interval.strip():
            self.interval = new_interval.strip()
            print(f"Interval updated to: {Fore.GREEN}{self.interval}{Style.RESET_ALL}")
            
        # Ask about using mock data
        use_mock_response = input(f"Use mock data? (y/n, press Enter to keep {self.use_mock_data}): ").lower()
        if use_mock_response in ['y', 'yes']:
            self.use_mock_data = True
            print(f"Using {Fore.GREEN}mock data{Style.RESET_ALL}")
        elif use_mock_response in ['n', 'no']:
            self.use_mock_data = False
            print(f"Using {Fore.GREEN}real data{Style.RESET_ALL}")
            
        # Ask about temperature for LLM
        try:
            temp_response = input(f"Enter temperature (0-1, press Enter to keep {self.temperature}): ")
            if temp_response.strip():
                self.temperature = float(temp_response.strip())
                print(f"Temperature updated to: {Fore.GREEN}{self.temperature}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid temperature, keeping {self.temperature}{Style.RESET_ALL}")
        
        # Need to reinitialize data provider if settings changed
        if new_symbol.strip() or use_mock_response in ['y', 'yes', 'n', 'no']:
            print(f"\n{Fore.CYAN}Reinitializing data provider with new settings...{Style.RESET_ALL}")
            self._init_data_provider()
            
        print(f"\n{Fore.GREEN}Interactive configuration complete{Style.RESET_ALL}")
        print(f"Running test with: Symbol={self.symbol}, Interval={self.interval}, MockData={self.use_mock_data}, Temp={self.temperature}")
        print("")
    
    def _create_agent(self) -> BaseAnalystAgent:
        """
        Create an instance of the specified agent with the configuration.
        
        Returns:
            Initialized agent instance
        """
        # Base parameters for different agent types
        if self.agent_name == 'DecisionAgent':
            # Decision agent has a unique initialization
            mock_analyst_results = {
                'technical_analysis': {
                    'signal': 'HOLD',
                    'confidence': 70,
                    'reasoning': 'Mock technical analysis for testing',
                    'data': {'indicators': {'rsi': 50, 'macd': 0.1}}
                },
                'sentiment_analysis': {
                    'signal': 'BUY',
                    'confidence': 65,
                    'reasoning': 'Mock sentiment analysis for testing',
                    'data': {'sentiment_score': 0.7}
                },
                'sentiment_aggregator_analysis': {
                    'signal': 'NEUTRAL',
                    'confidence': 60,
                    'reasoning': 'Mock sentiment aggregator analysis for testing',
                    'data': {'social_sentiment': 0.5, 'news_sentiment': 0.6}
                },
                'liquidity_analysis': {
                    'signal': 'HOLD',
                    'confidence': 60,
                    'reasoning': 'Mock liquidity analysis for testing',
                    'data': {'support_level': 49000, 'resistance_level': 51000}
                },
                'open_interest_analysis': {
                    'signal': 'SELL',
                    'confidence': 55,
                    'reasoning': 'Mock open interest analysis for testing',
                    'data': {'open_interest_change': -0.05}
                },
                'funding_rate_analysis': {
                    'signal': 'SELL',
                    'confidence': 50,
                    'reasoning': 'Mock funding rate analysis for testing',
                    'data': {'funding_rate': -0.01}
                }
            }
            
            # Updated params for DecisionAgent initialization - it only takes allow_conflict_state
            agent_params = {
                'allow_conflict_state': True
            }
            
            # Store the mock analyst results to be set after initialization
            self.mock_analyst_results = self.data_override.get('mock_analyst_results', mock_analyst_results)
        elif self.agent_name == 'TradePlanAgent':
            # TradePlanAgent has a unique initialization
            agent_params = {
                'data_provider': self.data_provider,
                'symbol': self.symbol,
                'interval': self.interval,
                'mock_analyst_results': self.data_override.get('mock_analyst_results', None),
                'use_context_manager': True,
                'log_conflict_traces': self.log_conflict_traces
            }
            
            # Use the factory function if available
            if create_trade_plan_agent:
                return create_trade_plan_agent(**agent_params)
        elif self.agent_name == 'PortfolioManagerAgent':
            # Portfolio manager has a unique initialization
            agent_params = {
                'data_provider': self.data_provider,
                'config': {
                    'max_portfolio_exposure': 0.75,  # 75% maximum total exposure
                    'max_position_size': 0.2,        # 20% maximum per position
                    'risk_limit_per_trade': 0.05     # 5% risk per trade
                },
                'mock_portfolio': self.data_override.get('mock_portfolio', {})
            }
        elif self.agent_name == 'ToneAgent':
            # ToneAgent has a simple initialization
            agent_params = {}  # No specific parameters needed for ToneAgent
        elif self.agent_name == 'TechnicalAnalystAgent':
            # TechnicalAnalystAgent takes data_fetcher instead of data_provider
            agent_params = {
                'data_fetcher': self.data_provider,
                'config': {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'use_cache': False
                }
            }
        elif self.agent_name in ['SentimentAnalystAgent', 'SentimentAggregatorAgent']:
            # These agents also use data_fetcher and have temperature settings
            agent_params = {
                'data_fetcher': self.data_provider,
                'config': {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'use_cache': False,
                    'temperature': self.temperature
                }
            }
        else:
            # Standard parameters for other analyst agents
            agent_params = {
                'data_fetcher': self.data_provider,
                'config': {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'use_cache': False
                }
            }
        
        # Override with any data_override params for this specific agent
        if self.data_override.get(self.agent_name, {}):
            if 'config' in agent_params:
                agent_params['config'].update(self.data_override.get(self.agent_name, {}))
            else:
                agent_params.update(self.data_override.get(self.agent_name, {}))
        
        # Create and return the agent
        return self.agent_class(**agent_params)
    
    def run_test(self):
        """
        Run the test for the selected agent.
        
        In interactive mode, it prompts the user for inputs before running the test.
        
        Returns:
            Dictionary with test results
        """
        # Handle interactive mode if enabled
        if self.interactive:
            self._run_interactive_mode()
        if self.full_cycle and self.agent_name != 'DecisionAgent':
            logger.warning(f"{Fore.YELLOW}Warning: Full decision cycle mode is enabled but agent is not DecisionAgent. "
                         f"Switching target agent to DecisionAgent.{Style.RESET_ALL}")
            # Save the original agent for reference
            self.original_agent_name = self.agent_name
            self.agent_name = 'DecisionAgent'
            self.agent_class = AVAILABLE_AGENTS['DecisionAgent']
            
        # Special handling for full trade cycle test
        if self.trade_cycle:
            return self.run_full_trade_cycle_test()
            
        # Banner
        banner_width = 80
        centered_text = f" Testing {self.agent_name} for {self.symbol} ({self.interval}) "
        padding = "=" * ((banner_width - len(centered_text)) // 2)
        banner = f"\n{padding}{centered_text}{padding}"
        if len(banner) < banner_width:
            banner += "="  # Ensure the banner is exactly banner_width characters
        
        logger.info(banner)
        
        # Create agent instance
        agent = self._create_agent()
        
        # Get current price for reference
        try:
            current_price = self.data_provider.get_current_price(self.symbol)
            logger.info(f"{Fore.WHITE}Current price of {self.symbol}: ${current_price:.2f}{Style.RESET_ALL}")
        except Exception as e:
            logger.warning(f"{Fore.YELLOW}Could not get current price: {str(e)}{Style.RESET_ALL}")
            current_price = None
        
        # Track execution time
        start_time = time.time()
        
        # For decision agent, we need to run the full analysis
        if self.agent_name == 'DecisionAgent' and self.full_cycle:
            result = self.run_full_decision_cycle(agent)
        elif self.agent_name == 'TradePlanAgent':
            result = self.run_trade_plan_test(agent)
        else:
            # Run standard analysis for analyst agents
            logger.info(f"{Fore.CYAN}Running {self.agent_name} analysis...{Style.RESET_ALL}")
            
            # Prepare default parameters
            params = {
                "symbol": self.symbol,
                "interval": self.interval
            }
            
            # Add any overrides
            params.update(self.data_override.get('analyze_params', {}))
            
            # Execute the analysis
            try:
                analysis_result = agent.analyze(**params)
                execution_time = time.time() - start_time
                
                result = {
                    'status': 'success',
                    'execution_time': execution_time,
                    'result': analysis_result,
                    'parameters': params
                }
            except Exception as e:
                logger.error(f"{Fore.RED}Error running analysis: {str(e)}{Style.RESET_ALL}")
                import traceback
                logger.error(traceback.format_exc())
                
                result = {
                    'status': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'execution_time': time.time() - start_time,
                    'parameters': params
                }
        
        # Execution time
        execution_time = result.get('execution_time', time.time() - start_time)
        logger.info(f"\n{Fore.WHITE}Execution time: {execution_time:.2f} seconds{Style.RESET_ALL}")
        
        # Add to test results history
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'agent': self.agent_name,
            'symbol': self.symbol,
            'interval': self.interval,
            'execution_time': execution_time,
            'result': result.get('result', {}),
            'status': result.get('status', 'unknown')
        })
        
        # Show analysis result summary
        self.display_result_summary(result, banner_width)
        
        # Add agent tone if ToneAgent is available
        if self.tone_agent and 'result' in result and isinstance(result['result'], dict):
            self.add_agent_tones(result)
            
        return result
        
    def run_full_decision_cycle(self, decision_agent):
        """
        Run a full analysis cycle with all available analyst agents feeding the decision agent.
        
        Args:
            decision_agent: The DecisionAgent instance
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"{Fore.CYAN}Running FULL DECISION CYCLE TEST with all available agents{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}Target symbol: {self.symbol}, Interval: {self.interval}{Style.RESET_ALL}")
        
        # Check if we should run with a subset of agents
        target_agent = getattr(self, 'original_agent_name', None)
        
        all_results = {}
        analyst_results = {}
        
        # Track execution time
        start_time = time.time()
        
        # Initialize all available analyst agents and run their analysis
        analyst_agents = {
            'technical_analysis': TechnicalAnalystAgent if TechnicalAnalystAgent else None,
            'sentiment_analysis': SentimentAnalystAgent if SentimentAnalystAgent else None,
            'sentiment_aggregator_analysis': SentimentAggregatorAgent if SentimentAggregatorAgent else None,
            'liquidity_analysis': LiquidityAnalystAgent if LiquidityAnalystAgent else None,
            'open_interest_analysis': OpenInterestAnalystAgent if OpenInterestAnalystAgent else None,
            'funding_rate_analysis': FundingRateAnalystAgent if FundingRateAnalystAgent else None
        }
        
        # Filter if testing a specific agent
        if target_agent and target_agent != 'DecisionAgent' and target_agent in AVAILABLE_AGENTS:
            # Map the agent class name to the analysis key
            agent_key_map = {
                'TechnicalAnalystAgent': 'technical_analysis',
                'SentimentAnalystAgent': 'sentiment_analysis',
                'SentimentAggregatorAgent': 'sentiment_aggregator_analysis',
                'LiquidityAnalystAgent': 'liquidity_analysis',
                'OpenInterestAnalystAgent': 'open_interest_analysis',
                'FundingRateAnalystAgent': 'funding_rate_analysis'
            }
            
            if target_agent in agent_key_map:
                # Only include the target agent and mock the rest
                target_key = agent_key_map[target_agent]
                logger.info(f"{Fore.YELLOW}Running focused test with only {target_agent} providing real analysis{Style.RESET_ALL}")
                
                # Create mock results for all other agents
                mock_results = self.mock_analyst_results
                
                # Run the target agent for real
                for key, agent_class in analyst_agents.items():
                    if key == target_key and agent_class:
                        logger.info(f"{Fore.CYAN}Running analysis for {key.replace('_', ' ').title()}{Style.RESET_ALL}")
                        agent = agent_class(
                            data_provider=self.data_provider,
                            symbol=self.symbol,
                            interval=self.interval,
                            use_cache=False
                        )
                        try:
                            result = agent.analyze(symbol=self.symbol, interval=self.interval)
                            analyst_results[key] = result
                            all_results[key] = {
                                'status': 'success',
                                'execution_time': 0,
                                'result': result
                            }
                        except Exception as e:
                            logger.error(f"{Fore.RED}Error running {key} analysis: {str(e)}{Style.RESET_ALL}")
                            analyst_results[key] = mock_results.get(key, {})
                            all_results[key] = {
                                'status': 'error',
                                'error': str(e)
                            }
                    else:
                        # Use mock results for other agents
                        analyst_results[key] = mock_results.get(key, {})
                        all_results[key] = {
                            'status': 'mocked',
                            'result': mock_results.get(key, {})
                        }
            else:
                logger.warning(f"{Fore.YELLOW}Target agent {target_agent} not found in agent map, running full cycle{Style.RESET_ALL}")
                # Run all agents normally
                for key, agent_class in analyst_agents.items():
                    if agent_class:
                        logger.info(f"{Fore.CYAN}Running analysis for {key.replace('_', ' ').title()}{Style.RESET_ALL}")
                        agent = agent_class(
                            data_provider=self.data_provider,
                            symbol=self.symbol,
                            interval=self.interval,
                            use_cache=False
                        )
                        try:
                            result = agent.analyze(symbol=self.symbol, interval=self.interval)
                            analyst_results[key] = result
                            all_results[key] = {
                                'status': 'success',
                                'execution_time': 0,
                                'result': result
                            }
                        except Exception as e:
                            logger.error(f"{Fore.RED}Error running {key} analysis: {str(e)}{Style.RESET_ALL}")
                            all_results[key] = {
                                'status': 'error',
                                'error': str(e)
                            }
                    else:
                        logger.warning(f"{Fore.YELLOW}{key.replace('_', ' ').title()} agent not available{Style.RESET_ALL}")
        else:
            # Run all available agents
            for key, agent_class in analyst_agents.items():
                if agent_class:
                    logger.info(f"{Fore.CYAN}Running analysis for {key.replace('_', ' ').title()}{Style.RESET_ALL}")
                    agent = agent_class(
                        data_provider=self.data_provider,
                        symbol=self.symbol,
                        interval=self.interval,
                        use_cache=False
                    )
                    try:
                        result = agent.analyze(symbol=self.symbol, interval=self.interval)
                        analyst_results[key] = result
                        all_results[key] = {
                            'status': 'success',
                            'execution_time': 0,
                            'result': result
                        }
                    except Exception as e:
                        logger.error(f"{Fore.RED}Error running {key} analysis: {str(e)}{Style.RESET_ALL}")
                        all_results[key] = {
                            'status': 'error',
                            'error': str(e)
                        }
                else:
                    logger.warning(f"{Fore.YELLOW}{key.replace('_', ' ').title()} agent not available{Style.RESET_ALL}")
        
        # Now run the decision agent with the analysis results
        logger.info(f"{Fore.CYAN}Running final decision analysis with DecisionAgent{Style.RESET_ALL}")
        
        try:
            # Combine results for the make_decision method
            analysis_params = {
                "agent_analyses": analyst_results,
                "symbol": self.symbol,
                "interval": self.interval
            }
            
            decision_result = decision_agent.make_decision(**analysis_params)
            
            # Add to all results
            all_results['decision'] = {
                'status': 'success',
                'execution_time': time.time() - start_time,
                'result': decision_result
            }
            
            # Create final result
            result = {
                'status': 'success',
                'execution_time': time.time() - start_time,
                'result': {
                    'decision': decision_result,
                    'analyses': analyst_results
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"{Fore.RED}Error running decision analysis: {str(e)}{Style.RESET_ALL}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Create error result
            result = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'execution_time': time.time() - start_time,
                'result': {
                    'analyses': analyst_results
                }
            }
            
            return result
    
    def run_trade_plan_test(self, trade_plan_agent):
        """
        Run a test with TradePlanAgent.
        
        Args:
            trade_plan_agent: The TradePlanAgent instance
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"{Fore.CYAN}Running TradePlanAgent analysis for {self.symbol} ({self.interval})...{Style.RESET_ALL}")
        
        # First run a decision cycle to get analyst results
        decision_agent = DecisionAgent(
            allow_conflict_state=True
        )
        
        decision_result = self.run_full_decision_cycle(decision_agent)
        
        # Check if decision was successful
        if decision_result['status'] != 'success':
            logger.error(f"{Fore.RED}Decision cycle failed, cannot run TradePlanAgent.{Style.RESET_ALL}")
            return decision_result
        
        # Extract the decision and analyst results
        final_decision = decision_result['result']['decision']
        analyst_results = decision_result['result']['analyses']
        
        # Run TradePlanAgent
        logger.info(f"{Fore.CYAN}Running trade plan generation with TradePlanAgent{Style.RESET_ALL}")
        
        start_time = time.time()
        try:
            # Prepare the input parameters for TradePlanAgent
            plan_params = {
                "decision": final_decision,
                "analyst_results": analyst_results,
                "symbol": self.symbol,
                "interval": self.interval
            }
            
            # Add optional parameters if configured
            if self.data_override.get('mock_portfolio', None):
                plan_params["portfolio"] = self.data_override.get('mock_portfolio')
                
            trade_plan = trade_plan_agent.generate_trade_plan(**plan_params)
            
            # Create full result
            result = {
                'status': 'success',
                'execution_time': time.time() - start_time,
                'result': {
                    'trade_plan': trade_plan,
                    'decision': final_decision,
                    'analyses': analyst_results
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"{Fore.RED}Error generating trade plan: {str(e)}{Style.RESET_ALL}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Create error result
            result = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'execution_time': time.time() - start_time,
                'result': {
                    'decision': final_decision,
                    'analyses': analyst_results
                }
            }
            
            return result
    
    def run_full_trade_cycle_test(self):
        """
        Run a complete trade cycle test with all agents:
        - All analyst agents
        - DecisionAgent
        - TradePlanAgent
        - PortfolioManagerAgent (if requested)
        
        Returns:
            Dictionary with test results
        """
        logger.info(f"{Fore.CYAN}Running FULL TRADE CYCLE TEST with all agents{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}Target symbol: {self.symbol}, Interval: {self.interval}{Style.RESET_ALL}")
        
        # Track execution time
        start_time = time.time()
        
        # 1. Run analyst agents first
        analyst_agents = {
            'technical_analysis': TechnicalAnalystAgent if TechnicalAnalystAgent else None,
            'sentiment_analysis': SentimentAnalystAgent if SentimentAnalystAgent else None,
            'sentiment_aggregator_analysis': SentimentAggregatorAgent if SentimentAggregatorAgent else None,
            'liquidity_analysis': LiquidityAnalystAgent if LiquidityAnalystAgent else None,
            'open_interest_analysis': OpenInterestAnalystAgent if OpenInterestAnalystAgent else None,
            'funding_rate_analysis': FundingRateAnalystAgent if FundingRateAnalystAgent else None
        }
        
        analyst_results = {}
        
        for key, agent_class in analyst_agents.items():
            if agent_class:
                logger.info(f"{Fore.CYAN}Running analysis for {key.replace('_', ' ').title()}{Style.RESET_ALL}")
                # Different initialization parameters based on agent type
                if key == 'technical_analysis':
                    agent = agent_class(
                        data_fetcher=self.data_provider,
                        config={"symbol": self.symbol, "interval": self.interval, "use_cache": False}
                    )
                elif key in ['sentiment_analysis', 'sentiment_aggregator_analysis']:
                    agent = agent_class(
                        data_fetcher=self.data_provider,
                        config={"symbol": self.symbol, "interval": self.interval, 
                                "use_cache": False, "temperature": self.temperature}
                    )
                else:
                    agent = agent_class(
                        data_fetcher=self.data_provider,
                        config={"symbol": self.symbol, "interval": self.interval, "use_cache": False}
                    )
                try:
                    result = agent.analyze(symbol=self.symbol, interval=self.interval)
                    analyst_results[key] = result
                except Exception as e:
                    logger.error(f"{Fore.RED}Error running {key} analysis: {str(e)}{Style.RESET_ALL}")
            else:
                logger.warning(f"{Fore.YELLOW}{key.replace('_', ' ').title()} agent not available{Style.RESET_ALL}")
        
        # Create a portfolio manager if needed
        # Simplified portfolio for testing
        portfolio = {
            'total_value': 100000.0,
            'base_currency': 'USDT',
            'positions': {
                'BTC/USDT': {
                    'amount': 0.5,
                    'entry_price': 48000.0,
                    'current_price': self.data_provider.get_current_price(self.symbol)
                }
            },
            'open_positions_count': 1,
            'total_exposure_pct': 0.25
        }
        
        # 2. Run decision agent
        logger.info(f"{Fore.CYAN}Running DecisionAgent analysis{Style.RESET_ALL}")
        # DecisionAgent has a simpler initialization
        decision_agent = DecisionAgent(allow_conflict_state=True)
        
        try:
            # DecisionAgent uses make_decision instead of analyze
            decision = decision_agent.make_decision(
                agent_analyses=analyst_results,
                symbol=self.symbol,
                interval=self.interval
            )
        except Exception as e:
            logger.error(f"{Fore.RED}Error running decision analysis: {str(e)}{Style.RESET_ALL}")
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': time.time() - start_time,
                'result': {
                    'analyses': analyst_results
                }
            }
        
        # 3. Run trade plan agent
        logger.info(f"{Fore.CYAN}Running TradePlanAgent analysis{Style.RESET_ALL}")
        if TradePlanAgent and create_trade_plan_agent:
            # TradePlanAgent uses a factory function with config
            trade_plan_agent = create_trade_plan_agent(
                config={
                    "data_fetcher": self.data_provider,
                    "symbol": self.symbol,
                    "interval": self.interval
                }
            )
            
            try:
                # Pass market_data parameter properly
                market_data = {
                    "symbol": self.symbol,
                    "interval": self.interval,
                    "current_price": self.data_provider.get_current_price(self.symbol)
                }
                trade_plan = trade_plan_agent.generate_trade_plan(
                    decision=decision,
                    market_data=market_data,
                    portfolio_data=portfolio
                )
            except Exception as e:
                logger.error(f"{Fore.RED}Error generating trade plan: {str(e)}{Style.RESET_ALL}")
                return {
                    'status': 'error',
                    'error': str(e),
                    'execution_time': time.time() - start_time,
                    'result': {
                        'decision': decision,
                        'analyses': analyst_results
                    }
                }
        else:
            logger.warning(f"{Fore.YELLOW}TradePlanAgent not available. Skipping trade plan generation.{Style.RESET_ALL}")
            trade_plan = {
                'signal': decision.get('signal', 'UNKNOWN'),
                'confidence': decision.get('confidence', 0),
                'position_size': 0.1,  # Default position size
                'status': 'mocked'
            }
            
        # 4. Generate ToneAgent summary if available
        tone_summary = None
        if self.tone_agent:
            logger.info(f"{Fore.CYAN}Generating styled agent voices with ToneAgent{Style.RESET_ALL}")
            try:
                tone_summary = self.tone_agent.generate_summary(
                    analysis_results=analyst_results,
                    final_decision=decision,
                    symbol=self.symbol,
                    interval=self.interval
                )
            except Exception as e:
                logger.error(f"{Fore.RED}Error generating tone summary: {str(e)}{Style.RESET_ALL}")
        
        # Create the final result
        result = {
            'status': 'success',
            'execution_time': time.time() - start_time,
            'result': {
                'trade_plan': trade_plan,
                'decision': decision,
                'analyses': analyst_results,
                'portfolio_summary': portfolio,
                'tone_summary': tone_summary
            }
        }
        
        # Save result as JSON if requested
        if self.trade_log:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"trade_cycle_test_{self.symbol.replace('/', '')}_{self.interval}_{timestamp}.json"
                
                with open(log_filename, 'w') as f:
                    json.dump(result, f, indent=2)
                    
                logger.info(f"{Fore.GREEN}Trade cycle test results saved to {log_filename}{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}Error saving trade log: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def display_result_summary(self, result, banner_width=80):
        """
        Display a summary of the test result.
        
        Args:
            result: Test result dictionary
            banner_width: Width of the banner
        """
        if result.get('status') == 'error':
            print(f"\n{Fore.RED}## Error occurred! ##")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if self.explain and 'traceback' in result:
                print("\nTraceback:")
                print(result['traceback'])
            print(Style.RESET_ALL)
            return
        
        print("="*banner_width)
        
        # Display individual agent results
        print(f"\n{Fore.CYAN}## Individual Agent Results ##")
        
        analyses = result['result'].get('analyses', {})
        for agent_name, analysis in analyses.items():
            # Skip if analysis is None or not a dict
            if not analysis or not isinstance(analysis, dict):
                continue
                
            # Extract key data using multiple possible field names for better compatibility
            agent_signal = analysis.get('signal') or analysis.get('final_signal') or analysis.get('action') or analysis.get('pair') or 'UNKNOWN'
            agent_confidence = analysis.get('confidence', 0)
            
            # Extract reasoning with improved logic
            agent_reasoning = analysis.get('reasoning', None)
            if not agent_reasoning or agent_reasoning == 'No reasoning provided':
                agent_reasoning = analysis.get('reason', None)
            
            # If we still don't have reasoning, generate a default one based on the signal
            if not agent_reasoning or agent_reasoning == 'No reasoning provided':
                signal_desc = {
                    'BUY': f"Bullish signals detected for {self.symbol}",
                    'SELL': f"Bearish signals detected for {self.symbol}",
                    'NEUTRAL': f"Neutral market conditions for {self.symbol}",
                    'HOLD': f"Current position maintained for {self.symbol}"
                }
                agent_reasoning = signal_desc.get(agent_signal, f"Analysis completed for {self.symbol}")
                
            # Color-code based on signal
            if agent_signal == 'BUY':
                agent_signal_color = Fore.GREEN
            elif agent_signal == 'SELL':
                agent_signal_color = Fore.RED
            elif agent_signal == 'CONFLICTED':
                agent_signal_color = Fore.MAGENTA  # Use magenta for CONFLICTED signals
            else:  # HOLD, NEUTRAL, or others
                agent_signal_color = Fore.YELLOW
                
            # Confidence color
            if agent_confidence >= 80:
                agent_confidence_color = Fore.GREEN
            elif agent_confidence >= 60:
                agent_confidence_color = Fore.YELLOW
            else:
                agent_confidence_color = Fore.RED
                
            print(f"\n{Fore.WHITE}{agent_name.replace('_', ' ').title()}{Style.RESET_ALL}")
            print(f"  Signal:     {agent_signal_color}{agent_signal}{Style.RESET_ALL}")
            print(f"  Confidence: {agent_confidence_color}{agent_confidence}%{Style.RESET_ALL}")
            
            # Check if we have a styled tone for this agent
            agent_tone = self.get_agent_tone_for_display(agent_name)
            if agent_tone:
                print(f"  {Fore.CYAN}Voice:      \"{agent_tone}\"{Style.RESET_ALL}")
            else:
                # Truncate reasoning if it's too long
                if len(agent_reasoning) > 100:
                    print(f"  Reasoning:  {agent_reasoning[:100]}...")
                else:
                    print(f"  Reasoning:  {agent_reasoning}")
                
        # Display portfolio summary if available
        if 'portfolio_summary' in result:
            print("\n" + "="*80)
            print(f"{Fore.CYAN}## Portfolio Manager Summary ##")
            
            portfolio_summary = result['portfolio_summary']
            
            # Format portfolio metrics with colors
            total_value = portfolio_summary.get('total_value', 0)
            if isinstance(total_value, (int, float)):
                total_value = f"{Fore.GREEN}${float(total_value):.2f}{Style.RESET_ALL}"
            print(f"Portfolio Value:   {total_value}")
            
            exposure = portfolio_summary.get('total_exposure_pct', 0)
            if isinstance(exposure, (int, float)):
                if exposure > 0.5:  # High exposure
                    exposure = f"{Fore.RED}{float(exposure) * 100:.2f}%{Style.RESET_ALL}"
                else:
                    exposure = f"{Fore.GREEN}{float(exposure) * 100:.2f}%{Style.RESET_ALL}"
            print(f"Total Exposure:    {exposure}")
            
            positions_count = portfolio_summary.get('open_positions_count', 0)
            print(f"Open Positions:    {positions_count}")
            
            risk_per_trade = portfolio_summary.get('risk_limit_per_trade', 0)
            if isinstance(risk_per_trade, (int, float)):
                risk_per_trade = f"{float(risk_per_trade) * 100:.2f}%"
            print(f"Risk Per Trade:    {risk_per_trade}")
        
        # Display final decision if available
        decision = result['result'].get('decision', {})
        if decision:
            print("\n" + "="*80)
            print(f"{Fore.CYAN}## Final Decision ##")
            
            # Extract decision data
            decision_signal = decision.get('signal', 'UNKNOWN')
            decision_confidence = decision.get('confidence', 0)
            
            # Color coding
            if decision_signal == 'BUY':
                decision_signal_color = Fore.GREEN
            elif decision_signal == 'SELL':
                decision_signal_color = Fore.RED
            elif decision_signal == 'CONFLICTED':
                decision_signal_color = Fore.MAGENTA
            else:  # HOLD, NEUTRAL
                decision_signal_color = Fore.YELLOW
                
            if decision_confidence >= 80:
                decision_confidence_color = Fore.GREEN
            elif decision_confidence >= 60:
                decision_confidence_color = Fore.YELLOW
            else:
                decision_confidence_color = Fore.RED
                
            print(f"Signal:     {decision_signal_color}{decision_signal}{Style.RESET_ALL}")
            print(f"Confidence: {decision_confidence_color}{decision_confidence}%{Style.RESET_ALL}")
            
            # Display conflict score if available
            conflict_score = decision.get('conflict_score', 0)
            if conflict_score > 0:
                if conflict_score >= 50:
                    conflict_color = Fore.RED
                elif conflict_score >= 25:
                    conflict_color = Fore.YELLOW
                else:
                    conflict_color = Fore.GREEN
                    
                print(f"Conflict:   {conflict_color}{conflict_score}{Style.RESET_ALL}")
            
            # Display contributing agents
            contributing_agents = decision.get('contributing_agents', [])
            if contributing_agents:
                print(f"Based on:   {', '.join(contributing_agents)}")
                
            # Display reasoning if available
            reasoning = decision.get('reasoning', '')
            if reasoning:
                print(f"Reasoning:  {reasoning}")
                
        # Display trade plan if available
        trade_plan = result['result'].get('trade_plan', {})
        if trade_plan:
            print("\n" + "="*80)
            print(f"{Fore.CYAN}## Trade Plan ##")
            
            # Extract trade plan data
            plan_signal = trade_plan.get('signal', 'UNKNOWN')
            plan_confidence = trade_plan.get('confidence', 0)
            position_size = trade_plan.get('position_size', 0.0)
            
            # Color coding
            if plan_signal == 'BUY':
                plan_signal_color = Fore.GREEN
            elif plan_signal == 'SELL':
                plan_signal_color = Fore.RED
            elif plan_signal == 'CONFLICTED':
                plan_signal_color = Fore.MAGENTA
            else:  # HOLD, NEUTRAL
                plan_signal_color = Fore.YELLOW
                
            print(f"Signal:       {plan_signal_color}{plan_signal}{Style.RESET_ALL}")
            
            # Position size color
            if position_size >= 0.5:
                position_size_color = Fore.RED  # Large position
            elif position_size >= 0.2:
                position_size_color = Fore.YELLOW  # Medium position
            else:
                position_size_color = Fore.GREEN  # Small position
                
            # Format as percentage
            position_size_pct = position_size * 100
            print(f"Position:     {position_size_color}{position_size_pct:.2f}%{Style.RESET_ALL}")
            
            # Display other fields if available
            if 'entry_price' in trade_plan:
                entry_price = trade_plan.get('entry_price', 0)
                current_price = self.data_provider.get_current_price(self.symbol)
                if current_price and entry_price:
                    # Determine if entry price is favorable
                    if (plan_signal == 'BUY' and entry_price <= current_price) or \
                       (plan_signal == 'SELL' and entry_price >= current_price):
                        price_color = Fore.GREEN
                    else:
                        price_color = Fore.YELLOW
                        
                    print(f"Entry Price:  {price_color}${entry_price:.2f}{Style.RESET_ALL}")
                    
            if 'stop_loss' in trade_plan:
                stop_loss = trade_plan.get('stop_loss', 0)
                if stop_loss:
                    print(f"Stop Loss:    ${stop_loss:.2f}")
                    
            if 'take_profit' in trade_plan:
                take_profit = trade_plan.get('take_profit', 0)
                if take_profit:
                    print(f"Take Profit:  ${take_profit:.2f}")
                    
            # Display reason summary if available
            reason_summary = trade_plan.get('reason_summary', '')
            if reason_summary:
                print(f"Reason:       {reason_summary}")
                
            # Display trade strategy if available
            trade_strategy = trade_plan.get('strategy', '')
            if trade_strategy:
                print(f"Strategy:     {trade_strategy}")
                
            # Display trade type if available
            trade_type = trade_plan.get('trade_type', '')
            if trade_type:
                print(f"Type:         {trade_type}")
                
            # Display trade timeframe if available
            time_horizon = trade_plan.get('time_horizon', '')
            if time_horizon:
                print(f"Time Horizon: {time_horizon}")
                
        # Display tone agent summary if available
        tone_summary = result['result'].get('tone_summary', None)
        if tone_summary:
            print("\n" + "="*80)
            print(f"{Fore.CYAN}## Tone Agent Summary ##")
            
            system_summary = tone_summary.get('system_summary', 'No summary available')
            mood = tone_summary.get('mood', 'neutral')
            
            # Format mood with color
            if mood == 'bullish' or mood == 'euphoric':
                mood_color = Fore.GREEN
            elif mood == 'bearish':
                mood_color = Fore.RED
            elif mood == 'conflicted':
                mood_color = Fore.MAGENTA
            elif mood == 'cautious':
                mood_color = Fore.YELLOW
            else:
                mood_color = Fore.WHITE
                
            print(f"Summary: {system_summary}")
            print(f"Mood:    {mood_color}{mood}{Style.RESET_ALL}")
            
        print("\n" + "="*banner_width)
    
    def add_agent_tones(self, result):
        """
        Add agent tones to the result data using the ToneAgent.
        
        Args:
            result: Test result dictionary to update
        """
        try:
            # Skip if we don't have the necessary components
            if not self.tone_agent:
                logger.warning(f"{Fore.YELLOW}ToneAgent not available. Skipping tone generation.{Style.RESET_ALL}")
                return
                
            if 'result' not in result or not isinstance(result['result'], dict):
                logger.warning(f"{Fore.YELLOW}Result is not in expected format for tone generation.{Style.RESET_ALL}")
                return
            
            # Check data structure type - could be full cycle results or standard agent results
            # For full cycle, we check for all_analyses
            if self.full_cycle and 'all_analyses' in result['result']:
                logger.info(f"{Fore.CYAN}Processing full cycle results for ToneAgent...{Style.RESET_ALL}")
                analyses = result['result']['all_analyses']
                decision = result['result']
            # For standard results, we check for analyses and decision fields
            else:
                logger.info(f"{Fore.CYAN}Processing standard agent results for ToneAgent...{Style.RESET_ALL}")
                analyses = result['result'].get('analyses', {})
                decision = result['result'].get('decision', {})
            
            if not analyses:
                logger.warning(f"{Fore.YELLOW}No analyses found for ToneAgent to process.{Style.RESET_ALL}")
                return
                
            if not decision:
                logger.warning(f"{Fore.YELLOW}No decision data found for ToneAgent to process.{Style.RESET_ALL}")
                return
                
            # Log what we're doing
            logger.info(f"{Fore.CYAN}Generating agent voices using ToneAgent...{Style.RESET_ALL}")
            
            # Try to generate the tone summary with different possible method signatures
            try:
                # First try with the standard 4-parameter signature
                tone_summary = self.tone_agent.generate_summary(
                    analysis_results=analyses,
                    final_decision=decision,
                    symbol=self.symbol,
                    interval=self.interval
                )
            except TypeError as e:
                # If that fails, try with just the analysis_results and final_decision
                logger.warning(f"{Fore.YELLOW}Standard ToneAgent signature failed, trying alternate: {str(e)}{Style.RESET_ALL}")
                tone_summary = self.tone_agent.generate_summary(
                    analysis_results=analyses,
                    final_decision=decision
                )
            
            # Add to result
            result['result']['tone_summary'] = tone_summary
            
            # Store agent tones for display
            self.agent_tones = tone_summary.get('agent_comments', {})
            
            # Log the result
            logger.info(f"{Fore.GREEN}Successfully generated {len(self.agent_tones)} agent voices{Style.RESET_ALL}")
            
            # Print a sample of the agent voices and enable display if explain is set
            agent_names = list(self.agent_tones.keys())
            if agent_names:
                sample_agent = agent_names[0]
                sample_voice = self.agent_tones[sample_agent]
                logger.info(f"{Fore.CYAN}Sample agent voice - {sample_agent}: \"{sample_voice}\"{Style.RESET_ALL}")
                
                # If explain is enabled, show all the voices
                if self.explain:
                    self.display_agent_tones(tone_summary)
            
        except Exception as e:
            logger.error(f"{Fore.RED}Error adding agent tones: {str(e)}{Style.RESET_ALL}")
            import traceback
            logger.error(traceback.format_exc())
            
    def display_agent_tones(self, tone_summary):
        """
        Display agent tones from the summary.
        
        Args:
            tone_summary: Dictionary containing agent_comments and system_summary
        """
        if not tone_summary:
            logger.warning(f"{Fore.YELLOW}No tone summary available{Style.RESET_ALL}")
            return
            
        agent_comments = tone_summary.get('agent_comments', {})
        system_summary = tone_summary.get('system_summary', '')
        
        if agent_comments:
            print(f"\n{Fore.GREEN}=== Agent Voices ==={Style.RESET_ALL}")
            for agent_name, comment in agent_comments.items():
                print(f"\n{Fore.MAGENTA}[{agent_name}]{Style.RESET_ALL}")
                print(f"{Fore.WHITE}\"{comment}\"{Style.RESET_ALL}")
                    
        if system_summary:
            print(f"\n{Fore.GREEN}=== Overall Market View ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE}{system_summary}{Style.RESET_ALL}")
    
    def get_agent_tone_for_display(self, agent_name):
        """
        Get the styled agent tone for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Styled agent tone or None if not available
        """
        if not hasattr(self, 'agent_tones') or not self.agent_tones:
            return None
            
        # Convert name format (e.g., technical_analysis -> TechnicalAnalystAgent)
        name_mapping = {
            'technical_analysis': 'TechnicalAnalystAgent',
            'sentiment_analysis': 'SentimentAnalystAgent',
            'sentiment_aggregator_analysis': 'SentimentAggregatorAgent',
            'liquidity_analysis': 'LiquidityAnalystAgent',
            'open_interest_analysis': 'OpenInterestAnalystAgent',
            'funding_rate_analysis': 'FundingRateAnalystAgent'
        }
        
        # Try to find the agent tone using different name formats
        for key, tone in self.agent_tones.items():
            if agent_name == key:
                return tone
            if agent_name in name_mapping and name_mapping[agent_name] == key:
                return tone
                
        # As a fallback, try the reverse mapping
        reverse_mapping = {v: k for k, v in name_mapping.items()}
        if agent_name in reverse_mapping and reverse_mapping[agent_name] in self.agent_tones:
            return self.agent_tones[reverse_mapping[agent_name]]
                
        return None

# Command-line argument parsing
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run agent tests.')
    
    # Required arguments
    parser.add_argument('--agent', type=str, required=False, default='TechnicalAnalystAgent',
                      help='Name of the agent to test')
    
    # Trading parameters
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                      help='Trading symbol to test (default: BTC/USDT)')
    parser.add_argument('--interval', type=str, default='1h',
                      help='Time interval for analysis (default: 1h)')
    
    # Test configuration
    parser.add_argument('--mock-data', action='store_true',
                      help='Use mock data instead of real API')
    parser.add_argument('--repeat', type=int, default=1,
                      help='Number of times to repeat the test (default: 1)')
    parser.add_argument('--temperature', type=float, default=0.0,
                      help='Temperature setting for LLM to control randomness (default: 0.0)')
    parser.add_argument('--explain', action='store_true',
                      help='Print detailed explanations')
    
    # Advanced features
    parser.add_argument('--full-cycle', action='store_true',
                      help='Run full decision cycle with all agents')
    parser.add_argument('--trade-cycle', action='store_true',
                      help='Run full trade cycle (analysis, decision, plan)')
    parser.add_argument('--trade-log', action='store_true',
                      help='Save full JSON output of trade cycle test')
    parser.add_argument('--mock-portfolio', action='store_true',
                      help='Use mock portfolio for testing')
    parser.add_argument('--interactive', action='store_true',
                      help='Run in interactive mode with prompts for user input')
    
    return parser.parse_args()

def main():
    """Run the test harness."""
    args = parse_args()
    
    # Check if any core modules are missing
    if not IMPORTED_SUCCESSFULLY:
        print(f"{Fore.RED}Error: Core modules missing. Cannot run tests.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Make sure you're running this script from the project root directory.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Create test harness
    try:
        harness = AgentTestHarness(
            agent_name=args.agent,
            symbol=args.symbol,
            interval=args.interval,
            use_mock_data=args.mock_data,
            temperature=args.temperature,
            explain=args.explain,
            interactive=args.interactive
        )
        
        # Configure advanced features
        harness.full_cycle = args.full_cycle
        harness.trade_cycle = args.trade_cycle
        harness.trade_log = args.trade_log
        
        # Add mock portfolio if needed
        if args.mock_portfolio:
            mock_portfolio = {
                'total_value': 100000.0,
                'base_currency': 'USDT',
                'positions': {
                    args.symbol: {
                        'amount': 0.5,
                        'entry_price': 48000.0,
                        'current_price': harness.data_provider.get_current_price(args.symbol)
                    }
                },
                'open_positions_count': 1,
                'total_exposure_pct': 0.25,
                'risk_limit_per_trade': 0.05
            }
            harness.data_override['mock_portfolio'] = mock_portfolio
        
        # Run tests
        for i in range(args.repeat):
            if args.repeat > 1:
                print(f"\n{Fore.WHITE}Running test {i+1} of {args.repeat}...{Style.RESET_ALL}")
                
            result = harness.run_test()
            
            # Add short delay between tests
            if i < args.repeat - 1:
                time.sleep(1)
        
        # Clean up
        harness._restore_llm_client()
        
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()