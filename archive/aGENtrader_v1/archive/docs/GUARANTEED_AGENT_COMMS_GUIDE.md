# Guaranteed Agent Communications Guide for Authentic Backtesting

## Overview

This guide provides step-by-step instructions to ensure your multi-agent backtesting system captures all authentic agent communications without any simulated or hard-coded responses. The approach focuses on monitoring and logging real agent interactions rather than creating fake ones.

## Key Principles

1. **Authentic Data Only**: Use only real market data from the database.
2. **No Simulations**: Never replace real agent responses with simulated ones.
3. **Fail Rather Than Fake**: If an authentic process fails, log the error but don't substitute with simulations.
4. **Complete Logging**: Capture all agent communications for analysis.

## Implementation Approach

We use a **monitoring approach** rather than a **simulation approach**. This means our code observes and logs what's already happening in the system without interfering or injecting simulated content.

### Method 1: Monkey Patching

The most reliable way to capture authentic agent communications is through monkey patching. This technique:

1. Stores references to the original methods
2. Creates new methods that:
   - Log the entry and parameters
   - Call the original method
   - Log the result
   - Return the unaltered result

Example of proper monkey patching:

```python
# Store original method
original_method = SomeClass.some_method

# Define wrapper method
def patched_method(*args, **kwargs):
    # Log entry
    logger.info(f"Entering method with args: {args}, kwargs: {kwargs}")
    
    # Call original method - DO NOT REPLACE WITH SIMULATION
    result = original_method(*args, **kwargs)
    
    # Log result WITHOUT ALTERING IT
    logger.info(f"Method returned: {result}")
    
    # Return unaltered result
    return result

# Replace method
SomeClass.some_method = patched_method
```

### Method 2: Inheritance with Logging

Another approach is to create a logging subclass:

```python
class LoggingDecisionSession(DecisionSession):
    def run_session(self, *args, **kwargs):
        # Log entry
        logger.info(f"Entering run_session with args: {args}, kwargs: {kwargs}")
        
        # Call original method - NO SIMULATION HERE
        result = super().run_session(*args, **kwargs)
        
        # Log result WITHOUT ALTERING IT
        logger.info(f"run_session returned: {result}")
        
        # Return unaltered result
        return result
```

## Step-by-Step Implementation

### 1. Prepare Logging Infrastructure

```python
import logging
from datetime import datetime

# Create log directory
os.makedirs('data/logs', exist_ok=True)

# Set up logger for agent communications
agent_logger = logging.getLogger('agent_comms')
agent_logger.setLevel(logging.INFO)
agent_logger.propagate = False  # Don't propagate to parent logger

# Add file handler
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file_handler = logging.FileHandler(f'data/logs/agent_comms_{timestamp}.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
agent_logger.addHandler(file_handler)
```

### 2. Identify Communication Points

Locate all methods where agents communicate:

1. **DecisionSession.run_session**: Main entry point for decision making
2. **DecisionSession.initiate_chat**: Starts multi-agent chat
3. **AutoGen.GroupChatManager.initiate_chat**: Manages group chats
4. **AutoGen.ConversableAgent.generate_reply**: Individual agent responses

### 3. Apply Monkey Patching

```python
def patch_decision_session():
    """Patch DecisionSession with logging"""
    from orchestration.decision_session import DecisionSession
    
    # Store original methods
    original_run_session = DecisionSession.run_session
    original_initiate_chat = DecisionSession.initiate_chat
    
    # Patch run_session
    def patched_run_session(self, *args, **kwargs):
        # Log before calling
        agent_logger.info(f"===== STARTING DECISION SESSION =====")
        
        # Call original - NO SIMULATION
        result = original_run_session(self, *args, **kwargs)
        
        # Log after - NO ALTERATION
        if isinstance(result, dict) and 'decision' in result:
            decision = result['decision']
            if isinstance(decision, dict):
                action = decision.get('action', 'UNKNOWN')
                confidence = decision.get('confidence', 0)
                agent_logger.info(f"Decision: {action} with {confidence*100:.1f}% confidence")
        
        agent_logger.info(f"===== COMPLETED DECISION SESSION =====")
        return result
    
    # Apply patches
    DecisionSession.run_session = patched_run_session
    # (similar patching for other methods)
```

### 4. Patch AutoGen Components

```python
def patch_autogen():
    """Patch AutoGen components with logging"""
    import autogen
    
    if hasattr(autogen, 'ConversableAgent'):
        original_generate = autogen.ConversableAgent.generate_reply
        
        def patched_generate_reply(self, *args, **kwargs):
            agent_name = getattr(self, 'name', str(self))
            agent_logger.info(f"Agent {agent_name} generating reply")
            
            # Call original - NO SIMULATION
            result = original_generate(self, *args, **kwargs)
            
            # Log result - NO ALTERATION
            if result:
                shortened = result[:100] + "..." if len(result) > 100 else result
                agent_logger.info(f"Agent {agent_name} replied: {shortened}")
            
            return result
        
        # Apply patch
        autogen.ConversableAgent.generate_reply = patched_generate_reply
```

## Deployment Process

1. **Upload Logging Scripts**: Transfer the agent communication logging patches to EC2
2. **Set Environment Variables**: Ensure DATABASE_URL and OPENAI_API_KEY are set
3. **Apply Patches**: Run the patching script before starting the backtest
4. **Run Backtest**: Execute the backtest with full agent framework integration
5. **Collect Logs**: Retrieve and analyze the agent communications logs

## Common Issues and Solutions

### 1. No Communications Logged

**Problem**: The backtest runs but no agent communications are logged.

**Solution**:
- Verify that the logging patches were successfully applied
- Check the class and method names are correct
- Ensure the logging directory exists and is writable
- Try adding debug logs before and after the patching

### 2. Missing Components

**Problem**: Some components are not found (ImportError).

**Solution**:
- Check PYTHONPATH includes the project root
- Verify all directories have `__init__.py` files
- Check for typos in import statements
- Use absolute imports rather than relative

### 3. Incomplete Logs

**Problem**: Some agent communications are missing from logs.

**Solution**:
- Add more patch points to cover additional methods
- Check if some methods are using alternate communication channels
- Increase logging verbosity
- Add error handling to log exceptions during communications

## Testing Your Setup

1. **Mini Backtest**: Run a short backtest with 1-2 days of data
2. **Check Log Content**: Verify logs contain actual agent communications
3. **Decision Process**: Confirm the entire decision process is captured
4. **Verify Authenticity**: Ensure no simulated data is being used

## Reading Agent Communications Logs

The logs will contain entries like:

```
2025-04-15 13:45:22 - INFO - ===== STARTING DECISION SESSION FOR BTCUSDT =====
2025-04-15 13:45:22 - INFO - Current price: $67890.50
2025-04-15 13:45:23 - INFO - Initiating multi-agent chat session
2025-04-15 13:45:23 - INFO - Participating agents: Technical Analyst, Fundamental Analyst, Portfolio Manager, Decision Agent
2025-04-15 13:45:30 - INFO - Agent Technical Analyst generating reply
2025-04-15 13:45:45 - INFO - Agent Technical Analyst replied: Analysis of price action shows resistance at $68500...
...
2025-04-15 13:46:32 - INFO - Decision: BUY with 78.5% confidence
2025-04-15 13:46:32 - INFO - ===== COMPLETED DECISION SESSION FOR BTCUSDT =====
```

## EC2 Deployment Commands

To deploy and run the full-scale authentic backtesting system:

```bash
# Upload scripts
scp -i key.pem agent_log_patch.py ec2-user@<EC2_IP>:/home/ec2-user/aGENtrader/

# Set up environment
ssh -i key.pem ec2-user@<EC2_IP> "export PYTHONPATH=/home/ec2-user/aGENtrader && cd /home/ec2-user/aGENtrader"

# Run backtest with agent logging
ssh -i key.pem ec2-user@<EC2_IP> "cd /home/ec2-user/aGENtrader && python3 -c 'import agent_log_patch; agent_log_patch.patch_all()' && python3 -m backtesting.core.authentic_backtest --symbol BTCUSDT --interval 1h --start_date 2025-04-01 --end_date 2025-04-10"

# Retrieve logs
scp -i key.pem ec2-user@<EC2_IP>:/home/ec2-user/aGENtrader/data/logs/agent_comms_*.log ./results/logs/
```

## Conclusion

By following this guide, you ensure that your multi-agent backtesting system captures authentic agent communications without any simulated responses. This approach:

1. Maintains integrity of the backtest results
2. Provides genuine insight into agent decision making
3. Enables truthful evaluation of system performance
4. Ensures what you see in testing is what you'll get in production

Remember: Real trading systems must be built on authentic data and genuine agent communications. Simulations may mask real issues that would emerge in production.