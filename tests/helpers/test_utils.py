"""
Test utilities for aGENtrader test suite.

This module provides helper functions and utilities for writing and running tests.
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable

# Add root directory to path if needed
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

class TestCase(unittest.TestCase):
    """Enhanced TestCase class with additional assertion methods."""
    
    def assertIsValidSignal(self, signal):
        """Assert that a signal is valid (BUY, SELL, or NEUTRAL)."""
        self.assertIn(signal, ["BUY", "SELL", "NEUTRAL", "HOLD"], 
                     f"Signal '{signal}' is not a valid signal")
        
    def assertIsValidConfidence(self, confidence):
        """Assert that a confidence value is valid (0-100)."""
        self.assertIsInstance(confidence, int, "Confidence must be an integer")
        self.assertTrue(0 <= confidence <= 100, 
                       f"Confidence {confidence} must be between 0 and 100")
        
    def assertIsValidTimestamp(self, timestamp):
        """Assert that a timestamp is valid ISO format."""
        try:
            if isinstance(timestamp, str):
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, int):
                datetime.fromtimestamp(timestamp / 1000)  # Assuming milliseconds
            else:
                self.fail(f"Timestamp {timestamp} is not a string or integer")
        except (ValueError, TypeError):
            self.fail(f"Timestamp '{timestamp}' is not a valid ISO timestamp")
            
    def assertIsValidAgentAnalysis(self, analysis, agent_name=None):
        """Assert that an agent analysis result has the required fields."""
        self.assertIsInstance(analysis, dict, "Analysis must be a dictionary")
        
        # Check required fields
        self.assertIn('signal', analysis, "Analysis missing 'signal' field")
        self.assertIn('confidence', analysis, "Analysis missing 'confidence' field")
        self.assertIn('timestamp', analysis, "Analysis missing 'timestamp' field")
        
        # Check agent name if provided
        if agent_name:
            self.assertEqual(analysis.get('agent'), agent_name, 
                           f"Expected agent name '{agent_name}' but got '{analysis.get('agent')}'")
            
        # Validate field values
        self.assertIsValidSignal(analysis['signal'])
        self.assertIsValidConfidence(analysis['confidence'])
        self.assertIsValidTimestamp(analysis['timestamp'])
        
    def assertIsValidDecision(self, decision):
        """Assert that a decision result has the required fields."""
        self.assertIsInstance(decision, dict, "Decision must be a dictionary")
        
        # Check required fields
        self.assertIn('signal', decision, "Decision missing 'signal' field")
        self.assertIn('confidence', decision, "Decision missing 'confidence' field")
        self.assertIn('timestamp', decision, "Decision missing 'timestamp' field")
        
        # Validate field values
        self.assertIsValidSignal(decision['signal'])
        self.assertIsValidConfidence(decision['confidence'])
        self.assertIsValidTimestamp(decision['timestamp'])

class MockPriceDataGenerator:
    """Generate mock price data for testing."""
    
    @staticmethod
    def generate_uptrend(base_price=50000.0, candles=50, volatility=0.02):
        """Generate an uptrend price series."""
        data = []
        current_price = base_price
        timestamp_base = int(datetime.now().timestamp() * 1000)
        
        for i in range(candles):
            # Add some noise but maintain uptrend
            change_pct = 0.005 + (volatility * (0.5 - (i % 10) / 10))
            
            open_price = current_price
            close_price = current_price * (1 + change_pct)
            high_price = max(open_price, close_price) * 1.01
            low_price = min(open_price, close_price) * 0.99
            
            data.append({
                'timestamp': timestamp_base - (candles - i) * 3600 * 1000,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': 1000000 * (1 + (i % 5) * 0.2)
            })
            
            current_price = close_price
            
        return data
    
    @staticmethod
    def generate_downtrend(base_price=50000.0, candles=50, volatility=0.02):
        """Generate a downtrend price series."""
        data = []
        current_price = base_price
        timestamp_base = int(datetime.now().timestamp() * 1000)
        
        for i in range(candles):
            # Add some noise but maintain downtrend
            change_pct = -0.005 - (volatility * (0.5 - (i % 10) / 10))
            
            open_price = current_price
            close_price = current_price * (1 + change_pct)
            high_price = max(open_price, close_price) * 1.01
            low_price = min(open_price, close_price) * 0.99
            
            data.append({
                'timestamp': timestamp_base - (candles - i) * 3600 * 1000,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': 1000000 * (1 + (i % 5) * 0.2)
            })
            
            current_price = close_price
            
        return data
    
    @staticmethod
    def generate_sideways(base_price=50000.0, candles=50, volatility=0.02):
        """Generate a sideways (ranging) price series."""
        data = []
        current_price = base_price
        timestamp_base = int(datetime.now().timestamp() * 1000)
        
        for i in range(candles):
            # Random noise around base price
            change_pct = volatility * (0.5 - (i % 10) / 10)
            
            open_price = current_price
            close_price = base_price * (1 + change_pct)
            high_price = max(open_price, close_price) * 1.01
            low_price = min(open_price, close_price) * 0.99
            
            data.append({
                'timestamp': timestamp_base - (candles - i) * 3600 * 1000,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': 1000000 * (1 + (i % 5) * 0.2)
            })
            
            current_price = close_price
            
        return data

class DecisionLoggerExtensions:
    """Extensions for the DecisionLogger class to support testing."""
    
    @staticmethod
    def create_summary_from_result(logger_instance, agent_name: str, result: Dict[str, Any], symbol: str):
        """
        Create a summary from analysis result and log it.
        
        Args:
            agent_name: Name of the agent
            result: Analysis result from the agent
            symbol: Trading symbol
            
        This is a compatibility method for code that expects this method to exist.
        """
        if not result or not isinstance(result, dict):
            return None
            
        # Extract key fields
        signal = result.get('signal', 'NEUTRAL')
        confidence = result.get('confidence', 50)
        
        # Get explanation - handle different formats
        explanation = result.get('explanation', '')
        if isinstance(explanation, list) and explanation:
            explanation = explanation[0]
        elif not explanation:
            explanation = f"{agent_name} analysis"
            
        # Get price
        price = result.get('current_price', 0)
        
        # Log the decision if we have a valid price
        if price > 0:
            try:
                logger_instance.log_decision(
                    agent_name=agent_name,
                    signal=signal,
                    confidence=confidence,
                    reason=explanation,
                    symbol=symbol,
                    price=price,
                    timestamp=result.get('timestamp', datetime.now().isoformat()),
                    additional_data=result.get('metrics', {})
                )
            except Exception as e:
                print(f"Warning: Failed to log decision: {str(e)}")
                
        return {
            'agent': agent_name,
            'signal': signal,
            'confidence': confidence,
            'explanation': explanation
        }