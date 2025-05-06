#!/usr/bin/env python3
"""
aGENtrader v2 - Tone Agent

This module provides a tone agent that generates human-like styled summaries of
multi-agent trade decisions and integrates it into the full trade cycle test output.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import base agent
from agents.base_agent import BaseAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ToneAgent(BaseAgent):
    """ToneAgent for aGENtrader v0.2.2
    
    This agent generates human-like styled summaries of multi-agent trade decisions.
    It provides a unique "voice" for each agent and synthesizes an overall narrative.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tone agent.
        
        Args:
            config: Configuration dictionary (optional)
        """
        super().__init__(agent_name="ToneAgent")
        self.version = "v0.2.2"
        self.config = config or {}
        
        # Configure paths
        self.log_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
            
        # Load agent tone profiles
        self.agent_tones = {
            "TechnicalAnalystAgent": "Analytical and precise. Likes indicators, rarely exaggerates.",
            "SentimentAnalystAgent": "Emotive, intuitive, speaks in moods. Feels the crowd.",
            "LiquidityAnalystAgent": "Blunt and tactical. Sees the order book like a battlefield.",
            "OpenInterestAnalystAgent": "Cautious, looks for consistency or divergence.",
            "FundingRateAnalystAgent": "Skeptical, sharp. Knows when the herd is paying the wrong price.",
            "SentimentAggregatorAgent": "Strategic and composed. Thinks big picture, macro framing."
        }
        
        # Try to load from LLM client for Grok integration
        try:
            from models.llm_client import LLMClient
            self.llm_client = LLMClient(model="grok:grok-2-1212")
            self.use_api = self.config.get("use_api", True)
            logger.info("ToneAgent initialized with Grok LLM client")
        except ImportError:
            logger.warning("LLMClient not available, ToneAgent will use fallback generation")
            self.llm_client = None
            self.use_api = False
            
    def generate_summary(self, 
                          analysis_results: Dict[str, Dict[str, Any]], 
                          final_decision: Dict[str, Any],
                          symbol: str = "BTC/USDT",
                          interval: str = "1h") -> Dict[str, Any]:
        """
        Generate a human-like styled summary of multi-agent trade decisions.
        
        Args:
            analysis_results: Results from each analyst agent
            final_decision: Final decision from the decision agent
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Dictionary containing agent comments, system summary, and mood
        """
        try:
            # Map from expected keys in analysis_results to agent names
            key_to_agent_map = {
                "technical_analysis": "TechnicalAnalystAgent",
                "sentiment_analysis": "SentimentAnalystAgent",
                "liquidity_analysis": "LiquidityAnalystAgent",
                "open_interest_analysis": "OpenInterestAnalystAgent",
                "funding_rate_analysis": "FundingRateAnalystAgent",
                "sentiment_aggregator": "SentimentAggregatorAgent"
            }
            
            # Build the prompt for the LLM
            prompt = self._build_generation_prompt(analysis_results, final_decision, key_to_agent_map, symbol, interval)
            
            # Generate the summary using the LLM
            if self.use_api and self.llm_client:
                logger.info("Generating summary using Grok API")
                summary = self._generate_with_llm(prompt, symbol, interval)
            else:
                logger.info("Generating summary using fallback method")
                summary = self._generate_fallback(analysis_results, final_decision, symbol, interval)
                
            # Save the summary to a file
            self._save_summary_to_file(summary, symbol)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            return self._generate_error_response(symbol, interval)
            
    def _build_generation_prompt(self, 
                                analysis_results: Dict[str, Dict[str, Any]], 
                                final_decision: Dict[str, Any],
                                key_to_agent_map: Dict[str, str],
                                symbol: str,
                                interval: str) -> str:
        """
        Build a prompt for the LLM to generate a summary.
        
        Args:
            analysis_results: Results from each analyst agent
            final_decision: Final decision from the decision agent
            key_to_agent_map: Mapping from analysis keys to agent names
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Prompt string for the LLM
        """
        # Extract current price from final decision
        current_price = final_decision.get("current_price", "unknown")
        signal = final_decision.get("signal", "UNKNOWN")
        confidence = final_decision.get("confidence", 0)
        directional_confidence = final_decision.get("directional_confidence", 0)
        conflict_score = final_decision.get("conflict_score", 0)
        
        prompt = f"""
You are the ToneAgent for aGENtrader v0.2.2, a multi-agent AI trading system. Your role is to generate human-like styled summaries of trading decisions.

Trading context:
- Symbol: {symbol}
- Interval: {interval}
- Current price: {current_price}
- Final decision: {signal} with {confidence}% confidence
- Directional confidence: {directional_confidence}%
- Conflict score: {conflict_score}

Agent analysis results:
"""
        
        # Add each agent's analysis to the prompt
        for key, analysis in analysis_results.items():
            agent_name = key_to_agent_map.get(key, key)
            agent_tone = self.agent_tones.get(agent_name, "Analytical and professional.")
            
            signal = analysis.get("signal", "UNKNOWN")
            confidence = analysis.get("confidence", 0)
            reasoning = analysis.get("reasoning", "No reasoning provided.")
            
            prompt += f"""
{agent_name}:
- Tone profile: {agent_tone}
- Signal: {signal}
- Confidence: {confidence}%
- Reasoning: {reasoning}
"""
        
        prompt += f"""
Final decision details:
{json.dumps(final_decision, indent=2)}

Task:
1. Generate one unique sentence for each agent in their characteristic tone representing their perspective.
2. Create an overall system summary that balances all views (2-3 sentences).
3. Assign a mood from: bullish, neutral, conflicted, cautious, euphoric

Respond ONLY with a valid JSON in this format:
{{
  "agent_comments": {{
    "AgentName1": "Their comment in their unique voice...",
    "AgentName2": "Their comment in their unique voice..."
  }},
  "system_summary": "Overall balanced market narrative...",
  "mood": "bullish|neutral|conflicted|cautious|euphoric"
}}
"""

        if confidence < 70 or signal == "CONFLICTED":
            prompt += "\nInclude a more cautious tone in the system summary since confidence is low or the decision is conflicted."
            
        return prompt
        
    def _generate_with_llm(self, prompt: str, symbol: str, interval: str) -> Dict[str, Any]:
        """
        Generate a summary using the LLM client.
        
        Args:
            prompt: Prompt for the LLM
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Dictionary containing agent comments, system summary, and mood
        """
        try:
            # Call the LLM with JSON response format
            start_time = datetime.now()
            try:
                # Try the new API format
                import openai
                
                # Check if we have an XAI API key in the environment
                xai_api_key = os.environ.get("XAI_API_KEY")
                
                if xai_api_key:
                    # Initialize a client for xAI using OpenAI-compatible client
                    xai_client = openai.OpenAI(base_url="https://api.x.ai/v1", api_key=xai_api_key)
                    
                    # Make the request using the OpenAI-compatible API
                    xai_response = xai_client.chat.completions.create(
                        model="grok-2-1212",
                        messages=[
                            {"role": "system", "content": "You are a trading summary expert for aGENtrader. Format your response as JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=1000,
                        temperature=0.7
                    )
                    
                    # Extract the content from the response
                    response = {"content": xai_response.choices[0].message.content}
                    logger.info("Successfully called xAI API with OpenAI-compatible client")
                else:
                    # Fall back to the original client if available
                    if self.llm_client and hasattr(self.llm_client, 'query'):
                        response = self.llm_client.query(
                            prompt=prompt,
                            model="grok-2-1212",
                            json_response=True,
                            max_tokens=1000,
                            temperature=0.7
                        )
                    else:
                        raise ValueError("No xAI API key and no compatible LLM client available")
            except Exception as e:
                logger.error(f"Error calling xAI API: {e}", exc_info=True)
                # Fall back to the original client if available
                if self.llm_client and hasattr(self.llm_client, 'query'):
                    response = self.llm_client.query(
                        prompt=prompt,
                        model="grok-2-1212",
                        json_response=True,
                        max_tokens=1000,
                        temperature=0.7
                    )
                else:
                    raise ValueError("Failed to call xAI API and no fallback LLM client available")
            end_time = datetime.now()
            
            # Log performance metrics
            duration = (end_time - start_time).total_seconds()
            logger.info(f"LLM call completed in {duration:.2f} seconds")
            
            # Parse the response
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                if isinstance(content, str):
                    try:
                        # Try to parse the content as JSON
                        summary = json.loads(content)
                        return summary
                    except json.JSONDecodeError:
                        logger.error("Failed to parse LLM response as JSON")
                        return self._generate_fallback(None, None, symbol, interval)
                elif isinstance(content, dict):
                    return content
            
            # If we got here, something went wrong
            logger.error(f"Unexpected LLM response format: {type(response)}")
            return self._generate_fallback(None, None, symbol, interval)
            
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}", exc_info=True)
            return self._generate_fallback(None, None, symbol, interval)
            
    def _generate_fallback(self, 
                           analysis_results: Optional[Dict[str, Dict[str, Any]]], 
                           final_decision: Optional[Dict[str, Any]],
                           symbol: str,
                           interval: str) -> Dict[str, Any]:
        """
        Generate a fallback summary when the LLM is not available.
        
        Args:
            analysis_results: Results from each analyst agent
            final_decision: Final decision from the decision agent
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Dictionary containing agent comments, system summary, and mood
        """
        logger.warning("Using fallback summary generation")
        
        # Create agent comments
        agent_comments = {}
        
        # If analysis_results is available, extract agent signals
        if analysis_results:
            signal_map = {
                "BUY": "bullish",
                "SELL": "bearish",
                "HOLD": "cautious",
                "NEUTRAL": "neutral",
                "UNKNOWN": "uncertain"
            }
            
            for key, analysis in analysis_results.items():
                agent_name = key.replace("_analysis", "").title() + "AnalystAgent"
                signal = analysis.get("signal", "UNKNOWN")
                mood = signal_map.get(signal, "neutral")
                
                if "technical" in key:
                    agent_comments[agent_name] = f"The indicators suggest a {mood} trend with moderate volume supporting the move."
                elif "sentiment" in key:
                    agent_comments[agent_name] = f"Market sentiment feels {mood} with social chatter increasingly focused on this direction."
                elif "liquidity" in key:
                    agent_comments[agent_name] = f"Order books show {mood} pressure with key levels forming around current price."
                elif "funding" in key:
                    agent_comments[agent_name] = f"Funding rates indicate {mood} bias in the derivatives market."
                elif "open_interest" in key:
                    agent_comments[agent_name] = f"Open interest patterns suggest a {mood} momentum building."
                else:
                    agent_comments[agent_name] = f"Analysis indicates a {mood} outlook based on available data."
        else:
            # Provide generic comments if no analysis data is available
            agent_comments = {
                "TechnicalAnalystAgent": "Charts are showing a potential trend change, but need confirmation.",
                "SentimentAnalystAgent": "Market mood is shifting but remains cautious overall.",
                "LiquidityAnalystAgent": "Order flow is balanced with support building at key levels.",
                "FundingRateAnalystAgent": "Funding shows balanced positioning with no excessive leverage.",
                "OpenInterestAnalystAgent": "Position changes remain muted, suggesting indecision."
            }
        
        # Determine overall mood from final decision
        mood = "neutral"
        if final_decision:
            signal = final_decision.get("signal", "UNKNOWN")
            confidence = final_decision.get("confidence", 0)
            conflict_score = final_decision.get("conflict_score", 0)
            
            if signal == "BUY" and confidence > 75:
                mood = "bullish"
            elif signal == "SELL" and confidence > 75:
                mood = "bearish"
            elif conflict_score > 60:
                mood = "conflicted"
            elif confidence < 60:
                mood = "cautious"
            
        # Create system summary
        if final_decision:
            signal = final_decision.get("signal", "UNKNOWN")
            confidence = final_decision.get("confidence", 0)
            
            if signal == "BUY":
                system_summary = f"Analysis suggests upward momentum for {symbol} with {confidence}% confidence based on technical and sentiment factors."
            elif signal == "SELL":
                system_summary = f"Conditions appear to favor downward movement for {symbol} with {confidence}% confidence, primarily due to technical indicators."
            elif signal == "HOLD":
                system_summary = f"Current market conditions suggest holding positions for {symbol} with limited directional bias at this time."
            elif signal == "NEUTRAL":
                system_summary = f"The market lacks clear direction for {symbol} with agents showing mixed signals. Recommend waiting for clearer setups."
            else:
                system_summary = f"Market conditions for {symbol} are uncertain. Consider reducing exposure until stronger signals emerge."
        else:
            system_summary = f"Market analysis for {symbol} shows mixed signals. Consider waiting for confirmation before taking action."
        
        # Construct the final summary
        summary = {
            "agent_comments": agent_comments,
            "system_summary": system_summary,
            "mood": mood
        }
        
        return summary
        
    def _save_summary_to_file(self, summary: Dict[str, Any], symbol: str) -> None:
        """
        Save the summary to a file.
        
        Args:
            summary: Summary dictionary
            symbol: Trading symbol
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize symbol for filename
            symbol_safe = symbol.replace("/", "_").replace("\\", "_").replace(":", "_")
            
            filename = f"tone_summary_{symbol_safe}_{timestamp}.json"
            filepath = os.path.join(self.log_dir, filename)
            
            with open(filepath, "w") as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Saved tone summary to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving summary to file: {str(e)}", exc_info=True)
            
    def _generate_error_response(self, symbol: str, interval: str) -> Dict[str, Any]:
        """
        Generate an error response when summary generation fails.
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            
        Returns:
            Dictionary containing error response
        """
        return {
            "agent_comments": {
                "TechnicalAnalystAgent": "Technical signals are unclear at this point.",
                "SentimentAnalystAgent": "Market sentiment is mixed with no clear direction.",
                "LiquidityAnalystAgent": "Order book shows balanced liquidity levels.",
                "OpenInterestAnalystAgent": "No significant change in market positions detected.",
                "FundingRateAnalystAgent": "Funding rates indicate neutral market expectations."
            },
            "system_summary": f"Unable to generate a complete analysis for {symbol} on {interval} timeframe. Consider waiting for clearer market conditions.",
            "mood": "cautious"
        }
        
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run the tone agent (wrapper for generate_summary).
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Dictionary containing agent comments, system summary, and mood
        """
        # Extract required parameters
        analysis_results = kwargs.get("analysis_results", {})
        final_decision = kwargs.get("final_decision", {})
        symbol = kwargs.get("symbol", "BTC/USDT")
        interval = kwargs.get("interval", "1h")
        
        return self.generate_summary(analysis_results, final_decision, symbol, interval)
    
    def print_styled_summary(self, summary: Dict[str, Any], symbol: str, interval: str) -> None:
        """
        Print a styled summary to the console.
        
        Args:
            summary: Summary dictionary
            symbol: Trading symbol
            interval: Time interval
        """
        try:
            # Check if colorama is available for better formatting
            try:
                from colorama import Fore, Style, init
                init(autoreset=True)
                colored_output = True
            except ImportError:
                colored_output = False
                
            # Define colors for colored output
            if colored_output:
                GREEN = Fore.GREEN
                YELLOW = Fore.YELLOW
                CYAN = Fore.CYAN
                MAGENTA = Fore.MAGENTA
                RED = Fore.RED
                WHITE = Fore.WHITE
                RESET = Style.RESET_ALL
            else:
                GREEN = YELLOW = CYAN = MAGENTA = RED = WHITE = RESET = ""
                
            # Print header
            print(f"\n{GREEN}{'=' * 80}{RESET}")
            print(f"{CYAN}🎙️ ToneAgent Summary — {symbol} ({interval}){RESET}")
            print(f"{GREEN}{'=' * 80}{RESET}")
            
            # Print agent comments
            agent_comments = summary.get("agent_comments", {})
            if agent_comments:
                print(f"\n{YELLOW}📣 Agent Voices:{RESET}")
                for agent, comment in agent_comments.items():
                    print(f"{MAGENTA}- {agent}:{RESET} \"{WHITE}{comment}{RESET}\"")
            
            # Print system summary
            system_summary = summary.get("system_summary", "")
            if system_summary:
                print(f"\n{YELLOW}🧠 Summary:{RESET} {WHITE}{system_summary}{RESET}")
            
            # Print mood
            mood = summary.get("mood", "neutral")
            mood_color = YELLOW
            if mood.lower() in ["bullish", "euphoric"]:
                mood_color = GREEN
            elif mood.lower() in ["bearish"]:
                mood_color = RED
            elif mood.lower() in ["cautious", "conflicted"]:
                mood_color = YELLOW
                
            print(f"\n{YELLOW}⚡ Market Mood:{RESET} {mood_color}{mood.capitalize()}{RESET}")
            print(f"{GREEN}{'=' * 80}{RESET}\n")
            
        except Exception as e:
            logger.error(f"Error printing styled summary: {str(e)}", exc_info=True)
            # Fallback to simple print
            print("\n=== ToneAgent Summary ===")
            print(json.dumps(summary, indent=2))
            print("========================\n")

def test_tone_agent():
    """
    Test the tone agent functionality.
    """
    # Sample analysis results
    analysis_results = {
        "technical_analysis": {
            "signal": "BUY",
            "confidence": 75,
            "reasoning": "Moving averages show bullish crossover and RSI indicates momentum."
        },
        "sentiment_analysis": {
            "signal": "BUY",
            "confidence": 80,
            "reasoning": "Social media sentiment has turned positive with increased mentions."
        },
        "liquidity_analysis": {
            "signal": "NEUTRAL",
            "confidence": 60,
            "reasoning": "Order book shows balanced buying and selling pressure."
        },
        "funding_rate_analysis": {
            "signal": "SELL",
            "confidence": 65,
            "reasoning": "Funding rates turning negative, indicating potential market exhaustion."
        },
        "open_interest_analysis": {
            "signal": "NEUTRAL",
            "confidence": 55,
            "reasoning": "Open interest has been flat over the past 24 hours."
        }
    }
    
    # Sample final decision
    final_decision = {
        "signal": "BUY",
        "confidence": 72,
        "directional_confidence": 65,
        "reason": "Bullish technical indicators with supportive sentiment.",
        "position_size": 0.15,
        "risk_score": 65,
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USDT",
        "current_price": 49876.32,
        "validity_period_hours": 24,
        "conflict_score": 35,
        "contributing_agents": ["TechnicalAnalystAgent", "SentimentAnalystAgent"],
        "strategy_tags": ["momentum_driven", "sentiment_aligned"],
        "risk_feedback": "Position size adjusted due to funding rate concerns"
    }
    
    # Initialize tone agent
    tone_agent = ToneAgent()
    
    # Generate summary
    summary = tone_agent.generate_summary(
        analysis_results=analysis_results,
        final_decision=final_decision,
        symbol="BTC/USDT",
        interval="4h"
    )
    
    # Print styled summary
    tone_agent.print_styled_summary(summary, "BTC/USDT", "4h")
    
    return summary

if __name__ == "__main__":
    test_tone_agent()