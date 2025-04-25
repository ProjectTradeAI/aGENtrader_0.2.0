/**
 * Start script for aGENtrader v2
 * This script executes the Python main.py file.
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('Starting aGENtrader v2...');

// Spawn a Python process to run main.py
const pythonProcess = spawn('python3', [path.join(__dirname, 'main.py')], {
  stdio: 'inherit',
  env: process.env
});

// Handle process events
pythonProcess.on('error', (err) => {
  console.error('Failed to start Python process:', err);
  process.exit(1);
});

pythonProcess.on('close', (code) => {
  console.log(`Python process exited with code ${code}`);
  process.exit(code);
});

// Handle termination signals
process.on('SIGINT', () => {
  console.log('Received SIGINT. Stopping Python process...');
  pythonProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM. Stopping Python process...');
  pythonProcess.kill('SIGTERM');
});