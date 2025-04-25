FROM python:3.11-slim

LABEL maintainer="aGENtrader Support <support@agentrader.ai>"
LABEL description="aGENtrader v2 - Advanced multi-agent AI trading system"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directories
WORKDIR /app
RUN mkdir -p /app/logs

# Copy requirements first for better caching
COPY agentrader_v2_requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r agentrader_v2_requirements.txt

# Copy application code
COPY . /app/

# Create a non-root user to run the app
RUN useradd -m agentrader
RUN chown -R agentrader:agentrader /app
USER agentrader

# Set up entrypoint
ENTRYPOINT ["python", "-m", "aGENtrader_v2.run"]

# Default command with arguments
CMD ["--mode", "test", "--symbol", "BTC/USDT", "--interval", "1h", "--duration", "24h", "--config", "config/default.json"]