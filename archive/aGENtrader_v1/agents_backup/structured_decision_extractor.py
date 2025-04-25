"""
Structured Decision Extractor

This module provides utility functions to extract structured trading decisions
from agent conversation outputs. It handles multiple formats and ensures
that the extracted decisions conform to the expected schema.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f"data/logs/decision_extraction_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

# Define the required fields for a valid trading decision
REQUIRED_DECISION_FIELDS = [
    "decision",
    "asset",
    "entry_price",
    "stop_loss",
    "take_profit",
    "confidence_score",
    "reasoning"
]

# Define valid values for decision field
VALID_DECISIONS = ["BUY", "SELL", "HOLD"]


def validate_decision_format(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize the trading decision format.
    
    Args:
        decision: Dictionary containing the parsed trading decision
        
    Returns:
        Validated and normalized decision dict or error dict
    """
    # Check for required fields
    missing_fields = [field for field in REQUIRED_DECISION_FIELDS if field not in decision]
    if missing_fields:
        return {
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "partial_decision": decision
        }
    
    # Normalize decision (always uppercase)
    decision["decision"] = str(decision["decision"]).strip().upper()
    
    # Validate decision value
    if decision["decision"] not in VALID_DECISIONS:
        return {
            "error": f"Invalid decision value: {decision['decision']}. Must be one of {VALID_DECISIONS}",
            "partial_decision": decision
        }
    
    # Convert numeric values
    try:
        if isinstance(decision["entry_price"], str):
            decision["entry_price"] = float(decision["entry_price"].replace(",", "").strip())
        
        if isinstance(decision["stop_loss"], str):
            decision["stop_loss"] = float(decision["stop_loss"].replace(",", "").strip())
            
        if isinstance(decision["take_profit"], str):
            decision["take_profit"] = float(decision["take_profit"].replace(",", "").strip())
            
        if isinstance(decision["confidence_score"], str):
            # Handle percentage format (e.g., "85%")
            confidence = decision["confidence_score"].replace("%", "").strip()
            confidence_float = float(confidence)
            # Convert percentage to 0-1 scale if needed
            if confidence_float > 1.0 and confidence_float <= 100.0:
                confidence_float /= 100.0
            decision["confidence_score"] = confidence_float
    
    except (ValueError, TypeError) as e:
        return {
            "error": f"Error converting numeric values: {str(e)}",
            "partial_decision": decision
        }
    
    # Validate numeric ranges
    if not (0.0 <= decision["confidence_score"] <= 1.0):
        return {
            "error": f"Confidence score must be between 0.0 and 1.0, got {decision['confidence_score']}",
            "partial_decision": decision
        }
    
    # Add timestamp if not present
    if "timestamp" not in decision:
        decision["timestamp"] = datetime.now().isoformat()
    
    return decision


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Extracted JSON object or None if no valid JSON found
    """
    # Try to find JSON object pattern in the text
    json_patterns = [
        r'```json\s*([\s\S]*?)```',  # JSON in code block
        r'```\s*([\s\S]*?)```',       # Any code block
        r'\{[\s\S]*?\}',              # Bare JSON object
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Check if this looks like a trading decision
                if any(field in match for field in ["decision", "asset"]):
                    # Clean up the match (remove leading/trailing whitespace)
                    match = match.strip()
                    # Ensure it starts with { and ends with }
                    if not match.startswith("{"):
                        match = "{" + match
                    if not match.endswith("}"):
                        match = match + "}"
                    
                    # Try to parse as JSON
                    decision_json = json.loads(match)
                    return decision_json
            except json.JSONDecodeError:
                continue
    
    return None


def extract_key_value_pairs(text: str) -> Dict[str, Any]:
    """
    Extract key-value pairs from text.
    
    Args:
        text: Text containing key-value pairs
        
    Returns:
        Dictionary of extracted key-value pairs
    """
    decision = {}
    
    # Look for key-value pairs
    for key in REQUIRED_DECISION_FIELDS:
        # Pattern matches: key: value, "key": value, key = value, etc.
        patterns = [
            rf'{key}[:\s]+([^,\n]+)',              # key: value
            rf'"{key}"[:\s]+([^,\n]+)',            # "key": value
            rf"'{key}'[:\s]+([^,\n]+)",            # 'key': value
            rf"{key}[=\s]+([^,\n]+)",              # key = value
            rf"{key.capitalize()}[:\s]+([^,\n]+)"  # Key: value
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                decision[key] = match.group(1).strip().strip('"\' ')
                break
    
    return decision


def extract_trading_decision(agent_response: str) -> Dict[str, Any]:
    """
    Extract trading decision from agent response.
    
    Args:
        agent_response: Text response from agent
        
    Returns:
        Dictionary containing parsed trading decision or error
    """
    logging.info("Extracting trading decision from agent response")
    
    try:
        # First attempt: Try to find and parse JSON directly
        decision_json = extract_json_from_text(agent_response)
        if decision_json:
            logging.info("Found JSON in agent response")
            return validate_decision_format(decision_json)
        
        # Second attempt: Look for key-value pairs if JSON not found
        logging.info("No valid JSON found, trying to extract key-value pairs")
        decision = extract_key_value_pairs(agent_response)
        
        if decision:
            logging.info(f"Extracted key-value pairs: {decision}")
            return validate_decision_format(decision)
        
        # Failed to extract decision
        logging.warning("Failed to extract trading decision from agent response")
        return {
            "error": "Failed to parse trading decision from agent response",
            "agent_response": agent_response
        }
    
    except Exception as e:
        logging.error(f"Error extracting trading decision: {str(e)}")
        return {
            "error": f"Error extracting trading decision: {str(e)}",
            "agent_response": agent_response
        }


def log_trading_decision(decision: Dict[str, Any], log_dir: str = "data/logs") -> None:
    """
    Log trading decision to file and potentially to database.
    
    Args:
        decision: Trading decision dictionary
        log_dir: Directory to store log files
    """
    import os
    from datetime import datetime
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path
    log_file = os.path.join(log_dir, f"trading_decisions_{datetime.now().strftime('%Y%m%d')}.jsonl")
    
    # Append decision to log file
    with open(log_file, "a") as f:
        f.write(json.dumps(decision) + "\n")
    
    logging.info(f"Logged trading decision: {decision.get('decision', 'UNKNOWN')} for {decision.get('asset', 'UNKNOWN')}")


def store_decision_in_database(decision: Dict[str, Any]) -> bool:
    """
    Store trading decision in database.
    
    This is a placeholder for database storage implementation.
    
    Args:
        decision: Trading decision dictionary
        
    Returns:
        True if successful, False otherwise
    """
    # Placeholder for database storage
    # This would be implemented based on your specific database setup
    try:
        # Example with SQLAlchemy:
        # from sqlalchemy import create_engine, text
        # engine = create_engine(DATABASE_URI)
        # with engine.connect() as conn:
        #     query = text(
        #         "INSERT INTO trading_decisions (decision, asset, entry_price, stop_loss, take_profit, confidence_score, reasoning, timestamp) "
        #         "VALUES (:decision, :asset, :entry_price, :stop_loss, :take_profit, :confidence_score, :reasoning, :timestamp)"
        #     )
        #     conn.execute(query, decision)
        #     conn.commit()
        
        logging.info(f"Stored decision in database: {decision.get('decision', 'UNKNOWN')} for {decision.get('asset', 'UNKNOWN')}")
        return True
    
    except Exception as e:
        logging.error(f"Error storing decision in database: {str(e)}")
        return False


def test_decision_extraction():
    """
    Test the decision extraction functionality with various input formats.
    
    Returns:
        True if all tests pass, False otherwise
    """
    test_cases = [
        # JSON format in code block
        {
            "input": """
            After analyzing the market data, I recommend:
            ```json
            {
              "decision": "BUY",
              "asset": "BTC",
              "entry_price": 45300,
              "stop_loss": 44800,
              "take_profit": 46800,
              "confidence_score": 0.85,
              "reasoning": "Bullish momentum confirmed by RSI and positive on-chain flows."
            }
            ```
            """,
            "expected_decision": "BUY"
        },
        
        # Direct JSON
        {
            "input": """
            Here's my trading recommendation:
            {
              "decision": "SELL",
              "asset": "ETH",
              "entry_price": 3200,
              "stop_loss": 3300,
              "take_profit": 2900,
              "confidence_score": 0.7,
              "reasoning": "Bearish divergence on RSI with decreased volume."
            }
            """,
            "expected_decision": "SELL"
        },
        
        # Key-value pairs
        {
            "input": """
            Based on my analysis, here's what I recommend:
            
            Decision: HOLD
            Asset: BTC
            Entry Price: 46500
            Stop Loss: 45000
            Take Profit: 48000
            Confidence Score: 0.6
            Reasoning: Market in consolidation phase with mixed signals.
            """,
            "expected_decision": "HOLD"
        },
        
        # Percentage confidence score format
        {
            "input": """
            {
              "decision": "BUY",
              "asset": "BTC",
              "entry_price": 45300,
              "stop_loss": 44800,
              "take_profit": 46800,
              "confidence_score": "90%",
              "reasoning": "Strong support level confirmed."
            }
            """,
            "expected_decision": "BUY"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        result = extract_trading_decision(test_case["input"])
        
        if "error" in result:
            logging.error(f"Test case {i+1} failed: {result['error']}")
            return False
            
        if result["decision"] != test_case["expected_decision"]:
            logging.error(f"Test case {i+1} failed: Expected '{test_case['expected_decision']}', got '{result['decision']}'")
            return False
    
    logging.info("All decision extraction test cases passed!")
    return True


if __name__ == "__main__":
    # Run tests if executed directly
    test_decision_extraction()