#!/bin/bash
# Alternative approach to gather EC2 results without SSH

# Configuration
INSTANCE_ID="i-XXXXXXXXXXXX"  # Replace with your actual instance ID
REGION="eu-west-1"           # Replace with your AWS region
OUTPUT_DIR="ec2_results"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "=================================================="
echo "  EC2 Results Gatherer (Non-SSH Method)"
echo "=================================================="
echo
echo "This script provides alternatives to SSH for retrieving backtest results"
echo "from your EC2 instance. Some options require AWS CLI configuration."
echo

# Display options
echo "Available options:"
echo "1. Use AWS CLI to send commands via SSM (requires AWS CLI setup)"
echo "2. Instructions for downloading via AWS Console"
echo "3. Setup AWS S3 sync for results (requires S3 bucket)"
echo "q. Quit"
echo

read -p "Select an option: " choice

case "$choice" in
  1)
    echo "Using AWS CLI to execute commands via SSM..."
    echo "NOTE: This requires AWS CLI to be configured with appropriate permissions."
    echo
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    echo "Executing command to list backtest results..."
    aws ssm send-command \
      --instance-ids "$INSTANCE_ID" \
      --document-name "AWS-RunShellScript" \
      --region "$REGION" \
      --parameters commands="find /home/ec2-user/aGENtrader/results -type f -name \"*.json\" -o -name \"*.txt\" | sort" \
      --output text
    
    echo
    echo "To download a specific file, modify and use this command:"
    echo 'aws ssm send-command --instance-ids "$INSTANCE_ID" --document-name "AWS-RunShellScript" --region "$REGION" --parameters commands="cat /path/to/result/file.json" --output text > ec2_results/output.json'
    ;;
    
  2)
    echo "Instructions for downloading via AWS Console:"
    echo "---------------------------------------------"
    echo "1. Log in to AWS Management Console"
    echo "2. Navigate to EC2 > Instances"
    echo "3. Select your instance ($INSTANCE_ID)"
    echo "4. Click 'Connect'"
    echo "5. Choose 'Session Manager' and click 'Connect'"
    echo "6. In the browser terminal, run:"
    echo "   cd /home/ec2-user/aGENtrader"
    echo "   ls -la results/"
    echo "7. To view a result file, use:"
    echo "   cat results/filename.json"
    echo "8. To create a downloadable archive of results:"
    echo "   tar -czvf results.tar.gz results/"
    echo "   This will create results.tar.gz which you can download"
    echo "9. You can use the AWS S3 console to upload this file to an"
    echo "   S3 bucket, then download it to your local machine"
    ;;
    
  3)
    echo "Setting up AWS S3 sync for results:"
    echo "---------------------------------"
    echo "1. Create an S3 bucket (if you don't have one already)"
    echo "2. Install AWS CLI on your EC2 instance"
    echo "3. Configure proper IAM roles or credentials"
    echo "4. Run this command on your EC2 instance:"
    echo "   aws s3 sync /home/ec2-user/aGENtrader/results/ s3://your-bucket-name/results/"
    echo "5. Download the results from S3 to your local machine:"
    echo "   aws s3 sync s3://your-bucket-name/results/ ./ec2_results/"
    echo
    echo "You can automate this by creating a cron job on your EC2 instance."
    ;;
    
  q|Q)
    echo "Exiting..."
    exit 0
    ;;
    
  *)
    echo "Invalid option selected."
    exit 1
    ;;
esac

echo
echo "Done!"
