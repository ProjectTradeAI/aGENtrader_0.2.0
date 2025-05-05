"""
Core logging package for aGENtrader v2.

This package provides centralized logging functionality for the trading system.
"""

from core.logging.decision_logger import DecisionLogger

# Create a global instance of the decision logger
decision_logger = DecisionLogger()

# Export the decision logger
__all__ = ['decision_logger', 'DecisionLogger']