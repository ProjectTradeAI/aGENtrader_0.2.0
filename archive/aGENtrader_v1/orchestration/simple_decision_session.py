#!/usr/bin/env python3
"""
Simple Decision Session with Local TinyLlama

This module provides a simplified decision-making session using 
the local TinyLlama model directly without the complexity of AutoGen.
"""
import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for importing utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simple_decision")

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
    logger.info("Llama-cpp-python is available for local LLM inference")
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("Llama-cpp-python is not installed. Local LLM will not be available.")

# Global model instance for reuse
_MODEL_INSTANCE = None

class SimpleDecisionSession:
    """
    A simplified decision session using the local LLM directly.
    """
    
    def __init__(self):
        """Initialize the decision session."""
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = os.path.join("data", "decisions")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize model
        self.model = None
        self.model_loaded = self._load_model()
    
    def _load_model(self) -> bool:
        """
        Load the TinyLlama model.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        global _MODEL_INSTANCE
        
        # For now, we'll always return False to use the fallback decision process
        # This is because we're having issues with the llama-cpp-python library
        logger.warning("Currently using fallback decision process without LLM")
        return False
        
        # The below code is kept for reference but not used
        """
        if not LLAMA_CPP_AVAILABLE:
            logger.error("Llama-cpp-python is not installed. Cannot load local LLM.")
            return False
            
        # If model already loaded globally, use it
        if _MODEL_INSTANCE is not None:
            self.model = _MODEL_INSTANCE
            return True
            
        # Otherwise, load the model
        try:
            # Check common locations for TinyLlama model
            potential_paths = [
                "./models/tinyllama.gguf",
                "./models/TinyLlama-1.1B-Chat-v1.0.Q5_K_M.gguf",
                "/models/tinyllama.gguf",
                "/models/TinyLlama-1.1B-Chat-v1.0.Q5_K_M.gguf",
                # Add paths found in the system
                "/home/runner/workspace/models/llm_models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "/home/runner/workspace/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/52e7645ba7c309695bec7ac98f4f005b139cf465/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
            ]
            
            model_path = None
            for path in potential_paths:
                if os.path.exists(path):
                    model_path = path
                    logger.info(f"Found TinyLlama model at {path}")
                    break
                    
            if model_path is None:
                logger.error("No model found at any known location")
                return False
            
            # Configure model parameters
            model_params = {
                "n_ctx": 2048,           # Context window size
                "n_threads": 4,           # Use 4 threads
                "n_batch": 512,           # Batch size for prompt processing
                "verbose": False,         # Don't show verbose outputs
            }
            
            logger.info(f"Loading model from {model_path}")
            logger.info(f"Model parameters: {model_params}")
            
            # Load the model
            self.model = Llama(model_path=model_path, **model_params)
            
            # Store model globally
            _MODEL_INSTANCE = self.model
            
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        """
    
    def run_decision(self, symbol: str, interval: str = '1h', 
                   current_price: float = None, market_data: Dict = None,
                   analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Run a trading decision.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe interval
            current_price: Current price of the asset
            market_data: Market data for analysis
            analysis_type: Type of analysis to perform
            
        Returns:
            Decision data
        """
        timestamp = datetime.datetime.utcnow()
        
        # Check if model is loaded
        if not self.model_loaded or self.model is None:
            logger.error("Model not loaded, cannot run decision")
            return self._fallback_decision(symbol, interval, current_price, timestamp)
        
        try:
            # Format the prompt
            market_info = self._format_market_data(symbol, interval, current_price, market_data)
            
            prompt = f"""<|system|>
You are an expert cryptocurrency trading advisor specializing in {symbol}. 
Your task is to analyze the market data and provide a trading decision.
Your final decision MUST be one of: BUY, SELL, or HOLD with a confidence score from 0.0 to 1.0.
You should provide a brief rationale for your decision.

<|user|>
I need a trading decision for {symbol} on the {interval} timeframe.
Current timestamp: {timestamp.isoformat()}
Current price: ${current_price if current_price else 'Unknown'}

{market_info}

Please provide a concise trading decision with the following format:
1. Analysis of the price action
2. Key support and resistance levels
3. Market sentiment analysis 
4. Final decision with confidence score
5. Stop loss and take profit recommendations

<|assistant|>
"""

            # Generate response from model
            logger.info(f"Generating trading decision for {symbol} at {current_price}")
            
            response = self.model.create_completion(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.4,
                stop=["<|user|>", "<|system|>"],
                repeat_penalty=1.2
            )
            
            # Extract response text
            response_text = response["choices"][0]["text"].strip()
            
            logger.info(f"Generated response of {len(response_text)} chars")
            
            # Extract decision from response
            decision = self._extract_decision(response_text)
            
            # Create decision data
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
                },
                "full_analysis": response_text
            }
            
            # Save decision to file
            self._save_decision(decision_data)
            
            return decision_data
            
        except Exception as e:
            logger.error(f"Error in decision making: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Use fallback in case of error
            return self._fallback_decision(symbol, interval, current_price, timestamp)
    
    def _extract_decision(self, text: str) -> Dict[str, Any]:
        """
        Extract decision from response text.
        
        Args:
            text: Response text from LLM
            
        Returns:
            Decision dictionary
        """
        # Default values
        action = "HOLD"
        confidence = 0.5
        reasoning = "Analysis inconclusive"
        timeframe = "short-term"
        stop_loss_percent = 5.0
        take_profit_percent = 10.0
        
        # Look for action keywords
        text_upper = text.upper()
        if "DECISION: BUY" in text_upper or "FINAL DECISION: BUY" in text_upper:
            action = "BUY"
        elif "DECISION: SELL" in text_upper or "FINAL DECISION: SELL" in text_upper:
            action = "SELL"
        elif "DECISION: HOLD" in text_upper or "FINAL DECISION: HOLD" in text_upper:
            action = "HOLD"
        else:
            # Fallback to keyword counting
            buy_count = text_upper.count("BUY")
            sell_count = text_upper.count("SELL")
            hold_count = text_upper.count("HOLD")
            
            if buy_count > sell_count and buy_count > hold_count:
                action = "BUY"
            elif sell_count > buy_count and sell_count > hold_count:
                action = "SELL"
            else:
                action = "HOLD"
        
        # Try to extract confidence score
        try:
            # Look for confidence mentions
            confidence_idx = text.lower().find("confidence")
            if confidence_idx >= 0:
                # Extract the line with confidence
                end_idx = text.find("\n", confidence_idx)
                if end_idx < 0:
                    end_idx = len(text)
                confidence_line = text[confidence_idx:end_idx]
                
                # Extract numbers from the line
                import re
                numbers = re.findall(r"0\.\d+", confidence_line)
                if numbers:
                    confidence = float(numbers[0])
                    # Ensure confidence is between 0 and 1
                    confidence = max(0.0, min(1.0, confidence))
        except Exception as e:
            logger.warning(f"Error extracting confidence: {str(e)}")
        
        # Try to extract reasoning
        try:
            reasoning_idx = text.lower().find("reason")
            if reasoning_idx >= 0:
                # Extract a few lines after reasoning
                end_idx = text.find("\n\n", reasoning_idx)
                if end_idx < 0:
                    end_idx = len(text)
                reasoning = text[reasoning_idx:end_idx].strip()
                # Truncate if too long
                if len(reasoning) > 200:
                    reasoning = reasoning[:200] + "..."
            else:
                # Use the last paragraph as reasoning
                paragraphs = text.split("\n\n")
                if paragraphs:
                    reasoning = paragraphs[-1].strip()
                    # Truncate if too long
                    if len(reasoning) > 200:
                        reasoning = reasoning[:200] + "..."
        except Exception as e:
            logger.warning(f"Error extracting reasoning: {str(e)}")
        
        # Try to extract stop loss and take profit
        try:
            # Look for stop loss mentions
            sl_idx = text.lower().find("stop loss")
            if sl_idx >= 0:
                sl_line = text[sl_idx:text.find("\n", sl_idx) if text.find("\n", sl_idx) >= 0 else len(text)]
                sl_numbers = re.findall(r"\d+\.?\d*%?", sl_line)
                if sl_numbers:
                    # Remove % sign if present and convert to float
                    sl_value = float(sl_numbers[0].replace("%", ""))
                    if sl_value > 0 and sl_value < 50:  # Sanity check
                        stop_loss_percent = sl_value
                        
            # Look for take profit mentions
            tp_idx = text.lower().find("take profit")
            if tp_idx >= 0:
                tp_line = text[tp_idx:text.find("\n", tp_idx) if text.find("\n", tp_idx) >= 0 else len(text)]
                tp_numbers = re.findall(r"\d+\.?\d*%?", tp_line)
                if tp_numbers:
                    # Remove % sign if present and convert to float
                    tp_value = float(tp_numbers[0].replace("%", ""))
                    if tp_value > 0 and tp_value < 100:  # Sanity check
                        take_profit_percent = tp_value
        except Exception as e:
            logger.warning(f"Error extracting stop loss/take profit: {str(e)}")
        
        # Create the decision dictionary
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "timeframe": timeframe,
            "stop_loss_percent": stop_loss_percent,
            "take_profit_percent": take_profit_percent
        }
    
    def _format_market_data(self, symbol: str, interval: str, 
                          current_price: Optional[float], 
                          market_data: Optional[Dict]) -> str:
        """
        Format market data for the prompt.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe interval
            current_price: Current price
            market_data: Market data dictionary
            
        Returns:
            Formatted market data string
        """
        result = "Market Information:\n"
        
        if current_price:
            result += f"- Current Price: ${current_price}\n"
        
        if market_data:
            # Format provided market data
            if "recent_prices" in market_data:
                result += "- Recent Prices:\n"
                for timestamp, price in market_data["recent_prices"][-5:]:  # Last 5 prices
                    result += f"  * {timestamp}: ${price}\n"
            
            if "volume_24h" in market_data:
                result += f"- 24h Volume: ${market_data['volume_24h']:,.2f}\n"
            
            if "change_24h" in market_data:
                result += f"- 24h Change: {market_data['change_24h']:.2f}%\n"
            
            # Add more technical indicators if available
            if "recent_data" in market_data and len(market_data["recent_data"]) > 0:
                # Calculate some basic indicators
                recent_data = market_data["recent_data"]
                
                # Calculate simple moving averages if enough data
                if len(recent_data) >= 20:
                    # MA7
                    ma7 = sum(candle["close"] for candle in recent_data[-7:]) / 7
                    # MA20
                    ma20 = sum(candle["close"] for candle in recent_data[-20:]) / 20
                    
                    result += f"- Simple Moving Averages:\n"
                    result += f"  * MA7: ${ma7:.2f}\n"
                    result += f"  * MA20: ${ma20:.2f}\n"
                    
                    if ma7 > ma20:
                        result += f"  * MA7 is above MA20 (bullish)\n"
                    else:
                        result += f"  * MA7 is below MA20 (bearish)\n"
                    
                # Calculate basic RSI if enough data
                if len(recent_data) >= 14:
                    closes = [candle["close"] for candle in recent_data[-15:]]
                    gains = []
                    losses = []
                    
                    for i in range(1, len(closes)):
                        change = closes[i] - closes[i-1]
                        if change >= 0:
                            gains.append(change)
                            losses.append(0)
                        else:
                            gains.append(0)
                            losses.append(abs(change))
                    
                    avg_gain = sum(gains) / len(gains)
                    avg_loss = sum(losses) / len(losses)
                    
                    if avg_loss == 0:
                        rsi = 100
                    else:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    
                    result += f"- Relative Strength Index (RSI): {rsi:.2f}\n"
        
        return result
    
    def _fallback_decision(self, symbol: str, interval: str, 
                         current_price: Optional[float], 
                         timestamp: datetime.datetime) -> Dict[str, Any]:
        """
        Generate a fallback decision when model is not available.
        
        Args:
            symbol: Trading symbol
            interval: Timeframe interval
            current_price: Current price
            timestamp: Current timestamp
            
        Returns:
            Decision data
        """
        logger.info("Using fallback decision strategy")
        
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
                
            logger.info(f"Decision saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving decision: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())