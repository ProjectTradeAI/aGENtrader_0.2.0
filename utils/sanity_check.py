#!/usr/bin/env python3
# Standard library imports
import logging
import math
from typing import Dict, Any, List, Union, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Try to import numpy for array validation
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available. Array validation will use basic methods.")
"""
Sanity Check Utilities for aGENtrader v0.2.2

This module provides utility functions for performing sanity checks on agent outputs.
These checks ensure that agent outputs are well-formed and reliable before 
they are used in decision making.
"""

# Module contains all necessary imports at the top

def validate_action_format(output: Dict[str, Any]) -> bool:
    """
    Validate that the action format is correct.
    
    Args:
        output: Agent output dictionary
        
    Returns:
        True if action format is valid, False otherwise
    """
    # Check if recommendation exists
    if 'recommendation' not in output:
        logger.warning("Missing 'recommendation' in agent output")
        return False
        
    # Check if action exists in recommendation
    recommendation = output.get('recommendation', {})
    if not isinstance(recommendation, dict):
        logger.warning(f"'recommendation' is not a dictionary: {type(recommendation)}")
        return False
        
    if 'action' not in recommendation:
        logger.warning("Missing 'action' in recommendation")
        return False
        
    # Check if action is a valid value
    action = recommendation.get('action')
    valid_actions = ['BUY', 'SELL', 'HOLD', 'NEUTRAL', 'CONFLICTED']
    if action not in valid_actions:
        logger.warning(f"Invalid action: {action}, must be one of {valid_actions}")
        return False
        
    return True

def validate_confidence_score(output: Dict[str, Any]) -> bool:
    """
    Validate that the confidence score is valid.
    
    Args:
        output: Agent output dictionary
        
    Returns:
        True if confidence score is valid, False otherwise
    """
    # Check if recommendation exists
    if 'recommendation' not in output:
        return False
        
    # Check if confidence exists in recommendation
    recommendation = output.get('recommendation', {})
    if 'confidence' not in recommendation:
        logger.warning("Missing 'confidence' in recommendation")
        return False
        
    # Check if confidence is a number
    confidence = recommendation.get('confidence')
    if not isinstance(confidence, (int, float)):
        logger.warning(f"Confidence is not a number: {type(confidence)}")
        return False
        
    # Check if confidence is within valid range
    if confidence < 0 or confidence > 100:
        logger.warning(f"Confidence out of range: {confidence}, must be between 0 and 100")
        return False
        
    # Check if confidence is a valid number (not NaN or Inf)
    if isinstance(confidence, float) and (math.isnan(confidence) or math.isinf(confidence)):
        logger.warning(f"Confidence is an invalid number: {confidence}")
        return False
        
    return True

def validate_required_fields(output: Dict[str, Any], required_fields: Optional[List[str]] = None) -> bool:
    """
    Validate that the output contains all required fields.
    
    Args:
        output: Agent output dictionary
        required_fields: List of required field names (optional)
        
    Returns:
        True if all required fields are present, False otherwise
    """
    # Default required fields if not specified
    if required_fields is None:
        required_fields = ['agent_name', 'timestamp', 'signal', 'confidence']
        
    # Check if all required fields are present
    for field in required_fields:
        if field not in output:
            logger.warning(f"Missing required field: {field}")
            return False
            
    return True

def validate_numeric_fields(output: Dict[str, Any], numeric_fields: Optional[List[str]] = None) -> bool:
    """
    Validate that numeric fields contain valid numbers.
    
    Args:
        output: Agent output dictionary
        numeric_fields: List of numeric field names (optional)
        
    Returns:
        True if all numeric fields contain valid numbers, False otherwise
    """
    # Default numeric fields if not specified
    if numeric_fields is None:
        numeric_fields = ['confidence', 'score', 'value', 'probability']
        
    # Check all numeric fields
    for field in numeric_fields:
        # Skip if field doesn't exist
        if field not in output:
            continue
            
        value = output[field]
        
        # Check if value is a number
        if not isinstance(value, (int, float)):
            logger.warning(f"Field '{field}' is not a number: {type(value)}")
            return False
            
        # Check if value is a valid number (not NaN or Inf)
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            logger.warning(f"Field '{field}' contains an invalid number: {value}")
            return False
            
    return True

def validate_data_arrays(output: Dict[str, Any], array_fields: Optional[List[str]] = None) -> bool:
    """
    Validate that data arrays are non-empty and contain valid values.
    
    Args:
        output: Agent output dictionary
        array_fields: List of array field names (optional)
        
    Returns:
        True if all array fields are valid, False otherwise
    """
    # Default array fields if not specified
    if array_fields is None:
        array_fields = ['data', 'prices', 'volumes', 'indicators', 'values']
        
    # Check all array fields
    for field in array_fields:
        # Skip if field doesn't exist
        if field not in output:
            continue
            
        value = output[field]
        
        # Check if value is a list or numpy array
        if NUMPY_AVAILABLE:
            if not isinstance(value, (list, np.ndarray)):
                logger.warning(f"Field '{field}' is not an array: {type(value)}")
                return False
                
            # Check if array is empty
            if len(value) == 0:
                logger.warning(f"Field '{field}' is an empty array")
                return False
                
            # Check if array contains all zeros (potential data issue)
            if isinstance(value, np.ndarray) and np.all(value == 0):
                logger.warning(f"Field '{field}' contains all zeros")
                return False
                
            # Check if array contains any NaN or Inf values
            if isinstance(value, np.ndarray) and (np.isnan(value).any() or np.isinf(value).any()):
                logger.warning(f"Field '{field}' contains NaN or Inf values")
                return False
        else:
            # Fallback for when numpy is not available
            if not isinstance(value, list):
                logger.warning(f"Field '{field}' is not a list: {type(value)}")
                return False
                
            # Check if array is empty
            if len(value) == 0:
                logger.warning(f"Field '{field}' is an empty list")
                return False
                
            # Basic check for all zeros
            if all(v == 0 for v in value if isinstance(v, (int, float))):
                logger.warning(f"Field '{field}' contains all zeros")
                return False
            
    return True

def check_passed_sanity_flag(output: Dict[str, Any]) -> bool:
    """
    Check if the output includes a passed_sanity_check flag.
    
    Args:
        output: Agent output dictionary
        
    Returns:
        Value of passed_sanity_check if present, False otherwise
    """
    # Check if passed_sanity_check exists and is a boolean
    if 'passed_sanity_check' in output and isinstance(output['passed_sanity_check'], bool):
        return output['passed_sanity_check']
        
    logger.warning("Missing or invalid 'passed_sanity_check' flag in agent output")
    return False

def sanitize_agent_output(output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform all sanity checks on agent output and update the passed_sanity_check flag.
    
    Args:
        output: Agent output dictionary
        
    Returns:
        Updated agent output dictionary with passed_sanity_check flag
    """
    # Make a copy of the output to avoid modifying the original
    sanitized_output = output.copy()
    
    # Perform all basic sanity checks
    action_valid = validate_action_format(sanitized_output)
    confidence_valid = validate_confidence_score(sanitized_output)
    fields_valid = validate_required_fields(sanitized_output)
    numeric_valid = validate_numeric_fields(sanitized_output)
    arrays_valid = validate_data_arrays(sanitized_output)
    
    # Set the passed_sanity_check flag based on all checks
    passed_sanity = all([action_valid, confidence_valid, fields_valid, numeric_valid, arrays_valid])
    sanitized_output['passed_sanity_check'] = passed_sanity
    
    # Log the result
    if passed_sanity:
        logger.debug(f"Agent output passed all sanity checks")
    else:
        logger.warning(f"Agent output failed one or more sanity checks")
        
    return sanitized_output

def filter_passed_sanity_checks(analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter a list of agent analyses to include only those that passed sanity checks.
    
    Args:
        analyses: List of agent analysis dictionaries
        
    Returns:
        Filtered list containing only analyses that passed sanity checks
    """
    valid_analyses = []
    rejected_analyses = []
    
    for analysis in analyses:
        if check_passed_sanity_flag(analysis):
            valid_analyses.append(analysis)
        else:
            rejected_analyses.append(analysis)
    
    # Log the rejected analyses
    if rejected_analyses:
        agent_names = [a.get('agent_name', 'UnknownAgent') for a in rejected_analyses]
        logger.warning(f"Rejected {len(rejected_analyses)} analyses that failed sanity checks: {agent_names}")
    
    return valid_analyses