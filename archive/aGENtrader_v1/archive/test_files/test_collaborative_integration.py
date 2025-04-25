"""
Test Collaborative Integration

This script tests the collaborative integration between AutoGen agents
and the database retrieval tool for market analysis.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Warning: AutoGen not available. Cannot run collaborative integration test.")

# Import agent factory
from agents.trading_agents import TradingAgentFactory, AUTOGEN_AVAILABLE
from agents.autogen_db_integration import create_speaker_llm_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("collaborative_integration")

def setup_openai_config() -> Optional[Dict[str, Any]]:
    """Set up OpenAI API configuration"""
    # Check if API key is available
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return None
    
    # Create configuration
    config_list = [
        {
            "model": "gpt-3.5-turbo-0125",
            "api_key": openai_api_key
        }
    ]
    
    return {
        "config_list": config_list,
        "temperature": 0.1,
        "seed": 42
    }

def generate_agent_task(symbol: str) -> str:
    """Generate the initial task for agents"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
I need a collaborative market analysis for {symbol}. 

Current timestamp: {timestamp}

Please perform the following tasks:
1. Retrieve and analyze recent market data for {symbol}
2. Identify key price patterns and trends
3. Calculate and interpret technical indicators
4. Identify support and resistance levels
5. Assess current market volatility
6. Generate a trading recommendation based on your analysis
7. Provide a clear rationale for your recommendation

This is a collaborative task that requires:
- Market analysis with technical indicators
- Pattern recognition and trend identification
- Risk assessment based on volatility
- Strategic recommendation based on all factors

Let's work together to generate a comprehensive market analysis that
can inform trading decisions.
"""

def test_collaborative_integration(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Test collaborative integration between agents and database
    
    Args:
        symbol: Trading symbol to analyze
        
    Returns:
        Test results
    """
    # Skip if AutoGen is not available
    if not AUTOGEN_AVAILABLE:
        logger.error("AutoGen is not available. Skipping test.")
        return {"status": "skipped", "reason": "AutoGen not available"}
    
    # Set up OpenAI configuration
    llm_config = setup_openai_config()
    if not llm_config:
        logger.error("Failed to set up LLM configuration. Skipping test.")
        return {"status": "skipped", "reason": "LLM configuration failed"}
    
    # Start timestamp
    start_time = datetime.now()
    
    logger.info(f"Starting collaborative integration test for {symbol}")
    
    # Create agents using static methods
    
    # Market analyst
    market_analyst = TradingAgentFactory.create_market_analyst({
        "llm_config": llm_config
    })
    
    # Strategy advisor
    strategy_advisor = TradingAgentFactory.create_strategy_advisor({
        "llm_config": llm_config
    })
    
    # Risk manager
    risk_manager = TradingAgentFactory.create_risk_manager({
        "llm_config": llm_config
    })
    
    # Create user proxy agent
    user_proxy = TradingAgentFactory.create_user_proxy(
        name="TradingSystemProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10
    )
    
    # Create group chat
    groupchat = autogen.GroupChat(
        agents=[user_proxy, market_analyst, strategy_advisor, risk_manager],
        messages=[],
        max_round=12
    )
    
    # Create group chat manager with a clean LLM config (no function tools)
    speaker_llm_config = create_speaker_llm_config(llm_config)
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=speaker_llm_config  # Use clean config without function tools
    )
    
    logger.info("Starting group chat")
    
    # Generate task
    task = generate_agent_task(symbol)
    
    # Start the conversation
    try:
        user_proxy.initiate_chat(
            manager,
            message=task,
            clear_history=True
        )
        
        logger.info("Group chat completed")
        
        # Extract chat history
        chat_history = []
        for message in groupchat.messages:
            chat_history.append({
                "sender": message.get("sender", "unknown"),
                "content": message.get("content", "")
            })
        
        # End timestamp
        end_time = datetime.now()
        
        # Format results
        results = {
            "status": "completed",
            "symbol": symbol,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "execution_time_seconds": (end_time - start_time).total_seconds(),
            "message_count": len(chat_history),
            "chat_history": chat_history
        }
        
        logger.info(f"Test completed successfully in {results['execution_time_seconds']:.2f} seconds")
        
        return results
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        
        # End timestamp
        end_time = datetime.now()
        
        # Format error results
        error_results = {
            "status": "error",
            "symbol": symbol,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "execution_time_seconds": (end_time - start_time).total_seconds(),
            "error": str(e)
        }
        
        return error_results

def save_results(results: Dict[str, Any]) -> str:
    """
    Save test results to file
    
    Args:
        results: Test results dictionary
        
    Returns:
        Path to saved file
    """
    # Create output directory
    os.makedirs("data/logs/current_tests", exist_ok=True)
    
    # Generate filename based on timestamp
    timestamp = int(time.time())
    filename = f"data/logs/current_tests/collab_integration_{timestamp}.json"
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {filename}")
    
    return filename

def main():
    """Main entry point"""
    # Parse symbol from command line
    symbol = "BTCUSDT"
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    
    # Run test
    results = test_collaborative_integration(symbol)
    
    # Save results
    save_path = save_results(results)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f" Collaborative Integration Test Results ".center(60, "="))
    print("=" * 60)
    print(f"Status: {results['status']}")
    print(f"Symbol: {results['symbol']}")
    print(f"Start time: {results['start_time']}")
    print(f"End time: {results['end_time']}")
    print(f"Execution time: {results['execution_time_seconds']:.2f} seconds")
    
    if results['status'] == "completed":
        print(f"Message count: {results['message_count']}")
    elif results['status'] == "error":
        print(f"Error: {results['error']}")
    
    print(f"\nResults saved to: {save_path}")
    print("To view detailed results, run: python view_test_results.py --session-id [SESSION_ID]")

if __name__ == "__main__":
    main()