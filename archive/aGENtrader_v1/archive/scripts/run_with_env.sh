#!/bin/bash
# Wrapper script to run Python commands with environment variables

# Set environment variables
export DATABASE_URL="${1}"
export ALPACA_API_KEY="${2}"
export ALPACA_API_SECRET="${3}"
export OPENAI_API_KEY="${4}"

# Shift arguments to remove the environment variables
shift 4

# Run the command with the remaining arguments
exec "$@"
