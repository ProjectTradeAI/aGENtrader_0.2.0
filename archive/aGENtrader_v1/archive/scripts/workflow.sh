
#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
GITHUB_BRANCH="main"

function show_menu {
  clear
  echo -e "${BLUE}=======================================${NC}"
  echo -e "${BLUE}   Trading Bot Development Workflow    ${NC}"
  echo -e "${BLUE}=======================================${NC}"
  echo -e "${YELLOW}1.${NC} Setup GitHub authentication"
  echo -e "${YELLOW}2.${NC} Test application locally"
  echo -e "${YELLOW}3.${NC} Commit and push changes to GitHub"
  echo -e "${YELLOW}4.${NC} Deploy to EC2"
  echo -e "${YELLOW}5.${NC} Check deployment status"
  echo -e "${YELLOW}6.${NC} Exit"
  echo
  echo -ne "${GREEN}Select an option:${NC} "
  read -r option
}

function setup_github {
  echo -e "${GREEN}Setting up GitHub authentication...${NC}"
  ./scripts/setup-github.sh
  echo -e "${GREEN}Press any key to continue...${NC}"
  read -n 1
}

function test_locally {
  echo -e "${GREEN}Testing application locally...${NC}"
  npm run dev
}

function commit_push {
  echo -e "${GREEN}Committing and pushing changes to GitHub...${NC}"
  
  # Check for changes
  if [[ -z $(git status -s) ]]; then
    echo -e "${YELLOW}No changes to commit.${NC}"
    echo -e "${GREEN}Press any key to continue...${NC}"
    read -n 1
    return
  fi
  
  # Show changes
  echo -e "${YELLOW}Changes to commit:${NC}"
  git status -s
  
  # Ask for commit message
  echo -ne "${GREEN}Enter commit message:${NC} "
  read -r commit_message
  
  # Commit and push
  git add .
  git commit -m "$commit_message"
  git push origin "$GITHUB_BRANCH"
  
  echo -e "${GREEN}Changes pushed to GitHub.${NC}"
  echo -e "${GREEN}Press any key to continue...${NC}"
  read -n 1
}

function deploy_ec2 {
  echo -e "${GREEN}Deploying to EC2...${NC}"
  ./scripts/ec2-deploy.sh
  echo -e "${GREEN}Press any key to continue...${NC}"
  read -n 1
}

function check_status {
  echo -e "${GREEN}Checking deployment status...${NC}"
  
  # Get health endpoint locally
  echo -e "${YELLOW}Local health check:${NC}"
  curl -s http://localhost:5000/health
  echo
  
  echo -e "${GREEN}Press any key to continue...${NC}"
  read -n 1
}

# Main loop
while true; do
  show_menu
  
  case $option in
    1) setup_github ;;
    2) test_locally ;;
    3) commit_push ;;
    4) deploy_ec2 ;;
    5) check_status ;;
    6) echo -e "${GREEN}Exiting...${NC}"; exit 0 ;;
    *) echo -e "${RED}Invalid option${NC}"; sleep 2 ;;
  esac
done
