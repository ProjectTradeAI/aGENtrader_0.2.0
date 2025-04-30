"""
aGENtrader v2 Base Agent Implementations

This module implements the base classes for all agent types
defined in agent_interface.py.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Callable

from agents.agent_interface import (
    AgentInterface,
    AnalystAgentInterface,
    DecisionAgentInterface,
    ExecutionAgentInterface
)

logger = logging.getLogger('agentrader.agents')

class BaseAgent(AgentInterface):
    """
    Base implementation of the AgentInterface.
    
    This class provides common functionality for all agent types.
    """
    
    def __init__(
        self,
        name: str = "BaseAgent",
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.last_run_time = None
        self.run_count = 0
        self.run_history = []
        
        # Set the agent configuration (legacy method for backward compatibility)
        self.agent_config = self.get_agent_config()
        
        # Extract common configuration
        self.log_level = self.config.get('log_level', logging.INFO)
        
        # Initialize logger
        self._setup_logging()
        
        self.logger.debug(f"Initialized {self.name}")
        
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get agent-specific configuration.
        
        This method is provided for backward compatibility with existing agent implementations.
        New implementations should use self.config directly.
        
        Returns:
            Dictionary with agent configuration
        """
        # Load from config, or use defaults
        return {
            # Common defaults for backward compatibility
            "name": self.name,
            "log_level": self.log_level,
            "provider": "mistral",  # Default LLM provider
            "model": "mistral-medium",  # Default model
            "temperature": 0.7,  # Default temperature
            # Additional configurations from self.config
            **self.config
        }
        
    def _setup_logging(self):
        """Set up logging for this agent."""
        self.logger = logging.getLogger(f"agentrader.agents.{self.name}")
        self.logger.setLevel(self.log_level)
        
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the agent's core functionality.
        
        This base implementation just logs and returns a timestamp.
        Subclasses should override this method.
        
        Returns:
            Dictionary with the agent's output
        """
        self.logger.debug(f"Running {self.name}")
        start_time = time.time()
        self.last_run_time = datetime.now().isoformat()
        self.run_count += 1
        
        # Call the subclass implementation
        try:
            result = self._run(**kwargs)
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {str(e)}", exc_info=True)
            result = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.last_run_time
            }
        
        # Add timing information
        elapsed = time.time() - start_time
        result.update({
            'agent': self.name,
            'elapsed_time': elapsed,
            'timestamp': self.last_run_time
        })
        
        # Store in history
        self.run_history.append({
            'timestamp': self.last_run_time,
            'elapsed': elapsed,
            'result': result
        })
        
        # Limit history length
        max_history = self.config.get('max_history', 100)
        if len(self.run_history) > max_history:
            self.run_history = self.run_history[-max_history:]
            
        return result
        
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Internal implementation of the run method.
        
        Subclasses should override this method.
        
        Returns:
            Dictionary with the agent's output
        """
        return {
            'status': 'info',
            'message': f"{self.name} ran with {kwargs}",
            'timestamp': self.last_run_time
        }
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            'name': self.name,
            'run_count': self.run_count,
            'last_run_time': self.last_run_time,
            'config': self.config
        }
        
    def validate_output_format(self, output: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that the output dictionary contains all required keys.
        
        Args:
            output: Output dictionary to validate
            required_keys: List of required key names
            
        Returns:
            True if all required keys are present, False otherwise
        """
        missing_keys = [key for key in required_keys if key not in output]
        if missing_keys:
            self.logger.warning(
                f"Output from {self.name} is missing required keys: {missing_keys}"
            )
            return False
            
        return True

class BaseAnalystAgent(BaseAgent, AnalystAgentInterface):
    """
    Base implementation of the AnalystAgentInterface.
    
    This class provides common functionality for all analyst agents.
    """
    
    def __init__(
        self,
        name: str = "BaseAnalystAgent",
        config: Optional[Dict[str, Any]] = None,
        data_provider: Optional[Any] = None,
        symbol: str = "BTC/USDT",
        interval: str = "1h",
        llm_client: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize the base analyst agent.
        
        Args:
            name: Agent name
            config: Configuration dictionary
            data_provider: Data provider instance
            symbol: Trading symbol
            interval: Analysis interval
            llm_client: LLM client instance
        """
        # Call the parent constructor
        super().__init__(name=name, config=config, **kwargs)
        
        # Set analyst-specific attributes
        self.data_provider = data_provider
        self.symbol = symbol
        self.interval = interval
        self.llm_client = llm_client
        
        # Default signal parameters
        self.signals = ["BUY", "SELL", "HOLD"]
        self.confidence_range = (0, 100)
        
        # Track last analysis
        self.last_signal = None
        self.last_confidence = None
        self.last_analysis = None
        
    def _run(self, market_data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Internal implementation of the run method.
        
        For analyst agents, this calls the analyze method.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with analysis results
        """
        # If market_data is not provided, try to fetch it if we have a data provider
        if market_data is None and self.data_provider is not None:
            self.logger.debug(f"Fetching market data for {self.symbol} ({self.interval})")
            try:
                market_data = self._fetch_market_data()
            except Exception as e:
                self.logger.error(f"Error fetching market data: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Could not fetch market data: {str(e)}",
                    'timestamp': self.last_run_time
                }
                
        if market_data is None:
            self.logger.error("No market data provided and no data provider available")
            return {
                'status': 'error',
                'error': "No market data provided and no data provider available",
                'timestamp': self.last_run_time
            }
            
        # Call the analyze method
        analysis_result = self.analyze(market_data, **kwargs)
        
        # Store the result
        if 'signal' in analysis_result:
            self.last_signal = analysis_result['signal']
        if 'confidence' in analysis_result:
            self.last_confidence = analysis_result['confidence']
        self.last_analysis = analysis_result
        
        return analysis_result
        
    def _fetch_market_data(self) -> Dict[str, Any]:
        """
        Fetch market data using the data provider.
        
        Returns:
            Dictionary containing market data
        """
        if self.data_provider is None:
            raise ValueError("No data provider available")
            
        # Get current price
        current_price = self.data_provider.get_current_price(self.symbol.replace('/', ''))
        
        # Fetch OHLCV data
        ohlcv_data = self.data_provider.fetch_ohlcv(
            symbol=self.symbol.replace('/', ''),
            interval=self.interval,
            limit=100  # Default to 100 candles
        )
        
        # Fetch market depth (order book)
        try:
            order_book = self.data_provider.fetch_market_depth(
                symbol=self.symbol.replace('/', ''),
                limit=100  # Default to 100 levels
            )
        except Exception as e:
            self.logger.warning(f"Could not fetch order book: {str(e)}")
            order_book = None
            
        # Build the market data dictionary
        market_data = {
            'symbol': self.symbol,
            'interval': self.interval,
            'current_price': current_price,
            'ohlcv': ohlcv_data,
            'order_book': order_book,
            'timestamp': datetime.now().isoformat()
        }
        
        return market_data
        
    def analyze(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and return insights.
        
        This base implementation returns a neutral HOLD signal.
        Subclasses should override this method.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dictionary with analysis results
        """
        self.logger.info(f"Base analysis for {self.symbol} ({self.interval})")
        
        return {
            'signal': 'HOLD',
            'confidence': 50,
            'reasoning': f"Base analyst agent does not implement any analysis logic.",
            'data': {}
        }
        
    def validate_analysis_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that the analysis result has the required format.
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            True if the result is valid, False otherwise
        """
        required_keys = ['signal', 'confidence', 'reasoning']
        if not self.validate_output_format(result, required_keys):
            return False
            
        # Check signal value
        if result['signal'] not in self.signals:
            self.logger.warning(
                f"Invalid signal value: {result['signal']} "
                f"(expected one of {self.signals})"
            )
            return False
            
        # Check confidence range
        confidence = result['confidence']
        min_conf, max_conf = self.confidence_range
        if not min_conf <= confidence <= max_conf:
            self.logger.warning(
                f"Confidence value out of range: {confidence} "
                f"(expected between {min_conf} and {max_conf})"
            )
            return False
            
        return True

class BaseDecisionAgent(BaseAgent, DecisionAgentInterface):
    """
    Base implementation of the DecisionAgentInterface.
    
    This class provides common functionality for all decision agents.
    """
    
    def __init__(
        self,
        name: str = "BaseDecisionAgent",
        config: Optional[Dict[str, Any]] = None,
        signal_weights: Optional[Dict[str, float]] = None,
        confidence_threshold: int = 60,
        **kwargs
    ):
        """
        Initialize the base decision agent.
        
        Args:
            name: Agent name
            config: Configuration dictionary
            signal_weights: Dictionary mapping analyst names to weight values
            confidence_threshold: Minimum confidence threshold for decisions
        """
        # Call the parent constructor
        super().__init__(name=name, config=config, **kwargs)
        
        # Set decision-specific attributes
        self.signal_weights = signal_weights or {}
        self.confidence_threshold = confidence_threshold
        
        # Default signals
        self.signals = ["BUY", "SELL", "HOLD"]
        
        # Track last decision
        self.last_decision = None
        
    def _run(self, analyst_results: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Internal implementation of the run method.
        
        For decision agents, this calls the make_decision method.
        
        Args:
            analyst_results: Dictionary containing outputs from analyst agents
            
        Returns:
            Dictionary with decision results
        """
        if analyst_results is None:
            self.logger.error("No analyst results provided")
            return {
                'status': 'error',
                'error': "No analyst results provided",
                'timestamp': self.last_run_time
            }
            
        # Call the make_decision method
        decision_result = self.make_decision(analyst_results, **kwargs)
        
        # Store the result
        self.last_decision = decision_result
        
        return decision_result
        
    def make_decision(self, analyst_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Make a trading decision based on analyst results.
        
        This base implementation uses a weighted voting mechanism.
        Subclasses should override this method for more sophisticated approaches.
        
        Args:
            analyst_results: Dictionary containing outputs from analyst agents
            
        Returns:
            Dictionary with decision results
        """
        self.logger.info("Making decision based on analyst results")
        
        # Default weights if not specified
        analyst_types = list(analyst_results.keys())
        default_weight = 1.0 / len(analyst_types) if analyst_types else 1.0
        
        # Initialize vote counters for each signal
        signal_votes = {signal: 0.0 for signal in self.signals}
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        # Process each analyst's result
        contributions = {}
        for analyst_type, result in analyst_results.items():
            if not isinstance(result, dict) or 'signal' not in result or 'confidence' not in result:
                self.logger.warning(f"Invalid result format from {analyst_type}")
                continue
                
            signal = result['signal']
            if signal not in self.signals:
                self.logger.warning(f"Invalid signal {signal} from {analyst_type}")
                continue
                
            confidence = result['confidence']
            weight = self.signal_weights.get(analyst_type, default_weight)
            
            # Calculate weighted vote
            weighted_vote = (confidence / 100.0) * weight
            signal_votes[signal] += weighted_vote
            total_weighted_confidence += weighted_vote
            total_weight += weight
            
            # Record contribution
            contributions[analyst_type] = {
                'signal': signal,
                'confidence': confidence,
                'weight': weight,
                'contribution': weighted_vote
            }
            
        # No valid votes
        if total_weight == 0:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reasoning': "No valid analyst signals available",
                'contributions': {}
            }
            
        # Normalize and find the highest signal
        normalized_votes = {
            signal: votes / total_weight 
            for signal, votes in signal_votes.items()
        }
        
        best_signal = max(normalized_votes, key=normalized_votes.get)
        confidence = int(normalized_votes[best_signal] * 100)
        
        # Check if confidence is below threshold
        if confidence < self.confidence_threshold:
            best_signal = 'HOLD'
            reasoning = f"Confidence too low ({confidence}), defaulting to HOLD"
        else:
            reasoning = f"Weighted consensus for {best_signal} with {confidence}% confidence"
            
        return {
            'signal': best_signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'contributions': contributions,
            'vote_distribution': normalized_votes
        }
        
    def validate_decision_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that the decision result has the required format.
        
        Args:
            result: Decision result dictionary
            
        Returns:
            True if the result is valid, False otherwise
        """
        required_keys = ['signal', 'confidence', 'reasoning', 'contributions']
        if not self.validate_output_format(result, required_keys):
            return False
            
        # Check signal value
        if result['signal'] not in self.signals:
            self.logger.warning(
                f"Invalid signal value: {result['signal']} "
                f"(expected one of {self.signals})"
            )
            return False
            
        # Check confidence range
        confidence = result['confidence']
        if not 0 <= confidence <= 100:
            self.logger.warning(
                f"Confidence value out of range: {confidence} "
                f"(expected between 0 and 100)"
            )
            return False
            
        return True