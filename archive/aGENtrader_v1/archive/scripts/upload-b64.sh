#!/bin/bash

# Encode the file to base64
B64_CONTENT=$(base64 run_simplified_test.py)

# Use direct-ssh-command.sh to create the file from base64
./direct-ssh-command.sh "echo '$B64_CONTENT' | base64 -d > /home/ec2-user/aGENtrader/run_simplified_test.py && echo 'File transferred successfully!'"
