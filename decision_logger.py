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
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('decision_logger')

class DecisionLogger:
    """
    Decision logger that creates human-readable summaries of agent decisions.
    
    This class handles logging of agent decisions in a standardized format.
    """
    
    def __init__(self, log_path: str = 'logs/decision_summary.logl'):
        """
        Initialize the decision logger.
        
        Args:
            log_path: Path to the log file
        """
        self.log_path = log_path
        
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
        logger.info(f"Decision logger initialized with log path: {self.log_path}")
    
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
        """
        try:
            # Get current UTC timestamp if not provided
            if timestamp is None:
                timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Limit reason to one sentence
            reason = self._limit_to_one_sentence(reason)
            
            # Format the log entry
            log_entry = f"[{timestamp}] {agent_name}"
            
            # Add timeframe if available
            if interval:
                log_entry += f" ({interval})"
                
            log_entry += f": {signal}"
            
            # Add symbol and price if available
            if symbol and price:
                log_entry += f" {symbol} @ ${price:,.2f}"
            elif symbol:
                log_entry += f" {symbol}"
            
            # Add confidence
            log_entry += f" | Confidence: {confidence}%"
            
            # Add reason
            log_entry += f" | Reason: {reason}"
            
            # Write to log file
            with open(self.log_path, 'a') as f:
                f.write(log_entry + "\n")
            
            # If additional data is provided, store it as JSON
            if additional_data:
                json_log_path = self.log_path + ".json"
                entry = {
                    "timestamp": timestamp,
                    "agent_name": agent_name,
                    "signal": signal,
                    "confidence": confidence,
                    "reason": reason,
                    "symbol": symbol,
                    "price": price,
                    "data": additional_data
                }
                
                with open(json_log_path, 'a') as f:
                    f.write(json.dumps(entry) + "\n")
            
            logger.debug(f"Decision logged: {log_entry}")
            
            return log_entry
            
        except Exception as e:
            logger.error(f"Error logging decision: {str(e)}", exc_info=True)
    
    def _limit_to_one_sentence(self, text: str) -> str:
        """
        Limit the text to one sentence.
        
        Args:
            text: The text to limit
            
        Returns:
            The first sentence from the text
        """
        # Define sentence endings
        sentence_endings = ['.', '!', '?']
        
        # Check each sentence ending
        for ending in sentence_endings:
            end_pos = text.find(ending)
            if end_pos != -1:
                # Include the ending punctuation
                return text[:end_pos + 1]
        
        # If no sentence endings found, return the original text
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
            # Extract common fields
            signal = result.get('signal', 'UNKNOWN')
            confidence = result.get('confidence', 0)
            timestamp = result.get('timestamp', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
            
            # Extract reason based on result format
            reason = None
            if 'explanation' in result and isinstance(result['explanation'], list):
                # Join explanations for technical analysis
                reason = '; '.join(result['explanation'][:1])  # Take just the first explanation
            elif 'explanation' in result:
                reason = result['explanation']
            elif 'analysis_summary' in result:
                # For sentiment analysis
                reason = result['analysis_summary']
            elif 'summary' in result:
                reason = result['summary']
            elif 'message' in result:
                reason = result['message']
            else:
                reason = f"{signal} signal generated"
            
            # Get symbol from result if not provided
            if symbol is None and 'symbol' in result:
                symbol = result['symbol']
            
            # Get price from result if not provided
            if price is None and 'current_price' in result:
                price = result['current_price']
            
            # Create logger instance
            logger = cls()
            
            # Get interval from result if available
            interval = result.get('interval')
            
            # Log the decision
            return logger.log_decision(
                agent_name=agent_name,
                signal=signal,
                confidence=confidence,
                reason=reason,
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                additional_data=result,
                interval=interval
            )
            
        except Exception as e:
            logging.error(f"Error creating summary from result: {str(e)}", exc_info=True)
            return None


# Create a singleton instance for use throughout the application
decision_logger = DecisionLogger()

# Example usage:
if __name__ == "__main__":
    # Example of direct logging
    decision_logger.log_decision(
        agent_name="TechnicalAnalystAgent",
        signal="BUY",
        confidence=82,
        reason="20EMA crossed above 50EMA with rising RSI and increasing volume",
        symbol="BTC/USDT",
        price=87240.50
    )
    
    # Example of creating summary from a result dictionary
    result = {
        "agent": "SentimentAggregatorAgent",
        "timestamp": "2025-04-22T08:30:15Z",
        "symbol": "ETH/USDT",
        "sentiment_score": 4,
        "confidence": 75,
        "analysis_summary": "Positive sentiment from institutional investors due to upcoming network upgrade.",
        "sentiment_signals": ["High social media engagement", "Positive news coverage", "Institutional buying"]
    }
    
    DecisionLogger.create_summary_from_result(
        agent_name="SentimentAggregatorAgent",
        result=result
    )