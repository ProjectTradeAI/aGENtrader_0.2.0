"""
Collaborative Trading Framework

This module implements a structured multi-agent collaborative trading framework
that integrates with the database retrieval tools and provides clear, actionable
trading decisions.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

# Ensure parent directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AutoGen
try:
    import autogen
    from autogen import ConversableAgent, UserProxyAgent, Agent, GroupChat, GroupChatManager
except ImportError:
    logging.error("AutoGen not installed. Please install it using: pip install pyautogen")
    raise

# Import local modules
from agents.structured_decision_extractor import extract_trading_decision, log_trading_decision
from utils.llm_integration.autogen_integration import get_llm_config, AutoGenLLMConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            f"data/logs/collaborative_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler()
    ]
)


class CollaborativeTradingFramework:
    """
    Implementation of a collaborative multi-agent trading framework.
    
    This class orchestrates multiple specialized agents to work together
    to analyze market data and produce structured trading decisions.
    """
    
    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        max_consecutive_auto_reply: int = 10,
        log_dir: str = "data/logs",
    ):
        """
        Initialize the collaborative trading framework.
        
        Args:
            llm_config: Configuration for the language model
            max_consecutive_auto_reply: Maximum number of consecutive auto-replies
            log_dir: Directory to store logs
        """
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Get LLM configuration if not provided
        self.llm_config = llm_config or get_llm_config()
        self.max_consecutive_auto_reply = max_consecutive_auto_reply
        
        # Register database tools
        self._register_database_tools()
        
        # Initialize agents
        self.agents = self._create_agents()
        
        # Initialize GroupChat
        self.group_chat = self._create_group_chat()
        
        logging.info("Collaborative Trading Framework initialized")
    
    def _register_database_tools(self) -> None:
        """
        Register database retrieval tools with AutoGen.
        """
        try:
            from agents.database_retrieval_tool import query_market_data, get_market_statistics
            
            # These will be registered with agents later
            self.db_tools = {
                "query_market_data": query_market_data,
                "get_market_statistics": get_market_statistics
            }
            
            logging.info("Database tools registered successfully")
        
        except ImportError:
            logging.warning("Database retrieval tools not found. Agents will not have database access.")
            self.db_tools = {}
    
    def _create_agents(self) -> Dict[str, ConversableAgent]:
        """
        Create specialized agents for the trading framework.
        
        Returns:
            Dictionary of agent instances
        """
        # User proxy agent (for orchestration)
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.max_consecutive_auto_reply,
            code_execution_config={"use_docker": False},
            llm_config=self.llm_config,
            system_message="You are a coordinator for the trading analysis process."
        )
        
        # Market Analyst Agent
        market_analyst = ConversableAgent(
            name="MarketAnalyst",
            llm_config=self.llm_config,
            max_consecutive_auto_reply=self.max_consecutive_auto_reply,
            system_message="""
            You are a cryptocurrency market analyst specializing in technical and on-chain analysis.
            
            Your responsibilities:
            1. Request and analyze market data using the database tools
            2. Identify key price levels, trends, and patterns
            3. Analyze market indicators (RSI, MACD, Volume profiles, etc.)
            4. Consider recent news and sentiment impact
            5. Provide a comprehensive but concise market analysis
            
            Always base your analysis on the available data, not assumptions.
            Be specific with price levels and timeframes in your analysis.
            Highlight key support/resistance levels and trend direction clearly.
            """
        )
        
        # Strategic Advisor Agent
        strategic_advisor = ConversableAgent(
            name="StrategicAdvisor",
            llm_config=self.llm_config,
            max_consecutive_auto_reply=self.max_consecutive_auto_reply,
            system_message="""
            You are a strategic trading advisor specializing in cryptocurrency markets.
            
            Your responsibilities:
            1. Interpret market analysis provided by the Market Analyst
            2. Formulate clear trading strategies based on the analysis
            3. Consider multiple timeframes for entry and exit
            4. Identify potential opportunities and their risk profiles
            5. Recommend precise entry, stop-loss, and take-profit levels
            
            Your strategy recommendations should be precise and actionable.
            Always consider risk-reward ratios for any recommendation.
            Be explicit about trade direction (BUY, SELL, or HOLD) with confidence.
            """
        )
        
        # Risk Manager Agent
        risk_manager = ConversableAgent(
            name="RiskManager",
            llm_config=self.llm_config,
            max_consecutive_auto_reply=self.max_consecutive_auto_reply,
            system_message="""
            You are a risk management specialist for cryptocurrency trading.
            
            Your responsibilities:
            1. Evaluate the risk-reward profile of proposed strategies
            2. Validate position sizing and risk parameters
            3. Assess market volatility and liquidity implications
            4. Challenge questionable assumptions or high-risk proposals
            5. Recommend adjustments to improve the risk profile
            
            Your primary concern is capital preservation.
            Question any strategy that appears to have unfavorable risk-reward.
            Insist on clear stop-loss levels for any trade recommendation.
            Evaluate the confidence level in the context of current market volatility.
            """
        )
        
        # Decision Maker Agent
        decision_maker = ConversableAgent(
            name="DecisionMaker",
            llm_config=self.llm_config,
            max_consecutive_auto_reply=self.max_consecutive_auto_reply,
            system_message="""
            You are the final decision-maker for trading recommendations.
            
            Your responsibilities:
            1. Synthesize input from all specialist agents
            2. Make a definitive trading decision (BUY, SELL, or HOLD)
            3. Specify exact entry, stop-loss, and take-profit levels
            4. Provide a confidence score (0.0-1.0) for the decision
            5. Summarize key reasoning behind the decision
            
            YOU MUST FORMAT YOUR FINAL DECISION IN THIS EXACT JSON FORMAT:
            ```json
            {
              "decision": "BUY",       // BUY, SELL, or HOLD
              "asset": "BTC",          // Asset symbol
              "entry_price": 45300,    // Target entry price as a number
              "stop_loss": 44800,      // Stop loss price as a number
              "take_profit": 46800,    // Take profit price as a number
              "confidence_score": 0.85, // Confidence score (0.0-1.0) as a number
              "reasoning": "Bullish momentum confirmed by RSI and positive on-chain flows."
            }
            ```
            
            The JSON output is critically important - ensure all values are correct and properly formatted.
            """
        )
        
        # Register database tools with agents
        if self.db_tools:
            for tool_name, tool_func in self.db_tools.items():
                autogen.register_function(
                    function=tool_func,
                    caller=market_analyst,
                    name=tool_name,
                    description=getattr(tool_func, "__doc__", f"Call {tool_name}")
                )
        
        # Return dictionary of agents
        agents = {
            "user_proxy": user_proxy,
            "market_analyst": market_analyst,
            "strategic_advisor": strategic_advisor,
            "risk_manager": risk_manager,
            "decision_maker": decision_maker
        }
        
        logging.info(f"Created {len(agents)} agents for the trading framework")
        return agents
    
    def _create_group_chat(self) -> GroupChat:
        """
        Create a GroupChat for agent collaboration.
        
        Returns:
            GroupChat instance
        """
        # Define the ordered sequence of agents in the conversation
        agents_list = [
            self.agents["user_proxy"],
            self.agents["market_analyst"],
            self.agents["strategic_advisor"],
            self.agents["risk_manager"],
            self.agents["decision_maker"],
        ]
        
        # Create the group chat
        group_chat = GroupChat(
            agents=agents_list,
            messages=[],
            max_round=12,  # Limit the number of conversation rounds
            speaker_selection_method="round_robin",  # Sequential agent participation
            allow_repeat_speaker=False  # Prevent consecutive messages from same agent
        )
        
        logging.info("Created GroupChat for agent collaboration")
        return group_chat
    
    def run_trading_session(
        self,
        symbol: str,
        interval: str = "1h",
        full_output: bool = False
    ) -> Dict[str, Any]:
        """
        Run a collaborative trading session to analyze a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1h', '4h', '1d')
            full_output: Whether to return full conversation history
            
        Returns:
            Dictionary containing the trading decision or error
        """
        logging.info(f"Starting trading session for {symbol} at {interval} interval")
        
        # Create GroupChat manager with properly configured speaker selection
        manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config,
            is_termination_msg=lambda msg: "TRADING SESSION COMPLETE" in msg.get("content", ""),
            select_speaker_auto_llm_config=self.llm_config  # This is critical - provide LLM config for speaker selection
        )
        
        # Initial prompt to start the conversation
        initial_prompt = f"""
        We need a trading decision for {symbol} at {interval} timeframe.
        
        MarketAnalyst, please start by retrieving and analyzing the most recent market data.
        Use query_market_data and get_market_statistics functions to get the data.
        
        After all agents have provided their input, DecisionMaker will make the final decision
        in the required JSON format.
        
        When the final decision is made, conclude with: TRADING SESSION COMPLETE
        """
        
        # Run the group chat
        try:
            chat_result = manager.run(
                message=initial_prompt,
                sender=self.agents["user_proxy"],
            )
            
            # Extract messages from the group chat
            messages = self.group_chat.messages
            
            # Extract the trading decision from the last message from DecisionMaker
            decision = None
            for message in reversed(messages):
                if message.get("name") == "DecisionMaker":
                    decision = extract_trading_decision(message.get("content", ""))
                    break
            
            if not decision or "error" in decision:
                logging.error("Failed to extract valid trading decision")
                error_message = decision.get("error", "Unknown error") if decision else "No decision found"
                result = {"error": error_message, "partial_decision": decision}
            else:
                # Success - log the trading decision
                log_trading_decision(decision, self.log_dir)
                logging.info(f"Trading decision: {decision['decision']} for {decision['asset']}")
                result = decision
            
            # Add full conversation if requested
            if full_output:
                result["conversation"] = [
                    {"name": msg.get("name", "Unknown"), 
                     "content": msg.get("content", "")} 
                    for msg in messages
                ]
            
            return result
            
        except Exception as e:
            logging.error(f"Error in trading session: {str(e)}")
            return {"error": f"Trading session failed: {str(e)}"}
    
    def get_agent_by_name(self, name: str) -> Optional[ConversableAgent]:
        """
        Get agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            Agent instance or None if not found
        """
        for agent in self.agents.values():
            if agent.name == name:
                return agent
        return None


def run_trading_framework(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    full_output: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to run the collaborative trading framework.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval (e.g., '1h', '4h', '1d')
        full_output: Whether to return full conversation history
        
    Returns:
        Dictionary containing the trading decision or error
    """
    # Initialize framework
    framework = CollaborativeTradingFramework()
    
    # Run trading session
    return framework.run_trading_session(symbol, interval, full_output)


if __name__ == "__main__":
    # Example usage when run directly
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Collaborative Trading Framework")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", type=str, default="1h", help="Time interval")
    parser.add_argument("--full", action="store_true", help="Include full conversation in output")
    args = parser.parse_args()
    
    # Run trading framework
    decision = run_trading_framework(args.symbol, args.interval, args.full)
    
    # Print result
    if "error" in decision:
        print(f"Error: {decision['error']}")
    else:
        print("\n===== TRADING DECISION =====")
        print(f"Decision: {decision['decision']}")
        print(f"Asset: {decision['asset']}")
        print(f"Entry Price: {decision['entry_price']}")
        print(f"Stop Loss: {decision['stop_loss']}")
        print(f"Take Profit: {decision['take_profit']}")
        print(f"Confidence: {decision['confidence_score']:.2f}")
        print(f"Reasoning: {decision['reasoning']}")
        print("============================\n")