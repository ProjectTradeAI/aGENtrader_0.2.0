#!/usr/bin/env python3
"""
AutoGen Decision Session for Trading

This module provides a decision session implementation using AutoGen
for collaborative multi-agent trading decisions.
"""
import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for importing utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try to import our custom LLM integration
try:
    from utils.llm_integration import AutoGenLLMConfig, LocalLLMAPIClient, clear_model
    LLM_INTEGRATION_AVAILABLE = True
except ImportError:
    LLM_INTEGRATION_AVAILABLE = False
    logging.warning("LLM integration not available. Will use default AutoGen configuration.")

# Try to import AutoGen
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logging.warning("AutoGen is not installed. Decision session will use fallback strategy.")

class MultiAgentDecisionSession:
    """
    Multi-agent decision session for trading using AutoGen.
    """
    
    def __init__(self):
        """Initialize the decision session."""
        self.logger = logging.getLogger("decision_session")
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = os.path.join("data", "decisions")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check if AutoGen is available
        self.autogen_available = AUTOGEN_AVAILABLE and LLM_INTEGRATION_AVAILABLE
        
        if self.autogen_available:
            self.logger.info("AutoGen is available. Using multi-agent decision making.")
            # Patch AutoGen to use local LLM if integration is available
            if LLM_INTEGRATION_AVAILABLE:
                AutoGenLLMConfig.patch_autogen()
                self.logger.info("AutoGen patched to use local LLM integration.")
        else:
            self.logger.warning("AutoGen not available. Will use fallback decision strategy.")
            
        # Initialize agents
        self.agents = None
        self.group_chat = None
    
    def _setup_agents(self, symbol: str) -> None:
        """
        Set up the trading agents for the decision session.
        
        Args:
            symbol: Trading symbol
        """
        if not self.autogen_available:
            return
        
        try:
            # Configure agents
            self.logger.info("Setting up trading agents...")
            
            # Create configs
            technical_config = AutoGenLLMConfig.create_llm_config(
                agent_name="TechnicalAnalyst",
                temperature=0.3,
                use_local_llm=True
            )
            
            fundamental_config = AutoGenLLMConfig.create_llm_config(
                agent_name="FundamentalAnalyst",
                temperature=0.4,
                use_local_llm=True
            )
            
            sentiment_config = AutoGenLLMConfig.create_llm_config(
                agent_name="SentimentAnalyst",
                temperature=0.5,
                use_local_llm=True
            )
            
            decision_config = AutoGenLLMConfig.create_llm_config(
                agent_name="DecisionMaker",
                temperature=0.2,
                use_local_llm=True
            )
            
            # Create agents
            technical_analyst = AssistantAgent(
                name="TechnicalAnalyst",
                system_message=f"""You are a cryptocurrency Technical Analyst specializing in {symbol}.
                You analyze price patterns, chart formations, and technical indicators.
                Focus only on technical analysis aspects. Be concise and specific.
                Provide actionable insights based on technical indicators.""",
                llm_config=technical_config
            )
            
            fundamental_analyst = AssistantAgent(
                name="FundamentalAnalyst",
                system_message=f"""You are a cryptocurrency Fundamental Analyst specializing in {symbol}.
                You analyze on-chain metrics, developer activity, adoption metrics, and macroeconomic factors.
                Focus only on fundamental analysis. Be concise and specific.
                Provide actionable insights based on fundamental factors.""",
                llm_config=fundamental_config
            )
            
            sentiment_analyst = AssistantAgent(
                name="SentimentAnalyst",
                system_message=f"""You are a cryptocurrency Sentiment Analyst specializing in {symbol}.
                You analyze market sentiment, social media trends, and trading psychology.
                Focus only on sentiment analysis. Be concise and specific.
                Provide actionable insights based on market sentiment.""",
                llm_config=sentiment_config
            )
            
            decision_maker = AssistantAgent(
                name="DecisionMaker",
                system_message=f"""You are the Trading Decision Maker specializing in {symbol}.
                You synthesize insights from technical, fundamental, and sentiment analysis.
                Your job is to make the final trading decision for {symbol}.
                Your decision MUST be either BUY, SELL, or HOLD with a confidence score from 0.0 to 1.0.
                You must provide a brief rationale for your decision.
                Format your final response as a JSON object with the following fields:
                {{
                    "action": "BUY/SELL/HOLD",
                    "confidence": 0.XX,
                    "reasoning": "brief explanation",
                    "timeframe": "short-term/medium-term/long-term",
                    "stop_loss_percent": XX.X,
                    "take_profit_percent": XX.X
                }}""",
                llm_config=decision_config
            )
            
            # Create a user proxy agent
            user_proxy = UserProxyAgent(
                name="TraderProxy",
                human_input_mode="NEVER",
                system_message="You coordinate the market analysis and trading decision process.",
                code_execution_config=False
            )
            
            # Set up the group chat
            self.agents = [
                user_proxy,
                technical_analyst,
                fundamental_analyst,
                sentiment_analyst,
                decision_maker
            ]
            
            # Create group chat
            groupchat = GroupChat(
                agents=self.agents,
                messages=[],
                max_round=5
            )
            
            # Create the group chat manager
            self.group_chat = GroupChatManager(
                groupchat=groupchat,
                llm_config=decision_config
            )
            
            self.logger.info("Trading agents setup completed successfully.")
            
        except Exception as e:
            self.logger.error(f"Error setting up agents: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.agents = None
            self.group_chat = None
    
    def run_decision(self, symbol: str, interval: str = '1h', 
                    current_price: float = None, market_data: Dict = None,
                    analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Run a trading decision session.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe interval (e.g., 1h, 4h, 1d)
            current_price: Current price of the asset
            market_data: Dictionary with additional market data
            analysis_type: Type of analysis to perform
            
        Returns:
            Dict with decision data
        """
        # Initialize timestamp
        timestamp = datetime.datetime.utcnow()
        
        # Set up agents if not already done
        if self.agents is None or self.group_chat is None:
            self._setup_agents(symbol)
        
        # Check if AutoGen is available
        if not self.autogen_available or self.agents is None:
            return self._fallback_decision(symbol, interval, current_price, timestamp)
        
        try:
            # Format market data for agents
            market_info = self._format_market_data(symbol, interval, current_price, market_data)
            
            # Create the initial prompt for the group chat
            prompt = f"""
            Trading Decision Request for {symbol} on {interval} timeframe
            Current timestamp: {timestamp.isoformat()}
            Current price: ${current_price if current_price else 'Unknown'}
            
            Please analyze the market and provide a trading decision for {symbol}.
            
            {market_info}
            
            This is the process I want you to follow:
            1. The TechnicalAnalyst will analyze price actions and technical indicators
            2. The FundamentalAnalyst will analyze on-chain metrics and fundamentals
            3. The SentimentAnalyst will analyze market sentiment and social indicators
            4. Each analyst should provide their view on whether to BUY, SELL, or HOLD
            5. The DecisionMaker will synthesize all analyses and make the final trading decision
            
            The final decision must be formatted as a JSON object with the following fields:
            {{
                "action": "BUY/SELL/HOLD",
                "confidence": 0.XX,
                "reasoning": "brief explanation",
                "timeframe": "short-term/medium-term/long-term",
                "stop_loss_percent": XX.X,
                "take_profit_percent": XX.X
            }}
            """
            
            # Start the group chat
            self.logger.info(f"Starting group chat for {symbol}...")
            user_proxy = next(agent for agent in self.agents if agent.name == "TraderProxy")
            
            # Initiate the chat
            result = user_proxy.initiate_chat(
                self.group_chat,
                message=prompt
            )
            
            # Extract the decision from the chat
            decision = self._parse_decision_from_chat(result)
            
            # Create decision data
            decision_data = {
                "status": "success",
                "timestamp": timestamp.isoformat(),
                "symbol": symbol,
                "interval": interval,
                "session_id": self.session_id,
                "decision": decision,
                "market_data": {
                    "current_price": current_price if current_price else 0,
                    "timestamp": timestamp.isoformat()
                }
            }
            
            # Save decision to file
            self._save_decision(decision_data)
            
            return decision_data
            
        except Exception as e:
            self.logger.error(f"Error in multi-agent decision: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Use fallback in case of error
            return self._fallback_decision(symbol, interval, current_price, timestamp)
        
        finally:
            # Clean up model to save memory
            if LLM_INTEGRATION_AVAILABLE:
                clear_model()
    
    def _parse_decision_from_chat(self, chat_result) -> Dict[str, Any]:
        """
        Parse the decision from the chat result.
        
        Args:
            chat_result: The result from the group chat
        
        Returns:
            Dict with parsed decision
        """
        try:
            # Get the last message from the DecisionMaker
            decision_messages = [
                msg for msg in chat_result.chat_history
                if msg.get("role") == "assistant" and "DecisionMaker" in msg.get("name", "")
            ]
            
            if not decision_messages:
                self.logger.warning("No decision message found in chat history")
                return self._create_default_decision("HOLD", 0.5, "No clear decision from analysis")
            
            # Get the last decision message
            decision_message = decision_messages[-1]["content"]
            
            # Try to extract JSON from the message
            json_start = decision_message.find("{")
            json_end = decision_message.rfind("}")
            
            if json_start >= 0 and json_end > json_start:
                json_str = decision_message[json_start:json_end+1]
                try:
                    decision = json.loads(json_str)
                    
                    # Validate required fields
                    required_fields = ["action", "confidence", "reasoning"]
                    for field in required_fields:
                        if field not in decision:
                            self.logger.warning(f"Missing required field '{field}' in decision")
                            return self._create_default_decision("HOLD", 0.5, "Invalid decision format")
                    
                    # Normalize action to uppercase
                    decision["action"] = decision["action"].upper()
                    
                    # Validate action
                    if decision["action"] not in ["BUY", "SELL", "HOLD"]:
                        self.logger.warning(f"Invalid action: {decision['action']}")
                        decision["action"] = "HOLD"
                    
                    # Ensure confidence is a float between 0 and 1
                    try:
                        decision["confidence"] = float(decision["confidence"])
                        if decision["confidence"] < 0 or decision["confidence"] > 1:
                            decision["confidence"] = max(0, min(1, decision["confidence"]))
                    except (ValueError, TypeError):
                        decision["confidence"] = 0.5
                    
                    return decision
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse decision JSON: {json_str}")
            
            # If we couldn't extract JSON, try to parse the text
            action = "HOLD"
            confidence = 0.5
            reasoning = "Default reasoning"
            
            if "BUY" in decision_message:
                action = "BUY"
            elif "SELL" in decision_message:
                action = "SELL"
            
            # Try to find confidence
            confidence_matches = [
                float(s.strip()) for s in decision_message.split() 
                if s.replace(".", "").isdigit() and 0 <= float(s) <= 1
            ]
            if confidence_matches:
                confidence = confidence_matches[0]
            
            # Extract reasoning
            reasoning_start = decision_message.find("reasoning")
            if reasoning_start >= 0:
                reasoning_end = decision_message.find("\n", reasoning_start)
                if reasoning_end < 0:
                    reasoning_end = len(decision_message)
                reasoning = decision_message[reasoning_start+10:reasoning_end].strip().strip('"\',:')
            
            return self._create_default_decision(action, confidence, reasoning)
            
        except Exception as e:
            self.logger.error(f"Error parsing decision from chat: {str(e)}")
            return self._create_default_decision("HOLD", 0.5, "Error parsing decision")
    
    def _create_default_decision(self, action: str, confidence: float, reasoning: str) -> Dict[str, Any]:
        """
        Create a default decision object.
        
        Args:
            action: Trading action (BUY, SELL, HOLD)
            confidence: Confidence level (0-1)
            reasoning: Reasoning for the decision
            
        Returns:
            Dict with decision data
        """
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "timeframe": "short-term",
            "stop_loss_percent": 5.0,
            "take_profit_percent": 10.0
        }
    
    def _format_market_data(self, symbol: str, interval: str, 
                          current_price: Optional[float], 
                          market_data: Optional[Dict]) -> str:
        """
        Format market data for agents.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe interval
            current_price: Current price
            market_data: Additional market data
            
        Returns:
            Formatted market data as a string
        """
        result = "Market Information:\n"
        
        if current_price:
            result += f"- Current Price: ${current_price}\n"
        
        if market_data:
            # Format any provided market data
            if "recent_prices" in market_data:
                result += "- Recent Prices:\n"
                for timestamp, price in market_data["recent_prices"][-5:]:  # Last 5 prices
                    result += f"  * {timestamp}: ${price}\n"
            
            if "volume_24h" in market_data:
                result += f"- 24h Volume: ${market_data['volume_24h']:,.2f}\n"
            
            if "change_24h" in market_data:
                result += f"- 24h Change: {market_data['change_24h']:.2f}%\n"
        
        return result
    
    def _fallback_decision(self, symbol: str, interval: str, 
                         current_price: Optional[float], 
                         timestamp: datetime.datetime) -> Dict[str, Any]:
        """
        Generate a fallback decision when AutoGen is not available.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe interval
            current_price: Current price
            timestamp: Current timestamp
            
        Returns:
            Dict with decision data
        """
        self.logger.info("Using fallback decision strategy")
        
        # Default values for different symbols
        if symbol.upper() == "BTCUSDT":
            action = "BUY"
            confidence = 0.65
            reasoning = "Fallback strategy for Bitcoin trading"
            current_price = current_price or 85000.0
        elif symbol.upper() == "ETHUSDT":
            action = "HOLD"
            confidence = 0.55
            reasoning = "Fallback strategy for Ethereum trading"
            current_price = current_price or 3500.0
        else:
            action = "HOLD"
            confidence = 0.5
            reasoning = f"Fallback strategy for {symbol} trading"
            current_price = current_price or 1000.0
        
        # Create decision data
        decision = {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "timeframe": "short-term",
            "stop_loss_percent": 5.0,
            "take_profit_percent": 10.0
        }
        
        decision_data = {
            "status": "success",
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "interval": interval,
            "session_id": self.session_id,
            "decision": decision,
            "market_data": {
                "current_price": current_price,
                "timestamp": timestamp.isoformat()
            }
        }
        
        # Save decision to file
        self._save_decision(decision_data)
        
        return decision_data
    
    def _save_decision(self, decision_data: Dict[str, Any]) -> None:
        """
        Save decision data to file.
        
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
                
            self.logger.info(f"Decision saved to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving decision: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())