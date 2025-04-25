"""
Trading Agent Framework

A comprehensive framework for creating and managing trading agents
with enhanced database integration and structured decision-making.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple, Callable

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Warning: AutoGen not available. Agent functionality will be limited.")

# Import database functions
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
    get_db_tool,
    CustomJSONEncoder
)

# Import database integration tools
from agents.database_query_agent import DatabaseQueryAgent
from agents.autogen_db_integration import get_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("trading_agent_framework")

class TradingAgentFramework:
    """
    A comprehensive framework for managing trading agents with enhanced database integration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the trading agent framework.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_dir = os.path.join(
            self.config.get("log_dir", "data/logs/trading_sessions"),
            self.session_id
        )
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Agent configuration
        self.max_session_time = self.config.get("max_session_time", 300)  # 5 minutes default
        self.model = self.config.get("model", "gpt-3.5-turbo-0125")
        self.temperature = self.config.get("temperature", 0.1)
        
        # Initialize agent components
        self.agents = {}
        self.function_map = {}
        self.openai_config = None
        self.db_agent = None
        self.db_integration = None
        self.initialized = False
        
        # Log initialization
        logger.info(f"Initialized TradingAgentFramework with session ID: {self.session_id}")
    
    def initialize(self) -> bool:
        """
        Initialize the agent framework.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot initialize agents.")
            return False
        
        try:
            # 1. Set up database agent and function map
            self.db_agent = DatabaseQueryAgent()
            
            # 2. Create OpenAI configuration
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.error("OpenAI API key not found. Cannot initialize agents.")
                return False
            
            config_list = [{"model": self.model, "api_key": api_key}]
            
            # 3. Get database integration
            # Create base config
            base_config = {
                "model": self.model,
                "temperature": self.temperature,
                "config_list": config_list
            }
            
            self.db_integration = get_integration(base_config)
            if not self.db_integration:
                logger.error("Failed to initialize database integration.")
                return False
            
            # 4. Extract components from integration
            self.function_map = self.db_integration.get("function_map", {})
            
            # Get the LLM config without the function_map to avoid serialization issues
            self.openai_config = self.db_integration.get("llm_config", None)
            
            if not self.openai_config:
                logger.error("Failed to initialize OpenAI configuration.")
                return False
            
            # 5. Create specialized agents
            self._create_agents()
            
            # Mark initialization complete
            self.initialized = True
            logger.info("Successfully initialized trading agent framework.")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing trading agent framework: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _create_agents(self):
        """Create specialized agents for trading decisions"""
        # Market Analyst Agent
        self.agents["market_analyst"] = AssistantAgent(
            name="MarketAnalyst",
            system_message="""You are a Market Analyst specialized in cryptocurrency technical analysis.
Your expertise includes:
1. Interpreting price charts and identifying patterns
2. Analyzing market trends using technical indicators
3. Identifying support and resistance levels
4. Evaluating market sentiment and volatility

You have database access to real-time and historical market data. Always use this data
to ground your analysis and clearly explain the technical indicators you're using.

When analyzing market conditions, follow this structured approach:
1. Get the latest price and recent price action using database functions
2. Analyze key technical indicators (MA, RSI, MACD, etc.)
3. Identify chart patterns and support/resistance levels
4. Assess market volatility and trading volume
5. Summarize the technical outlook with an explicit directional bias

Format your analysis with clear sections and provide specific price levels for reference.
""",
            llm_config=self.openai_config
        )
        
        # Strategy Manager Agent
        self.agents["strategy_manager"] = AssistantAgent(
            name="StrategyManager",
            system_message="""You are a Strategy Manager specialized in cryptocurrency trading strategies.
Your expertise includes:
1. Developing trading strategies based on technical analysis
2. Identifying optimal entry and exit points
3. Setting appropriate take-profit and stop-loss levels
4. Designing strategies for various market conditions

You have database access to real-time and historical market data. Use this data when 
evaluating different strategy options.

When developing strategies, follow this structured approach:
1. Assess whether the market conditions favor trend-following or range-trading strategies
2. Define specific entry criteria with precise price levels
3. Set appropriate stop-loss and take-profit targets based on support/resistance
4. Calculate the risk-reward ratio for the proposed trade
5. Provide a clear execution plan for implementing the strategy

Your recommendations should be specific, data-driven, and actionable with precise price levels.
""",
            llm_config=self.openai_config
        )
        
        # Risk Manager Agent
        self.agents["risk_manager"] = AssistantAgent(
            name="RiskManager",
            system_message="""You are a Risk Manager specialized in cryptocurrency trading risk assessment.
Your expertise includes:
1. Evaluating market and position risks
2. Determining appropriate position sizing
3. Calculating and optimizing risk-reward ratios
4. Setting risk parameters based on market volatility
5. Ensuring portfolio diversification and risk balance

You have database access to real-time market data, volatility metrics, and historical performance.

When assessing risk, follow this structured approach:
1. Calculate current market volatility using database functions
2. Determine appropriate position sizing based on volatility and account balance
3. Set precise stop-loss levels to manage downside risk
4. Verify the risk-reward ratio meets minimum thresholds (at least 2:1)
5. Ensure the total portfolio risk remains within acceptable parameters

Your recommendations should focus on capital preservation while optimizing for returns.
Provide specific percentages for position sizing and exact price levels for risk management.
""",
            llm_config=self.openai_config
        )
        
        # Liquidity Analyst Agent
        self.agents["liquidity_analyst"] = AssistantAgent(
            name="LiquidityAnalyst",
            system_message="""You are a Liquidity Analyst specialized in cryptocurrency market liquidity assessment.
Your expertise includes:
1. Analyzing exchange order book depth and liquidity
2. Evaluating bid-ask spreads and slippage estimations
3. Monitoring funding rates for futures markets
4. Tracking exchange flows and whale wallet movements
5. Assessing market impact for various position sizes

You have database access to exchange flow data, order book metrics, and funding rates.

When analyzing liquidity, follow this structured approach:
1. Retrieve current liquidity metrics using database functions
2. Evaluate order book depth and bid-ask spreads
3. Analyze recent exchange inflows and outflows
4. Check funding rates and basis for futures markets
5. Estimate potential slippage for planned position sizes

Your analysis should focus on how liquidity conditions might impact trade execution
and whether current liquidity supports the proposed trading strategy.
""",
            llm_config=self.openai_config
        )
        
        # Global Market Analyst
        self.agents["global_analyst"] = AssistantAgent(
            name="GlobalMarketAnalyst",
            system_message="""You are a Global Market Analyst specializing in macro-economic factors affecting cryptocurrency markets.
Your expertise includes:
1. Analyzing correlations between traditional and crypto markets
2. Tracking global market indicators (DXY, S&P 500, VIX)
3. Monitoring cryptocurrency market dominance shifts
4. Assessing regulatory developments and their market impact
5. Evaluating on-chain data and network fundamentals

You have database access to global market data, correlation metrics, and market indices.

When providing global market context, follow this structured approach:
1. Check correlations between crypto and traditional markets
2. Analyze recent performance of key global indicators
3. Evaluate Bitcoin dominance and sector rotations
4. Assess relevant macroeconomic factors
5. Provide a global market outlook and its implications for specific crypto assets

Your analysis should connect global market conditions to potential impacts on the specific
cryptocurrency being analyzed.
""",
            llm_config=self.openai_config
        )
        
        # Trading Decision Agent
        self.agents["decision_agent"] = AssistantAgent(
            name="TradingDecisionAgent",
            system_message="""You are the Trading Decision Agent responsible for making final trading decisions.
Your expertise includes:
1. Synthesizing analysis from multiple specialist agents
2. Making clear, decisive trading recommendations
3. Formatting decisions in a structured, machine-readable format
4. Assigning confidence levels to trading decisions
5. Providing clear rationale for decisions

You make the final trading decision by integrating input from specialist analysts.
Your decision must be in a specific JSON format for automated processing.

Always output your final decision in this exact JSON format:
{
  "decision": "BUY/SELL/HOLD",
  "asset": "BTC",
  "entry_price": 45000,
  "stop_loss": 43500,
  "take_profit": 48000,
  "position_size_percent": 10,
  "confidence_score": 0.75,
  "time_horizon": "short-term/medium-term/long-term",
  "reasoning": "Clear explanation of the decision rationale"
}

Ensure your decision is well-justified by the collective analysis and reflects
an appropriate balance of risk and potential reward.
""",
            llm_config=self.openai_config
        )
        
        # User Proxy Agent
        self.agents["user_proxy"] = UserProxyAgent(
            name="TradingSystemUser",
            human_input_mode="NEVER",
            code_execution_config={"last_n_messages": 3, "work_dir": "agents"},
            system_message="""You are the coordination agent that manages the conversation between specialist agents.
Your role is to ensure the conversation flows logically between agents to produce a structured trading decision.
You never provide your own analysis, but rather direct the conversation to the appropriate specialist.

Working with these specialist agents:
1. MarketAnalyst - Technical analysis expert
2. StrategyManager - Trading strategy expert
3. RiskManager - Risk assessment expert 
4. LiquidityAnalyst - Liquidity assessment expert
5. GlobalMarketAnalyst - Macro-economic analysis expert
6. TradingDecisionAgent - Final decision maker

Your goal is to facilitate a structured decision-making process that results in a clear trading decision.
""",
            function_map=self.function_map
        )
        
        # The function_map is stored separately and won't be included in JSON serialization
    
    def _extract_decision_json(self, decision_text: str) -> Dict[str, Any]:
        """
        Extract JSON decision from agent response text.
        
        Args:
            decision_text: Text containing the decision
            
        Returns:
            Decision as a dictionary
        """
        try:
            # Try to find JSON in the text
            import re
            
            # Look for JSON pattern
            json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
            match = re.search(json_pattern, decision_text)
            
            if match:
                json_str = match.group(1) if match.group(1) else match.group(0)
                # Clean up the JSON string
                json_str = json_str.strip()
                
                # Parse the JSON
                decision = json.loads(json_str)
                return decision
            else:
                logger.warning("No JSON found in decision text.")
                
                # Fallback: Extract structured data manually
                decision = {
                    "decision": "HOLD",
                    "asset": "Unknown",
                    "confidence_score": 0.0,
                    "reasoning": "Failed to parse decision JSON from agent output."
                }
                
                # Try to extract decision type
                if "buy" in decision_text.lower():
                    decision["decision"] = "BUY"
                elif "sell" in decision_text.lower():
                    decision["decision"] = "SELL"
                
                return decision
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing decision JSON: {str(e)}")
            # Return a default decision with error
            return {
                "decision": "HOLD",
                "asset": "Unknown",
                "confidence_score": 0.0,
                "reasoning": f"Failed to parse decision JSON: {str(e)}"
            }
    
    def run_sequential_session(self, symbol: str, objective: str = None) -> Dict[str, Any]:
        """
        Run a trading decision session with sequential agent consultation.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            objective: Optional specific objective for the decision session
            
        Returns:
            Session result with trading decision
        """
        if not self.initialized:
            initialized = self.initialize()
            if not initialized:
                return {
                    "status": "error",
                    "message": "Failed to initialize agent framework"
                }
        
        start_time = datetime.now()
        logger.info(f"Starting sequential trading session for {symbol} at {start_time.isoformat()}")
        
        try:
            # Get latest price
            latest_price_json = get_latest_price(symbol)
            if not latest_price_json:
                return {
                    "status": "error",
                    "message": f"Failed to get latest price for {symbol}"
                }
            
            latest_price_data = json.loads(latest_price_json)
            latest_price = latest_price_data.get("close", 0)
            price_str = f"${latest_price:,.2f}" if latest_price else "Unknown"
            
            # Get market summary
            market_summary_json = get_market_summary(symbol)
            if not market_summary_json:
                logger.warning(f"Failed to get market summary for {symbol}")
                market_summary = ""
            else:
                market_summary_data = json.loads(market_summary_json)
                market_summary = f"Recent price change: {market_summary_data.get('price_change_24h', 0):.2f}%, " + \
                                f"Volume: {market_summary_data.get('volume_24h', 0):,.0f}"
            
            # Access all agents
            user_proxy = self.agents["user_proxy"]
            market_analyst = self.agents["market_analyst"]
            strategy_manager = self.agents["strategy_manager"]
            risk_manager = self.agents["risk_manager"]
            liquidity_analyst = self.agents["liquidity_analyst"]
            global_analyst = self.agents["global_analyst"]
            decision_agent = self.agents["decision_agent"]
            
            # Formulate the initial prompt
            if not objective:
                objective = f"Analyze current market conditions for {symbol} and determine if a trade is recommended"
            
            prompt = f"""
I need a comprehensive trading decision for {symbol} currently priced at {price_str}.
{market_summary}

Objective: {objective}

Follow this structured process:
1. MarketAnalyst: Begin by retrieving the latest market data and providing a thorough technical analysis
2. StrategyManager: Review the market analysis and assess which trading strategies may be effective
3. RiskManager: Evaluate the potential risk factors and suggest risk mitigation measures
4. LiquidityAnalyst: Assess current market liquidity conditions that may impact trade execution
5. GlobalMarketAnalyst: Provide broader market context and macro factors affecting the asset
6. TradingDecisionAgent: Make a final trading decision in the required JSON format
                
Use the database query functions as needed to access real-time market data.
"""
            
            logger.info(f"Starting sequential decision session for {symbol} at {price_str}")
            
            # Start the conversation with the market analyst
            user_proxy.initiate_chat(
                market_analyst,
                message=prompt,
                clear_history=True,
                timeout=self.max_session_time
            )
            
            # Continue with strategy manager
            user_proxy.send(
                strategy_manager,
                message="Based on the market analysis above, what trading strategies would be appropriate? Use database functions to get additional data as needed."
            )
            
            # Continue with risk manager
            user_proxy.send(
                risk_manager,
                message="Based on the market analysis and strategy recommendations above, what are the key risk factors to consider? Please assess appropriate risk management measures including position sizing, stop loss levels and risk-reward ratio."
            )
            
            # Continue with liquidity analyst
            user_proxy.send(
                liquidity_analyst,
                message="Based on the analysis so far, please assess the current liquidity conditions for this asset. Consider order book depth, exchange flows, and futures market conditions."
            )
            
            # Continue with global market analyst
            user_proxy.send(
                global_analyst,
                message="Please provide global market context relevant to this trading decision. Consider correlations with traditional markets, macro-economic factors, and broader crypto market trends."
            )
            
            # Get final decision
            user_proxy.send(
                decision_agent,
                message="Based on all the analysis above from the Market Analyst, Strategy Manager, Risk Manager, Liquidity Analyst, and Global Market Analyst, please make a final trading decision in the required JSON format with decision, asset, entry_price, stop_loss, take_profit, position_size_percent, confidence_score, time_horizon, and reasoning fields."
            )
            
            # Extract decision from the trading decision agent's response
            decision_text = decision_agent.last_message()["content"]
            
            # Parse the JSON decision
            decision = self._extract_decision_json(decision_text)
            
            # Add metadata
            decision["timestamp"] = datetime.now().isoformat()
            decision["symbol"] = symbol
            decision["price_at_analysis"] = latest_price
            
            # Log the decision
            confidence = decision.get("confidence_score", 0)
            confidence_pct = confidence * 100 if isinstance(confidence, float) else confidence
            logger.info(f"Decision: {decision.get('decision', 'UNKNOWN')} with {confidence_pct:.1f}% confidence")
            
            # Save conversation history
            conversation_history = user_proxy.chat_messages
            session_log_file = os.path.join(
                self.session_dir, 
                f"sequential_{symbol.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Structure the session data
            session_data = {
                "session_id": self.session_id,
                "session_type": "sequential",
                "symbol": symbol,
                "objective": objective,
                "timestamp": start_time.isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "price_at_analysis": latest_price,
                "decision": decision,
                "conversation": conversation_history
            }
            
            # Save to file
            with open(session_log_file, "w") as f:
                json.dump(session_data, f, cls=CustomJSONEncoder, indent=2)
            
            logger.info(f"Session log saved to {session_log_file}")
            
            return {
                "status": "success",
                "session_id": self.session_id,
                "symbol": symbol,
                "decision": decision,
                "log_file": session_log_file
            }
            
        except Exception as e:
            logger.error(f"Error in sequential trading session: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "message": f"Error in trading session: {str(e)}",
                "session_id": self.session_id,
                "symbol": symbol
            }
    
    def run_group_session(self, symbol: str, objective: str = None) -> Dict[str, Any]:
        """
        Run a trading decision session using a group chat.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            objective: Optional specific objective for the decision session
            
        Returns:
            Session result with trading decision
        """
        if not self.initialized:
            initialized = self.initialize()
            if not initialized:
                return {
                    "status": "error",
                    "message": "Failed to initialize agent framework"
                }
        
        start_time = datetime.now()
        logger.info(f"Starting group chat trading session for {symbol} at {start_time.isoformat()}")
        
        try:
            # Get latest price
            latest_price_json = get_latest_price(symbol)
            if not latest_price_json:
                return {
                    "status": "error",
                    "message": f"Failed to get latest price for {symbol}"
                }
            
            latest_price_data = json.loads(latest_price_json)
            latest_price = latest_price_data.get("close", 0)
            price_str = f"${latest_price:,.2f}" if latest_price else "Unknown"
            
            # Get market summary
            market_summary_json = get_market_summary(symbol)
            if not market_summary_json:
                logger.warning(f"Failed to get market summary for {symbol}")
                market_summary = ""
            else:
                market_summary_data = json.loads(market_summary_json)
                market_summary = f"Recent price change: {market_summary_data.get('price_change_24h', 0):.2f}%, " + \
                                f"Volume: {market_summary_data.get('volume_24h', 0):,.0f}"
            
            # Set up the group chat
            groupchat = GroupChat(
                agents=[
                    self.agents["market_analyst"],
                    self.agents["strategy_manager"],
                    self.agents["risk_manager"],
                    self.agents["liquidity_analyst"],
                    self.agents["global_analyst"],
                    self.agents["decision_agent"],
                ],
                messages=[],
                max_round=15  # Limit the number of conversation rounds
            )
            
            # Create group chat manager with a clean config
            # Remove function_map to avoid serialization issues
            clean_config = self.openai_config.copy() if self.openai_config else {}
            
            manager = GroupChatManager(
                groupchat=groupchat,
                llm_config=clean_config
            )
            
            # Formulate the initial prompt
            if not objective:
                objective = f"Analyze current market conditions for {symbol} and determine if a trade is recommended"
            
            prompt = f"""
I need a comprehensive trading decision for {symbol} currently priced at {price_str}.
{market_summary}

Objective: {objective}

Please collaborate to analyze this trading opportunity following these steps:
1. MarketAnalyst: Begin by retrieving the latest market data and providing a thorough technical analysis
2. StrategyManager: Review the market analysis and assess which trading strategies may be effective
3. RiskManager: Evaluate the potential risk factors and suggest risk mitigation measures
4. LiquidityAnalyst: Assess current market liquidity conditions that may impact trade execution
5. GlobalMarketAnalyst: Provide broader market context and macro factors affecting the asset
6. TradingDecisionAgent: Make a final trading decision in the required JSON format with decision, asset, entry_price, stop_loss, take_profit, position_size_percent, confidence_score, time_horizon, and reasoning fields.

All agents can and should use database query functions as needed to access real-time market data.
"""
            
            # Run the group chat
            result = manager.run(prompt, timeout=self.max_session_time)
            
            # Process the result to extract decision
            chat_history = groupchat.messages
            
            # Find the last message from the decision agent
            decision_text = ""
            for msg in reversed(chat_history):
                if msg.get("name") == "TradingDecisionAgent":
                    decision_text = msg.get("content", "")
                    break
            
            # Parse the JSON decision
            decision = self._extract_decision_json(decision_text)
            
            # Add metadata
            decision["timestamp"] = datetime.now().isoformat()
            decision["symbol"] = symbol
            decision["price_at_analysis"] = latest_price
            
            # Log the decision
            confidence = decision.get("confidence_score", 0)
            confidence_pct = confidence * 100 if isinstance(confidence, float) else confidence
            logger.info(f"Decision: {decision.get('decision', 'UNKNOWN')} with {confidence_pct:.1f}% confidence")
            
            # Save conversation history
            session_log_file = os.path.join(
                self.session_dir, 
                f"group_{symbol.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Structure the session data
            session_data = {
                "session_id": self.session_id,
                "session_type": "group",
                "symbol": symbol,
                "objective": objective,
                "timestamp": start_time.isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "price_at_analysis": latest_price,
                "decision": decision,
                "conversation": chat_history
            }
            
            # Save to file
            with open(session_log_file, "w") as f:
                json.dump(session_data, f, cls=CustomJSONEncoder, indent=2)
            
            logger.info(f"Session log saved to {session_log_file}")
            
            return {
                "status": "success",
                "session_id": self.session_id,
                "symbol": symbol,
                "decision": decision,
                "log_file": session_log_file
            }
            
        except Exception as e:
            logger.error(f"Error in group trading session: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "message": f"Error in trading session: {str(e)}",
                "session_id": self.session_id,
                "symbol": symbol
            }

# For testing
def main():
    """Test the trading agent framework"""
    import os
    
    # Check OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return

    try:
        # Create framework
        framework = TradingAgentFramework()
        
        # Initialize
        initialized = framework.initialize()
        if not initialized:
            print("Failed to initialize trading agent framework")
            return
        
        # Run a test session
        symbol = "BTCUSDT"
        print(f"Running sequential test session for {symbol}...")
        
        result = framework.run_sequential_session(symbol)
        
        # Display result
        if result["status"] == "success":
            decision = result["decision"]
            print(f"\nDecision: {decision['decision']} {symbol}")
            print(f"Entry: ${decision.get('entry_price', 'N/A')}")
            print(f"Stop Loss: ${decision.get('stop_loss', 'N/A')}")
            print(f"Take Profit: ${decision.get('take_profit', 'N/A')}")
            print(f"Position Size: {decision.get('position_size_percent', 'N/A')}%")
            print(f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%")
            print(f"Time Horizon: {decision.get('time_horizon', 'N/A')}")
            print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
            print(f"\nLog file: {result['log_file']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        print(f"Error in main: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()