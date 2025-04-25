module.exports = {
  apps: [{
    name: 'trading-bot',
    script: './dist/server/index.js',
    env: {
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
      NODE_ENV: 'production'
    }
  }, {
    name: 'monitor',
    script: './server/monitor.js',
    env: {
      NODE_ENV: 'production',
      DEPLOYMENT_URL: 'http://localhost:5000'
    },
    autorestart: true,
    watch: false,
    error_file: './logs/monitor-error.log',
    out_file: './logs/monitor-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
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