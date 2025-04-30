"""
aGENtrader v2 Logging Module

This module provides logging utilities for aGENtrader v2.
"""

import logging

from core.logging.decision_logger import DecisionLogger

# Configure root logger once
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a global instance of DecisionLogger for convenient access
decision_logger = DecisionLogger()

# Export classes and functions
__all__ = [
    'DecisionLogger',
    'decision_logger'
]