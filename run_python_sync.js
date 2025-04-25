/**
 * run_python_sync.js
 * 
 * This script executes Python commands for the aGENtrader v2 test framework
 * in a synchronized manner, handling the output and proper error codes.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Define folder paths
const LOGS_DIR = path.join(__dirname, 'logs');
const DATASETS_DIR = path.join(__dirname, 'datasets');

// Ensure required directories exist
function ensureDirectoriesExist() {
  [LOGS_DIR, DATASETS_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
      console.log(`Creating directory: ${dir}`);
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

// Run a Python command synchronously and return the result
function runPythonCommand(command) {
  console.log(`\n> Executing: ${command}\n`);
  try {
    const output = execSync(command, { 
      encoding: 'utf8',
      stdio: 'inherit'
    });
    return { success: true, output };
  } catch (error) {
    console.error(`Error executing command: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0];

// Main execution
ensureDirectoriesExist();

switch(command) {
  case 'start':
    runPythonCommand('python run.py');
    break;
  case 'test-decision-logger':
    runPythonCommand('python test_decision_logger.py');
    break;
  case 'test-all':
    runPythonCommand('python run_all_tests.py');
    break;
  case 'export-dataset':
    const limit = args[1] || 100;
    runPythonCommand(`python scripts/export_decision_dataset.py --limit ${limit}`);
    break;
  case 'full-test-run':
    console.log('Starting full test run for aGENtrader v2.1...');
    
    // 1. Run test decision logger to create sample logs
    console.log('\n=== Step 1: Generate test decision logs ===');
    runPythonCommand('python test_decision_logger.py');
    
    // 2. Run main application for one cycle
    console.log('\n=== Step 2: Run main application for one cycle ===');
    runPythonCommand('python run.py --interval 1h --symbol BTCUSDT --test-cycle 1');
    
    // 3. Export decision dataset
    console.log('\n=== Step 3: Export decision dataset ===');
    runPythonCommand('python scripts/export_decision_dataset.py --limit 100');
    
    // 4. Check log files
    console.log('\n=== Step 4: Checking log files ===');
    if (fs.existsSync(path.join(LOGS_DIR, 'decision_summary.logl'))) {
      console.log('✅ Decision log created successfully');
    } else {
      console.log('❌ Decision log not found');
    }
    
    if (fs.existsSync(path.join(LOGS_DIR, 'trade_book.jsonl'))) {
      console.log('✅ Trade book log created successfully');
    } else {
      console.log('❌ Trade book log not found');
    }
    
    if (fs.existsSync(path.join(DATASETS_DIR, 'decision_log_dataset.jsonl'))) {
      console.log('✅ Decision dataset exported successfully');
    } else {
      console.log('❌ Decision dataset export failed');
    }
    
    console.log('\nFull test run completed!');
    break;
  default:
    console.log(`
    aGENtrader v2.1 Test Runner
    
    Available commands:
      node run_python_sync.js start                  - Run the main application
      node run_python_sync.js test-decision-logger   - Test the decision logger
      node run_python_sync.js test-all               - Run all tests
      node run_python_sync.js export-dataset [limit] - Export decision dataset
      node run_python_sync.js full-test-run          - Execute full test suite
    `);
}