
import fetch from 'node-fetch';
import fs from 'fs';

const DEPLOYMENT_URL = process.env.DEPLOYMENT_URL || 'https://your-repl-url.replit.dev';
const LOG_FILE = './logs/monitor.log';

async function checkHealth() {
  try {
    const response = await fetch(`${DEPLOYMENT_URL}/health`);
    const data = await response.json();
    const timestamp = new Date().toISOString();
    
    const logMessage = `[${timestamp}] Health check: Status ${data.status}, Uptime: ${data.uptime}s\n`;
    
    // Ensure logs directory exists
    if (!fs.existsSync('./logs')) {
      fs.mkdirSync('./logs', { recursive: true });
    }
    
    // Append to log file
    fs.appendFileSync(LOG_FILE, logMessage);
    
    console.log(logMessage);
    return data;
  } catch (error) {
    const errorMsg = `[${new Date().toISOString()}] Error checking health: ${error.message}\n`;
    console.error(errorMsg);
    fs.appendFileSync(LOG_FILE, errorMsg);
    return null;
  }
}

// Run once immediately
checkHealth();

// Schedule regular checks if this script is run directly
if (require.main === module) {
  console.log('Starting monitoring service...');
  setInterval(checkHealth, 5 * 60 * 1000); // Check every 5 minutes
}

export { checkHealth };
