#!/usr/bin/env python3
"""
aGENtrader v2 Individual Agent Test Utility

This script allows testing of individual analyst agents in isolation with:
- Controlled input data (real or mock)
- Full visibility into decision processes
- Deterministic testing for reproducibility
- Flexible agent selection via CLI

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
import time
import logging
from datetime import datetime
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
        self.agent_name = agent_name
        self.symbol = symbol
        self.interval = interval
        self.use_mock_data = use_mock_data
        self.temperature = temperature
        self.explain = explain
        self.data_override = data_override or {}
        
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
            agent = self.agent_class(analyst_results=analyst_results)
            
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
        start_time = time.time()
        
        # Create the agent
        agent = self._create_agent()
        
        # Record the timestamp
        timestamp = datetime.now().isoformat()
        
        # Get the analysis method for the agent
        if self.agent_name == 'DecisionAgent':
            analysis_method = agent.make_decision
        else:
            analysis_method = agent.analyze
        
        # Prepare market data if needed
        if self.agent_name != 'DecisionAgent':
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
            # For decision agent, we don't need market data directly
            logger.info(f"{Fore.CYAN}Running {self.agent_name} decision making...{Style.RESET_ALL}")
            result = analysis_method()
        
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
        
        return test_record
    
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
        signal = analysis.get('signal', 'UNKNOWN')
        confidence = analysis.get('confidence', 0)
        reasoning = analysis.get('reasoning', 'No reasoning provided')
        
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test individual agents in isolation')
    
    parser.add_argument('--agent', type=str, help='Agent class name to test')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading symbol (e.g., BTC/USDT)')
    parser.add_argument('--interval', type=str, default='4h', help='Time interval (e.g., 1h, 4h, 1d)')
    parser.add_argument('--mock-data', action='store_true', help='Use mock data instead of real API')
    parser.add_argument('--temperature', type=float, default=0.0, help='LLM temperature (0.0-1.0)')
    parser.add_argument('--explain', action='store_true', help='Show detailed explanation of prompts and responses')
    parser.add_argument('--repeat', type=int, default=1, help='Run N iterations to observe variability')
    parser.add_argument('--list', action='store_true', help='List available agent classes')
    
    args = parser.parse_args()
    
    # Show list of agents if requested or if no agent is specified
    if args.list or not args.agent:
        list_available_agents()
        if not args.agent:
            parser.error('--agent is required unless --list is specified')
    
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
        # Initialize test harness
        harness = AgentTestHarness(
            agent_name=args.agent,
            symbol=args.symbol,
            interval=args.interval,
            use_mock_data=args.mock_data,
            temperature=args.temperature,
            explain=args.explain
        )
        
        # Run the tests
        for i in range(args.repeat):
            if args.repeat > 1:
                logger.info(f"{Fore.CYAN}Running test iteration {i+1}/{args.repeat}{Style.RESET_ALL}")
            
            result = harness.run_test()
            harness.display_results(result)
            
            # Add a delay between iterations if repeating with temperature > 0
            if args.repeat > 1 and i < args.repeat - 1 and args.temperature > 0:
                time.sleep(1)
        
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