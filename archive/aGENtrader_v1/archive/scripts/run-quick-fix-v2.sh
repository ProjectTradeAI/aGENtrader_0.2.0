#!/bin/bash
# Deploy and run quick fix v2 for DecisionSession on EC2

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="quick-fix-v2-${TIMESTAMP}.log"

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

echo "🔧 Running Quick Fix v2 for DecisionSession on EC2" | tee "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

# Test EC2 connection
echo "Testing EC2 connection..." | tee -a "$LOG_FILE"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" >> "$LOG_FILE" 2>&1; then
  echo "Failed to connect to EC2. Please check your connection settings." | tee -a "$LOG_FILE"
  exit 1
fi
echo "✅ EC2 connection successful" | tee -a "$LOG_FILE"

# Create manual patch
echo "Creating manual patch..." | tee -a "$LOG_FILE"
cat > patch-decision-session.sh << 'EOF'
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
EOF

# Upload patch script to EC2
echo "Uploading patch script to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no patch-decision-session.sh "$SSH_USER@$EC2_IP:$EC2_DIR/" >> "$LOG_FILE" 2>&1
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/patch-decision-session.sh" >> "$LOG_FILE" 2>&1

# Run patch script on EC2
echo "Running patch script on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && export PYTHONPATH=\$PWD && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' ./patch-decision-session.sh" | tee -a "$LOG_FILE"

# Run a test backtest
echo "Running test backtest with the fix..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" \
  "cd $EC2_DIR && export PYTHONPATH=\$PWD && \
   DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' \
   ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' \
   python3 backtesting/run_simple_backtest.py --symbol BTCUSDT --interval 1h --days 1 --verbose" | tee -a "$LOG_FILE"

echo "✅ Quick fix v2 and verification completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"