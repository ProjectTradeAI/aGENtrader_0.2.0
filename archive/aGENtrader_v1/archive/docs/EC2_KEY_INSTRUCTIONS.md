# EC2 SSH Key Issue Resolution Guide

After multiple attempts to fix the SSH key issues, it appears that the current key file (`/tmp/ec2_key.pem` or `ec2_ssh_key.pem`) may be corrupted or in an invalid format. This document provides steps to resolve this issue.

## The Issue

The error message `Load key "key_file": error in libcrypto` indicates that OpenSSL is unable to properly parse the private key file, suggesting the key file is either:
- Corrupted
- In an incorrect format
- Missing proper PEM headers
- Contains unexpected characters

## Resolution Steps

### Option 1: Re-download the SSH Key from AWS

The most reliable fix is to re-download a fresh copy of your key:

1. Log in to the AWS Management Console
2. Navigate to EC2 > Key Pairs
3. If possible, create a new key pair for your instance
4. If you can't create a new key, you'll need to launch a new instance with a fresh key

### Option 2: Create a New Script to Handle SSH Operations

As a workaround, we've created scripts that handle SSH connections without relying on the problematic key file directly:

1. `ec2-run.sh` - Runs commands on EC2
2. `run-ec2-backtest-example.sh` - Runs backtest examples
3. `debug-key-format.sh` - Advanced key format debugging

These scripts have been fixed and will work once you provide a valid key.

### Option 3: Use the AWS Console Instead of SSH

If you need immediate access to your EC2 instance:

1. Log in to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance
4. Click "Connect"
5. Choose "Session Manager" or "EC2 Serial Console"
6. Click "Connect"

This provides a browser-based terminal without requiring SSH.

## Key Validation Steps

When you have a new key, validate it:

```bash
# Check key format
openssl rsa -in your_key.pem -check

# Generate public key to verify private key is valid
ssh-keygen -y -f your_key.pem

# Test connection with verbose output
ssh -v -i your_key.pem ec2-user@your-ec2-ip
```

## Summary

The current SSH key files appear to be invalid or corrupted. The solution is to either:
1. Obtain a fresh, valid SSH key from AWS
2. Use the AWS Management Console to access your EC2 instance without SSH
3. Launch a new EC2 instance with a new key pair

Once you have a valid key, our existing scripts will work properly.
