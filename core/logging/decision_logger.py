"""
aGENtrader v2 Decision Logger

This module provides decision logging functionality to create human-readable summaries
of agent decisions for monitoring and potential model training.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Set up logger
logger = logging.getLogger("decision_logger")

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
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Set up file logging
        self.logger = logging.getLogger("decision_logger")
        self.logger.setLevel(logging.INFO)
        
        # Initialize
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
            # Format timestamp
            if not timestamp:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                
            # Format symbol
            symbol_str = f"{symbol} @ {price:.2f}" if symbol and price else symbol or "Unknown"
            
            # Format interval
            interval_str = f" ({interval})" if interval else ""
            
            # Format reason (limit to one sentence)
            short_reason = self._limit_to_one_sentence(reason)
            
            # Create summary line
            summary = f"[{timestamp}] {agent_name}: {signal} ({confidence}%) - {short_reason} - {symbol_str}{interval_str}"
            
            # Log to file
            with open(self.log_path, "a") as f:
                f.write(summary + "\n")
                
            # Also log to console
            self.logger.info(summary)
            
            # Log additional data as JSON if provided
            if additional_data:
                try:
                    data_path = f"{os.path.splitext(self.log_path)[0]}_data.jsonl"
                    with open(data_path, "a") as f:
                        entry = {
                            "timestamp": timestamp,
                            "agent": agent_name,
                            "signal": signal,
                            "confidence": confidence,
                            "symbol": symbol,
                            "price": price,
                            "interval": interval,
                            "data": additional_data
                        }
                        f.write(json.dumps(entry) + "\n")
                except Exception as e:
                    self.logger.warning(f"Failed to log additional data: {str(e)}")
                    
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to log decision: {str(e)}")
            return None
            
    def _limit_to_one_sentence(self, text: str) -> str:
        """
        Limit the text to one sentence.
        
        Args:
            text: The text to limit
            
        Returns:
            The first sentence from the text
        """
        if not text:
            return "No reason provided"
            
        # Simple sentence splitting (looking for first ., ! or ?)
        end_markers = ['. ', '! ', '? ']
        for marker in end_markers:
            if marker in text:
                return text.split(marker)[0] + marker.rstrip()
                
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
            if not result:
                return None
                
            signal = result.get('signal', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            reason = result.get('reason', result.get('reasoning', 'No reason provided'))
            
            # Format symbol
            symbol_str = f"{symbol} @ {price:.2f}" if symbol and price else symbol or "Unknown"
            
            # Format reason (limit to one sentence)
            # Using a simple method for class method without instance
            short_reason = cls._limit_text_to_one_sentence(reason)
            
            # Create summary line
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            summary = f"[{timestamp}] {agent_name}: {signal} ({confidence}%) - {short_reason} - {symbol_str}"
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to create summary: {str(e)}")
            return None
            
    @classmethod
    def _limit_text_to_one_sentence(cls, text: str) -> str:
        """
        Static helper method to limit text to one sentence.
        
        Args:
            text: The text to limit
            
        Returns:
            The first sentence from the text
        """
        if not text:
            return "No reason provided"
            
        # Simple sentence splitting (looking for first ., ! or ?)
        end_markers = ['. ', '! ', '? ']
        for marker in end_markers:
            if marker in text:
                return text.split(marker)[0] + marker.rstrip()
                
        # If no sentence ending found, return as is
        return text

# Global instance
decision_logger = DecisionLogger()