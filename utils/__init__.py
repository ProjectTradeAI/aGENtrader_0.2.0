"""
aGENtrader v2 Utilities Package

This package contains utility functions and classes for aGENtrader v2.
"""

# Import utility modules
try:
    from .mock_data_provider import MockDataProvider
except ImportError:
    MockDataProvider = None

# Export available utilities
__all__ = [
    'MockDataProvider'
]