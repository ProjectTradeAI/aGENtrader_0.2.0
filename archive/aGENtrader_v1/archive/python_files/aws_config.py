"""AWS-specific configuration for LLM integration"""

# AWS instance-specific settings
AWS_DEPLOYMENT = True

# Model configuration
DEFAULT_MODEL_PATH = "models/llm_models/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"
DEFAULT_MODEL_REPO = "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"
DEFAULT_MODEL_FILE = "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf"

# Performance settings for EC2
import multiprocessing
DEFAULT_CONTEXT_LENGTH = 8192
NUM_THREADS = multiprocessing.cpu_count()  # Use all available CPU cores
N_GPU_LAYERS = 0  # Set to 0 if no GPU, or higher for GPU instances

# Advanced performance settings
BATCH_SIZE = 512  # Higher values may be faster but use more memory
OFFLOAD_KV = True  # Set to True to offload KV cache to CPU when possible
ROPE_SCALING_TYPE = "yarn"  # Better for longer contexts

# Timeout settings (in seconds)
DEFAULT_TIMEOUT = 120
ANALYST_TIMEOUT = 180
DECISION_TIMEOUT = 240
