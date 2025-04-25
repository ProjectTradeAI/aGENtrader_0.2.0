"""
Collaborative Decision Agent for AutoGen

This module implements a collaborative decision-making framework where multiple
specialized agents work together to analyze market data and generate trading decisions.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

# Import AutoGen
try:
    from autogen import (
        AssistantAgent, 
        UserProxyAgent, 
        config_list_from_json,
        ConversableAgent
    )
except ImportError:
    logging.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

# Import database query agent
from agents.database_query_agent import DatabaseQueryAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CollaborativeDecisionFramework:
    """
    A framework for collaborative decision-making among specialized agents.
    
    This framework orchestrates a structured conversation between different
    specialized agents to analyze market data and generate a trading decision.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 llm_model: str = "gpt-3.5-turbo",
                 temperature: float = 0.1,
                 max_session_time: int = 120
                ):
        """
        Initialize the collaborative decision framework
        
        Args:
            api_key: OpenAI API key (will try to get from env if None)
            llm_model: Language model to use
            temperature: Temperature for model generation
            max_session_time: Maximum session time in seconds
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No OpenAI API key provided or found in environment variables")
        
        # Basic configuration for all agents
        self.llm_model = llm_model
        self.temperature = temperature  
        self.max_session_time = max_session_time
        
        # Initialize database query agent
        self.db_agent = DatabaseQueryAgent()
        
        # Initialize agent instances
        self._init_agents()
        
        # Register functions with agents
        self._register_functions()
    
    def _init_agents(self) -> None:
        """Initialize the specialized agent instances"""
        
        # Core decision-making agents
        self.market_analyst = AssistantAgent(
            name="MarketAnalyst",
            system_message="""You are an expert cryptocurrency market analyst.
            Your role is to analyze market data and identify key patterns and trends.
            1. Analyze price action, volume, and market indicators
            2. Identify significant support and resistance levels
            3. Detect chart patterns and potential breakouts
            4. Evaluate market sentiment and momentum
            
            Focus purely on data analysis and pattern recognition.
            Be thorough but concise, focusing on actionable insights.
            Support your analysis with specific data points and metrics.
            
            DO NOT make trading recommendations - that's the responsibility of other agents.
            """,
            llm_config={
                "config_list": [{"model": self.llm_model, "api_key": self.api_key}],
                "temperature": self.temperature,
            }
        )
        
        self.strategy_manager = AssistantAgent(
            name="StrategyManager",
            system_message="""You are an expert crypto trading strategy manager.
            Your role is to evaluate market analysis and determine if conditions align
            with established trading strategies.
            
            1. Consider the market analysis provided by the MarketAnalyst
            2. Evaluate if current conditions match criteria for any trading strategies
            3. Assess probability of successful trade based on historical performance
            4. Consider timeframes and potential holding periods
            
            Focus on strategy alignment and execution timing.
            Clearly explain which strategies might work in current conditions and why.
            
            DO NOT make final trading decisions - only strategic evaluations.
            """,
            llm_config={
                "config_list": [{"model": self.llm_model, "api_key": self.api_key}],
                "temperature": self.temperature,
            }
        )
        
        self.risk_manager = AssistantAgent(
            name="RiskManager",
            system_message="""You are an expert risk management specialist.
            Your role is to evaluate potential trades from a risk management perspective.
            
            1. Analyze potential downside risks based on market conditions
            2. Calculate appropriate position sizing based on risk parameters
            3. Determine optimal stop-loss and take-profit levels
            4. Assess overall market risk conditions
            
            Focus on capital preservation and downside protection.
            Be conservative in your assessment and highlight all potential risks.
            
            DO NOT make specific trading decisions - only risk assessments.
            """,
            llm_config={
                "config_list": [{"model": self.llm_model, "api_key": self.api_key}],
                "temperature": self.temperature,
            }
        )
        
        self.trading_decision_agent = AssistantAgent(
            name="TradingDecisionAgent",
            system_message="""You are the final trading decision-maker.
            Your role is to synthesize input from all specialist agents and make a final trading decision.
            
            1. Carefully consider the market analysis from the MarketAnalyst
            2. Evaluate strategy alignment from the StrategyManager
            3. Incorporate risk assessment from the RiskManager
            4. Make a clear, justified trading decision
            
            Your output MUST be a well-structured JSON object with the following format:
            {
              "decision": "BUY/SELL/HOLD",
              "asset": "BTC",
              "entry_price": 45300,
              "stop_loss": 44800,
              "take_profit": 46800,
              "confidence_score": 0.85,
              "reasoning": "Concise explanation of decision rationale"
            }
            
            Always include all fields in your decision output.
            """,
            llm_config={
                "config_list": [{"model": self.llm_model, "api_key": self.api_key}],
                "temperature": self.temperature,
            }
        )
        
        # Create a UserProxy agent to handle function execution and orchestration
        self.user_proxy = UserProxyAgent(
            name="AgentCoordinator",
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=10,
            llm_config=False,  # No LLM for the UserProxy
        )
    
    def _register_functions(self) -> None:
        """Register database query functions with agents"""
        
        # Define function schemas
        query_functions = [
            {
                "name": "query_market_data",
                "description": "Query historical market data for a trading symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., 'BTCUSDT')"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (alternative to limit)"
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Output format ('json', 'markdown', 'text')"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_market_statistics",
                "description": "Get market statistics (price range, volatility, etc.) for a trading symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., 'BTCUSDT')"
                        },
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., '1h', '4h', '1d')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back"
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Output format ('json', 'markdown', 'text')"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "query_funding_rates", 
                "description": "Query funding rate data for a futures trading pair",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., 'BTCUSDT')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back"
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Output format ('json', 'markdown', 'text')"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "query_exchange_flows",
                "description": "Query exchange flow data (deposits/withdrawals) for a cryptocurrency",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Cryptocurrency symbol (e.g., 'BTC')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back"
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Output format ('json', 'markdown', 'text')"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        ]
        
        # Create function wrappers for the database query functions
        def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                         days: Optional[int] = None, format_type: str = 'json') -> str:
            """Query market data for a specific symbol"""
            return self.db_agent.query_market_data(symbol, interval, limit, days, format_type)
        
        def get_market_statistics(symbol: str, interval: str = '1d', 
                             days: int = 30, format_type: str = 'json') -> str:
            """Get market statistics for a specific symbol"""
            return self.db_agent.get_market_statistics(symbol, interval, days, format_type)
        
        def query_funding_rates(symbol: str, days: int = 7, format_type: str = 'json') -> str:
            """Query funding rates for a specific symbol"""
            return self.db_agent.query_funding_rates(symbol, days, format_type)
        
        def query_exchange_flows(symbol: str, days: int = 7, format_type: str = 'json') -> str:
            """Query exchange flows for a specific symbol"""
            return self.db_agent.query_exchange_flows(symbol, days, format_type)
        
        # Create function map
        function_map = {
            "query_market_data": query_market_data,
            "get_market_statistics": get_market_statistics,
            "query_funding_rates": query_funding_rates,
            "query_exchange_flows": query_exchange_flows
        }
        
        # Update LLM configurations with function schemas
        for agent in [self.market_analyst, self.strategy_manager, self.risk_manager, self.trading_decision_agent]:
            agent.llm_config["functions"] = query_functions
        
        # Register functions with all agents
        for agent in [self.market_analyst, self.strategy_manager, self.risk_manager, self.trading_decision_agent]:
            agent.register_function(function_map=function_map)
        
        # Register functions with the user proxy for execution
        self.user_proxy.register_function(function_map=function_map)
    
    def run_decision_session(self, symbol: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a full collaborative decision-making session
        
        Args:
            symbol: Trading symbol to analyze (e.g., 'BTCUSDT')
            prompt: Optional custom prompt to initiate the session
            
        Returns:
            The trading decision as a dictionary
        """
        try:
            # Get latest price for context
            latest_price = self.db_agent.db_interface.query_manager.get_latest_price(symbol)
            price_str = f"${latest_price:.2f}" if latest_price else "unavailable"
            
            # Default prompt if none provided
            if not prompt:
                prompt = f"""
                Analyze the current market conditions for {symbol} trading at {price_str}.

                Follow this structured process:
                1. MarketAnalyst: Begin by retrieving the latest market data and providing a thorough technical analysis
                2. StrategyManager: Review the market analysis and assess which trading strategies may be effective
                3. RiskManager: Evaluate the potential risk factors and suggest risk mitigation measures
                4. TradingDecisionAgent: Make a final trading decision in the required JSON format
                
                Use database query functions as needed to retrieve market data.
                """
            
            logger.info(f"Starting collaborative decision session for {symbol} at {price_str}")
            
            # Start the conversation with the market analyst
            self.user_proxy.initiate_chat(
                self.market_analyst,
                message=prompt,
                clear_history=True,
                timeout=self.max_session_time
            )
            
            # Continue the conversation with strategy manager
            self.user_proxy.send(
                self.strategy_manager,
                message="Based on the market analysis above, what trading strategies would be appropriate? Use functions to get additional data as needed."
            )
            
            # Continue the conversation with risk manager
            self.user_proxy.send(
                self.risk_manager, 
                message="Based on the market analysis and strategy recommendations above, what are the key risk factors to consider? Please assess appropriate risk management measures including position sizing, stop loss levels and risk-reward ratio."
            )
            
            # Get final decision from trading decision agent
            self.user_proxy.send(
                self.trading_decision_agent,
                message="Based on all the analysis above from the Market Analyst, Strategy Manager, and Risk Manager, please make a final trading decision in the required JSON format with decision, asset, entry_price, stop_loss, take_profit, confidence_score, and reasoning fields."
            )
            
            # Extract decision from the trading decision agent's response
            decision_text = self.trading_decision_agent.last_message()["content"]
            
            # Parse the JSON decision
            decision = self._extract_decision_json(decision_text)
            
            # Add metadata
            decision["timestamp"] = datetime.now().isoformat()
            decision["symbol"] = symbol
            decision["price_at_analysis"] = latest_price
            
            # Log the decision
            logger.info(f"Decision: {decision['decision']} with {decision['confidence_score']*100:.1f}% confidence")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in collaborative decision session: {str(e)}")
            
            # Return error decision
            return {
                "error": str(e),
                "decision": "ERROR",
                "asset": symbol,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            # Clean up
            self.db_agent.db_interface.query_manager.close()
    
    def _extract_decision_json(self, text: str) -> Dict[str, Any]:
        """
        Extract a JSON decision object from the agent's response text
        
        Args:
            text: Response text from the trading decision agent
            
        Returns:
            Decision dictionary
        """
        try:
            # Try to find JSON block in markdown format
            if "```json" in text:
                json_text = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_text)
            
            # Try to find JSON block with just backticks
            elif "```" in text:
                json_text = text.split("```")[1].strip()
                return json.loads(json_text)
            
            # Try to find JSON object with curly braces
            elif "{" in text and "}" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_text = text[start:end]
                return json.loads(json_text)
            
            # If no JSON found, return a default error response
            raise ValueError("No valid JSON decision found in response")
            
        except Exception as e:
            logger.error(f"Error parsing decision JSON: {str(e)}")
            return {
                "decision": "ERROR",
                "error": f"Failed to parse decision: {str(e)}",
                "confidence_score": 0.0,
                "reasoning": "Error in decision parsing"
            }

# Example usage
if __name__ == "__main__":
    try:
        # Create the collaborative decision framework
        framework = CollaborativeDecisionFramework()
        
        # Run a decision session
        decision = framework.run_decision_session("BTCUSDT")
        
        # Print the decision
        print(f"\nFinal Decision: {json.dumps(decision, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")