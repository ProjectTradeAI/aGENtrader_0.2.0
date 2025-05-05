import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
import logging

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import the TradePlanAgent class
from agents.trade_plan_agent import TradePlanAgent, create_trade_plan_agent

class TestTradePlanHoldSignal(unittest.TestCase):
    """
    Test TradePlanAgent handling of HOLD signals from DecisionAgent
    """
    
    def setUp(self):
        """
        Set up test environment before each test
        """
        # Create a TradePlanAgent with standard parameters for testing
        self.agent = create_trade_plan_agent(
            config={
                "risk_reward_ratio": 2.0,
                "portfolio_risk_per_trade": 2.0,
                "position_size_base": 1.0,
                "stop_loss_atr_multiplier": 1.5,
                "take_profit_atr_multiplier": 3.0,
                "detailed_logging": True,
                "test_mode": True
            }
        )
        
        # Create a TradePlanAgent with allow_fallback_on_hold=True for comparison
        self.agent_with_fallback = create_trade_plan_agent(
            config={
                "risk_reward_ratio": 2.0,
                "portfolio_risk_per_trade": 2.0,
                "position_size_base": 1.0,
                "stop_loss_atr_multiplier": 1.5,
                "take_profit_atr_multiplier": 3.0,
                "detailed_logging": True,
                "test_mode": True,
                "allow_fallback_on_hold": True
            }
        )
        
        # Create mock market data
        self.market_data = {
            "symbol": "BTC/USDT",
            "interval": "1h",
            "current_price": 50000.0,
            "ohlcv": [
                {"timestamp": "2025-04-01T00:00:00Z", "open": 48000, "high": 51000, "low": 47500, "close": 49000, "volume": 10000},
                {"timestamp": "2025-04-01T01:00:00Z", "open": 49000, "high": 52000, "low": 48500, "close": 50000, "volume": 12000}
            ]
        }
    
    def test_respect_hold_signal(self):
        """
        Test that TradePlanAgent strictly respects HOLD signals from DecisionAgent
        """
        # Create a HOLD decision from DecisionAgent
        hold_decision = {
            "signal": "NEUTRAL",
            "final_signal": "HOLD",
            "confidence": 75.0,
            "directional_confidence": 0.0,
            "contributing_agents": ["SentimentAnalystAgent", "LiquidityAnalystAgent", "FundingRateAnalystAgent"],
            "reasoning": "Market is indecisive with multiple conflicting signals",
            "agent_contributions": {
                "TechnicalAnalystAgent": {"signal": "BUY", "confidence": 70},
                "SentimentAnalystAgent": {"signal": "NEUTRAL", "confidence": 65},
                "LiquidityAnalystAgent": {"signal": "NEUTRAL", "confidence": 60},
                "FundingRateAnalystAgent": {"signal": "NEUTRAL", "confidence": 65},
                "OpenInterestAnalystAgent": {"signal": "SELL", "confidence": 60}
            }
        }
        
        # Generate trade plan
        trade_plan = self.agent.generate_trade_plan(hold_decision, self.market_data)
        
        # Verify the plan respects the HOLD signal
        self.assertEqual(trade_plan["signal"], "HOLD", "TradePlanAgent should respect HOLD signal")
        self.assertEqual(trade_plan["position_size"], 0, "Position size should be 0 for HOLD signal")
        self.assertTrue(trade_plan["decision_consistency"], "Decision consistency should be True")
        self.assertIn("DecisionAgent returned HOLD", trade_plan["reasoning"], "Reasoning should explain HOLD decision")
        
    def test_fallback_on_hold_when_allowed(self):
        """
        Test that TradePlanAgent can override HOLD when allow_fallback_on_hold=True
        """
        # Create a HOLD decision from DecisionAgent but with strong BUY signals
        hold_decision_with_strong_buy = {
            "signal": "NEUTRAL",
            "final_signal": "HOLD",
            "confidence": 55.0,
            "directional_confidence": 30.0,  # Some directional bias
            "contributing_agents": ["SentimentAnalystAgent", "LiquidityAnalystAgent"],
            "reasoning": "Market is indecisive but technical signals lean bullish",
            "agent_contributions": {
                "TechnicalAnalystAgent": {"signal": "BUY", "confidence": 85},  # Strong BUY signal
                "SentimentAnalystAgent": {"signal": "NEUTRAL", "confidence": 60},
                "LiquidityAnalystAgent": {"signal": "NEUTRAL", "confidence": 50},
                "FundingRateAnalystAgent": {"signal": "BUY", "confidence": 75},  # Another BUY signal
                "OpenInterestAnalystAgent": {"signal": "NEUTRAL", "confidence": 55}
            },
            "directional_bias": "BUY"  # Explicit directional bias
        }
        
        # Generate trade plan using the agent with fallback allowed
        trade_plan = self.agent_with_fallback.generate_trade_plan(hold_decision_with_strong_buy, self.market_data)
        
        # Verify the agent overrides HOLD when allowed
        self.assertNotEqual(trade_plan["signal"], "HOLD", "Agent with fallback should override HOLD")
        self.assertEqual(trade_plan["signal"], "BUY", "Signal should be BUY based on agent contributions")
        self.assertFalse(trade_plan["decision_consistency"], "Decision consistency should be False")
        self.assertGreater(trade_plan["position_size"], 0, "Position size should be > 0 for BUY signal")
    
    def test_conflicted_signal_with_hold_enforcement(self):
        """
        Test that CONFLICTED signals properly respect HOLD when required
        """
        # Create a CONFLICTED decision from DecisionAgent
        conflicted_decision = {
            "signal": "CONFLICTED",
            "final_signal": "HOLD",
            "confidence": 45.0,
            "directional_confidence": 5.0,
            "contributing_agents": [],
            "reasoning": "Market signals are in direct conflict",
            "agent_contributions": {
                "TechnicalAnalystAgent": {"signal": "BUY", "confidence": 80},
                "SentimentAnalystAgent": {"signal": "SELL", "confidence": 75},
                "LiquidityAnalystAgent": {"signal": "NEUTRAL", "confidence": 50},
                "FundingRateAnalystAgent": {"signal": "BUY", "confidence": 65},
                "OpenInterestAnalystAgent": {"signal": "SELL", "confidence": 70}
            }
        }
        
        # Generate trade plan
        trade_plan = self.agent.generate_trade_plan(conflicted_decision, self.market_data)
        
        # Verify the plan handles CONFLICTED signal correctly
        self.assertEqual(trade_plan["signal"], "HOLD", "CONFLICTED signal should be treated as HOLD")
        self.assertEqual(trade_plan["position_size"], 0, "Position size should be 0 for CONFLICTED signal")
        self.assertIn("risk_warning", trade_plan, "Trade plan should include risk warning for CONFLICTED signal")
        self.assertIn("conflicting_agents", trade_plan, "Trade plan should track conflicting agents")
        
if __name__ == "__main__":
    unittest.main()