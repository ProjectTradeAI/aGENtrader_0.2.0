#!/usr/bin/env python3
# Description: Tests the DecisionLogger component for tracking trading decisions

import sys
import os
import unittest
import tempfile
import shutil
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from core.logging import DecisionLogger
except ImportError:
    print("Error: DecisionLogger not found. Make sure the logging module is properly implemented.")
    sys.exit(1)

class TestDecisionLogger(unittest.TestCase):
    """Test suite for the DecisionLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for log files
        self.test_log_dir = tempfile.mkdtemp()
        self.logger = DecisionLogger(log_dir=self.test_log_dir)
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.test_log_dir)
        
    def test_initialization(self):
        """Test if logger initializes correctly."""
        self.assertEqual(self.logger.log_dir, self.test_log_dir)
        self.assertIsInstance(self.logger.decisions, dict)
        self.assertIsInstance(self.logger.agent_metrics, dict)
        
    def test_log_decision(self):
        """Test if log_decision properly logs a decision."""
        # Log a test decision
        decision_id = self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason",
            symbol="BTC/USDT",
            price=50000.0,
            timestamp="2025-04-30T12:00:00.000000",
            additional_data={"test_key": "test_value"}
        )
        
        # Check that decision was stored
        self.assertIn(decision_id, self.logger.decisions)
        
        # Check decision properties
        decision = self.logger.decisions[decision_id]
        self.assertEqual(decision['agent'], "TestAgent")
        self.assertEqual(decision['signal'], "BUY")
        self.assertEqual(decision['confidence'], 80)
        self.assertEqual(decision['reason'], "Test reason")
        self.assertEqual(decision['symbol'], "BTC/USDT")
        self.assertEqual(decision['price'], 50000.0)
        self.assertEqual(decision['timestamp'], "2025-04-30T12:00:00.000000")
        self.assertEqual(decision['additional_data'], {"test_key": "test_value"})
        
    def test_log_decision_updates_metrics(self):
        """Test if log_decision updates agent metrics correctly."""
        # Log multiple decisions
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason 1",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="SELL",
            confidence=90,
            reason="Test reason 2",
            symbol="ETH/USDT",
            price=3000.0
        )
        
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="NEUTRAL",
            confidence=60,
            reason="Test reason 3",
            symbol="BTC/USDT",
            price=49000.0
        )
        
        # Check agent metrics
        self.assertIn("TestAgent", self.logger.agent_metrics)
        metrics = self.logger.agent_metrics["TestAgent"]
        
        self.assertEqual(metrics['total_decisions'], 3)
        self.assertEqual(metrics['buy_signals'], 1)
        self.assertEqual(metrics['sell_signals'], 1)
        self.assertEqual(metrics['neutral_signals'], 1)
        
        # Check average confidence (80 + 90 + 60) / 3 = 76.67
        self.assertAlmostEqual(metrics['avg_confidence'], 76.67, places=2)
        
    def test_get_decision(self):
        """Test if get_decision retrieves a specific decision."""
        # Log a test decision
        decision_id = self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        # Retrieve the decision
        decision = self.logger.get_decision(decision_id)
        
        # Check that it's the correct decision
        self.assertEqual(decision['id'], decision_id)
        self.assertEqual(decision['agent'], "TestAgent")
        
        # Test with non-existent ID
        non_existent = self.logger.get_decision("non_existent_id")
        self.assertIsNone(non_existent)
        
    def test_get_decisions_by_symbol(self):
        """Test if get_decisions_by_symbol retrieves decisions for a symbol."""
        # Log decisions for different symbols
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason 1",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="SELL",
            confidence=90,
            reason="Test reason 2",
            symbol="ETH/USDT",
            price=3000.0
        )
        
        self.logger.log_decision(
            agent_name="AnotherAgent",
            signal="BUY",
            confidence=85,
            reason="Test reason 3",
            symbol="BTC/USDT",
            price=51000.0
        )
        
        # Get decisions for BTC/USDT
        btc_decisions = self.logger.get_decisions_by_symbol("BTC/USDT")
        
        # Should be 2 decisions for BTC/USDT
        self.assertEqual(len(btc_decisions), 2)
        
        # All decisions should be for BTC/USDT
        for decision in btc_decisions:
            self.assertEqual(decision['symbol'], "BTC/USDT")
            
        # Get decisions for ETH/USDT
        eth_decisions = self.logger.get_decisions_by_symbol("ETH/USDT")
        
        # Should be 1 decision for ETH/USDT
        self.assertEqual(len(eth_decisions), 1)
        self.assertEqual(eth_decisions[0]['symbol'], "ETH/USDT")
        
    def test_get_decisions_by_agent(self):
        """Test if get_decisions_by_agent retrieves decisions for an agent."""
        # Log decisions from different agents
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason 1",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="SELL",
            confidence=90,
            reason="Test reason 2",
            symbol="ETH/USDT",
            price=3000.0
        )
        
        self.logger.log_decision(
            agent_name="AnotherAgent",
            signal="BUY",
            confidence=85,
            reason="Test reason 3",
            symbol="BTC/USDT",
            price=51000.0
        )
        
        # Get decisions for TestAgent
        test_agent_decisions = self.logger.get_decisions_by_agent("TestAgent")
        
        # Should be 2 decisions for TestAgent
        self.assertEqual(len(test_agent_decisions), 2)
        
        # All decisions should be from TestAgent
        for decision in test_agent_decisions:
            self.assertEqual(decision['agent'], "TestAgent")
            
        # Get decisions for AnotherAgent
        another_agent_decisions = self.logger.get_decisions_by_agent("AnotherAgent")
        
        # Should be 1 decision for AnotherAgent
        self.assertEqual(len(another_agent_decisions), 1)
        self.assertEqual(another_agent_decisions[0]['agent'], "AnotherAgent")
        
    def test_get_agent_metrics(self):
        """Test if get_agent_metrics retrieves metrics for an agent."""
        # Log some decisions
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason 1",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="SELL",
            confidence=90,
            reason="Test reason 2",
            symbol="ETH/USDT",
            price=3000.0
        )
        
        # Get metrics for TestAgent
        metrics = self.logger.get_agent_metrics("TestAgent")
        
        # Check metrics
        self.assertEqual(metrics['total_decisions'], 2)
        self.assertEqual(metrics['buy_signals'], 1)
        self.assertEqual(metrics['sell_signals'], 1)
        
        # Check that metrics for non-existent agent returns empty dict
        self.assertEqual(self.logger.get_agent_metrics("NonExistentAgent"), {})
        
        # Check that get_agent_metrics() without agent name returns all metrics
        all_metrics = self.logger.get_agent_metrics()
        self.assertIsInstance(all_metrics, dict)
        self.assertIn("TestAgent", all_metrics)
        
    def test_clear_history(self):
        """Test if clear_history clears all decisions and metrics."""
        # Log some decisions
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        # Clear history
        self.logger.clear_history()
        
        # Check that decisions and metrics are empty
        self.assertEqual(len(self.logger.decisions), 0)
        self.assertEqual(len(self.logger.agent_metrics), 0)
        
    def test_export_decisions_json(self):
        """Test exporting decisions to JSON."""
        # Log some decisions
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        # Export to JSON
        export_file = os.path.join(self.test_log_dir, "test_export.json")
        result = self.logger.export_decisions(format="json", output_file=export_file)
        
        # Check that export was successful
        self.assertEqual(result, export_file)
        self.assertTrue(os.path.exists(export_file))
        
        # Check file contents
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
            
        self.assertEqual(len(exported_data), 1)
        self.assertEqual(exported_data[0]['agent'], "TestAgent")
        self.assertEqual(exported_data[0]['signal'], "BUY")
        
    def test_export_decisions_csv(self):
        """Test exporting decisions to CSV."""
        # Log some decisions
        self.logger.log_decision(
            agent_name="TestAgent",
            signal="BUY",
            confidence=80,
            reason="Test reason",
            symbol="BTC/USDT",
            price=50000.0
        )
        
        # Export to CSV
        export_file = os.path.join(self.test_log_dir, "test_export.csv")
        result = self.logger.export_decisions(format="csv", output_file=export_file)
        
        # Check that export was successful
        self.assertEqual(result, export_file)
        self.assertTrue(os.path.exists(export_file))
        
        # Check file contents (basic check)
        with open(export_file, 'r') as f:
            content = f.read()
            
        self.assertIn("id,agent,symbol,signal,confidence,reason,price,timestamp", content)
        self.assertIn("TestAgent", content)
        self.assertIn("BUY", content)

def main():
    """Run the test suite."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDecisionLogger))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())