#!/bin/bash

# Script to find the largest files on the EC2 instance
ssh -i ec2_ssh_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_PUBLIC_IP "sudo find / -type f -size +100M -exec ls -lah {} \; 2>/dev/null | sort -k5hr | head -20"
