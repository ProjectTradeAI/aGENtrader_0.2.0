#!/usr/bin/env python3
"""
Agent logging patch for multi-agent backtests
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging for agent communications
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a log file specifically for agent communications
agent_log_file = os.path.join(log_dir, f'agent_comms_{timestamp}.log')
print(f'Agent communications will be logged to: {agent_log_file}')

# Create a special formatter for agent communications
agent_formatter = logging.Formatter('%(asctime)s - AGENT - %(message)s')

# Create file handler for agent communications
agent_handler = logging.FileHandler(agent_log_file)
agent_handler.setFormatter(agent_formatter)
agent_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(agent_formatter)
console_handler.setLevel(logging.INFO)

# Create a dedicated logger for agent communications
agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)
agent_logger.addHandler(agent_handler)
agent_logger.addHandler(console_handler)

# Log the start of the patched run
agent_logger.info('=== MULTI-AGENT BACKTEST WITH ENHANCED LOGGING STARTED ===')

# Monkey patch key agent classes to add logging
def monkey_patch_agent_framework():
    """Monkey patch the agent framework to add enhanced logging"""
    try:
        # Try to import the agent classes
        agent_logger.info('Attempting to monkey patch agent framework classes...')
        
        # Patch CollaborativeDecisionFramework
        try:
            from agents.collaborative_decision_agent import CollaborativeDecisionFramework
            
            # Store original method
            original_run_decision = CollaborativeDecisionFramework.run_decision_session
            
            # Create patched method
            def patched_run_decision(self, symbol, prompt=None):
                agent_logger.info(f'=== STARTING COLLABORATIVE DECISION SESSION FOR {symbol} ===')
                result = original_run_decision(self, symbol, prompt)
                agent_logger.info(f'=== COMPLETED COLLABORATIVE DECISION SESSION ===')
                if isinstance(result, dict):
                    agent_logger.info(f'Decision: {result.get("decision", "Unknown")}')
                    agent_logger.info(f'Confidence: {result.get("confidence", "Unknown")}')
                    agent_logger.info(f'Reasoning: {result.get("reasoning", "None provided")}')
                return result
            
            # Replace original method
            CollaborativeDecisionFramework.run_decision_session = patched_run_decision
            agent_logger.info('Successfully patched CollaborativeDecisionFramework.run_decision_session')
            
        except (ImportError, AttributeError) as e:
            agent_logger.warning(f'Failed to patch CollaborativeDecisionFramework: {e}')
        
        # Patch DecisionSession
        try:
            from orchestration.decision_session import DecisionSession
            
            # Store original method
            if hasattr(DecisionSession, 'initiate_chat'):
                original_initiate_chat = DecisionSession.initiate_chat
                
                # Create patched method
                def patched_initiate_chat(self, *args, **kwargs):
                    agent_logger.info('=== INITIATING GROUP CHAT ===')
                    result = original_initiate_chat(self, *args, **kwargs)
                    agent_logger.info('=== GROUP CHAT INITIATED ===')
                    return result
                
                # Replace original method
                DecisionSession.initiate_chat = patched_initiate_chat
                agent_logger.info('Successfully patched DecisionSession.initiate_chat')
                
        except (ImportError, AttributeError) as e:
            agent_logger.warning(f'Failed to patch DecisionSession: {e}')
            
        # Patch AutoGen's GroupChatManager
        try:
            # Import AutoGen directly
            import autogen
            
            # Check if initiate_chat exists
            if hasattr(autogen.GroupChatManager, 'initiate_chat'):
                original_autogen_initiate = autogen.GroupChatManager.initiate_chat
                
                # Create patched method
                def patched_autogen_initiate(self, *args, **kwargs):
                    agent_logger.info('=== AUTOGEN INITIATING GROUP CHAT ===')
                    result = original_autogen_initiate(self, *args, **kwargs)
                    agent_logger.info('=== AUTOGEN GROUP CHAT INITIATED ===')
                    return result
                
                # Replace original method
                autogen.GroupChatManager.initiate_chat = patched_autogen_initiate
                agent_logger.info('Successfully patched autogen.GroupChatManager.initiate_chat')
                
            # Also patch the chat method if it exists
            if hasattr(autogen.GroupChat, 'chat'):
                original_autogen_chat = autogen.GroupChat.chat
                
                # Create patched method
                def patched_autogen_chat(self, *args, **kwargs):
                    agent_logger.info('=== AUTOGEN GROUP CHAT STARTED ===')
                    result = original_autogen_chat(self, *args, **kwargs)
                    agent_logger.info('=== AUTOGEN GROUP CHAT COMPLETED ===')
                    return result
                
                # Replace original method
                autogen.GroupChat.chat = patched_autogen_chat
                agent_logger.info('Successfully patched autogen.GroupChat.chat')
                
        except (ImportError, AttributeError) as e:
            agent_logger.warning(f'Failed to patch AutoGen classes: {e}')
            
        agent_logger.info('Monkey patching completed')
        
    except Exception as e:
        agent_logger.error(f'Error in monkey_patch_agent_framework: {e}')

# Export agent logger
__all__ = ['agent_logger', 'monkey_patch_agent_framework']
