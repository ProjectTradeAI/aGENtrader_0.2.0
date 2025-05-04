"""
aGENtrader v2 Base Decision Agent

This module provides the base decision agent class that synthesizes
analysis results from analyst agents to make trading decisions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.agent_interface import DecisionAgentInterface
from core.logging import decision_logger

# Configure logging
logger = logging.getLogger("aGENtrader.agents.decision")

class BaseDecisionAgent(BaseAgent, DecisionAgentInterface):
    """
    Base class for decision agents that synthesize analysis results.
    
    This class implements the common functionality for decision agents:
    - Collecting analysis results from various analyst agents
    - Weighing different analysis types
    - Synthesizing a final trading decision
    - Logging the decision with explanation
    """
    
    def __init__(self, analyst_results: Optional[Dict[str, Any]] = None):
        """
        Initialize the base decision agent.
        
        Args:
            analyst_results: Optional dictionary of analyst results
        """
        super().__init__(agent_name="decision")
        self._description = "Base decision agent for trading signals"
        
        # Storage for analyst results
        self.analyst_results = analyst_results or {}
        
        # Default weights for different analysis types
        self.analysis_weights = {
            'technical_analysis': 0.30,
            'sentiment_analysis': 0.20,
            'liquidity_analysis': 0.15,
            'funding_rate_analysis': 0.15,
            'open_interest_analysis': 0.20
        }
        
        # Current market symbol and price
        self.symbol = None
        self.current_price = None
        
    def add_analyst_result(self, analysis_type: str, result: Dict[str, Any]) -> None:
        """
        Add an analyst result to be considered in decision making.
        
        Args:
            analysis_type: Type of analysis (e.g., 'technical', 'sentiment')
            result: Dictionary with analysis results
        """
        if not result:
            logger.warning(f"Received empty {analysis_type} result")
            return
            
        # Validate the result has required fields
        required_fields = ['signal', 'confidence', 'reasoning']
        for field in required_fields:
            if field not in result:
                logger.warning(f"{analysis_type} result missing required field: {field}")
                return
                
        # Store the result
        self.analyst_results[analysis_type] = result
        logger.info(f"Added {analysis_type} result with signal: {result['signal']}, confidence: {result['confidence']}")
        
    def make_decision(self) -> Dict[str, Any]:
        """
        Make a trading decision based on analyst results.
        
        Returns:
            Dictionary with decision results
        """
        if not self.analyst_results:
            logger.warning("No analyst results available for decision making")
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reasoning': 'No analyst data available',
                'timestamp': datetime.now().isoformat(),
                'contributions': {},
                'data': {}
            }
            
        # Normalize and weigh signals
        signal_scores = {
            'BUY': 0.0,
            'HOLD': 0.0,
            'SELL': 0.0
        }
        
        # Track contributions for explanation
        contributions = {}
        
        # Collect all analyst data
        all_analyst_data = {}
        
        # Process each analysis result
        total_weight = 0.0
        for analysis_type, result in self.analyst_results.items():
            # Skip if the result has an error
            if 'error' in result:
                logger.warning(f"Skipping {analysis_type} due to error: {result.get('error_message', 'Unknown error')}")
                continue
                
            # Get the weight for this analysis type
            weight = self.analysis_weights.get(analysis_type, 0.1)
            total_weight += weight
            
            # Get the signal and confidence
            signal = result.get('signal', 'HOLD')
            confidence = result.get('confidence', 50) / 100.0  # Normalize to 0-1
            
            # Adjust signal to standard format
            if signal not in signal_scores:
                if signal == 'NEUTRAL':
                    signal = 'HOLD'
                else:
                    logger.warning(f"Unknown signal from {analysis_type}: {signal}")
                    signal = 'HOLD'
                    
            # Calculate weighted contribution
            contribution = weight * confidence
            
            # Add to signal scores
            signal_scores[signal] += contribution
            
            # Track contribution
            contributions[analysis_type] = {
                'signal': signal,
                'confidence': result.get('confidence', 50),
                'contribution': round(contribution * 100, 2)
            }
            
            # Collect analyst data
            if 'data' in result:
                all_analyst_data[analysis_type] = result['data']
                
        # Normalize the signal scores if we have any valid analysis
        if total_weight > 0:
            for signal in signal_scores:
                signal_scores[signal] /= total_weight
                
        # Determine final signal
        if signal_scores['BUY'] > signal_scores['SELL'] and signal_scores['BUY'] > signal_scores['HOLD']:
            final_signal = 'BUY'
            signal_strength = signal_scores['BUY']
        elif signal_scores['SELL'] > signal_scores['BUY'] and signal_scores['SELL'] > signal_scores['HOLD']:
            final_signal = 'SELL'
            signal_strength = signal_scores['SELL']
        else:
            final_signal = 'HOLD'
            signal_strength = max(signal_scores['HOLD'], 0.5)  # HOLD should have minimum strength
            
        # Calculate confidence as a percentage
        final_confidence = round(signal_strength * 100)
        
        # Generate reasoning
        reasoning = self._generate_decision_reasoning(final_signal, contributions)
        
        # Create final decision
        decision = {
            'signal': final_signal,
            'confidence': final_confidence,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat(),
            'contributions': contributions,
            'data': {
                'signal_scores': {k: round(v * 100, 2) for k, v in signal_scores.items()},
                'analyst_data': all_analyst_data
            }
        }
        
        # Add symbol and price if available
        if self.symbol:
            decision['symbol'] = self.symbol
        if self.current_price:
            decision['price'] = self.current_price
            
        # Log the decision
        self._log_decision(decision)
        
        return decision
        
    def _generate_decision_reasoning(self, signal: str, contributions: Dict[str, Any]) -> str:
        """
        Generate a reasoning string explaining the decision.
        
        Args:
            signal: Final trading signal
            contributions: Dictionary of analyst contributions
            
        Returns:
            String explaining the decision
        """
        # Count how many analysts agree with final signal
        agreement_count = sum(1 for info in contributions.values() if info['signal'] == signal)
        total_count = len(contributions)
        
        # Start with signal summary
        if signal == 'BUY':
            reasoning = f"BUY signal with {agreement_count}/{total_count} analysts in agreement. "
        elif signal == 'SELL':
            reasoning = f"SELL signal with {agreement_count}/{total_count} analysts in agreement. "
        else:
            reasoning = f"HOLD signal with {agreement_count}/{total_count} analysts in agreement. "
            
        # Add top contributors
        sorted_contributions = sorted(
            [(analysis_type, info) for analysis_type, info in contributions.items()],
            key=lambda x: x[1]['contribution'],
            reverse=True
        )
        
        top_contributors = sorted_contributions[:2]  # Get top 2 contributors
        
        if top_contributors:
            reasoning += "Top signals from "
            for i, (analysis_type, info) in enumerate(top_contributors):
                readable_name = analysis_type.replace('_', ' ').title()
                if i > 0:
                    reasoning += " and "
                reasoning += f"{readable_name} ({info['signal']} @{info['confidence']}%)"
                
        return reasoning
        
    def _log_decision(self, decision: Dict[str, Any]):
        """
        Log the decision to the decision logger.
        
        Args:
            decision: Decision dictionary
        """
        try:
            logger.info(f"Decision made: {decision['signal']} with {decision['confidence']}% confidence")
            
            # Log to decision logger if available
            if decision_logger:
                decision_logger.log_decision(
                    agent_name="DecisionAgent",
                    signal=decision['signal'],
                    confidence=decision['confidence'],
                    reason=decision['reasoning'],
                    symbol=decision.get('symbol'),
                    price=decision.get('price')
                )
        except Exception as e:
            logger.error(f"Error logging decision: {str(e)}")