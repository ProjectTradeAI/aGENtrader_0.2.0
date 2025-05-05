# Ollama Configuration Guide

This document explains how to properly configure Ollama for use with aGENtrader on EC2 instances.

## Common Issue: Localhost-Only Binding

By default, Ollama only listens on localhost (127.0.0.1), which means it can only be accessed from the same machine. This can cause connection issues when the system tries to use different network interfaces.

### Symptoms
- Ollama appears to be running: `systemctl status ollama` shows active
- `netstat -tulpn | grep ollama` shows it's only listening on 127.0.0.1:11434
- LLM client keeps falling back to Grok API
- Error messages mention "connection refused" or "connection timeout"

## Solution: Configure Ollama to Listen on All Interfaces

For production deployment, Ollama should be configured to listen on all network interfaces (0.0.0.0).

### Manual Fix

```bash
# 1. Stop the Ollama service
sudo systemctl stop ollama

# 2. Create or update the Ollama configuration
sudo mkdir -p /etc/ollama
sudo bash -c 'echo "host = \"0.0.0.0\"" > /etc/ollama/config'

# 3. Start the Ollama service
sudo systemctl start ollama

# 4. Verify it's listening on all interfaces
sudo netstat -tulpn | grep ollama
# Should show: 0.0.0.0:11434
```

### Automatic Fix

The system now includes an automatic fix in the `scripts/ollama_health_check.py` script. This script will:

1. Detect when Ollama is running but only listening on localhost
2. Automatically reconfigure it to listen on all interfaces
3. Restart the service with the new configuration

You can run this script manually:

```bash
python3 scripts/ollama_health_check.py --start --ec2
```

## Verification

After fixing the configuration, you can verify that Ollama is properly configured by:

```bash
# Check if Ollama is running
sudo systemctl status ollama

# Check which interfaces it's listening on
sudo netstat -tulpn | grep ollama
# Should show: 0.0.0.0:11434 (listening on all interfaces)

# Test a simple API request
curl http://localhost:11434/api/version
```

## Troubleshooting

If you're still having issues:

1. Check the Ollama logs: `sudo journalctl -u ollama -n 100`
2. Verify the config file is correct: `cat /etc/ollama/config`
3. Ensure no firewall rules are blocking port 11434
4. Verify the Mistral model is installed: `ollama list`

For comprehensive diagnostics, run:

```bash
python3 scripts/ollama_health_check.py --json
```