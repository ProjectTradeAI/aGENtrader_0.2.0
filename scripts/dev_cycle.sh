#!/bin/bash
# aGENtrader Dev Cycle Automation Script
# 
# This script automates the development cycle for aGENtrader:
# 1. Pulls latest code changes from selected branch
# 2. Rebuilds Docker image
# 3. Redeploys containers
# 4. Validates deployment
# 5. Logs results
#
# Author: AI Engineer Team
# Created: 2025-04-29
# Updated: 2025-04-30 - Added branch selection feature
#
# USAGE:
#   ./scripts/dev_cycle.sh             # Use default branch (main)
#   ./scripts/dev_cycle.sh -b v2.2.1   # Use branch v2.2.1
#   ./scripts/dev_cycle.sh --branch develop  # Use branch develop

# Get version from the centralized version file
VERSION=$(python3 -c 'from core.version import VERSION; print(VERSION)')

# --- Configuration ---
CONTAINER_NAME="agentrader"
IMAGE_NAME="agentrader"
IMAGE_TAG="latest"
LOG_FILE="dev_cycle_$(date +%Y%m%d_%H%M%S).log"
GITHUB_REPO="origin"
GITHUB_BRANCH="main"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--branch) GITHUB_BRANCH="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# ANSI color codes
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
PURPLE="\033[0;35m"
CYAN="\033[0;36m"
RESET="\033[0m"

# --- Helper Functions ---

# Log message to console and log file
log() {
    local level=$1
    local message=$2
    local color=""
    local prefix=""
    
    # Format timestamp
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Set color and prefix based on level
    case $level in
        "INFO")
            color=$BLUE
            prefix="[INFO]"
            ;;
        "SUCCESS")
            color=$GREEN
            prefix="[SUCCESS]"
            ;;
        "WARNING")
            color=$YELLOW
            prefix="[WARNING]"
            ;;
        "ERROR")
            color=$RED
            prefix="[ERROR]"
            ;;
        "STEP")
            color=$CYAN
            prefix="[STEP]"
            ;;
        *)
            prefix="[LOG]"
            ;;
    esac
    
    # Echo to console with color
    echo -e "${color}${timestamp} ${prefix} ${message}${RESET}"
    
    # Echo to log file without color codes (remove ANSI color codes)
    echo -e "${timestamp} ${prefix} ${message}" | sed 's/\x1b\[[0-9;]*m//g' >> $LOG_FILE
}

# Display section header
section() {
    local title=$1
    local line="-------------------------------------------------------------"
    echo -e "\n${PURPLE}$line${RESET}"
    echo -e "${PURPLE}    $title${RESET}"
    echo -e "${PURPLE}$line${RESET}\n"
    
    # Log to file without colors
    echo -e "\n$line" >> $LOG_FILE
    echo -e "    $title" >> $LOG_FILE
    echo -e "$line\n" >> $LOG_FILE
}

# Check if command succeeds and log result
check_step() {
    local cmd=$1
    local description=$2
    local output_file="step_output.tmp"
    
    log "STEP" "Executing: $description"
    
    # Run command and capture output/result
    eval "$cmd" > $output_file 2>&1
    local result=$?
    
    # Check result
    if [ $result -eq 0 ]; then
        log "SUCCESS" "$description completed successfully"
        if [ -s "$output_file" ]; then
            log "INFO" "Command output (truncated):"
            head -n 10 $output_file | while read -r line; do
                log "INFO" "  > $line"
            done
            
            # If output is larger than 10 lines, show message
            if [ $(wc -l < $output_file) -gt 10 ]; then
                log "INFO" "  > ... (output truncated, see $LOG_FILE for full output)"
                
                # Append full output to log file
                echo "--- Full command output ---" >> $LOG_FILE
                cat $output_file >> $LOG_FILE
                echo "--- End of command output ---" >> $LOG_FILE
            fi
        fi
        rm -f $output_file
        return 0
    else
        log "ERROR" "$description failed with error code $result"
        if [ -s "$output_file" ]; then
            log "ERROR" "Error output:"
            cat $output_file | while read -r line; do
                log "ERROR" "  > $line"
            done
            
            # Append full output to log file
            echo "--- Full error output ---" >> $LOG_FILE
            cat $output_file >> $LOG_FILE
            echo "--- End of error output ---" >> $LOG_FILE
        fi
        rm -f $output_file
        return 1
    fi
}

# --- Pre-flight Checks ---

# Display banner using Python to get the ASCII logo from version.py
echo -e "${CYAN}"
python3 -c "from core.version import MINI_LOGO; print(MINI_LOGO)"
echo -e "${RESET}"
echo -e "${BLUE}aGENtrader ${VERSION} - Automated Development Cycle${RESET} - Started at $(date)\n"

# Create log file
touch $LOG_FILE
log "INFO" "Starting aGENtrader dev cycle automation"
log "INFO" "Log file: $LOG_FILE"

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    log "ERROR" "This script must be run from the root of the aGENtrader repository"
    log "ERROR" "Current directory: $(pwd)"
    exit 1
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    log "ERROR" "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    log "ERROR" "Docker is not running. Please start Docker first."
    exit 1
fi

# --- Ollama Setup ---
section "0. OLLAMA - Setting up LLM service"

# Check if Python3 is available for enhanced Ollama health check
if command -v python3 &> /dev/null; then
    log "INFO" "Using enhanced Ollama health check script"
    
    # Check if we're in EC2 environment
    if grep -q "DEPLOY_ENV=ec2" .env 2>/dev/null; then
        EC2_FLAG="--ec2"
        log "INFO" "Detected EC2 environment from .env file"
    else
        EC2_FLAG=""
    fi
    
    # Run the Ollama health check
    log "INFO" "Running Ollama health check..."
    HEALTH_CHECK_OUTPUT=$(python3 scripts/ollama_health_check.py --json $EC2_FLAG 2>&1)
    HEALTH_CHECK_STATUS=$?
    
    # Parse the JSON output
    OLLAMA_INSTALLED=$(echo "$HEALTH_CHECK_OUTPUT" | grep -o '"installed": true' || echo "")
    OLLAMA_RUNNING=$(echo "$HEALTH_CHECK_OUTPUT" | grep -o '"running": true' || echo "")
    OLLAMA_ENDPOINT=$(echo "$HEALTH_CHECK_OUTPUT" | grep -o '"endpoint": "[^"]*"' | cut -d'"' -f4 || echo "")
    
    # Check if Ollama is installed
    if [[ -z "$OLLAMA_INSTALLED" ]]; then
        log "WARNING" "Ollama is not installed. Will attempt to install it."
        
        # Ask user for confirmation
        read -p "Install Ollama now? (y/n): " install_ollama
        
        if [[ $install_ollama == "y" || $install_ollama == "Y" ]]; then
            log "INFO" "Installing Ollama..."
            
            # Installation based on the official documentation
            if check_step "curl -fsSL https://ollama.com/install.sh | sh" "Installing Ollama"; then
                log "SUCCESS" "Ollama installed successfully"
            else
                log "WARNING" "Ollama installation failed. System will use fallback LLM providers."
                log "INFO" "You can install Ollama manually later: curl -fsSL https://ollama.com/install.sh | sh"
            fi
        else
            log "INFO" "Ollama installation skipped. System will use fallback LLM providers."
        fi
    else
        log "INFO" "Ollama is already installed"
    fi
    
    # Check if Ollama is running
    if [[ -z "$OLLAMA_RUNNING" ]]; then
        log "INFO" "Ollama server is not running. Attempting to start..."
        
        # Start Ollama using the health check script
        if python3 scripts/ollama_health_check.py --start $EC2_FLAG; then
            log "SUCCESS" "Ollama server started successfully"
            
            # Update the running state and endpoint
            HEALTH_CHECK_OUTPUT=$(python3 scripts/ollama_health_check.py --json $EC2_FLAG 2>&1)
            OLLAMA_RUNNING=$(echo "$HEALTH_CHECK_OUTPUT" | grep -o '"running": true' || echo "")
            OLLAMA_ENDPOINT=$(echo "$HEALTH_CHECK_OUTPUT" | grep -o '"endpoint": "[^"]*"' | cut -d'"' -f4 || echo "")
        else
            log "WARNING" "Failed to start Ollama server. System will use fallback LLM providers."
            log "INFO" "If on EC2, try manually: 'sudo systemctl start ollama'"
        fi
    else
        log "SUCCESS" "Ollama server is already running at: $OLLAMA_ENDPOINT"
    fi
    
    # Check and pull required models if needed
    if [[ ! -z "$OLLAMA_RUNNING" ]]; then
        log "INFO" "Checking if required models are available..."
        
        # Get model status
        MODEL_CHECK_OUTPUT=$(python3 scripts/ollama_health_check.py --check-models --json $EC2_FLAG 2>&1)
        MODEL_CHECK_STATUS=$?
        
        # Check if we have mistral models
        MISTRAL_AVAILABLE=$(echo "$MODEL_CHECK_OUTPUT" | grep -o '"mistral": true' || echo "")
        
        if [[ -z "$MISTRAL_AVAILABLE" ]]; then
            log "INFO" "Mistral model not found. Attempting to pull it..."
            
            # Ask user for confirmation as this is a moderately sized download
            read -p "Download Mistral model (~4GB)? Uses less memory than Mixtral. (y/n): " pull_mistral
            
            if [[ $pull_mistral == "y" || $pull_mistral == "Y" ]]; then
                if check_step "ollama pull mistral" "Downloading Mistral model"; then
                    log "SUCCESS" "Mistral model downloaded successfully"
                else
                    log "WARNING" "Failed to download Mistral model. System will use fallback LLM providers."
                fi
            else
                log "INFO" "Mistral model download skipped. System will use fallback LLM providers."
            fi
        else
            log "SUCCESS" "Mistral model is already downloaded and available"
        fi
    fi
else
    # Fallback to basic checks if Python3 is not available
    log "WARNING" "Python3 not found for enhanced checks. Using basic Ollama checks."
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        log "WARNING" "Ollama is not installed. Will attempt to install it."
        
        # Ask user for confirmation
        read -p "Install Ollama now? (y/n): " install_ollama
        
        if [[ $install_ollama == "y" || $install_ollama == "Y" ]]; then
            log "INFO" "Installing Ollama..."
            
            # Installation based on the official documentation
            if check_step "curl -fsSL https://ollama.com/install.sh | sh" "Installing Ollama"; then
                log "SUCCESS" "Ollama installed successfully"
            else
                log "WARNING" "Ollama installation failed. System will use fallback LLM providers."
                log "INFO" "You can install Ollama manually later: curl -fsSL https://ollama.com/install.sh | sh"
            fi
        else
            log "INFO" "Ollama installation skipped. System will use fallback LLM providers."
        fi
    else
        log "INFO" "Ollama is already installed"
    fi
    
    # Check if Ollama is running
    if command -v ollama &> /dev/null; then
        log "INFO" "Checking if Ollama server is running..."
        
        # Test connectivity to Ollama
        if curl -s http://localhost:11434 &> /dev/null; then
            log "SUCCESS" "Ollama server is already running"
        else
            log "INFO" "Starting Ollama server..."
            
            # Try to detect if we're on EC2
            if grep -q "DEPLOY_ENV=ec2" .env 2>/dev/null; then
                log "INFO" "Detected EC2 environment, trying systemctl first..."
                if sudo systemctl start ollama 2>/dev/null; then
                    log "SUCCESS" "Started Ollama with systemctl"
                    sleep 5 # Give it time to start
                else
                    # Fall back to regular method
                    log "INFO" "Systemctl failed, trying direct method..."
                    if check_step "ollama serve > /tmp/ollama.log 2>&1 &" "Starting Ollama server"; then
                        sleep 5 # Give it more time on EC2
                    fi
                fi
            else
                # Regular method for non-EC2
                if check_step "ollama serve > /tmp/ollama.log 2>&1 &" "Starting Ollama server"; then
                    # Give it a moment to start
                    sleep 2
                fi
            fi
            
            log "INFO" "Waiting for Ollama server to initialize..."
            
            # Check if it's now running
            attempt=0
            while [ $attempt -lt 5 ]; do
                if curl -s http://localhost:11434 &> /dev/null; then
                    log "SUCCESS" "Ollama server started successfully"
                    break
                fi
                attempt=$((attempt + 1))
                sleep 2
            done
            
            if [ $attempt -eq 5 ]; then
                log "WARNING" "Ollama server did not start properly. Check /tmp/ollama.log for details."
                log "INFO" "System will use fallback LLM providers."
            fi
        fi
        
        # Check if Mistral model is available
        if curl -s http://localhost:11434 &> /dev/null; then
            log "INFO" "Checking if Mistral model is available..."
            
            # List models and check if mistral is available
            models_output=$(ollama list 2>&1)
            if echo "$models_output" | grep -q "mistral"; then
                log "SUCCESS" "Mistral model is already downloaded and available"
            else
                log "INFO" "Mistral model not found. Attempting to pull it..."
                
                # Ask user for confirmation as this is a moderately sized download
                read -p "Download Mistral model (~4GB)? Uses less memory than Mixtral. (y/n): " pull_mistral
                
                if [[ $pull_mistral == "y" || $pull_mistral == "Y" ]]; then
                    if check_step "ollama pull mistral" "Downloading Mistral model"; then
                        log "SUCCESS" "Mistral model downloaded successfully"
                    else
                        log "WARNING" "Failed to download Mistral model. System will use fallback LLM providers."
                    fi
                else
                    log "INFO" "Mistral model download skipped. System will use fallback LLM providers."
                fi
            fi
        fi
    fi
fi

# --- Main Dev Cycle Steps ---

section "1. GIT PULL - Updating from repository"

# Get current branch for info
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "Detached HEAD")
log "INFO" "Current branch: $CURRENT_BRANCH"
log "INFO" "Target branch for pull: $GITHUB_BRANCH"

# Show available branches
log "INFO" "Available branches:"
git branch -r | grep -v '\->' | grep "origin/" | sed 's/origin\//  /' | while read -r branch; do
    if [[ "$branch" == "  $GITHUB_BRANCH" ]]; then
        log "INFO" "  > $branch (selected)"
    else
        log "INFO" "  > $branch"
    fi
done

# Check if the branch exists
if ! git ls-remote --heads $GITHUB_REPO $GITHUB_BRANCH | grep -q "$GITHUB_BRANCH"; then
    log "ERROR" "Branch '$GITHUB_BRANCH' does not exist in '$GITHUB_REPO'. Available branches:"
    git branch -r | grep -v '\->' | grep "origin/" | sed 's/origin\//  /' | while read -r branch; do
        log "INFO" "  > $branch"
    done
    exit 1
fi

# Ask for confirmation if switching branches
if [[ "$CURRENT_BRANCH" != "$GITHUB_BRANCH" ]]; then
    log "WARNING" "You are about to switch from branch '$CURRENT_BRANCH' to '$GITHUB_BRANCH'"
    read -p "Continue with branch switch? (y/n): " confirm_switch
    
    if [[ ! "$confirm_switch" =~ ^[Yy]$ ]]; then
        log "INFO" "Branch switch cancelled. Exiting."
        exit 0
    fi
    
    # Checkout the new branch
    if check_step "git checkout $GITHUB_BRANCH" "Switching to branch $GITHUB_BRANCH"; then
        log "SUCCESS" "Switched to branch $GITHUB_BRANCH"
    else
        log "ERROR" "Failed to switch to branch $GITHUB_BRANCH. Aborting."
        exit 1
    fi
fi

# Fetch and pull the latest changes
if check_step "git fetch $GITHUB_REPO $GITHUB_BRANCH" "Fetching latest changes from repository"; then
    current_commit=$(git rev-parse HEAD)
    
    if check_step "git pull $GITHUB_REPO $GITHUB_BRANCH" "Pulling latest changes"; then
        new_commit=$(git rev-parse HEAD)
        
        if [ "$current_commit" == "$new_commit" ]; then
            log "INFO" "No new changes to pull. Already at latest commit."
        else
            log "INFO" "Updated from $current_commit to $new_commit"
            log "INFO" "Changes summary:"
            git log --oneline $current_commit..$new_commit | while read -r line; do
                log "INFO" "  > $line"
            done
        fi
    else
        log "ERROR" "Git pull failed. Aborting dev cycle."
        exit 1
    fi
else
    log "ERROR" "Git fetch failed. Aborting dev cycle."
    exit 1
fi

section "2. DOCKER BUILD - Building Docker image"

# Build the Docker image
if [ -f "deployment/build_image.sh" ]; then
    if check_step "bash deployment/build_image.sh" "Building Docker image"; then
        log "SUCCESS" "Docker image built successfully"
    else
        log "ERROR" "Docker image build failed. Aborting dev cycle."
        exit 1
    fi
else
    log "ERROR" "Build script not found at deployment/build_image.sh"
    exit 1
fi

section "3. DEPLOYMENT - Deploying updated container"

# Deploy the container
if [ -f "deployment/deploy_local.sh" ]; then
    # Prefer local deployment for development
    if check_step "bash deployment/deploy_local.sh" "Deploying container locally"; then
        log "SUCCESS" "Container deployed successfully"
    else
        log "ERROR" "Local deployment failed. Aborting dev cycle."
        exit 1
    fi
elif [ -f "deployment/deploy_ec2.sh" ]; then
    # If EC2 deployment script exists but no local deploy script
    log "WARNING" "Local deployment script not found. Will use EC2 deployment script."
    
    # Prompt user for confirmation
    read -p "Continue with EC2 deployment? (y/n): " ec2_confirm
    if [[ $ec2_confirm == "y" || $ec2_confirm == "Y" ]]; then
        if check_step "bash deployment/deploy_ec2.sh" "Deploying to EC2"; then
            log "SUCCESS" "Container deployed to EC2 successfully"
        else
            log "ERROR" "EC2 deployment failed. Aborting dev cycle."
            exit 1
        fi
    else
        log "ERROR" "Deployment cancelled by user. Aborting dev cycle."
        exit 1
    fi
else
    log "ERROR" "Deployment scripts not found at deployment/deploy_local.sh or deployment/deploy_ec2.sh"
    exit 1
fi

section "4. VALIDATION - Verifying deployment"

# Run deployment validation
if [ -f "deployment/validate_deployment.py" ]; then
    log "INFO" "Running enhanced deployment validation..."
    
    # The validation script now automatically detects container names and
    # falls back to local process checks if Docker is not available
    
    # Run the validation script
    if check_step "python3 deployment/validate_deployment.py" "Validating deployment"; then
        log "SUCCESS" "Deployment validation passed"
    else
        log "WARNING" "Deployment validation reported issues. See output above."
        
        # Get container status if Docker is available
        if command -v docker &> /dev/null; then
            # Show container status for debugging
            actual_container_name=$(docker ps --format "{{.Names}}" | grep -i agentrader | head -1)
            
            if [ -n "$actual_container_name" ]; then
                log "INFO" "Container is running:"
                docker ps | grep -i "agentrader" | while read -r line; do
                    log "INFO" "  > $line"
                done
                
                # Offer to show logs as additional debugging info
                log "INFO" "You can check container logs after completion with: docker logs $actual_container_name"
            else
                log "WARNING" "No aGENtrader container appears to be running."
                
                # Check if containers exist but are stopped
                stopped_containers=$(docker ps -a --format "{{.Names}}" | grep -i agentrader)
                if [ -n "$stopped_containers" ]; then
                    log "INFO" "Found stopped aGENtrader containers:"
                    docker ps -a | grep -i "agentrader" | while read -r line; do
                        log "INFO" "  > $line"
                    done
                    
                    log "INFO" "You may want to restart one of these containers or check their logs."
                fi
            fi
        else
            # Docker not available, check for local processes
            log "INFO" "Docker not available. Checking for local processes..."
            ps aux | grep -i "python.*main.py\|python.*run.py" | grep -v grep | while read -r line; do
                log "INFO" "  > $line"
            done
        fi
    fi
else
    log "WARNING" "Validation script not found at deployment/validate_deployment.py"
    log "WARNING" "Checking deployment status manually..."
    
    # Basic container check if validation script is missing
    if command -v docker &> /dev/null; then
        if docker ps | grep -qi "agentrader"; then
            actual_container_name=$(docker ps --format "{{.Names}}" | grep -i agentrader | head -1)
            log "INFO" "Container is running:"
            docker ps | grep -i "agentrader" | while read -r line; do
                log "INFO" "  > $line"
            done
            
            # Show recent logs
            log "INFO" "Recent container logs:"
            docker logs --tail 10 $actual_container_name 2>&1 | while read -r line; do
                log "INFO" "  > $line"
            done
        else
            log "WARNING" "No aGENtrader container appears to be running."
            
            # Check for local Python processes
            log "INFO" "Checking for local processes instead..."
            ps aux | grep -i "python.*main.py\|python.*run.py" | grep -v grep | while read -r line; do
                log "INFO" "  > $line"
            done
        fi
    else
        # Docker not available, check for local processes
        log "INFO" "Docker not available. Checking for local processes..."
        ps aux | grep -i "python.*main.py\|python.*run.py" | grep -v grep | while read -r line; do
            log "INFO" "  > $line"
        done
        
        # Check if log files exist and show last few lines
        if [ -d "logs" ]; then
            log_files=$(find logs -name "*.log" -o -name "*.logl" | head -3)
            if [ -n "$log_files" ]; then
                log "INFO" "Found log files:"
                for log_file in $log_files; do
                    log "INFO" "  > $log_file (last 5 lines):"
                    tail -n 5 "$log_file" | while read -r line; do
                        log "INFO" "    $line"
                    done
                done
            else
                log "WARNING" "No log files found in logs/ directory."
            fi
        else
            log "WARNING" "No logs directory found."
        fi
    fi
fi

section "5. SUMMARY - Development Cycle Completed"

# Display summary
log "SUCCESS" "Dev cycle completed successfully"
log "INFO" "Current branch: $(git branch --show-current)"
log "INFO" "Current commit: $(git rev-parse --short HEAD)"

# Check if Docker is available
if command -v docker &> /dev/null; then
    # Get actual container name
    actual_container_name=$(docker ps --format "{{.Names}}" | grep -i agentrader | head -1)
    if [ -n "$actual_container_name" ]; then
        log "INFO" "Current container: $(docker ps | grep -i "$actual_container_name")"
        
        # --- Optional Log Viewing for Docker ---
        echo
        echo -e "${YELLOW}Would you like to:${RESET}"
        echo "  1) Tail Docker container logs"
        echo "  2) Exit"
        
        read -p "Enter your choice (1/2): " log_choice
        
        case $log_choice in
            1)
                echo -e "\n${CYAN}Tailing logs for $actual_container_name container (Ctrl+C to exit):${RESET}\n"
                docker logs -f "$actual_container_name"
                ;;
            *)
                echo -e "\n${GREEN}Dev cycle complete. Exiting.${RESET}"
                ;;
        esac
    else
        log "INFO" "No running aGENtrader container found"
        
        # Check if local Python process is running
        python_process=$(ps aux | grep -i "python.*main.py\|python.*run.py" | grep -v grep | head -1)
        if [ -n "$python_process" ]; then
            log "INFO" "Local Python process: $python_process"
        fi
        
        # --- Optional Log Viewing for Local Files ---
        if [ -d "logs" ]; then
            echo
            echo -e "${YELLOW}Would you like to:${RESET}"
            echo "  1) Tail local log file"
            echo "  2) Exit"
            
            read -p "Enter your choice (1/2): " log_choice
            
            case $log_choice in
                1)
                    log_files=$(find logs -name "*.log" -o -name "*.logl" | head -1)
                    if [ -n "$log_files" ]; then
                        echo -e "\n${CYAN}Tailing logs from $log_files (Ctrl+C to exit):${RESET}\n"
                        tail -f "$log_files"
                    else
                        echo -e "\n${YELLOW}No log files found.${RESET}"
                    fi
                    ;;
                *)
                    echo -e "\n${GREEN}Dev cycle complete. Exiting.${RESET}"
                    ;;
            esac
        else
            echo -e "\n${GREEN}Dev cycle complete. Exiting.${RESET}"
        fi
    fi
else
    # Check if local Python process is running
    python_process=$(ps aux | grep -i "python.*main.py\|python.*run.py" | grep -v grep | head -1)
    if [ -n "$python_process" ]; then
        log "INFO" "Local Python process: $python_process"
    else
        log "INFO" "No running aGENtrader process found"
    fi
    
    # --- Optional Log Viewing for Local Files ---
    if [ -d "logs" ]; then
        echo
        echo -e "${YELLOW}Would you like to:${RESET}"
        echo "  1) Tail local log file"
        echo "  2) Exit"
        
        read -p "Enter your choice (1/2): " log_choice
        
        case $log_choice in
            1)
                log_files=$(find logs -name "*.log" -o -name "*.logl" | head -1)
                if [ -n "$log_files" ]; then
                    echo -e "\n${CYAN}Tailing logs from $log_files (Ctrl+C to exit):${RESET}\n"
                    tail -f "$log_files"
                else
                    echo -e "\n${YELLOW}No log files found.${RESET}"
                fi
                ;;
            *)
                echo -e "\n${GREEN}Dev cycle complete. Exiting.${RESET}"
                ;;
        esac
    else
        echo -e "\n${GREEN}Dev cycle complete. Exiting.${RESET}"
    fi
fi

# Completion message
echo
echo -e "${GREEN}✅ Dev Cycle Complete - System updated and running!${RESET}"
echo -e "${BLUE}You can find the dev cycle log at: ${LOG_FILE}${RESET}"
echo

exit 0