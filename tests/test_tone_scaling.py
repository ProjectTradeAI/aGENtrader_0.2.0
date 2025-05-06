#!/usr/bin/env python3
"""
Test script for ToneAgent dynamic tone scaling

This script tests the ToneAgent's dynamic tone scaling based on confidence levels
and handling of fallback/partial data.
"""
import os
import sys
import json
import logging
import random
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Import the ToneAgent
    from agents.tone_agent import ToneAgent
    
    # Function to create mock data with specific confidence level
    def create_mock_data(confidence_level="mixed", include_fallback=False):
        """
        Create mock data with specified confidence level and optional fallback data.
        
        Args:
            confidence_level: One of "high", "medium", "low", or "mixed"
            include_fallback: Whether to include fallback/partial data flags
            
        Returns:
            Tuple of (analysis_results, final_decision)
        """
        # Set confidence ranges based on level
        if confidence_level == "high":
            conf_range = (80, 100)
        elif confidence_level == "medium":
            conf_range = (60, 79)
        elif confidence_level == "low":
            conf_range = (30, 59)
        else:  # mixed
            conf_ranges = [(80, 100), (60, 79), (30, 59)]
        
        # Create analysis results with appropriate confidence levels
        analysis_results = {}
        
        # Technical analysis - Always normal data
        tech_conf = random.randint(*conf_range) if confidence_level != "mixed" else random.randint(*random.choice(conf_ranges))
        analysis_results["technical_analysis"] = {
            "signal": "BUY" if tech_conf > 50 else "HOLD",
            "confidence": tech_conf,
            "reasoning": "Technical indicators show potential upward momentum."
        }
        
        # Sentiment analysis - May be fallback
        sentiment_conf = random.randint(*conf_range) if confidence_level != "mixed" else random.randint(*random.choice(conf_ranges))
        analysis_results["sentiment_analysis"] = {
            "signal": "NEUTRAL",
            "confidence": sentiment_conf,
            "reasoning": "Mixed sentiment with slight bullish bias."
        }
        if include_fallback:
            analysis_results["sentiment_analysis"]["is_fallback"] = True
            analysis_results["sentiment_analysis"]["reasoning"] = "Limited sentiment data available due to API issues."
        
        # Liquidity analysis
        liquidity_conf = random.randint(*conf_range) if confidence_level != "mixed" else random.randint(*random.choice(conf_ranges))
        analysis_results["liquidity_analysis"] = {
            "signal": "HOLD",
            "confidence": liquidity_conf,
            "reasoning": "Normal liquidity conditions."
        }
        
        # Funding rate analysis
        funding_conf = random.randint(*conf_range) if confidence_level != "mixed" else random.randint(*random.choice(conf_ranges))
        analysis_results["funding_rate_analysis"] = {
            "signal": "NEUTRAL",
            "confidence": funding_conf,
            "reasoning": "Funding rates within normal range."
        }
        
        # Open interest analysis - May be partial data
        interest_conf = random.randint(*conf_range) if confidence_level != "mixed" else random.randint(*random.choice(conf_ranges))
        analysis_results["open_interest_analysis"] = {
            "signal": "BUY" if interest_conf > 60 else "NEUTRAL",
            "confidence": interest_conf,
            "reasoning": "Increasing open interest suggests accumulation."
        }
        if include_fallback:
            analysis_results["open_interest_analysis"]["is_partial"] = True
            analysis_results["open_interest_analysis"]["reasoning"] = "Partial data available, some exchanges not responding."
        
        # Create final decision
        # For simplicity, use the technical analysis confidence for the final decision
        signal = "BUY" if tech_conf > 60 else "HOLD"
        final_decision = {
            "signal": signal,
            "confidence": min(95, max(tech_conf, sentiment_conf, liquidity_conf, funding_conf, interest_conf) - 5),
            "conflict_score": 20 if confidence_level == "mixed" else 0,
            "reasoning": f"Overall {signal.lower()} signal with moderate confidence."
        }
        
        return analysis_results, final_decision
    
    # Run tests
    def run_tone_scaling_tests():
        """Run a series of tests for tone scaling."""
        
        logger.info(f"{Fore.CYAN}=== Testing ToneAgent Dynamic Tone Scaling ==={Style.RESET_ALL}")
        tone_agent = ToneAgent()
        test_symbol = "BTC/USDT"
        test_interval = "1h"
        
        # Test case 1: High confidence levels
        logger.info(f"{Fore.CYAN}\nTest Case 1: High Confidence Levels{Style.RESET_ALL}")
        high_analysis, high_decision = create_mock_data("high", False)
        high_summary = tone_agent.generate_summary(
            analysis_results=high_analysis,
            final_decision=high_decision,
            symbol=test_symbol,
            interval=test_interval
        )
        
        # Test case 2: Medium confidence levels
        logger.info(f"{Fore.CYAN}\nTest Case 2: Medium Confidence Levels{Style.RESET_ALL}")
        medium_analysis, medium_decision = create_mock_data("medium", False)
        medium_summary = tone_agent.generate_summary(
            analysis_results=medium_analysis,
            final_decision=medium_decision,
            symbol=test_symbol,
            interval=test_interval
        )
        
        # Test case 3: Low confidence levels
        logger.info(f"{Fore.CYAN}\nTest Case 3: Low Confidence Levels{Style.RESET_ALL}")
        low_analysis, low_decision = create_mock_data("low", False)
        low_summary = tone_agent.generate_summary(
            analysis_results=low_analysis,
            final_decision=low_decision,
            symbol=test_symbol,
            interval=test_interval
        )
        
        # Test case 4: Mixed confidence with fallback data
        logger.info(f"{Fore.CYAN}\nTest Case 4: Mixed Confidence with Fallback Data{Style.RESET_ALL}")
        fallback_analysis, fallback_decision = create_mock_data("mixed", True)
        fallback_summary = tone_agent.generate_summary(
            analysis_results=fallback_analysis,
            final_decision=fallback_decision,
            symbol=test_symbol,
            interval=test_interval
        )
        
        # Test case 5: Corrupted data (missing signals)
        logger.info(f"{Fore.CYAN}\nTest Case 5: Corrupted Data (Missing Signals){Style.RESET_ALL}")
        corrupted_analysis = {
            "technical_analysis": {},  # Empty dict
            "sentiment_analysis": None,  # None value
            "liquidity_analysis": {"confidence": 50}  # Missing signal
        }
        corrupted_decision = {"signal": "UNKNOWN", "confidence": 0}
        corrupted_summary = tone_agent.generate_summary(
            analysis_results=corrupted_analysis,
            final_decision=corrupted_decision,
            symbol=test_symbol,
            interval=test_interval
        )
        
        # Report test results
        logger.info(f"{Fore.CYAN}\n=== Test Results Summary ==={Style.RESET_ALL}")
        
        # Check for tone variations based on confidence
        high_tone_words = ["clearly", "definitely", "strong", "confident", "absolutely", "certain", "convincing"]
        medium_tone_words = ["reasonably", "moderately", "balanced", "adequate", "decent"]
        low_tone_words = ["perhaps", "might", "possibly", "tentative", "hesitant", "cautious"]
        fallback_tone_words = ["limited data", "partial information", "incomplete", "insufficient"]
        
        # Function to check if any word from a list appears in a text (case insensitive)
        def contains_any(text, word_list):
            text_lower = text.lower()
            return any(word.lower() in text_lower for word in word_list)
        
        # Check high confidence tone
        high_tone_correct = any(
            contains_any(comment, high_tone_words) 
            for agent, comment in high_summary.get("agent_comments", {}).items()
        )
        
        # Check medium confidence tone
        medium_tone_correct = any(
            contains_any(comment, medium_tone_words) 
            for agent, comment in medium_summary.get("agent_comments", {}).items()
        )
        
        # Check low confidence tone
        low_tone_correct = any(
            contains_any(comment, low_tone_words) 
            for agent, comment in low_summary.get("agent_comments", {}).items()
        )
        
        # Check fallback tone
        fallback_tone_correct = any(
            contains_any(comment, fallback_tone_words) 
            for agent, comment in fallback_summary.get("agent_comments", {}).items()
        )
        
        # Check corrupted data handling
        corrupted_handled = isinstance(corrupted_summary, dict) and "agent_comments" in corrupted_summary
        
        # Print results
        logger.info(f"High confidence tone test: {Fore.GREEN}PASS{Style.RESET_ALL}" if high_tone_correct else f"High confidence tone test: {Fore.RED}FAIL{Style.RESET_ALL}")
        logger.info(f"Medium confidence tone test: {Fore.GREEN}PASS{Style.RESET_ALL}" if medium_tone_correct else f"Medium confidence tone test: {Fore.RED}FAIL{Style.RESET_ALL}")
        logger.info(f"Low confidence tone test: {Fore.GREEN}PASS{Style.RESET_ALL}" if low_tone_correct else f"Low confidence tone test: {Fore.RED}FAIL{Style.RESET_ALL}")
        logger.info(f"Fallback data tone test: {Fore.GREEN}PASS{Style.RESET_ALL}" if fallback_tone_correct else f"Fallback data tone test: {Fore.RED}FAIL{Style.RESET_ALL}")
        logger.info(f"Corrupted data handling test: {Fore.GREEN}PASS{Style.RESET_ALL}" if corrupted_handled else f"Corrupted data handling test: {Fore.RED}FAIL{Style.RESET_ALL}")
        
        # Overall result
        all_passed = high_tone_correct and medium_tone_correct and low_tone_correct and fallback_tone_correct and corrupted_handled
        logger.info(f"\nOverall test result: {Fore.GREEN}ALL TESTS PASSED{Style.RESET_ALL}" if all_passed else f"\nOverall test result: {Fore.RED}SOME TESTS FAILED{Style.RESET_ALL}")
        
        return all_passed
    
    # Run the tests
    if __name__ == "__main__":
        run_tone_scaling_tests()
        
except ImportError as e:
    logger.error(f"{Fore.RED}Error importing required modules: {str(e)}{Style.RESET_ALL}")
except Exception as e:
    logger.error(f"{Fore.RED}Error during test: {str(e)}{Style.RESET_ALL}")