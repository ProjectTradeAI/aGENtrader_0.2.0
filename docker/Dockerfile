FROM python:3.11-slim

# Accept build arguments for versioning
ARG VERSION="v0.2.0"
ARG BUILD_DATE="2025-04-25T00:00:00Z"

# Set metadata labels
LABEL maintainer="aGENtrader Support <support@agentrader.ai>"
LABEL description="aGENtrader v2 - Advanced multi-agent AI trading system"
LABEL version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.authors="aGENtrader Team"
LABEL org.opencontainers.image.url="https://github.com/ProjectTradeAI/aGENtrader_0.2.0"
LABEL org.opencontainers.image.documentation="https://github.com/ProjectTradeAI/aGENtrader_0.2.0/blob/main/README.md"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV AGENTRADER_VERSION="${VERSION}"
ENV IN_DOCKER=true
ENV TEST_DURATION=24h

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
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyyaml

# Copy application code
COPY . /app/

# Create a non-root user to run the app but ensure logs are accessible
RUN useradd -m agentrader
RUN mkdir -p /app/logs /app/reports /app/trades /app/config /app/data
RUN chmod -R 777 /app/logs /app/reports /app/trades /app/config /app/data
RUN chown -R agentrader:agentrader /app
# Run explicitly as root to ensure logs are accessible for validation
# USER agentrader

# Make docker_run.py executable
RUN chmod +x docker_run.py

# Set up entrypoint using the Docker-specific runner
ENTRYPOINT ["python", "docker_run.py"]

# No command needed as docker_run.py handles everything