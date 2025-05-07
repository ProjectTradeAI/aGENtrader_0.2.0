"""
aGENtrader v2 Base Agent

This module provides base classes for the agent architecture in aGENtrader v2.
These classes define the standard interfaces and common functionality for all agents.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

# Try to import yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not installed. Config loading will use fallback methods.")

# Import sanity check utilities
try:
    from utils.sanity_check import sanitize_agent_output, filter_passed_sanity_checks
    SANITY_CHECKS_AVAILABLE = True
except ImportError:
    SANITY_CHECKS_AVAILABLE = False
    logging.warning("Sanity check utilities not available. Falling back to basic validation.")

# Configure logging
logger = logging.getLogger(__name__)

class AgentInterface(ABC):
    """
    Base interface for all agents in the system.
    
    This abstract base class defines the methods that all agents must implement.
    """
    
    @abstractmethod
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration.
        
        Returns:
            Dictionary containing agent configuration
        """
        pass
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run the agent's main functionality.
        
        Returns:
            Result dictionary
        """
        pass

class BaseAgent:
    """BaseAgent for aGENtrader v0.2.2"""
    
    def __init__(self, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name of the agent
        """
        self.version = "v0.2.2"
        self.agent_name = agent_name
        self.name = agent_name  # For backward compatibility
        self.description = "Base analyst agent implementation"
        
    def build_error_response(self, error_code: str, error_message: str) -> Dict[str, Any]:
        """
        Build a standardized error response.
        
        Args:
            error_code: Error code string
            error_message: Error message description
            
        Returns:
            Error response dictionary
        """
        response = {
            "error": True,
            "error_code": error_code,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "passed_sanity_check": False
        }
        return response
        
    def sanitize_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply sanity checks to the agent output and add passed_sanity_check flag.
        
        Args:
            output: The agent output dictionary
            
        Returns:
            Sanitized output with passed_sanity_check flag
        """
        # Add agent name and timestamp if not present
        if 'agent_name' not in output:
            output['agent_name'] = self.agent_name
            
        if 'timestamp' not in output:
            output['timestamp'] = datetime.now().isoformat()
            
        # If output already has passed_sanity_check, respect it
        if 'passed_sanity_check' in output:
            return output
            
        # Check for error response, which never passes sanity check
        if output.get('error', False):
            output['passed_sanity_check'] = False
            return output
            
        # If sanity check utilities are available, use them
        if SANITY_CHECKS_AVAILABLE:
            try:
                return sanitize_agent_output(output)
            except Exception as e:
                logger.warning(f"Error during sanity check for {self.agent_name}: {str(e)}")
                output['passed_sanity_check'] = False
                return output
        else:
            # Basic sanity check if utilities aren't available
            if not output:
                output['passed_sanity_check'] = False
                return output
                
            # Ensure recommendation exists if this is a decision agent
            if 'recommendation' in output:
                recommendation = output.get('recommendation', {})
                if not isinstance(recommendation, dict) or not recommendation:
                    output['passed_sanity_check'] = False
                    return output
                    
                action = recommendation.get('action')
                confidence = recommendation.get('confidence')
                
                if not action or not confidence:
                    output['passed_sanity_check'] = False
                    return output
                    
                # Check confidence is a number and in valid range
                try:
                    confidence_value = float(confidence)
                    if confidence_value < 0 or confidence_value > 100:
                        output['passed_sanity_check'] = False
                        return output
                except (ValueError, TypeError):
                    output['passed_sanity_check'] = False
                    return output
            
            # If we get here, basic checks passed
            output['passed_sanity_check'] = True
            return output
    
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration.
        
        Returns:
            Configuration dictionary
        """
        # Try to load agent-specific configuration
        return self.load_config_section(self.agent_name)
        
    def load_config_section(self, section_name: str) -> Dict[str, Any]:
        """
        Load a specific section from the configuration file.
        
        Args:
            section_name: The name of the configuration section to load
            
        Returns:
            Configuration dictionary for the specified section
        """
        try:
            config_data = self.load_config_file()
            
            # Check if the section exists at the root level
            if section_name in config_data:
                return config_data.get(section_name, {})
                
            # Check if it's in the agents section
            if 'agents' in config_data and section_name in config_data['agents']:
                return config_data['agents'].get(section_name, {})
                
            # For agent names that might have different formats (e.g., portfolio_manager vs portfolio_manager_agent)
            if 'agents' in config_data:
                # Try with _agent suffix removed
                if section_name.endswith('_agent'):
                    base_name = section_name[:-6]  # Remove '_agent'
                    if base_name in config_data['agents']:
                        return config_data['agents'].get(base_name, {})
                
                # Try with shortened names
                for key in config_data['agents'].keys():
                    if section_name.lower().startswith(key.lower()):
                        return config_data['agents'].get(key, {})
                        
            # Return empty dict if no matching section found
            logger.warning(f"Configuration section '{section_name}' not found")
            return {}
            
        except Exception as e:
            logger.warning(f"Error loading config section '{section_name}': {str(e)}")
            return {}
            
    def load_config_file(self) -> Dict[str, Any]:
        """
        Load the entire configuration file.
        
        Returns:
            Complete configuration dictionary
        """
        # Get configuration file path
        config_path = self.get_config_path()
        
        # If file doesn't exist, return empty dict
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found at {config_path}")
            return {}
            
        try:
            # Try to load with YAML if available
            if YAML_AVAILABLE:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                # Try JSON as fallback
                try:
                    with open(config_path, 'r') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    # If not valid JSON, try parsing as simple key-value pairs
                    config = {}
                    with open(config_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                try:
                                    key, value = line.split('=', 1)
                                    config[key.strip()] = value.strip()
                                except ValueError:
                                    pass
                    return config
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
            return {}
    
    def get_config_path(self) -> str:
        """
        Get the path to the configuration file.
        
        Returns:
            Path to the configuration file
        """
        # Try to determine project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Check for configuration in known locations
        potential_paths = [
            os.path.join(project_root, "config", "settings.yaml"),
            os.path.join(project_root, "config", "settings.yml"),
            os.path.join(project_root, "config", "config.yaml"),
            os.path.join(project_root, "config", "config.yml"),
            os.path.join(project_root, "settings.yaml"),
            os.path.join(project_root, "config.yaml")
        ]
        
        # Return the first path that exists
        for path in potential_paths:
            if os.path.exists(path):
                return path
                
        # Default to settings.yaml in the config directory
        return os.path.join(project_root, "config", "settings.yaml")
        
    def run(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Run the analyst agent with the specified parameters.
        
        This method serves as a wrapper for the analyze method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        if not symbol:
            symbol = "BTC/USDT"  # Default symbol
            
        if not interval:
            interval = "1h"  # Default interval
            
        return self._run(symbol=symbol, interval=interval, **kwargs)
        
    def _run(self, symbol: Optional[str] = None, interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Run the analyst agent's analyze method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results with sanity checks applied
        """
        # Get the analysis results
        result = self.analyze(symbol=symbol, interval=interval, **kwargs)
        
        # Apply sanity checks to the result
        return self.sanitize_output(result)
    
    def analyze(self, symbol: Optional[str] = None, market_data: Optional[Dict[str, Any]] = None, 
                interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and generate insights.
        
        This method should be overridden by subclasses.
        
        Args:
            symbol: Trading symbol
            market_data: Pre-fetched market data (optional)
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        return self.build_error_response(
            "NOT_IMPLEMENTED",
            f"Agent {self.name} does not implement analyze()"
        )
        
    def _fetch_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch market data for analysis.
        
        This method should be overridden by subclasses.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Market data
        """
        return {}

class BaseAnalystAgent(BaseAgent):
    """
    Base class for analyst agents that analyze market data.
    
    These agents perform specialized analysis on market data and generate insights.
    """
    
    def __init__(self, agent_name: str = "base_analyst"):
        """
        Initialize a base analyst agent.
        
        Args:
            agent_name: Name of the agent
        """
        super().__init__(agent_name)
        self.version = "v0.2.2"
        self.description = "Base analyst agent implementation"
        
    def analyze(self, symbol: Optional[str] = None, market_data: Optional[Dict[str, Any]] = None, 
                interval: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze market data and generate insights.
        
        This method should be overridden by subclasses.
        
        Args:
            symbol: Trading symbol
            market_data: Pre-fetched market data (optional)
            interval: Time interval
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        return self.build_error_response(
            "NOT_IMPLEMENTED",
            f"Agent {self.name} does not implement analyze()"
        )
        
class DecisionAgentInterface(AgentInterface):
    """
    Interface for decision-making agents that determine trading actions.
    
    These agents combine multiple analysis results to make trading decisions.
    """
    
    @abstractmethod
    def make_decision(self, symbol: str, interval: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make a trading decision based on multiple analyses.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Decision result
        """
        pass

class BaseDecisionAgent(BaseAgent, DecisionAgentInterface):
    """
    Base class for decision-making agents that determine trading actions.
    
    These agents combine multiple analysis results to make trading decisions.
    """
    
    def __init__(self, agent_name: str = "base_decision"):
        """
        Initialize a base decision agent.
        
        Args:
            agent_name: Name of the agent
        """
        super().__init__(agent_name)
        self.description = "Base decision agent implementation"
        
        # Load agent weights from config
        config = self.get_agent_config()
        self.confidence_threshold = config.get("confidence_threshold", 70)
        
    def run(self, symbol: str, interval: str, analyses: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Run the decision agent with the specified parameters.
        
        This method serves as a wrapper for the make_decision method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            **kwargs: Additional parameters
            
        Returns:
            Decision results
        """
        return self._run(symbol=symbol, interval=interval, analyses=analyses, **kwargs)
        
    def _run(self, symbol: str, interval: str, analyses: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Run the decision agent's make_decision method.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            **kwargs: Additional parameters
            
        Returns:
            Decision results with sanity checks applied
        """
        # Filter analyses to include only those that passed sanity checks
        if SANITY_CHECKS_AVAILABLE:
            filtered_analyses = filter_passed_sanity_checks(analyses)
            if not filtered_analyses:
                logger.warning("All analyses failed sanity checks. Decision making may be unreliable.")
            else:
                analyses = filtered_analyses
                logger.info(f"Using {len(analyses)} analyses that passed sanity checks")
        
        # Get the decision results
        result = self.make_decision(symbol=symbol, interval=interval, analyses=analyses)
        
        # Apply sanity checks to the result
        return self.sanitize_output(result)
    
    def make_decision(self, symbol: str, interval: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make a trading decision based on multiple analyses.
        
        This method should be overridden by subclasses.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            analyses: List of analysis results from different agents
            
        Returns:
            Decision result
        """
        return self.build_error_response(
            "NOT_IMPLEMENTED", 
            f"Agent {self.name} does not implement make_decision()"
        )

class ExecutionAgentInterface(AgentInterface):
    """
    Interface for execution agents that execute trading actions.
    
    These agents interact with exchange APIs to place and manage orders.
    """
    
    @abstractmethod
    def execute_trade(self, symbol: str, side: str, quantity: float, price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute a trade on the exchange.
        
        Args:
            symbol: Trading symbol
            side: Trade side (buy or sell)
            quantity: Quantity to trade
            price: Price to trade at (optional for market orders)
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
            **kwargs: Additional parameters
            
        Returns:
            Cancellation result
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Get a list of open orders.
        
        Args:
            symbol: Trading symbol (optional)
            **kwargs: Additional parameters
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get current position for a symbol.
        
        Args:
            symbol: Trading symbol
            **kwargs: Additional parameters
            
        Returns:
            Position information
        """
        pass