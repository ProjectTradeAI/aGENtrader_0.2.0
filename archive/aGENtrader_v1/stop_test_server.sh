#!/bin/bash
# Stop script for the Trading System API Server

echo "Stopping Trading System API Server..."

# Check if the PID file exists
if [ -f "server.pid" ]; then
    PID=$(cat server.pid)
    
    # Check if the process is running
    if ps -p $PID > /dev/null; then
        echo "Stopping server with PID $PID..."
        kill $PID
        
        # Wait for the process to stop (up to 5 seconds)
        COUNT=0
        while ps -p $PID > /dev/null && [ $COUNT -lt 5 ]; do
            sleep 1
            COUNT=$((COUNT+1))
        done
        
        # If the process is still running, force kill
        if ps -p $PID > /dev/null; then
            echo "Process did not terminate gracefully, force killing..."
            kill -9 $PID
        fi
    else
        echo "No server process found with PID $PID."
    fi
    
    # Remove the PID file
    rm server.pid
    echo "Server stopped."
    
else
    echo "No server PID file found."
    
    # Try to find and kill the process using port
    PORT=5050
    for p in $(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1); do
        if [ ! -z "$p" ]; then
            echo "Found process $p using port $PORT, stopping it..."
            kill $p || kill -9 $p
        fi
    done
    
    PORT=5051
    for p in $(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1); do
        if [ ! -z "$p" ]; then
            echo "Found process $p using port $PORT, stopping it..."
            kill $p || kill -9 $p
        fi
    done
    
    # Alternative method: find by process name
    PIDS=$(ps aux | grep "[n]ode test_simple_api.js" | awk '{print $2}')
    if [ ! -z "$PIDS" ]; then
        echo "Found node processes running test_simple_api.js:"
        for p in $PIDS; do
            echo "Stopping process $p..."
            kill $p || kill -9 $p
        done
    fi
fi

echo "Server shutdown completed."