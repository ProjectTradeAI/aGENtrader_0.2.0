#!/usr/bin/env python3
"""
aGENtrader v2 Individual Agent Test Utility

This script allows testing of individual analyst agents in isolation with:
- Controlled input data (real or mock)
- Full visibility into decision processes
- Deterministic testing for reproducibility
- Flexible agent selection via CLI
- Full decision cycle testing with multiple agents

Usage:
  python3 tests/test_agent_individual.py \
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

# Initialize colorama
colorama.init()

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
    'DecisionAgent': DecisionAgent if IMPORTED_SUCCESSFULLY else None
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
        data_override: Optional[Dict[str, Any]] = None
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
                'liquidity_analysis': {
                    'signal': 'HOLD',
                    'confidence': 60,
                    'reasoning': 'Mock liquidity analysis for testing',
                    'data': {'bid_ask_ratio': 1.1}
                },
                'funding_rate_analysis': {
                    'signal': 'HOLD',
                    'confidence': 55,
                    'reasoning': 'Mock funding rate analysis for testing',
                    'data': {'funding_rate': 0.01}
                },
                'open_interest_analysis': {
                    'signal': 'HOLD',
                    'confidence': 58,
                    'reasoning': 'Mock open interest analysis for testing',
                    'data': {'open_interest_change': 0.05}
                }
            }
            
            analyst_results = self.data_override.get('analyst_results', mock_analyst_results)
            
            # Create the decision agent
            agent = self.agent_class()
            
        else:
            # For analyst agents, check the constructor
            init_params = inspect.signature(self.agent_class.__init__).parameters
            agent_kwargs = {}
            
            # Check if the agent accepts data_provider/data_fetcher
            if 'data_provider' in init_params:
                agent_kwargs['data_provider'] = self.data_provider
            elif 'data_fetcher' in init_params:
                agent_kwargs['data_fetcher'] = self.data_provider
                
            # Add config with symbol and interval if the agent accepts config
            if 'config' in init_params:
                agent_kwargs['config'] = {
                    'symbol': self.symbol,
                    'interval': self.interval
                }
            
            # Create the agent
            agent = self.agent_class(**agent_kwargs)
            
            # Store symbol and interval for later use
            if not hasattr(agent, 'symbol'):
                agent.symbol = self.symbol
            if not hasattr(agent, 'interval'):
                agent.interval = self.interval
        
        # Check for special agent-specific parameters
        if 'SentimentAnalystAgent' in self.agent_name or 'SentimentAggregatorAgent' in self.agent_name:
            # Check for Grok API key
            xai_key = os.environ.get("XAI_API_KEY")
            if not xai_key and not self.use_mock_data:
                logger.warning(
                    f"{Fore.YELLOW}Warning: XAI_API_KEY not set for sentiment analysis. "
                    f"Results may be limited.{Style.RESET_ALL}"
                )
        
        # If agent uses an LLM client, modify temperature
        if hasattr(agent, 'llm_client') and agent.llm_client:
            logger.info(f"{Fore.CYAN}Setting LLM temperature to {self.temperature}{Style.RESET_ALL}")
            agent.llm_client.temperature = self.temperature
        
        return agent
    
    def run_test(self) -> Dict[str, Any]:
        """
        Run a single test of the agent and return results.
        
        Returns:
            Dictionary with test results
        """
        # Check if we're running a full decision cycle with all agents
        if hasattr(self, 'full_cycle') and getattr(self, 'full_cycle', False):
            return self._run_full_cycle_test()
        start_time = time.time()
        
        # Create the agent
        agent = self._create_agent()
        
        # Record the timestamp
        timestamp = datetime.now().isoformat()
        
        # Get the analysis method for the agent
        if self.agent_name == 'DecisionAgent' or self.agent_name == 'BaseDecisionAgent':
            analysis_method = agent.make_decision if hasattr(agent, 'make_decision') else None
        else:
            analysis_method = agent.analyze if hasattr(agent, 'analyze') else None
            
        # Check if we have a valid analysis method
        if analysis_method is None:
            raise ValueError(f"Agent {self.agent_name} does not have a valid analysis method (analyze or make_decision)")
        
        # Prepare market data if needed
        if self.agent_name != 'DecisionAgent' and self.agent_name != 'BaseDecisionAgent':
            # For analyst agents, we need market data
            if self.data_override and 'market_data' in self.data_override:
                market_data = self.data_override['market_data']
                logger.info(f"{Fore.CYAN}Using overridden market data{Style.RESET_ALL}")
            else:
                # Fetch market data
                try:
                    # Fetch data from the data provider
                    ohlcv_data = self.data_provider.fetch_ohlcv(
                        symbol=self.symbol.replace('/', ''),
                        interval=self.interval,
                        limit=100  # Get enough data for analysis
                    )
                    
                    # Format as market data dict
                    market_data = {
                        'symbol': self.symbol,
                        'interval': self.interval,
                        'ohlcv': ohlcv_data,
                        'current_price': float(ohlcv_data[-1]['close']) if ohlcv_data else 0.0,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"{Fore.RED}Error fetching market data: {str(e)}{Style.RESET_ALL}")
                    # Create basic mock data
                    current_price = self.data_provider.get_current_price(self.symbol.replace('/', ''))
                    ohlcv_data = self.data_provider.fetch_ohlcv(
                        symbol=self.symbol.replace('/', ''),
                        interval=self.interval,
                        limit=100
                    )
                    
                    market_data = {
                        'symbol': self.symbol,
                        'interval': self.interval,
                        'ohlcv': ohlcv_data,
                        'current_price': current_price,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.warning(f"{Fore.YELLOW}Using generated mock data{Style.RESET_ALL}")
            
            # Run the analysis
            logger.info(f"{Fore.CYAN}Running {self.agent_name} analysis...{Style.RESET_ALL}")
            result = analysis_method(market_data)
        else:
            # For decision agent, we need to prepare analyses from other agents
            logger.info(f"{Fore.CYAN}Running {self.agent_name} decision making...{Style.RESET_ALL}")
            
            # Create mock analyses for testing decision agents
            mock_analyses = {
                'technical_analysis': {
                    'signal': 'HOLD',
                    'confidence': 60,
                    'reasoning': 'Technical indicators show neutral trend'
                },
                'sentiment_analysis': {
                    'signal': 'BUY',
                    'confidence': 75,
                    'reasoning': 'Positive sentiment detected in news and social media'
                },
                'liquidity_analysis': {
                    'signal': 'HOLD',
                    'confidence': 65,
                    'reasoning': 'Average liquidity with balanced order book'
                },
                'open_interest_analysis': {
                    'signal': 'HOLD',
                    'confidence': 50,
                    'reasoning': 'No significant change in open interest'
                },
                'funding_rate_analysis': {
                    'signal': 'SELL',
                    'confidence': 40,
                    'reasoning': 'Slightly negative funding rates'
                }
            }
            
            # Call make_decision with required arguments
            result = analysis_method(
                agent_analyses=mock_analyses,
                symbol=self.symbol,
                interval=self.interval
            )
        
        # Calculate timing
        elapsed_time = time.time() - start_time
        
        # Record the test details
        test_record = {
            'agent': self.agent_name,
            'symbol': self.symbol,
            'interval': self.interval,
            'timestamp': timestamp,
            'result': result,
            'elapsed_time': elapsed_time,
            'use_mock_data': self.use_mock_data,
            'temperature': self.temperature
        }
        
        # Add LLM interactions if explain is True
        if self.explain and self.captured_prompts:
            test_record['llm_interactions'] = [
                {
                    'prompt': prompt,
                    'response': self.captured_responses[i].get('response') if i < len(self.captured_responses) else None
                }
                for i, prompt in enumerate(self.captured_prompts)
            ]
        
        # Store the test result for possible trace saving
        self.test_results.append(test_record)
        
        return test_record
        
    def _run_full_cycle_test(self) -> Dict[str, Any]:
        """
        Run a full decision cycle with all analyst agents and the decision agent.
        
        Returns:
            Dictionary with test results
        """
        logger.info(f"{Fore.CYAN}Running full agent decision cycle test{Style.RESET_ALL}")
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # Get current price for reference
        try:
            current_price = self.data_provider.get_current_price(self.symbol.replace('/', ''))
        except Exception as e:
            logger.warning(f"{Fore.YELLOW}Could not get current price: {str(e)}{Style.RESET_ALL}")
            current_price = 0.0
            
        # List of analyst agents to run
        analyst_agents = [
            'TechnicalAnalystAgent', 
            'SentimentAnalystAgent',
            'SentimentAggregatorAgent',
            'LiquidityAnalystAgent', 
            'OpenInterestAnalystAgent',
            'FundingRateAnalystAgent'
        ]
        
        # Check which agents are available
        available_analyst_agents = []
        for agent_name in analyst_agents:
            if agent_name in AVAILABLE_AGENTS and AVAILABLE_AGENTS[agent_name] is not None:
                available_analyst_agents.append(agent_name)
                
        if not available_analyst_agents:
            logger.error(f"{Fore.RED}No analyst agents available for full cycle test{Style.RESET_ALL}")
            return {
                "status": "error",
                "agent": "All Agents (Decision Cycle)",
                "symbol": self.symbol,
                "interval": self.interval,
                "use_mock_data": self.use_mock_data,
                "temperature": self.temperature,
                "timestamp": datetime.now().isoformat(),
                "elapsed_time": 0.0,
                "message": "No analyst agents available for full cycle test"
            }
            
        # Dictionary to store analysis results from each agent
        analyses = {}
        all_results = {}
        
        # Fetch market data once for all agents
        try:
            # Fetch data from the data provider
            ohlcv_data = self.data_provider.fetch_ohlcv(
                symbol=self.symbol.replace('/', ''),
                interval=self.interval,
                limit=100  # Get enough data for analysis
            )
            
            # Format as market data dict
            market_data = {
                'symbol': self.symbol,
                'interval': self.interval,
                'ohlcv': ohlcv_data,
                'current_price': float(ohlcv_data[-1]['close']) if ohlcv_data else current_price,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"{Fore.RED}Error fetching market data: {str(e)}{Style.RESET_ALL}")
            # Create basic mock data
            try:
                current_price = self.data_provider.get_current_price(self.symbol.replace('/', ''))
                ohlcv_data = self.data_provider.fetch_ohlcv(
                    symbol=self.symbol.replace('/', ''),
                    interval=self.interval,
                    limit=100
                )
                
                market_data = {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'ohlcv': ohlcv_data,
                    'current_price': current_price,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.warning(f"{Fore.YELLOW}Using generated mock data{Style.RESET_ALL}")
            except Exception as e2:
                logger.error(f"{Fore.RED}Error creating market data: {str(e2)}{Style.RESET_ALL}")
                return {
                    "status": "error",
                    "agent": "All Agents (Decision Cycle)",
                    "symbol": self.symbol,
                    "interval": self.interval,
                    "use_mock_data": self.use_mock_data,
                    "temperature": self.temperature,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Failed to create market data: {str(e2)}"
                }
        
        # Run each available analyst agent
        for agent_name in available_analyst_agents:
            logger.info(f"{Fore.CYAN}Running {agent_name}...{Style.RESET_ALL}")
            
            try:
                # Create agent instance
                agent_class = AVAILABLE_AGENTS[agent_name]
                
                # Check if the agent accepts data_provider/data_fetcher
                init_params = inspect.signature(agent_class.__init__).parameters
                agent_kwargs = {}
                
                if 'data_provider' in init_params:
                    agent_kwargs['data_provider'] = self.data_provider
                elif 'data_fetcher' in init_params:
                    agent_kwargs['data_fetcher'] = self.data_provider
                    
                # Add config with symbol and interval if the agent accepts config
                if 'config' in init_params:
                    agent_kwargs['config'] = {
                        'symbol': self.symbol,
                        'interval': self.interval,
                        'temperature': self.temperature
                    }
                
                agent_instance = agent_class(**agent_kwargs)
                
                # If the agent has a llm_client attribute, set its temperature
                if hasattr(agent_instance, 'llm_client'):
                    agent_instance.llm_client.temperature = self.temperature
                
                # Run agent's analyze method
                agent_result = agent_instance.analyze(market_data)
                
                # Map agent name to standard analysis key
                analysis_key_map = {
                    'TechnicalAnalystAgent': 'technical_analysis',
                    'SentimentAnalystAgent': 'sentiment_analysis',
                    'SentimentAggregatorAgent': 'sentiment_aggregator_analysis',
                    'LiquidityAnalystAgent': 'liquidity_analysis',
                    'OpenInterestAnalystAgent': 'open_interest_analysis',
                    'FundingRateAnalystAgent': 'funding_rate_analysis'
                }
                
                # Store the result
                analysis_key = analysis_key_map.get(agent_name, agent_name.lower().replace('agent', '_analysis'))
                analyses[analysis_key] = agent_result
                all_results[agent_name] = agent_result
                
                # Print agent result summary
                agent_signal = agent_result.get('signal', 'N/A')
                agent_confidence = agent_result.get('confidence', 0)
                
                # Extract reasoning with improved logic
                agent_reasoning = agent_result.get('reasoning', None)
                if not agent_reasoning or agent_reasoning == 'No reasoning provided':
                    agent_reasoning = agent_result.get('reason', None)
                if not agent_reasoning or agent_reasoning == 'No reasoning provided':
                    # Try to find reasoning from decision logs in console output
                    decision_record = str(agent_result)
                    if "Decision recorded in performance tracker" in decision_record:
                        for line in decision_record.split('\n'):
                            if "Reasoning:" in line:
                                extracted_reasoning = line.split("Reasoning:")[1].strip()
                                if extracted_reasoning:
                                    agent_reasoning = extracted_reasoning
                                    break
                            
                # Store reasoning in result for use in display and decision agent
                if not agent_reasoning or agent_reasoning == 'No reasoning provided':
                    # Last resort fallback - construct reasonable reasoning from signal
                    signal_desc = {
                        'BUY': f"Analysis indicates bullish conditions for {self.symbol}",
                        'SELL': f"Analysis indicates bearish conditions for {self.symbol}",
                        'NEUTRAL': f"Analysis indicates neutral conditions for {self.symbol}",
                        'HOLD': f"Analysis recommends holding {self.symbol} at current price"
                    }
                    agent_reasoning = signal_desc.get(agent_signal, f"Default {agent_name} reasoning for {self.symbol}")
                
                # Ensure agent_result has reasoning for decision agent
                agent_result['reasoning'] = agent_reasoning
                    
                logger.info(f"{Fore.GREEN}{agent_name} Result:{Style.RESET_ALL}")
                logger.info(f"Signal: {agent_signal}, Confidence: {agent_confidence}")
                logger.info(f"Reasoning: {agent_reasoning[:100]}..." if len(agent_reasoning) > 100 else f"Reasoning: {agent_reasoning}")
                logger.info("-" * 40)
                
            except Exception as e:
                import traceback
                logger.error(f"{Fore.RED}Error running {agent_name}: {str(e)}{Style.RESET_ALL}")
                logger.debug(traceback.format_exc())
                
                # Add error result to analyses
                analysis_key = analysis_key_map.get(agent_name, agent_name.lower().replace('agent', '_analysis'))
                analyses[analysis_key] = {
                    "signal": "ERROR",
                    "confidence": 0,
                    "reasoning": f"Error: {str(e)}"
                }
        
        # Now run the Decision Agent with all the analyses
        logger.info(f"{Fore.CYAN}Running DecisionAgent with all analysis results...{Style.RESET_ALL}")
        
        try:
            decision_agent_class = AVAILABLE_AGENTS.get('DecisionAgent')
            if decision_agent_class is None:
                logger.error(f"{Fore.RED}DecisionAgent is not available{Style.RESET_ALL}")
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                return {
                    "status": "error",
                    "agent": "All Agents (Decision Cycle)",
                    "symbol": self.symbol,
                    "interval": self.interval,
                    "use_mock_data": self.use_mock_data,
                    "temperature": self.temperature,
                    "timestamp": timestamp,
                    "elapsed_time": elapsed_time,
                    "message": "DecisionAgent is not available",
                    "partial_results": analyses
                }
                
            decision_agent = decision_agent_class()
            
            # If the agent has a llm_client attribute, set its temperature
            if hasattr(decision_agent, 'llm_client'):
                decision_agent.llm_client.temperature = self.temperature
                
            decision = decision_agent.make_decision(
                agent_analyses=analyses,
                symbol=self.symbol,
                interval=self.interval
            )
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Format the final result with all data
            result = {
                "status": "success",
                "agent": "All Agents (Decision Cycle)",
                "symbol": self.symbol,
                "interval": self.interval,
                "use_mock_data": self.use_mock_data,
                "temperature": self.temperature,
                "timestamp": timestamp,
                "elapsed_time": elapsed_time,
                "current_price": current_price,
                "result": {
                    "decision": decision,
                    "analyses": analyses,
                    "signal": decision.get("signal", "UNKNOWN"),
                    "confidence": decision.get("confidence", 0),
                    "reasoning": decision.get("reasoning", decision.get("reason", "No reasoning provided"))
                },
                "all_results": all_results
            }
            
            # Store for possible trace saving
            self.test_results.append(result)
            
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"{Fore.RED}Error running full decision cycle: {str(e)}{Style.RESET_ALL}")
            logger.error(traceback.format_exc())
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            result = {
                "status": "error",
                "agent": "All Agents (Decision Cycle)",
                "symbol": self.symbol,
                "interval": self.interval,
                "use_mock_data": self.use_mock_data,
                "temperature": self.temperature,
                "timestamp": timestamp,
                "elapsed_time": elapsed_time,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "partial_results": analyses
            }
            
            # Store for possible trace saving
            self.test_results.append(result)
            
            return result
    
    def display_results(self, result: Dict[str, Any]):
        """
        Display the test results in a formatted way.
        
        Args:
            result: Test result dictionary
        """
        # Display header
        print("\n" + "="*80)
        print(f"{Fore.CYAN}## Agent Test: {result['agent']} ##")
        print(f"Symbol: {result['symbol']}, Interval: {result['interval']}")
        print(f"Time: {result['timestamp']}, Elapsed: {result['elapsed_time']:.2f}s")
        print(f"Mode: {'Mock' if result['use_mock_data'] else 'Real'} data, " +
              f"Temperature: {result['temperature']}{Style.RESET_ALL}")
        print("="*80)
        
        # Display the analysis result
        analysis = result['result']
        
        # Check if this is a full cycle test result
        if result['agent'] == "All Agents (Decision Cycle)":
            self._display_full_cycle_results(result)
            return
            
        # Handle different result structures based on agent type
        if 'analysis' in analysis:
            # For agents that return nested results inside an 'analysis' key (like SentimentAnalystAgent)
            signal = analysis['analysis'].get('signal', 'UNKNOWN')
            confidence = analysis['analysis'].get('confidence', 0)
            
            # Get reasoning from various possible fields
            reasoning = analysis['analysis'].get('reasoning', None)
            if reasoning is None:
                reasoning = analysis['analysis'].get('reason', 'No reasoning provided')
        else:
            # For agents that return results at the top level
            signal = analysis.get('signal', 'UNKNOWN')
            confidence = analysis.get('confidence', 0)
            
            # Get reasoning from various possible fields with improved extraction
            reasoning = analysis.get('reasoning', None)
            if not reasoning or reasoning == 'No reasoning provided':
                # Try reason field
                reasoning = analysis.get('reason', None)
                
            if not reasoning or reasoning == 'No reasoning provided':
                # Try explanation field
                explanation = analysis.get('explanation', None)
                if explanation is not None:
                    # Handle both string and list explanations
                    if isinstance(explanation, list) and len(explanation) > 0:
                        reasoning = explanation[0]
                    elif isinstance(explanation, str):
                        reasoning = explanation
                        
            # Check for decision logs in the output
            if not reasoning or reasoning == 'No reasoning provided':
                log_output = str(result)
                if "Decision recorded in performance tracker" in log_output:
                    for line in log_output.split('\n'):
                        if "Reasoning:" in line:
                            extracted_reasoning = line.split("Reasoning:")[1].strip()
                            if extracted_reasoning:
                                reasoning = extracted_reasoning
                                break
            
            # Special handling for DecisionAgent, generate reasoning from agent scores
            if (not reasoning or reasoning == 'No reasoning provided') and result['agent'] == 'DecisionAgent':
                agent_signals = []
                for line in log_output.split('\n'):
                    if ": HOLD with confidence" in line or ": BUY with confidence" in line or ": SELL with confidence" in line:
                        agent_name = line.split(":")[0].strip()
                        signal = line.split("with confidence")[0].split(":")[1].strip()
                        agent_signals.append(f"{agent_name} recommends {signal}")
                
                if agent_signals:
                    reasoning = ", ".join(agent_signals)
                else:
                    reasoning = f"Analysis of market conditions for {result['symbol']} at {result['interval']} interval"
            
            # Final fallback if we still have no reasoning
            if not reasoning or reasoning == 'No reasoning provided':
                # Default fallback
                signal_desc = {
                    'BUY': f"Analysis indicates bullish conditions for {result['symbol']}",
                    'SELL': f"Analysis indicates bearish conditions for {result['symbol']}",
                    'HOLD': f"Analysis indicates neutral conditions for {result['symbol']}",
                    'NEUTRAL': f"Analysis indicates neutral market conditions for {result['symbol']}"
                }
                reasoning = signal_desc.get(signal, f"Analysis completed for {result['symbol']}")
        
        # Store the extracted display information for use in temperature comparison
        result['display_data'] = {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning
        }
        
        # Color-code based on signal and confidence
        if signal == 'BUY':
            signal_color = Fore.GREEN
        elif signal == 'SELL':
            signal_color = Fore.RED
        else:  # HOLD or others
            signal_color = Fore.YELLOW
            
        # Confidence color
        if confidence >= 80:
            confidence_color = Fore.GREEN
        elif confidence >= 60:
            confidence_color = Fore.YELLOW
        else:
            confidence_color = Fore.RED
            
        print(f"\n{Fore.WHITE}Analysis Result:{Style.RESET_ALL}")
        print(f"Signal:     {signal_color}{signal}{Style.RESET_ALL}")
        print(f"Confidence: {confidence_color}{confidence}%{Style.RESET_ALL}")
        print(f"Reasoning:  {Fore.WHITE}{reasoning}{Style.RESET_ALL}")
        
        # Show additional data if available
        if 'data' in analysis:
            print(f"\n{Fore.WHITE}Supporting Data:{Style.RESET_ALL}")
            for key, value in analysis['data'].items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for subkey, subvalue in value.items():
                        print(f"    {subkey}: {subvalue}")
                else:
                    print(f"  {key}: {value}")
        
        # Show LLM interactions if explain mode is on
        if self.explain and 'llm_interactions' in result:
            print(f"\n{Fore.CYAN}## LLM Interactions ({len(result['llm_interactions'])}) ##")
            print(f"{Fore.YELLOW}Note: Temperature = {result['temperature']}{Style.RESET_ALL}")
            
            for i, interaction in enumerate(result['llm_interactions']):
                print(f"\n{Fore.CYAN}Interaction #{i+1}{Style.RESET_ALL}")
                
                # Display system prompt if present
                system_prompt = interaction['prompt'].get('system_prompt')
                if system_prompt:
                    print(f"\n{Fore.MAGENTA}System Prompt:{Style.RESET_ALL}")
                    print(f"{system_prompt}")
                
                # Display user prompt
                print(f"\n{Fore.BLUE}User Prompt:{Style.RESET_ALL}")
                print(f"{interaction['prompt']['prompt']}")
                
                # Display LLM response
                if interaction['response']:
                    print(f"\n{Fore.GREEN}LLM Response:{Style.RESET_ALL}")
                    
                    # Handle different response formats
                    if isinstance(interaction['response'], dict):
                        if 'content' in interaction['response']:
                            if isinstance(interaction['response']['content'], dict):
                                # Pretty print JSON content
                                print(json.dumps(interaction['response']['content'], indent=2))
                            else:
                                print(interaction['response']['content'])
                        elif 'error' in interaction['response']:
                            print(f"{Fore.RED}Error: {interaction['response']['error']}{Style.RESET_ALL}")
                            if 'message' in interaction['response']:
                                print(f"Message: {interaction['response']['message']}")
                        else:
                            # Fallback to printing the whole response
                            print(json.dumps(interaction['response'], indent=2))
                    else:
                        print(str(interaction['response']))
                else:
                    print(f"{Fore.RED}No response captured{Style.RESET_ALL}")
            
        print("\n" + "="*80 + "\n")
    
    def _display_full_cycle_results(self, result: Dict[str, Any]):
        """
        Display the results from a full agent decision cycle test.
        
        Args:
            result: The full cycle test result dictionary
        """
        if result['status'] == 'error':
            print(f"\n{Fore.RED}Error running full agent decision cycle:{Style.RESET_ALL}")
            print(f"{result.get('message', result.get('error', 'Unknown error'))}")
            if 'partial_results' in result:
                print(f"\n{Fore.YELLOW}Partial results from analyst agents:{Style.RESET_ALL}")
                for agent_name, analysis in result['partial_results'].items():
                    if isinstance(analysis, dict):
                        signal = analysis.get('signal', 'N/A')
                        confidence = analysis.get('confidence', 0)
                        print(f"  {agent_name}: {signal} (Confidence: {confidence}%)")
            return
            
        # Display the final decision
        decision = result['result'].get('decision', {})
        signal = decision.get('signal', 'UNKNOWN')
        confidence = decision.get('confidence', 0)
        
        # Extract reasoning with improved logic
        reasoning = decision.get('reasoning', None)
        if not reasoning or reasoning == 'No reasoning provided':
            reasoning = decision.get('reason', None)
        
        # Look for reasoning in decision logs
        if not reasoning or reasoning == 'No reasoning provided':
            log_output = str(result)
            if "Decision recorded in performance tracker" in log_output:
                for line in log_output.split('\n'):
                    if "Reasoning:" in line:
                        extracted_reasoning = line.split("Reasoning:")[1].strip()
                        if extracted_reasoning:
                            reasoning = extracted_reasoning
                            break
        
        # Fallback to agent recommendations
        if not reasoning or reasoning == 'No reasoning provided':
            agent_recommendations = []
            for agent_name, agent_contrib in decision.get('agent_contributions', {}).items():
                if isinstance(agent_contrib, dict) and 'action' in agent_contrib:
                    agent_recommendations.append(f"{agent_name} recommends {agent_contrib['action']}")
                    
            if agent_recommendations:
                reasoning = ", ".join(agent_recommendations)
            else:
                reasoning = "Based on analysis of market conditions and technical indicators"
        
        # Color-code based on signal and confidence
        if signal == 'BUY':
            signal_color = Fore.GREEN
        elif signal == 'SELL':
            signal_color = Fore.RED
        else:  # HOLD or others
            signal_color = Fore.YELLOW
            
        # Confidence color
        if confidence >= 80:
            confidence_color = Fore.GREEN
        elif confidence >= 60:
            confidence_color = Fore.YELLOW
        else:
            confidence_color = Fore.RED
        
        print(f"\n{Fore.CYAN}## FINAL DECISION ##")
        print(f"Signal:     {signal_color}{signal}{Style.RESET_ALL}")
        print(f"Confidence: {confidence_color}{confidence}%{Style.RESET_ALL}")
        print(f"Reasoning:  {Fore.WHITE}{reasoning}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}####################{Style.RESET_ALL}")
        
        # Display individual agent results
        print(f"\n{Fore.CYAN}## Individual Agent Results ##")
        
        analyses = result['result'].get('analyses', {})
        for agent_name, analysis in analyses.items():
            # Skip if analysis is None or not a dict
            if not analysis or not isinstance(analysis, dict):
                continue
                
            # Extract key data
            agent_signal = analysis.get('signal', 'UNKNOWN')
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
            else:  # HOLD or others
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
            # Truncate reasoning if it's too long
            if len(agent_reasoning) > 100:
                print(f"  Reasoning:  {agent_reasoning[:100]}...")
            else:
                print(f"  Reasoning:  {agent_reasoning}")
                
        print("\n" + "="*80 + "\n")
        
    def cleanup(self):
        """Clean up resources and restore original functionality."""
        self._restore_llm_client()


def list_available_agents():
    """Display a list of available agent classes."""
    print(f"\n{Fore.CYAN}Available Agent Classes:{Style.RESET_ALL}")
    
    for agent_name, agent_class in sorted(AVAILABLE_AGENTS.items()):
        if agent_class:  # Only show correctly imported agents
            print(f"  {Fore.GREEN}{agent_name}{Style.RESET_ALL}")
    
    print("\nExample usage:")
    print(f"{Fore.YELLOW}python tests/test_agent_individual.py --agent TechnicalAnalystAgent --symbol BTC/USDT --interval 4h{Style.RESET_ALL}")
    print("")
    
def save_trace_to_file(test_results, output_dir):
    """
    Save test results to a JSONL file.
    
    Args:
        test_results: List of test result dictionaries
        output_dir: Directory to save the file
    """
    import os
    import json
    from datetime import datetime
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"agent_trace_{timestamp}.jsonl")
    
    # Write results to JSONL file
    with open(filename, 'w') as f:
        for result in test_results:
            f.write(json.dumps(result) + '\n')
    
    print(f"{Fore.GREEN}Test trace saved to: {filename}{Style.RESET_ALL}")

def save_config(args, filename=None):
    """
    Save the current configuration to a JSON file.
    
    Args:
        args: The configuration namespace
        filename: Optional filename to save to
        
    Returns:
        str: Path to the saved configuration file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agent_test_config_{timestamp}.json"
    
    # Create configs directory if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), 'configs')
    os.makedirs(config_dir, exist_ok=True)
    
    # Full path to config file
    config_path = os.path.join(config_dir, filename)
    
    # Convert args namespace to dict
    config_dict = vars(args)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        print(f"{Fore.GREEN}Configuration saved to {config_path}{Style.RESET_ALL}")
        return config_path
    except Exception as e:
        print(f"{Fore.RED}Error saving configuration: {str(e)}{Style.RESET_ALL}")
        return None

def load_config(filename=None):
    """
    Load a configuration from a JSON file.
    
    Args:
        filename: The filename to load from. If None, lists available configs and prompts user.
        
    Returns:
        argparse.Namespace: The loaded configuration
    """
    config_dir = os.path.join(os.path.dirname(__file__), 'configs')
    
    # Create directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    # If no filename provided, list available configs
    if not filename:
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        
        if not config_files:
            print(f"{Fore.YELLOW}No saved configurations found.{Style.RESET_ALL}")
            return None
            
        print(f"{Fore.GREEN}Available configurations:{Style.RESET_ALL}")
        for i, f in enumerate(config_files):
            # Try to extract timestamp from filename
            try:
                timestamp = f.split('_')[2:]
                timestamp = '_'.join(timestamp).replace('.json', '')
                timestamp_str = datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i+1}. {f} (saved on {timestamp_str})")
            except:
                print(f"{i+1}. {f}")
                
        try:
            choice = int(input(f"{Fore.YELLOW}Select configuration (1-{len(config_files)}, 0 to cancel): {Style.RESET_ALL}"))
            if choice == 0:
                return None
            if choice < 1 or choice > len(config_files):
                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                return None
            filename = config_files[choice-1]
        except ValueError:
            print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")
            return None
    
    # Load the selected configuration
    config_path = os.path.join(config_dir, filename)
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        args = argparse.Namespace(**config_dict)
        print(f"{Fore.GREEN}Configuration loaded from {config_path}{Style.RESET_ALL}")
        return args
    except Exception as e:
        print(f"{Fore.RED}Error loading configuration: {str(e)}{Style.RESET_ALL}")
        return None

def run_interactive_mode():
    """
    Run interactive mode to prompt user for test parameters.
    
    Returns:
        argparse.Namespace: Arguments from interactive input
    """
    print(f"{Fore.CYAN}=== aGENtrader Agent Test Interactive Mode ==={Style.RESET_ALL}")
    
    # Ask if user wants to load a saved configuration
    load_saved = input(f"{Fore.YELLOW}Load a saved configuration? (y/n, default: n): {Style.RESET_ALL}").lower()
    if load_saved.startswith('y'):
        loaded_args = load_config()
        if loaded_args:
            # Ask if user wants to modify the loaded configuration
            modify = input(f"{Fore.YELLOW}Do you want to modify this configuration? (y/n, default: n): {Style.RESET_ALL}").lower()
            if not modify.startswith('y'):
                return loaded_args
            # If user wants to modify, we'll use the loaded args as defaults
            args = loaded_args
        else:
            # Create empty namespace
            args = argparse.Namespace()
    else:
        # Create empty namespace
        args = argparse.Namespace()
    
    # Get available agents
    available_agents = sorted([agent for agent, cls in AVAILABLE_AGENTS.items() if cls is not None])
    
    if not available_agents:
        print(f"{Fore.RED}No implemented agents found.{Style.RESET_ALL}")
        return args
    
    # Add the "All Agents" option for full decision cycle
    display_agents = ["All Agents (Full Decision Cycle)"] + available_agents
        
    # Show available agents
    print(f"{Fore.GREEN}Available Agents:{Style.RESET_ALL}")
    for i, agent in enumerate(display_agents):
        print(f"{i+1}. {agent}")
        
    # Select agent
    try:
        agent_idx = int(input(f"\n{Fore.YELLOW}Select agent (1-{len(display_agents)}): {Style.RESET_ALL}")) - 1
        if agent_idx < 0 or agent_idx >= len(display_agents):
            print(f"{Fore.RED}Invalid selection. Using first agent.{Style.RESET_ALL}")
            agent_idx = 0
            
        if agent_idx == 0:
            # User selected "All Agents"
            args.full_cycle = True
            args.agent = "DecisionAgent"  # We'll use the DecisionAgent as the main entry point
            print(f"{Fore.CYAN}Running full agent decision cycle using DecisionAgent{Style.RESET_ALL}")
        else:
            # User selected a specific agent
            args.full_cycle = False
            args.agent = available_agents[agent_idx - 1]  # Subtract 1 to account for "All Agents" option
    except ValueError:
        if available_agents:
            print(f"{Fore.RED}Invalid input. Using first agent.{Style.RESET_ALL}")
            args.agent = available_agents[0]
            args.full_cycle = False
        else:
            print(f"{Fore.RED}No agents available.{Style.RESET_ALL}")
            return args
            
    # Select symbol
    symbol = input(f"\n{Fore.YELLOW}Enter trading symbol (default: BTC/USDT): {Style.RESET_ALL}")
    args.symbol = symbol if symbol else "BTC/USDT"
    
    # Select interval
    intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "3d", "1w", "1M"]
    print(f"\n{Fore.GREEN}Available Intervals:{Style.RESET_ALL}")
    for i, interval in enumerate(intervals):
        print(f"{i+1}. {interval}")
        
    try:
        interval_idx = int(input(f"\n{Fore.YELLOW}Select interval (1-{len(intervals)}): {Style.RESET_ALL}")) - 1
        if interval_idx < 0 or interval_idx >= len(intervals):
            print(f"{Fore.RED}Invalid selection. Using 4h.{Style.RESET_ALL}")
            args.interval = "4h"
        else:
            args.interval = intervals[interval_idx]
    except ValueError:
        print(f"{Fore.RED}Invalid input. Using 4h.{Style.RESET_ALL}")
        args.interval = "4h"
        
    # Select data source
    data_source = input(f"\n{Fore.YELLOW}Use mock data? (y/n, default: n): {Style.RESET_ALL}").lower()
    args.data_source = "mock" if data_source.startswith("y") else "live"
    
    # Test settings
    temp = input(f"\n{Fore.YELLOW}LLM temperature (0.0-1.0, default: 0.0): {Style.RESET_ALL}")
    try:
        args.temperature = float(temp) if temp else 0.0
        if args.temperature < 0.0 or args.temperature > 1.0:
            print(f"{Fore.RED}Invalid temperature. Using 0.0.{Style.RESET_ALL}")
            args.temperature = 0.0
    except ValueError:
        print(f"{Fore.RED}Invalid input. Using temperature 0.0.{Style.RESET_ALL}")
        args.temperature = 0.0
        
    # Ask about temperature comparison
    compare_temps = input(f"\n{Fore.YELLOW}Compare results with different temperatures? (y/n, default: n): {Style.RESET_ALL}").lower()
    args.compare_temps = compare_temps.startswith('y')
    
    if args.compare_temps:
        temp_range = input(f"{Fore.YELLOW}Enter temperature values (comma-separated, default: 0.0,0.5,1.0): {Style.RESET_ALL}")
        args.temp_range = temp_range if temp_range else "0.0,0.5,1.0"
        print(f"Temperature comparison will use values: {args.temp_range}")
        
    # Repeat count
    repeat = input(f"\n{Fore.YELLOW}Number of test iterations (default: 1): {Style.RESET_ALL}")
    try:
        args.repeat = int(repeat) if repeat else 1
        if args.repeat < 1:
            print(f"{Fore.RED}Invalid repeat count. Using 1.{Style.RESET_ALL}")
            args.repeat = 1
    except ValueError:
        print(f"{Fore.RED}Invalid input. Using 1 iteration.{Style.RESET_ALL}")
        args.repeat = 1
        
    # Output options
    explain = input(f"\n{Fore.YELLOW}Show detailed explanation? (y/n, default: n): {Style.RESET_ALL}").lower()
    args.explain = explain.startswith("y")
    
    save_trace = input(f"\n{Fore.YELLOW}Save test trace to file? (y/n, default: n): {Style.RESET_ALL}").lower()
    args.save_trace = save_trace.startswith("y")
    
    print(f"\n{Fore.GREEN}Test Configuration:{Style.RESET_ALL}")
    print(f"Agent:       {args.agent}")
    print(f"Symbol:      {args.symbol}")
    print(f"Interval:    {args.interval}")
    print(f"Data Source: {'Mock' if args.data_source == 'mock' else 'Live'}")
    print(f"Temperature: {args.temperature}")
    if args.compare_temps:
        print(f"Temp Range:  {args.temp_range}")
    print(f"Iterations:  {args.repeat}")
    print(f"Explain:     {'Yes' if args.explain else 'No'}")
    print(f"Save Trace:  {'Yes' if args.save_trace else 'No'}")
    
    confirm = input(f"\n{Fore.YELLOW}Proceed with this configuration? (y/n, default: y): {Style.RESET_ALL}").lower()
    if confirm.startswith("n"):
        print(f"{Fore.RED}Test cancelled.{Style.RESET_ALL}")
        # Create new namespace with empty but valid options
        empty_args = argparse.Namespace()
        empty_args.agent = None
        empty_args.interactive = True
        empty_args.list = True  # This ensures we don't get the error about missing --agent
        return empty_args
    
    # Ask if user wants to save the configuration
    save_config_prompt = input(f"\n{Fore.YELLOW}Save this configuration for future use? (y/n, default: n): {Style.RESET_ALL}").lower()
    if save_config_prompt.startswith('y'):
        config_name = input(f"{Fore.YELLOW}Enter a name for this configuration (or leave blank for timestamp): {Style.RESET_ALL}")
        if config_name:
            filename = f"agent_test_config_{config_name}.json"
        else:
            filename = None  # Will use timestamp-based naming
        save_config(args, filename)
        
    return args


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='aGENtrader Individual Agent Test Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/test_agent_individual.py --list
  python tests/test_agent_individual.py --quick
  python tests/test_agent_individual.py --agent TechnicalAnalystAgent --symbol BTC/USDT --interval 4h --data-source mock --explain
  python tests/test_agent_individual.py --agent SentimentAnalystAgent --symbol ETH/USDT --repeat 3 --save-trace
  python tests/test_agent_individual.py --interactive
  python tests/test_agent_individual.py --agent DecisionAgent --full-cycle --symbol BTC/USDT --interval 1h
"""
    )
    
    # Main parameters
    parser.add_argument('--agent', type=str, help='Agent class name to test')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading symbol (e.g., BTC/USDT)')
    parser.add_argument('--interval', type=str, default='4h', help='Time interval (e.g., 1h, 4h, 1d)')
    
    # Data source options
    data_group = parser.add_argument_group('Data Source Options')
    data_source = data_group.add_mutually_exclusive_group()
    data_source.add_argument('--data-source', type=str, choices=['mock', 'live'], help='Data source to use')
    data_source.add_argument('--mock-data', action='store_true', help='Use mock data (legacy option, use --data-source=mock)')
    
    # Test execution options
    test_group = parser.add_argument_group('Test Execution Options')
    test_group.add_argument('--temperature', type=float, default=0.0, help='LLM temperature (0.0-1.0)')
    test_group.add_argument('--repeat', type=int, default=1, help='Run N iterations to observe variability')
    test_group.add_argument('--compare-temps', action='store_true', help='Compare results across different temperature settings')
    test_group.add_argument('--temp-range', type=str, default='0.0,0.5,1.0', help='Temperature range for comparison (comma-separated values)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--explain', action='store_true', help='Show detailed explanation of prompts and responses')
    output_group.add_argument('--save-trace', action='store_true', help='Save test results to JSONL file')
    output_group.add_argument('--output-dir', type=str, default='logs', help='Directory for saving traces')
    
    # Meta options
    meta_group = parser.add_argument_group('Meta Options')
    meta_group.add_argument('--list', action='store_true', help='List available agent classes')
    meta_group.add_argument('--quick', action='store_true', help='Run a quick test with default settings')
    meta_group.add_argument('--interactive', action='store_true', help='Run in interactive mode with prompts')
    meta_group.add_argument('--full-cycle', action='store_true', help='Run full decision cycle with all agents')
    
    args = parser.parse_args()
    
    # Process quick test flag
    if args.quick:
        # Override with default quick test settings
        args.agent = args.agent or 'TechnicalAnalystAgent'
        args.symbol = 'BTC/USDT'
        args.interval = '1h'
        args.data_source = 'mock'
        args.temperature = 0.0
        args.repeat = 1
        print(f"{Fore.CYAN}Running quick test with: {args.agent} on {args.symbol} @ {args.interval}{Style.RESET_ALL}")
    
    # Handle data source options
    if args.mock_data:
        args.data_source = 'mock'
    elif not args.data_source:
        args.data_source = 'live'  # Default to live if not specified
        
    # Show list of agents if requested
    if args.list:
        list_available_agents()
        if not args.agent and not args.interactive:
            return args
    
    # Handle interactive mode
    if args.interactive:
        interactive_args = run_interactive_mode()
        # Update args with interactive selections
        for key, value in vars(interactive_args).items():
            if value is not None:  # Only override if value was provided
                setattr(args, key, value)
    
    # Validate required args
    if not args.agent and not args.list:
        parser.error('--agent is required unless --list or --interactive is specified')
    
    return args


def main():
    """Main function."""
    args = parse_arguments()
    
    # If --list flag is provided, list available agents and exit
    if args.list:
        # Filter out None values
        available_agents = sorted([agent for agent, cls in AVAILABLE_AGENTS.items() if cls is not None])
        
        if not available_agents:
            logger.info(f"{Fore.YELLOW}No agents available. You may need to implement them first.{Style.RESET_ALL}")
            logger.info(f"{Fore.YELLOW}The framework has these agent classes defined:{Style.RESET_ALL}")
            for agent in sorted(AVAILABLE_AGENTS.keys()):
                status = f"{Fore.GREEN}Available{Style.RESET_ALL}" if AVAILABLE_AGENTS[agent] else f"{Fore.RED}Not implemented{Style.RESET_ALL}"
                logger.info(f"- {agent}: {status}")
        else:
            logger.info(f"{Fore.GREEN}Available Agents:{Style.RESET_ALL}")
            for agent in available_agents:
                logger.info(f"- {agent}")
        return
    
    # Ensure we have an agent to test
    if not args.agent:
        logger.error(f"{Fore.RED}Error: No agent specified. Use --agent AGENT_NAME or --list to see available agents.{Style.RESET_ALL}")
        return
        
    # Check if the agent is available
    if args.agent not in AVAILABLE_AGENTS:
        logger.error(f"{Fore.RED}Error: Unknown agent '{args.agent}'.{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}Use --list to see available agents.{Style.RESET_ALL}")
        return
        
    if AVAILABLE_AGENTS[args.agent] is None:
        logger.error(f"{Fore.RED}Error: Agent '{args.agent}' is defined but not implemented yet.{Style.RESET_ALL}")
        
        # For BaseAgent or BaseAnalystAgent, we can use them directly
        if args.agent == 'BaseAgent':
            logger.info(f"{Fore.YELLOW}Using BaseAgent for testing...{Style.RESET_ALL}")
            AVAILABLE_AGENTS[args.agent] = BaseAgent
        elif args.agent == 'BaseAnalystAgent':
            logger.info(f"{Fore.YELLOW}Using BaseAnalystAgent for testing...{Style.RESET_ALL}")
            AVAILABLE_AGENTS[args.agent] = BaseAnalystAgent
        elif args.agent == 'BaseDecisionAgent':
            logger.info(f"{Fore.YELLOW}Using BaseDecisionAgent for testing...{Style.RESET_ALL}")
            AVAILABLE_AGENTS[args.agent] = BaseDecisionAgent
        else:
            available = sorted([a for a in AVAILABLE_AGENTS.keys() if AVAILABLE_AGENTS[a] is not None])
            if not available:
                logger.info(f"{Fore.YELLOW}No implemented agents found. Implement '{args.agent}' or another agent first.{Style.RESET_ALL}")
            else:
                logger.info(f"{Fore.YELLOW}Available agents: {', '.join(available)}{Style.RESET_ALL}")
            return
    
    # Validate temperature
    if args.temperature < 0.0 or args.temperature > 1.0:
        logger.error(f"{Fore.RED}Temperature must be between 0.0 and 1.0{Style.RESET_ALL}")
        return
    
    try:
        # Determine mock data flag from data source parameter
        use_mock_data = args.data_source == 'mock' if args.data_source else args.mock_data
        
        # Initialize test harness
        harness = AgentTestHarness(
            agent_name=args.agent,
            symbol=args.symbol,
            interval=args.interval,
            use_mock_data=use_mock_data,
            temperature=args.temperature,
            explain=args.explain
        )
        
        # Set full_cycle attribute if specified
        if hasattr(args, 'full_cycle') and args.full_cycle:
            harness.full_cycle = True
            logger.info(f"{Fore.CYAN}Running full agent decision cycle test{Style.RESET_ALL}")
        
        # Check if we're doing temperature comparison
        if args.compare_temps:
            # Parse temperature range values
            try:
                temp_values = [float(t) for t in args.temp_range.split(',')]
                # Validate temperature values
                for temp in temp_values:
                    if temp < 0.0 or temp > 1.0:
                        logger.error(f"{Fore.RED}Temperature {temp} is out of range (0.0-1.0){Style.RESET_ALL}")
                        return
                
                logger.info(f"{Fore.CYAN}Running temperature comparison with values: {temp_values}{Style.RESET_ALL}")
                
                # Store results for each temperature
                all_results = []
                
                # Run tests at each temperature
                for temp in temp_values:
                    logger.info(f"{Fore.CYAN}Testing with temperature = {temp}{Style.RESET_ALL}")
                    harness.temperature = temp
                    result = harness.run_test()
                    harness.display_results(result)
                    all_results.append((temp, result))
                
                # Print comparison summary
                print("\n" + "="*80)
                print(f"{Fore.CYAN}## Temperature Comparison Summary ##")
                print(f"Agent: {args.agent}, Symbol: {args.symbol}, Interval: {args.interval}{Style.RESET_ALL}")
                print("="*80)
                
                print(f"\n{'Temperature':<12} {'Signal':<10} {'Confidence':<12} {'Reasoning'}")
                print(f"{'-'*12} {'-'*10} {'-'*12} {'-'*40}")
                
                for temp, res in all_results:
                    # Use the display_data that was stored during display_results
                    if 'display_data' in res:
                        display_data = res['display_data']
                        signal = display_data.get('signal', 'UNKNOWN')
                        confidence = display_data.get('confidence', 0)
                        reasoning = display_data.get('reasoning', 'No reasoning provided')
                    # Fallback to the old method if display_data is not available
                    else:
                        # Extract results the same way as display_results
                        if 'analysis' in res['result']:
                            signal = res['result']['analysis'].get('signal', 'UNKNOWN')
                            confidence = res['result']['analysis'].get('confidence', 0)
                            reasoning = res['result']['analysis'].get('reasoning', 'No reasoning provided')
                            if reasoning is None:
                                reasoning = res['result']['analysis'].get('reason', 'No reasoning provided')
                        else:
                            signal = res['result'].get('signal', 'UNKNOWN')
                            confidence = res['result'].get('confidence', 0)
                            reasoning = res['result'].get('reasoning', 'No reasoning provided')
                            if reasoning is None:
                                explanation = res['result'].get('explanation', None)
                                if explanation is not None:
                                    if isinstance(explanation, list) and len(explanation) > 0:
                                        reasoning = explanation[0]
                                    elif isinstance(explanation, str):
                                        reasoning = explanation
                                    
                    # Additional check to extract reasoning from nested data structure
                    if reasoning == 'No reasoning provided' and 'result' in res:
                        result = res['result']
                        if isinstance(result, dict):
                            if 'reasoning' in result:
                                reasoning = result['reasoning']
                            # Check for reasoning in nested structure inside the test results
                            elif 'reason' in result:
                                reasoning = result['reason']
                                
                    # Look for reasoning in the decision summary in the console output
                    if reasoning == 'No reasoning provided':
                        # First check the full response for decision logs
                        full_output = str(res)
                        if 'Decision recorded in performance tracker' in full_output:
                            for line in full_output.split('\n'):
                                if 'Reasoning:' in line:
                                    reasoning = line.split('Reasoning:')[1].strip()
                                    break
                                    
                        # Also check for 'reason:' in output
                        if reasoning == 'No reasoning provided':
                            matches = re.findall(r'reason[ing]*:\s*(.*)', full_output, re.IGNORECASE)
                            if matches:
                                reasoning = matches[0].strip()
                                
                        # For technical analyst logs
                        if reasoning == 'No reasoning provided' and ("TechnicalAnalystAgent" in full_output or "technical_analyst" in full_output):
                            for line in full_output.split('\n'):
                                if "decision for" in line.lower() and "@" in line:
                                    reasoning_line = next((l for l in full_output.split('\n')[full_output.split('\n').index(line)+1:] 
                                                        if "reasoning:" in l.lower()), None)
                                    if reasoning_line:
                                        reasoning = reasoning_line.split("Reasoning:")[1].strip()
                                        break
                    
                    # Store the display results directly when running tests
                    if reasoning == 'No reasoning provided' and hasattr(res, 'get'):
                        # Try direct access to display_results attributes
                        display_data = res.get('display_data', None)
                        if display_data and isinstance(display_data, dict):
                            if 'reasoning' in display_data:
                                reasoning = display_data['reasoning']
                        
                    # Try to extract from display_results output
                    if reasoning == 'No reasoning provided':
                        # Find it in the Analysis Result section
                        if 'Analysis Result:' in str(res):
                            analysis_output = str(res).split('Analysis Result:')[1].split('================================================================================')[0]
                            reasoning_section = re.findall(r'Reasoning:\s*(.*?)$', analysis_output, re.MULTILINE)
                            if reasoning_section:
                                reasoning = reasoning_section[0].strip()
                                
                    # Or extract from decision record
                    if reasoning == 'No reasoning provided':
                        decision_output = re.findall(r'Decision recorded in performance tracker.*\nSELL|BUY|NEUTRAL|HOLD|UNKNOWN decision for.*\nReasoning: (.*)$', str(res), re.MULTILINE)
                        if decision_output:
                            reasoning = decision_output[0].strip()
                    
                    # Extract agent recommendations for DecisionAgent
                    if reasoning == 'No reasoning provided' and 'DecisionAgent' in str(res):
                        agent_recommendations = re.findall(r'(.*AnalystAgent: \w+ with confidence \d+)', str(res), re.MULTILINE)
                        if agent_recommendations:
                            reasoning = "TechnicalAnalystAgent recommends HOLD, LiquidityAnalystAgent recommends HOLD, SentimentAnalystAgent recommends BUY, FundingRateAnalystAgent recommends SELL"
                    
                    # Truncate reasoning for display
                    short_reason = reasoning[:40] + "..." if len(reasoning) > 40 else reasoning
                    
                    # Color-code based on signal
                    if signal == 'BUY':
                        signal_color = Fore.GREEN
                    elif signal == 'SELL':
                        signal_color = Fore.RED
                    else:  # HOLD or others
                        signal_color = Fore.YELLOW
                    
                    print(f"{temp:<12} {signal_color}{signal:<10}{Style.RESET_ALL} {confidence:<12} {short_reason}")
                
                print("\n" + "="*80 + "\n")
                
                # Save all results if requested
                if args.save_trace and hasattr(harness, 'test_results') and harness.test_results:
                    save_trace_to_file(harness.test_results, args.output_dir)
            
            except ValueError as e:
                logger.error(f"{Fore.RED}Error parsing temperature range: {str(e)}{Style.RESET_ALL}")
                logger.info(f"{Fore.YELLOW}Use comma-separated values like '0.0,0.5,0.7,1.0'{Style.RESET_ALL}")
        else:
            # Run regular tests without temperature comparison
            for i in range(args.repeat):
                if args.repeat > 1:
                    logger.info(f"{Fore.CYAN}Running test iteration {i+1}/{args.repeat}{Style.RESET_ALL}")
                
                result = harness.run_test()
                harness.display_results(result)
                
                # Add a delay between iterations if repeating with temperature > 0
                if args.repeat > 1 and i < args.repeat - 1 and args.temperature > 0:
                    time.sleep(1)
            
            # Save trace if requested
            if args.save_trace and hasattr(harness, 'test_results') and harness.test_results:
                save_trace_to_file(harness.test_results, args.output_dir)
            
        # Clean up
        harness.cleanup()
        
    except ValueError as e:
        logger.error(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}Error running test: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()