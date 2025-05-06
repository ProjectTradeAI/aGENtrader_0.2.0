"""
aGENtrader v2 Tone Agent

This agent is responsible for generating human-like, styled summaries of multi-agent trade
decisions, giving each agent a unique voice and providing an overall narrative.
"""
import os
import sys
import json
import random
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
        
        # Define confidence-based tone modifiers
        self.confidence_tone_modifiers = {
            "high": {  # 80%+ confidence
                "prefix_templates": [
                    "Decisively", "Confidently", "Absolutely", "Clearly", "Without a doubt",
                    "All indicators suggest", "The data strongly shows", "I'm convinced"
                ],
                "suffix_templates": [
                    "with strong conviction", "with high confidence", "based on solid evidence",
                    "looking remarkably clear", "- the signals are strong"
                ],
                "description": "assertive, confident, definitive"
            },
            "medium": {  # 60-79% confidence
                "prefix_templates": [
                    "Moderately", "Reasonably", "It appears", "The data suggests", "I believe",
                    "There's decent evidence", "It seems", "I'm seeing signs"
                ],
                "suffix_templates": [
                    "with moderate confidence", "with reasonable certainty", "though not absolutely certain",
                    "based on adequate evidence", "- the signals are moderate"
                ],
                "description": "balanced, measured, somewhat cautious"
            },
            "low": {  # Below 60% confidence
                "prefix_templates": [
                    "Tentatively", "Hesitantly", "Perhaps", "There's a hint that", "I'm sensing",
                    "Early indications suggest", "It's possible", "I'm slightly leaning"
                ],
                "suffix_templates": [
                    "but I'm not entirely confident", "though the signals are weak", "with low confidence",
                    "though it's too early to be certain", "- take this with caution"
                ],
                "description": "hesitant, reserved, speculative"
            }
        }
        
        # Define fallback tone modifiers
        self.fallback_tone_modifiers = {
            "prefix_templates": [
                "With limited data", "Based on partial information", "Working with minimal signals",
                "From what little I can gather", "With incomplete information"
            ],
            "suffix_templates": [
                "but take this with extra caution", "though more data would help", "though this is highly uncertain",
                "consider this preliminary at best", "until more information becomes available"
            ],
            "description": "cautious, minimal, explicitly uncertain"
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
                
                # Check for fallback/partial data flags
                is_fallback = analysis.get("is_fallback", False) or analysis.get("fallback", False)
                is_partial_data = analysis.get("is_partial", False) or analysis.get("partial_data", False)
                using_heuristics = analysis.get("using_heuristics", False) or analysis.get("heuristic_based", False)
                
                # Generate a flag for fallback data
                data_quality = "normal"
                if is_fallback or is_partial_data or using_heuristics:
                    data_quality = "fallback"
                    
                self.logger.info(f"Agent: {agent_name}, Signal: {signal}, Confidence: {confidence}, Data Quality: {data_quality}")
                
                analyst_info.append({
                    "agent": agent_name,
                    "signal": signal,
                    "confidence": confidence,
                    "reasoning": reasoning[:300],  # Truncate for prompt length
                    "data_quality": data_quality
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
            data_quality = info.get("data_quality", "normal")
            
            prompt += f"- {agent}:\n"
            prompt += f"  Signal: {signal}\n"
            prompt += f"  Confidence: {confidence}%\n"
            prompt += f"  Data Quality: {data_quality}\n"
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
        
        # Add dynamic tone scaling instructions based on confidence levels
        prompt += "\nTONE SCALING INSTRUCTIONS:\n"
        prompt += "- Adjust each agent's tone based on their confidence level:\n"
        prompt += "  * 80%+ confidence: Use assertive, confident, definitive language\n"
        prompt += "  * 60-79% confidence: Use balanced, measured, somewhat cautious language\n"
        prompt += "  * Below 60% confidence: Use hesitant, reserved, speculative language\n"
        
        # Add fallback tone instructions
        prompt += "- For any agent whose data is flagged as fallback or has missing/partial data:\n"
        prompt += "  * Use explicitly cautious, minimal tone that acknowledges limited information\n"
        prompt += "  * Include phrasing like 'with limited data' or 'based on partial information'\n"
        
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
        
        # Determine tone level based on confidence
        if confidence >= 80:
            tone_level = "high"
            mood_prefix = ""
        elif confidence >= 60:
            tone_level = "medium"
            mood_prefix = "cautiously_"
        else:
            tone_level = "low"
            mood_prefix = "tentatively_"
            
        # Get tone modifiers
        prefix = random.choice(self.confidence_tone_modifiers[tone_level]["prefix_templates"])
        
        # Adjust system summary based on signal with appropriate tone
        if signal == "BUY":
            result["system_summary"] = f"{prefix} seeing a bullish signal for {symbol} with {confidence}% confidence."
            result["mood"] = f"{mood_prefix}bullish"
        elif signal == "SELL":
            result["system_summary"] = f"{prefix} seeing a bearish signal for {symbol} with {confidence}% confidence."
            result["mood"] = f"{mood_prefix}bearish"
        elif signal == "HOLD":
            result["system_summary"] = f"{prefix} maintaining a neutral stance on {symbol} with {confidence}% confidence."
            result["mood"] = "neutral"
        elif signal == "CONFLICTED":
            result["system_summary"] = f"Seeing conflicted signals for {symbol}, which requires caution."
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
            
            # Check for fallback/partial data flags
            is_fallback = analysis.get("is_fallback", False) or analysis.get("fallback", False)
            is_partial_data = analysis.get("is_partial", False) or analysis.get("partial_data", False)
            using_heuristics = analysis.get("using_heuristics", False) or analysis.get("heuristic_based", False)
            
            # Apply confidence-based tone modifiers
            if confidence >= 80:
                tone_level = "high"
            elif confidence >= 60:
                tone_level = "medium"
            else:
                tone_level = "low"
                
            # Generate comment with appropriate tone
            if is_fallback or is_partial_data or using_heuristics:
                # Use fallback tone
                prefix = self.fallback_tone_modifiers["prefix_templates"][0]
                suffix = self.fallback_tone_modifiers["suffix_templates"][0]
                comment = f"{prefix}, I'm seeing a {signal} signal {suffix}."
            else:
                # Use confidence-based tone
                prefix = self.confidence_tone_modifiers[tone_level]["prefix_templates"][0]
                suffix = self.confidence_tone_modifiers[tone_level]["suffix_templates"][0]
                comment = f"{prefix} seeing a {signal} signal {suffix}."
            
            result["agent_comments"][agent_name] = comment
            
            self.logger.info(f"Fallback for {agent_name}: {signal} with {confidence}% (Tone: {tone_level})")
        
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