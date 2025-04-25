"""
Test Collaborative Agent

This script tests the collaborative decision agent implementation and verifies 
that it can properly interact with the database and generate trading decisions.
"""

import os
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test the database connection"""
    logger.info("Testing database connection...")
    
    from utils.database_manager import get_db_manager
    
    try:
        # Get the database manager
        db_manager = get_db_manager()
        
        # Execute a simple query
        result = db_manager.execute_query("SELECT 1 as test")
        
        if result and result[0].get('test') == 1:
            logger.info("✓ Database connection successful")
            return True
        else:
            logger.error("✗ Database connection test failed")
            return False
    
    except Exception as e:
        logger.error(f"✗ Database connection error: {str(e)}")
        return False

def test_collaborative_agent(symbol: str = "BTCUSDT", test_mode: bool = True):
    """
    Test the collaborative agent implementation
    
    Args:
        symbol: Symbol to analyze
        test_mode: Whether to run in test mode (shorter response)
    """
    logger.info(f"Testing collaborative agent with symbol: {symbol}")
    
    try:
        from agents.collaborative_decision_agent import CollaborativeDecisionFramework
        
        # Check API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found in environment variables")
            return False
        
        # Create the collaborative decision framework
        framework = CollaborativeDecisionFramework(
            api_key=api_key,
            max_session_time=60 if test_mode else 120
        )
        
        # Prepare a custom prompt for test mode
        prompt = None
        if test_mode:
            prompt = f"""
            This is a quick test of the collaborative decision agent for {symbol}.
            
            As this is only a test run, please keep all responses extremely brief:
            
            1. MarketAnalyst: Just retrieve and state the latest price for {symbol}
            2. StrategyManager: Give a one-sentence strategy assessment 
            3. RiskManager: Provide a one-sentence risk assessment with suggested stop-loss percentage
            4. TradingDecisionAgent: Make a final trading decision in the EXACT format below:
            
            ```json
            {{
              "decision": "BUY or SELL or HOLD",
              "asset": "{symbol}",
              "entry_price": 88000,
              "stop_loss": 87000,
              "take_profit": 90000,
              "confidence_score": 0.75,
              "reasoning": "Very brief explanation of your decision"
            }}
            ```
            
            THIS IS A TEST - all agents must be extremely concise. The final decision MUST include ALL fields shown above.
            """
        
        # Run the decision session
        logger.info("Running collaborative decision session...")
        decision = framework.run_decision_session(symbol=symbol, prompt=prompt)
        
        # Print the decision
        logger.info(f"Decision received: {decision.get('decision', 'ERROR')}")
        logger.info(json.dumps(decision, indent=2))
        
        # Validate the decision
        if 'error' in decision:
            logger.error(f"✗ Decision error: {decision.get('error')}")
            return False
            
        # Check for required fields
        required_fields = ['decision', 'asset', 'entry_price', 'stop_loss', 
                         'take_profit', 'confidence_score', 'reasoning']
        
        missing_fields = [field for field in required_fields if field not in decision]
        
        if missing_fields:
            logger.error(f"✗ Missing required fields in decision: {missing_fields}")
            return False
        
        logger.info(f"✓ Collaborative agent test successful for {symbol}")
        return True
    
    except Exception as e:
        logger.error(f"✗ Error testing collaborative agent: {str(e)}")
        return False

def main():
    """Main test function"""
    try:
        # Test database connection
        db_success = test_database_connection()
        if not db_success:
            logger.error("Database connection test failed, aborting further tests")
            return "Database connection test failed"
        
        # Test collaborative agent
        agent_success = test_collaborative_agent(symbol="BTCUSDT", test_mode=True)
        
        if db_success and agent_success:
            return "All tests passed successfully!"
        else:
            return "Some tests failed, check the logs for details"
    
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        return f"Error during testing: {str(e)}"

if __name__ == "__main__":
    result = main()
    print(f"\nTest Result: {result}")