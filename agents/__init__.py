"""
aGENtrader v2 Agents Package

This package contains all agent implementations for aGENtrader v2.
"""

# Export interfaces
from .agent_interface import (
    AgentInterface,
    AnalystAgentInterface,
    DecisionAgentInterface,
    ExecutionAgentInterface
)

# Export base classes
from .base_agent import (
    BaseAgent,
    BaseAnalystAgent,
    BaseDecisionAgent
)

# Import specialized agents if available
try:
    from .technical_analyst_agent import TechnicalAnalystAgent
except ImportError:
    TechnicalAnalystAgent = None

try:
    from .sentiment_analyst_agent import SentimentAnalystAgent
except ImportError:
    SentimentAnalystAgent = None

try:
    from .sentiment_aggregator_agent import SentimentAggregatorAgent
except ImportError:
    SentimentAggregatorAgent = None

try:
    from .liquidity_analyst_agent import LiquidityAnalystAgent
except ImportError:
    LiquidityAnalystAgent = None

try:
    from .funding_rate_analyst_agent import FundingRateAnalystAgent
except ImportError:
    FundingRateAnalystAgent = None

try:
    from .open_interest_analyst_agent import OpenInterestAnalystAgent
except ImportError:
    OpenInterestAnalystAgent = None

try:
    from .decision_agent import DecisionAgent
except ImportError:
    DecisionAgent = None

# Export the available agents
__all__ = [
    # Interfaces
    'AgentInterface',
    'AnalystAgentInterface',
    'DecisionAgentInterface',
    'ExecutionAgentInterface',
    
    # Base classes
    'BaseAgent',
    'BaseAnalystAgent',
    'BaseDecisionAgent',
    
    # Specialized agents (may be None if not implemented)
    'TechnicalAnalystAgent',
    'SentimentAnalystAgent',
    'SentimentAggregatorAgent',
    'LiquidityAnalystAgent',
    'FundingRateAnalystAgent',
    'OpenInterestAnalystAgent',
    'DecisionAgent'
]