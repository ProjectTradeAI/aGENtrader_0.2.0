const dotenv = require('dotenv');
dotenv.config();

module.exports = {
  apps: [{
    name: 'trading-bot',
    script: './dist/index.js',
    env: {
      ...process.env,
      NODE_ENV: 'production',
      PORT: 5000
    },
    instances: 1,
    exec_mode: 'cluster',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/error.log',
    out_file: './logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    env_production: {
      ...process.env,
      NODE_ENV: 'production'
    }
  }, {
    name: 'market-data-collector',
    script: './scripts/run_market_data_collection.py',
    interpreter: 'python3',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    error_file: './logs/market-data-error.log',
    out_file: './logs/market-data-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'  // Ensure Python output is not buffered
    }
  }]
}