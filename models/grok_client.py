"""
Grok Client Module for aGENtrader v0.2.2

This module provides a client for interacting with xAI's Grok API,
following similar patterns to OpenAI's API structure.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union

import openai
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

class GrokClient:
    """
    Client for interacting with xAI's Grok API.
    
    This client follows similar patterns to OpenAI's API structure,
    making it familiar for developers who have worked with OpenAI's services.
    """
    
    def __init__(self):
        """Initialize the Grok client"""
        self.api_key = os.environ.get("XAI_API_KEY")
        self.base_url = "https://api.x.ai/v1"
        
        if not self.api_key:
            logger.warning("XAI_API_KEY not found in environment variables")
            
        self.client = None
        if self.api_key:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
    
    def is_available(self) -> bool:
        """
        Check if the Grok API is available
        
        Returns:
            bool: True if API key is configured, False otherwise
        """
        return self.client is not None
    
    def summarize_text(self, text: str) -> str:
        """
        Summarize text using Grok model
        
        Args:
            text: Text to summarize
            
        Returns:
            Summarized text
        """
        if not self.is_available():
            raise ValueError("Grok API is not available. Please check XAI_API_KEY.")
            
        prompt = f"Please summarize the following text concisely while maintaining key points:\n\n{text}"
        
        try:
            response = self.client.chat.completions.create(
                model="grok-2-1212",
                messages=[{"role": "user", "content": prompt}],
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error summarizing text with Grok: {e}")
            raise
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using Grok model
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self.is_available():
            raise ValueError("Grok API is not available. Please check XAI_API_KEY.")
            
        try:
            response = self.client.chat.completions.create(
                model="grok-2-1212",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze the sentiment of the text and provide a rating from 1 to 5 stars and a confidence score between 0 and 1. Respond with JSON in this format: { 'rating': number, 'confidence': number }"
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                response_format={"type": "json_object"},
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "rating": max(1, min(5, round(result.get("rating", 3)))),
                "confidence": max(0, min(1, result.get("confidence", 0.5))),
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Grok: {e}")
            raise
    
    def format_trade_summary(self, 
                            trade_plan: Dict[str, Any], 
                            agent_analyses: List[Dict[str, Any]],
                            system_prompt: Optional[str] = None,
                            style: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a stylized trade summary using Grok model
        
        Args:
            trade_plan: Dictionary containing trade plan details
            agent_analyses: List of dictionaries containing agent analyses
            system_prompt: Optional custom system prompt
            style: Optional style specification (formal, casual, technical)
            
        Returns:
            Dictionary containing formatted summary
        """
        if not self.is_available():
            raise ValueError("Grok API is not available. Please check XAI_API_KEY.")
            
        # Default system prompt if none provided
        if not system_prompt:
            system_prompt = (
                "You are a trading summary expert for aGENtrader. "
                "Your task is to create a summary of a trading decision with distinct voices for different analyst agents. "
                "Format your response as JSON with keys: agent_comments, system_summary, and mood."
            )
            
        # Add style guidance if provided
        if style:
            if style.lower() == "formal":
                system_prompt += " Use professional, precise language appropriate for financial reports."
            elif style.lower() == "casual":
                system_prompt += " Use conversational, accessible language as if explaining to a friend."
            elif style.lower() == "technical":
                system_prompt += " Use detailed technical language with specific trading terminology."
            
        # Create a structured prompt
        user_prompt = "Here is the trading plan and agent analyses to summarize:\n\n"
        user_prompt += f"TRADE PLAN: {json.dumps(trade_plan, indent=2)}\n\n"
        user_prompt += f"AGENT ANALYSES: {json.dumps(agent_analyses, indent=2)}\n\n"
        user_prompt += "Create a summary with these components:\n"
        user_prompt += "1. agent_comments: Comments from each agent with distinct voices\n"
        user_prompt += "2. system_summary: Overall trade summary and rationale\n"
        user_prompt += "3. mood: The overall market sentiment (bullish/bearish/neutral)"
        
        try:
            response = self.client.chat.completions.create(
                model="grok-2-1212",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure expected keys are present
            required_keys = ["agent_comments", "system_summary", "mood"]
            for key in required_keys:
                if key not in result:
                    result[key] = f"Missing {key} in response"
                    
            return result
            
        except Exception as e:
            logger.error(f"Error generating trade summary with Grok: {e}")
            # Return a basic fallback response
            return {
                "agent_comments": f"Error generating agent comments: {str(e)}",
                "system_summary": "Unable to generate summary due to API error",
                "mood": "neutral"
            }
    
    def analyze_image(self, base64_image: str) -> str:
        """
        Analyze image using Grok vision model
        
        Args:
            base64_image: Base64-encoded image
            
        Returns:
            Image analysis text
        """
        if not self.is_available():
            raise ValueError("Grok API is not available. Please check XAI_API_KEY.")
            
        try:
            response = self.client.chat.completions.create(
                model="grok-2-vision-1212",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image in detail and describe its key elements, context, and any notable aspects."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ],
                    },
                ],
                max_tokens=500,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing image with Grok: {e}")
            raise