/**
 * Trading System API Server
 * 
 * This Express server provides an API for the Python-based trading system.
 * It uses child_process to spawn Python processes for handling requests.
 */
require('dotenv').config();
const express = require('express');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Increase the timeout for the Node.js process
process.setMaxListeners(20); // Increase max listeners to prevent warnings
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Ensure logs directory exists
const logsDir = path.join(__dirname, '..', 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Function to run a Python script and return its output
function runPythonScript(scriptPath, args = []) {
  return new Promise((resolve, reject) => {
    console.log(`Running Python: ${scriptPath} ${args.join(' ')}`);
    
    // Add a timeout to prevent hanging
    const TIMEOUT_MS = 30000; // 30 seconds
    const timeoutId = setTimeout(() => {
      console.error(`Python script execution timed out after ${TIMEOUT_MS}ms`);
      
      // Kill the process if it's still running
      if (pythonProcess && !pythonProcess.killed) {
        console.log('Killing Python process due to timeout');
        pythonProcess.kill();
      }
      
      // Return a proper error response
      resolve({
        error: "Python script execution timed out",
        message: `Script execution exceeded ${TIMEOUT_MS/1000} seconds`,
        args: args
      });
    }, TIMEOUT_MS);
    
    const pythonProcess = spawn('python', [scriptPath, ...args]);
    
    let result = '';
    let errorOutput = '';
    let jsonFound = false;
    
    // Process stdout data
    pythonProcess.stdout.on('data', (data) => {
      const dataStr = data.toString();
      result += dataStr;
      
      // Check if this chunk contains JSON
      if (dataStr.includes('{') && dataStr.includes('}')) {
        console.log(`Found potential JSON in stdout: ${dataStr.substring(0, 50)}...`);
      }
    });
    
    // Process stderr data - important since Python logging goes to stderr by default
    pythonProcess.stderr.on('data', (data) => {
      const dataStr = data.toString();
      
      // Check if stderr actually contains an error message
      if (dataStr.includes('ERROR') || dataStr.includes('Error') || dataStr.includes('Traceback')) {
        errorOutput += dataStr;
        console.error(`Python error: ${dataStr}`);
      } else {
        // This is just logging info, not a real error
        console.log(`Python log: ${dataStr.substring(0, 100)}...`);
      }
    });
    
    // Process script completion
    pythonProcess.on('close', (code) => {
      console.log(`Python process completed with code ${code}`);
      
      // Clear the timeout since the process has completed
      clearTimeout(timeoutId);
      
      if (code !== 0) {
        console.error(`Python script failed with code ${code}`);
        console.error(`Error output: ${errorOutput}`);
        reject(new Error(`Python script exited with code ${code}: ${errorOutput}`));
      } else {
        try {
          // First try to find JSON in stdout
          let jsonStart = result.indexOf('{');
          let jsonEnd = result.lastIndexOf('}') + 1;
          
          if (jsonStart >= 0 && jsonEnd > jsonStart) {
            const jsonStr = result.substring(jsonStart, jsonEnd);
            console.log(`Extracted JSON from stdout: ${jsonStr.substring(0, 50)}...`);
            
            try {
              const jsonResult = JSON.parse(jsonStr);
              resolve(jsonResult);
              return;
            } catch (parseErr) {
              console.error(`Error parsing JSON from stdout: ${parseErr}`);
              // Fall through to try errorOutput next
            }
          }
          
          // If we get here, we either didn't find JSON in stdout or couldn't parse it
          // Return a valid error response
          resolve({ 
            error: "Failed to process Python output",
            message: "Could not extract valid JSON from Python output",
            symbol: args.find(arg => !arg.startsWith('-')),
            result_data: result.substring(0, 200) // Include a snippet for debugging
          });
          
        } catch (err) {
          console.error('Error processing Python output:', err);
          resolve({ 
            error: "Failed to process Python output", 
            message: err.message, 
            symbol: args.find(arg => !arg.startsWith('-'))
          });
        }
      }
    });
  });
}

// Simple landing page for the root route
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Multi-Agent Trading System API</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        h1 { color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        h2 { color: #3498db; margin-top: 30px; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .endpoint { background: #e8f4fc; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
        .method { font-weight: bold; color: #2980b9; }
        .url { color: #27ae60; }
        footer { margin-top: 50px; color: #7f8c8d; font-size: 0.9em; text-align: center; }
      </style>
    </head>
    <body>
      <h1>Multi-Agent Trading System API</h1>
      <p>Welcome to the Multi-Agent Trading System API server. This API provides access to the trading system's functionality.</p>
      
      <h2>Available Endpoints</h2>
      
      <div class="endpoint">
        <p><span class="method">GET</span> <span class="url">/api/health</span></p>
        <p>Check the system's health status.</p>
        <pre>curl -X GET http://localhost:5000/api/health</pre>
      </div>
      
      <div class="endpoint">
        <p><span class="method">GET</span> <span class="url">/api/system</span></p>
        <p>Get information about the trading system.</p>
        <pre>curl -X GET http://localhost:5000/api/system</pre>
      </div>
      
      <div class="endpoint">
        <p><span class="method">POST</span> <span class="url">/api/decision</span></p>
        <p>Request a trading decision for a specific symbol.</p>
        <pre>curl -X POST http://localhost:5000/api/decision \\
  -H "Content-Type: application/json" \\
  -d '{"symbol":"BTCUSDT","interval":"1h"}'</pre>
      </div>
      
      <div class="endpoint">
        <p><span class="method">GET</span> <span class="url">/api/decision/:symbol</span></p>
        <p>Alternative endpoint to request a trading decision using GET parameters.</p>
        <pre>curl -X GET http://localhost:5000/api/decision/BTCUSDT?interval=1h</pre>
      </div>
      
      <div class="endpoint">
        <p><span class="method">GET</span> <span class="url">/api/decision-static/:symbol</span></p>
        <p>Test endpoint that returns a static decision response (for debugging).</p>
        <pre>curl -X GET http://localhost:5000/api/decision-static/BTCUSDT?interval=1h</pre>
      </div>
      
      <div class="endpoint">
        <p><span class="method">POST</span> <span class="url">/api/backtest</span></p>
        <p>Run a backtest for a trading strategy.</p>
        <pre>curl -X POST http://localhost:5000/api/backtest \\
  -H "Content-Type: application/json" \\
  -d '{"symbol":"BTCUSDT","interval":"1h","days":30,"mode":"authentic"}'</pre>
      </div>
      
      <h2>API Status</h2>
      <p>The API server is currently running and ready to accept requests.</p>
      
      <footer>
        <p>Multi-Agent Trading System &copy; 2025</p>
      </footer>
    </body>
    </html>
  `);
});

// Health check route
app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// API route for system info
app.get('/api/system', async (req, res) => {
  try {
    const scriptPath = path.join(__dirname, '..', 'api', 'trading_api.py');
    const result = await runPythonScript(scriptPath, ['--info']);
    res.json(result);
  } catch (error) {
    console.error('Error getting system info:', error);
    res.status(500).json({ 
      error: 'Failed to get system information',
      message: error.message 
    });
  }
});

// API route to trigger a trading decision
app.post('/api/decision', async (req, res) => {
  const { symbol, interval } = req.body;
  
  if (!symbol) {
    return res.status(400).json({ error: 'Symbol is required' });
  }
  
  console.log(`Processing POST trading decision for ${symbol} with interval ${interval || '1h'}`);
  
  try {
    // First check if aGENtrader v2 backend is available
    const backendAvailable = await agentrader.checkBackendAccess();
    
    if (backendAvailable) {
      // Use aGENtrader v2 for decision
      console.log('Using aGENtrader v2 backend for trading decision');
      try {
        const decision = await agentrader.getTradingDecision(symbol, interval || '1h');
        
        if (decision && decision.success) {
          return res.json(decision.data);
        } else {
          console.log('aGENtrader v2 returned an error, falling back to v1');
        }
      } catch (v2Error) {
        console.error('Error using aGENtrader v2:', v2Error);
        console.log('Falling back to v1 backend');
      }
    }
    
    // Fallback to v1 backend if v2 is not available or fails
    const { execSync } = require('child_process');
    const scriptPath = path.join(__dirname, '..', 'api', 'trading_api.py');
    const helperScript = path.join(__dirname, '..', 'run_python_sync.js');
    
    // Run the helper script to execute the Python code
    const command = `node ${helperScript} ${scriptPath} --decision ${symbol} --interval ${interval || '1h'}`;
    console.log(`Falling back to v1: ${command}`);
    
    const output = execSync(command, { 
      encoding: 'utf8',
      maxBuffer: 1024 * 1024, // 1MB buffer
      timeout: 30000 // 30 seconds timeout
    });
    
    // The helper script will output only the JSON result
    try {
      const result = JSON.parse(output);
      console.log('Successfully parsed JSON result from v1');
      return res.json(result);
    } catch (parseErr) {
      console.error(`Error parsing JSON result from v1: ${parseErr.message}`);
      return res.status(500).json({ 
        error: 'Failed to parse JSON result',
        message: parseErr.message,
        output_sample: output.substring(0, 200)
      });
    }
  } catch (error) {
    console.error(`Error in trading decision endpoint: ${error.message}`);
    return res.status(500).json({ 
      error: 'Failed to get trading decision',
      message: error.message
    });
  }
});

// Simple GET route for trading decisions (easier for testing)
app.get('/api/decision/:symbol', async (req, res) => {
  const symbol = req.params.symbol;
  const interval = req.query.interval || '1h';
  
  console.log(`Running simple trading decision GET for ${symbol} with interval ${interval}`);
  
  try {
    // First check if aGENtrader v2 backend is available
    const backendAvailable = await agentrader.checkBackendAccess();
    
    if (backendAvailable) {
      // Use aGENtrader v2 for decision
      console.log('Using aGENtrader v2 backend for trading decision (GET)');
      try {
        const decision = await agentrader.getTradingDecision(symbol, interval);
        
        if (decision && decision.success) {
          return res.json(decision.data);
        } else {
          console.log('aGENtrader v2 returned an error, falling back to v1');
        }
      } catch (v2Error) {
        console.error('Error using aGENtrader v2:', v2Error);
        console.log('Falling back to v1 backend');
      }
    }
    
    // Fallback to v1 backend if v2 is not available or fails
    const { execSync } = require('child_process');
    const scriptPath = path.join(__dirname, '..', 'api', 'trading_api.py');
    const helperScript = path.join(__dirname, '..', 'run_python_sync.js');
    
    // Run the helper script to execute the Python code
    const command = `node ${helperScript} ${scriptPath} --decision ${symbol} --interval ${interval}`;
    console.log(`Falling back to v1 (GET): ${command}`);
    
    const output = execSync(command, { 
      encoding: 'utf8',
      maxBuffer: 1024 * 1024, // 1MB buffer
      timeout: 30000 // 30 seconds timeout
    });
    
    // The helper script will output only the JSON result
    try {
      const result = JSON.parse(output);
      console.log('Successfully parsed JSON result from v1');
      return res.json(result);
    } catch (parseErr) {
      console.error(`Error parsing JSON result from v1: ${parseErr.message}`);
      return res.status(500).json({ 
        error: 'Failed to parse JSON result',
        message: parseErr.message,
        output_sample: output.substring(0, 200)
      });
    }
  } catch (error) {
    console.error(`Error in trading decision GET endpoint: ${error.message}`);
    return res.status(500).json({ 
      error: 'Failed to get trading decision',
      message: error.message
    });
  }
});

// Simplified endpoint that returns a static response for testing
app.get('/api/decision-static/:symbol', (req, res) => {
  const symbol = req.params.symbol;
  const interval = req.query.interval || '1h';
  
  console.log(`Providing static decision for ${symbol} with interval ${interval}`);
  
  // Return a static example response
  res.json({
    "symbol": symbol,
    "timestamp": new Date().toISOString(),
    "decision": "hold",
    "confidence": 0.95,
    "reasoning": "This is a static test response. In a real scenario, this would contain technical and fundamental analysis.",
    "data_sources": ["market_data"],
    "interval": interval,
    "request_id": `static-${Date.now()}`
  });
});

// API route to run a backtest
app.post('/api/backtest', async (req, res) => {
  const { symbol, interval, days, startDate, endDate, mode } = req.body;
  
  if (!symbol) {
    return res.status(400).json({ error: 'Symbol is required' });
  }
  
  try {
    const scriptPath = path.join(__dirname, '..', 'api', 'trading_api.py');
    const args = ['--backtest', symbol];
    
    if (interval) args.push('--interval', interval);
    if (days) args.push('--days', days.toString());
    if (startDate) args.push('--start', startDate);
    if (endDate) args.push('--end', endDate);
    if (mode) args.push('--mode', mode);
    
    const result = await runPythonScript(scriptPath, args);
    res.json(result);
  } catch (error) {
    console.error('Error running backtest:', error);
    res.status(500).json({ 
      error: 'Failed to run backtest',
      message: error.message,
      symbol
    });
  }
});

// Start the server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running at http://0.0.0.0:${PORT}`);
  console.log('API endpoints:');
  console.log('  GET  /       - Landing page with API documentation');
  console.log('  GET  /api/health    - Check system health');
  console.log('  GET  /api/system    - Get system information');
  console.log('  POST /api/decision  - Request a trading decision');
  console.log('  POST /api/backtest  - Run a backtest');
});
