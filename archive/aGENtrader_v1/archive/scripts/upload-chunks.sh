#!/bin/bash

# First ensure the file exists on the remote side
./direct-ssh-command.sh "touch /home/ec2-user/aGENtrader/run_simplified_test.py"

# Split the file into chunks and process each chunk
split -b 2000 run_simplified_test.py chunk_
for chunk in chunk_*; do
  chunk_content=$(cat $chunk | sed 's/"/\\"/g' | sed 's/$/\\n/' | tr -d '\n')
  ./direct-ssh-command.sh "echo -e \"$chunk_content\" >> /home/ec2-user/aGENtrader/run_simplified_test.py"
done

# Clean up chunks
rm chunk_*

# Make the script executable
./direct-ssh-command.sh "chmod +x /home/ec2-user/aGENtrader/run_simplified_test.py && echo 'File transferred and made executable.'"
