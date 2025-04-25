#!/usr/bin/env python3
"""
Direct Agent Fix Script

This script focuses on fixing agent communications in the backtesting framework.
"""
import os
import sys
import inspect
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'direct_agent_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("direct_agent_fix")

def setup_logging():
    """Set up agent communications logging directory"""
    logger.info("Setting up agent communications logging directory...")
    
    # Create log directory
    log_dir = os.path.join('data', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'direct_agent_comms_{timestamp}.log')
    
    # Create agent logger
    agent_logger = logging.getLogger('agent_comms')
    agent_logger.setLevel(logging.INFO)
    
    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - AGENT - %(message)s')
    file_handler.setFormatter(file_formatter)
    agent_logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('>>> AGENT: %(message)s')
    console_handler.setFormatter(console_formatter)
    agent_logger.addHandler(console_handler)
    
    logger.info(f"Agent communications will be logged to: {log_file}")
    return agent_logger, log_file

def examine_decision_session():
    """Examine the DecisionSession class"""
    logger.info("Examining DecisionSession class...")
    
    try:
        # Import the DecisionSession class
        from orchestration.decision_session import DecisionSession
        
        # Check if the class has the expected methods
        methods = []
        for name in dir(DecisionSession):
            if not name.startswith('__'):
                attr = getattr(DecisionSession, name)
                if inspect.isfunction(attr) or inspect.ismethod(attr):
                    methods.append(name)
        
        logger.info(f"DecisionSession methods: {', '.join(methods)}")
        
        # Check if the class is using a simplified implementation
        if hasattr(DecisionSession, 'run_session'):
            run_session_code = None
            try:
                run_session_code = inspect.getsource(DecisionSession.run_session)
                logger.info(f"run_session code: {run_session_code[:100]}...")
            except Exception as e:
                logger.warning(f"Could not get source code for run_session: {e}")
            
            # Store if using simplified agent framework
            is_simplified = (run_session_code and "simplified agent framework" in run_session_code)
            
            if is_simplified:
                logger.warning("DecisionSession is using a simplified agent framework")
            else:
                logger.info("DecisionSession appears to be using the full agent framework")
        else:
            logger.warning("DecisionSession does not have a run_session method")
        
        return {
            "exists": True,
            "methods": methods,
            "is_simplified": is_simplified if 'is_simplified' in locals() else False
        }
    
    except ImportError as e:
        logger.error(f"Failed to import DecisionSession: {e}")
        return {"exists": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error examining DecisionSession: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"exists": False, "error": str(e)}

def patch_decision_session(agent_logger):
    """Patch the DecisionSession class to add better logging"""
    logger.info("Patching DecisionSession class...")
    
    try:
        # Import the DecisionSession class
        from orchestration.decision_session import DecisionSession
        
        # Store original run_session method
        if hasattr(DecisionSession, 'run_session'):
            original_run_session = DecisionSession.run_session
            
            # Create patched method
            def patched_run_session(self, symbol=None, current_price=None, prompt=None):
                """Patched run_session method with better logging"""
                # Log entry
                agent_logger.info(f"===== STARTING DECISION SESSION FOR {symbol} =====")
                if current_price is not None:
                    agent_logger.info(f"Current price: ${current_price}")
                
                # Call original method
                result = original_run_session(self, symbol, current_price, prompt)
                
                # Log the decision without altering anything
                if isinstance(result, dict):
                    if 'status' in result:
                        agent_logger.info(f"Session status: {result['status']}")
                    
                    if 'session_id' in result:
                        agent_logger.info(f"Session ID: {result['session_id']}")
                    
                    if 'decision' in result:
                        decision = result['decision']
                        if isinstance(decision, dict):
                            action = decision.get('action', 'UNKNOWN')
                            confidence = decision.get('confidence', 0)
                            
                            agent_logger.info(f"Decision: {action} with {confidence*100:.1f}% confidence")
                            
                            if 'reasoning' in decision:
                                agent_logger.info(f"Reasoning: {decision['reasoning']}")
                
                # Log exit
                agent_logger.info(f"===== COMPLETED DECISION SESSION FOR {symbol} =====")
                
                return result
            
            # Apply patch
            DecisionSession.run_session = patched_run_session
            logger.info("Successfully patched DecisionSession.run_session")
            
            # Add a flag to indicate that the class has been patched
            setattr(DecisionSession, 'is_patched', True)
            
            return True
        else:
            logger.error("DecisionSession does not have a run_session method")
            return False
    
    except ImportError as e:
        logger.error(f"Failed to import DecisionSession: {e}")
        return False
    except Exception as e:
        logger.error(f"Error patching DecisionSession: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_autogen_availability():
    """Check if AutoGen is available"""
    logger.info("Checking AutoGen availability...")
    
    try:
        import autogen
        
        # Get version
        version = getattr(autogen, '__version__', 'Unknown')
        logger.info(f"AutoGen version: {version}")
        
        # Check key components
        has_assistant_agent = hasattr(autogen, 'AssistantAgent')
        has_user_proxy_agent = hasattr(autogen, 'UserProxyAgent')
        has_group_chat = hasattr(autogen, 'GroupChat')
        has_group_chat_manager = hasattr(autogen, 'GroupChatManager')
        
        logger.info(f"AssistantAgent available: {has_assistant_agent}")
        logger.info(f"UserProxyAgent available: {has_user_proxy_agent}")
        logger.info(f"GroupChat available: {has_group_chat}")
        logger.info(f"GroupChatManager available: {has_group_chat_manager}")
        
        return {
            "available": True,
            "version": version,
            "components": {
                "AssistantAgent": has_assistant_agent,
                "UserProxyAgent": has_user_proxy_agent,
                "GroupChat": has_group_chat,
                "GroupChatManager": has_group_chat_manager
            }
        }
    
    except ImportError:
        logger.warning("AutoGen is not available")
        return {"available": False}
    except Exception as e:
        logger.error(f"Error checking AutoGen availability: {e}")
        return {"available": False, "error": str(e)}

def patch_autogen(agent_logger):
    """Patch AutoGen to add better logging"""
    logger.info("Patching AutoGen components...")
    
    try:
        import autogen
        
        patched_components = []
        
        # Patch GroupChatManager.initiate_chat
        if hasattr(autogen, 'GroupChatManager') and hasattr(autogen.GroupChatManager, 'initiate_chat'):
            original_initiate_chat = autogen.GroupChatManager.initiate_chat
            
            def patched_initiate_chat(self, *args, **kwargs):
                """Patched initiate_chat method with better logging"""
                agent_logger.info("AutoGen group chat initiated")
                
                # Extract agent names if available
                if hasattr(self, 'groupchat') and hasattr(self.groupchat, 'agents'):
                    agent_names = [getattr(agent, 'name', str(agent)) for agent in self.groupchat.agents]
                    agent_logger.info(f"Participating agents: {', '.join(agent_names)}")
                
                # Call original method
                result = original_initiate_chat(self, *args, **kwargs)
                
                # Log chat history
                if hasattr(self, 'groupchat') and hasattr(self.groupchat, 'messages'):
                    agent_logger.info(f"Group chat completed with {len(self.groupchat.messages)} messages")
                    
                    # Log individual messages
                    for i, msg in enumerate(self.groupchat.messages):
                        if isinstance(msg, dict):
                            agent_name = msg.get('name', 'Unknown')
                            content = msg.get('content', '')
                            if content:
                                # Truncate long messages
                                truncated_content = content[:100] + '...' if len(content) > 100 else content
                                agent_logger.info(f"Message {i+1} - {agent_name}: {truncated_content}")
                
                agent_logger.info("AutoGen group chat completed")
                return result
            
            # Apply patch
            autogen.GroupChatManager.initiate_chat = patched_initiate_chat
            logger.info("Successfully patched autogen.GroupChatManager.initiate_chat")
            patched_components.append('GroupChatManager.initiate_chat')
        
        # Patch ConversableAgent.generate_reply
        if hasattr(autogen, 'ConversableAgent') and hasattr(autogen.ConversableAgent, 'generate_reply'):
            original_generate_reply = autogen.ConversableAgent.generate_reply
            
            def patched_generate_reply(self, *args, **kwargs):
                """Patched generate_reply method with better logging"""
                agent_name = getattr(self, 'name', str(self))
                
                # Extract message content
                message = "No message content"
                if args and len(args) > 0 and isinstance(args[0], list) and len(args[0]) > 0:
                    last_message = args[0][-1]
                    if isinstance(last_message, dict) and 'content' in last_message:
                        # Truncate long messages
                        content = last_message['content']
                        message = content[:100] + '...' if len(content) > 100 else content
                
                agent_logger.info(f"Agent {agent_name} generating reply to: {message}")
                
                # Call original method
                result = original_generate_reply(self, *args, **kwargs)
                
                # Log result
                if result:
                    # Truncate long replies
                    truncated_result = result[:100] + '...' if len(result) > 100 else result
                    agent_logger.info(f"Agent {agent_name} replied: {truncated_result}")
                
                return result
            
            # Apply patch
            autogen.ConversableAgent.generate_reply = patched_generate_reply
            logger.info("Successfully patched autogen.ConversableAgent.generate_reply")
            patched_components.append('ConversableAgent.generate_reply')
        
        if patched_components:
            logger.info(f"Successfully patched {len(patched_components)} AutoGen components")
            return {"success": True, "patched_components": patched_components}
        else:
            logger.warning("No AutoGen components were patched")
            return {"success": False, "error": "No components patched"}
    
    except ImportError:
        logger.warning("AutoGen is not available, skipping patch")
        return {"success": False, "error": "AutoGen not available"}
    except Exception as e:
        logger.error(f"Error patching AutoGen: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

def run_test_decision_session(agent_logger):
    """Run a test decision session"""
    logger.info("Running test decision session...")
    
    try:
        from orchestration.decision_session import DecisionSession
        
        # Create a decision session
        session = DecisionSession()
        
        # Run a test decision
        symbol = "BTCUSDT"
        current_price = 80000.0
        
        agent_logger.info("========================================")
        agent_logger.info(f"Running TEST decision session for {symbol}")
        agent_logger.info("========================================")
        
        logger.info(f"Running decision session for {symbol} at price ${current_price}")
        result = session.run_session(symbol=symbol, current_price=current_price)
        
        logger.info(f"Test decision result: {result}")
        return result
    
    except ImportError as e:
        logger.error(f"Failed to import DecisionSession: {e}")
        return None
    except Exception as e:
        logger.error(f"Error running test decision session: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Main function"""
    logger.info("Starting direct agent fix")
    
    # Set up logging
    agent_logger, log_file = setup_logging()
    
    # Examine DecisionSession
    decision_session_info = examine_decision_session()
    logger.info(f"DecisionSession info: {decision_session_info}")
    
    # Check AutoGen availability
    autogen_info = check_autogen_availability()
    logger.info(f"AutoGen info: {autogen_info}")
    
    # Patch DecisionSession
    decision_session_patched = patch_decision_session(agent_logger)
    logger.info(f"DecisionSession patched: {decision_session_patched}")
    
    # Patch AutoGen if available
    if autogen_info.get("available", False):
        autogen_patched = patch_autogen(agent_logger)
        logger.info(f"AutoGen patched: {autogen_patched}")
    
    # Run test decision session
    test_result = run_test_decision_session(agent_logger)
    
    logger.info("Direct agent fix completed")
    
    # Print summary
    print("\n===== DIRECT AGENT FIX SUMMARY =====")
    print(f"Decision Session examined: {decision_session_info.get('exists', False)}")
    print(f"Decision Session simplified: {decision_session_info.get('is_simplified', 'Unknown')}")
    print(f"Decision Session patched: {decision_session_patched}")
    print(f"AutoGen available: {autogen_info.get('available', False)}")
    
    if autogen_info.get("available", False):
        print(f"AutoGen version: {autogen_info.get('version', 'Unknown')}")
    
    print(f"Test decision successful: {test_result is not None}")
    print(f"Agent communications log: {log_file}")
    print("=====================================")
    
    return {
        "success": decision_session_patched,
        "log_file": log_file,
        "decision_session_info": decision_session_info,
        "autogen_info": autogen_info,
        "test_result": test_result is not None
    }

if __name__ == "__main__":
    main()