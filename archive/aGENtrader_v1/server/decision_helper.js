/**
 * Decision Helper
 * 
 * This module provides helper functions for the trading decision API
 * focusing on the integration between Node.js and Python.
 */
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * Get a trading decision using a file-based approach
 * 
 * @param {string} symbol - Trading symbol
 * @param {string} interval - Time interval
 * @returns {Promise<object>} - Trading decision object
 */
function getTradingDecision(symbol, interval) {
  return new Promise((resolve, reject) => {
    const outputFilePath = path.join(__dirname, '..', 'temp_decision_output.json');
    const scriptPath = path.join(__dirname, '..', 'api', 'trading_api.py');
    
    console.log(`Getting trading decision for ${symbol} with interval ${interval}`);
    console.log(`Output will be saved to ${outputFilePath}`);
    
    // Clean up any existing output file
    if (fs.existsSync(outputFilePath)) {
      try {
        fs.unlinkSync(outputFilePath);
        console.log('Removed existing output file');
      } catch (err) {
        console.warn(`Failed to remove existing output file: ${err.message}`);
      }
    }
    
    // Instead of using output redirection, we'll capture the output directly
    // and write it to a file ourselves for better control
    const command = `python ${scriptPath} --decision ${symbol} --interval ${interval}`;
    
    console.log(`Executing command: ${command}`);
    
    // Execute the command and capture output directly
    exec(command, (error, stdout, stderr) => {
      console.log('Python command completed');
      
      if (error) {
        console.error(`Error executing Python: ${error.message}`);
        
        if (stderr) {
          console.error(`Python stderr: ${stderr}`);
        }
        
        return reject(new Error(`Failed to execute Python script: ${error.message}`));
      }
      
      // Log the output we received
      console.log(`Received stdout (${stdout.length} bytes):`);
      console.log(stdout.substring(0, 200) + (stdout.length > 200 ? '...' : ''));
      
      // First try to extract JSON directly from stdout
      const stdoutJsonStart = stdout.indexOf('{');
      const stdoutJsonEnd = stdout.lastIndexOf('}') + 1;
      
      if (stdoutJsonStart >= 0 && stdoutJsonEnd > stdoutJsonStart) {
        console.log(`Found JSON in stdout at positions ${stdoutJsonStart}-${stdoutJsonEnd}`);
        const jsonStr = stdout.substring(stdoutJsonStart, stdoutJsonEnd);
        
        try {
          const result = JSON.parse(jsonStr);
          console.log('Successfully parsed JSON result directly from stdout');
          return resolve(result);
        } catch (parseErr) {
          console.error(`Error parsing JSON from stdout: ${parseErr.message}`);
          // Continue to file-based approach as fallback
        }
      }
      
      // Write the stdout to our output file as a fallback
      try {
        fs.writeFileSync(outputFilePath, stdout);
        console.log(`Wrote ${stdout.length} bytes to ${outputFilePath}`);
        
        if (stderr && stderr.length > 0) {
          fs.writeFileSync(`${outputFilePath}.err`, stderr);
          console.log(`Wrote ${stderr.length} bytes of stderr to ${outputFilePath}.err`);
        }
      } catch (writeErr) {
        console.error(`Error writing output to file: ${writeErr.message}`);
        return reject(new Error(`Failed to write Python output to file: ${writeErr.message}`));
      }
      
      // Wait a moment to ensure the file is completely written
      setTimeout(() => {
        // Check if the output file exists
        if (fs.existsSync(outputFilePath)) {
          try {
            console.log('Output file exists, reading content...');
            const fileContent = fs.readFileSync(outputFilePath, 'utf8');
            console.log(`Read ${fileContent.length} bytes from output file`);
            
            // Look for JSON in the file content
            const jsonStart = fileContent.indexOf('{');
            const jsonEnd = fileContent.lastIndexOf('}') + 1;
            
            if (jsonStart >= 0 && jsonEnd > jsonStart) {
              console.log(`Found JSON at positions ${jsonStart}-${jsonEnd}`);
              const jsonStr = fileContent.substring(jsonStart, jsonEnd);
              
              try {
                const result = JSON.parse(jsonStr);
                console.log('Successfully parsed JSON result');
                
                // Clean up the files
                try {
                  fs.unlinkSync(outputFilePath);
                  if (fs.existsSync(`${outputFilePath}.err`)) {
                    fs.unlinkSync(`${outputFilePath}.err`);
                  }
                } catch (cleanupErr) {
                  console.warn(`Warning: Failed to clean up temporary files: ${cleanupErr.message}`);
                }
                
                resolve(result);
              } catch (parseErr) {
                console.error(`Error parsing JSON from file: ${parseErr.message}`);
                console.error(`JSON string: ${jsonStr.substring(0, 200)}...`);
                reject(new Error(`Failed to parse JSON from Python output: ${parseErr.message}`));
              }
            } else {
              console.error('No JSON found in file output');
              console.error(`File content: ${fileContent.substring(0, 200)}...`);
              reject(new Error('No JSON found in Python output file'));
            }
          } catch (fileErr) {
            console.error(`Error reading output file: ${fileErr.message}`);
            reject(new Error(`Failed to read Python output file: ${fileErr.message}`));
          }
        } else {
          console.error('Output file was not created');
          reject(new Error('Python script did not create output file'));
        }
      }, 500); // Wait 500ms to ensure file is completely written
    });
  });
}

module.exports = {
  getTradingDecision
};