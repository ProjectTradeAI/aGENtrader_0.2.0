"""
Structured Decision Agent Module

Provides a framework for making structured, consistent trading decisions
using AutoGen agents with direct database integration.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
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
    CustomJSONEncoder
)

# Import database integration
from agents.database_query_agent import DatabaseQueryAgent
from agents.autogen_db_integration import (
    create_market_data_function_map,
    create_db_function_specs,
    enhance_llm_config,
    format_trading_decision
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("structured_decision_agent")

class StructuredDecisionManager:
    """
    Manages structured agent decision-making with database integration
    for cryptocurrency trading decisions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the structured decision manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.max_session_time = self.config.get("max_session_time", 300)  # 5 minutes default
        self.agents = {}
        self.initialized = False
        self.db_agent = DatabaseQueryAgent()
        self.function_map = create_market_data_function_map()
        self.function_specs = create_db_function_specs()
        
        # Set up logging directory
        self.log_dir = self.config.get("log_dir", "data/logs/structured_decisions")
        os.makedirs(self.log_dir, exist_ok=True)
        
        logger.info(f"Initialized StructuredDecisionManager with session ID: {self.session_id}")
    
    def _setup_openai_config(self) -> Optional[Dict[str, Any]]:
        """Set up OpenAI API configuration"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OpenAI API key found in environment variables")
            return None
        
        model = self.config.get("model", "gpt-3.5-turbo-0125")
        temperature = self.config.get("temperature", 0.1)
        
        base_config = {
            "model": model,
            "temperature": temperature,
            "config_list": [{"model": model, "api_key": api_key}]
        }
        
        # Enhance the config with function specs but don't include function_map
        return enhance_llm_config(base_config)
    
    def initialize(self) -> bool:
        """
        Initialize the agent system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen not available. Cannot initialize agents.")
            return False
        
        # Set up OpenAI config
        llm_config = self._setup_openai_config()
        if not llm_config:
            logger.error("Failed to set up LLM configuration.")
            return False
        
        try:
            # Create specialized agents
            
            # 1. Market Analyst Agent - Performs technical analysis
            self.agents["market_analyst"] = AssistantAgent(
                name="MarketAnalyst",
                system_message="""You are a Market Analyst specialized in cryptocurrency technical analysis.
Your expertise includes:
1. Interpreting price charts and identifying patterns
2. Analyzing market trends using technical indicators
3. Identifying support and resistance levels
4. Evaluating market sentiment and volatility

You can access historical market data directly from the database for analysis and provide 
clear, data-driven insights to help with trading decisions. Always base your analysis 
on the data provided, and clearly explain your reasoning.

When analyzing the market, follow this structured approach:
1. Get current price and recent price action
2. Analyze key technical indicators (MA, RSI, MACD, etc.)
3. Identify chart patterns and support/resistance levels
4. Assess market volatility and volume
5. Summarize the technical outlook

Your analysis should be comprehensive, data-driven, and actionable.
""",
                llm_config=llm_config
            )
            
            # 2. Strategy Advisor Agent - Recommends trading strategies
            self.agents["strategy_advisor"] = AssistantAgent(
                name="StrategyAdvisor",
                system_message="""You are a Strategy Advisor specialized in cryptocurrency trading strategies.
Your expertise includes:
1. Developing trade strategies based on technical analysis
2. Identifying optimal entry and exit points
3. Determining appropriate position sizing
4. Balancing risk and reward in trading plans

Based on market analysis provided, you recommend concrete trading strategies with specific
parameters. Always provide actionable recommendations with clear reasoning.

When recommending strategies, follow this structured approach:
1. Evaluate different strategy options based on market conditions
2. Recommend specific entry and exit criteria
3. Provide target prices and stop-loss levels
4. Estimate risk-reward ratios for the trade
5. Explain the reasoning behind your recommendations

Your strategies should be specific, practical, and tailored to current market conditions.
""",
                llm_config=llm_config
            )
            
            # 3. Risk Manager Agent - Evaluates risk factors
            self.agents["risk_manager"] = AssistantAgent(
                name="RiskManager",
                system_message="""You are a Risk Manager specialized in cryptocurrency trading risk assessment.
Your expertise includes:
1. Evaluating market and position risk factors
2. Determining appropriate position sizing
3. Setting stop-loss levels to manage downside
4. Calculating risk-reward ratios for trades
5. Monitoring portfolio exposure and concentration

You analyze risk factors and provide guidance on risk management for trading decisions.
Always prioritize capital preservation while maximizing potential returns.

When assessing risk, follow this structured approach:
1. Identify key risk factors for the proposed trade
2. Determine appropriate position sizing based on account size and risk
3. Set precise stop-loss levels to limit potential losses
4. Calculate the risk-reward ratio for the trade
5. Provide specific risk mitigation recommendations

Your risk assessment should be detailed, precise, and focused on protecting capital.
""",
                llm_config=llm_config
            )
            
            # 4. Trading Decision Agent - Produces final trading decisions
            self.agents["trading_decision"] = AssistantAgent(
                name="TradingDecisionAgent",
                system_message="""You are the Trading Decision Agent responsible for making final trading decisions.
Your expertise includes:
1. Synthesizing analysis from multiple specialists
2. Making clear, decisive trading recommendations
3. Formatting decisions in a structured, machine-readable format
4. Assigning confidence levels to trading decisions
5. Providing clear rationale for decisions

You make the final trading decision by integrating input from the Market Analyst, 
Strategy Advisor, and Risk Manager. Your decision must be in a specific JSON format 
for automated processing.

Always output your final decision in this exact JSON format:
{
  "decision": "BUY/SELL/HOLD",
  "asset": "BTC",
  "entry_price": 45000,
  "stop_loss": 43500,
  "take_profit": 48000,
  "position_size_percent": 10,
  "confidence_score": 0.75,
  "reasoning": "Clear explanation of the decision rationale"
}

Your decision should be clear, justified by data, and formatted precisely for automated systems.
""",
                llm_config=llm_config
            )
            
            # 5. User Proxy Agent - Orchestrates the conversation
            self.agents["user_proxy"] = UserProxyAgent(
                name="TradingSystemUser",
                human_input_mode="NEVER",
                code_execution_config={"last_n_messages": 3, "work_dir": "agents"},
                system_message="""You are the coordination agent that manages the conversation between specialist agents.
Your role is to ensure the conversation flows logically between agents to produce a structured trading decision.
You never provide your own analysis, but rather direct the conversation to the appropriate specialist.

Working with these specialist agents:
1. MarketAnalyst - Technical analysis expert
2. StrategyAdvisor - Trading strategy expert
3. RiskManager - Risk assessment expert 
4. TradingDecisionAgent - Final decision maker

Your goal is to facilitate a structured decision-making process that results in a clear trading decision.
""",
                function_map=self.function_map
            )
            
            # Record initialization success
            self.initialized = True
            logger.info("Successfully initialized all agents in the structured decision system.")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing agents: {str(e)}")
            return False
    
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
                logger.warning("No JSON found in decision text. Attempting to extract structured data.")
                
                # Fallback: For now, return a default decision
                # This should be improved to parse text
                return {
                    "decision": "HOLD",
                    "asset": "Unknown",
                    "confidence_score": 0.0,
                    "reasoning": "Failed to parse decision from agent output.",
                    "error": "No valid decision format found in agent output."
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing decision JSON: {str(e)}")
            # Return a default decision with error
            return {
                "decision": "HOLD",
                "asset": "Unknown",
                "confidence_score": 0.0,
                "reasoning": "Failed to parse decision JSON.",
                "error": str(e)
            }
    
    def run_trading_session(self, symbol: str, objective: str = None) -> Dict[str, Any]:
        """
        Run a trading decision session with all agents.
        
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
                    "message": "Failed to initialize agent system"
                }
        
        start_time = datetime.now()
        logger.info(f"Starting trading session for {symbol} at {start_time.isoformat()}")
        
        # Get initial market data
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
            
            # Access user proxy and market analyst agents
            user_proxy = self.agents["user_proxy"]
            market_analyst = self.agents["market_analyst"]
            strategy_advisor = self.agents["strategy_advisor"]
            risk_manager = self.agents["risk_manager"]
            trading_decision_agent = self.agents["trading_decision"]
            
            # Formulate the initial prompt
            if not objective:
                objective = f"Analyze current market conditions for {symbol} and determine if a trade is recommended"
            
            prompt = f"""
I need a collaborative trading decision for {symbol} currently priced at {price_str}.
{market_summary}

Objective: {objective}

Follow this structured process:
1. MarketAnalyst: Begin by retrieving the latest market data and providing a thorough technical analysis
2. StrategyAdvisor: Review the market analysis and assess which trading strategies may be effective
3. RiskManager: Evaluate the potential risk factors and suggest risk mitigation measures
4. TradingDecisionAgent: Make a final trading decision in the required JSON format
                
Use the database query functions as needed to access real-time market data.
"""
            
            logger.info(f"Starting collaborative decision session for {symbol} at {price_str}")
            
            # Start the conversation with the market analyst
            user_proxy.initiate_chat(
                market_analyst,
                message=prompt,
                clear_history=True,
                timeout=self.max_session_time
            )
            
            # Continue the conversation with strategy advisor
            user_proxy.send(
                strategy_advisor,
                message="Based on the market analysis above, what trading strategies would be appropriate? Use functions to get additional data as needed."
            )
            
            # Continue the conversation with risk manager
            user_proxy.send(
                risk_manager,
                message="Based on the market analysis and strategy recommendations above, what are the key risk factors to consider? Please assess appropriate risk management measures including position sizing, stop loss levels and risk-reward ratio."
            )
            
            # Get final decision from trading decision agent
            user_proxy.send(
                trading_decision_agent,
                message="Based on all the analysis above from the Market Analyst, Strategy Advisor, and Risk Manager, please make a final trading decision in the required JSON format with decision, asset, entry_price, stop_loss, take_profit, position_size_percent, confidence_score, and reasoning fields."
            )
            
            # Extract decision from the trading decision agent's response
            decision_text = trading_decision_agent.last_message()["content"]
            
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
            session_log_file = os.path.join(self.log_dir, f"{self.session_id}_{symbol.lower()}.json")
            
            # Structure the session data
            session_data = {
                "session_id": self.session_id,
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
            logger.error(f"Error in trading session: {str(e)}")
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
    """Test the structured decision manager"""
    import os
    
    # Check OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return

    try:
        # Create manager
        manager = StructuredDecisionManager()
        
        # Initialize
        initialized = manager.initialize()
        if not initialized:
            print("Failed to initialize structured decision manager")
            return
        
        # Run a test session
        symbol = "BTCUSDT"
        print(f"Running test session for {symbol}...")
        
        result = manager.run_trading_session(symbol)
        
        # Display result
        if result["status"] == "success":
            decision = result["decision"]
            print(f"\nDecision: {decision['decision']} {symbol}")
            print(f"Entry: ${decision.get('entry_price', 'N/A')}")
            print(f"Stop Loss: ${decision.get('stop_loss', 'N/A')}")
            print(f"Take Profit: ${decision.get('take_profit', 'N/A')}")
            print(f"Position Size: {decision.get('position_size_percent', 'N/A')}%")
            print(f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%")
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