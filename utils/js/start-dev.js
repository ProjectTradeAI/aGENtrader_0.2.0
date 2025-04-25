/**
 * start-dev.js
 * 
 * This script runs the aGENtrader test workflow
 */

const { execSync } = require('child_process');

console.log('Starting aGENtrader v2.1 test workflow...');

try {
  execSync('./run-workflow.sh', { stdio: 'inherit' });
} catch (error) {
  console.error('Error running workflow:', error.message);
  process.exit(1);
}