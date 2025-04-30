"""
aGENtrader v2 Agent System

This package contains specialist agents for market analysis and decision making.
"""

from .agent_interface import (
    AgentInterface,
    AnalystAgentInterface,
    DecisionAgentInterface,
    ExecutionAgentInterface
)

from .base_agent import (
    BaseAgent,
    BaseAnalystAgent,
    BaseDecisionAgent
)

__all__ = [
    'AgentInterface',
    'AnalystAgentInterface',
    'DecisionAgentInterface',
    'ExecutionAgentInterface',
    'BaseAgent',
    'BaseAnalystAgent',
    'BaseDecisionAgent'
]