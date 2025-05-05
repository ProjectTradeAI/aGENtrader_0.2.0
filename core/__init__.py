"""
aGENtrader v2 Core Module

This package contains core functionality for the aGENtrader v2 system.
"""

from .version import VERSION, get_version, get_version_banner
from .logging import DecisionLogger, decision_logger

__all__ = [
    'VERSION',
    'get_version',
    'get_version_banner',
    'DecisionLogger',
    'decision_logger'
]