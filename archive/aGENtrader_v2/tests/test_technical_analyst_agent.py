"""
Unit tests for the Technical Analyst Agent

This module tests the functionality of the TechnicalAnalystAgent class.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Any

# Add parent directory to path to allow importing from the main package
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import the json_serializable function from the liquidity test
from tests.test_liquidity_analyst_agent import json_serializable

# Setup logger for testing
from utils.logger import get_logger
logger = get_logger("test_technical_analyst")

class TestTechnicalAnalystAgent(unittest.TestCase):
    """Test cases for TechnicalAnalystAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_db_connector = MagicMock()
        self.mock_llm_client = MagicMock()
        
        # Set up the mock responses
        self.setup_mock_db_responses()
        self.setup_mock_llm_responses()
        
        # Create a patched agent with mocks
        with patch('agents.technical_analyst_agent.DatabaseConnector') as mock_db_class, \
             patch('agents.technical_analyst_agent.LLMClient') as mock_llm_class:
            # Configure the mock classes to return our mock instances
            mock_db_class.return_value = self.mock_db_connector
            mock_llm_class.return_value = self.mock_llm_client
            
            # Import TechnicalAnalystAgent here to ensure our patches work
            from agents.technical_analyst_agent import TechnicalAnalystAgent
            self.TechnicalAnalystAgent = TechnicalAnalystAgent
            
            # Create the agent
            self.agent = TechnicalAnalystAgent()
    
    def setup_mock_db_responses(self):
        """Set up mock database responses."""
        # Mock connect/disconnect methods
        self.mock_db_connector.connect.return_value = True
        self.mock_db_connector.disconnect.return_value = None
        
        # Create mock price data
        price_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-04-01', periods=100, freq='H'),
            'open': [45000 + i * 10 + np.random.randn() * 50 for i in range(100)],
            'high': [45100 + i * 10 + np.random.randn() * 50 for i in range(100)],
            'low': [44900 + i * 10 + np.random.randn() * 50 for i in range(100)],
            'close': [45050 + i * 10 + np.random.randn() * 50 for i in range(100)],
            'volume': [1000000 + np.random.randn() * 50000 for _ in range(100)]
        })
        
        # Convert pandas numeric types to Python native types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            price_data[col] = price_data[col].astype(float)
        
        # Create mock indicator data (e.g., RSI)
        indicator_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-04-01', periods=100, freq='H'),
            'rsi': [30 + np.random.randn() * 20 for _ in range(100)],
            'macd': [5 + np.random.randn() * 3 for _ in range(100)],
            'macd_signal': [4 + np.random.randn() * 2 for _ in range(100)],
            'macd_hist': [1 + np.random.randn() for _ in range(100)]
        })
        
        # Convert pandas numeric types to Python native types
        for col in ['rsi', 'macd', 'macd_signal', 'macd_hist']:
            indicator_data[col] = indicator_data[col].astype(float)
        
        # Configure the mock methods to return our dataframes
        self.mock_db_connector.get_market_data.return_value = price_data
        self.mock_db_connector.get_technical_indicators.return_value = indicator_data
    
    def setup_mock_llm_responses(self):
        """Set up mock LLM responses."""
        # Mock LLM analysis response
        mock_llm_response = json.dumps({
            "market_trend": {
                "primary_trend": "bullish",
                "secondary_trend": "consolidation",
                "strength": "moderate",
                "confidence": 75
            },
            "key_levels": {
                "support": [45100, 44800, 44500],
                "resistance": [45500, 45800, 46200],
                "pivot_point": 45300
            },
            "indicators": {
                "rsi_signal": "neutral",
                "macd_signal": "bullish",
                "overall_signal": "bullish"
            },
            "pattern_recognition": {
                "patterns_identified": ["ascending triangle", "higher lows"],
                "reliability": "high"
            },
            "price_prediction": {
                "short_term": "upward movement likely",
                "medium_term": "target 46000",
                "confidence": 70
            },
            "technical_score": 65
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
        
        # Assert analysis fields are present (technical agent has different fields)
        self.assertIn("indicators", result)
        self.assertIn("pattern_analysis", result)
        self.assertIn("llm_analysis", result)
        
        # Assert key fields in the analysis
        self.assertIn("market_trend", result["llm_analysis"])
        self.assertIn("key_levels", result["llm_analysis"])
        self.assertIn("indicators", result["llm_analysis"])
        
        # Assert technical score is within expected range
        self.assertIn("technical_score", result["llm_analysis"])
        technical_score = result["llm_analysis"]["technical_score"]
        self.assertGreaterEqual(technical_score, 0)
        self.assertLessEqual(technical_score, 100)
    
    def test_analyze_with_no_data(self):
        """Test that analyze method handles the case where no data is available."""
        # Configure mock to return empty dataframes
        self.mock_db_connector.get_market_data.return_value = pd.DataFrame()
        self.mock_db_connector.get_technical_indicators.return_value = pd.DataFrame()
        
        # Also patch the _generate_mock_data method to return empty DataFrame
        with patch.object(self.agent, '_generate_mock_data', return_value=pd.DataFrame()):
            # Call the agent's analyze method
            result = self.agent.analyze("BTCUSDT", "1h")
            
            # Log the result for visual inspection
            logger.info(f"No data analysis result: {json.dumps(result, default=json_serializable, indent=2)}")
            
            # Assert that an error message is returned
            self.assertIn("error", result)
            self.assertEqual(result["error"], "No data available for analysis")
    
    def test_db_connection_failure(self):
        """Test that analyze method handles database connection failures."""
        # The TechnicalAnalystAgent generates mock data when DB connection fails
        # but we want to test what happens when both DB connection fails AND
        # the mock data generation fails
        
        # Configure mock to simulate connection failure
        self.mock_db_connector.connect.return_value = False
        
        # Patch the _generate_mock_data method to return empty DataFrame
        with patch.object(self.agent, '_generate_mock_data', return_value=pd.DataFrame()):
            # Call the agent's analyze method
            result = self.agent.analyze("BTCUSDT", "1h")
            
            # Log the result for visual inspection
            logger.info(f"DB connection failure result: {json.dumps(result, default=json_serializable, indent=2)}")
            
            # Assert that an error message is returned
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertEqual(result["error"], "No data available for analysis")

def run_tests():
    """Run the unit tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    print("Running Technical Analyst Agent tests...")
    run_tests()
    print("Tests completed.")