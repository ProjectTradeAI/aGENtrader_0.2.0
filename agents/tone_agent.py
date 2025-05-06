"""
aGENtrader v2 Tone Agent

This agent is responsible for generating human-like, styled summaries of multi-agent trade
decisions, giving each agent a unique voice and providing an overall narrative.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import base agent class
from agents.base_agent import BaseAgent

# Import Grok sentiment client for LLM capabilities
try:
    from models.grok_sentiment_client import GrokSentimentClient
except ImportError:
    GrokSentimentClient = None
    print("Warning: GrokSentimentClient not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToneAgent")

class ToneAgent(BaseAgent):
    """
    Agent that generates human-like, styled summaries of multi-agent trade decisions.
    
    This agent takes all analyst outputs and the final decision, then creates
    a narrative with each agent having a unique voice/tone.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Tone Agent.
        
        Args:
            config: Configuration dictionary with optional settings
        """
        super().__init__("ToneAgent")
        self.description = "Generates human-like summaries of multi-agent trade decisions"
        
        # Set up logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize Grok client if available
        self.grok_client = GrokSentimentClient() if GrokSentimentClient else None
        
        if self.grok_client and not self.grok_client.enabled:
            self.logger.warning("Grok client not enabled. Check XAI_API_KEY and OpenAI package.")
        
        # Agent-specific configuration
        self.config = config or {}
        
        # Define agent tone profiles
        self.tone_profiles = {
            "TechnicalAnalystAgent": "Analytical and precise. Likes indicators, rarely exaggerates.",
            "SentimentAnalystAgent": "Emotive, intuitive, speaks in moods. Feels the crowd.",
            "LiquidityAnalystAgent": "Blunt and tactical. Sees the order book like a battlefield.",
            "OpenInterestAnalystAgent": "Cautious, looks for consistency or divergence.",
            "FundingRateAnalystAgent": "Skeptical, sharp. Knows when the herd is paying the wrong price.",
            "SentimentAggregatorAgent": "Strategic and composed. Thinks big picture, macro framing."
        }
        
        # Create logs directory if it doesn't exist
        self.logs_dir = os.path.join(parent_dir, "logs")
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            
        # Initialize agent signals storage for validation
        self._agent_signals = {}
        
        self.logger.info(f"Tone Agent initialized with {len(self.tone_profiles)} agent profiles")
    
    def generate_summary(self, 
                         analysis_results: Dict[str, Any], 
                         final_decision: Dict[str, Any], 
                         symbol: str, 
                         interval: str) -> Dict[str, Any]:
        """
        Generate a human-like summary of the multi-agent trade decision.
        
        Args:
            analysis_results: Dictionary of all analyst outputs
            final_decision: Final trade decision JSON
            symbol: Trading symbol (e.g., "BTC/USDT")
            interval: Trading interval (e.g., "1h", "4h")
            
        Returns:
            Dictionary with agent comments and system summary
        """
        # First, log the actual signals from analyst results for validation
        self._validate_and_log_signals(analysis_results)
        
        if not self.grok_client or not self.grok_client.enabled:
            self.logger.warning("Grok client not available. Using fallback summary.")
            return self._generate_fallback_summary(analysis_results, final_decision, symbol, interval)
        
        try:
            # Extract key information for prompt
            signal = final_decision.get("signal", "UNKNOWN")
            confidence = final_decision.get("confidence", 0)
            conflict_score = final_decision.get("conflict_score", 0)
            
            # Prepare analyst information for the prompt
            analyst_info = []
            
            # Map analysis type keys to agent names for better readability
            analysis_type_to_agent = {
                'technical_analysis': 'TechnicalAnalystAgent',
                'sentiment_analysis': 'SentimentAnalystAgent',
                'sentiment_aggregator_analysis': 'SentimentAggregatorAgent',
                'liquidity_analysis': 'LiquidityAnalystAgent',
                'open_interest_analysis': 'OpenInterestAnalystAgent',
                'funding_rate_analysis': 'FundingRateAnalystAgent'
            }
            
            self.logger.info(f"Raw analysis_results keys: {list(analysis_results.keys())}")
            
            for analysis_type, analysis in analysis_results.items():
                if not isinstance(analysis, dict):
                    self.logger.warning(f"Analysis for {analysis_type} is not a dictionary")
                    continue
                    
                # Get the proper agent name
                agent_name = analysis_type_to_agent.get(analysis_type, analysis_type)
                
                # Extract signal with fallbacks for different field names
                signal = analysis.get("signal") or analysis.get("final_signal") or analysis.get("action") or "UNKNOWN"
                confidence = analysis.get("confidence", 0)
                
                # Extract reasoning with fallbacks
                reasoning = analysis.get("reasoning") or analysis.get("reason") or "No reasoning provided"
                
                self.logger.info(f"Agent: {agent_name}, Signal: {signal}, Confidence: {confidence}")
                
                analyst_info.append({
                    "agent": agent_name,
                    "signal": signal,
                    "confidence": confidence,
                    "reasoning": reasoning[:300]  # Truncate for prompt length
                })
            
            # Construct the prompt
            prompt = self._construct_prompt(analyst_info, final_decision, symbol, interval)
            
            # Generate summary using Grok
            response = self.grok_client.client.chat.completions.create(
                model="grok-2-1212",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert crypto trading narrator that summarizes multi-agent trading decisions. "
                            "For each agent, create a unique voice using their personality profile. "
                            "IMPORTANT: You must accurately convey each agent's actual signal (BUY, SELL, HOLD, or NEUTRAL) "
                            "in their tone comment. Never misrepresent what signal an agent is giving - accuracy of signal "
                            "representation is critical. For example, if TechnicalAnalystAgent gives a BUY signal, their "
                            "tone must clearly indicate they are positive/recommending buying, not holding or selling. "
                            "Then create an overall summary that balances all views. Your response should be in JSON format "
                            "with keys for agent_comments (object with agent names as keys), system_summary (string), and "
                            "mood (string - one of: bullish, neutral, conflicted, cautious, euphoric)."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse the response
            if not response or not response.choices or not response.choices[0].message.content:
                raise ValueError("Empty response from Grok API")
                
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate and ensure expected fields
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
                
            if "agent_comments" not in result or "system_summary" not in result:
                raise ValueError("Response missing required fields")
                
            # Save the summary to logs
            self._save_summary(result, symbol, interval)
            
            # Print formatted summary
            self._print_formatted_summary(result, symbol, interval)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return self._generate_fallback_summary(analysis_results, final_decision, symbol, interval)
    
    def _construct_prompt(self, analyst_info: List[Dict[str, Any]], 
                          final_decision: Dict[str, Any], 
                          symbol: str, 
                          interval: str) -> str:
        """
        Construct the prompt for the Grok API.
        
        Args:
            analyst_info: List of dictionaries with analyst information
            final_decision: Final trade decision
            symbol: Trading symbol
            interval: Trading interval
            
        Returns:
            Constructed prompt as string
        """
        # Extract signal and confidence
        signal = final_decision.get("signal", "UNKNOWN")
        confidence = final_decision.get("confidence", 0)
        conflict_score = final_decision.get("conflict_score", 0)
        is_conflicted = signal == "CONFLICTED" or confidence < 70
        
        prompt = f"Generate a styled narrative summary for a {symbol} {interval} trade decision.\n\n"
        
        # Add agent tone profiles
        prompt += "AGENT TONE PROFILES:\n"
        for agent, tone in self.tone_profiles.items():
            prompt += f"- {agent}: {tone}\n"
        
        prompt += "\nANALYST OUTPUTS:\n"
        for info in analyst_info:
            agent = info.get("agent", "UnknownAgent")
            signal = info.get("signal", "UNKNOWN")
            confidence = info.get("confidence", 0)
            reasoning = info.get("reasoning", "No reasoning provided")
            
            prompt += f"- {agent}:\n"
            prompt += f"  Signal: {signal}\n"
            prompt += f"  Confidence: {confidence}%\n"
            prompt += f"  Reasoning: {reasoning}\n\n"
        
        # Add final decision
        prompt += "FINAL DECISION:\n"
        prompt += f"Signal: {signal}\n"
        prompt += f"Confidence: {confidence}%\n"
        
        if conflict_score > 0:
            prompt += f"Conflict Score: {conflict_score}%\n"
        
        # Special instructions based on decision state
        prompt += "\nSPECIAL INSTRUCTIONS:\n"
        
        # Emphasis on signal accuracy
        prompt += "- CRITICAL: For each agent comment, you MUST clearly convey their exact signal (BUY/SELL/HOLD/NEUTRAL).\n"
        prompt += "- If an agent gives a BUY signal, their comment should clearly indicate bullishness or buying action.\n"
        prompt += "- If an agent gives a NEUTRAL or HOLD signal, their comment should express caution, neutrality, or waiting.\n"
        prompt += "- If an agent gives a SELL signal, their comment should clearly indicate bearishness or selling action.\n"
        prompt += "- Never misrepresent an agent's signal in their comment - this is a critical requirement.\n"
        
        if is_conflicted:
            prompt += "- Use a more cautious tone in the system summary as this is a conflicted or low confidence decision.\n"
        
        if signal == "BUY":
            prompt += "- The final decision is bullish, but acknowledge any dissenting views.\n"
        elif signal == "SELL":
            prompt += "- The final decision is bearish, but acknowledge any dissenting views.\n"
        
        # Output format instructions
        prompt += """
OUTPUT FORMAT:
Generate a JSON object with these keys:
1. agent_comments: An object where keys are agent names and values are their comments in their distinctive voice (1 sentence each)
2. system_summary: A 1-2 sentence overall summary that balances all views
3. mood: A single word describing the overall mood (bullish, neutral, conflicted, cautious, or euphoric)

For example:
{
  "agent_comments": {
    "TechnicalAnalystAgent": "The RSI is cooling off but I see a promising setup forming.",
    ...
  },
  "system_summary": "Growing bullish momentum with some caution flags.",
  "mood": "cautiously_bullish"
}
"""
        
        return prompt
    
    def _generate_fallback_summary(self, 
                                 analysis_results: Dict[str, Any], 
                                 final_decision: Dict[str, Any], 
                                 symbol: str, 
                                 interval: str) -> Dict[str, Any]:
        """
        Generate a fallback summary when Grok is unavailable.
        
        Args:
            analysis_results: Dictionary of all analyst outputs
            final_decision: Final trade decision JSON
            symbol: Trading symbol
            interval: Trading interval
            
        Returns:
            Dictionary with agent comments and system summary
        """
        # Create basic summary with generic agent comments
        result = {
            "agent_comments": {},
            "system_summary": "Trading decision based on multiple factors.",
            "mood": "neutral"
        }
        
        # Extract signal and confidence
        signal = final_decision.get("signal", "UNKNOWN")
        confidence = final_decision.get("confidence", 0)
        
        # Adjust system summary based on signal
        if signal == "BUY":
            result["system_summary"] = f"Bullish signal for {symbol} with {confidence}% confidence."
            result["mood"] = "bullish"
        elif signal == "SELL":
            result["system_summary"] = f"Bearish signal for {symbol} with {confidence}% confidence."
            result["mood"] = "bearish"
        elif signal == "HOLD":
            result["system_summary"] = f"Neutral stance on {symbol} with {confidence}% confidence."
            result["mood"] = "neutral"
        elif signal == "CONFLICTED":
            result["system_summary"] = f"Conflicted signals for {symbol}, requires caution."
            result["mood"] = "conflicted"
        
        # Map analysis type keys to agent names for better readability
        analysis_type_to_agent = {
            'technical_analysis': 'TechnicalAnalystAgent',
            'sentiment_analysis': 'SentimentAnalystAgent',
            'sentiment_aggregator_analysis': 'SentimentAggregatorAgent',
            'liquidity_analysis': 'LiquidityAnalystAgent',
            'open_interest_analysis': 'OpenInterestAnalystAgent',
            'funding_rate_analysis': 'FundingRateAnalystAgent'
        }
        
        # Add basic agent comments
        for analysis_type, analysis in analysis_results.items():
            if not isinstance(analysis, dict):
                continue
                
            # Get the proper agent name
            agent_name = analysis_type_to_agent.get(analysis_type, analysis_type)
            
            # Extract signal with fallbacks for different field names
            signal = analysis.get("signal") or analysis.get("final_signal") or analysis.get("action") or "UNKNOWN"
            confidence = analysis.get("confidence", 0)
            
            comment = f"{signal} signal with {confidence}% confidence."
            result["agent_comments"][agent_name] = comment
            
            self.logger.info(f"Fallback for {agent_name}: {signal} with {confidence}%")
        
        # Save the summary to logs
        self._save_summary(result, symbol, interval)
        
        # Print formatted summary
        self._print_formatted_summary(result, symbol, interval)
        
        return result
    
    def _save_summary(self, summary: Dict[str, Any], symbol: str, interval: str) -> None:
        """
        Save the summary to a log file.
        
        Args:
            summary: Summary dictionary
            symbol: Trading symbol
            interval: Trading interval
        """
        try:
            # Create a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Clean the symbol for filename
            clean_symbol = symbol.replace("/", "")
            
            # Create the log filename
            filename = f"tone_summary_{clean_symbol}_{interval}_{timestamp}.json"
            filepath = os.path.join(self.logs_dir, filename)
            
            # Save the summary as JSON
            with open(filepath, "w") as f:
                json.dump(summary, f, indent=2)
                
            self.logger.info(f"Tone summary saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving tone summary: {str(e)}")
    
    def _validate_and_log_signals(self, analysis_results: Dict[str, Any]) -> None:
        """
        Validate and log the actual signals from the analysis results.
        This helps in debugging signal mismatches between agent outputs and tone summaries.
        
        Args:
            analysis_results: Dictionary of all analyst outputs
        """
        try:
            # Map analysis type keys to agent names for better readability
            analysis_type_to_agent = {
                'technical_analysis': 'TechnicalAnalystAgent',
                'sentiment_analysis': 'SentimentAnalystAgent',
                'sentiment_aggregator_analysis': 'SentimentAggregatorAgent',
                'liquidity_analysis': 'LiquidityAnalystAgent',
                'open_interest_analysis': 'OpenInterestAnalystAgent',
                'funding_rate_analysis': 'FundingRateAnalystAgent'
            }
            
            # Count signals by type
            signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0, "UNKNOWN": 0}
            agent_signals = {}
            
            # Banner for visibility in logs
            self.logger.info("=" * 50)
            self.logger.info("VALIDATION - ACTUAL AGENT SIGNALS:")
            self.logger.info("-" * 50)
            
            for analysis_type, analysis in analysis_results.items():
                if not isinstance(analysis, dict):
                    self.logger.warning(f"Analysis for {analysis_type} is not a dictionary")
                    continue
                
                # Get the proper agent name
                agent_name = analysis_type_to_agent.get(analysis_type, analysis_type)
                
                # Extract signal with fallbacks for different field names
                signal = analysis.get("signal") or analysis.get("final_signal") or analysis.get("action") or "UNKNOWN"
                confidence = analysis.get("confidence", 0)
                
                # Update counts and record
                if signal in signal_counts:
                    signal_counts[signal] += 1
                else:
                    signal_counts["UNKNOWN"] += 1
                
                agent_signals[agent_name] = {
                    "signal": signal,
                    "confidence": confidence
                }
                
                self.logger.info(f"Agent: {agent_name}, Signal: {signal}, Confidence: {confidence}%")
                
            # Print summary of signals
            self.logger.info("-" * 50)
            self.logger.info(f"Signal Count: BUY: {signal_counts['BUY']}, SELL: {signal_counts['SELL']}, HOLD/NEUTRAL: {signal_counts['HOLD'] + signal_counts['NEUTRAL']}, UNKNOWN: {signal_counts['UNKNOWN']}")
            self.logger.info("=" * 50)
            
            # Store for comparison later
            self._agent_signals = agent_signals
            
        except Exception as e:
            self.logger.error(f"Error validating signals: {str(e)}")
            
    def _print_formatted_summary(self, summary: Dict[str, Any], symbol: str, interval: str) -> None:
        """
        Print the summary in a formatted way.
        
        Args:
            summary: Summary dictionary
            symbol: Trading symbol
            interval: Trading interval
        """
        try:
            agent_comments = summary.get("agent_comments", {})
            system_summary = summary.get("system_summary", "No summary available")
            mood = summary.get("mood", "neutral")
            
            # Format the output
            output = f"\n🎙️ ToneAgent Summary — {symbol} ({interval})\n\n"
            
            # Add agent comments
            output += "📣 Agent Voices:\n"
            for agent, comment in agent_comments.items():
                output += f"- {agent}: \"{comment}\"\n"
            
            # Extract and count signals from agent comments (for validation)
            signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "NEUTRAL": 0, "UNKNOWN": 0}
            for comment in agent_comments.values():
                for signal in signal_counts.keys():
                    if signal in comment:
                        signal_counts[signal] += 1
                        break
            
            # Log signal counts for validation
            output += f"\n📊 Signal Count (from tone): BUY: {signal_counts['BUY']}, SELL: {signal_counts['SELL']}, HOLD/NEUTRAL: {signal_counts['HOLD'] + signal_counts['NEUTRAL']}\n"
            
            # Compare with actual signals (if available)
            if hasattr(self, '_agent_signals') and self._agent_signals:
                output += "\n⚠️ VALIDATION - Signals in Tone vs Actual:\n"
                for agent, comment in agent_comments.items():
                    if agent in self._agent_signals:
                        actual_signal = self._agent_signals[agent]["signal"]
                        actual_confidence = self._agent_signals[agent]["confidence"]
                        
                        # Check if the tone matches the actual signal
                        tone_matches = actual_signal in comment
                        match_marker = "✅" if tone_matches else "❌"
                        
                        output += f"{match_marker} {agent}: Actual={actual_signal} @ {actual_confidence}%, Tone: \"{comment}\"\n"
                
            # Add system summary
            output += f"\n🧠 Summary: {system_summary}\n"
            
            # Add mood if available
            if mood:
                output += f"\n🔮 Mood: {mood}\n"
                
            # Print the formatted summary
            logger.info(output)
            
        except Exception as e:
            self.logger.error(f"Error printing formatted summary: {str(e)}")