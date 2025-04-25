"""
Decision Session Module

This module provides the DecisionSession class which orchestrates the multi-agent
decision process, including the new Global Market Analyst agent.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Import agents
from agents.global_market_analyst import GlobalMarketAnalyst
from agents.global_market_data import get_macro_market_summary

# Configure logging
logger = logging.getLogger(__name__)

class DecisionSession:
    """
    Orchestrates the multi-agent decision process for trading.
    Now includes the Global Market Analyst agent for macro analysis.
    """
    
    def __init__(self, symbol: str, track_performance: bool = False, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a decision session.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            track_performance: Whether to track decision performance
            config: Optional configuration dictionary
        """
        self.session_id = str(uuid.uuid4())
        self.symbol = symbol
        self.track_performance = track_performance
        self.config = config or {}
        self.timestamp = datetime.now()
        
        # Initialize logger
        self.setup_logging()
        
        # Initialize decision tracker if tracking is enabled
        if self.track_performance:
            try:
                from utils.decision_tracker import DecisionTracker
                self.decision_tracker = DecisionTracker()
                logger.info(f"Decision tracking enabled for session {self.session_id}")
            except ImportError:
                logger.warning("Decision tracker not available. Performance will not be tracked.")
                self.track_performance = False
        
        # Get current price for the symbol
        self.current_price = self._get_current_price()
        logger.info(f"Initialized decision session for {symbol} at price {self.current_price}")
    
    def setup_logging(self):
        """Setup session-specific logging"""
        # This would configure logging for the session
        pass
    
    def _get_current_price(self) -> Optional[float]:
        """Get current price for the symbol"""
        try:
            # This would call a function to get the latest price
            # For now, just return a placeholder
            return 0.0
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    def _gather_market_data(self) -> Dict[str, Any]:
        """
        Gather market data for the decision process.
        Now includes global market data.
        
        Returns:
            Dictionary containing market data
        """
        try:
            # Get global market data first
            global_data = get_macro_market_summary()
            
            # Then get symbol-specific data
            # This would include calls to get:
            # - Latest price
            # - Recent market data
            # - Technical indicators
            # - Market summary
            # For now, just return placeholder
            
            symbol_data = {
                "symbol": self.symbol,
                "current_price": self.current_price,
                "timestamp": datetime.now().isoformat()
            }
            
            # Combine the data
            market_data = {
                "global_market_data": global_data,
                "symbol_data": symbol_data
            }
            
            return market_data
        
        except Exception as e:
            logger.error(f"Error gathering market data: {e}")
            return {
                "error": "Failed to gather market data",
                "symbol": self.symbol,
                "timestamp": datetime.now().isoformat()
            }
    
    def _format_market_summary(self, market_data: Dict[str, Any]) -> str:
        """
        Format market data into a summary for the initial agent message.
        Now includes global market context.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Formatted market summary string
        """
        try:
            # Format global market data
            global_data = market_data.get("global_market_data", {})
            global_summary = []
            
            if "global_indicators" in global_data:
                indicators = global_data["global_indicators"]
                global_summary.append(f"DXY (US Dollar Index): {indicators.get('dxy', {}).get('latest')} - Trend: {indicators.get('dxy', {}).get('trend', 'unknown')}")
                global_summary.append(f"SPX (S&P 500): {indicators.get('spx', {}).get('latest')} - Trend: {indicators.get('spx', {}).get('trend', 'unknown')}")
                global_summary.append(f"VIX (Volatility Index): {indicators.get('vix', {}).get('latest')} - Trend: {indicators.get('vix', {}).get('trend', 'unknown')}")
            
            if "crypto_metrics" in global_data:
                metrics = global_data["crypto_metrics"]
                global_summary.append(f"Total Crypto Market Cap: ${metrics.get('total_market_cap', {}).get('latest')} - Trend: {metrics.get('total_market_cap', {}).get('trend', 'unknown')}")
                global_summary.append(f"Altcoin Market Cap (Total1): ${metrics.get('total1', {}).get('latest')} - Trend: {metrics.get('total1', {}).get('trend', 'unknown')}")
            
            if "dominance" in global_data:
                dominance = global_data["dominance"]
                global_summary.append(f"BTC Dominance: {dominance.get('btc', {}).get('latest')}% - Trend: {dominance.get('btc', {}).get('trend', 'unknown')}")
                global_summary.append(f"ETH Dominance: {dominance.get('eth', {}).get('latest')}% - Trend: {dominance.get('eth', {}).get('trend', 'unknown')}")
            
            if "correlations" in global_data:
                correlations = global_data["correlations"]
                global_summary.append(f"BTC-DXY Correlation: {correlations.get('btc_dxy')}")
                global_summary.append(f"BTC-SPX Correlation: {correlations.get('btc_spx')}")
            
            if "market_state" in global_data:
                global_summary.append(f"Market State: {global_data['market_state']}")
            
            # Format symbol-specific data
            symbol_data = market_data.get("symbol_data", {})
            symbol_summary = [
                f"Symbol: {self.symbol}",
                f"Current Price: ${symbol_data.get('current_price')}"
            ]
            
            # Combine the summaries
            summary = [
                "=== GLOBAL MARKET CONTEXT ===",
                "\n".join(global_summary),
                "",
                "=== SYMBOL SPECIFIC DATA ===",
                "\n".join(symbol_summary)
            ]
            
            return "\n".join(summary)
        
        except Exception as e:
            logger.error(f"Error formatting market summary: {e}")
            return f"Error formatting market data. Symbol: {self.symbol}, Price: {self.current_price}"
    
    def _check_autogen_available(self) -> bool:
        """Check if the AutoGen framework is available"""
        try:
            import autogen
            return True
        except ImportError:
            logger.warning("AutoGen not available. Using simulated decision process.")
            return False
    
    def _run_simulated_session(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a simulated decision session without AutoGen.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Decision dictionary
        """
        # This would be a simplified rule-based decision process
        # For now, just return a placeholder decision
        decision = {
            "symbol": self.symbol,
            "action": "HOLD",
            "confidence": 50.0,
            "price": self.current_price,
            "risk_level": "medium",
            "reasoning": "Simulated decision process",
            "timestamp": datetime.now().isoformat(),
            "is_simulated": True
        }
        
        return decision
    
    def _run_agent_session(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a multi-agent decision session using AutoGen.
        Now includes the Global Market Analyst agent.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Decision dictionary
        """
        try:
            import autogen
            from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager
            
            # Setup AutoGen configuration
            llm_config = {
                "temperature": 0.2,
                "model": "gpt-4-turbo"
            }
            
            # Create the Global Market Analyst agent
            global_analyst = GlobalMarketAnalyst()
            global_analyst_def = global_analyst.get_agent_definition()
            global_analyst_functions = global_analyst.register_functions()
            
            # Enhance the LLM config with database function specifications
            llm_config_with_db = llm_config.copy()
            llm_config_with_db["tools"] = global_analyst_functions["function_specs"]
            
            # Create the agents
            # Note: This is a simplified version. In reality, you would create all your specialized agents.
            global_market_analyst_agent = ConversableAgent(
                name=global_analyst_def["name"],
                system_message=global_analyst_def["system_message"],
                llm_config=llm_config_with_db,
                function_map=global_analyst_functions["function_map"]
            )
            
            # Create other agents (simplified for this example)
            market_analyst_agent = ConversableAgent(
                name="MarketAnalyst",
                system_message="You are a cryptocurrency market analyst specializing in technical analysis.",
                llm_config=llm_config
            )
            
            risk_manager_agent = ConversableAgent(
                name="RiskManager",
                system_message="You are a risk management expert specializing in cryptocurrency trading.",
                llm_config=llm_config
            )
            
            trading_decision_agent = ConversableAgent(
                name="TradingAdvisor",
                system_message="You are a trading advisor who synthesizes information to make final recommendations.",
                llm_config=llm_config
            )
            
            # Create user proxy to act as moderator
            user_proxy = UserProxyAgent(
                name="Moderator",
                system_message="You are moderating a discussion between experts to make a trading decision.",
                human_input_mode="NEVER",
                llm_config=llm_config,
                code_execution_config=False
            )
            
            # Prepare market summary for initial message
            market_summary = self._format_market_summary(market_data)
            
            # Create group chat with all agents, putting GlobalMarketAnalyst first
            groupchat = GroupChat(
                agents=[global_market_analyst_agent, market_analyst_agent, risk_manager_agent, trading_decision_agent, user_proxy],
                messages=[],
                max_round=15
            )
            
            # Create manager
            manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
            
            # Start the conversation with market data
            initial_message = f"""
We need to make a trading decision for {self.symbol} based on current market data.

Here is the current market data:

{market_summary}

Global Market Analyst, please begin by providing your macro analysis of current market conditions and how they might impact {self.symbol}.
Then MarketAnalyst, please provide your technical analysis.
RiskManager, please assess risk levels.
Finally, TradingAdvisor, please synthesize the information and recommend a trading action (BUY, SELL, or HOLD) with a confidence level (0-100).
"""
            
            # Start the chat
            user_proxy.initiate_chat(manager, message=initial_message)
            
            # Extract the decision from the chat
            decision = self._extract_decision(groupchat.messages, self.symbol)
            
            return decision
        
        except Exception as e:
            logger.error(f"Error running agent session: {e}")
            return {
                "symbol": self.symbol,
                "action": "HOLD",
                "confidence": 0.0,
                "price": self.current_price,
                "risk_level": "high",
                "reasoning": f"Error in agent session: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "error": True
            }
    
    def _extract_decision(self, messages: List[Dict[str, Any]], symbol: str) -> Dict[str, Any]:
        """
        Extract trading decision from agent messages.
        
        Args:
            messages: List of messages from the agent chat
            symbol: Trading symbol
            
        Returns:
            Decision dictionary
        """
        # This would parse the messages to extract the decision
        # For now, just return a placeholder decision
        decision = {
            "symbol": symbol,
            "action": "HOLD",
            "confidence": 50.0,
            "price": self.current_price,
            "risk_level": "medium",
            "reasoning": "Placeholder reasoning",
            "timestamp": datetime.now().isoformat()
        }
        
        return decision
    
    def run_session(self) -> Dict[str, Any]:
        """
        Run the decision session.
        
        Returns:
            Decision dictionary
        """
        # Check if symbol and price are available
        if not self.symbol or not self.current_price:
            logger.error("Symbol or price not available")
            return {
                "error": "Symbol or price not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Gather market data
        market_data = self._gather_market_data()
        if "error" in market_data:
            logger.error(f"Error gathering market data: {market_data['error']}")
            return {
                "error": market_data["error"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if AutoGen is available
        if self._check_autogen_available():
            # Run agent-based session
            decision = self._run_agent_session(market_data)
        else:
            # Run simulated session
            decision = self._run_simulated_session(market_data)
        
        # Track decision if enabled
        if self.track_performance and hasattr(self, "decision_tracker"):
            try:
                # Record the decision in the tracker
                self.decision_tracker.track_session_decision(
                    session_id=self.session_id,
                    decision=decision,
                    market_data=market_data
                )
                logger.info(f"Decision tracked for session {self.session_id}")
            except Exception as e:
                logger.error(f"Error tracking decision: {e}")
        
        return decision