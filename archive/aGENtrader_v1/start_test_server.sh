#!/bin/bash
# Start script for the Trading System API Server

echo "Starting Trading System API Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js before continuing."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm before continuing."
    exit 1
fi

# Check if required npm packages are installed
if [ ! -d "node_modules/express" ] || [ ! -d "node_modules/cors" ]; then
    echo "Installing required npm packages..."
    npm install express cors
fi

# Check if the API server file exists
if [ ! -f "test_simple_api.js" ]; then
    echo "Error: test_simple_api.js file not found."
    exit 1
fi

# Find an available port (default: 5050)
PORT=5050
PORT_ENV=""

# Check if port is already in use, try an alternative if needed
if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
    PORT=5051
    PORT_ENV="PORT=$PORT"
    echo "Port 5050 is in use, using port $PORT instead."
fi

# Start the server in the background with a specified PORT
echo "Starting server on port $PORT..."
nohup $PORT_ENV node test_simple_api.js > server.log 2>&1 &

# Save the process ID to a file
echo $! > server.pid
echo "Server started with PID $(cat server.pid)"
echo "Log file: server.log"
echo ""
echo "API is available at: http://localhost:$PORT"
echo "To stop the server, run: ./stop_test_server.sh"