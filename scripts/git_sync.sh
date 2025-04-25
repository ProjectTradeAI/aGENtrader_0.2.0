#!/bin/bash
# git_sync.sh - Synchronize the aGENtrader repository with a remote Git repository
# This script is essential for deployment and version management

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
REMOTE="origin"
BRANCH="main"
COMMIT_MSG="Automated sync $(date +"%Y-%m-%d %H:%M:%S")"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--remote)
      REMOTE="$2"
      shift 2
      ;;
    -b|--branch)
      BRANCH="$2"
      shift 2
      ;;
    -m|--message)
      COMMIT_MSG="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [-r|--remote <name>] [-b|--branch <name>] [-m|--message <msg>]"
      echo "  -r, --remote    Remote repository name (default: origin)"
      echo "  -b, --branch    Branch name (default: main)"
      echo "  -m, --message   Commit message (default: Automated sync with timestamp)"
      echo "  -h, --help      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Display configuration
echo -e "${BLUE}Git Sync Configuration:${NC}"
echo -e "  Remote: ${GREEN}$REMOTE${NC}"
echo -e "  Branch: ${GREEN}$BRANCH${NC}"
echo -e "  Commit: ${GREEN}$COMMIT_MSG${NC}"
echo

# Check if git is initialized
if [ ! -d ".git" ]; then
  echo -e "${RED}Error: Not a git repository.${NC}"
  echo "Please run 'git init' first."
  exit 1
fi

# Add all changes
echo -e "${BLUE}Adding changes...${NC}"
git add .

# Commit changes
echo -e "${BLUE}Committing changes...${NC}"
git commit -m "$COMMIT_MSG" || echo -e "${YELLOW}No changes to commit.${NC}"

# Push to remote
echo -e "${BLUE}Pushing to $REMOTE/$BRANCH...${NC}"
git push "$REMOTE" "$BRANCH" || {
  echo -e "${YELLOW}Push failed. Trying with --force...${NC}"
  git push --force "$REMOTE" "$BRANCH"
}

echo -e "${GREEN}Git sync completed successfully!${NC}"