"""
Conflict Logger Module

This module provides logging utilities specifically for tracking and analyzing
conflicted decisions in the trading system. It writes structured logs of all
conflicted signals to support analysis, backtesting, and improvement of
conflict resolution logic.
"""

import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback

# Set up module-level logger
logger = logging.getLogger(__name__)

class ConflictLogger:
    """
    Logger for conflicted trading decisions that writes to a structured JSONL file.
    
    This class safely logs all CONFLICTED trading decisions in a standardized
    format for later analysis, backtesting, and improvement of conflict resolution logic.
    """
    
    def __init__(self, log_dir: str = "logs", log_file: str = "conflicted_decisions.jsonl"):
        """
        Initialize the conflict logger.
        
        Args:
            log_dir: Directory to store logs (default: "logs")
            log_file: Filename for the log file (default: "conflicted_decisions.jsonl")
        """
        self.log_dir = log_dir
        self.log_file = log_file
        self.log_path = os.path.join(log_dir, log_file)
        self.lock = threading.Lock()
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        logger.info(f"ConflictLogger initialized with log path: {self.log_path}")

    def log(self, 
           symbol: str, 
           interval: str,
           final_signal: str,
           confidence: float,
           reasoning: str,
           agent_scores: Dict[str, Dict[str, Any]],
           metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a conflicted decision asynchronously.
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            interval: Time interval (e.g., "1h")
            final_signal: The final trading signal (usually "CONFLICTED")
            confidence: Confidence score (0-100)
            reasoning: Explanation for the conflicted decision
            agent_scores: Dictionary of agent contributions with signals, confidences, and weights
            metadata: Optional additional information about the decision
        
        Note:
            This method is non-blocking and gracefully handles I/O errors.
        """
        # Spawn a thread to handle logging asynchronously
        threading.Thread(
            target=self._log_thread,
            args=(symbol, interval, final_signal, confidence, reasoning, agent_scores, metadata),
            daemon=True
        ).start()
    
    def _log_thread(self,
                   symbol: str, 
                   interval: str,
                   final_signal: str,
                   confidence: float,
                   reasoning: str,
                   agent_scores: Dict[str, Dict[str, Any]],
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Thread worker that safely writes the log entry to disk.
        
        Args:
            Same as log() method
        """
        try:
            # Create log entry
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "interval": interval,
                "final_signal": final_signal,
                "confidence": confidence,
                "reasoning": reasoning,
                "agent_scores": agent_scores
            }
            
            # Add optional metadata if provided
            if metadata:
                entry["metadata"] = metadata
                
            # Generate a unique ID for the entry
            entry_id = f"{symbol.replace('/', '')}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            entry["id"] = entry_id
            
            # Write to log file with lock to prevent concurrent writes
            with self.lock:
                with open(self.log_path, 'a') as f:
                    f.write(json.dumps(entry) + '\n')
                    
            logger.debug(f"Logged conflicted decision: {entry_id}")
            
        except Exception as e:
            logger.error(f"Error logging conflicted decision: {str(e)}")
            logger.debug(traceback.format_exc())
    
    def get_recent_conflicts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent conflicted decisions from the log.
        
        Args:
            limit: Maximum number of entries to return (default: 10)
            
        Returns:
            List of the most recent log entries as dictionaries
        """
        try:
            if not os.path.exists(self.log_path):
                return []
                
            with self.lock:
                with open(self.log_path, 'r') as f:
                    # Read all lines and parse JSON
                    entries = [json.loads(line) for line in f]
                    
                # Sort by timestamp descending and limit results
                entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                return entries[:limit]
                
        except Exception as e:
            logger.error(f"Error retrieving recent conflicts: {str(e)}")
            logger.debug(traceback.format_exc())
            return []
    
    def get_conflicts_by_symbol(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve conflicted decisions for a specific symbol.
        
        Args:
            symbol: Trading symbol to filter by (e.g., "BTC/USDT")
            limit: Maximum number of entries to return (default: 100)
            
        Returns:
            List of conflict log entries for the specified symbol
        """
        try:
            if not os.path.exists(self.log_path):
                return []
                
            with self.lock:
                with open(self.log_path, 'r') as f:
                    # Read all lines and parse JSON, filtering by symbol
                    entries = [json.loads(line) for line in f 
                              if json.loads(line).get('symbol') == symbol]
                    
                # Sort by timestamp descending and limit results
                entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                return entries[:limit]
                
        except Exception as e:
            logger.error(f"Error retrieving conflicts by symbol: {str(e)}")
            logger.debug(traceback.format_exc())
            return []


# Singleton instance for application-wide use
_instance = None

def get_logger(log_dir: str = "logs", log_file: str = "conflicted_decisions.jsonl") -> ConflictLogger:
    """
    Get or create the ConflictLogger singleton instance.
    
    Args:
        log_dir: Directory to store logs (default: "logs")
        log_file: Filename for the log file (default: "conflicted_decisions.jsonl")
        
    Returns:
        ConflictLogger instance
    """
    global _instance
    if _instance is None:
        _instance = ConflictLogger(log_dir, log_file)
    return _instance


def log_conflict(
    symbol: str, 
    interval: str,
    final_signal: str,
    confidence: float,
    reasoning: str,
    agent_scores: Dict[str, Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Convenience function to log a conflicted decision.
    
    Args:
        symbol: Trading symbol (e.g., "BTC/USDT")
        interval: Time interval (e.g., "1h")
        final_signal: The final trading signal (usually "CONFLICTED")
        confidence: Confidence score (0-100)
        reasoning: Explanation for the conflicted decision
        agent_scores: Dictionary of agent contributions with signals, confidences, and weights
        metadata: Optional additional information about the decision
    """
    logger_instance = get_logger()
    logger_instance.log(
        symbol, interval, final_signal, confidence, reasoning, agent_scores, metadata
    )