"""
aGENtrader v2 Decision Logger

This module provides the DecisionLogger class for recording and tracking
trading decisions made by various agents in the system.
"""

import os
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class DecisionLogger:
    """
    Logger for recording and tracking trading decisions.
    
    This class provides methods to log decisions from various agents,
    track performance, and provide decision history.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the decision logger.
        
        Args:
            log_dir: Directory for storing decision logs
        """
        self.log_dir = log_dir or os.environ.get('DECISION_LOG_DIR', 'logs/decisions')
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                logger.info(f"Created decision log directory: {self.log_dir}")
            except Exception as e:
                logger.warning(f"Failed to create decision log directory: {str(e)}")
                
        # Dictionary to store decision history in memory
        self.decisions = {}
        
        # Dictionary to track agent contribution metrics
        self.agent_metrics = {}
        
        # Load existing decisions if available
        self._load_decisions()
        
    def _load_decisions(self):
        """Load existing decisions from log files."""
        try:
            decisions_file = os.path.join(self.log_dir, 'decisions.json')
            if os.path.exists(decisions_file):
                with open(decisions_file, 'r') as f:
                    self.decisions = json.load(f)
                logger.info(f"Loaded {len(self.decisions)} historical decisions")
        except Exception as e:
            logger.warning(f"Failed to load historical decisions: {str(e)}")
            
    def log_decision(self, 
                     agent_name: str, 
                     signal: str, 
                     confidence: int, 
                     reason: str, 
                     symbol: str, 
                     price: float,
                     timestamp: Optional[str] = None,
                     additional_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a trading decision.
        
        Args:
            agent_name: Name of the agent making the decision
            signal: Trading signal (BUY, SELL, NEUTRAL)
            confidence: Confidence level (0-100)
            reason: Reason for the decision
            symbol: Trading symbol
            price: Current price
            timestamp: Timestamp (optional, will use current time if not provided)
            additional_data: Additional data to include in the log
            
        Returns:
            Decision ID
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        if additional_data is None:
            additional_data = {}
            
        # Generate a unique ID for the decision
        decision_id = f"{symbol.replace('/', '')}-{timestamp}"
        
        # Create the decision record
        decision = {
            'id': decision_id,
            'agent': agent_name,
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'price': price,
            'timestamp': timestamp,
            'additional_data': additional_data
        }
        
        # Store the decision in memory
        self.decisions[decision_id] = decision
        
        # Log to console
        logger.info(f"Decision recorded in performance tracker with ID: {decision_id}")
        logger.info(f"{signal} decision for {symbol} @ {price}")
        logger.info(f"Reasoning: {reason}")
        
        # Update agent metrics
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = {
                'total_decisions': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'neutral_signals': 0,
                'avg_confidence': 0
            }
            
        metrics = self.agent_metrics[agent_name]
        metrics['total_decisions'] += 1
        
        if signal == 'BUY':
            metrics['buy_signals'] += 1
        elif signal == 'SELL':
            metrics['sell_signals'] += 1
        else:
            metrics['neutral_signals'] += 1
            
        # Update average confidence
        metrics['avg_confidence'] = (
            (metrics['avg_confidence'] * (metrics['total_decisions'] - 1) + confidence) / 
            metrics['total_decisions']
        )
        
        # Save to file periodically
        if metrics['total_decisions'] % 10 == 0:
            self._save_decisions()
            
        return decision_id
        
    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific decision by ID.
        
        Args:
            decision_id: Decision ID
            
        Returns:
            Decision record or None if not found
        """
        return self.decisions.get(decision_id)
        
    def get_decisions_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get decisions for a specific symbol.
        
        Args:
            symbol: Trading symbol
            limit: Maximum number of decisions to return
            
        Returns:
            List of decision records
        """
        matching_decisions = [
            d for d in self.decisions.values() 
            if d['symbol'] == symbol
        ]
        
        # Sort by timestamp (newest first)
        matching_decisions.sort(key=lambda d: d['timestamp'], reverse=True)
        
        return matching_decisions[:limit]
        
    def get_decisions_by_agent(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get decisions made by a specific agent.
        
        Args:
            agent_name: Name of the agent
            limit: Maximum number of decisions to return
            
        Returns:
            List of decision records
        """
        matching_decisions = [
            d for d in self.decisions.values() 
            if d['agent'] == agent_name
        ]
        
        # Sort by timestamp (newest first)
        matching_decisions.sort(key=lambda d: d['timestamp'], reverse=True)
        
        return matching_decisions[:limit]
        
    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Get metrics for a specific agent or all agents.
        
        Args:
            agent_name: Name of the agent (optional)
            
        Returns:
            Dictionary of agent metrics
        """
        if agent_name:
            return self.agent_metrics.get(agent_name, {})
        return self.agent_metrics
        
    def _save_decisions(self):
        """Save decisions to a file."""
        try:
            decisions_file = os.path.join(self.log_dir, 'decisions.json')
            with open(decisions_file, 'w') as f:
                json.dump(self.decisions, f, indent=2)
                
            metrics_file = os.path.join(self.log_dir, 'agent_metrics.json')
            with open(metrics_file, 'w') as f:
                json.dump(self.agent_metrics, f, indent=2)
                
            logger.debug(f"Saved {len(self.decisions)} decisions to {decisions_file}")
        except Exception as e:
            logger.warning(f"Failed to save decisions: {str(e)}")
    
    def clear_history(self):
        """Clear decision history."""
        self.decisions = {}
        self.agent_metrics = {}
        logger.info("Decision history cleared")
        
    def export_decisions(self, format: str = 'json', output_file: Optional[str] = None) -> Optional[str]:
        """
        Export decisions to a file in the specified format.
        
        Args:
            format: Export format ('json' or 'csv')
            output_file: Output file path (optional)
            
        Returns:
            Path to the output file if successful, None otherwise
        """
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_file = os.path.join(self.log_dir, f'decisions_export_{timestamp}.{format}')
            
        try:
            if format == 'json':
                with open(output_file, 'w') as f:
                    json.dump(list(self.decisions.values()), f, indent=2)
            elif format == 'csv':
                import csv
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header
                    header = ['id', 'agent', 'symbol', 'signal', 'confidence', 'reason', 'price', 'timestamp']
                    writer.writerow(header)
                    
                    # Write rows
                    for d in self.decisions.values():
                        row = [d.get(h, '') for h in header]
                        writer.writerow(row)
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
                
            logger.info(f"Exported {len(self.decisions)} decisions to {output_file}")
            return output_file
            
        except Exception as e:
            logger.warning(f"Failed to export decisions: {str(e)}")
            return None