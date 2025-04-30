"""
aGENtrader v2 Decision Logger

This module provides decision logging functionality to create human-readable summaries
of agent decisions for monitoring and potential model training.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create a singleton instance for easy import
decision_logger = None


class DecisionLogger:
    """
    Decision logger that creates human-readable summaries of agent decisions.
    
    This class handles logging of agent decisions in a standardized format.
    """
    
    def __init__(self, log_path: str = 'logs/decision_summary.log'):
        """
        Initialize the decision logger.
        
        Args:
            log_path: Path to the log file
        """
        self.log_path = log_path
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Initialize file logger
        self.file_logger = logging.getLogger('decision_logger')
        self.file_logger.setLevel(logging.INFO)
        
        # Check if handlers already exist to avoid duplicates
        if not self.file_logger.handlers:
            # Add file handler
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
            self.file_logger.addHandler(file_handler)
            
        logger.info(f"Decision logger initialized with log path: {log_path}")
        
    def log_decision(
        self,
        agent_name: str,
        signal: str,
        confidence: int,
        reason: str,
        symbol: Optional[str] = None,
        price: Optional[float] = None,
        timestamp: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        interval: Optional[str] = None
    ) -> Optional[str]:
        """
        Log a decision to the decision summary log.
        
        Args:
            agent_name: Name of the agent making the decision
            signal: Trading signal (BUY, SELL, HOLD, etc.)
            confidence: Confidence percentage
            reason: Short reason for the decision (1 sentence max)
            symbol: Trading symbol (e.g., BTC/USDT)
            price: Current price
            timestamp: Custom timestamp (defaults to current UTC time)
            additional_data: Additional data to store for future reference
            interval: Time interval used for the analysis
            
        Returns:
            The logged summary string or None if logging failed
        """
        try:
            # Set defaults
            if not timestamp:
                timestamp = datetime.now().isoformat()
                
            # Limit reason to one sentence for readability
            reason = self._limit_to_one_sentence(reason)
            
            # Build log entry
            entry = {
                'timestamp': timestamp,
                'agent': agent_name,
                'signal': signal.upper(),
                'confidence': confidence,
                'reason': reason
            }
            
            # Add optional fields if provided
            if symbol:
                entry['symbol'] = symbol
            if price:
                entry['price'] = price
            if interval:
                entry['interval'] = interval
            if additional_data:
                entry['data'] = additional_data
                
            # Convert to string
            log_str = json.dumps(entry)
            
            # Create human-readable summary
            summary = (
                f"[{timestamp}] {agent_name}: {signal} {symbol or ''} "
                f"with {confidence}% confidence - {reason}"
            )
            
            # Log both machine-readable and human-readable formats
            self.file_logger.info(log_str)
            logger.info(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error logging decision: {str(e)}")
            return None
            
    def _limit_to_one_sentence(self, text: str) -> str:
        """
        Limit the text to one sentence.
        
        Args:
            text: The text to limit
            
        Returns:
            The first sentence from the text
        """
        # Basic sentence splitting - can be improved
        sentence_endings = ['. ', '! ', '? ']
        for ending in sentence_endings:
            if ending in text:
                return text.split(ending)[0] + ending.strip()
                
        # If no sentence ending found, return as is
        return text
        
    @classmethod
    def create_summary_from_result(
        cls,
        agent_name: str,
        result: Dict[str, Any],
        symbol: Optional[str] = None,
        price: Optional[float] = None
    ) -> Optional[str]:
        """
        Create a summary from an agent's result dictionary.
        
        Args:
            agent_name: Name of the agent
            result: The result dictionary from an agent
            symbol: Trading symbol
            price: Current price
            
        Returns:
            The summary string or None if creation failed
        """
        try:
            # Extract info from result
            signal = result.get('signal', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            reason = result.get('reasoning', 'No reason provided')
            timestamp = result.get('timestamp', datetime.now().isoformat())
            
            # Create summary
            summary = (
                f"[{timestamp}] {agent_name}: {signal} {symbol or ''} "
                f"with {confidence}% confidence - {reason}"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            return None


# Initialize the singleton instance
decision_logger = DecisionLogger()