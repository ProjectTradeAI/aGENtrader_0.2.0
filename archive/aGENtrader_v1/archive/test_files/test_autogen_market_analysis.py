"""
Test script for AutoGen market analysis with optimized data format.

This script demonstrates how AutoGen agents can analyze market data retrieved 
from the database with proper serialization of datetime and Decimal values.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check for AutoGen availability
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
    from agents.autogen_db_integration import get_integration
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("AutoGen not installed, skipping test")
    exit(1)

def print_section(title: str) -> None:
    """Print a section header for better readability"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "-"))
    print("="*80 + "\n")

def save_results(results: Dict[str, Any], file_prefix: str = "market_analysis"):
    """Save results to a JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/{file_prefix}_{timestamp}.json"
    
    os.makedirs("logs", exist_ok=True)
    
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {filename}")
    return filename

def setup_openai_config():
    """Set up OpenAI API config for AutoGen"""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        return None
    
    config_list = [
        {
            "model": "gpt-3.5-turbo",  
            "api_key": openai_api_key
        }
    ]
    
    return config_list

async def run_analysis():
    """Run market analysis with AutoGen agents using optimized data format"""
    print_section("AutoGen Market Analysis Test")
    
    # Set up OpenAI config
    config_list = setup_openai_config()
    if not config_list:
        print("⚠️ Skipping test: No OpenAI API key found")
        return False
    
    # Get AutoGen integration
    integration = get_integration(config_list)
    
    # Create market analyst agent
    market_analyst = integration.create_market_analyst(name="Market_Analyst")
    
    # Create strategy advisor agent
    strategy_advisor = integration.create_strategy_advisor(name="Strategy_Advisor")

    # Create a user proxy agent
    user_proxy = integration.create_user_proxy(
        name="User",
        human_input_mode="NEVER",
        code_execution_config={"work_dir": ".", "use_docker": False}
    )
    
    # Define analysis task
    analysis_task = """
    As a market analyst, please:
    
    1. Import the necessary functions with:
       from agents.database_retrieval_tool import get_db_tool, serialize_results
    
    2. Get the database tool:
       db_tool = get_db_tool()
       
    3. Get the market summary for BTCUSDT:
       market_summary = db_tool.get_market_summary('BTCUSDT')
       
    4. Analyze the market data and provide:
       - Current price and volume analysis
       - Key support and resistance levels
       - Moving average analysis
       - A short-term price prediction with confidence level
       - Trading recommendation (buy/sell/hold) with reasoning
       
    5. Format your analysis as a structured JSON response with proper serialization
    """
    
    # Start a group chat
    try:
        results = await user_proxy.a_initiate_chat(
            market_analyst,
            message=analysis_task
        )
        
        # Save results
        save_results({"chat_history": results.chat_history}, "market_analysis")
        
        print("\nMarket analysis test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during market analysis: {str(e)}")
        print(f"❌ Market analysis test failed with error: {str(e)}")
        return False

def main():
    """Main entry point"""
    asyncio.run(run_analysis())

if __name__ == "__main__":
    main()