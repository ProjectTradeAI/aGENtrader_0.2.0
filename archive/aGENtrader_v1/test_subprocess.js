const { spawn } = require('child_process');

// Function to run a Python script
function runPythonScript(scriptPath) {
  console.log(`Running Python script: ${scriptPath}`);
  
  const pythonProcess = spawn('python', [scriptPath]);
  
  let result = '';
  let errorOutput = '';
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
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
    } else {
      try {
        // Try to parse JSON
        const jsonResult = JSON.parse(result);
        console.log('Parsed JSON:', jsonResult);
      } catch (err) {
        console.error('Error parsing JSON:', err);
        console.log('Raw output:', result);
      }
    }
  });
}

// Run the test script
runPythonScript('./test_output.py');
