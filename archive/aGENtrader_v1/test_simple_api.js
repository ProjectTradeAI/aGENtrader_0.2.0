/**
 * Simple API Server for Trading System
 * 
 * This file provides a simple HTTP API for the trading system.
 * It serves as a bridge between HTTP requests and the Python backend.
 */

const express = require('express');
const cors = require('cors');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Create Express app
const app = express();
const PORT = process.env.PORT || 5050;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

/**
 * Run a Python script with arguments and return the result
 * 
 * @param {string} scriptPath - Path to the Python script
 * @param {Object} args - Arguments to pass to the script
 * @returns {Object} - JSON result from the script
 */
function runPythonScript(scriptPath, args = {}) {
    // Convert JS object to command line arguments
    const argString = Object.entries(args)
        .map(([key, value]) => {
            // Handle different value types
            if (typeof value === 'object') {
                return `--${key}='${JSON.stringify(value)}'`;
            } else {
                return `--${key}='${value}'`;
            }
        })
        .join(' ');

    try {
        console.log(`Running: python ${scriptPath} ${argString}`);
        
        // Set a longer timeout for complex operations (30 seconds)
        const output = execSync(`python ${scriptPath} ${argString}`, { 
            encoding: 'utf8',
            timeout: 30000
        });

        // Extract JSON from output
        const jsonMatch = output.match(/({[\s\S]*})|(\[[\s\S]*\])/);
        if (jsonMatch) {
            try {
                return JSON.parse(jsonMatch[0]);
            } catch (e) {
                console.error('Error parsing JSON from Python output:', e);
                return { error: 'Invalid JSON output from Python script', details: output };
            }
        }
        
        return { result: output.trim() };
    } catch (error) {
        console.error('Error running Python script:', error);
        return { error: error.message, stderr: error.stderr };
    }
}

// Documentation route
app.get('/', (req, res) => {
    // Check if documentation file exists
    if (fs.existsSync('API_DOCUMENTATION.md')) {
        const docs = fs.readFileSync('API_DOCUMENTATION.md', 'utf8');
        res.send(`<html>
            <head>
                <title>Trading System API</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0 auto; max-width: 800px; padding: 20px; }
                    pre { background: #f4f4f4; border-left: 3px solid #007bff; padding: 15px; overflow: auto; }
                    code { background: #f4f4f4; padding: 2px 4px; }
                    h1, h2, h3 { color: #333; }
                    .endpoint { border-left: 3px solid #28a745; padding-left: 15px; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <h1>Trading System API</h1>
                <div id="content">
                    <pre>${docs}</pre>
                </div>
            </body>
        </html>`);
    } else {
        // Basic documentation if file not found
        res.send(`<html>
            <head>
                <title>Trading System API</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0 auto; max-width: 800px; padding: 20px; }
                    pre { background: #f4f4f4; border-left: 3px solid #007bff; padding: 15px; overflow: auto; }
                    code { background: #f4f4f4; padding: 2px 4px; }
                    h1, h2, h3 { color: #333; }
                    .endpoint { border-left: 3px solid #28a745; padding-left: 15px; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <h1>Trading System API</h1>
                <div id="content">
                    <h2>Available Endpoints:</h2>
                    <div class="endpoint">
                        <h3>GET /api/health</h3>
                        <p>Check system health</p>
                    </div>
                    <div class="endpoint">
                        <h3>GET /api/system</h3>
                        <p>Get system information</p>
                    </div>
                    <div class="endpoint">
                        <h3>POST /api/decision</h3>
                        <p>Request a trading decision</p>
                    </div>
                    <div class="endpoint">
                        <h3>POST /api/backtest</h3>
                        <p>Run a backtest</p>
                    </div>
                </div>
            </body>
        </html>`);
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// System info endpoint
app.get('/api/system', (req, res) => {
    try {
        // Try to run a simple Python check
        const result = runPythonScript('api/trading_api.py', { mode: 'system_info' });
        res.json(result);
    } catch (error) {
        res.status(500).json({ 
            status: 'error', 
            message: 'Failed to get system information',
            error: error.message
        });
    }
});

// Trading decision endpoint
app.post('/api/decision', (req, res) => {
    try {
        const { symbol, interval, analysis_type } = req.body;
        
        if (!symbol) {
            return res.status(400).json({ error: 'Symbol is required' });
        }
        
        const result = runPythonScript('api/trading_api.py', { 
            mode: 'decision',
            symbol: symbol || 'BTCUSDT',
            interval: interval || '1h',
            analysis_type: analysis_type || 'full'
        });
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ 
            status: 'error', 
            message: 'Failed to generate trading decision',
            error: error.message
        });
    }
});

// Backtest endpoint
app.post('/api/backtest', (req, res) => {
    try {
        const { symbol, interval, start_date, end_date, strategy } = req.body;
        
        if (!symbol || !start_date || !end_date) {
            return res.status(400).json({ error: 'Symbol, start_date, and end_date are required' });
        }
        
        const result = runPythonScript('api/trading_api.py', { 
            mode: 'backtest',
            symbol: symbol,
            interval: interval || '1h',
            start: start_date,
            end: end_date,
            strategy: strategy || 'default'
        });
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ 
            status: 'error', 
            message: 'Failed to run backtest',
            error: error.message
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