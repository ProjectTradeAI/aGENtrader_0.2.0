#!/bin/bash
# Run extract-run-session.py script on EC2

# Set parameters
EC2_IP="51.20.250.135"
SSH_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
KEY_PATH="/tmp/backtest_key.pem"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="extract-run-session-${TIMESTAMP}.log"

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

echo "📄 Extracting run_session Method from EC2" | tee "$LOG_FILE"
echo "=====================================" | tee -a "$LOG_FILE"

# Test EC2 connection
echo "Testing EC2 connection..." | tee -a "$LOG_FILE"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "echo 'Connection successful!'" >> "$LOG_FILE" 2>&1; then
  echo "Failed to connect to EC2. Please check your connection settings." | tee -a "$LOG_FILE"
  exit 1
fi
echo "✅ EC2 connection successful" | tee -a "$LOG_FILE"

# Upload script to EC2
echo "Uploading extract script to EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no extract-run-session.py "$SSH_USER@$EC2_IP:$EC2_DIR/" >> "$LOG_FILE" 2>&1
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "chmod +x $EC2_DIR/extract-run-session.py" >> "$LOG_FILE" 2>&1

# Run script on EC2
echo "Running extract script on EC2..." | tee -a "$LOG_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && export PYTHONPATH=\$PWD && DATABASE_URL='$DB_URL' ALPACA_API_KEY='$ALPACA_API_KEY' ALPACA_API_SECRET='$ALPACA_API_SECRET' OPENAI_API_KEY='$OPENAI_API_KEY' python3 extract-run-session.py" | tee -a "$LOG_FILE"

# Download the method file
echo "Downloading run_session_method.txt from EC2..." | tee -a "$LOG_FILE"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP:$EC2_DIR/run_session_method.txt" ./ 2>/dev/null

# Check if file was downloaded
if [ -f "run_session_method.txt" ]; then
  echo "✅ Successfully downloaded run_session_method.txt" | tee -a "$LOG_FILE"
  
  echo -e "\n===== run_session METHOD CONTENT =====" | tee -a "$LOG_FILE"
  cat run_session_method.txt | tee -a "$LOG_FILE"
  echo -e "\n======================================" | tee -a "$LOG_FILE"
else
  echo "❌ Failed to download run_session_method.txt" | tee -a "$LOG_FILE"
fi

echo "✅ Extraction completed" | tee -a "$LOG_FILE"
echo "Log file saved to: $LOG_FILE" | tee -a "$LOG_FILE"