"""
Unit tests for the Liquidity Analyst Agent

This module tests the functionality of the LiquidityAnalystAgent class.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from typing import Dict, Any

# Add parent directory to path to allow importing from the main package
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import modules to test
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from utils.logger import get_logger

# Setup logger for testing
logger = get_logger("test_liquidity_analyst")

class TestLiquidityAnalystAgent(unittest.TestCase):
    """Test cases for LiquidityAnalystAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_db_connector = MagicMock()
        self.mock_llm_client = MagicMock()
        
        # Set up the mock responses
        self.setup_mock_db_responses()
        self.setup_mock_llm_responses()
        
        # Create a patched agent with mocks
        with patch('agents.liquidity_analyst_agent.DatabaseConnector') as mock_db_class, \
             patch('agents.liquidity_analyst_agent.LLMClient') as mock_llm_class:
            # Configure the mock classes to return our mock instances
            mock_db_class.return_value = self.mock_db_connector
            mock_llm_class.return_value = self.mock_llm_client
            
            # Create the agent
            self.agent = LiquidityAnalystAgent()
    
    def setup_mock_db_responses(self):
        """Set up mock database responses."""
        # Mock connect/disconnect methods
        self.mock_db_connector.connect.return_value = True
        self.mock_db_connector.disconnect.return_value = None
        
        # Create mock market depth data
        market_depth_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-04-01', periods=10, freq='H'),
            'bid_depth': [1000000, 950000, 1100000, 1050000, 980000, 
                          1020000, 1070000, 990000, 1030000, 1060000],
            'ask_depth': [900000, 920000, 880000, 950000, 930000, 
                          890000, 910000, 940000, 900000, 880000],
            'bid_ask_ratio': [1.11, 1.03, 1.25, 1.11, 1.05, 
                              1.15, 1.18, 1.05, 1.14, 1.20]
        })
        
        # Convert pandas numeric types to Python native types
        market_depth_data['bid_depth'] = market_depth_data['bid_depth'].astype(float)
        market_depth_data['ask_depth'] = market_depth_data['ask_depth'].astype(float)
        market_depth_data['bid_ask_ratio'] = market_depth_data['bid_ask_ratio'].astype(float)
        
        # Create mock volume profile data
        volume_profile_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-04-01', periods=20, freq='30min'),
            'price_level': [45000, 45100, 45200, 45300, 45400, 45500, 45600, 45700, 45800, 45900,
                           46000, 46100, 46200, 46300, 46400, 46500, 46600, 46700, 46800, 46900],
            'volume': [15000, 22000, 12000, 8000, 5000, 18000, 25000, 7000, 4000, 3000,
                      20000, 10000, 6000, 9000, 11000, 14000, 8000, 5000, 7000, 9000],
            'is_buying': [True, False, True, False, True, False, True, False, True, False,
                         True, False, True, False, True, False, True, False, True, False]
        })
        
        # Convert pandas numeric types to Python native types
        volume_profile_data['price_level'] = volume_profile_data['price_level'].astype(float)
        volume_profile_data['volume'] = volume_profile_data['volume'].astype(float)
        
        # Create mock funding rate data
        funding_rate_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-04-01', periods=10, freq='8H'),
            'rate': [0.01, 0.008, 0.012, -0.005, 0.002, 0.009, 0.015, -0.003, 0.007, 0.011]
        })
        
        # Convert pandas numeric types to Python native types
        funding_rate_data['rate'] = funding_rate_data['rate'].astype(float)
        
        # Configure the mock methods to return our dataframes
        self.mock_db_connector.get_market_depth.return_value = market_depth_data
        self.mock_db_connector.get_volume_profile.return_value = volume_profile_data
        self.mock_db_connector.get_funding_rates.return_value = funding_rate_data
    
    def setup_mock_llm_responses(self):
        """Set up mock LLM responses."""
        # Mock LLM analysis response
        mock_llm_response = json.dumps({
            "analysis": {
                "overall_liquidity": "high",
                "bid_ask_imbalance": "neutral",
                "volume_profile": "above average",
                "depth_analysis": "Large buy walls observed at key support levels",
                "funding_rate_impact": "neutral to slightly positive",
                "liquidity_score": 78
            },
            "interpretation": "Market shows strong liquidity with balanced order books. Volume concentration at key price levels suggests institutional interest.",
            "recommendation": "Current liquidity conditions are favorable for both entry and exit with minimal slippage."
        })
        
        # Configure the mock generate method to return our response
        self.mock_llm_client.generate.return_value = mock_llm_response
    
    def test_analyze_returns_valid_structure(self):
        """Test that analyze method returns a dictionary with expected structure."""
        # Call the agent's analyze method
        symbol = "BTCUSDT"
        interval = "1h"
        result = self.agent.analyze(symbol, interval)
        
        # Log the result for visual inspection
        logger.info(f"Analysis result: {json.dumps(result, default=json_serializable, indent=2)}")
        
        # Assert the result is a dictionary
        self.assertIsInstance(result, dict)
        
        # Assert required fields are present
        self.assertIn("symbol", result)
        self.assertIn("interval", result)
        self.assertIn("timestamp", result)
        
        # Assert the symbol and interval match what we passed in
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["interval"], interval)
        
        # Assert analysis fields are present
        self.assertIn("rule_analysis", result)
        self.assertIn("llm_analysis", result)
        
        # Assert LLM analysis contains expected fields
        llm_analysis = result["llm_analysis"]
        self.assertIn("analysis", llm_analysis)
        self.assertIn("interpretation", llm_analysis)
        self.assertIn("recommendation", llm_analysis)
        
        # Assert liquidity score is within expected range
        self.assertIn("liquidity_score", llm_analysis["analysis"])
        liquidity_score = llm_analysis["analysis"]["liquidity_score"]
        self.assertGreaterEqual(liquidity_score, 0)
        self.assertLessEqual(liquidity_score, 100)
    
    def test_analyze_with_no_data(self):
        """Test that analyze method handles the case where no data is available."""
        # Configure mock to return empty dataframes
        self.mock_db_connector.get_market_depth.return_value = pd.DataFrame()
        self.mock_db_connector.get_volume_profile.return_value = pd.DataFrame()
        self.mock_db_connector.get_funding_rates.return_value = pd.DataFrame()
        
        # Call the agent's analyze method
        result = self.agent.analyze("BTCUSDT", "1h")
        
        # Log the result for visual inspection
        logger.info(f"No data analysis result: {json.dumps(result, default=json_serializable, indent=2)}")
        
        # Assert that an error message is returned
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No data available for analysis")
    
    def test_db_connection_failure(self):
        """Test that analyze method handles database connection failures."""
        # Configure mock to simulate connection failure
        self.mock_db_connector.connect.return_value = False
        
        # Call the agent's analyze method
        result = self.agent.analyze("BTCUSDT", "1h")
        
        # Log the result for visual inspection
        logger.info(f"DB connection failure result: {json.dumps(result, default=json_serializable, indent=2)}")
        
        # Assert that the function returns a valid result even on connection failure
        self.assertIsInstance(result, dict)
        self.assertIn("symbol", result)
        self.assertIn("interval", result)

def json_serializable(obj):
    """Convert objects to JSON serializable types."""
    import numpy as np
    import pandas as pd
    from datetime import datetime, date
    
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return str(obj)

def run_tests():
    """Run the unit tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    print("Running Liquidity Analyst Agent tests...")
    run_tests()
    print("Tests completed.")