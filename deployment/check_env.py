#!/usr/bin/env python3
"""
aGENtrader v2.2 - Environment Setup Check

This script checks that all required environment variables are set
correctly for deployment and verifies API connections if possible.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode
import datetime

# ANSI color codes for prettier output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"

# Required environment variables
REQUIRED_ENV_VARS = [
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "XAI_API_KEY"
]

# Optional environment variables
OPTIONAL_ENV_VARS = [
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "AGENTRADER_VERSION"
]

# API test endpoints
BINANCE_TEST_URL = "https://api.binance.com/api/v3/ping"
BINANCE_ACCOUNT_URL = "https://api.binance.com/api/v3/account"


def print_header():
    """Print header for the environment check report"""
    print(f"\n{BLUE}====================================================================={RESET}")
    print(f"{BLUE}            aGENtrader v2.2 - Environment Check{RESET}")
    print(f"{BLUE}====================================================================={RESET}\n")
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"System: {os.uname().sysname} {os.uname().release}")
    print()


def print_section(title):
    """Print a section header"""
    print(f"\n{BLUE}---------------------------------------------------------------------{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}---------------------------------------------------------------------{RESET}")


def check_env_vars() -> Tuple[List[str], List[str], List[str]]:
    """
    Check for the presence of all required and optional environment variables.
    
    Returns:
        Tuple of (found_required, missing_required, found_optional)
    """
    found_required = []
    missing_required = []
    found_optional = []
    
    # Check required variables
    for var in REQUIRED_ENV_VARS:
        if var in os.environ and os.environ[var]:
            found_required.append(var)
        else:
            missing_required.append(var)
    
    # Check optional variables
    for var in OPTIONAL_ENV_VARS:
        if var in os.environ and os.environ[var]:
            found_optional.append(var)
    
    return found_required, missing_required, found_optional


def test_binance_connection() -> Tuple[bool, str]:
    """
    Test connection to Binance API.
    
    Returns:
        Tuple of (success, message)
    """
    if "BINANCE_API_KEY" not in os.environ or "BINANCE_API_SECRET" not in os.environ:
        return False, "Binance API credentials are not set"
    
    api_key = os.environ["BINANCE_API_KEY"]
    api_secret = os.environ["BINANCE_API_SECRET"]
    
    if not api_key or not api_secret:
        return False, "Binance API credentials are empty"
    
    # First test simple ping (doesn't require auth)
    try:
        headers = {"X-MBX-APIKEY": api_key}
        response = requests.get(BINANCE_TEST_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return False, f"Binance ping test failed with status {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Binance ping test failed with error: {str(e)}"
    
    # Now test authenticated endpoint
    try:
        timestamp = int(time.time() * 1000)
        params = {
            "timestamp": int(timestamp)
        }
        
        # Create signature
        query_string = urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Create new params dict with the signature
        query_params = {
            "timestamp": int(timestamp),
            "signature": signature
        }
        
        headers = {"X-MBX-APIKEY": api_key}
        response = requests.get(
            BINANCE_ACCOUNT_URL,
            params=query_params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return False, f"Binance auth test failed with status {response.status_code}: {response.text}"
        
        # Check if the response is valid
        data = response.json()
        if "accountType" not in data:
            return False, "Binance auth response is missing 'accountType' field"
            
        return True, f"Binance API connection successful (Account type: {data['accountType']})"
        
    except Exception as e:
        return False, f"Binance auth test failed with error: {str(e)}"


def test_xai_connection() -> Tuple[bool, str]:
    """
    Test connection to XAI API.
    
    Returns:
        Tuple of (success, message)
    """
    if "XAI_API_KEY" not in os.environ:
        return False, "XAI API key is not set"
    
    api_key = os.environ["XAI_API_KEY"]
    
    if not api_key:
        return False, "XAI API key is empty"
    
    # XAI doesn't have a dedicated ping endpoint, so we'll just verify the key format
    if len(api_key) < 32:  # Assuming minimum key length
        return False, "XAI API key appears to be invalid (too short)"
    
    # We could make a real API call here, but since it might incur costs,
    # we'll just do a basic check of the key presence and format
    return True, "XAI API key is present and appears to be valid"


def check_dotenv_file() -> Tuple[bool, str, Optional[Dict[str, str]]]:
    """
    Check if .env file exists and contains the required variables.
    
    Returns:
        Tuple of (exists, message, env_contents)
    """
    env_file = '.env'
    env_contents = {}
    
    if not os.path.exists(env_file):
        return False, "No .env file found", None
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_contents[key] = value
    except Exception as e:
        return True, f"Error reading .env file: {str(e)}", None
    
    missing_in_env = []
    for var in REQUIRED_ENV_VARS:
        if var not in env_contents or not env_contents[var]:
            missing_in_env.append(var)
    
    if missing_in_env:
        return True, f"Found .env file but missing {', '.join(missing_in_env)}", env_contents
    
    return True, "Found .env file with all required variables", env_contents


def main():
    """Run environment checks and display results"""
    print_header()
    
    # Check environment variables
    print_section("Environment Variables")
    found_required, missing_required, found_optional = check_env_vars()
    
    if found_required:
        print(f"{GREEN}✓ Found required environment variables:{RESET}")
        for var in found_required:
            # Hide the actual values for security
            print(f"  - {var} = {'*' * 10}")
    
    if missing_required:
        print(f"{RED}× Missing required environment variables:{RESET}")
        for var in missing_required:
            print(f"  - {var}")
    
    if found_optional:
        print(f"{GREEN}✓ Found optional environment variables:{RESET}")
        for var in found_optional:
            print(f"  - {var} = {'*' * 10}")
    
    # Check .env file
    print_section(".env File")
    env_exists, env_message, env_contents = check_dotenv_file()
    
    if env_exists:
        print(f"{GREEN}✓ {env_message}{RESET}")
        
        # Show which vars are in .env file but not loaded in environment
        if env_contents:
            not_loaded = []
            for key in env_contents:
                if key not in os.environ:
                    not_loaded.append(key)
            
            if not_loaded:
                print(f"{YELLOW}! Warning: Some variables in .env file are not loaded:{RESET}")
                for var in not_loaded:
                    print(f"  - {var}")
                print(f"{YELLOW}  This may happen if the script is not using dotenv package.{RESET}")
    else:
        print(f"{RED}× {env_message}{RESET}")
        print(f"{YELLOW}  Create a .env file with the following variables:{RESET}")
        for var in REQUIRED_ENV_VARS:
            print(f"  - {var}=your_{var.lower()}_here")
    
    # Test API connections
    print_section("API Connections")
    
    # Test Binance API
    binance_success, binance_message = test_binance_connection()
    if binance_success:
        print(f"{GREEN}✓ Binance API: {binance_message}{RESET}")
    else:
        print(f"{RED}× Binance API: {binance_message}{RESET}")
    
    # Test XAI API
    xai_success, xai_message = test_xai_connection()
    if xai_success:
        print(f"{GREEN}✓ XAI API: {xai_message}{RESET}")
    else:
        print(f"{RED}× XAI API: {xai_message}{RESET}")
    
    # Print summary
    print_section("Summary")
    
    if not missing_required and (binance_success or xai_success):
        print(f"{GREEN}✓ Environment is ready for deployment!{RESET}")
        return 0
    else:
        print(f"{YELLOW}! Environment needs attention before deployment.{RESET}")
        
        if missing_required:
            print(f"{RED}× Missing required environment variables: {', '.join(missing_required)}{RESET}")
        
        if not binance_success:
            print(f"{RED}× Binance API connection issue: {binance_message}{RESET}")
        
        if not xai_success:
            print(f"{RED}× XAI API connection issue: {xai_message}{RESET}")
        
        print(f"\n{YELLOW}Please fix these issues by updating your .env file and reloading.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())