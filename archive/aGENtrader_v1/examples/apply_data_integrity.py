"""
Apply Data Integrity Measures

This example demonstrates how to apply data integrity measures to analyst agents
in the trading system. It ensures agents explicitly communicate when they don't have
access to real data instead of providing simulated responses.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import data integrity module
try:
    from agents.data_integrity import ensure_data_integrity_for_agents, validate_data_response
except ImportError as e:
    logger.error(f"Error importing data integrity module: {str(e)}")
    sys.exit(1)

# Mock trading system for testing
class MockTradingSystem:
    """
    Mock trading system for testing data integrity modifications
    """
    
    def __init__(self):
        """Initialize the mock trading system with basic agents"""
        # Create mock agents with simple system messages
        self.agents = {
            "fundamental_analyst": MockAgent("Fundamental Analyst", """
You are a Fundamental Analyst for cryptocurrency trading.
Your job is to analyze on-chain metrics, exchange flows, and network statistics.
Provide insights on the fundamental health of the cryptocurrency.
"""),
            "sentiment_analyst": MockAgent("Sentiment Analyst", """
You are a Sentiment Analyst for cryptocurrency trading.
Your job is to analyze social media sentiment, news sentiment, and market mood.
Provide insights on the overall sentiment around the cryptocurrency.
"""),
            "technical_analyst": MockAgent("Technical Analyst", """
You are a Technical Analyst for cryptocurrency trading.
Your job is to analyze price charts, indicators, and patterns.
Provide technical analysis and trading recommendations.
""")
        }

class MockAgent:
    """
    Mock agent for testing data integrity modifications
    """
    
    def __init__(self, name: str, system_message: str):
        """
        Initialize the mock agent
        
        Args:
            name: Agent name
            system_message: Agent system message
        """
        self.name = name
        self.system_message = system_message
    
    def update_system_message(self, new_message: str):
        """
        Update the agent's system message
        
        Args:
            new_message: New system message
        """
        self.system_message = new_message
        logger.info(f"Updated system message for {self.name}")
    
    def generate_response(self, with_data: bool = True) -> str:
        """
        Generate a mock response from the agent
        
        Args:
            with_data: Whether the agent has access to data
            
        Returns:
            Agent response
        """
        if with_data:
            # Simulate a response with data
            if self.name == "Fundamental Analyst":
                return """
From a fundamental perspective:
1. On-chain metrics show accumulation by large holders (whales)
2. Exchange reserves have decreased by 3.2% over the past week
3. Network hash rate is at an all-time high, indicating strong security
4. Recent regulatory developments in EU markets are positive
"""
            elif self.name == "Sentiment Analyst":
                return """
Sentiment analysis indicates:
1. Social media sentiment is 68% positive, up 5% from last week
2. Trading forum activity shows increased interest in BTC
3. Fear & Greed Index is at 74, in the 'Greed' zone
4. News sentiment analysis shows positive coverage increasing
"""
            else:
                return "Technical analysis shows bullish patterns"
        else:
            # Generate a response without data based on data integrity instructions
            if "DATA INTEGRITY INSTRUCTIONS" in self.system_message:
                # Parse the system message to find the appropriate response for no data
                if "fundamental analysis" in self.system_message.lower():
                    return "I cannot provide fundamental analysis at this time due to lack of access to on-chain data sources. My input should NOT be counted in trading decisions."
                elif "sentiment analysis" in self.system_message.lower():
                    return "I cannot provide sentiment analysis at this time due to lack of access to sentiment data sources. My input should NOT be counted in trading decisions."
                else:
                    return "I cannot provide analysis at this time due to lack of access to data."
            else:
                # Without data integrity instructions, agent might still try to provide analysis
                if self.name == "Fundamental Analyst":
                    return "Based on recent on-chain activity, there appears to be growing adoption."
                elif self.name == "Sentiment Analyst":
                    return "Market sentiment seems positive based on social media indicators."
                else:
                    return "Technical indicators suggest a potential uptrend."

def demonstrate_data_integrity():
    """
    Demonstrate the effect of applying data integrity measures to agents
    """
    print("DEMONSTRATING DATA INTEGRITY MEASURES")
    print("====================================")
    
    # Create mock trading system
    print("\n1. Creating mock trading system with analyst agents...")
    trading_system = MockTradingSystem()
    
    # Show original responses (with and without data)
    print("\n2. Original agent responses:")
    print("\nWITH DATA ACCESS:")
    for name, agent in trading_system.agents.items():
        response = agent.generate_response(with_data=True)
        print(f"\n{agent.name}:")
        print(response)
    
    print("\nWITHOUT DATA ACCESS (before data integrity measures):")
    for name, agent in trading_system.agents.items():
        response = agent.generate_response(with_data=False)
        print(f"\n{agent.name}:")
        print(response)
    
    # Apply data integrity measures
    print("\n3. Applying data integrity measures to all analyst agents...")
    results = ensure_data_integrity_for_agents(trading_system)
    print("Results:", json.dumps(results, indent=2))
    
    # Show updated responses without data
    print("\n4. Agent responses WITHOUT DATA ACCESS (after data integrity measures):")
    for name, agent in trading_system.agents.items():
        response = agent.generate_response(with_data=False)
        print(f"\n{agent.name}:")
        print(response)
        
        # Validate the response
        if name in ["fundamental_analyst", "sentiment_analyst"]:
            analyst_type = name.split("_")[0]
            validation = validate_data_response(response, analyst_type)
            if validation["is_valid"]:
                print("✅ Response correctly discloses data unavailability")
            else:
                print("❌ Response does not properly disclose data unavailability")
    
    # Show the modified system messages
    print("\n5. Modified agent system messages:")
    for name, agent in trading_system.agents.items():
        print(f"\n{agent.name} System Message:")
        print(agent.system_message[:200] + "..." if len(agent.system_message) > 200 else agent.system_message)

def apply_to_real_trading_system():
    """
    Instructions for applying data integrity measures to a real trading system
    """
    print("\nAPPLYING TO YOUR REAL TRADING SYSTEM")
    print("====================================")
    print("""
To apply these data integrity measures to your actual trading system:

1. Import the data integrity module:
   from agents.data_integrity import ensure_data_integrity_for_agents

2. Apply to your trading system:
   results = ensure_data_integrity_for_agents(your_trading_system)

3. This will update all analyst agents to properly communicate when data is unavailable

4. Add this step to your trading system initialization to ensure data integrity
   is always maintained

5. When providing API keys or real data sources later, the agents will seamlessly
   switch to using real data while maintaining proper disclosure for any unavailable data
""")

def main():
    """Main entry point"""
    # Demonstrate data integrity measures
    demonstrate_data_integrity()
    
    # Show how to apply to real trading system
    apply_to_real_trading_system()

if __name__ == "__main__":
    main()