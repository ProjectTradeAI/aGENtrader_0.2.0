# LLM Setup Guide for aGENtrader

This guide outlines the setup of Large Language Models (LLMs) for the aGENtrader system.

## Overview

aGENtrader uses a hierarchical LLM selection system with the following priority:

1. **Local Mistral via Ollama** (primary for cost efficiency and privacy)
2. **Grok API** (fallback when local Ollama is unavailable)
3. **OpenAI API** (fallback when both Ollama and Grok are unavailable)

## Model Selection

The system now uses Mistral as the default local model, which has been chosen for its:
- Lower memory footprint (requires ~4GB vs Mixtral's 25.6GB)
- Sufficient performance for trading analysis
- Compatibility with resource-constrained EC2 instances

## Local LLM Setup

### Installing Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Installing Mistral Model

```bash
ollama pull mistral
```

### Testing Installation

```bash
# Test if Ollama is running
ollama list

# Quick test of Mistral
echo "Hello, what can you do for trading analysis?" | ollama run mistral
```

## API Fallbacks

If local Ollama is unavailable, the system will automatically fall back to cloud APIs:

1. **Grok API**: Requires `XAI_API_KEY` in environment variables
2. **OpenAI API**: Requires `OPENAI_API_KEY` in environment variables

## Memory Requirements

| Model   | Memory Required | Suitable For              |
|---------|----------------|---------------------------|
| Mistral | ~4GB           | EC2 t2/t3.medium and up   |
| Mixtral | ~25.6GB        | High-memory instances only |

## Simplified Switch Script

For EC2 instances with memory constraints, use our provided script to switch from Mixtral to Mistral:

```bash
# Make the script executable
chmod +x scripts/switch_to_mistral.sh

# Run the script
./scripts/switch_to_mistral.sh
```

## Environment Configuration

You can configure the default LLM provider and model in the `.env` file:

```ini
# Local LLM Setup
LLM_PROVIDER_DEFAULT=local
LLM_MODEL_DEFAULT=mistral
LLM_ENDPOINT_DEFAULT=http://localhost:11434

# API Keys for fallbacks
XAI_API_KEY=your_grok_key_here
OPENAI_API_KEY=your_openai_key_here
```

## Troubleshooting

### Ollama Connection Issues

If you see connection errors like:

```
WARNING:llm_client:Local Ollama server is not available: HTTPConnectionPool(host='localhost', port=11434)
```

1. **Check if Ollama is running:**
   ```bash
   ps aux | grep ollama
   ```

2. **Restart Ollama:**
   ```bash
   sudo systemctl restart ollama  # For systemd systems
   # OR
   ollama serve > /tmp/ollama.log 2>&1 &  # Manual start
   ```

3. **Verify port availability:**
   ```bash
   sudo lsof -i :11434
   ```

### Model Compatibility

If you see errors about insufficient memory:

```
Error: model requires more system memory than is available
```

Switch to the Mistral model using our provided script:

```bash
./scripts/switch_to_mistral.sh
```