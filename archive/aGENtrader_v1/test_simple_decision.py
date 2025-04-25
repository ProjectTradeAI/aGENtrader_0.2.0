#!/usr/bin/env python3
"""
Test SimpleDecisionSession with local TinyLlama model

This script tests the SimpleDecisionSession class and verifies
that it can work with the local TinyLlama model to generate
cryptocurrency trading decisions.
"""
import os
import sys
import json
import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_simple_decision")

try:
    from orchestration.simple_decision_session import SimpleDecisionSession
    logger.info("SimpleDecisionSession imported successfully")
except ImportError:
    logger.error("Failed to import SimpleDecisionSession")
    sys.exit(1)

def test_simple_decision():
    """Test the SimpleDecisionSession with BTC data"""
    logger.info("Creating SimpleDecisionSession instance")
    session = SimpleDecisionSession()
    
    # Test basic decision
    logger.info("Running basic decision for BTCUSDT")
    decision_data = session.run_decision(
        symbol="BTCUSDT",
        interval="1h",
        current_price=85000.50,
        market_data={
            "volume_24h": 2500000000,
            "change_24h": 2.5,
            "recent_prices": [
                ("2025-04-17T10:00:00", 84500.00),
                ("2025-04-17T11:00:00", 84750.25),
                ("2025-04-17T12:00:00", 84900.75),
                ("2025-04-17T13:00:00", 85050.00),
                ("2025-04-17T14:00:00", 85000.50)
            ]
        },
        analysis_type="full"
    )
    
    # Output decision
    logger.info(f"Decision action: {decision_data['decision']['action']}")
    logger.info(f"Confidence: {decision_data['decision']['confidence']}")
    
    # Save the full decision to file for inspection
    output_file = "test_decision_output.json"
    with open(output_file, "w") as f:
        json.dump(decision_data, f, indent=2, default=str)
    
    logger.info(f"Full decision saved to {output_file}")
    return decision_data

if __name__ == "__main__":
    logger.info("Starting SimpleDecisionSession test")
    try:
        decision_data = test_simple_decision()
        logger.info("Test completed successfully")
        
        # Print a summary of the decision
        print("\n" + "="*50)
        print("DECISION SUMMARY")
        print("="*50)
        print(f"Symbol: {decision_data['symbol']}")
        print(f"Action: {decision_data['decision']['action']}")
        print(f"Confidence: {decision_data['decision']['confidence']:.2f}")
        print(f"Reasoning: {decision_data['decision']['reasoning']}")
        
        if 'full_analysis' in decision_data:
            print("\nFull Analysis Preview:")
            analysis = decision_data['full_analysis']
            # Truncate if too long
            if len(analysis) > 500:
                print(analysis[:500] + "...")
            else:
                print(analysis)
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)