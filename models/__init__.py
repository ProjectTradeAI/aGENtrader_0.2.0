"""
aGENtrader v2 Models Package

This package contains model implementations and clients for aGENtrader v2.
"""

# Import model modules
try:
    from .llm_client import LLMClient
except ImportError:
    LLMClient = None

# Export available models
__all__ = [
    'LLMClient'
]