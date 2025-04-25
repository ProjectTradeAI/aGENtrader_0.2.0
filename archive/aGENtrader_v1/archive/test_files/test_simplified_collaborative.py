"""
Simplified test script for collaborative trading decision

Tests the collaborative agent-based decision making with reduced complexity
to avoid timeout issues.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("collaborative_test")

# Import test logger
from utils.test_logging import TestLogger, display_header, CustomJSONEncoder

# Import database functions
from agents.database_retrieval_tool import (
    get_latest_price,
    get_recent_market_data,
    calculate_moving_average,
    calculate_rsi,
    get_market_summary
)

# Import AutoGen integration functions
from agents.autogen_db_integration import (
    create_market_data_function_map,
    create_db_function_specs,
    enhance_llm_config,
    create_speaker_llm_config,
    format_trading_decision
)

# Try to import AutoGen
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
    AUTOGEN_AVAILABLE = True
except ImportError:
    logger.warning("AutoGen not available. Running in simulation mode.")
    AUTOGEN_AVAILABLE = False

def display_header(title: str) -> None:
    """Display formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def setup_openai_config() -> Optional[Dict[str, Any]]:
    """Configure OpenAI settings for agents"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OpenAI API key not found in environment")
        return None
    
    # Basic configuration
    config = {
        "model": "gpt-3.5-turbo-0125",
        "temperature": 0.1,
        "top_p": 0.5,
        "config_list": [{"model": "gpt-3.5-turbo-0125", "api_key": api_key}]
    }
    
    return config

def test_simplified_collaborative(symbol: str = "BTCUSDT") -> None:
    """Run simplified collaborative decision test"""
    test_logger = TestLogger(log_dir="data/logs/current_tests", prefix="collab")
    
    display_header("Starting Simplified Collaborative Analysis Test")
    
    if not AUTOGEN_AVAILABLE:
        logger.error("Test cannot run: AutoGen is not available")
        return
    
    # Set up OpenAI configuration
    config = setup_openai_config()
    if not config:
        logger.error("Test cannot run: OpenAI API configuration not available")
        return
    
    # Test parameters
    params = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "agent_count": 3,  # Number of specialized agents
        "max_turns": 5,    # Increased conversation length for better completion
    }
    
    test_logger.log_session_start("collaborative", params)
    
    try:
        # Get market data for analysis
        price_data_json = get_latest_price(symbol)
        if not price_data_json:
            logger.error(f"Failed to get price data for {symbol}")
            test_logger.log_session_end("collaborative", {"status": "error", "reason": "Database error"})
            return
        
        # Parse JSON response
        price_data = json.loads(price_data_json)
        current_price = price_data["close"]
        timestamp = price_data["timestamp"]
        
        # Get recent market data
        recent_data_json = get_recent_market_data(symbol, 10)
        if not recent_data_json:
            logger.error(f"Failed to get recent market data for {symbol}")
            test_logger.log_session_end("collaborative", {"status": "error", "reason": "Database error"})
            return
        
        # Calculate indicators
        rsi_json = calculate_rsi(symbol)
        sma_json = calculate_moving_average(symbol)
        summary_json = get_market_summary(symbol)
        
        # Enhance LLM config with database function specs
        llm_config = enhance_llm_config(config)
        function_map = create_market_data_function_map()
        
        # Create specialized agents
        market_analyst = AssistantAgent(
            name="MarketAnalyst",
            system_message=f"""You are a cryptocurrency market analyst specializing in technical analysis.
Your job is to analyze market data for {symbol} and identify patterns and trends.
Focus on price action, volume, and technical indicators.
Use the database access functions to get real market data.
Provide a clear analysis with concrete observations about recent market behavior.""",
            llm_config=llm_config
        )
        
        risk_manager = AssistantAgent(
            name="RiskManager",
            system_message=f"""You are a risk management specialist focusing on cryptocurrency markets.
Your job is to assess the risk level of trading {symbol} based on market conditions.
Consider volatility, liquidity, market sentiment, and potential downside.
Use the database access functions to get real market data.
Provide a risk assessment with a clear risk rating (low/medium/high).""",
            llm_config=llm_config
        )
        
        trading_advisor = AssistantAgent(
            name="TradingAdvisor",
            system_message=f"""You are a cryptocurrency trading advisor specializing in actionable recommendations.
Your job is to synthesize market analysis and risk assessment to provide a final trading recommendation.
Consider both technical patterns and risk metrics when making a decision.
Use the database access functions to get real market data if needed.
Provide a clear BUY, SELL, or HOLD recommendation with confidence level and reasoning.
Format your final recommendation in JSON with these keys: action, confidence, reasoning, price, risk_level.""",
            llm_config=llm_config
        )
        
        moderator = UserProxyAgent(
            name="Moderator",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            system_message="""You are the moderator of this group discussion about cryptocurrency trading.
Your job is to facilitate a productive conversation between the specialists and guide them to a consensus decision.
First, ask the Market Analyst to provide their technical analysis.
Then, ask the Risk Manager to assess the current risk level.
Finally, ask the Trading Advisor to synthesize the information and make a recommendation.
Keep the conversation focused and goal-oriented.""",
            function_map=function_map
        )
        
        # Prepare initial message with current market data
        initial_message = f"""
Let's analyze the current market conditions for {symbol} and come to a trading decision.

Current market data:
- Symbol: {symbol}
- Current Price: ${current_price}
- Latest Data Timestamp: {timestamp}

Please follow this process:
1. Market Analyst: Provide technical analysis of recent price action and indicators
2. Risk Manager: Assess the current risk level based on market conditions
3. Trading Advisor: Synthesize the analysis and recommend a trading action (BUY/SELL/HOLD)

Let's proceed in an orderly fashion with each specialist contributing their expertise.
"""
        
        display_header("Starting Collaborative Discussion")
        print(f"Topic: Trading decision for {symbol} at ${current_price}")
        
        # Run the group chat
        groupchat = autogen.GroupChat(
            agents=[moderator, market_analyst, risk_manager, trading_advisor],
            messages=[],
            max_round=params["max_turns"]
        )
        
        # Use a clean config without function tools for GroupChatManager
        speaker_llm_config = create_speaker_llm_config(config)
        group_manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=speaker_llm_config)
        
        # Start the chat
        chat_result = moderator.initiate_chat(
            group_manager,
            message=initial_message
        )
        
        # Process the results
        chat_history = chat_result.chat_history
        decision = None
        
        # Try to extract the final decision
        for message in reversed(chat_history):
            if message.get("name") == "TradingAdvisor":
                # Handle None content values explicitly
                content = message.get("content")
                if content is None:
                    logger.warning("TradingAdvisor message has None content")
                    continue
                    
                # Convert content to string if it's not already
                content = str(content)
                
                try:
                    # Try to find JSON in the content
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx+1]
                        decision_data = json.loads(json_str)
                        decision = format_trading_decision(decision_data)
                        decision["symbol"] = symbol
                        decision["timestamp"] = datetime.now().isoformat()
                        break
                except Exception as e:
                    logger.warning(f"Failed to extract decision from message: {str(e)}")
        
        # Log and save results
        session_result = {
            "status": "success" if decision else "incomplete",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "chat_history": chat_history,
            "decision": decision
        }
        
        # Save results
        test_logger.save_chat_history(chat_history, f"collab_{symbol}")
        test_logger.save_full_session(session_result, f"collab_{symbol}")
        test_logger.log_session_end("collaborative", {
            "status": session_result["status"],
            "decision": decision
        })
        
        display_header("Collaborative Analysis Completed")
        if decision:
            print(f"Decision: {decision['action']} {symbol} (Confidence: {decision['confidence']}%)")
            print(f"Reasoning: {decision['reasoning'][:100]}...")
        else:
            print("No conclusive decision was reached.")
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error during collaborative test: {str(e)}\n{error_trace}")
        test_logger.log_session_end("collaborative", {
            "status": "error",
            "error": str(e),
            "traceback": error_trace
        })

def main() -> None:
    """Main entry point"""
    display_header("Simplified Collaborative Decision Test")
    
    # Check if OpenAI API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OpenAI API key not found in environment variables")
        print("Please set the OPENAI_API_KEY environment variable and try again")
        return
    
    # Run the test with default parameters
    symbol = "BTCUSDT"
    print(f"Running collaborative analysis for {symbol}...")
    test_simplified_collaborative(symbol)

if __name__ == "__main__":
    main()