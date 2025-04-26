# EC2 Setup Guide for aGENtrader v2.2

This guide provides detailed instructions for setting up a fresh EC2 instance for running the aGENtrader v2.2 platform.

## Prerequisites

- An AWS account with permission to create and manage EC2 instances
- Access to the aGENtrader v2.2 codebase
- SSH key pair for secure instance access

## 1. Launch a New EC2 Instance

### Instance Specifications

- **Instance Type**: t2.medium (or larger for production use)
- **Architecture**: x86_64
- **AMI**: Ubuntu Server 20.04 LTS (HVM)
- **Storage**: 30GB+ gp2 or gp3 SSD
- **Security Group Settings**:
  - SSH (TCP port 22) - Restricted to your IP address
  - HTTP (TCP port 80) - Optional, for web UI access
  - HTTPS (TCP port 443) - Optional, for secure web access

### Step-by-Step Launch Process

1. Log in to the AWS Management Console
2. Navigate to EC2 service
3. Click "Launch Instance"
4. Select Ubuntu Server 20.04 LTS AMI
5. Choose instance type (t2.medium or better)
6. Configure instance details (use defaults unless specific network requirements exist)
7. Add storage (30GB minimum recommended)
8. Add tags (recommended: Key=Name, Value=aGENtrader-production)
9. Configure security group as described above
10. Review and launch
11. Select an existing key pair or create a new one
    - If creating new: Download and securely store the .pem file
    - If using existing: Ensure you have access to the private key
12. Launch the instance

## 2. Initial EC2 Instance Setup

### Connect to Your Instance

```bash
# Ensure the .pem file has proper permissions
chmod 400 path/to/your-key.pem

# Connect to the instance
ssh -i path/to/your-key.pem ubuntu@your-instance-public-ip
```

### Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### Install Required Dependencies

```bash
# Install basic tools
sudo apt install -y git curl wget build-essential
```

### Setup SSH Key for GitHub Access

1. Generate a new SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
   
2. Add the key to the SSH agent:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

3. View and copy the public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

4. Add this key to the GitHub repository as a deploy key:
   - Go to the repository on GitHub
   - Navigate to Settings > Deploy keys
   - Click "Add deploy key"
   - Paste the public key and give it a descriptive title
   - Enable "Allow write access" if needed (usually not required for deployment)
   - Click "Add key"

5. Verify the connection:
   ```bash
   ssh -T git@github.com
   ```

## 3. Docker Installation

### Install Docker Engine

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update packages
sudo apt update

# Install Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io
```

### Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Apply executable permissions
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Configure Docker Permissions

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# IMPORTANT: Log out and log back in for the group changes to take effect
exit
# Then reconnect to your instance
```

## 4. Environment Configuration

### Create Project Directory

```bash
mkdir -p ~/aGENtrader
```

### Configure Environment Variables

Create a `.env` file in your home directory with the required API keys:

```bash
touch ~/.env

# Edit the file with your preferred editor
nano ~/.env
```

Add the following content, replacing the placeholder values with your actual API keys:

```
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
XAI_API_KEY=your_xai_api_key
```

## 5. System Monitoring Setup (Optional)

### Basic Monitoring with Docker Stats

```bash
# Create a simple monitoring script
cat > ~/monitor.sh << 'EOF'
#!/bin/bash
while true; do
  clear
  echo "===== $(date) ====="
  echo "DOCKER CONTAINERS:"
  docker ps
  echo -e "\nCONTAINER STATS:"
  docker stats --no-stream
  echo -e "\nDISK USAGE:"
  df -h /
  sleep 30
done
EOF

chmod +x ~/monitor.sh
```

To use: Run `~/monitor.sh` to monitor system resources.

### Setup Log Rotation

```bash
sudo apt install -y logrotate

# Create a Docker log rotation configuration
sudo tee /etc/logrotate.d/docker-container-logs > /dev/null << 'EOF'
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
EOF
```

## Next Steps

After setting up your EC2 instance, you can deploy aGENtrader using the clean deployment script:

```bash
# From your local machine containing the aGENtrader repository
bash deployment/clean_deploy_ec2.sh --host your-ec2-ip --key path/to/your-key.pem
```

## Troubleshooting Common Issues

### SSH Connection Issues

- Verify that the security group allows SSH access from your IP address
- Ensure the key pair .pem file has permissions set to 400
- Confirm you're using the correct username (ubuntu for Ubuntu AMIs)

### Docker Permission Issues

If you see "permission denied" errors when running Docker commands:

```bash
# Verify your user is in the docker group
groups

# If docker is not listed, add your user and restart the session
sudo usermod -aG docker $USER
exit
# Then reconnect
```

### GitHub SSH Connection Issues

If you cannot connect to GitHub via SSH:

```bash
# Test the GitHub connection
ssh -T git@github.com

# Check if GitHub is in known_hosts
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# Verify the SSH agent is running
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## Additional Resources

- [AWS EC2 User Guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub SSH Key Setup Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)