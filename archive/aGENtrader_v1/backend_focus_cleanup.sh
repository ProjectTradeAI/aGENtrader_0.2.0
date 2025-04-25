#!/bin/bash
# Cleanup script focused on removing frontend files and outdated logs/tests
echo "Starting backend-focused cleanup process..."

# Create archive directories if they don't exist
mkdir -p archive/{frontend,logs,test_outputs,results}

# Archive frontend-related files and directories
echo "Archiving frontend-related files and directories..."
mv client archive/frontend/ 2>/dev/null
mv dist archive/frontend/ 2>/dev/null
mv shared archive/frontend/ 2>/dev/null
mv server/api archive/frontend/ 2>/dev/null

# Move frontend dependencies in package.json to a backup file
if [ -f "package.json" ]; then
    echo "Backing up package.json..."
    cp package.json archive/frontend/package.json.original
    
    # For now, we'll leave package.json as is, but in the future we might 
    # want to create a minimal version with only backend dependencies
fi

# Archive all log files
echo "Archiving logs..."
find . -name "*.log" -type f -not -path "./archive/*" | while read -r logfile; do
    echo "  - Archiving $logfile"
    cp "$logfile" archive/logs/
    rm "$logfile"
done

# Archive all test results and outputs
echo "Archiving test results and outputs..."
mv test_outputs/* archive/test_outputs/ 2>/dev/null
find . -path "*/results/*" -type f -not -path "./archive/*" | while read -r resultfile; do
    echo "  - Archiving $resultfile"
    cp "$resultfile" archive/results/
    rm "$resultfile"
done

# Clean up node_modules (can be reinstalled later if needed)
echo "Removing node_modules directory..."
rm -rf node_modules

# Tailwind and other frontend config files
echo "Archiving frontend config files..."
for config in tailwind.config.ts postcss.config.js vite.config.ts theme.json; do
    if [ -f "$config" ]; then
        echo "  - Archiving $config"
        mv "$config" archive/frontend/
    fi
done

# Clean up empty directories
echo "Cleaning up empty directories..."
find . -type d -empty -not -path "*/\.*" -not -path "*/__pycache__*" -not -path "*/archive*" -delete

# Create a minimal package.json for backend only
echo "Creating minimal package.json for backend..."
cat > package.json << 'EOF'
{
  "name": "trading-system-backend",
  "version": "1.0.0",
  "description": "Multi-Agent Trading System Backend",
  "main": "server/index.js",
  "scripts": {
    "start": "node server/index.js",
    "dev": "nodemon server/index.js",
    "test": "jest"
  },
  "dependencies": {
    "dotenv": "^16.0.3",
    "express": "^4.18.2",
    "fastify": "^4.17.0",
    "@fastify/cors": "^8.3.0",
    "axios": "^1.4.0",
    "pm2": "^5.3.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.22",
    "jest": "^29.5.0"
  }
}
EOF

# Update .gitignore to exclude frontend-related files
echo "Updating .gitignore..."
cat > .gitignore << 'EOF'
# Node.js
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/
.env
.env.local

# Logs and databases
*.log
*.sqlite
*.db

# Archives
archive/

# Temporary files
tmp/
.tmp/
.DS_Store
Thumbs.db

# Coverage
.coverage
htmlcov/

# Cached data
.cache/

# Test outputs
test_outputs/

# Frontend (archived)
client/
dist/
EOF

# Create a minimal server entry point
echo "Creating minimal server.js..."
mkdir -p server
cat > server/index.js << 'EOF'
/**
 * Minimal Trading System API Server
 * 
 * This is a simple Express server that provides an API for the trading system.
 * It will be expanded as we develop the backend functionality.
 */
require('dotenv').config();
const express = require('express');
const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check route
app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// API route for system info
app.get('/api/system', (req, res) => {
  res.json({
    name: 'Multi-Agent Trading System',
    version: '1.0.0',
    components: [
      'Technical Analysis Agent',
      'Fundamental Analysis Agent',
      'Portfolio Management Agent',
      'Decision Session Orchestration'
    ],
    status: 'operational'
  });
});

// API route to trigger a trading decision
app.post('/api/decision', (req, res) => {
  const { symbol } = req.body;
  
  if (!symbol) {
    return res.status(400).json({ error: 'Symbol is required' });
  }
  
  // In the future, this will call the Python trading system
  // For now, we just return a placeholder response
  res.json({
    message: `Trading decision request received for ${symbol}`,
    status: 'pending',
    requestId: `req-${Date.now()}`,
    note: 'This is a placeholder. The actual decision process will be implemented soon.'
  });
});

// Start the server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running at http://0.0.0.0:${PORT}`);
  console.log('API endpoints:');
  console.log('  GET  /api/health   - Check system health');
  console.log('  GET  /api/system   - Get system information');
  console.log('  POST /api/decision - Request a trading decision');
});
EOF

echo "Backend-focused cleanup complete!"
echo "The system is now focused solely on the backend trading functionality."
echo "All frontend files, logs, and test outputs have been archived."