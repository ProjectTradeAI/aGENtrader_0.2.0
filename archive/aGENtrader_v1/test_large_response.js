const express = require('express');
const { spawn } = require('child_process');
const app = express();
const PORT = 5050;

app.use(express.json());

// Generate a large JSON response
app.get('/large-json', (req, res) => {
  const largeObject = {
    title: "Test Large JSON Response",
    items: Array(1000).fill(0).map((_, i) => ({ id: i, value: `Item ${i}`, data: "x".repeat(100) }))
  };
  res.json(largeObject);
});

// Test Python with large output
app.get('/python-large', (req, res) => {
  const pythonProcess = spawn('python', ['-c', `
import json
import sys

large_dict = {
  "result": "success",
  "items": [{"id": i, "value": f"Item {i}", "data": "x" * 100} for i in range(1000)]
}

print(json.dumps(large_dict))
  `]);
  
  let result = '';
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Received chunk of ${data.length} bytes`);
    result += data.toString();
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python error: ${data}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    console.log(`Total response size: ${result.length} bytes`);
    
    try {
      const jsonData = JSON.parse(result);
      res.json({ success: true, itemCount: jsonData.items.length });
    } catch (err) {
      res.status(500).json({ error: `Failed to parse JSON: ${err.message}` });
    }
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Test server running at http://0.0.0.0:${PORT}`);
});
