#!/usr/bin/env python3
"""
Test for aGENtrader v0.2.2 Self-Sanity Checks

This script tests the sanity check utilities to ensure they correctly
validate agent outputs and filter out invalid ones.
"""

import os
import sys
import logging
import unittest
from datetime import datetime

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import sanity check utilities
from utils.sanity_check import (
    validate_action_format,
    validate_confidence_score,
    validate_required_fields,
    validate_numeric_fields,
    validate_data_arrays,
    check_passed_sanity_flag,
    sanitize_agent_output,
    filter_passed_sanity_checks
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestSanityChecks(unittest.TestCase):
    """Test cases for sanity check utilities"""
    
    def setUp(self):
        """Setup test data"""
        self.valid_output = {
            "agent_name": "TestAgent",
            "timestamp": datetime.now().isoformat(),
            "recommendation": {
                "action": "BUY",
                "confidence": 85
            },
            "signal": "BUY",
            "confidence": 85,
            "reasoning": "Test reasoning"
        }
        
        self.error_output = {
            "error": True,
            "error_code": "TEST_ERROR",
            "message": "Test error message",
            "agent_name": "TestAgent",
            "timestamp": datetime.now().isoformat()
        }
    
    def test_validate_action_format(self):
        """Test validate_action_format function"""
        # Valid case
        self.assertTrue(validate_action_format(self.valid_output))
        
        # Missing recommendation
        invalid_output = self.valid_output.copy()
        invalid_output.pop("recommendation")
        self.assertFalse(validate_action_format(invalid_output))
        
        # Invalid action
        invalid_output = self.valid_output.copy()
        invalid_output["recommendation"]["action"] = "INVALID_ACTION"
        self.assertFalse(validate_action_format(invalid_output))
    
    def test_validate_confidence_score(self):
        """Test validate_confidence_score function"""
        # Valid case
        self.assertTrue(validate_confidence_score(self.valid_output))
        
        # Missing confidence
        invalid_output = self.valid_output.copy()
        invalid_output["recommendation"].pop("confidence")
        self.assertFalse(validate_confidence_score(invalid_output))
        
        # Confidence out of range
        invalid_output = self.valid_output.copy()
        invalid_output["recommendation"]["confidence"] = 101
        self.assertFalse(validate_confidence_score(invalid_output))
        
        invalid_output["recommendation"]["confidence"] = -1
        self.assertFalse(validate_confidence_score(invalid_output))
    
    def test_validate_required_fields(self):
        """Test validate_required_fields function"""
        # Valid case with default required fields
        self.assertTrue(validate_required_fields(self.valid_output))
        
        # Missing a required field
        invalid_output = self.valid_output.copy()
        invalid_output.pop("agent_name")
        self.assertFalse(validate_required_fields(invalid_output))
        
        # Custom required fields
        custom_fields = ["signal", "confidence", "reasoning"]
        self.assertTrue(validate_required_fields(self.valid_output, custom_fields))
        
        invalid_output = self.valid_output.copy()
        invalid_output.pop("reasoning")
        self.assertFalse(validate_required_fields(invalid_output, custom_fields))
    
    def test_validate_numeric_fields(self):
        """Test validate_numeric_fields function"""
        # Valid case
        self.assertTrue(validate_numeric_fields(self.valid_output))
        
        # Invalid numeric field
        invalid_output = self.valid_output.copy()
        invalid_output["confidence"] = "not a number"
        self.assertFalse(validate_numeric_fields(invalid_output))
        
        # NaN value
        import math
        invalid_output = self.valid_output.copy()
        invalid_output["confidence"] = float('nan')
        self.assertFalse(validate_numeric_fields(invalid_output))
    
    def test_check_passed_sanity_flag(self):
        """Test check_passed_sanity_flag function"""
        # No flag present
        self.assertFalse(check_passed_sanity_flag(self.valid_output))
        
        # Flag is True
        output_with_flag = self.valid_output.copy()
        output_with_flag["passed_sanity_check"] = True
        self.assertTrue(check_passed_sanity_flag(output_with_flag))
        
        # Flag is False
        output_with_flag["passed_sanity_check"] = False
        self.assertFalse(check_passed_sanity_flag(output_with_flag))
    
    def test_sanitize_agent_output(self):
        """Test sanitize_agent_output function"""
        # Valid output
        sanitized_output = sanitize_agent_output(self.valid_output)
        self.assertTrue(sanitized_output["passed_sanity_check"])
        
        # Error output
        sanitized_error = sanitize_agent_output(self.error_output)
        self.assertFalse(sanitized_error["passed_sanity_check"])
        
        # Invalid action
        invalid_output = self.valid_output.copy()
        invalid_output["recommendation"]["action"] = "INVALID_ACTION"
        sanitized_invalid = sanitize_agent_output(invalid_output)
        self.assertFalse(sanitized_invalid["passed_sanity_check"])
    
    def test_filter_passed_sanity_checks(self):
        """Test filter_passed_sanity_checks function"""
        # Create a list of analyses
        passed1 = self.valid_output.copy()
        passed1["passed_sanity_check"] = True
        passed1["agent_name"] = "Agent1"
        
        passed2 = self.valid_output.copy()
        passed2["passed_sanity_check"] = True
        passed2["agent_name"] = "Agent2"
        
        failed1 = self.error_output.copy()
        failed1["passed_sanity_check"] = False
        failed1["agent_name"] = "Agent3"
        
        analyses = [passed1, passed2, failed1]
        
        # Filter the analyses
        filtered = filter_passed_sanity_checks(analyses)
        
        # Check results
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["agent_name"], "Agent1")
        self.assertEqual(filtered[1]["agent_name"], "Agent2")

if __name__ == "__main__":
    unittest.main()