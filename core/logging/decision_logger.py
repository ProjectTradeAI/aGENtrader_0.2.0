"""
aGENtrader v2 Decision Logger

This module provides decision logging functionality to create human-readable summaries
of agent decisions for monitoring and potential model training.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

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
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger('decision_logger')
        self.logger.setLevel(logging.INFO)
        
        # Add file handler if not already added
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_path)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Also add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
        self.logger.info("Decision logger initialized")
        
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
            The summary string that was logged or None if an error occurred
        """
        try:
            # Set defaults
            if timestamp is None:
                timestamp = datetime.utcnow().isoformat()
                
            # Limit reason to one sentence
            short_reason = self._limit_to_one_sentence(reason)
            
            # Format the decision summary
            summary_parts = []
            summary_parts.append(f"AGENT: {agent_name}")
            summary_parts.append(f"SIGNAL: {signal}")
            summary_parts.append(f"CONFIDENCE: {confidence}%")
            
            if symbol:
                summary_parts.append(f"SYMBOL: {symbol}")
                
            if price:
                summary_parts.append(f"PRICE: {price:.2f}")
                
            if interval:
                summary_parts.append(f"INTERVAL: {interval}")
                
            summary_parts.append(f"REASON: {short_reason}")
            
            # Join all parts with separator
            summary = " | ".join(summary_parts)
            
            # Log the summary
            self.logger.info(summary)
            
            # Also log additional data as JSON if provided
            if additional_data:
                data_json = json.dumps(additional_data)
                self.logger.debug(f"Additional data for {agent_name}: {data_json}")
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Error logging decision: {str(e)}")
            return None
            
    def _limit_to_one_sentence(self, text: str) -> str:
        """
        Limit the text to one sentence.
        
        Args:
            text: The text to limit
            
        Returns:
            The first sentence from the text
        """
        # Simple sentence splitting by common sentence terminators
        for terminator in ['. ', '! ', '? ']:
            if terminator in text:
                return text.split(terminator)[0] + terminator.strip()
                
        # If no terminator found, return as is (likely already one sentence)
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
            # Extract required fields from the result
            signal = result.get('signal')
            confidence = result.get('confidence')
            reasoning = result.get('reasoning')
            
            if not all([signal, confidence, reasoning]):
                raise ValueError(f"Missing required fields in result: {result}")
                
            # Create a logger instance
            logger = cls()
            
            # Log the decision
            return logger.log_decision(
                agent_name=agent_name,
                signal=signal,
                confidence=confidence,
                reason=reasoning,
                symbol=symbol,
                price=price,
                additional_data=result.get('data')
            )
            
        except Exception as e:
            logging.error(f"Error creating summary: {str(e)}")
            return None