/**
 * Simple test script for the trading API
 */
const express = require('express');
const { exec } = require('child_process');
const app = express();
const PORT = 5555;

// Simple test endpoint
app.get('/test/:symbol', (req, res) => {
  const symbol = req.params.symbol;
  const interval = req.query.interval || '1h';
  
  console.log(`Testing trading decision for ${symbol} with interval ${interval}`);
  
  exec(`python api/trading_api.py --decision ${symbol} --interval ${interval}`, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error.message}`);
      return res.status(500).json({ error: error.message });
    }
    
    if (stderr) {
      console.error(`stderr: ${stderr}`);
    }
    
    console.log(`stdout: ${stdout.substring(0, 200)}...`);
    
    // Try to extract JSON from stdout
    try {
      const jsonStart = stdout.indexOf('{');
      const jsonEnd = stdout.lastIndexOf('}') + 1;
      
      if (jsonStart >= 0 && jsonEnd > jsonStart) {
        const jsonStr = stdout.substring(jsonStart, jsonEnd);
        const result = JSON.parse(jsonStr);
        return res.json(result);
      } else {
        return res.status(500).json({ error: 'No JSON found in output', stdout: stdout.substring(0, 200) });
      }
    } catch (parseErr) {
      return res.status(500).json({ error: parseErr.message, stdout: stdout.substring(0, 200) });
    }
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Test server running at http://0.0.0.0:${PORT}`);
});