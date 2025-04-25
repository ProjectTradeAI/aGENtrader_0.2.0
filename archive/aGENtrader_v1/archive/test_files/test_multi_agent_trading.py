"""
Multi-Agent Trading System Test

Tests the complete workflow of multi-agent trading system with:
1. Database integration for market data retrieval
2. Agent communication and collaboration
3. Decision making process
4. Log output in structured format

This script provides a comprehensive test of the system's core functionality.
"""

import os
import json
import asyncio
import logging
import datetime
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("multi_agent_test")

# Import custom modules
from utils.test_logging import TestLogger, format_chat_history, display_header
from agents.database_retrieval_tool import (
    get_db_tool,
    get_recent_market_data,
    get_latest_price,
    CustomJSONEncoder
)
from agents.autogen_db_integration import create_speaker_llm_config

# Try to import AutoGen
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
    AUTOGEN_AVAILABLE = True
except ImportError:
    logger.warning("AutoGen not available. Running in simulation mode.")
    AUTOGEN_AVAILABLE = False

class MultiAgentTradingTest:
    """Test harness for multi-agent trading system"""
    
    def __init__(self, log_dir: str = "data/logs/current_tests"):
        """Initialize the test harness"""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize test logger
        self.test_logger = TestLogger(log_dir=log_dir, prefix="trading_system")
        
        # Set up OpenAI config
        self.openai_config = self._setup_openai_config()
        
        # Test configuration
        self.symbol = "BTCUSDT"
        self.timeframe = "1h"
        self.test_id = f"multi_agent_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Database functions
        self.db_functions = {
            "get_latest_price": get_latest_price,
            "get_recent_market_data": get_recent_market_data,
        }
    
    def _setup_openai_config(self) -> Optional[Dict[str, Any]]:
        """Set up OpenAI API configuration"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OpenAI API key found in environment variables")
            return None
        
        return {
            "model": "gpt-3.5-turbo-0125",
            "temperature": 0,
            "config_list": [{"model": "gpt-3.5-turbo-0125", "api_key": api_key}]
        }
    
    def _create_market_analyst(self) -> Optional[AssistantAgent]:
        """Create market analyst agent"""
        if not AUTOGEN_AVAILABLE or not self.openai_config:
            return None
            
        # Create function definitions
        function_defs = [
            {
                "name": "get_latest_price",
                "description": "Get the latest price data for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol, e.g., BTCUSDT"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_recent_market_data",
                "description": "Get a list of recent market data points for a cryptocurrency symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The trading symbol, e.g., BTCUSDT"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of data points to retrieve"
                        }
                    },
                    "required": ["symbol", "limit"]
                }
            }
        ]
        
        # Add functions to config
        llm_config = self.openai_config.copy()
        llm_config["functions"] = function_defs
        
        # Create the agent
        return AssistantAgent(
            name="MarketAnalyst",
            system_message="""You are a cryptocurrency market analyst specializing in technical analysis.
You have access to market data through function calls and MUST USE THEM to get real data.
DO NOT make up or invent price data - ALWAYS call the appropriate functions.

Your role is to analyze market data and provide detailed insights on:
1. Price trends and patterns
2. Support and resistance levels
3. Volatility assessment
4. Recent price movements

Be precise, quantitative, and focus on facts derived from the data.""",
            llm_config=llm_config
        )
    
    def _create_strategy_advisor(self) -> Optional[AssistantAgent]:
        """Create strategy advisor agent"""
        if not AUTOGEN_AVAILABLE or not self.openai_config:
            return None
            
        # Create the agent without direct function access
        # It will rely on the analyst's data
        return AssistantAgent(
            name="StrategyAdvisor",
            system_message="""You are a cryptocurrency trading strategy advisor.
Your role is to interpret market analysis and recommend specific trading strategies.

Focus on:
1. Recommending clear buy, sell, or hold actions with confidence levels
2. Suggesting entry and exit points
3. Providing risk assessment
4. Explaining your reasoning

You should base your recommendations on the market analyst's data and insights.
Be specific about price targets, stop-loss levels, and risk/reward ratios.""",
            llm_config=self.openai_config
        )
    
    def _create_portfolio_manager(self) -> Optional[AssistantAgent]:
        """Create portfolio manager agent"""
        if not AUTOGEN_AVAILABLE or not self.openai_config:
            return None
            
        # Create the agent
        return AssistantAgent(
            name="PortfolioManager",
            system_message="""You are a cryptocurrency portfolio manager.
Your role is to make final trading decisions based on market analysis and strategy recommendations.

You should:
1. Evaluate trading recommendations critically
2. Make a final decision: BUY, SELL, or HOLD with specific parameters
3. Consider position sizing and portfolio impact
4. Document your decision rationale clearly

Your decisions should be presented as a formal decision summary with:
- Action: (BUY/SELL/HOLD)
- Confidence: (0-100%)
- Entry/Exit: (price targets)
- Stop-Loss: (price level)
- Take-Profit: (price level)
- Position Size: (% of portfolio)
- Timeframe: (short/medium/long term)""",
            llm_config=self.openai_config
        )
    
    def _create_user_proxy(self) -> Optional[UserProxyAgent]:
        """Create user proxy agent"""
        if not AUTOGEN_AVAILABLE:
            return None
            
        return UserProxyAgent(
            name="TradingSystem",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            function_map=self.db_functions
        )
    
    async def test_single_agent_analysis(self) -> Dict[str, Any]:
        """Test single agent market analysis"""
        display_header("Testing Single Agent Market Analysis")
        
        if not AUTOGEN_AVAILABLE or not self.openai_config:
            logger.warning("Test skipped: AutoGen not available")
            return {"status": "skipped", "reason": "AutoGen not available"}
        
        # Log session start
        session_id = f"single_agent_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_logger.log_session_start("single_agent", {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "session_id": session_id
        })
        
        # Create agents
        analyst = self._create_market_analyst()
        user_proxy = self._create_user_proxy()
        
        if not analyst or not user_proxy:
            logger.error("Failed to create required agents")
            return {"status": "error", "reason": "Failed to create agents"}
        
        # Test message
        message = f"""Analyze the current market for {self.symbol} by following these steps:
1. Get the latest price data for {self.symbol}
2. Get the 10 most recent price points
3. Calculate key metrics (price change %, volatility)
4. Identify any significant patterns or trends
5. Provide a concise market summary with your assessment"""
        
        try:
            # Start conversation with timeout
            chat_result = user_proxy.initiate_chat(
                analyst,
                message=message,
                max_turns=6
            )
            
            # Process results
            result = {
                "status": "success",
                "symbol": self.symbol,
                "session_id": session_id,
                "chat_history": chat_result.chat_history,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Log session end
            self.test_logger.log_session_end("single_agent", result)
            
            # Save chat history
            self.test_logger.save_chat_history(
                chat_result.chat_history,
                session_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in single agent test: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def test_multi_agent_collaboration(self) -> Dict[str, Any]:
        """Test collaboration between multiple agents"""
        display_header("Testing Multi-Agent Collaboration")
        
        if not AUTOGEN_AVAILABLE or not self.openai_config:
            logger.warning("Test skipped: AutoGen not available")
            return {"status": "skipped", "reason": "AutoGen not available"}
        
        # Log session start
        session_id = f"multi_agent_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_logger.log_session_start("multi_agent", {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "session_id": session_id
        })
        
        # Create agents
        analyst = self._create_market_analyst()
        advisor = self._create_strategy_advisor()
        manager = self._create_portfolio_manager()
        user_proxy = self._create_user_proxy()
        
        if not analyst or not advisor or not manager or not user_proxy:
            logger.error("Failed to create required agents")
            return {"status": "error", "reason": "Failed to create agents"}
        
        # Group chat message
        message = f"""Coordinate a trading decision for {self.symbol} with the following process:
1. MarketAnalyst: Analyze current market data for {self.symbol} including latest price and recent trends
2. StrategyAdvisor: Review the analysis and recommend a trading strategy with entry/exit points
3. PortfolioManager: Make a final trading decision with specific parameters
4. All agents: Reach consensus on the final recommendation

The goal is to produce a well-reasoned trading decision backed by actual market data."""
        
        try:
            # Start group chat with timeout
            groupchat = autogen.GroupChat(
                agents=[user_proxy, analyst, advisor, manager],
                messages=[],
                max_round=10
            )
            # Use a clean config without function tools for GroupChatManager
            speaker_llm_config = create_speaker_llm_config(self.openai_config)
            manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=speaker_llm_config)
            
            chat_result = user_proxy.initiate_chat(
                manager,
                message=message
            )
            
            # Process results
            result = {
                "status": "success",
                "symbol": self.symbol,
                "session_id": session_id,
                "chat_history": chat_result.chat_history,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Log session end
            self.test_logger.log_session_end("multi_agent", result)
            
            # Save chat history
            self.test_logger.save_chat_history(
                chat_result.chat_history,
                session_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-agent test: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def test_decision_workflow(self) -> Dict[str, Any]:
        """Test sequential decision workflow"""
        display_header("Testing Trading Decision Workflow")
        
        if not AUTOGEN_AVAILABLE or not self.openai_config:
            logger.warning("Test skipped: AutoGen not available")
            return {"status": "skipped", "reason": "AutoGen not available"}
        
        # Log session start
        session_id = f"decision_workflow_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_logger.log_session_start("decision_workflow", {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "session_id": session_id
        })
        
        # Create agents
        analyst = self._create_market_analyst()
        advisor = self._create_strategy_advisor()
        manager = self._create_portfolio_manager()
        user_proxy = self._create_user_proxy()
        
        if not analyst or not advisor or not manager or not user_proxy:
            logger.error("Failed to create required agents")
            return {"status": "error", "reason": "Failed to create agents"}
        
        try:
            # 1. First, get market analysis
            analysis_message = f"""Perform a detailed market analysis for {self.symbol}:
1. Get the latest price data
2. Analyze recent price movements (last 10-15 data points)
3. Identify key support and resistance levels
4. Assess current market volatility
5. Determine the overall market trend (bullish, bearish, or neutral)
6. Provide a comprehensive summary of your findings"""
            
            analysis_result = user_proxy.initiate_chat(
                analyst,
                message=analysis_message,
                max_turns=5
            )
            
            # Extract the last substantive message from the analyst
            analyst_messages = [msg for msg in analysis_result.chat_history if msg.get("role") == "assistant"]
            analysis_content = analyst_messages[-1].get("content", "") if analyst_messages else "No analysis provided."
            
            # 2. Next, get strategy recommendation
            strategy_message = f"""Based on the following market analysis for {self.symbol}, recommend a specific trading strategy:

{analysis_content}

Please include:
1. A clear trading recommendation (buy, sell, or hold)
2. Specific entry and exit price points
3. Stop-loss and take-profit levels
4. Risk assessment and position sizing guidance
5. Timeframe for the strategy (short, medium, or long term)"""
            
            strategy_result = user_proxy.initiate_chat(
                advisor,
                message=strategy_message,
                max_turns=3
            )
            
            # Extract the last substantive message from the advisor
            advisor_messages = [msg for msg in strategy_result.chat_history if msg.get("role") == "assistant"]
            strategy_content = advisor_messages[-1].get("content", "") if advisor_messages else "No strategy provided."
            
            # 3. Finally, get portfolio manager decision
            decision_message = f"""Based on the market analysis and strategy recommendation for {self.symbol}, make a final trading decision:

MARKET ANALYSIS:
{analysis_content}

STRATEGY RECOMMENDATION:
{strategy_content}

Please provide a formal decision with:
- Action: (BUY/SELL/HOLD)
- Confidence: (0-100%)
- Entry/Exit: (price targets)
- Stop-Loss: (price level)
- Take-Profit: (price level)
- Position Size: (% of portfolio)
- Timeframe: (short/medium/long term)
- Rationale: (brief explanation)"""
            
            decision_result = user_proxy.initiate_chat(
                manager,
                message=decision_message,
                max_turns=2
            )
            
            # Extract the last substantive message from the manager
            manager_messages = [msg for msg in decision_result.chat_history if msg.get("role") == "assistant"]
            decision_content = manager_messages[-1].get("content", "") if manager_messages else "No decision provided."
            
            # Combine all results
            all_messages = (
                analysis_result.chat_history +
                strategy_result.chat_history +
                decision_result.chat_history
            )
            
            # Process results
            result = {
                "status": "success",
                "symbol": self.symbol,
                "session_id": session_id,
                "analysis": analysis_content,
                "strategy": strategy_content,
                "decision": decision_content,
                "chat_history": all_messages,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Log session end
            self.test_logger.log_session_end("decision_workflow", result)
            
            # Save chat history
            self.test_logger.save_chat_history(
                all_messages,
                session_id
            )
            
            # Save full session data
            self.test_logger.save_full_session(
                result,
                session_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in decision workflow test: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests sequentially"""
        display_header("Running All Multi-Agent Trading System Tests")
        
        results = {}
        
        # Run single agent test
        display_header("1. Single Agent Market Analysis")
        single_result = await self.test_single_agent_analysis()
        results["single_agent"] = single_result
        
        # Run multi-agent collaboration test
        display_header("2. Multi-Agent Collaboration")
        multi_result = await self.test_multi_agent_collaboration()
        results["multi_agent"] = multi_result
        
        # Run decision workflow test
        display_header("3. Trading Decision Workflow")
        workflow_result = await self.test_decision_workflow()
        results["decision_workflow"] = workflow_result
        
        # Save summary results
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(self.log_dir, f"test_summary_{timestamp}.json")
        
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        with open(summary_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "test_id": self.test_id,
                    "results": results
                },
                f,
                cls=CustomJSONEncoder,
                indent=2
            )
        
        logger.info(f"Test summary saved to {summary_file}")
        return results

async def main():
    """Main entry point"""
    try:
        # Run the multi-agent trading system test
        test_harness = MultiAgentTradingTest()
        results = await test_harness.run_all_tests()
        
        # Display final status
        display_header("Test Results Summary")
        
        for test_name, result in results.items():
            status = result.get("status", "unknown")
            if status == "success":
                print(f"✅ {test_name}: Success")
            elif status == "skipped":
                print(f"⏭️ {test_name}: Skipped - {result.get('reason', 'Unknown reason')}")
            else:
                print(f"❌ {test_name}: Failed - {result.get('error', 'Unknown error')}")
                
        print("\nTests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())