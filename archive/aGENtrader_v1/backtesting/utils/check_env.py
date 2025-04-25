#!/usr/bin/env python3
"""
Environment Variable Checker

This script checks if environment variables are properly loaded.
"""
import os
import sys
from dotenv import load_dotenv

def main():
    """Check environment variables."""
    print("Checking environment variables...")
    
    # Try to load environment variables
    print("Loading environment variables from .env file...")
    load_dotenv()
    
    # Check DATABASE_URL
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Mask the actual value for security
        masked_url = db_url[:10] + "..." + db_url[-10:] if len(db_url) > 20 else "***"
        print(f"DATABASE_URL is set: {masked_url}")
    else:
        print("DATABASE_URL is NOT set!")
    
    # Check ALPACA_API_KEY
    alpaca_key = os.environ.get("ALPACA_API_KEY")
    if alpaca_key:
        print("ALPACA_API_KEY is set")
    else:
        print("ALPACA_API_KEY is NOT set")
    
    # Check ALPACA_API_SECRET
    alpaca_secret = os.environ.get("ALPACA_API_SECRET")
    if alpaca_secret:
        print("ALPACA_API_SECRET is set")
    else:
        print("ALPACA_API_SECRET is NOT set")
    
    # Print all environment variables (without sensitive values)
    print("\nAll environment variables:")
    for key in sorted(os.environ.keys()):
        value = os.environ[key]
        # Mask sensitive values
        if key in ["DATABASE_URL", "ALPACA_API_KEY", "ALPACA_API_SECRET"] and value:
            masked_value = "***MASKED***"
        else:
            masked_value = value
        print(f"  {key}: {masked_value}")

if __name__ == "__main__":
    main()