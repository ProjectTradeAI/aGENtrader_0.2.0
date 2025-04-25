#!/usr/bin/env python3
"""
Quick Verification of DecisionSession Fix

This script quickly verifies that the DecisionSession class
no longer uses the simplified agent framework text.
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fix")

def verify_decision_session():
    """Verify that the DecisionSession class no longer uses simplified agent framework"""
    try:
        # Import the fixed DecisionSession
        from orchestration.decision_session import DecisionSession
        
        # Create an instance
        session = DecisionSession()
        
        # Run a test decision
        logger.info("Running test decision...")
        result = session.run_session("BTCUSDT", 50000)
        
        # Check result
        if 'decision' in result and 'reasoning' in result['decision']:
            reasoning = result['decision']['reasoning']
            logger.info(f"Decision reasoning: {reasoning}")
            
            is_fixed = "simplified agent framework" not in reasoning.lower()
            logger.info(f"Is fixed: {is_fixed}")
            
            return is_fixed
        else:
            logger.warning("Invalid result format")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying fix: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Verifying DecisionSession fix...")
    is_fixed = verify_decision_session()
    
    if is_fixed:
        print("✅ Fix successfully applied! The 'simplified agent framework' text is gone.")
    else:
        print("❌ Fix verification failed. The 'simplified agent framework' text may still be present.")
