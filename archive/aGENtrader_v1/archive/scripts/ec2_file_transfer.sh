#!/bin/bash
# EC2 File Transfer Utility
# This script helps transfer files to and from the EC2 instance

# Default values
EC2_USER="ec2-user"
EC2_DIR="/home/ec2-user/aGENtrader"
LOCAL_DIR="./ec2_results"
PRIVATE_KEY_FILE="~/.ssh/your-key.pem"  # Update this with your key path

# Function to show usage
show_usage() {
    echo "EC2 File Transfer Utility"
    echo "========================="
    echo "Usage: $0 [options] [command]"
    echo ""
    echo "Commands:"
    echo "  push <local_file>     Push a local file to EC2"
    echo "  pull <remote_file>    Pull a file from EC2 to local machine"
    echo "  sync-to-ec2           Sync local directory to EC2"
    echo "  sync-from-ec2         Sync EC2 results to local machine"
    echo "  run <script> [args]   Run a script on EC2"
    echo "  list-results          List result files on EC2"
    echo ""
    echo "Options:"
    echo "  -i, --identity <file>   SSH private key file"
    echo "  -h, --host <host>       EC2 hostname or IP address"
    echo "  -u, --user <user>       EC2 username (default: ec2-user)"
    echo "  -d, --dir <dir>         EC2 directory (default: /home/ec2-user/aGENtrader)"
    echo "  -l, --local <dir>       Local directory for syncing (default: ./ec2_results)"
    echo "  --help                  Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -i ~/.ssh/key.pem -h 12.34.56.78 push improved_simplified_test.py"
    echo "  $0 -i ~/.ssh/key.pem -h 12.34.56.78 pull results/latest_test.json"
    echo "  $0 -i ~/.ssh/key.pem -h 12.34.56.78 run improved_simplified_test.py --strategy combined"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--identity)
            PRIVATE_KEY_FILE="$2"
            shift 2
            ;;
        -h|--host)
            EC2_HOST="$2"
            shift 2
            ;;
        -u|--user)
            EC2_USER="$2"
            shift 2
            ;;
        -d|--dir)
            EC2_DIR="$2"
            shift 2
            ;;
        -l|--local)
            LOCAL_DIR="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Check if required arguments are provided
if [ -z "$EC2_HOST" ]; then
    echo "Error: EC2 hostname or IP address not provided"
    echo "Use -h or --host to specify the EC2 hostname or IP address"
    exit 1
fi

if [ ! -f "$PRIVATE_KEY_FILE" ] && [ "$1" != "help" ]; then
    echo "Error: SSH private key file not found: $PRIVATE_KEY_FILE"
    echo "Use -i or --identity to specify the SSH private key file"
    exit 1
fi

# Execute command
case $1 in
    push)
        if [ -z "$2" ]; then
            echo "Error: Local file not specified"
            echo "Usage: $0 push <local_file>"
            exit 1
        fi
        
        echo "Pushing $2 to $EC2_USER@$EC2_HOST:$EC2_DIR/"
        scp -i "$PRIVATE_KEY_FILE" "$2" "$EC2_USER@$EC2_HOST:$EC2_DIR/"
        ;;
    
    pull)
        if [ -z "$2" ]; then
            echo "Error: Remote file not specified"
            echo "Usage: $0 pull <remote_file>"
            exit 1
        fi
        
        # Create local directory if it doesn't exist
        mkdir -p "$LOCAL_DIR"
        
        echo "Pulling $EC2_USER@$EC2_HOST:$EC2_DIR/$2 to $LOCAL_DIR/"
        scp -i "$PRIVATE_KEY_FILE" "$EC2_USER@$EC2_HOST:$EC2_DIR/$2" "$LOCAL_DIR/"
        ;;
    
    sync-to-ec2)
        echo "Syncing local directory to EC2: $LOCAL_DIR/ → $EC2_USER@$EC2_HOST:$EC2_DIR/"
        rsync -avz -e "ssh -i $PRIVATE_KEY_FILE" "$LOCAL_DIR/" "$EC2_USER@$EC2_HOST:$EC2_DIR/"
        ;;
    
    sync-from-ec2)
        # Create local directory if it doesn't exist
        mkdir -p "$LOCAL_DIR"
        
        echo "Syncing EC2 results to local machine: $EC2_USER@$EC2_HOST:$EC2_DIR/results/ → $LOCAL_DIR/"
        rsync -avz -e "ssh -i $PRIVATE_KEY_FILE" "$EC2_USER@$EC2_HOST:$EC2_DIR/results/" "$LOCAL_DIR/"
        ;;
    
    run)
        if [ -z "$2" ]; then
            echo "Error: Script not specified"
            echo "Usage: $0 run <script> [args]"
            exit 1
        fi
        
        SCRIPT="$2"
        shift 2  # Remove 'run' and script name from args
        
        echo "Running script on EC2: $SCRIPT $@"
        ssh -i "$PRIVATE_KEY_FILE" "$EC2_USER@$EC2_HOST" "cd $EC2_DIR && python3 $SCRIPT $@"
        ;;
    
    list-results)
        echo "Listing result files on EC2:"
        ssh -i "$PRIVATE_KEY_FILE" "$EC2_USER@$EC2_HOST" "ls -la $EC2_DIR/results/"
        ;;
    
    help)
        show_usage
        ;;
    
    *)
        echo "Error: Unknown command - $1"
        show_usage
        exit 1
        ;;
esac

exit 0