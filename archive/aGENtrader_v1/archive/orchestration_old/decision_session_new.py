"""
Decision Session Module

Manages structured agent decision-making sessions for trading, providing a framework
for consistent, logged, and audit-friendly trading decisions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# Import test logging utilities
from utils.test_logging import TestLogger, CustomJSONEncoder

# Import performance tracking utilities
from utils.decision_tracker import DecisionTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("decision_session")

class DecisionSession:
    """
    Decision Session Manager for trading agent interactions.
    
    Coordinates and manages structured decision-making sessions between multiple
    specialized agents to produce consistent, well-formatted trading decisions.
    """
    
    def __init__(self, config_path: str = "config/decision_session.json", 
                 symbol: Optional[str] = None, 
                 session_id: Optional[str] = None,
                 track_performance: bool = True):
        """
        Initialize the decision session manager.
        
        Args:
            config_path: Path to configuration file
            symbol: Trading symbol to analyze (e.g., "BTCUSDT")
            session_id: Custom session identifier (generated if not provided)
            track_performance: Whether to track decision performance
        """
        self.session_id = session_id if session_id else f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.timestamp = datetime.now().isoformat()
        self.config = self._load_config(config_path)
        self.logger = TestLogger(log_dir=self.config.get("log_dir", "data/logs/decisions"))
        self.symbol = symbol
        self.track_performance = track_performance
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config.get("output_dir", "data/decisions"), exist_ok=True)
        
        # Initialize decision performance tracker if enabled
        self.decision_tracker = None
        if self.track_performance:
            try:
                self.decision_tracker = DecisionTracker(
                    performance_dir=self.config.get("performance_dir", "data/performance")
                )
                logger.info("Decision performance tracking enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize decision tracker: {str(e)}")
                self.track_performance = False
        
        # Get current price if symbol is provided
        self.current_price = None
        if self.symbol:
            try:
                from agents.database_retrieval_tool import get_latest_price
                import json
                
                price_data_json = get_latest_price(self.symbol)
                if price_data_json:
                    price_data = json.loads(price_data_json)
                    self.current_price = price_data["close"]
                    logger.info(f"Current price for {self.symbol}: ${self.current_price}")
            except Exception as e:
                logger.warning(f"Could not get current price for {self.symbol}: {str(e)}")
        
        logger.info(f"Decision session {self.session_id} initialized{' for '+self.symbol if self.symbol else ''}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary containing configuration
        """
        try:
            if not os.path.exists(config_path):
                logger.warning(f"Config file {config_path} not found, using default configuration")
                return self._default_config()
            
            with open(config_path, "r") as f:
                config = json.load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            logger.info("Using default configuration")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Create default configuration if config file is missing or invalid.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "log_dir": "data/logs/decisions",
            "output_dir": "data/decisions",
            "agent_config": {
                "analyst": {
                    "name": "MarketAnalyst",
                    "description": "Expert in technical analysis of cryptocurrency markets"
                },
                "risk_manager": {
                    "name": "RiskManager",
                    "description": "Expert in assessing market risks and position sizing"
                },
                "strategist": {
                    "name": "TradingStrategist",
                    "description": "Expert in developing and evaluating trading strategies"
                },
                "advisor": {
                    "name": "TradingAdvisor",
                    "description": "Expert in synthesizing analysis and making final recommendations"
                }
            },
            "decision_format": {
                "symbol": "",
                "action": "HOLD",
                "confidence": 0.0,
                "price": 0.0,
                "risk_level": "medium",
                "reasoning": "",
                "timestamp": ""
            },
            "max_turns": 10,
            "system_prompts": {
                "coordinator": """You are coordinating a decision-making session between specialized trading agents.
Your job is to guide the conversation to reach a clear trading decision.
Keep the discussion focused and make sure each agent contributes their expertise.
Summarize key points and highlight areas of agreement or disagreement."""
            }
        }
    
    def run_session(self, symbol: Optional[str] = None, current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Run a full decision-making session.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT"), if not provided uses self.symbol
            current_price: Current price of the asset, if not provided uses self.current_price
            
        Returns:
            Decision data dictionary
        """
        # Use instance variables if parameters not provided
        symbol = symbol or self.symbol
        current_price = current_price or self.current_price
        
        # Make sure we have required values
        if not symbol:
            error_msg = "No trading symbol provided to decision session"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}
            
        if not current_price:
            # Try to get current price if not provided
            try:
                from agents.database_retrieval_tool import get_latest_price
                import json
                
                price_data_json = get_latest_price(symbol)
                if price_data_json:
                    price_data = json.loads(price_data_json)
                    current_price = price_data["close"]
                    logger.info(f"Retrieved current price for {symbol}: ${current_price}")
                else:
                    error_msg = f"Could not retrieve current price for {symbol}"
                    logger.error(error_msg)
                    return {"status": "error", "error": error_msg}
            except Exception as e:
                error_msg = f"Error retrieving current price: {str(e)}"
                logger.error(error_msg)
                return {"status": "error", "error": error_msg}
        
        # Log session start
        logger.info(f"Starting decision session for {symbol} at ${current_price}")
        
        try:
            # Get market data for analysis
            market_data = self._gather_market_data(symbol)
            if not market_data:
                logger.error(f"Failed to gather market data for {symbol}")
                return {
                    "session_id": self.session_id,
                    "status": "error",
                    "error": "Failed to gather market data"
                }
            
            # Prepare session data
            session_data = {
                "session_id": self.session_id,
                "symbol": symbol,
                "current_price": current_price,
                "timestamp": self.timestamp,
                "market_data": market_data
            }
            
            # Log session data
            self.logger.log_session_start("decision", session_data)
            
            # Check if AutoGen is available
            if not self._check_autogen_available():
                logger.warning("AutoGen not available, running simulated session")
                return self._run_simulated_session(session_data)
            
            # Run real agent-based session with AutoGen
            decision = self._run_agent_session(session_data)
            
            # Log session end
            self.logger.log_session_end("decision", {
                "session_id": self.session_id,
                "status": "completed",
                "decision": decision
            })
            
            # Track decision performance if enabled
            if self.track_performance and self.decision_tracker:
                try:
                    # Create complete session data for tracking
                    complete_session_data = {
                        "session_id": self.session_id,
                        "status": "completed",
                        "symbol": symbol,
                        "current_price": current_price,
                        "timestamp": self.timestamp,
                        "decision": decision,
                        "market_data": session_data.get("market_data", {}),
                        "technical_indicators": session_data.get("market_data", {}).get("technical_indicators", {})
                    }
                    
                    # Track the decision
                    decision_id = self.decision_tracker.track_session_decision(complete_session_data)
                    logger.info(f"Decision tracked with ID: {decision_id}")
                except Exception as e:
                    logger.warning(f"Failed to track decision performance: {str(e)}")
            
            return {
                "session_id": self.session_id,
                "status": "completed",
                "symbol": symbol,
                "current_price": current_price,
                "timestamp": self.timestamp,
                "decision": decision
            }
            
        except Exception as e:
            logger.error(f"Error in decision session: {str(e)}")
            
            # Log session error
            self.logger.log_session_end("decision", {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            })
            
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }
    
    def _gather_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Gather relevant market data for the decision session.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary of market data or None if error
        """
        try:
            from agents.database_retrieval_tool import (
                get_latest_price,
                get_recent_market_data,
                calculate_moving_average,
                calculate_rsi,
                get_market_summary,
                find_support_resistance,
                detect_patterns,
                calculate_volatility
            )
            
            # Try to import global market data functions
            try:
                from agents.global_market_analyst import GlobalMarketAnalyst
                has_global_analyst = True
            except ImportError:
                logger.warning("GlobalMarketAnalyst not available")
                has_global_analyst = False
                
            # Try to import liquidity data functions
            try:
                from agents.liquidity_analyst import get_liquidity_analyst
                has_liquidity_analyst = True
            except ImportError:
                logger.warning("LiquidityAnalyst not available")
                has_liquidity_analyst = False
            
            # Parse JSON responses
            def parse_json(json_str):
                if not json_str:
                    return None
                try:
                    return json.loads(json_str)
                except:
                    return None
            
            # Get various market data points
            latest_price = parse_json(get_latest_price(symbol))
            market_summary = parse_json(get_market_summary(symbol))
            recent_data = parse_json(get_recent_market_data(symbol, 20))
            sma = parse_json(calculate_moving_average(symbol))
            rsi = parse_json(calculate_rsi(symbol))
            support_resistance = parse_json(find_support_resistance(symbol))
            patterns = parse_json(detect_patterns(symbol))
            volatility = parse_json(calculate_volatility(symbol))
            
            # Compile core data
            market_data = {
                "latest_price": latest_price,
                "market_summary": market_summary,
                "recent_data": recent_data,
                "technical_indicators": {
                    "sma": sma,
                    "rsi": rsi,
                    "support_resistance": support_resistance,
                    "patterns": patterns,
                    "volatility": volatility
                }
            }
            
            # Add global market data if available
            if has_global_analyst:
                try:
                    global_analyst = GlobalMarketAnalyst()
                    macro_summary = global_analyst.get_macro_market_summary()
                    market_data["global_market"] = {
                        "macro_summary": macro_summary,
                        "correlations": global_analyst.get_relevant_correlations(symbol),
                        "market_indices": global_analyst.get_market_indices(),
                        "crypto_metrics": global_analyst.get_crypto_market_metrics()
                    }
                    logger.info("Added global market data to analysis")
                except Exception as e:
                    logger.warning(f"Error adding global market data: {str(e)}")
            
            # Add liquidity data if available
            if has_liquidity_analyst:
                try:
                    liquidity_analyst = get_liquidity_analyst()
                    liquidity_summary = liquidity_analyst.get_liquidity_analysis(symbol)
                    
                    market_data["liquidity"] = {
                        "summary": liquidity_summary,
                        "exchange_flows": liquidity_analyst.analyze_exchange_flows(symbol),
                        "funding_rates": liquidity_analyst.analyze_funding_rates(symbol),
                        "market_depth": liquidity_analyst.analyze_market_depth(symbol),
                        "futures_basis": liquidity_analyst.analyze_futures_basis(symbol),
                        "volume_profile": liquidity_analyst.analyze_volume_profile(symbol)
                    }
                    logger.info("Added liquidity data to analysis")
                except Exception as e:
                    logger.warning(f"Error adding liquidity data: {str(e)}")
                
            return market_data
            
        except Exception as e:
            logger.error(f"Error gathering market data: {str(e)}")
            return None
    
    def _check_autogen_available(self) -> bool:
        """
        Check if AutoGen is available for agent-based session.
        
        Returns:
            True if AutoGen is available, False otherwise
        """
        try:
            import autogen
            return True
        except ImportError:
            logger.warning("AutoGen not available. Install with 'pip install pyautogen'")
            return False
    
    def _run_simulated_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a simulated decision session without AutoGen.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Decision data dictionary
        """
        symbol = session_data.get("symbol", "UNKNOWN")
        current_price = session_data.get("current_price", 0.0)
        
        logger.info(f"Running simulated decision session for {symbol}")
        
        # Extract market sentiment from available data
        market_data = session_data.get("market_data", {})
        rsi_data = market_data.get("technical_indicators", {}).get("rsi", {})
        sma_data = market_data.get("technical_indicators", {}).get("sma", {})
        
        # Default to HOLD with medium confidence
        action = "HOLD"
        confidence = 0.5
        
        # Basic decision logic based on technical indicators
        if rsi_data and "value" in rsi_data:
            rsi = rsi_data["value"]
            
            if rsi > 70:
                action = "SELL"
                confidence = min(0.6 + (rsi - 70) / 100, 0.9)
            elif rsi < 30:
                action = "BUY"
                confidence = min(0.6 + (30 - rsi) / 100, 0.9)
        
        # Use SMA crossovers if available
        if sma_data and "sma_20" in sma_data and "sma_50" in sma_data:
            sma_20 = sma_data["sma_20"]
            sma_50 = sma_data["sma_50"]
            
            if sma_20 > sma_50:
                # Golden cross - bullish
                if action != "SELL":  # Don't override strong SELL signals
                    action = "BUY"
                    confidence = max(confidence, 0.65)
            elif sma_20 < sma_50:
                # Death cross - bearish
                if action != "BUY":  # Don't override strong BUY signals
                    action = "SELL"
                    confidence = max(confidence, 0.65)
        
        # Create formatted decision object
        decision = {
            "symbol": symbol,
            "action": action,
            "confidence": round(confidence, 2),
            "price": current_price,
            "risk_level": "medium",
            "timestamp": datetime.now().isoformat(),
            "reasoning": f"Simulated decision based on RSI ({rsi_data.get('value', 'N/A')}) and SMA indicators. Note: This is a simulated decision without full agent analysis."
        }
        
        logger.info(f"Simulated decision: {action} {symbol} with {confidence:.2f} confidence")
        
        return decision
    
    def _run_agent_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a real decision session with AutoGen agents.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Decision data dictionary
        """
        try:
            import autogen
            from autogen import Agent, AssistantAgent, UserProxyAgent
            import random
            
            # Extract session parameters
            symbol = session_data.get("symbol", "UNKNOWN")
            current_price = session_data.get("current_price", 0.0)
            
            logger.info(f"Running agent-based decision session for {symbol}")
            
            # Prepare market data summary for initial message
            market_summary = self._format_market_summary(session_data.get("market_data", {}))
            
            # Configure the agents
            config_list = [
                {
                    "model": "gpt-4",
                }
            ]
            
            # Create the specialized agents
            market_analyst = AssistantAgent(
                name="MarketAnalyst",
                system_message="""You are an expert cryptocurrency market analyst specializing in technical analysis.
Analyze price patterns, indicators, and market structure.
Focus on identifying key support/resistance levels and trend direction.
Be specific about time frames in your analysis.""",
                llm_config={"config_list": config_list},
            )
            
            risk_manager = AssistantAgent(
                name="RiskManager",
                system_message="""You are an expert risk manager for cryptocurrency trading.
Evaluate market conditions for potential risks and optimal position sizing.
Consider volatility, liquidity, and potential downside scenarios.
Always prioritize capital preservation and suggest appropriate stop-loss levels.""",
                llm_config={"config_list": config_list},
            )
            
            global_market_analyst = None
            try:
                # Include GlobalMarketAnalyst if available
                if "global_market" in session_data.get("market_data", {}):
                    global_market_analyst = AssistantAgent(
                        name="GlobalMarketAnalyst",
                        system_message="""You are an expert in global market analysis, focusing on macro trends and correlations.
Analyze relationships between crypto assets and traditional markets.
Consider economic indicators, geopolitical events, and institutional activity.
Highlight relevant market sentiment across asset classes.""",
                        llm_config={"config_list": config_list},
                    )
            except Exception as e:
                logger.warning(f"Could not create GlobalMarketAnalyst: {str(e)}")
            
            liquidity_analyst = None
            try:
                # Include LiquidityAnalyst if available
                if "liquidity" in session_data.get("market_data", {}):
                    liquidity_analyst = AssistantAgent(
                        name="LiquidityAnalyst",
                        system_message="""You are an expert in market liquidity and order flow analysis.
Analyze exchange flows, futures basis, funding rates, and market depth.
Identify potential liquidity issues, unusual flows, and smart money movement.
Focus on on-chain metrics and derivatives market conditions.""",
                        llm_config={"config_list": config_list},
                    )
            except Exception as e:
                logger.warning(f"Could not create LiquidityAnalyst: {str(e)}")
            
            trading_advisor = AssistantAgent(
                name="TradingAdvisor",
                system_message=f"""You are a cryptocurrency trading advisor synthesizing all information.
Create clear, decisive trading recommendations based on all specialists' input.
For {symbol}, provide a final decision in this exact JSON format within a code block:
```json
{{
  "symbol": "{symbol}",
  "action": "BUY|SELL|HOLD",
  "confidence": 0.XX,  # 0.0-1.0 representing certainty level
  "price": {current_price},
  "risk_level": "low|medium|high",
  "reasoning": "Brief explanation of the decision"
}}```
Propose a clear strategy that matches the current market conditions.""",
                llm_config={"config_list": config_list},
            )
            
            strategy_manager = AssistantAgent(
                name="StrategyManager",
                system_message="""You are a trading strategy expert.
Formulate specific entry, exit, and management plans.
Adjust strategies based on changing market conditions and time horizons.
Provide concrete action plans with clear price targets.""",
                llm_config={"config_list": config_list},
            )
            
            # Create a user proxy to manage the conversation
            user_proxy = UserProxyAgent(
                name="ModerationAgent",
                system_message="I need help analyzing market conditions and making a trading decision.",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=2
            )
            
            # Construct the moderation message that guides the conversation
            moderator_message = f"""You are the moderator of this trading decision session about {symbol}.
Current price: ${current_price}
Time: {datetime.now().isoformat()}
"""
            
            # Include global market analyst prompt if available
            if global_market_analyst:
                moderator_message += """First, ask the GlobalMarketAnalyst to provide macro context and correlations.
"""
            
            # Include market analyst prompt
            moderator_message += """Ask the MarketAnalyst to provide their technical analysis of recent price action and indicators.
"""
            
            # Include liquidity analyst prompt if available
            if liquidity_analyst:
                moderator_message += """Ask the LiquidityAnalyst to provide insights on market flows and liquidity conditions.
"""
                
            # Include risk manager prompt
            moderator_message += """Then, ask the RiskManager to assess the current risk level based on all available information.
Next, ask the StrategyManager to propose specific trading strategies given the market conditions.
Finally, ask the TradingAdvisor to synthesize all information and provide a final trading decision in JSON format.
Keep the conversation focused and goal-oriented, calling on specialists in the order mentioned."""
            
            # Prepare the list of agents to include in the group chat
            agents = [user_proxy, market_analyst, risk_manager, strategy_manager, trading_advisor]
            
            # Add optional specialized analysts if available
            if global_market_analyst:
                agents.append(global_market_analyst)
                
            if liquidity_analyst:
                agents.append(liquidity_analyst)
            
            # Setup a group chat
            groupchat = autogen.GroupChat(
                agents=agents,
                messages=[],
                max_round=self.config.get("max_turns", 10)
            )
            
            manager = autogen.GroupChatManager(groupchat=groupchat)
            
            # Start the conversation with market data summary
            initial_message = f"""
# Decision Session: {symbol} Analysis

## Current Market Data Summary
{market_summary}

{moderator_message}
"""
            
            # Initiate the group chat
            user_proxy.initiate_chat(
                manager,
                message=initial_message
            )
            
            # Extract the final decision from the chat history
            chat_history = groupchat.messages
            decision = self._extract_decision(chat_history)
            
            if not decision:
                logger.warning("Could not extract decision from chat history")
                decision = {
                    "symbol": symbol,
                    "action": "HOLD",
                    "confidence": 0.5,
                    "price": current_price,
                    "risk_level": "medium",
                    "reasoning": "Default HOLD decision as no clear decision could be extracted from the agent conversation.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Add missing fields if necessary
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.now().isoformat()
                
            if "price" not in decision:
                decision["price"] = current_price
            
            logger.info(f"Agent decision: {decision.get('action', 'UNKNOWN')} {symbol} with {decision.get('confidence', 0.0):.2f} confidence")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in agent session: {str(e)}")
            
            # Fallback to simulated session if agent session fails
            logger.info("Falling back to simulated session due to error")
            return self._run_simulated_session(session_data)
    
    def _format_market_summary(self, market_data: Dict[str, Any]) -> str:
        """
        Format market data as a human-readable summary for the initial message.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            Formatted market summary text
        """
        summary_parts = []
        
        # Add latest price information
        latest = market_data.get("latest_price", {})
        if latest:
            summary_parts.append(f"Current Price: ${latest.get('close', 'Unknown')}")
            summary_parts.append(f"24h Change: {latest.get('percent_change', 'Unknown')}%")
            summary_parts.append(f"24h Volume: {latest.get('volume', 'Unknown')}")
        
        # Add technical indicator summary
        indicators = market_data.get("technical_indicators", {})
        
        # RSI
        rsi = indicators.get("rsi", {})
        if rsi and "value" in rsi:
            rsi_value = rsi["value"]
            rsi_signal = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
            summary_parts.append(f"RSI: {rsi_value:.2f} ({rsi_signal})")
        
        # Moving Averages
        sma = indicators.get("sma", {})
        if sma:
            if "sma_20" in sma and "sma_50" in sma:
                sma20 = sma["sma_20"]
                sma50 = sma["sma_50"]
                cross_signal = "Bullish (Above 50 SMA)" if sma20 > sma50 else "Bearish (Below 50 SMA)"
                summary_parts.append(f"SMA 20: {sma20:.2f}, SMA 50: {sma50:.2f}")
                summary_parts.append(f"MA Signal: {cross_signal}")
        
        # Support & Resistance
        sr = indicators.get("support_resistance", {})
        if sr:
            supports = sr.get("support_levels", [])
            resistances = sr.get("resistance_levels", [])
            
            if supports:
                summary_parts.append(f"Support Levels: {', '.join([f'${s:.2f}' for s in supports[:3]])}")
            
            if resistances:
                summary_parts.append(f"Resistance Levels: {', '.join([f'${r:.2f}' for r in resistances[:3]])}")
        
        # Patterns
        patterns = indicators.get("patterns", {})
        if patterns and "detected_patterns" in patterns:
            detected = patterns["detected_patterns"]
            if detected:
                summary_parts.append(f"Patterns: {', '.join(detected[:3])}")
        
        # Volatility
        vol = indicators.get("volatility", {})
        if vol and "value" in vol:
            summary_parts.append(f"Volatility (20-day): {vol['value']:.2f}%")
        
        # Add global market summary if available
        global_market = market_data.get("global_market", {})
        if global_market:
            macro = global_market.get("macro_summary", {})
            if macro and "summary" in macro:
                summary_parts.append("\n## Global Market Context")
                summary_parts.append(macro["summary"])
            
            indices = global_market.get("market_indices", {})
            if indices:
                summary_parts.append("\n## Market Indices")
                for idx, value in indices.items():
                    if isinstance(value, dict) and "value" in value and "change" in value:
                        summary_parts.append(f"- {idx}: {value['value']} ({value['change']}%)")
        
        # Add liquidity data if available
        liq = market_data.get("liquidity", {})
        if liq:
            summary_parts.append("\n## Liquidity Metrics")
            
            if "exchange_flows" in liq and liq["exchange_flows"]:
                ef = liq["exchange_flows"]
                if "net_flow_trend" in ef:
                    summary_parts.append(f"- Exchange Flow Trend: {ef['net_flow_trend']}")
            
            if "funding_rates" in liq and liq["funding_rates"]:
                fr = liq["funding_rates"]
                if "average_funding_rate" in fr:
                    avg_rate = fr["average_funding_rate"] * 100  # Convert to percentage
                    summary_parts.append(f"- Avg. Funding Rate: {avg_rate:.4f}%")
            
            if "futures_basis" in liq and liq["futures_basis"]:
                fb = liq["futures_basis"]
                if "annualized_basis" in fb:
                    basis = fb["annualized_basis"]
                    summary_parts.append(f"- Futures Annualized Basis: {basis:.2f}%")
        
        return "\n".join(summary_parts)
    
    def _extract_decision(self, chat_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract trading decision from chat history.
        
        Args:
            chat_history: List of chat messages
            
        Returns:
            Decision dictionary or None if not found
        """
        # Look for messages from the trading advisor
        for message in reversed(chat_history):
            if message.get("name") == "TradingAdvisor":
                content = message.get("content", "")
                
                # Try to find JSON in the message
                try:
                    # Look for JSON pattern
                    import re
                    json_matches = re.findall(r'\{[^{}]*"action"[^{}]*\}', content, re.DOTALL)
                    
                    for json_str in json_matches:
                        try:
                            decision_data = json.loads(json_str)
                            if "action" in decision_data:
                                return decision_data
                        except:
                            continue
                    
                    # Alternative approach: look for JSON block markers
                    json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    
                    for block in json_blocks:
                        try:
                            decision_data = json.loads(block)
                            if "action" in decision_data:
                                return decision_data
                        except:
                            continue
                    
                except Exception as e:
                    logger.error(f"Error extracting decision JSON: {str(e)}")
        
        return None