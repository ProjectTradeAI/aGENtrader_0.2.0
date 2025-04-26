#!/usr/bin/env python3
"""
aGENtrader v2.2 - Version Extraction Test

This script tests that version information is correctly extracted from Git
and used in the Docker build and runtime environments.
"""

import os
import sys
import subprocess
import argparse
from typing import Dict, Optional, Tuple

# ANSI color codes
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def print_header():
    """Print a nice header for the test report"""
    print(f"{BLUE}=====================================================================")
    print(f"            aGENtrader v2.2 - Version Extraction Test")
    print(f"====================================================================={NC}")
    print()


def run_command(command: list) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except Exception as e:
        return False, str(e)


def check_git_version() -> Tuple[bool, str]:
    """Get the current Git version (tag or commit)"""
    # Try to get the most descriptive version (tag-commits-hash)
    success, version = run_command(["git", "describe", "--tags", "--always"])
    if not success:
        # If that fails, just get the commit hash
        success, version = run_command(["git", "rev-parse", "--short", "HEAD"])
        if not success:
            return False, "Failed to extract Git version information"
    return True, version


def check_dockerfile_args() -> Dict[str, str]:
    """Check if Dockerfile contains VERSION and BUILD_DATE args"""
    result = {
        "version_arg": "Not found",
        "version_label": "Not found",
        "version_env": "Not found",
        "build_date": "Not found"
    }
    
    try:
        with open("docker/Dockerfile", "r") as f:
            content = f.read()
            
        # Check for VERSION ARG
        if "ARG VERSION=" in content:
            result["version_arg"] = "Found"
            
        # Check for version LABEL
        if "LABEL version=" in content:
            result["version_label"] = "Found"
            
        # Check for AGENTRADER_VERSION environment variable
        if "ENV AGENTRADER_VERSION=" in content:
            result["version_env"] = "Found"
            
        # Check for BUILD_DATE
        if "ARG BUILD_DATE=" in content:
            result["build_date"] = "Found"
            
    except Exception as e:
        print(f"{RED}Error checking Dockerfile: {str(e)}{NC}")
    
    return result


def check_docker_compose() -> Tuple[bool, str]:
    """Check if docker-compose.yml correctly uses VERSION variable"""
    try:
        with open("docker/docker-compose.yml", "r") as f:
            content = f.read()
            
        if "${VERSION:-" in content:
            return True, "Found VERSION variable with default fallback"
        elif "${VERSION}" in content:
            return True, "Found VERSION variable (without fallback)"
        else:
            return False, "VERSION variable not found in docker-compose.yml"
            
    except Exception as e:
        return False, f"Error checking docker-compose.yml: {str(e)}"


def check_version_in_scripts() -> Dict[str, str]:
    """Check if deployment scripts correctly pass version information"""
    results = {}
    scripts = [
        "build_image.sh",
        "deployment/deploy_ec2.sh",
        "deployment/rollback_ec2.sh"
    ]
    
    for script in scripts:
        try:
            with open(script, "r") as f:
                content = f.read()
                
            if "VERSION=" in content and "git describe" in content:
                results[script] = "Correctly extracts Git version"
            elif "VERSION=" in content:
                results[script] = "Contains VERSION variable"
            else:
                results[script] = "No version handling found"
                
        except Exception as e:
            results[script] = f"Error: {str(e)}"
    
    return results


def simulate_version_extraction():
    """Simulate how version would be extracted in production"""
    print(f"{BLUE}Simulating version extraction in production environment:{NC}")
    
    # How version is extracted in Git
    success, git_version = check_git_version()
    if success:
        print(f"Git version extraction:      {GREEN}{git_version}{NC}")
    else:
        print(f"Git version extraction:      {RED}Failed{NC}")
    
    # How version would be passed to Docker build
    print(f"Docker build arg:            {YELLOW}VERSION={git_version}{NC}")
    
    # How version would be accessible in container
    print(f"Container environment var:   {YELLOW}AGENTRADER_VERSION={git_version}{NC}")
    
    # How it would be tagged
    print(f"Docker image tag:            {YELLOW}agentrader:{git_version}{NC}")
    
    print()
    print(f"{BLUE}Production deployment would use these commands:{NC}")
    print(f"VERSION={git_version} docker-compose build")
    print(f"VERSION={git_version} docker-compose up -d")
    print()


def main():
    """Run version extraction tests"""
    parser = argparse.ArgumentParser(description="Test version extraction for aGENtrader")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    print_header()
    
    print(f"{BLUE}Testing Git version extraction...{NC}")
    success, version = check_git_version()
    if success:
        print(f"{GREEN}✓ Successfully extracted version: {version}{NC}")
    else:
        print(f"{RED}× Failed to extract version: {version}{NC}")
        print(f"{YELLOW}Make sure you are running this script from the repository root.{NC}")
        sys.exit(1)
    
    print()
    print(f"{BLUE}Checking Dockerfile version arguments...{NC}")
    dockerfile_results = check_dockerfile_args()
    
    if dockerfile_results["version_arg"] == "Found":
        print(f"{GREEN}✓ Dockerfile contains VERSION ARG{NC}")
    else:
        print(f"{RED}× Dockerfile missing VERSION ARG{NC}")
    
    if dockerfile_results["version_label"] == "Found":
        print(f"{GREEN}✓ Dockerfile sets version LABEL{NC}")
    else:
        print(f"{RED}× Dockerfile missing version LABEL{NC}")
    
    if dockerfile_results["version_env"] == "Found":
        print(f"{GREEN}✓ Dockerfile sets AGENTRADER_VERSION environment variable{NC}")
    else:
        print(f"{RED}× Dockerfile missing AGENTRADER_VERSION environment variable{NC}")
    
    print()
    print(f"{BLUE}Checking docker-compose.yml...{NC}")
    success, message = check_docker_compose()
    if success:
        print(f"{GREEN}✓ {message}{NC}")
    else:
        print(f"{RED}× {message}{NC}")
    
    print()
    print(f"{BLUE}Checking version extraction in scripts...{NC}")
    script_results = check_version_in_scripts()
    
    for script, result in script_results.items():
        if "Error" in result:
            print(f"{RED}× {script}: {result}{NC}")
        elif "Correctly extracts" in result:
            print(f"{GREEN}✓ {script}: {result}{NC}")
        else:
            print(f"{YELLOW}! {script}: {result}{NC}")
    
    print()
    simulate_version_extraction()
    
    print(f"{BLUE}VERSION EXTRACTION TEST SUMMARY{NC}")
    print(f"{BLUE}---------------------------------------------{NC}")
    
    all_success = (
        success and 
        all(v == "Found" for v in dockerfile_results.values()) and
        "Error" not in " ".join(script_results.values())
    )
    
    if all_success:
        print(f"{GREEN}✓ Version extraction system is correctly configured{NC}")
        print(f"{GREEN}✓ Version information will be properly propagated{NC}")
        print()
        print(f"{BLUE}The system will use Git version: {version}{NC}")
    else:
        print(f"{RED}× Version extraction system has configuration issues{NC}")
        print(f"{YELLOW}Review the output above and fix any highlighted problems{NC}")
    
    print()
    print(f"{BLUE}Test completed.{NC}")


if __name__ == "__main__":
    main()