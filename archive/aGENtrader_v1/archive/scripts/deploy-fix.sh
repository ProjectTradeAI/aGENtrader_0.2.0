#!/bin/bash
# Deploy and run fix for DecisionSession on EC2

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="fix-deployment-${TIMESTAMP}.log"

# Create key file if needed
if [ ! -f "$KEY_PATH" ]; then
  echo "Creating EC2 key file..."
  cat > "$KEY_PATH" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEoQIBAAKCAQEAyxNT6X+1frDllJPAbCAjOjNV6+IYbJTBJF+NNUESxrYsMK8J
1Dt4OBuXKSMV7nttmb6/jy6tItkztExoPyqr1QuKwHUInkbkKTm15Cl90o6yzXba
UfntOfpwZHwmEOJRVniLRJPzkOldOplyTiIxaf8mZKLeaXDlleaHZlNyrBWs9wNN
gJJbCBve2Z1TJsZeRig3u0Tg0+xo1BPxSm8dROalr8/30UrXpCkDQVL5S3oA2kSd
6hvwQhUZclGNheGgLOGTMtZ/FxGAI/mVsD29ErWnEoysLGCpbLfXpw7o3yEDCND+
cpqtV+ckbTeX2gqbugyZmBVrxcnbafwW1ykoaQIDAQABAoIBAE53gmXn1c5FNgBp
8uEUrefwLBQAAeX6uIKAdUSNh17Gx15sVATwkaxEZO0dRH0orhnJDaWaqIWdnY/e
Mi2uJEUmt49T6WeXBtQzG2g07Awu3UHs2cDxLEvJzCHXorHFcR5TZ6Sw8l0c/swE
vJkaNzO4xjH+iKf/WobIU6sjNVzuNjJF7TNUJ/kZmfZHOjOKCSBF/ahY+weeVBFp
lqaSKrNINPYoYn4nrAgWVxMiPqItWhm3Y9G3c3z9ePNJKRkNKnRB+pCfGS3EZTq0
deI3rcurPsBe34B/SxZF7G1hLVhEtom18YUbZvSBxgCJmI7D239e/Qz6bgqB7FAo
rFJ/S3ECgYEA+oCEP5NjBilqOHSdLLPhI/Ak6pNIK017xMBdiBTjnRh93D8Xzvfh
glkHRisZo8gmIZsgW3izlEeUv4CaVf7OzlOUiu2KmmrLxGHPoT+QPLf/Ak3GZE14
XY9vtaQQSwxM+i5sNtAD/3/KcjH6wT1B+8R4xqtHUYXw7VoEQWRSs/UCgYEAz4hW
j7+ooYlyHzkfuiEMJG0CtKR/fYsd9Zygn+Y6gGQvCiL+skAmx/ymG/qU6D8ZejkN
Azzv7JGQ+1z8OtTNStgDPE7IT74pA0BC60jHySDYzyGAaoMJDhHxA2CPm60EwPDU
5pRVy+FN5LmCCT8oDgcpsPpgjALOqR2TUkcOziUCgYAFXdN3eTTZ4PFBnF3xozjj
iDWCQP1+z/4izOw0Ch6GMwwfN8rOyEiwfi/FtQ6rj5Ihji03SHKwboglQiAMT5Um
nmvEPiqF/Fu5LU9BaRcx9c8kwX3KkE5P0s7V2VnwAad0hKIU2of7ZUV1BNUWZrWP
KzpbJzgz6uaqbw9AR2HuMQJ/YuaWWer8cf8OY9LVS95z6ugIYg4Cs9GYdXQvGASf
3I/h2vLSbiAkWyoL/0lrrUJk4dpOWTyxGgxFC4VErsS7EO/gmtzwmRAGe4YkXfxR
OYhtykgs6pWHuyzRrspVpdrOaSRcUYZfXMoCVP4S+lUewZCoTa8EU7UCx5VQn+U9
KQKBgQDsjVRcsfC/szL7KgeheEN/2zRADix5bqrg0rAB1y+sw+yzkCCh3jcRn2O2
wNIMroggGNy+vcR8Xo/V1wLCsEn45cxB6W7onqxFRM6IkGxkBgdatEL/aBnETSAI
x4C5J+IqaT2T53O2n3DR+GsVoeNUbz8j/lPONNQnV0ZqHRVWpA==
-----END RSA PRIVATE KEY-----
KEYEOF
  chmod 600 "$KEY_PATH"
fi

# Get environment variables
DB_URL=$(node -e "console.log(process.env.DATABASE_URL || '')")
ALPACA_API_KEY=$(node -e "console.log(process.env.ALPACA_API_KEY || '')")
ALPACA_API_SECRET=$(node -e "console.log(process.env.ALPACA_API_SECRET || '')")
OPENAI_API_KEY=$(node -e "console.log(process.env.OPENAI_API_KEY || '')")

echo "🔧 Deploying Fix for DecisionSession on EC2" | tee "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

# Test EC2 connection
echo "Testing EC2 connection..." | tee -a "$LOG_FILE"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" >> "$LOG_FILE" 2>&1; then
  echo "Failed to connect to EC2. Please check your connection settings." | tee -a "$LOG_FILE"
  exit 1
fi
echo "✅ EC2 connection successful" | tee -a "$LOG_FILE"

# Check for required dependencies on EC2
echo "Checking for required dependencies on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && python3 -m pip list | grep -E 'autogen|flaml'" | tee -a "$LOG_FILE"

# Install dependencies if needed
echo "Installing required dependencies on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && python3 -m pip install pyautogen flaml[automl]" | tee -a "$LOG_FILE"

# Upload fix script to EC2
echo "Uploading fix script to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no fix-decision-session.py "$SSH_USER@$EC2_IP:$EC2_DIR/" >> "$LOG_FILE" 2>&1
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/fix-decision-session.py" >> "$LOG_FILE" 2>&1

# Run fix script on EC2
echo "Running fix script on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && export PYTHONPATH=\$PWD && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' python3 fix-decision-session.py" | tee -a "$LOG_FILE"

# Download the fixed file
echo "Downloading fixed decision_session.py from EC2..." | tee -a "$LOG_FILE"
mkdir -p ./results/fixed
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/fixed_decision_session.py" ./results/fixed/ 2>/dev/null

# Verify the fix using a simple test
echo "Verifying the fix with a simple test..." | tee -a "$LOG_FILE"
cat > verify-fix.py << EOF
#!/usr/bin/env python3
"""
Verify DecisionSession Fix

This script verifies that the DecisionSession class now uses the full agent framework.
"""
import os
import sys
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fix")

def verify_decision_session():
    """Verify that the DecisionSession class now uses the full agent framework"""
    try:
        # Import the fixed DecisionSession
        from orchestration.decision_session import DecisionSession
        
        # Create an instance
        session = DecisionSession()
        
        # Check if it has the agents attribute
        has_agents_attr = hasattr(session, 'agents')
        logger.info(f"Has agents attribute: {has_agents_attr}")
        
        # Check if it has autogen-related methods
        has_init_agents = hasattr(session, 'init_agents')
        logger.info(f"Has init_agents method: {has_init_agents}")
        
        # Run a test decision
        logger.info("Running test decision...")
        result = session.run_session("BTCUSDT", 50000)
        
        # Check result
        if 'decision' in result and 'reasoning' in result['decision']:
            reasoning = result['decision']['reasoning']
            logger.info(f"Decision reasoning: {reasoning}")
            
            is_fixed = "simplified agent framework" not in reasoning.lower()
            logger.info(f"Is fixed: {is_fixed}")
            
            return {
                "status": "success" if is_fixed else "failed",
                "has_agents_attr": has_agents_attr,
                "has_init_agents": has_init_agents,
                "reasoning": reasoning,
                "is_fixed": is_fixed
            }
        else:
            logger.warning("Invalid result format")
            return {
                "status": "failed",
                "error": "Invalid result format"
            }
    
    except Exception as e:
        logger.error(f"Error verifying fix: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    print("Verifying DecisionSession fix...")
    result = verify_decision_session()
    print(f"Verification result: {result}")
    
    if result.get("status") == "success":
        print("✅ Fix successfully applied!")
    else:
        print("❌ Fix verification failed")
EOF

# Upload verification script
echo "Uploading verification script to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no verify-fix.py "$SSH_USER@$EC2_IP:$EC2_DIR/" >> "$LOG_FILE" 2>&1
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/verify-fix.py" >> "$LOG_FILE" 2>&1

# Run verification script
echo "Running verification script on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && export PYTHONPATH=\$PWD && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' python3 verify-fix.py" | tee -a "$LOG_FILE"

echo "✅ Deployment and verification completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"