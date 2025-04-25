"""
Trading Agents Module

Contains specialized agent definitions for market analysis and trading decisions.
These agents can be imported and used in various test scenarios.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Union

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Warning: AutoGen not available. Agent functionality will be limited.")

from agents.database_retrieval_tool import (
    get_recent_market_data,
    get_market_data_range,
    get_latest_price,
    get_market_summary,
    get_price_history,
    calculate_moving_average,
    calculate_rsi,
    find_support_resistance,
    detect_patterns,
    calculate_volatility,
    CustomJSONEncoder
)

# Configure logging
logger = logging.getLogger("trading_agents")

class TradingAgentFactory:
    """Factory for creating specialized trading agents"""
    
    @staticmethod
    def create_market_analyst(config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a market analyst agent specializing in technical analysis
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            AssistantAgent instance or None if AutoGen is not available
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create market analyst agent.")
            return None
        
        # Default configuration
        default_config = {
            "name": "MarketAnalyst",
            "system_message": """You are a Market Analyst specialized in cryptocurrency technical analysis.
Your expertise includes:
1. Interpreting price charts and identifying patterns
2. Analyzing market trends using technical indicators
3. Identifying support and resistance levels
4. Evaluating market sentiment and volatility

You can access historical market data for analysis and provide clear, data-driven 
insights to help with trading decisions. Always base your analysis on the data provided,
and clearly explain your reasoning.

Always format your response in a structured way, with clear sections for:
- Market Trend Analysis
- Technical Indicators
- Support/Resistance Levels
- Pattern Recognition
- Trading Recommendation (if any)
"""
        }
        
        # Merge configurations
        if config:
            for key, value in config.items():
                default_config[key] = value
        
        # Get LLM config from default_config if available, otherwise use default values
        llm_config = default_config.get("llm_config", {
            "temperature": 0.1,
            "request_timeout": 120,
            "config_list": [{"model": "gpt-3.5-turbo"}]
        })
        
        # Create the agent
        agent = AssistantAgent(
            name=default_config["name"],
            system_message=default_config["system_message"],
            llm_config=llm_config
        )
        
        return agent
    
    @staticmethod
    def create_strategy_advisor(config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a strategy advisor agent specializing in trading strategy
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            AssistantAgent instance or None if AutoGen is not available
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create strategy advisor agent.")
            return None
        
        # Default configuration
        default_config = {
            "name": "StrategyAdvisor",
            "system_message": """You are a Strategy Advisor specialized in cryptocurrency trading strategies.
Your expertise includes:
1. Developing trading strategies based on technical analysis
2. Risk management and position sizing
3. Entry and exit point identification
4. Managing trading psychology

Your role is to evaluate market analysis and develop concrete trading strategies
with clear entry/exit points, position sizes, and risk management approaches.
Always consider the risk-reward ratio and provide specific actionable advice.

Always format your recommendations in a structured way, with clear sections for:
- Strategy Summary
- Entry Points
- Exit Points
- Risk Management
- Position Size
- Key Indicators to Monitor
"""
        }
        
        # Merge configurations
        if config:
            for key, value in config.items():
                default_config[key] = value
        
        # Get LLM config from default_config if available, otherwise use default values
        llm_config = default_config.get("llm_config", {
            "temperature": 0.2,
            "request_timeout": 120,
            "config_list": [{"model": "gpt-3.5-turbo"}]
        })
        
        # Create the agent
        agent = AssistantAgent(
            name=default_config["name"],
            system_message=default_config["system_message"],
            llm_config=llm_config
        )
        
        return agent
    
    @staticmethod
    def create_portfolio_manager(config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a portfolio manager agent specializing in portfolio optimization
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            AssistantAgent instance or None if AutoGen is not available
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create portfolio manager agent.")
            return None
        
        # Default configuration
        default_config = {
            "name": "PortfolioManager",
            "system_message": """You are a Portfolio Manager specialized in cryptocurrency portfolio optimization.
Your expertise includes:
1. Portfolio allocation and rebalancing
2. Risk distribution across assets
3. Long-term investment strategies
4. Performance tracking and analysis

Your role is to evaluate trading recommendations in the context of an overall portfolio,
ensuring proper diversification, risk management, and alignment with investment goals.
You should provide guidance on how to integrate specific trades into the broader portfolio strategy.

Always format your portfolio advice in a structured way, with clear sections for:
- Portfolio Impact Analysis
- Allocation Recommendation
- Risk Assessment
- Rebalancing Strategy
- Long-term Considerations
"""
        }
        
        # Merge configurations
        if config:
            for key, value in config.items():
                default_config[key] = value
        
        # Get LLM config from default_config if available, otherwise use default values
        llm_config = default_config.get("llm_config", {
            "temperature": 0.2,
            "request_timeout": 120,
            "config_list": [{"model": "gpt-3.5-turbo"}]
        })
        
        # Create the agent
        agent = AssistantAgent(
            name=default_config["name"],
            system_message=default_config["system_message"],
            llm_config=llm_config
        )
        
        return agent
    
    @staticmethod
    def create_risk_manager(config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a risk manager agent specializing in risk assessment
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            AssistantAgent instance or None if AutoGen is not available
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create risk manager agent.")
            return None
        
        # Default configuration
        default_config = {
            "name": "RiskManager",
            "system_message": """You are a Risk Manager specialized in cryptocurrency trading risk assessment.
Your expertise includes:
1. Identifying potential risks in trading strategies
2. Calculating risk-reward ratios
3. Setting appropriate stop-loss and take-profit levels
4. Evaluating market volatility and its impact on risk

Your role is to critically evaluate trading strategies from a risk perspective,
ensuring that potential losses are limited and in line with overall risk tolerance.
You should highlight potential risks and suggest modifications to mitigate them.

Always format your risk assessment in a structured way, with clear sections for:
- Risk Identification
- Risk Quantification
- Stop-Loss Recommendations
- Volatility Assessment
- Risk Mitigation Strategies
"""
        }
        
        # Merge configurations
        if config:
            for key, value in config.items():
                default_config[key] = value
        
        # Get LLM config from default_config if available, otherwise use default values
        llm_config = default_config.get("llm_config", {
            "temperature": 0.1,
            "request_timeout": 120,
            "config_list": [{"model": "gpt-3.5-turbo"}]
        })
        
        # Create the agent
        agent = AssistantAgent(
            name=default_config["name"],
            system_message=default_config["system_message"],
            llm_config=llm_config
        )
        
        return agent
    
    @staticmethod
    def create_decision_integrator(config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a decision integrator agent that combines insights from other agents
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            AssistantAgent instance or None if AutoGen is not available
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create decision integrator agent.")
            return None
        
        # Default configuration
        default_config = {
            "name": "DecisionIntegrator",
            "system_message": """You are a Decision Integrator specialized in synthesizing diverse analyses and recommendations.
Your expertise includes:
1. Combining insights from multiple sources
2. Weighing conflicting recommendations
3. Making clear, decisive conclusions
4. Justifying decisions with data-backed reasoning

Your role is to review inputs from market analysts, strategy advisors, portfolio managers,
and risk managers, then synthesize their insights into a cohesive, actionable trading decision.
You should identify areas of consensus and resolve conflicts with clear reasoning.

Always format your decision in a structured way, with clear sections for:
- Decision Summary (BUY, SELL, or HOLD with confidence level)
- Key Factors Considered
- Areas of Consensus
- Resolved Conflicts
- Action Plan
- Risk Assessment
"""
        }
        
        # Merge configurations
        if config:
            for key, value in config.items():
                default_config[key] = value
        
        # Get LLM config from default_config if available, otherwise use default values
        llm_config = default_config.get("llm_config", {
            "temperature": 0.1,
            "request_timeout": 120,
            "config_list": [{"model": "gpt-3.5-turbo"}]
        })
        
        # Create the agent
        agent = AssistantAgent(
            name=default_config["name"],
            system_message=default_config["system_message"],
            llm_config=llm_config
        )
        
        return agent
    
    @staticmethod
    def create_user_proxy(
        name: str = "TradingSystem",
        human_input_mode: str = "NEVER",
        max_consecutive_auto_reply: int = 10,
        functions: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """
        Create a user proxy agent for facilitating agent conversations
        
        Args:
            name: Name of the user proxy
            human_input_mode: Human input mode (e.g., "NEVER", "ALWAYS")
            max_consecutive_auto_reply: Maximum consecutive auto replies
            functions: List of functions to expose to agents
            
        Returns:
            UserProxyAgent instance or None if AutoGen is not available
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create user proxy agent.")
            return None
        
        # Define default functions for market data retrieval
        default_functions = [
            {
                "name": "get_recent_market_data",
                "description": "Get recent market data for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of records to retrieve"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_data_range",
                "description": "Get market data for a specific date range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., 1m, 15m, 1h, 1d)"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_latest_price",
                "description": "Get the latest price for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_summary",
                "description": "Get a summary of market data for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to include in summary"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "calculate_moving_average",
                "description": "Calculate moving average for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for moving average calculation"
                        },
                        "ma_type": {
                            "type": "string",
                            "description": "Type of moving average (SMA, EMA)"
                        }
                    },
                    "required": ["symbol", "period"]
                }
            },
            {
                "name": "calculate_rsi",
                "description": "Calculate Relative Strength Index for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for RSI calculation"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "find_support_resistance",
                "description": "Find support and resistance levels for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for calculation"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "detect_patterns",
                "description": "Detect common chart patterns for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to consider"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "calculate_volatility",
                "description": "Calculate volatility for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to consider"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        ]
        
        # Format function specifications for OpenAI API
        function_specs = []
        for func in (functions or default_functions):
            # Ensure the function spec has the required 'type': 'function'
            function_spec = {
                "type": "function",
                "function": func
            }
            function_specs.append(function_spec)
            
        # Create function map for execution
        function_map = {
            "get_recent_market_data": get_recent_market_data,
            "get_market_data_range": get_market_data_range,
            "get_latest_price": get_latest_price,
            "get_market_summary": get_market_summary,
            "calculate_moving_average": calculate_moving_average,
            "calculate_rsi": calculate_rsi,
            "find_support_resistance": find_support_resistance,
            "detect_patterns": detect_patterns,
            "calculate_volatility": calculate_volatility
        }
        
        # Create the agent
        agent = UserProxyAgent(
            name=name,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            code_execution_config={"use_docker": False},
            function_map=function_map
        )
        
        return agent
    
    @staticmethod
    def get_integration_dict(llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a complete integration dictionary for AutoGen
        
        Args:
            llm_config: Optional LLM configuration to use
            
        Returns:
            Dictionary with function_map, llm_config, and function_specs
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot create integration dictionary.")
            return {}
        
        # Define default functions for market data retrieval
        default_functions = [
            {
                "name": "get_recent_market_data",
                "description": "Get recent market data for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of records to retrieve"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_data_range",
                "description": "Get market data for a specific date range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., 1m, 15m, 1h, 1d)"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_latest_price",
                "description": "Get the latest price for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_summary",
                "description": "Get a summary of market data for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to include in summary"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "calculate_moving_average",
                "description": "Calculate moving average for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for moving average calculation"
                        },
                        "ma_type": {
                            "type": "string",
                            "description": "Type of moving average (SMA, EMA)"
                        }
                    },
                    "required": ["symbol", "period"]
                }
            },
            {
                "name": "calculate_rsi",
                "description": "Calculate Relative Strength Index for a symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTCUSDT)"
                        },
                        "period": {
                            "type": "integer",
                            "description": "Period for RSI calculation"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        ]
        
        # Format function specifications for OpenAI API
        function_specs = []
        for func in default_functions:
            # Ensure the function spec has the required 'type': 'function'
            function_spec = {
                "type": "function",
                "function": func
            }
            function_specs.append(function_spec)
            
        # Create function map for execution
        function_map = {
            "get_recent_market_data": get_recent_market_data,
            "get_market_data_range": get_market_data_range,
            "get_latest_price": get_latest_price,
            "get_market_summary": get_market_summary,
            "calculate_moving_average": calculate_moving_average,
            "calculate_rsi": calculate_rsi,
            "find_support_resistance": find_support_resistance,
            "detect_patterns": detect_patterns,
            "calculate_volatility": calculate_volatility
        }
        
        # Default LLM configuration
        default_llm_config = {
            "config_list": [{"model": "gpt-3.5-turbo"}],
            "temperature": 0.1,
            "request_timeout": 120
        }
        
        # Use provided LLM config or default
        final_llm_config = llm_config or default_llm_config
        
        # Create integration dictionary
        integration = {
            "function_map": function_map,
            "llm_config": final_llm_config,
            "function_specs": function_specs
        }
        
        return integration