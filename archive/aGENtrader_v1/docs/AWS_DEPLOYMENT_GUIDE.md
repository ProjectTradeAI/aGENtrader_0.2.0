# AWS EC2 Deployment Guide for Trading Bot with Local LLM

This guide provides step-by-step instructions for deploying the trading bot with local LLM integration to Amazon EC2, enabling more powerful model inference and faster backtesting.

## 1. Instance Selection

### Recommended Instance Types

| Use Case | Instance Type | vCPUs | Memory | Approx. Cost | LLM Capabilities |
|----------|--------------|-------|--------|--------------|------------------|
| Development & Testing | t3.xlarge | 4 | 16 GB | ~$0.17/hr | Llama-2-7B (quantized) |
| Standard Backtesting | r5.xlarge | 4 | 32 GB | ~$0.25/hr | Llama-2-13B (quantized) |
| Intensive Backtesting | r5.2xlarge | 8 | 64 GB | ~$0.50/hr | Llama-2-13B/70B (quantized) |

#### Cost-Saving Options
- Use **Spot Instances** to reduce costs by 70-90% (set a maximum price to avoid unexpected termination)
- Configure **Auto-shutdown** scripts to turn off instances when not in use
- Use **Amazon S3** to store model files and backtest results instead of keeping them on the instance

### Storage Requirements
- Root volume: 30 GB (gp3)
- Data volume: 100 GB (gp3) - for model files, database, and backtest results

## 2. Initial Setup

### 2.1. Launch Instance
1. Sign in to the AWS Management Console and navigate to EC2
2. Click "Launch Instance"
3. Configure the instance:
   - Name: `trading-bot-backtesting`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.xlarge (or as needed)
   - Key pair: Create or select existing
   - Network settings: Allow SSH (port 22)
   - Storage: Increase root volume to 30 GB
   - Add data volume: 100 GB gp3

### 2.2. Connect to Instance
```bash
ssh -i /path/to/your-key.pem ubuntu@your-instance-public-dns
```

### 2.3. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install -y python3-pip python3-dev build-essential git cmake

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install additional libraries for LLM support
sudo apt install -y libopenblas-dev
```

## 3. Project Setup

### 3.1. Clone Repository
```bash
# Clone the repository
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot

# Install Python dependencies
pip3 install -r requirements.txt

# Install additional packages for local LLM
pip3 install llama-cpp-python huggingface_hub autogen-agentchat
```

### 3.2. Configure Database
```bash
# Create database user and database
sudo -u postgres createuser trading_bot
sudo -u postgres createdb trading_bot_db -O trading_bot

# Set password for the user
sudo -u postgres psql -c "ALTER USER trading_bot WITH PASSWORD 'your_secure_password';"

# Update .env file with database credentials
echo "DATABASE_URL=postgresql://trading_bot:your_secure_password@localhost:5432/trading_bot_db" >> .env
```

### 3.3. Download LLM Models
```bash
# Create model directory
mkdir -p models/llm_models

# Option 1: Download smaller 7B model for development
python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download('TheBloke/Llama-2-7B-Chat-GGUF', 'llama-2-7b-chat.Q4_K_M.gguf', local_dir='models/llm_models')"

# Option 2: Download larger model for better analysis
python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download('TheBloke/Llama-2-13B-Chat-GGUF', 'llama-2-13b-chat.Q4_K_M.gguf', local_dir='models/llm_models')"
```

## 4. Model Configuration

### 4.1. Update Local LLM Configuration
Create a new configuration file for AWS deployment:

```bash
nano utils/llm_integration/aws_config.py
```

Add the following content:

```python
"""AWS-specific configuration for LLM integration"""

# AWS instance-specific settings
AWS_DEPLOYMENT = True

# Model configuration
DEFAULT_MODEL_PATH = "models/llm_models/llama-2-7b-chat.Q4_K_M.gguf"  # Update path to your downloaded model
DEFAULT_MODEL_REPO = "TheBloke/Llama-2-7B-Chat-GGUF"
DEFAULT_MODEL_FILE = "llama-2-7b-chat.Q4_K_M.gguf"

# Performance settings for EC2
DEFAULT_CONTEXT_LENGTH = 4096
NUM_THREADS = 4  # Set to number of available CPU cores
N_GPU_LAYERS = 0  # Set to 0 if no GPU, or higher for GPU instances

# Timeout settings (in seconds)
DEFAULT_TIMEOUT = 60
ANALYST_TIMEOUT = 90
DECISION_TIMEOUT = 120
```

### 4.2. Modify Main LLM Integration
Update `utils/llm_integration/local_llm.py` to use AWS-specific configuration:

```bash
nano utils/llm_integration/local_llm.py
```

Add the following near the top of the file:

```python
# Check if AWS configuration exists
try:
    from .aws_config import (
        AWS_DEPLOYMENT,
        DEFAULT_MODEL_PATH as AWS_MODEL_PATH,
        DEFAULT_MODEL_REPO as AWS_MODEL_REPO,
        DEFAULT_MODEL_FILE as AWS_MODEL_FILE,
        DEFAULT_CONTEXT_LENGTH as AWS_CONTEXT_LENGTH,
        NUM_THREADS as AWS_NUM_THREADS,
        N_GPU_LAYERS as AWS_N_GPU_LAYERS
    )
    USE_AWS_CONFIG = AWS_DEPLOYMENT
except ImportError:
    USE_AWS_CONFIG = False
```

Then update the constants section to use AWS config when available:

```python
# Constants
if USE_AWS_CONFIG:
    DEFAULT_MODEL_PATH = AWS_MODEL_PATH
    DEFAULT_MODEL_REPO = AWS_MODEL_REPO
    DEFAULT_MODEL_FILE = AWS_MODEL_FILE
    DEFAULT_CONTEXT_LENGTH = AWS_CONTEXT_LENGTH
    DEFAULT_NUM_THREADS = AWS_NUM_THREADS
    DEFAULT_N_GPU_LAYERS = AWS_N_GPU_LAYERS
else:
    DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      "../../models/llm_models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    DEFAULT_MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    DEFAULT_MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    DEFAULT_CONTEXT_LENGTH = 2048
    DEFAULT_NUM_THREADS = 2
    DEFAULT_N_GPU_LAYERS = 0
```

Update the `get_model()` function to use these settings:

```python
def get_model() -> Llama:
    """
    Gets or creates a thread-local model instance.
    
    Returns:
        Llama model instance
    """
    if not hasattr(_thread_local, "model"):
        try:
            # Make sure model is downloaded
            model_path = download_model_if_needed()
            
            # Load the model
            logger.info(f"Loading model from {model_path}...")
            _thread_local.model = Llama(
                model_path=model_path,
                n_ctx=DEFAULT_CONTEXT_LENGTH,
                n_threads=DEFAULT_NUM_THREADS,
                n_gpu_layers=DEFAULT_N_GPU_LAYERS,
                verbose=False
            )
            logger.info("Model loaded successfully")
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise LocalLLMException(f"Failed to load model: {str(e)}")
    
    return _thread_local.model
```

## 5. Deploy and Run

### 5.1. Set up PM2 for Process Management
```bash
# Install PM2 globally
sudo npm install -g pm2

# Start the application
pm2 start ecosystem.config.cjs

# Save the process list
pm2 save

# Set up PM2 to start on boot
pm2 startup
```

### 5.2. Set up Auto-shutdown Script (Optional)
Create a script to shut down the instance when idle:

```bash
nano auto-shutdown.sh
```

```bash
#!/bin/bash
# Auto-shutdown script for EC2 instance when idle

IDLE_TIME_THRESHOLD=60  # minutes
CPU_THRESHOLD=5         # percent

# Check if CPU usage is below threshold
avg_cpu=$(top -bn2 | grep "Cpu(s)" | tail -n1 | awk '{print $2}' | cut -d. -f1)

if [ $avg_cpu -lt $CPU_THRESHOLD ]; then
    echo "CPU usage below threshold ($avg_cpu% < $CPU_THRESHOLD%)"
    
    # Check for running backtests
    backtest_processes=$(ps aux | grep -E "run_backtest|run_enhanced_backtest" | grep -v grep | wc -l)
    
    if [ $backtest_processes -eq 0 ]; then
        echo "No active backtest processes detected"
        echo "Instance will shutdown in 5 minutes unless canceled"
        
        # Schedule shutdown
        sudo shutdown -h +5 "Auto-shutdown due to inactivity"
        
        # Create cancellation file
        echo '#!/bin/bash
sudo shutdown -c "Shutdown canceled"
echo "Scheduled shutdown canceled"' > /home/ubuntu/cancel-shutdown.sh
        
        chmod +x /home/ubuntu/cancel-shutdown.sh
    else
        echo "Backtest processes are still running, not shutting down"
    fi
else
    echo "CPU usage above threshold ($avg_cpu% >= $CPU_THRESHOLD%), not shutting down"
fi
```

Make the script executable and set up a cron job:

```bash
chmod +x auto-shutdown.sh
(crontab -l 2>/dev/null; echo "0 * * * * /home/ubuntu/trading-bot/auto-shutdown.sh >> /home/ubuntu/auto-shutdown.log 2>&1") | crontab -
```

### 5.3. Run a Backtest with Local LLM
```bash
# Create necessary directories
mkdir -p data/logs data/backtest_results

# Run a backtest with the local LLM
python3 run_backtest_with_local_llm.py --symbol BTCUSDT --interval 1h --start_date 2025-03-01 --end_date 2025-03-15 --analysis_timeout 90
```

### 5.4. Monitor Performance
```bash
# Check CPU usage
htop

# Monitor log files
tail -f data/logs/backtest_local_llm_*.log

# Check model memory usage
ps aux | grep llama
```

## 6. Performance Optimization

### 6.1. Optimize Model Performance
For better model performance with larger models, consider these optimizations:

```python
# utils/llm_integration/aws_config.py - Add these settings

# Advanced performance settings
BATCH_SIZE = 512  # Higher values may be faster but use more memory
OFFLOAD_KV = True  # Set to True to offload KV cache to CPU when possible
ROPE_SCALING_TYPE = "yarn"  # Better for longer contexts
KV_OFFLOAD_THRESHOLD = 0.5  # Percentage of context fill to trigger offload

```

Update the model initialization in `local_llm.py`:

```python
_thread_local.model = Llama(
    model_path=model_path,
    n_ctx=DEFAULT_CONTEXT_LENGTH,
    n_threads=DEFAULT_NUM_THREADS,
    n_gpu_layers=DEFAULT_N_GPU_LAYERS,
    n_batch=BATCH_SIZE if USE_AWS_CONFIG else 512,
    offload_kqv=OFFLOAD_KV if USE_AWS_CONFIG else False,
    rope_scaling_type=ROPE_SCALING_TYPE if USE_AWS_CONFIG else None,
    verbose=False
)
```

### 6.2. Database Performance
For faster database operations:

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Add these optimizations:
```
# Memory settings
shared_buffers = 4GB                    # 25% of instance memory
work_mem = 128MB                        # Higher for complex queries
maintenance_work_mem = 256MB            # Higher for maintenance tasks

# Write settings
wal_buffers = 16MB
synchronous_commit = off                # Faster but slightly less safe
checkpoint_timeout = 15min              # Less frequent checkpoints

# Query optimization
effective_cache_size = 12GB             # 75% of instance memory

# Apply changes
sudo systemctl restart postgresql
```

## 7. Backup and Data Management

### 7.1. Set up S3 Backup
Create a script to back up models and results to S3:

```bash
nano backup-to-s3.sh
```

```bash
#!/bin/bash
# Back up important data to S3

# Configure your bucket
S3_BUCKET="your-trading-bot-bucket"

# Backup backtest results
aws s3 sync data/backtest_results/ s3://$S3_BUCKET/backtest_results/

# Backup logs
aws s3 sync data/logs/ s3://$S3_BUCKET/logs/

# Backup database (optional)
pg_dump -U trading_bot trading_bot_db > db_backup.sql
aws s3 cp db_backup.sql s3://$S3_BUCKET/db_backups/db_backup_$(date +%Y%m%d_%H%M%S).sql
rm db_backup.sql

echo "Backup completed at $(date)"
```

Set up automated backup:
```bash
chmod +x backup-to-s3.sh
(crontab -l 2>/dev/null; echo "0 0 * * * /home/ubuntu/trading-bot/backup-to-s3.sh >> /home/ubuntu/s3-backup.log 2>&1") | crontab -
```

## 8. Security Considerations

### 8.1. Secure API Keys
Never store API keys directly in code or configuration files:

```bash
# Store secrets in environment variables
nano ~/.bashrc
```

Add:
```bash
# Trading Bot API Keys
export OPENAI_API_KEY="your-openai-key"
export EXCHANGE_API_KEY="your-exchange-key"
export EXCHANGE_API_SECRET="your-exchange-secret"
```

Apply changes:
```bash
source ~/.bashrc
```

### 8.2. Firewall Configuration
Secure your instance with a basic firewall:

```bash
# Install and configure UFW
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow 5432/tcp  # PostgreSQL (only if needed remotely)
sudo ufw enable
```

## 9. Troubleshooting

### Common Issues and Solutions

#### Model Loading Errors
```
Error loading model: Failed to allocate memory
```
**Solution**: Reduce context length or use a smaller/more quantized model.

#### Performance Issues
```
Response times are too slow for backtesting
```
**Solutions**:
- Increase NUM_THREADS to match available CPU cores
- Use a more quantized model (Q4_K_M instead of Q8_0)
- Test with smaller context lengths

#### Memory Management
```
Out of memory errors during long backtests
```
**Solutions**:
- Add memory monitoring and cleanup in the backtest loop
- Add explicit model unloading after each major analysis
- Add this code after each major LLM operation:
```python
# Clear model and run garbage collection
clear_model()
import gc
gc.collect()
```

## 10. Further Optimizations

### 10.1. GPU Acceleration
If using a GPU instance (like g4dn.xlarge):

1. Install CUDA drivers:
```bash
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
```

2. Update LLM configuration:
```python
# utils/llm_integration/aws_config.py
N_GPU_LAYERS = 32  # Use -1 for all layers on GPU
```

3. Reinstall llama-cpp-python with CUDA support:
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install --force-reinstall llama-cpp-python
```

### 10.2. Parallel Backtesting
For running multiple backtests simultaneously:

```bash
nano run_parallel_backtests.sh
```

```bash
#!/bin/bash
# Run multiple backtests in parallel

# Define backtest configurations
CONFIG1="--symbol BTCUSDT --interval 1h --start_date 2025-01-01 --end_date 2025-01-31"
CONFIG2="--symbol ETHUSDT --interval 1h --start_date 2025-01-01 --end_date 2025-01-31"
CONFIG3="--symbol BTCUSDT --interval 4h --start_date 2025-01-01 --end_date 2025-02-28"

# Run backtests in parallel
python3 run_backtest_with_local_llm.py $CONFIG1 --analysis_timeout 60 &
python3 run_backtest_with_local_llm.py $CONFIG2 --analysis_timeout 60 &
python3 run_backtest_with_local_llm.py $CONFIG3 --analysis_timeout 60 &

# Wait for all backtests to complete
wait

echo "All backtests completed!"
```

## 11. Conclusion

This deployment guide should help you set up a powerful EC2 instance for your trading bot with local LLM integration. The larger compute resources will allow you to use more capable models and run backtests much faster than on Replit.

Remember to monitor your AWS costs and use strategies like spot instances and auto-shutdown to minimize expenses when the system is not actively being used.