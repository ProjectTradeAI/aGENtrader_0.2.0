#!/usr/bin/env python3
"""
Test the multi-agent decision session
"""
import os
import sys
import json
import logging
import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_decision")

# Import the decision session
from orchestration.decision_session import DecisionSession

def test_decision_session():
    """
    Test the decision session with a simple case.
    """
    logger.info("Testing decision session...")
    
    # Create a decision session
    session = DecisionSession()
    
    # Sample market data
    market_data = {
        "recent_prices": [
            ("2025-03-20 10:00:00", 81200.45),
            ("2025-03-20 11:00:00", 81400.78),
            ("2025-03-20 12:00:00", 81350.22),
            ("2025-03-20 13:00:00", 81500.91),
            ("2025-03-20 14:00:00", 81650.33)
        ],
        "volume_24h": 1250000000,
        "change_24h": 1.2
    }
    
    # Run the decision
    try:
        decision_data = session.run_decision(
            symbol="BTCUSDT",
            interval="1h",
            current_price=81650.33,
            market_data=market_data,
            analysis_type="full"
        )
        
        # Print decision
        logger.info("Decision completed successfully")
        logger.info(f"Action: {decision_data['decision']['action']}")
        logger.info(f"Confidence: {decision_data['decision']['confidence']}")
        logger.info(f"Reasoning: {decision_data['decision']['reasoning']}")
        
        # Save to file
        with open("test_decision_result.json", "w") as f:
            json.dump(decision_data, f, indent=2, default=str)
            
        logger.info("Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running decision: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Run the test
    test_decision_session()