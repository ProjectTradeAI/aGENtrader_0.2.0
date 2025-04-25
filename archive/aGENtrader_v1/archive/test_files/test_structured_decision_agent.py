"""
Test module for structured_decision_agent.py

This script tests the structured decision-making process for trading with
collaborative multi-agent interactions and database integration.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.structured_decision_agent import StructuredDecisionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_structured_decision")

def test_trading_session_with_symbol(symbol: str = "BTCUSDT", 
                                     objective: Optional[str] = None) -> Dict[str, Any]:
    """
    Test running a trading session with the specified symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        objective: Optional specific objective for the decision session
        
    Returns:
        Session result with trading decision
    """
    logger.info(f"Testing trading session with symbol {symbol}")
    
    # Create and initialize decision manager
    manager = StructuredDecisionManager(config={
        "log_dir": "test_outputs/structured_decisions",
        "model": "gpt-3.5-turbo-0125",  # Use lower cost model for testing
        "temperature": 0.1,             # Low temperature for consistency
        "max_session_time": 300         # 5 minutes max
    })
    
    # Initialize
    initialized = manager.initialize()
    if not initialized:
        logger.error("Failed to initialize structured decision manager")
        return {
            "status": "error",
            "message": "Failed to initialize manager"
        }
    
    # Set default objective if none provided
    if not objective:
        objective = f"Analyze current market conditions for {symbol} and recommend a trading decision with clear entry, exit and risk parameters"
    
    # Run trading session
    result = manager.run_trading_session(symbol, objective)
    
    # Log the result
    if result["status"] == "success":
        decision = result["decision"]
        logger.info(f"Decision: {decision.get('decision', 'UNKNOWN')} {symbol}")
        logger.info(f"Entry: ${decision.get('entry_price', 'N/A')}")
        logger.info(f"Stop Loss: ${decision.get('stop_loss', 'N/A')}")
        logger.info(f"Take Profit: ${decision.get('take_profit', 'N/A')}")
        logger.info(f"Position Size: {decision.get('position_size_percent', 'N/A')}%")
        logger.info(f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%")
        logger.info(f"Log file: {result.get('log_file', 'Not available')}")
    else:
        logger.error(f"Error: {result.get('message', 'Unknown error')}")
    
    return result

def validate_decision_format(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the format of a trading decision.
    
    Args:
        decision: Trading decision dictionary
        
    Returns:
        Validation result
    """
    required_fields = [
        "decision", "asset", "entry_price", "stop_loss", 
        "take_profit", "position_size_percent", "confidence_score", "reasoning"
    ]
    
    # Check for required fields
    missing_fields = [field for field in required_fields if field not in decision]
    
    # Check decision value
    decision_value = decision.get("decision", "").upper()
    valid_decisions = ["BUY", "SELL", "HOLD"]
    
    validation_result = {
        "is_valid": not missing_fields and decision_value in valid_decisions,
        "missing_fields": missing_fields,
        "decision_value_valid": decision_value in valid_decisions,
        "warnings": []
    }
    
    # Check for warnings
    confidence = decision.get("confidence_score", 0)
    position_size = decision.get("position_size_percent", 0)
    
    if confidence > 0.95:
        validation_result["warnings"].append("Suspiciously high confidence score")
    
    if position_size > 50:
        validation_result["warnings"].append("Unusually large position size")
    
    if position_size < 1 and decision_value in ["BUY", "SELL"]:
        validation_result["warnings"].append("Position size too small for a trade")
    
    # Analyze risk-reward ratio
    entry = decision.get("entry_price", 0)
    stop = decision.get("stop_loss", 0)
    target = decision.get("take_profit", 0)
    
    if entry and stop and target and entry != stop:
        if decision_value == "BUY":
            risk = (entry - stop) / entry if entry > 0 else 0
            reward = (target - entry) / entry if entry > 0 else 0
        elif decision_value == "SELL":
            risk = (stop - entry) / entry if entry > 0 else 0
            reward = (entry - target) / entry if entry > 0 else 0
        else:  # HOLD
            risk = 0
            reward = 0
        
        if risk > 0:
            risk_reward_ratio = reward / risk
            validation_result["risk_reward_ratio"] = risk_reward_ratio
            
            if risk_reward_ratio < 1:
                validation_result["warnings"].append("Risk-reward ratio below 1:1")
    
    return validation_result

def examine_session_log(log_file_path: str) -> Dict[str, Any]:
    """
    Examine a session log file.
    
    Args:
        log_file_path: Path to the session log file
        
    Returns:
        Analysis of the session log
    """
    try:
        # Load session log
        with open(log_file_path, 'r') as f:
            session_data = json.load(f)
        
        # Extract key information
        decision = session_data.get("decision", {})
        conversation = session_data.get("conversation", {})
        
        # Calculate session statistics
        total_messages = sum(len(messages) for messages in conversation.values())
        
        # Analyze decision quality
        validation_result = validate_decision_format(decision)
        
        return {
            "session_id": session_data.get("session_id", "unknown"),
            "symbol": session_data.get("symbol", "unknown"),
            "duration_seconds": session_data.get("duration_seconds", 0),
            "total_messages": total_messages,
            "decision": decision,
            "validation_result": validation_result,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error examining session log: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "message": f"Error examining session log: {str(e)}"
        }

def main():
    """Run the structured decision agent test"""
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    # Create output directory if needed
    os.makedirs("test_outputs/structured_decisions", exist_ok=True)
    
    # Test with default symbol
    symbol = "BTCUSDT"
    print(f"Testing structured decision-making for {symbol}...")
    
    # Run the test
    result = test_trading_session_with_symbol(symbol)
    
    # Process results
    if result["status"] == "success":
        decision = result["decision"]
        log_file = result.get("log_file")
        
        print(f"\nDecision: {decision['decision']} {symbol}")
        print(f"Entry: ${decision.get('entry_price', 'N/A')}")
        print(f"Stop Loss: ${decision.get('stop_loss', 'N/A')}")
        print(f"Take Profit: ${decision.get('take_profit', 'N/A')}")
        print(f"Position Size: {decision.get('position_size_percent', 'N/A')}%")
        print(f"Confidence: {decision.get('confidence_score', 0) * 100:.1f}%")
        print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
        
        # Validate the decision format
        validation = validate_decision_format(decision)
        
        print("\nValidation Results:")
        print(f"Valid format: {'✓' if validation['is_valid'] else '✗'}")
        
        if validation["missing_fields"]:
            print(f"Missing fields: {', '.join(validation['missing_fields'])}")
        
        if validation.get("risk_reward_ratio"):
            print(f"Risk-Reward Ratio: {validation['risk_reward_ratio']:.2f}")
        
        if validation["warnings"]:
            print("\nWarnings:")
            for warning in validation["warnings"]:
                print(f"- {warning}")
        
        # Examine session log if available
        if log_file and os.path.exists(log_file):
            print(f"\nSession log saved to: {log_file}")
            
            # Analyze log (but don't display full results as it would be verbose)
            log_analysis = examine_session_log(log_file)
            if log_analysis["status"] == "success":
                print(f"Session duration: {log_analysis['duration_seconds']:.1f} seconds")
                print(f"Total messages: {log_analysis['total_messages']}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()