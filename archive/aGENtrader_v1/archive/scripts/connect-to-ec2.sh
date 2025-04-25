#!/bin/bash
# Comprehensive EC2 connection script

# Configuration
EC2_IP="${EC2_PUBLIC_IP:-51.20.250.135}"
SSH_USER="${EC2_USERNAME:-ec2-user}"
KEY_PATH="$HOME/.ssh/ec2_key.pem"
EC2_DIR="/home/ec2-user/aGENtrader"

# Ensure the key file exists with proper permissions
if [ ! -f "$KEY_PATH" ]; then
  # Create the key file from the predefined key
  mkdir -p ~/.ssh
  chmod 700 ~/.ssh
  
  cat > "$KEY_PATH" << 'KEYDATA'
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
KEYDATA

  chmod 600 "$KEY_PATH"
fi

# Function to display help
function show_help() {
  echo "EC2 Connection Helper"
  echo "===================="
  echo "This script helps you connect to your EC2 instance and run commands."
  echo
  echo "Usage:"
  echo "  $0 [options] [command]"
  echo
  echo "Options:"
  echo "  --help        Show this help message"
  echo "  --ip IP       Set EC2 IP address (default: $EC2_IP)"
  echo "  --user USER   Set SSH username (default: $SSH_USER)"
  echo "  --key PATH    Set SSH key path (default: $KEY_PATH)"
  echo "  --dir PATH    Set working directory on EC2 (default: $EC2_DIR)"
  echo
  echo "Examples:"
  echo "  $0                                           # Simple connection test"
  echo "  $0 \"ls -la\"                                  # List files in home directory"
  echo "  $0 \"cd $EC2_DIR && ls -la\"                   # List files in project directory"
  echo "  $0 \"cd $EC2_DIR && ./ec2-multi-agent-backtest.sh --help\"  # Show backtest help"
}

# Process command line arguments
while [[ "$1" == --* ]]; do
  case "$1" in
    --help)
      show_help
      exit 0
      ;;
    --ip)
      EC2_IP="$2"
      shift 2
      ;;
    --user)
      SSH_USER="$2"
      shift 2
      ;;
    --key)
      KEY_PATH="$2"
      shift 2
      ;;
    --dir)
      EC2_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# First check if port 22 is open
echo "Checking if port 22 is reachable on $EC2_IP..."
if timeout 5 bash -c "</dev/tcp/$EC2_IP/22" 2>/dev/null; then
  echo "✅ Port 22 (SSH) is open on $EC2_IP"
else
  echo "❌ Port 22 (SSH) is not reachable on $EC2_IP"
  echo "This could mean the instance is not running, the security group blocks port 22, or there's a network issue."
  echo
  echo "Please try using AWS Console Connect as described in aws-console-connect.md"
  exit 1
fi

# Try to connect
if [ $# -eq 0 ]; then
  # Simple connection test
  echo "Testing connection to $EC2_IP..."
  ssh -v -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$EC2_IP" "echo Connection successful!"
  
  if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
  else
    echo "❌ Connection failed."
    echo "Please check:"
    echo "1. The SSH key is correct for this instance"
    echo "2. The security group allows SSH access from this IP"
    echo "3. The username is correct (try different users with --user)"
    echo
    echo "As a fallback, use AWS Console as described in aws-console-connect.md"
  fi
else
  # Run the provided command
  echo "Running command on EC2: $@"
  echo "---------------------------------------------------"
  ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@$EC2_IP" "cd $EC2_DIR && $@"
  
  if [ $? -eq 0 ]; then
    echo "---------------------------------------------------"
    echo "✅ Command executed successfully."
  else
    echo "---------------------------------------------------"
    echo "❌ Command execution failed."
    echo "Please try AWS Console Connect if SSH continues to fail."
  fi
fi
