const dotenv = require('dotenv');
dotenv.config();

module.exports = {
  apps: [{
    name: 'trading-bot-backtesting',
    script: 'python3',
    args: 'run_backtest_with_local_llm.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-15 --analysis_timeout 120',
    instances: 1,
    exec_mode: 'fork',
    autorestart: false,  // Don't restart automatically when backtesting finishes
    watch: false,
    max_memory_restart: '2G',
    error_file: './logs/backtest-error.log',
    out_file: './logs/backtest-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    env: {
      PYTHONUNBUFFERED: '1',  // Ensure Python output is not buffered
      ...process.env
    }
  }, {
    name: 'llm-monitoring',
    script: 'python3',
    args: 'utils/llm_integration/monitor_llm.py',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    error_file: './logs/llm-monitor-error.log',
    out_file: './logs/llm-monitor-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    env: {
      PYTHONUNBUFFERED: '1',
      ...process.env
    }
  }]
}