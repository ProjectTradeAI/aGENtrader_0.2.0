#!/usr/bin/env python3
"""
aGENtrader v2.2 - Versioning Verification Script

This script verifies that the Git-based versioning system is correctly set up
to support the rollback mechanism.
"""

import os
import sys
import subprocess
import re
from typing import List, Tuple, Dict, Any, Optional

# ANSI color codes for prettier output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"


def print_header():
    """Print a nice header for the verification report"""
    print(f"\n{BLUE}====================================================================={RESET}")
    print(f"{BLUE}            aGENtrader v2.2 - Versioning Verification{RESET}")
    print(f"{BLUE}====================================================================={RESET}\n")


def run_command(command: List[str]) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr.strip()}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_git_repo() -> Tuple[bool, str]:
    """Check if current directory is a Git repository"""
    success, output = run_command(["git", "rev-parse", "--is-inside-work-tree"])
    if success and output == "true":
        return True, "Valid Git repository detected"
    return False, "Not a valid Git repository"


def check_git_tags() -> Tuple[bool, str, List[str]]:
    """Check if there are Git tags available"""
    success, output = run_command(["git", "tag", "-l"])
    if not success:
        return False, "Failed to list Git tags", []
    
    tags = [tag for tag in output.split("\n") if tag]
    if tags:
        return True, f"Found {len(tags)} Git tags", tags
    else:
        return False, "No Git tags found", []


def check_versioning_in_files() -> List[Tuple[str, bool, str]]:
    """Check if versioning is properly implemented in key files"""
    files_to_check = [
        "build_image.sh",
        "docker/docker-compose.yml",
        "deployment/deploy_ec2.sh",
        "deployment/rollback_ec2.sh"
    ]
    
    results = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            results.append((file_path, False, "File not found"))
            continue
            
        with open(file_path, "r") as file:
            content = file.read()
            
        # Define patterns to look for in each file type
        if file_path.endswith(".sh"):
            version_patterns = [
                r"VERSION=\$\(git describe --tags --always",  # Shell script Git versioning
                r"TAG=\$\(git describe",                       # Alternative form
                r"version.*\$VERSION"                          # Version variable usage
            ]
        elif file_path.endswith(".yml"):
            version_patterns = [
                r"image:.*\$\{VERSION",                        # Docker Compose version variable
                r"VERSION=\$\{VERSION",                        # Environment variable passing
            ]
        else:
            version_patterns = [r"version", r"VERSION"]         # Generic checks
            
        # Check for each pattern
        found_patterns = []
        for pattern in version_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
                
        if found_patterns:
            results.append((file_path, True, f"Version handling detected with {len(found_patterns)} patterns"))
        else:
            results.append((file_path, False, "No version handling detected"))
            
    return results


def check_docker_build_args() -> Tuple[bool, str]:
    """Check if Dockerfile has support for build args for versioning"""
    dockerfile_path = "docker/Dockerfile"
    
    if not os.path.exists(dockerfile_path):
        return False, "Dockerfile not found"
        
    with open(dockerfile_path, "r") as file:
        content = file.read()
        
    # Look for ARG directives in Dockerfile
    arg_matches = re.findall(r"ARG\s+VERSION", content)
    label_matches = re.findall(r"LABEL\s+version", content)
    
    if arg_matches:
        if label_matches:
            return True, f"Dockerfile has {len(arg_matches)} VERSION ARG(s) and {len(label_matches)} version LABEL(s)"
        else:
            return True, f"Dockerfile has {len(arg_matches)} VERSION ARG(s) but no version LABELs"
    else:
        return False, "Dockerfile does not have VERSION ARG directive for versioning"


def simulate_version_resolution() -> Tuple[bool, str]:
    """Test if Git versioning works by simulating a resolve"""
    success, output = run_command(["git", "describe", "--tags", "--always"])
    if success:
        return True, f"Version resolution successful: {output}"
    else:
        return False, "Failed to resolve version using Git describe"


def main():
    """Run versioning verification checks"""
    print_header()
    
    # Perform checks
    print(f"{BLUE}Performing versioning verification checks...{RESET}\n")
    
    # Check 1: Git repository
    repo_ok, repo_msg = check_git_repo()
    print(f"{GREEN if repo_ok else RED}[{'✓' if repo_ok else '✗'}] Git repository: {repo_msg}{RESET}")
    
    if not repo_ok:
        print(f"\n{RED}Critical failure: Not a valid Git repository. Aborting checks.{RESET}")
        return 1
    
    # Check 2: Git tags
    tags_ok, tags_msg, tags = check_git_tags()
    print(f"{GREEN if tags_ok else YELLOW}[{'✓' if tags_ok else '!'}] Git tags: {tags_msg}{RESET}")
    
    if tags:
        print("  Example tags:")
        for tag in tags[:5]:  # Show up to 5 tags as examples
            print(f"  - {tag}")
        if len(tags) > 5:
            print(f"  ...and {len(tags) - 5} more")
    
    # Check 3: Version resolution
    version_ok, version_msg = simulate_version_resolution()
    print(f"{GREEN if version_ok else RED}[{'✓' if version_ok else '✗'}] Version resolution: {version_msg}{RESET}")
    
    # Check 4: Versioning in files
    print(f"\n{BLUE}Checking versioning in key deployment files:{RESET}")
    file_results = check_versioning_in_files()
    
    all_files_ok = all(result[1] for result in file_results)
    
    for file_path, is_ok, message in file_results:
        print(f"{GREEN if is_ok else RED}[{'✓' if is_ok else '✗'}] {file_path}: {message}{RESET}")
    
    # Check 5: Dockerfile build args
    docker_ok, docker_msg = check_docker_build_args()
    print(f"\n{GREEN if docker_ok else YELLOW}[{'✓' if docker_ok else '!'}] Dockerfile: {docker_msg}{RESET}")
    
    # Overall assessment
    print(f"\n{BLUE}Overall assessment:{RESET}")
    if repo_ok and version_ok and all_files_ok:
        print(f"{GREEN}✓ Versioning system is properly set up for rollbacks{RESET}")
        if not tags_ok:
            print(f"{YELLOW}! Warning: No Git tags found. Consider creating version tags for easier rollbacks{RESET}")
            print(f"{YELLOW}  Example: git tag -a v0.2.0 -m 'Version 0.2.0' && git push origin v0.2.0{RESET}")
        if not docker_ok:
            print(f"{YELLOW}! Warning: Dockerfile may not fully support versioning. Consider adding ARG VERSION directive{RESET}")
        return 0
    else:
        print(f"{RED}✗ Versioning system needs improvements to fully support rollbacks{RESET}")
        
        if not version_ok:
            print(f"{RED}  - Fix version resolution using Git describe{RESET}")
        
        if not all_files_ok:
            print(f"{RED}  - Update the following files to properly handle versioning:{RESET}")
            for file_path, is_ok, _ in file_results:
                if not is_ok:
                    print(f"{RED}    * {file_path}{RESET}")
        
        if not docker_ok:
            print(f"{RED}  - Update Dockerfile to support build-time version arguments{RESET}")
            
        return 1


if __name__ == "__main__":
    sys.exit(main())