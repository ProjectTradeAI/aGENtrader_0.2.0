#!/usr/bin/env python3
"""
aGENtrader v0.2.2 Version Update Script

This script updates version references across the codebase to ensure consistency
with the aGENtrader v0.2.2 branding guidelines.
"""

import os
import re
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('version_update')

# Define version constants
OLD_VERSIONS = [
    r'aGENtrader v2',
    r'aGENtrader v0\.2\.0',
    r'aGENtrader v0\.2\.1',
    r'aGentrader',
    r'aGENtrader ([^v0\.2\.2])',
    r'v0\.2\.0',
    r'v0\.2\.1',
    r'v2([^\.])' # Match v2 but not v0.2.x
]
NEW_VERSION = 'aGENtrader v0.2.2'
VERSION_NUMBER = 'v0.2.2'

# Define file types to update
PYTHON_EXTENSIONS = ['.py', '.pyw']
CONFIG_EXTENSIONS = ['.json', '.jsonl', '.yml', '.yaml']
DOC_EXTENSIONS = ['.md', '.txt']
LOG_EXTENSIONS = ['.log']

# Define directories to exclude
EXCLUDE_DIRS = [
    'venv', 
    'env', 
    '.git',
    'archive',
    '__pycache__',
    'node_modules'
]

def create_directory_structure():
    """Create the versioned logs directory structure."""
    # Create directory structure for logs
    log_structure = [
        f"logs/v0.2.2/technical_analyst",
        f"logs/v0.2.2/sentiment_analyst",
        f"logs/v0.2.2/sentiment_aggregator",
        f"logs/v0.2.2/liquidity_analyst",
        f"logs/v0.2.2/funding_rate_analyst",
        f"logs/v0.2.2/open_interest_analyst",
        f"logs/v0.2.2/decision_agent",
        f"logs/v0.2.2/trade_plan_agent",
        f"logs/v0.2.2/tone_agent",
        f"logs/v0.2.2/portfolio_manager",
        f"logs/v0.2.2/market_data",
        f"logs/v0.2.2/system",
    ]
    
    # Add date directories for today
    today = datetime.now().strftime('%Y%m%d')
    log_structure_with_dates = []
    for directory in log_structure:
        date_dir = os.path.join(directory, today)
        log_structure_with_dates.append(date_dir)
    
    # Create directories
    for directory in log_structure_with_dates:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Create archive directory for old versions if it doesn't exist
    os.makedirs("logs/archive/v0.2.0", exist_ok=True)
    os.makedirs("logs/archive/v0.2.1", exist_ok=True)
    logger.info("Created archive directories for older versions")

def update_file_content(file_path: str) -> bool:
    """
    Update version references in a file.
    
    Args:
        file_path: Path to the file to update
        
    Returns:
        True if the file was updated, False otherwise
    """
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return False
    
    # Skip binary or very large files
    if len(content) > 10_000_000 or not all(c in range(128) for c in content[:1000]):
        logger.warning(f"Skipping large or binary file: {file_path}")
        return False
    
    # Make a copy of the original content for comparison
    original_content = content
    
    # Update simple version references
    for old_version in OLD_VERSIONS:
        # Special handling for v2 to avoid changing v0.2.2
        if old_version == r'v2([^\.])':
            content = re.sub(r'v2([^\.])', f'v0.2.2\\1', content)
        elif old_version == r'aGENtrader ([^v0\.2\.2])':
            content = re.sub(r'aGENtrader ([^v0\.2\.2])', f'aGENtrader v0.2.2 \\1', content)
        else:
            content = re.sub(old_version, NEW_VERSION, content)
    
    # Update log file paths
    content = re.sub(
        r'logs/agentrader_', 
        f'logs/v0.2.2/system/agentrader_', 
        content
    )
    content = re.sub(
        r'logs/aGENtrader_', 
        f'logs/v0.2.2/system/aGENtrader_', 
        content
    )
    content = re.sub(
        r'logs/decision_summary', 
        f'logs/v0.2.2/decision_agent/decision_summary', 
        content
    )
    content = re.sub(
        r'logs/tone_summary', 
        f'logs/v0.2.2/tone_agent/tone_summary', 
        content
    )
    content = re.sub(
        r'logs/trade_plan', 
        f'logs/v0.2.2/trade_plan_agent/trade_plan', 
        content
    )
    
    # Update CLI banner formats
    content = re.sub(
        r'=== ([^=]*) ===', 
        f'=== aGENtrader v0.2.2: \\1 ===', 
        content
    )
    
    # Update version fields in dictionaries
    content = re.sub(
        r'"version":\s*"([^"]*)"', 
        f'"version": "v0.2.2"', 
        content
    )
    content = re.sub(
        r"'version':\s*'([^']*)'", 
        f"'version': 'v0.2.2'", 
        content
    )
    
    # Add version field in __init__ methods if missing
    if '.py' in file_path:
        content = re.sub(
            r'(\s+)def __init__\(self(.*?)\):(.*?)super\(\).__init__\(([^)]*)\)',
            r'\1def __init__(self\2):\3super().__init__(\4)\n\1    self.version = "v0.2.2"',
            content,
            flags=re.DOTALL
        )
    
    # If content has changed, write it back
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Updated file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {str(e)}")
            return False
    
    return False

def find_and_update_files(root_dir: str = ".") -> Dict[str, int]:
    """
    Find and update version references in all files in the given directory.
    
    Args:
        root_dir: Root directory to search for files
        
    Returns:
        Dictionary with update statistics
    """
    stats = {
        "total_files": 0,
        "updated_files": 0,
        "python_files": 0,
        "config_files": 0,
        "doc_files": 0,
        "log_files": 0,
        "other_files": 0
    }
    
    # Walk through all files in the directory
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            
            # Count file by type
            if ext in PYTHON_EXTENSIONS:
                stats["python_files"] += 1
            elif ext in CONFIG_EXTENSIONS:
                stats["config_files"] += 1
            elif ext in DOC_EXTENSIONS:
                stats["doc_files"] += 1
            elif ext in LOG_EXTENSIONS:
                stats["log_files"] += 1
            else:
                stats["other_files"] += 1
            
            stats["total_files"] += 1
            
            # Update file content
            if update_file_content(file_path):
                stats["updated_files"] += 1
    
    return stats

def migrate_old_log_files():
    """Migrate old log files to archive directories."""
    # Define patterns to identify older version files
    v0_2_0_pattern = re.compile(r'.*v0\.2\.0.*|.*agentrader_2025[01][0-9].*')
    v0_2_1_pattern = re.compile(r'.*v0\.2\.1.*|.*agentrader_202504.*')
    
    # Get all files in the logs directory
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        logger.warning("Logs directory does not exist, skipping migration")
        return
    
    files_to_move = []
    
    for file in os.listdir(logs_dir):
        file_path = os.path.join(logs_dir, file)
        
        # Skip directories under /logs that are part of the new structure
        if os.path.isdir(file_path) and file in ["v0.2.2", "archive"]:
            continue
        
        # Check if file belongs to v0.2.0
        if v0_2_0_pattern.match(file):
            target_dir = "logs/archive/v0.2.0"
            files_to_move.append((file_path, os.path.join(target_dir, file)))
        
        # Check if file belongs to v0.2.1
        elif v0_2_1_pattern.match(file):
            target_dir = "logs/archive/v0.2.1"
            files_to_move.append((file_path, os.path.join(target_dir, file)))
        
        # Other old files go to v0.2.1 by default
        elif os.path.isfile(file_path):
            target_dir = "logs/archive/v0.2.1"
            files_to_move.append((file_path, os.path.join(target_dir, file)))
    
    # Move files
    for source, target in files_to_move:
        try:
            os.rename(source, target)
            logger.info(f"Moved {source} to {target}")
        except Exception as e:
            logger.error(f"Failed to move {source} to {target}: {str(e)}")

def update_class_definitions():
    """Update agent class definitions to include version information."""
    agent_files = [
        ("agents/base_agent.py", "BaseAgent"),
        ("agents/base_analyst_agent.py", "BaseAnalystAgent"),
        ("agents/base_decision_agent.py", "BaseDecisionAgent"),
        ("agents/technical_analyst_agent.py", "TechnicalAnalystAgent"),
        ("agents/sentiment_analyst_agent.py", "SentimentAnalystAgent"),
        ("agents/sentiment_aggregator_agent.py", "SentimentAggregatorAgent"),
        ("agents/liquidity_analyst_agent.py", "LiquidityAnalystAgent"),
        ("agents/funding_rate_analyst_agent.py", "FundingRateAnalystAgent"),
        ("agents/open_interest_analyst_agent.py", "OpenInterestAnalystAgent"),
        ("agents/decision_agent.py", "DecisionAgent"),
        ("agents/trade_plan_agent.py", "TradePlanAgent"),
        ("agents/portfolio_manager_agent.py", "PortfolioManagerAgent"),
        ("agents/tone_agent.py", "ToneAgent")
    ]
    
    for file_path, class_name in agent_files:
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} does not exist, skipping")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the class has a version attribute
        if 'self.version = ' not in content:
            # Add version attribute to __init__ method
            pattern = fr'class\s+{class_name}\(.*?\):\s*.*?def\s+__init__\s*\(self(.*?)\):(.*?)super\(\)'
            replacement = fr'class {class_name}(\\1):\n    """{class_name} for aGENtrader v0.2.2"""\n\\2def __init__(self\\3):\\4    self.version = "v0.2.2"\n        super()'
            
            # Apply the replacement
            updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            if updated_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                logger.info(f"Added version attribute to {class_name} in {file_path}")

def create_version_info_file():
    """Create a version info file with the current version information."""
    version_info = {
        "version": VERSION_NUMBER,
        "name": "aGENtrader",
        "full_name": NEW_VERSION,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "description": "Multi-agent AI trading system",
        "major_version": 0,
        "minor_version": 2,
        "patch_version": 2
    }
    
    # Write to version.json
    with open("version.json", 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=4)
    
    logger.info("Created version.json file")

def main():
    logger.info(f"=== Starting Version Update to {NEW_VERSION} ===")
    
    # Create directory structure
    create_directory_structure()
    
    # Migrate old log files
    migrate_old_log_files()
    
    # Update class definitions
    update_class_definitions()
    
    # Create version info file
    create_version_info_file()
    
    # Find and update files
    stats = find_and_update_files()
    
    # Log statistics
    logger.info(f"=== Version Update Complete ===")
    logger.info(f"Total files scanned: {stats['total_files']}")
    logger.info(f"Files updated: {stats['updated_files']}")
    logger.info(f"Python files: {stats['python_files']}")
    logger.info(f"Config files: {stats['config_files']}")
    logger.info(f"Document files: {stats['doc_files']}")
    logger.info(f"Log files: {stats['log_files']}")
    logger.info(f"Other files: {stats['other_files']}")

if __name__ == "__main__":
    main()