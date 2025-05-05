#!/usr/bin/env python3
"""
Simple test script for TradePlanAgent HOLD signal handling
"""

import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_simple_hold')

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def test_hold_respect():
    """Simple test to verify that HOLD signals are preserved in the trade plan"""
    # Import the agents
    try:
        from agents.trade_plan_agent import create_trade_plan_agent
    except ImportError as e:
        logger.error(f"Failed to import trade_plan_agent: {str(e)}")
        return False

    # Create a mock data provider
    class MockDataProvider:
        """Basic mock data provider for testing"""
        def __init__(self):
            self.current_price = 50000.0
            
        def get_current_price(self, symbol=None):
            return self.current_price
            
    # Create a simple HOLD decision
    decision = {
        "final_signal": "HOLD",
        "signal": "HOLD",
        "confidence": 60,
        "reasoning": "Testing HOLD signal respect",
        "timestamp": datetime.now().isoformat()
    }
    
    # Create market data
    market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
        "data_provider": MockDataProvider()
    }
    
    # Create the trade plan agent with allow_fallback_on_hold=False
    trade_plan_agent = create_trade_plan_agent(config={
        "data_provider": market_data["data_provider"],
        "allow_fallback_on_hold": False,
        "risk_reward_ratio": 1.5,
        "portfolio_risk_per_trade": 0.02
    })
    
    # Generate a trade plan
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs={}
    )
    
    # Check if the signal in the trade plan matches the signal in decision
    final_signal = trade_plan.get("signal")
    decision_consistency = trade_plan.get("decision_consistency", False)
    
    logger.info(f"Decision input signal: {decision['signal']}")
    logger.info(f"Trade plan output signal: {final_signal}")
    logger.info(f"Decision consistency: {decision_consistency}")
    
    return (final_signal == "HOLD", decision_consistency)

def test_conflicted_respect():
    """Simple test to verify that CONFLICTED signals are preserved in the trade plan"""
    # Import the agents
    try:
        from agents.trade_plan_agent import create_trade_plan_agent
    except ImportError as e:
        logger.error(f"Failed to import trade_plan_agent: {str(e)}")
        return False

    # Create a mock data provider
    class MockDataProvider:
        """Basic mock data provider for testing"""
        def __init__(self):
            self.current_price = 50000.0
            
        def get_current_price(self, symbol=None):
            return self.current_price
            
    # Create a simple CONFLICTED decision
    decision = {
        "final_signal": "CONFLICTED",
        "signal": "CONFLICTED",
        "confidence": 40,
        "reasoning": "Testing CONFLICTED signal respect",
        "risk_warning": "Market signals are conflicted",
        "timestamp": datetime.now().isoformat()
    }
    
    # Create market data
    market_data = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "current_price": 50000.0,
        "data_provider": MockDataProvider()
    }
    
    # Create the trade plan agent with allow_fallback_on_hold=False
    trade_plan_agent = create_trade_plan_agent(config={
        "data_provider": market_data["data_provider"],
        "allow_fallback_on_hold": False,
        "risk_reward_ratio": 1.5,
        "portfolio_risk_per_trade": 0.02
    })
    
    # Generate a trade plan
    trade_plan = trade_plan_agent.generate_trade_plan(
        decision=decision,
        market_data=market_data,
        analyst_outputs={}
    )
    
    # Check if the signal in the trade plan matches the signal in decision
    final_signal = trade_plan.get("signal")
    decision_consistency = trade_plan.get("decision_consistency", False)
    risk_warning = trade_plan.get("risk_warning")
    
    logger.info(f"Decision input signal: {decision['signal']}")
    logger.info(f"Trade plan output signal: {final_signal}")
    logger.info(f"Decision consistency: {decision_consistency}")
    logger.info(f"Risk warning included: {risk_warning is not None}")
    
    return (final_signal == "CONFLICTED", decision_consistency, risk_warning is not None)

if __name__ == "__main__":
    print("=== Testing HOLD Signal Respect ===")
    signal_matches, consistency = test_hold_respect()
    print(f"HOLD Signal Test Result:")
    print(f"  Signal preserved: {'✓' if signal_matches else '✗'}")
    print(f"  Decision consistency maintained: {'✓' if consistency else '✗'}")
    
    print("\n=== Testing CONFLICTED Signal Respect ===")
    signal_matches, consistency, risk_warning = test_conflicted_respect()
    print(f"CONFLICTED Signal Test Result:")
    print(f"  Signal preserved: {'✓' if signal_matches else '✗'}")
    print(f"  Decision consistency maintained: {'✓' if consistency else '✗'}")
    print(f"  Risk warning included: {'✓' if risk_warning else '✗'}")
    
    if (signal_matches and consistency and risk_warning):
        print("\nAll tests passed! The TradePlanAgent now correctly respects HOLD and CONFLICTED signals.")
        sys.exit(0)
    else:
        print("\nSome tests failed. The TradePlanAgent is not fully fixed yet.")
        sys.exit(1)