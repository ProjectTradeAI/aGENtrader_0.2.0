#!/usr/bin/env python3
"""
Version Tag Validation Script for aGENtrader v0.2.2

This script validates that all agent outputs (JSON, JSONL, logs) include the correct
system version from either settings.yaml or .env, ensuring version consistency
across all components of the aGENtrader system.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Set, Any, Optional, Tuple
import yaml
import re
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('version_validator')


def get_expected_version() -> str:
    """
    Get the expected version from version.json, core/version.py, or environment variables.
    
    Returns:
        The expected version string (e.g., "0.2.2", "v0.2.2")
    """
    # First try from version.json
    try:
        with open('version.json', 'r') as f:
            version_data = json.load(f)
            if 'version' in version_data:
                logger.info(f"Found version in version.json: {version_data['version']}")
                # Remove 'v' prefix if present for standardization
                return version_data['version'].lstrip('v')
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Could not read version from version.json: {e}")
    
    # Then try from core/version.py
    try:
        version_file_path = Path('core/version.py')
        if version_file_path.exists():
            with open(version_file_path, 'r') as f:
                content = f.read()
                match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    logger.info(f"Found version in core/version.py: {match.group(1)}")
                    return match.group(1)
    except Exception as e:
        logger.warning(f"Could not read version from core/version.py: {e}")
    
    # Then try from settings.yaml
    try:
        with open('config/settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
            if 'system' in settings and 'version' in settings['system']:
                logger.info(f"Found version in settings.yaml: {settings['system']['version']}")
                return settings['system']['version'].lstrip('v')
    except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
        logger.warning(f"Could not read version from settings.yaml: {e}")
    
    # Finally, try from environment variable
    env_version = os.environ.get('SYSTEM_VERSION')
    if env_version:
        logger.info(f"Found version in environment variable: {env_version}")
        return env_version.lstrip('v')
    
    # If we got here, we couldn't find a version
    logger.error("Could not determine system version from any source")
    return "0.2.2"  # Default to current version


def collect_files(directories: List[str], extensions: List[str], verbose: bool = False) -> List[str]:
    """
    Collect all files with the specified extensions from the specified directories.
    
    Args:
        directories: List of directory paths to search in
        extensions: List of file extensions to include (e.g., ['.json', '.jsonl'])
        verbose: Whether to print verbose information
        
    Returns:
        List of file paths
    """
    file_paths = []
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            continue
            
        if verbose:
            logger.info(f"Scanning directory: {directory}")
            
        for ext in extensions:
            # Use recursive globbing to find all files with the extension
            matching_files = list(dir_path.glob(f"**/*{ext}"))
            file_paths.extend([str(f) for f in matching_files])
            
            if verbose:
                logger.info(f"Found {len(matching_files)} {ext} files in {directory}")
    
    return file_paths


def validate_json_file(file_path: str, expected_version: str, version_keys: List[str], 
                       verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate that a JSON file contains the expected version in at least one of the specified keys.
    
    Args:
        file_path: Path to the JSON file
        expected_version: Expected version string
        version_keys: List of keys that might contain the version
        verbose: Whether to print verbose information
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    try:
        with open(file_path, 'r') as f:
            # Try loading as a single JSON object
            try:
                data = json.load(f)
                return validate_json_object(data, expected_version, version_keys, file_path, verbose)
            except json.JSONDecodeError:
                # If that fails, try loading as JSONL (multiple JSON objects per line)
                f.seek(0)
                lines = f.readlines()
                all_valid = True
                line_errors = []
                
                for i, line in enumerate(lines, 1):
                    if not line.strip():
                        continue
                        
                    try:
                        data = json.loads(line)
                        line_valid, line_error = validate_json_object(
                            data, expected_version, version_keys, f"{file_path}:line {i}", verbose
                        )
                        if not line_valid:
                            all_valid = False
                            line_errors.extend(line_error)
                    except json.JSONDecodeError as e:
                        all_valid = False
                        error = f"Invalid JSON at {file_path}:line {i}: {str(e)}"
                        line_errors.append(error)
                        if verbose:
                            logger.error(error)
                
                return all_valid, line_errors
    except Exception as e:
        error = f"Error processing file {file_path}: {str(e)}"
        errors.append(error)
        logger.error(error)
        return False, errors


def validate_json_object(data: Dict[str, Any], expected_version: str, version_keys: List[str], 
                         context: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate that a JSON object contains the expected version in at least one of the specified keys.
    
    Args:
        data: JSON object as a dictionary
        expected_version: Expected version string
        version_keys: List of keys that might contain the version
        context: Context information for error messages
        verbose: Whether to print verbose information
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    found_version = False
    found_version_value = None
    
    def check_nested_dict(d, path=''):
        nonlocal found_version, found_version_value
        
        for key, value in d.items():
            current_path = f"{path}.{key}" if path else key
            
            if key in version_keys:
                found_version = True
                found_version_value = value
                
                # Make version comparison consistent by stripping 'v' prefix if present
                cleaned_value = str(value).lstrip('v')
                cleaned_expected = expected_version.lstrip('v')
                
                if cleaned_value != cleaned_expected:
                    error = f"Version mismatch in {context}, key '{current_path}': expected {expected_version}, found {value}"
                    errors.append(error)
                    if verbose:
                        logger.error(error)
                elif verbose:
                    logger.info(f"Verified version in {context}, key '{current_path}': {value}")
            
            # Recurse into nested dictionaries
            if isinstance(value, dict):
                check_nested_dict(value, current_path)
            
            # Check for version in list elements if they are dictionaries
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        check_nested_dict(item, f"{current_path}[{i}]")
    
    check_nested_dict(data)
    
    if not found_version:
        error = f"No version tag found in {context}. Expected one of these keys: {', '.join(version_keys)}"
        errors.append(error)
        if verbose:
            logger.error(error)
    
    return len(errors) == 0, errors


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Validate version tags across aGENtrader output files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--directories', '-d', nargs='+', default=['logs', 'trades', 'datasets'],
                        help='Directories to scan for files')
    parser.add_argument('--extensions', '-e', nargs='+', default=['.json', '.jsonl'],
                        help='File extensions to check')
    parser.add_argument('--version-keys', '-k', nargs='+', 
                        default=['version', 'system_version', 'version_tag', 'agent_version', 'plan_version'],
                        help='Keys to check for version information')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    
    logger.info("Starting version tag validation")
    
    # Get the expected version
    expected_version = get_expected_version()
    logger.info(f"Expected version: {expected_version}")
    
    # Collect files to validate
    files = collect_files(args.directories, args.extensions, args.verbose)
    logger.info(f"Found {len(files)} files to validate")
    
    # Validate each file
    all_valid = True
    error_count = 0
    error_files = []
    
    for file_path in files:
        is_valid, errors = validate_json_file(file_path, expected_version, args.version_keys, args.verbose)
        
        if not is_valid:
            all_valid = False
            error_count += len(errors)
            error_files.append(file_path)
            
            for error in errors:
                logger.error(error)
    
    # Output final results
    if all_valid:
        logger.info("✅ Version tag validation successful! All files have consistent version tags.")
        sys.exit(0)
    else:
        logger.error(f"❌ Version tag validation failed! Found {error_count} errors in {len(error_files)} files.")
        logger.error("Files with errors:")
        for file_path in error_files:
            logger.error(f"  - {file_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()