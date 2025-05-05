#!/usr/bin/env python3
"""
aGENtrader - Test Hold Signal Handling

This script tests that the TradePlanAgent properly respects HOLD signals
from the DecisionAgent, ensuring:
1. Decision consistency tracking works correctly
2. The system never generates a trade plan for a HOLD signal
3. allow_fallback_on_hold configuration parameter works correctly

Usage:
  python test_trade_plan_hold_signal.py
"""

import json
import time
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_hold_signals')

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the decision and trade plan agents
try:
    from agents.decision_agent import DecisionAgent
    from agents.trade_plan_agent import create_trade_plan_agent
except ImportError as e:
    logger.error(f"Failed to import agents: {str(e)}")
    sys.exit(1)

class MockDataProvider:
    """Mock data provider for testing"""
    
    def __init__(self, symbol="BTC/USDT"):
        self.symbol = symbol
        self.current_price = 50000.0
    
    def get_current_price(self, symbol=None):
        """Get current price"""
        return self.current_price
    
    def fetch_ohlcv(self, symbol=None, interval="1h", limit=100, **kwargs):
        """Fetch mock OHLCV data"""
        return [
            # timestamp, open, high, low, close, volume
            [int(time.time() * 1000) - 3600000 * i, 
             self.current_price * (1 - 0.001 * i),
             self.current_price * (1 + 0.002 * i), 
             self.current_price * (1 - 0.002 * i),
             self.current_price * (1 + 0.001 * i),
             100000.0 - 1000.0 * i] 
            for i in range(limit)
        ]
    
    def fetch_market_depth(self, symbol=None, limit=100):
        """Fetch mock order book data"""
        return {
            "bids": [[self.current_price * (1 - 0.001 * i), 10.0 - 0.1 * i] for i in range(limit)],
            "asks": [[self.current_price * (1 + 0.001 * i), 10.0 - 0.1 * i] for i in range(limit)]
        }


def create_mock_analyses() -> Dict[str, Any]:
    """Create mock analysis outputs for testing"""
    return {
        "technical_analysis": {
            "signal": "NEUTRAL",
            "confidence": 60,
            "indicators": {
                "rsi": 45,
                "macd": "neutral",
                "bollinger": "inside"
            },
            "timestamp": datetime.now().isoformat()
        },
        "sentiment_analysis": {
            "signal": "NEUTRAL",
            "confidence": 70,
            "sentiment_score": 0.1,
            "timestamp": datetime.now().isoformat()
        },
        "liquidity_analysis": {
            "signal": "NEUTRAL",
            "confidence": 55,
            "buy_wall": 49500,
            "sell_wall": 50500,
            "timestamp": datetime.now().isoformat()
        },
        "funding_rate_analysis": {
            "signal": "NEUTRAL",
            "confidence": 65,
            "funding_rate": 0.01,
            "timestamp": datetime.now().isoformat()
        },
        "open_interest_analysis": {
            "signal": "NEUTRAL",
            "confidence": 58,
            "open_interest_change": 0.5,
            "timestamp": datetime.now().isoformat()
        }
    }


def test_hold_signal_respected(allow_fallback=False):
    """
    Test that HOLD signals are properly respected by the TradePlanAgent
    
    Args:
        allow_fallback: Whether to allow fallback to generating trade plans for HOLD signals
        
    Returns:
        Dict with test results
    """
    logger.info(f"Testing HOLD signal with allow_fallback_on_hold={allow_fallback}")
    
    try:
        # Initialize agents and mock data
        data_provider = MockDataProvider()
        decision_agent = DecisionAgent()
        
        # Create trade plan agent with configuration
        trade_plan_agent = create_trade_plan_agent(config={
            "data_provider": data_provider,
            "allow_fallback_on_hold": allow_fallback,
            "risk_reward_ratio": 1.5, 
            "portfolio_risk_per_trade": 0.02
        })
        
        # Create market data
        symbol = "BTC/USDT"
        market_data = {
            "symbol": symbol,
            "interval": "1h",
            "current_price": data_provider.current_price,
            "data_provider": data_provider
        }
        
        # Create mock analysis results
        analyses = create_mock_analyses()
        
        # Make decision with DecisionAgent (should be HOLD with all NEUTRAL inputs)
        logger.info("Making decision with DecisionAgent...")
        decision = decision_agent.make_decision(
            agent_analyses=analyses,
            symbol=symbol,
            market_data=market_data
        )
        
        # Validate the decision
        decision_signal = decision.get('final_signal')
        decision_confidence = decision.get('confidence')
        logger.info(f"Decision: {decision_signal} with {decision_confidence}% confidence")
        
        # Assert decision should be HOLD
        assert decision_signal == "HOLD", f"Expected HOLD decision but got {decision_signal}"
        
        # Now generate a trade plan
        logger.info("Generating trade plan...")
        trade_plan = trade_plan_agent.generate_trade_plan(
            decision=decision,
            market_data=market_data,
            analyst_outputs=analyses
        )
        
        # Check trade plan signal
        trade_plan_signal = trade_plan.get('signal')
        trade_plan_consistency = trade_plan.get('decision_consistency', False)
        logger.info(f"Trade plan signal: {trade_plan_signal}, Decision consistency: {trade_plan_consistency}")
        
        # If allow_fallback is False, the trade plan signal should match the decision signal (HOLD)
        if not allow_fallback:
            assert trade_plan_signal == "HOLD", f"Expected HOLD trade plan but got {trade_plan_signal}"
            assert trade_plan_consistency is True, "Expected decision_consistency to be True"
        else:
            # If fallback is allowed and signal differs, consistency should be False
            if trade_plan_signal != "HOLD":
                assert trade_plan_consistency is False, "Expected decision_consistency to be False when signal changed"
        
        # Check that position_size is None or 0 for HOLD signals 
        # (no position size should be calculated for HOLD)
        if trade_plan_signal == "HOLD":
            position_size = trade_plan.get('position_size')
            assert position_size is None or position_size == 0, f"Expected None/0 position size for HOLD but got {position_size}"
            
        # Return test result
        return {
            "status": "success",
            "decision_signal": decision_signal,
            "decision_confidence": decision_confidence,
            "trade_plan_signal": trade_plan_signal,
            "decision_consistency": trade_plan_consistency,
            "allow_fallback": allow_fallback,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Error in test: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }


def test_conflicted_signal_respected(allow_fallback=False):
    """
    Test that CONFLICTED signals are properly respected by the TradePlanAgent
    
    Args:
        allow_fallback: Whether to allow fallback to generating trade plans for CONFLICTED signals
        
    Returns:
        Dict with test results
    """
    logger.info(f"Testing CONFLICTED signal with allow_fallback_on_hold={allow_fallback}")
    
    try:
        # Initialize agents and mock data
        data_provider = MockDataProvider()
        
        # Create trade plan agent with configuration
        trade_plan_agent = create_trade_plan_agent(config={
            "data_provider": data_provider,
            "allow_fallback_on_hold": allow_fallback,
            "risk_reward_ratio": 1.5, 
            "portfolio_risk_per_trade": 0.02
        })
        
        # Create market data
        symbol = "BTC/USDT"
        market_data = {
            "symbol": symbol,
            "interval": "1h",
            "current_price": data_provider.current_price,
            "data_provider": data_provider
        }
        
        # Create mock analysis results (mixture of conflicting signals)
        analyses = {
            "technical_analysis": {
                "signal": "BUY",
                "confidence": 65,
                "indicators": {
                    "rsi": 62,
                    "macd": "bullish",
                    "bollinger": "breakout"
                },
                "timestamp": datetime.now().isoformat()
            },
            "sentiment_analysis": {
                "signal": "SELL",
                "confidence": 70,
                "sentiment_score": -0.3,
                "timestamp": datetime.now().isoformat()
            },
            "liquidity_analysis": {
                "signal": "BUY",
                "confidence": 55,
                "buy_wall": 49500,
                "sell_wall": 50500,
                "timestamp": datetime.now().isoformat()
            },
            "funding_rate_analysis": {
                "signal": "SELL",
                "confidence": 68,
                "funding_rate": -0.03,
                "timestamp": datetime.now().isoformat()
            },
            "open_interest_analysis": {
                "signal": "SELL",
                "confidence": 60,
                "open_interest_change": 1.2,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Create mock decision with CONFLICTED signal
        decision = {
            "final_signal": "CONFLICTED",
            "confidence": 45,
            "reasoning": "Conflicting signals from various analyst agents",
            "competing_signals": {
                "BUY": 2,
                "SELL": 3
            },
            "signal_scores": {
                "BUY": 120,
                "SELL": 198
            },
            "contributing_agents": "TechnicalAnalystAgent, SentimentAnalystAgent, LiquidityAnalystAgent, FundingRateAnalystAgent, OpenInterestAnalystAgent",
            "risk_warning": "Conflicting signals indicate market uncertainty, caution advised",
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate a trade plan
        logger.info("Generating trade plan for CONFLICTED decision...")
        trade_plan = trade_plan_agent.generate_trade_plan(
            decision=decision,
            market_data=market_data,
            analyst_outputs=analyses
        )
        
        # Check trade plan signal
        trade_plan_signal = trade_plan.get('signal')
        trade_plan_consistency = trade_plan.get('decision_consistency', False)
        risk_warning = trade_plan.get('risk_warning')
        logger.info(f"Trade plan signal: {trade_plan_signal}, Decision consistency: {trade_plan_consistency}")
        
        # If allow_fallback is False, the trade plan signal should match the decision signal (CONFLICTED)
        # Even with fallback enabled, CONFLICTED should always result in HOLD
        if not allow_fallback:
            assert trade_plan_signal == "CONFLICTED" or trade_plan_signal == "HOLD", \
                f"Expected CONFLICTED or HOLD trade plan but got {trade_plan_signal}"
            assert trade_plan_consistency is True, "Expected decision_consistency to be True"
        else:
            if trade_plan_signal not in ["CONFLICTED", "HOLD"]:
                assert trade_plan_consistency is False, "Expected decision_consistency to be False when signal changed"
        
        # For CONFLICTED signals, risk_warning should always be included
        assert risk_warning is not None and risk_warning != "", "Expected risk_warning to be included for CONFLICTED signal"
        
        # Check that position_size is None or 0 for CONFLICTED signals
        if trade_plan_signal in ["CONFLICTED", "HOLD"]:
            position_size = trade_plan.get('position_size')
            assert position_size is None or position_size == 0, \
                f"Expected None/0 position size for CONFLICTED but got {position_size}"
            
        # Return test result
        return {
            "status": "success",
            "decision_signal": decision.get("final_signal"),
            "decision_confidence": decision.get("confidence"),
            "trade_plan_signal": trade_plan_signal,
            "decision_consistency": trade_plan_consistency,
            "risk_warning_included": risk_warning is not None and risk_warning != "",
            "allow_fallback": allow_fallback,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Error in test: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Run the tests"""
    logger.info("=== Testing TradePlanAgent HOLD signal handling ===")
    
    # Create log directory
    os.makedirs("logs", exist_ok=True)
    
    # Run tests and collect results
    results = {
        "hold_signal_no_fallback": test_hold_signal_respected(allow_fallback=False),
        "hold_signal_with_fallback": test_hold_signal_respected(allow_fallback=True),
        "conflicted_signal_no_fallback": test_conflicted_signal_respected(allow_fallback=False),
        "conflicted_signal_with_fallback": test_conflicted_signal_respected(allow_fallback=True),
    }
    
    # Log results
    for test_name, result in results.items():
        status = result.get("status")
        if status == "success":
            logger.info(f"Test {test_name}: PASSED")
        else:
            logger.error(f"Test {test_name}: FAILED - {result.get('error')}")
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"logs/hold_signal_test_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {filename}")
    
    # Return success if all tests passed
    all_passed = all(r.get("status") == "success" for r in results.values())
    logger.info(f"Overall test status: {'SUCCESS' if all_passed else 'FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())