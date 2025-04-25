#!/bin/bash
# aGENtrader v2 Monitoring Script
# This script monitors the running aGENtrader system and verifies logs

# Colors for console output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}aGENtrader v2 System Monitoring${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Check container status
echo -e "${YELLOW}Checking container status...${NC}"
CONTAINER_ID=$(docker ps -qf "name=agentrader")
if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Error: agentrader container is not running.${NC}"
    echo -e "${YELLOW}Would you like to see recent logs from stopped containers? [y/N]${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
        docker-compose logs --tail=50
    fi
    exit 1
fi
echo -e "${GREEN}Container running with ID: $CONTAINER_ID${NC}"

# Get container details
CONTAINER_UP_TIME=$(docker inspect --format='{{.State.StartedAt}}' $CONTAINER_ID)
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' $CONTAINER_ID)
CONTAINER_HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' $CONTAINER_ID)

echo -e "${CYAN}Container Details:${NC}"
echo -e "  Status: ${GREEN}$CONTAINER_STATUS${NC}"
echo -e "  Health: ${GREEN}$CONTAINER_HEALTH${NC}"
echo -e "  Started: ${GREEN}$CONTAINER_UP_TIME${NC}"

# Check screen session
echo -e "${YELLOW}Checking screen session...${NC}"
if ! screen -list | grep -q "aGENtrader"; then
    echo -e "${RED}Warning: No 'aGENtrader' screen session found.${NC}"
    echo -e "${YELLOW}The container may be running directly or in another session.${NC}"
else
    echo -e "${GREEN}Screen session 'aGENtrader' is active.${NC}"
fi

# Check log files
echo -e "${YELLOW}Checking log files...${NC}"
LOG_FILES=(
    "logs/trade_book.jsonl"
    "logs/sentiment_feed.jsonl"
    "logs/trade_performance.jsonl"
    "logs/rejected_trades.jsonl"
    "logs/trigger_timestamps.jsonl"
    "logs/agentrader.log"
)

echo -e "${CYAN}Log Status:${NC}"
for log in "${LOG_FILES[@]}"; do
    if [ -f "$log" ]; then
        LOG_SIZE=$(du -h "$log" | cut -f1)
        LOG_ENTRIES=$(grep -c . "$log" 2>/dev/null || echo "0")
        LAST_MODIFIED=$(stat -c %y "$log" 2>/dev/null || stat -f "%Sm" "$log" 2>/dev/null)
        echo -e "  ${GREEN}✓${NC} $log ($LOG_SIZE, $LOG_ENTRIES entries, last modified: $LAST_MODIFIED)"
    else
        echo -e "  ${RED}✗${NC} $log (not found)"
    fi
done

# Check for recent activity
echo -e "${YELLOW}Checking for recent activity...${NC}"
LATEST_LOG=$(ls -t logs/*.jsonl 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    LAST_ENTRY=$(tail -n 1 "$LATEST_LOG" 2>/dev/null)
    if [ -n "$LAST_ENTRY" ]; then
        echo -e "${GREEN}Most recent log entry (from $LATEST_LOG):${NC}"
        echo -e "${CYAN}$LAST_ENTRY${NC}"
    else
        echo -e "${RED}No entries found in $LATEST_LOG${NC}"
    fi
else
    echo -e "${RED}No log files found in logs/ directory${NC}"
fi

# Show recent Docker logs
echo -e "${YELLOW}Recent Docker logs:${NC}"
docker logs --tail=10 $CONTAINER_ID

# Memory and CPU usage
echo -e "${YELLOW}Container resource usage:${NC}"
docker stats --no-stream $CONTAINER_ID

# Option to view more detailed logs
echo -e "${YELLOW}Would you like to see more detailed logs? [y/N]${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    echo -e "${YELLOW}Choose a log to view:${NC}"
    echo -e "  1) Docker container logs (last 50 lines)"
    echo -e "  2) trade_book.jsonl (last 5 entries)"
    echo -e "  3) sentiment_feed.jsonl (last 5 entries)"
    echo -e "  4) trigger_timestamps.jsonl (last 5 entries)"
    echo -e "  5) agentrader.log (last 20 lines)"
    echo -e "  6) All available logs"
    read -r choice
    
    case $choice in
        1)
            docker logs --tail=50 $CONTAINER_ID
            ;;
        2)
            if [ -f "logs/trade_book.jsonl" ]; then
                echo -e "${CYAN}Last 5 entries from trade_book.jsonl:${NC}"
                tail -n 5 logs/trade_book.jsonl | jq '.'
            else
                echo -e "${RED}logs/trade_book.jsonl not found${NC}"
            fi
            ;;
        3)
            if [ -f "logs/sentiment_feed.jsonl" ]; then
                echo -e "${CYAN}Last 5 entries from sentiment_feed.jsonl:${NC}"
                tail -n 5 logs/sentiment_feed.jsonl | jq '.'
            else
                echo -e "${RED}logs/sentiment_feed.jsonl not found${NC}"
            fi
            ;;
        4)
            if [ -f "logs/trigger_timestamps.jsonl" ]; then
                echo -e "${CYAN}Last 5 entries from trigger_timestamps.jsonl:${NC}"
                tail -n 5 logs/trigger_timestamps.jsonl | jq '.'
            else
                echo -e "${RED}logs/trigger_timestamps.jsonl not found${NC}"
            fi
            ;;
        5)
            if [ -f "logs/agentrader.log" ]; then
                echo -e "${CYAN}Last 20 lines from agentrader.log:${NC}"
                tail -n 20 logs/agentrader.log
            else
                echo -e "${RED}logs/agentrader.log not found${NC}"
            fi
            ;;
        6)
            for log in "${LOG_FILES[@]}"; do
                if [ -f "$log" ]; then
                    echo -e "${CYAN}Contents of $log:${NC}"
                    if [[ "$log" == *.jsonl ]]; then
                        tail -n 3 "$log" | jq '.'
                    else
                        tail -n 10 "$log"
                    fi
                    echo -e ""
                fi
            done
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
fi

# Final status message
echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}aGENtrader v2 Monitoring Complete!${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo -e "${YELLOW}Container ID:${NC} $CONTAINER_ID"
echo -e ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  - View screen session: ${GREEN}screen -r aGENtrader${NC}"
echo -e "  - View Docker logs: ${GREEN}docker logs -f $CONTAINER_ID${NC}"
echo -e "  - Run the tests: ${GREEN}python run_all_tests.py${NC}"
echo -e "  - Deploy Binance integration: ${GREEN}./deploy_binance_integration.sh${NC}"
echo -e "${BLUE}=======================================================${NC}"