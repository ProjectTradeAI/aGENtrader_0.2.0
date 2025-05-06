#!/usr/bin/env python3
"""
Test script for ToneAgent fallback generator with dynamic tone scaling

This script tests the ToneAgent's fallback summary generator with dynamic tone scaling.
"""
import os
import sys
import json
import logging
from datetime import datetime

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
    
    def test_fallback_summary():
        """Test the fallback summary generator with dynamic tone scaling."""
        
        logger.info("=== Testing ToneAgent Fallback Generator with Dynamic Tone Scaling ===")
        
        # Create a ToneAgent
        tone_agent = ToneAgent()
        
        # Create test data for different confidence levels
        test_cases = [
            {
                "name": "High Confidence",
                "analysis_results": {
                    "technical_analysis": {
                        "signal": "BUY", 
                        "confidence": 90,
                        "reasoning": "Strong technical indicators"
                    },
                    "sentiment_analysis": {
                        "signal": "NEUTRAL",
                        "confidence": 85,
                        "reasoning": "Mixed sentiment with bullish bias"
                    }
                },
                "final_decision": {
                    "signal": "BUY",
                    "confidence": 88,
                    "reasoning": "Technical signal with moderate sentiment support"
                }
            },
            {
                "name": "Medium Confidence",
                "analysis_results": {
                    "technical_analysis": {
                        "signal": "SELL", 
                        "confidence": 70,
                        "reasoning": "Bearish technical indicators"
                    },
                    "sentiment_analysis": {
                        "signal": "NEUTRAL",
                        "confidence": 65,
                        "reasoning": "Slightly negative sentiment"
                    }
                },
                "final_decision": {
                    "signal": "SELL",
                    "confidence": 65,
                    "reasoning": "Bearish technical signals"
                }
            },
            {
                "name": "Low Confidence",
                "analysis_results": {
                    "technical_analysis": {
                        "signal": "HOLD", 
                        "confidence": 40,
                        "reasoning": "Unclear technicals"
                    },
                    "sentiment_analysis": {
                        "signal": "HOLD",
                        "confidence": 55,
                        "reasoning": "Uncertain sentiment"
                    }
                },
                "final_decision": {
                    "signal": "HOLD",
                    "confidence": 45,
                    "reasoning": "Uncertainty in both technicals and sentiment"
                }
            },
            {
                "name": "Fallback Data",
                "analysis_results": {
                    "technical_analysis": {
                        "signal": "BUY", 
                        "confidence": 60,
                        "reasoning": "Limited technical data",
                        "is_fallback": True
                    },
                    "sentiment_analysis": {
                        "signal": "NEUTRAL",
                        "confidence": 50,
                        "reasoning": "Partial sentiment data",
                        "is_partial": True
                    }
                },
                "final_decision": {
                    "signal": "HOLD",
                    "confidence": 40,
                    "reasoning": "Limited data requires caution"
                }
            }
        ]
        
        # Run tests
        results = []
        
        for test_case in test_cases:
            logger.info(f"\n--- Testing {test_case['name']} ---")
            
            # Call the fallback generator directly to ensure it's used
            summary = tone_agent._generate_fallback_summary(
                analysis_results=test_case["analysis_results"],
                final_decision=test_case["final_decision"],
                symbol="BTC/USDT",
                interval="1h"
            )
            
            # Log the result
            logger.info(f"Summary for {test_case['name']}:")
            for agent, comment in summary.get("agent_comments", {}).items():
                logger.info(f"- {agent}: \"{comment}\"")
            logger.info(f"System summary: {summary.get('system_summary', '')}")
            logger.info(f"Mood: {summary.get('mood', '')}")
            
            # Store result for analysis
            results.append({
                "test_case": test_case["name"],
                "confidence": test_case["final_decision"]["confidence"],
                "summary": summary
            })
        
        # Check tone variations in results
        logger.info("\n=== Analysis of Tone Scaling in Fallback Summaries ===")
        
        high_tone_words = ["decisively", "confidently", "absolutely", "clearly", "without a doubt", "strong"]
        medium_tone_words = ["moderately", "reasonably", "it appears", "suggests", "believe", "decent"]
        low_tone_words = ["tentatively", "hesitantly", "perhaps", "hint", "sensing", "possible"]
        fallback_tone_words = ["limited data", "partial information", "minimal signals", "incomplete"]
        
        for result in results:
            # Check tone scaling in agent comments
            tone_types_found = []
            
            for comment in result["summary"]["agent_comments"].values():
                comment_lower = comment.lower()
                
                if any(word in comment_lower for word in high_tone_words):
                    tone_types_found.append("high confidence")
                if any(word in comment_lower for word in medium_tone_words):
                    tone_types_found.append("medium confidence")
                if any(word in comment_lower for word in low_tone_words):
                    tone_types_found.append("low confidence")
                if any(word in comment_lower for word in fallback_tone_words):
                    tone_types_found.append("fallback/partial data")
            
            # Check system summary tone scaling
            system_summary = result["summary"]["system_summary"].lower()
            if any(word in system_summary for word in high_tone_words):
                tone_types_found.append("high confidence system")
            if any(word in system_summary for word in medium_tone_words):
                tone_types_found.append("medium confidence system")
            if any(word in system_summary for word in low_tone_words):
                tone_types_found.append("low confidence system")
            
            # Determine expected tone based on confidence
            confidence = result["confidence"]
            expected_tone = "high" if confidence >= 80 else "medium" if confidence >= 60 else "low"
            
            # Log findings
            logger.info(f"Test case: {result['test_case']} (Confidence: {confidence}%)")
            logger.info(f"Expected primary tone: {expected_tone} confidence")
            logger.info(f"Tone types found: {', '.join(set(tone_types_found))}")
            logger.info("---")
        
        logger.info("\nTest completed.")
        
        return results
        
    if __name__ == "__main__":
        test_fallback_summary()
        
except ImportError as e:
    logger.error(f"Error importing required modules: {str(e)}")
except Exception as e:
    logger.error(f"Error during test: {str(e)}")