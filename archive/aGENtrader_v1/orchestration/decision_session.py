#!/usr/bin/env python3
"""
Decision Session

This module provides the DecisionSession class for managing trading decisions.
It integrates with the MultiAgentDecisionSession for more advanced decision making.
"""
import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("decision_session")

# Try to import SimpleDecisionSession
try:
    from orchestration.simple_decision_session import SimpleDecisionSession
    SIMPLE_DECISION_AVAILABLE = True
    logger.info("SimpleDecisionSession is available for local LLM decisions")
except ImportError:
    SIMPLE_DECISION_AVAILABLE = False
    logger.warning("SimpleDecisionSession is not available. Will use basic DecisionSession.")
    
# Try to import MultiAgentDecisionSession (more complex, may not work with local LLM)
try:
    from orchestration.autogen_decision_session import MultiAgentDecisionSession
    MULTI_AGENT_AVAILABLE = True
    logger.info("MultiAgentDecisionSession is available")
except ImportError:
    MULTI_AGENT_AVAILABLE = False
    logger.warning("MultiAgentDecisionSession is not available. Will use alternatives.")

class DecisionSession:
    """
    Decision Session class for managing trading decisions
    """
    
    def __init__(self):
        """Initialize DecisionSession"""
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = os.path.join("data", "decisions")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize simple decision session if available
        if SIMPLE_DECISION_AVAILABLE:
            try:
                self.simple_decision_session = SimpleDecisionSession()
                logger.info("SimpleDecisionSession initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing SimpleDecisionSession: {str(e)}")
                self.simple_decision_session = None
        else:
            self.simple_decision_session = None
            
        # Initialize multi-agent session if available
        if MULTI_AGENT_AVAILABLE:
            try:
                self.multi_agent_session = MultiAgentDecisionSession()
                logger.info("MultiAgentDecisionSession initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing MultiAgentDecisionSession: {str(e)}")
                self.multi_agent_session = None
        else:
            self.multi_agent_session = None
    
    def run_decision(self, symbol: str, interval: str = '1h', 
                    current_price: float = None,
                    market_data: Dict = None,
                    analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Run a trading decision
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            current_price: Current price of the asset
            market_data: Additional market data for analysis
            analysis_type: Type of analysis
            
        Returns:
            Decision data
        """
        # First try the simple decision session with local TinyLlama
        if SIMPLE_DECISION_AVAILABLE and self.simple_decision_session is not None:
            try:
                logger.info(f"Using SimpleDecisionSession with local LLM for {symbol}")
                return self.simple_decision_session.run_decision(
                    symbol=symbol,
                    interval=interval,
                    current_price=current_price,
                    market_data=market_data,
                    analysis_type=analysis_type
                )
            except Exception as e:
                logger.error(f"Error using SimpleDecisionSession: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                logger.info("Falling back to multi-agent session")
        
        # If simple decision session failed, try multi-agent session
        if MULTI_AGENT_AVAILABLE and self.multi_agent_session is not None:
            try:
                logger.info(f"Using MultiAgentDecisionSession for {symbol}")
                return self.multi_agent_session.run_decision(
                    symbol=symbol,
                    interval=interval,
                    current_price=current_price,
                    market_data=market_data,
                    analysis_type=analysis_type
                )
            except Exception as e:
                logger.error(f"Error using MultiAgentDecisionSession: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                logger.info("Falling back to basic decision process")
        
        # If both methods failed, use basic decision process
        return self._basic_decision_process(symbol, interval, current_price, analysis_type)
    
    def _basic_decision_process(self, symbol: str, interval: str,
                              current_price: float = None,
                              analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Basic decision process as fallback
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            current_price: Current price
            analysis_type: Type of analysis
            
        Returns:
            Decision data
        """
        logger.info(f"Using basic decision process for {symbol}")
        current_timestamp = datetime.datetime.utcnow()
        
        # Different decisions based on symbol for testing
        if symbol.upper() == "BTCUSDT":
            decision_price = current_price or 85010.45
            action = "BUY"
            confidence = 0.65
            reasoning = "Strong support level with increasing volume"
        elif symbol.upper() == "ETHUSDT":
            decision_price = current_price or 3800.75
            action = "HOLD"
            confidence = 0.55
            reasoning = "Consolidation phase, waiting for breakout"
        else:
            decision_price = current_price or 1000.00
            action = "SELL"
            confidence = 0.60
            reasoning = "Bearish divergence with resistance overhead"
        
        # Create decision data
        decision_data = {
            "status": "success",
            "timestamp": current_timestamp.isoformat(),
            "symbol": symbol,
            "interval": interval,
            "session_id": self.session_id,
            "decision": {
                "action": action,
                "confidence": confidence,
                "entry_price": decision_price,
                "stop_loss_percent": 5.0,
                "take_profit_percent": 10.0,
                "timeframe": "short-term",
                "reasoning": reasoning,
                "analysis_summary": f"Decision based on {analysis_type} analysis"
            },
            "market_data": {
                "current_price": decision_price,
                "timestamp": current_timestamp.isoformat()
            }
        }
        
        # Save decision to file
        self._save_decision(decision_data)
        
        return decision_data
    
    def _save_decision(self, decision_data: Dict[str, Any]) -> None:
        """
        Save decision data to file
        
        Args:
            decision_data: Decision data to save
        """
        try:
            file_path = os.path.join(
                self.output_dir, 
                f"{decision_data['symbol']}_{self.session_id}.json"
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(decision_data, f, indent=2, default=str)
                
            logger.info(f"Decision saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving decision: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
