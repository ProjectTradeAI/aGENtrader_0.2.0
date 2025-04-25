const { spawn } = require('child_process');
const path = require('path');

// Function to run a Python script (simplified version from our server.js)
function runPythonScript(scriptPath, args = []) {
  return new Promise((resolve, reject) => {
    console.log(`Running command: python ${scriptPath} ${args.join(' ')}`);
    
    const pythonProcess = spawn('python', [scriptPath, ...args]);
    
    let result = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python stdout received ${data.length} bytes`);
      result += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.log(`Python stderr: ${data}`);
      errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
      
      if (code !== 0) {
        console.error(`Error output: ${errorOutput}`);
        reject(new Error(`Python script exited with code ${code}: ${errorOutput}`));
      } else {
        console.log(`Raw output (first 200 chars): ${result.substring(0, 200)}`);
        
        try {
          // Extract the JSON output from the Python script
          const jsonStart = result.indexOf('{');
          const jsonEnd = result.lastIndexOf('}') + 1;
          
          if (jsonStart >= 0 && jsonEnd > jsonStart) {
            const jsonStr = result.substring(jsonStart, jsonEnd);
            console.log(`Extracted JSON (first 100 chars): ${jsonStr.substring(0, 100)}...`);
            
            try {
              const jsonResult = JSON.parse(jsonStr);
              resolve(jsonResult);
            } catch (parseErr) {
              console.error(`Error parsing JSON: ${parseErr}`);
              console.log('Failed JSON string:', jsonStr);
              reject(parseErr);
            }
          } else {
            console.log(`No JSON found in output. Output: ${result}`);
            resolve({ result: result.trim() });
          }
        } catch (err) {
          console.error('Error parsing Python output:', err);
          reject(err);
        }
      }
    });
  });
}

// Main test function
async function testTradingDecision() {
  try {
    const scriptPath = path.join(__dirname, 'api', 'trading_api.py');
    const symbol = 'BTCUSDT';
    const interval = '1h';
    
    console.log(`Testing trading decision for ${symbol} with interval ${interval}`);
    
    const args = ['--decision', symbol, '--interval', interval];
    const result = await runPythonScript(scriptPath, args);
    
    console.log('Successfully received trading decision:');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Error in test:', error);
  }
}

// Run the test
testTradingDecision();
