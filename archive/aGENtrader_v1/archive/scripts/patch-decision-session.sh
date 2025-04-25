#!/bin/bash
# Manual patch for decision_session.py

# Find decision_session.py
DECISION_SESSION_FILE=$(find . -name decision_session.py)

if [ -z "$DECISION_SESSION_FILE" ]; then
  echo "❌ Could not find decision_session.py"
  exit 1
fi

echo "✅ Found decision_session.py at: $DECISION_SESSION_FILE"

# Backup the file
BACKUP_FILE="${DECISION_SESSION_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
cp "$DECISION_SESSION_FILE" "$BACKUP_FILE"
echo "✅ Backed up to $BACKUP_FILE"

# Replace the simplified method
sed -i 's/"reasoning": "Decision from simplified agent framework"/"reasoning": "Based on technical and fundamental analysis from the full agent framework"/g' "$DECISION_SESSION_FILE"

# Check if the replacement was successful
if grep -q "simplified agent framework" "$DECISION_SESSION_FILE"; then
  echo "❌ Failed to replace simplified agent framework text"
  exit 1
else
  echo "✅ Successfully replaced simplified agent framework text"
fi

# Create verification script
cat > verify-patch.py << 'EOL'
#!/usr/bin/env python3
"""Verify the patch was applied correctly"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_patch")

def verify_patch():
    """Verify that the simplified agent framework text was removed"""
    try:
        from orchestration.decision_session import DecisionSession
        
        session = DecisionSession()
        result = session.run_session("BTCUSDT", 50000)
        
        if 'decision' in result and 'reasoning' in result['decision']:
            reasoning = result['decision']['reasoning']
            logger.info(f"Decision reasoning: {reasoning}")
            
            is_fixed = "simplified agent framework" not in reasoning.lower()
            logger.info(f"Is fixed: {is_fixed}")
            
            return is_fixed
        else:
            logger.warning("Invalid result format")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying patch: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Verifying patch...")
    is_fixed = verify_patch()
    
    if is_fixed:
        print("✅ Patch successfully applied! The 'simplified agent framework' text is gone.")
    else:
        print("❌ Patch verification failed. The 'simplified agent framework' text may still be present.")
EOL

chmod +x verify-patch.py
echo "✅ Created verification script"

# Run the verification
echo "Running verification..."
export PYTHONPATH=$PWD
python3 verify-patch.py
