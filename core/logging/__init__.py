"""
aGENtrader v2 Logging Module

This package contains logging functionality for the aGENtrader v2 system.
"""

from .decision_logger import DecisionLogger, decision_logger

__all__ = [
    'DecisionLogger',
    'decision_logger'
]