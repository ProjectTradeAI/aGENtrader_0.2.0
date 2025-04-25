#!/usr/bin/env python3
"""
Fix Decision Session Implementation

This script fixes the DecisionSession class to use the full agent framework
instead of the simplified version.
"""
import os
import sys
import inspect
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'fix_decision_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("fix_decision_session")

def get_decision_session_path():
    """Get the path to the decision_session.py file"""
    # Try to locate orchestration/decision_session.py
    base_path = os.getcwd()
    decision_session_path = os.path.join(base_path, 'orchestration', 'decision_session.py')
    
    if os.path.exists(decision_session_path):
        return decision_session_path
    
    # Search for it
    for root, dirs, files in os.walk(base_path):
        if 'decision_session.py' in files:
            path = os.path.join(root, 'decision_session.py')
            logger.info(f"Found decision_session.py at: {path}")
            return path
    
    return None

def backup_file(file_path):
    """Backup a file before modifying it"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up file to: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup file: {e}")
        return False

def has_agent_imports(file_content):
    """Check if the file already has necessary agent imports"""
    required_imports = [
        "import autogen",
        "from autogen import AssistantAgent",
        "from autogen import UserProxyAgent",
        "from autogen import GroupChat",
        "from autogen import GroupChatManager"
    ]
    
    for imp in required_imports:
        if imp in file_content:
            return True
    
    return False

def add_agent_imports(file_content):
    """Add necessary imports for agents"""
    new_imports = """
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from typing import Dict, List, Any, Optional, Union
import logging
"""
    
    # Find a good place to add imports
    import_section_end = 0
    lines = file_content.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_section_end = i + 1
    
    # Add imports after other imports
    updated_lines = lines[:import_section_end] + [new_imports] + lines[import_section_end:]
    return '\n'.join(updated_lines)

def add_agent_class_properties(file_content):
    """Add agent-related properties to the DecisionSession class"""
    # Define the properties to add
    class_properties = """
    # Agent-related properties
    llm_config: Dict[str, Any] = {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "config_list": [{"api_key": os.environ.get("OPENAI_API_KEY", "")}],
    }
    technical_analyst = None
    fundamental_analyst = None
    portfolio_manager = None
    agents = []
    group_chat = None
    manager = None
"""
    
    # Find the class definition
    class_def_pattern = "class DecisionSession"
    
    if class_def_pattern not in file_content:
        logger.error("Could not find DecisionSession class definition")
        return file_content
    
    # Find the __init__ method
    init_method_pattern = "def __init__"
    
    if init_method_pattern not in file_content:
        logger.error("Could not find __init__ method")
        return file_content
    
    # Add properties before __init__
    file_content = file_content.replace(
        class_def_pattern, 
        class_def_pattern + class_properties
    )
    
    return file_content

def add_init_agent_method(file_content):
    """Add a method to initialize agents"""
    init_agents_method = """
    def init_agents(self):
        """Initialize autogen agents for the decision session"""
        if not self.agents:
            logger.info("Initializing agents for decision session")
            
            # Configure the language model
            if not os.environ.get("OPENAI_API_KEY"):
                logger.warning("OPENAI_API_KEY not set. Agents may not function properly.")
            
            # Create the agents
            self.technical_analyst = AssistantAgent(
                name="TechnicalAnalyst",
                system_message='''You are a Technical Analyst specializing in cryptocurrency markets.
                Your role is to analyze price patterns, trends, support/resistance levels, and technical indicators.
                Focus on providing actionable insights based on technical analysis.''',
                llm_config=self.llm_config
            )
            
            self.fundamental_analyst = AssistantAgent(
                name="FundamentalAnalyst",
                system_message='''You are a Fundamental Analyst specializing in cryptocurrency markets.
                Your role is to analyze market sentiment, on-chain metrics, macroeconomic factors, and news.
                Focus on providing actionable insights based on fundamental analysis.''',
                llm_config=self.llm_config
            )
            
            self.portfolio_manager = AssistantAgent(
                name="PortfolioManager",
                system_message='''You are a Portfolio Manager specializing in cryptocurrency trading.
                Your role is to make the final decision about trading actions based on technical and fundamental analysis.
                Consider risk management, position sizing, and market conditions to provide a clear buy/sell/hold decision with confidence level.''',
                llm_config=self.llm_config
            )
            
            self.human_proxy = UserProxyAgent(
                name="DecisionCoordinator",
                system_message="Coordinate the discussion about the trading decision for the cryptocurrency.",
                code_execution_config=False,
                human_input_mode="NEVER"
            )
            
            # Add agents to the list
            self.agents = [
                self.technical_analyst,
                self.fundamental_analyst,
                self.portfolio_manager,
                self.human_proxy
            ]
            
            # Create a group chat
            self.group_chat = GroupChat(
                agents=self.agents,
                messages=[],
                max_round=5
            )
            
            # Create a manager for the group chat
            self.manager = GroupChatManager(
                groupchat=self.group_chat,
                llm_config=self.llm_config
            )
            
            logger.info("Agents initialized successfully")
        else:
            logger.info("Agents already initialized")
"""
    
    # Find a good place to add the method (after __init__ method)
    init_pattern = "def __init__"
    
    if init_pattern not in file_content:
        logger.error("Could not find __init__ method to add init_agents after")
        return file_content
    
    # Find the end of the __init__ method
    lines = file_content.split('\n')
    init_start = -1
    init_end = -1
    
    for i, line in enumerate(lines):
        if init_pattern in line:
            init_start = i
            break
    
    if init_start == -1:
        logger.error("Could not find __init__ method to add init_agents after")
        return file_content
    
    # Find the end of the __init__ method by tracking indentation
    if init_start >= 0:
        init_indent = len(lines[init_start]) - len(lines[init_start].lstrip())
        for i in range(init_start + 1, len(lines)):
            if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) <= init_indent:
                init_end = i
                break
        if init_end == -1:  # If we reached the end of the file
            init_end = len(lines)
    
    if init_end == -1:
        logger.error("Could not determine the end of __init__ method")
        return file_content
    
    # Add init_agents method after __init__
    updated_lines = lines[:init_end] + [init_agents_method] + lines[init_end:]
    
    return '\n'.join(updated_lines)

def update_run_session_method(file_content):
    """Update the run_session method to use the full agent framework"""
    # Define the new run_session method
    new_run_session = """
    def run_session(self, symbol=None, current_price=None):
        """Run a decision session with the full agent framework"""
        symbol = symbol or self.symbol
        logger.info(f"Running decision session for {symbol} at price {current_price}")
        
        # Initialize agents if not already done
        if not self.agents:
            self.init_agents()
        
        try:
            # Create a market summary for the agents
            market_summary = self._get_market_summary(symbol, current_price)
            
            # Set up the chat prompt
            prompt = f'''
            Trading Decision Required for {symbol} at ${current_price}
            
            Current Market Summary:
            {market_summary}
            
            TechnicalAnalyst: Please analyze the technical aspects of {symbol}.
            FundamentalAnalyst: Please analyze the fundamental factors for {symbol}.
            PortfolioManager: After hearing from the analysts, make a final decision (BUY/SELL/HOLD)
            with a confidence level (0.0-1.0) and clear reasoning.
            
            The final output should include:
            - Action: (BUY/SELL/HOLD)
            - Confidence: (0.0-1.0)
            - Reasoning: (A clear explanation)
            '''
            
            # Run the group chat
            logger.info(f"Initiating agent discussion for {symbol}")
            chat_result = self.human_proxy.initiate_chat(
                self.manager,
                message=prompt
            )
            
            # Extract the decision from the chat result
            # Get the last message from PortfolioManager
            decision = self._extract_decision_from_chat(chat_result)
            
            logger.info(f"Decision for {symbol}: {decision['action']} (Confidence: {decision['confidence']})")
            
            return {
                "status": "completed",
                "decision": decision,
                "session_id": self.session_id,
                "full_chat": chat_result
            }
        
        except Exception as e:
            logger.error(f"Error in agent-based decision process: {e}")
            logger.error("Falling back to simplified decision logic")
            
            # Fallback to simplified logic if the agent framework fails
            decision = {
                "action": "HOLD",
                "confidence": 0.5,
                "price": current_price,
                "reasoning": f"Fallback decision due to agent framework error: {str(e)}"
            }
            
            return {
                "status": "error",
                "decision": decision,
                "session_id": self.session_id,
                "error": str(e)
            }
"""
    
    # Replace the existing run_session method
    method_pattern = "def run_session"
    method_end_pattern = "def "
    
    if method_pattern not in file_content:
        logger.error("Could not find run_session method in file")
        return file_content
    
    # Find the run_session method
    method_start = file_content.find(method_pattern)
    
    if method_start == -1:
        logger.error("Could not find run_session method")
        return file_content
    
    # Find the end of the method (next method definition)
    method_end = file_content.find(method_end_pattern, method_start + len(method_pattern))
    
    if method_end == -1:  # If this is the last method in the file
        # Find end of class (next class definition)
        class_end = file_content.find("class ", method_start + len(method_pattern))
        
        if class_end == -1:  # If this is the last class in the file
            method_code = file_content[method_start:]
            updated_content = file_content[:method_start] + new_run_session
        else:
            method_code = file_content[method_start:class_end]
            updated_content = file_content[:method_start] + new_run_session + file_content[class_end:]
    else:
        method_code = file_content[method_start:method_end]
        updated_content = file_content[:method_start] + new_run_session + file_content[method_end:]
    
    logger.info(f"Replaced run_session method:\n{method_code}\n\nWith:\n{new_run_session}")
    
    return updated_content

def add_helper_methods(file_content):
    """Add helper methods for the run_session method"""
    # Define helper methods
    helper_methods = """
    def _get_market_summary(self, symbol, current_price):
        """Get a market summary for the trading decision"""
        # Insert code to fetch real market data from database
        # This is a placeholder that can be enhanced to include real data
        return f'''
        Symbol: {symbol}
        Current Price: ${current_price}
        
        Recent market data for {symbol} shows the current price at ${current_price}.
        Please analyze the technical and fundamental factors to make a trading decision.
        '''
    
    def _extract_decision_from_chat(self, chat_result):
        """Extract the decision from the chat result"""
        # Get messages from chat result
        messages = chat_result.get("messages", [])
        
        # Find the last message from PortfolioManager
        portfolio_manager_messages = [
            m for m in messages 
            if isinstance(m, dict) and m.get("role") == "assistant" and "PortfolioManager" in m.get("content", "")
        ]
        
        if portfolio_manager_messages:
            last_pm_message = portfolio_manager_messages[-1]
            content = last_pm_message.get("content", "")
            
            # Try to parse the decision
            action = "HOLD"  # Default
            confidence = 0.5  # Default
            reasoning = "No clear reasoning provided"
            
            # Simple parsing logic - can be made more robust
            if "BUY" in content.upper():
                action = "BUY"
            elif "SELL" in content.upper():
                action = "SELL"
            elif "HOLD" in content.upper():
                action = "HOLD"
            
            # Try to extract confidence
            import re
            confidence_patterns = [
                r"confidence:?\s*(0\.\d+)",
                r"confidence:?\s*(\d+)%",
                r"confidence\s+level:?\s*(0\.\d+)",
                r"confidence\s+level:?\s*(\d+)%"
            ]
            
            for pattern in confidence_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    confidence_str = match.group(1)
                    try:
                        if "%" in confidence_str:
                            confidence = float(confidence_str.replace("%", "")) / 100
                        else:
                            confidence = float(confidence_str)
                        break
                    except:
                        pass
            
            # Extract reasoning - everything after "reasoning:" or similar
            reasoning_patterns = [
                r"reasoning:?\s*(.+)$",
                r"rationale:?\s*(.+)$",
                r"because:?\s*(.+)$"
            ]
            
            for pattern in reasoning_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    reasoning = match.group(1).strip()
                    break
            
            return {
                "action": action,
                "confidence": confidence,
                "price": None,  # Will be filled in by the calling code
                "reasoning": reasoning
            }
        
        # Fallback if no valid decision was found
        return {
            "action": "HOLD",
            "confidence": 0.5,
            "price": None,
            "reasoning": "No clear decision could be extracted from the agent conversation."
        }
"""
    
    # Add helper methods at the end of the class
    class_end_pattern = "class "
    
    if class_end_pattern not in file_content:
        # If there's only one class, add at the end of the file
        return file_content + "\n" + helper_methods
    
    # Find the end of the first class (start of next class)
    class_start = file_content.find(class_end_pattern)
    next_class_start = file_content.find(class_end_pattern, class_start + len(class_end_pattern))
    
    if next_class_start == -1:
        # This is the only class, add at the end of the file
        return file_content + "\n" + helper_methods
    else:
        # Add helper methods before the next class
        return file_content[:next_class_start] + "\n" + helper_methods + "\n" + file_content[next_class_start:]

def fix_decision_session():
    """Fix the DecisionSession class to use the full agent framework"""
    logger.info("Fixing DecisionSession class...")
    
    # Get the path to decision_session.py
    decision_session_path = get_decision_session_path()
    
    if not decision_session_path:
        logger.error("Could not find decision_session.py")
        return False
    
    logger.info(f"Found decision_session.py at: {decision_session_path}")
    
    # Backup the file
    if not backup_file(decision_session_path):
        logger.error("Failed to backup decision_session.py")
        return False
    
    # Read the file
    try:
        with open(decision_session_path, 'r') as f:
            file_content = f.read()
        
        # Make sure the file contains the DecisionSession class
        if "class DecisionSession" not in file_content:
            logger.error("File does not contain DecisionSession class")
            return False
        
        # Add necessary imports if they don't exist
        if not has_agent_imports(file_content):
            logger.info("Adding agent imports")
            file_content = add_agent_imports(file_content)
        
        # Add agent class properties
        logger.info("Adding agent class properties")
        file_content = add_agent_class_properties(file_content)
        
        # Add init_agents method
        logger.info("Adding init_agents method")
        file_content = add_init_agent_method(file_content)
        
        # Update run_session method
        logger.info("Updating run_session method")
        file_content = update_run_session_method(file_content)
        
        # Add helper methods
        logger.info("Adding helper methods")
        file_content = add_helper_methods(file_content)
        
        # Write the updated file
        with open(decision_session_path, 'w') as f:
            f.write(file_content)
        
        # Copy to a result file for downloading
        with open('fixed_decision_session.py', 'w') as f:
            f.write(file_content)
        
        logger.info(f"Updated decision_session.py successfully")
        logger.info(f"Also saved to fixed_decision_session.py for download")
        
        return True
    
    except Exception as e:
        logger.error(f"Error fixing decision_session.py: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function"""
    logger.info("Starting fix of DecisionSession class")
    
    # Fix the DecisionSession class
    if fix_decision_session():
        print("✅ Successfully fixed DecisionSession class")
    else:
        print("❌ Failed to fix DecisionSession class")
    
    logger.info("Fix completed")

if __name__ == "__main__":
    main()