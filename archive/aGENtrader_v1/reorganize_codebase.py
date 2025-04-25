#!/usr/bin/env python3
"""
Codebase Reorganization Script

This script reorganizes the codebase based on the inventory results,
moving essential files to the new directory structure.
"""
import os
import re
import sys
import json
import shutil
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime

# Configuration for categorization
FILE_CATEGORIES = {
    'orchestration': {
        'patterns': [
            r'orchestration/.*\.py$',
            r'decision_session\.py$',
            r'agent_.*\.py$'
        ],
        'target_dir': 'orchestration'
    },
    'backtesting': {
        'patterns': [
            r'backtest.*\.py$',
            r'backtesting/.*\.py$'
        ],
        'target_dir': 'backtesting/core'
    },
    'backtesting_strategies': {
        'patterns': [
            r'strategies/.*\.py$',
            r'strategy_.*\.py$'
        ],
        'target_dir': 'backtesting/strategies'
    },
    'backtesting_analysis': {
        'patterns': [
            r'analyze_.*\.py$',
            r'analysis/.*\.py$'
        ],
        'target_dir': 'backtesting/analysis'
    },
    'backtesting_utils': {
        'patterns': [
            r'backtesting/utils/.*\.py$',
            r'backtest_utils\.py$'
        ],
        'target_dir': 'backtesting/utils'
    },
    'backtesting_scripts': {
        'patterns': [
            r'run_.*backtest.*\.sh$',
            r'backtest.*\.sh$'
        ],
        'target_dir': 'backtesting/scripts'
    },
    'data_sources': {
        'patterns': [
            r'data/sources/.*\.py$',
            r'market_data.*\.py$',
            r'data_source.*\.py$'
        ],
        'target_dir': 'data/sources'
    },
    'data_storage': {
        'patterns': [
            r'data/storage/.*\.py$',
            r'database.*\.py$',
            r'storage.*\.py$'
        ],
        'target_dir': 'data/storage'
    },
    'data_preprocessing': {
        'patterns': [
            r'data/preprocessing/.*\.py$',
            r'preprocess.*\.py$'
        ],
        'target_dir': 'data/preprocessing'
    },
    'agents_technical': {
        'patterns': [
            r'technical_.*\.py$',
            r'agents/technical/.*\.py$'
        ],
        'target_dir': 'agents/technical'
    },
    'agents_fundamental': {
        'patterns': [
            r'fundamental_.*\.py$',
            r'agents/fundamental/.*\.py$'
        ],
        'target_dir': 'agents/fundamental'
    },
    'agents_portfolio': {
        'patterns': [
            r'portfolio_.*\.py$',
            r'agents/portfolio/.*\.py$'
        ],
        'target_dir': 'agents/portfolio'
    },
    'strategies_core': {
        'patterns': [
            r'strategies/core/.*\.py$',
            r'strategy_base\.py$'
        ],
        'target_dir': 'strategies/core'
    },
    'strategies_implementations': {
        'patterns': [
            r'strategies/implementations/.*\.py$',
            r'strategy_[a-z]+\.py$'
        ],
        'target_dir': 'strategies/implementations'
    },
    'utils_logging': {
        'patterns': [
            r'utils/logging/.*\.py$',
            r'log.*utils\.py$'
        ],
        'target_dir': 'utils/logging'
    },
    'utils_config': {
        'patterns': [
            r'utils/config/.*\.py$',
            r'config.*\.py$'
        ],
        'target_dir': 'utils/config'
    },
    'utils_validation': {
        'patterns': [
            r'utils/validation/.*\.py$',
            r'validate.*\.py$'
        ],
        'target_dir': 'utils/validation'
    },
    'scripts_setup': {
        'patterns': [
            r'setup.*\.sh$',
            r'install.*\.sh$'
        ],
        'target_dir': 'scripts/setup'
    },
    'scripts_deployment': {
        'patterns': [
            r'deploy.*\.sh$',
            r'ec2.*\.sh$'
        ],
        'target_dir': 'scripts/deployment'
    },
    'docs': {
        'patterns': [
            r'docs/.*\.md$',
            r'.*\.md$'
        ],
        'target_dir': 'docs'
    },
    'tests': {
        'patterns': [
            r'tests/.*\.py$',
            r'test_.*\.py$'
        ],
        'target_dir': 'tests'
    }
}

# Special files that need specific handling
SPECIAL_FILES = {
    'decision_session.py': 'orchestration/decision_session.py',
    'market_data.py': 'data/sources/market_data.py',
    'database.py': 'data/storage/database.py',
    'run_backtest.sh': 'backtesting/scripts/run_backtest.sh',
    'analyze_backtest_results.py': 'backtesting/analysis/analyze_results.py',
    'README.md': 'README.md'
}

# Files that should be preserved at their original locations
PRESERVE_FILES = [
    '.replit',
    'package.json',
    'package-lock.json',
    'tsconfig.json',
    '.env',
    '.gitignore'
]

def load_inventory(inventory_file: str) -> Dict[str, Any]:
    """Load inventory results from JSON file"""
    try:
        with open(inventory_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading inventory file: {e}")
        sys.exit(1)

def categorize_file(file_path: str) -> str:
    """Categorize a file based on its path and patterns"""
    # Check SPECIAL_FILES first
    file_name = os.path.basename(file_path)
    if file_name in SPECIAL_FILES:
        return SPECIAL_FILES[file_name]
    
    # Check patterns
    for category, config in FILE_CATEGORIES.items():
        for pattern in config['patterns']:
            if re.search(pattern, file_path):
                return config['target_dir']
    
    # Default: keep in the same location
    return None

def should_preserve(file_path: str) -> bool:
    """Check if a file should be preserved at its original location"""
    file_name = os.path.basename(file_path)
    return file_name in PRESERVE_FILES

def prepare_target_directory(target_dir: str) -> None:
    """Ensure the target directory exists"""
    os.makedirs(target_dir, exist_ok=True)

def copy_file(source_path: str, target_path: str) -> bool:
    """Copy a file to the target path, preserving its content"""
    try:
        # Ensure target directory exists
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        return True
    except Exception as e:
        print(f"Error copying {source_path} to {target_path}: {e}")
        return False

def update_imports(target_path: str, old_path: str, mapping: Dict[str, str]) -> None:
    """Update imports in Python files to match the new structure"""
    if not target_path.endswith('.py'):
        return
    
    try:
        with open(target_path, 'r') as f:
            content = f.read()
        
        # Map of old import paths to new import paths
        import_map = {}
        
        # Build the import map based on the file mapping
        for old_file, new_file in mapping.items():
            if old_file == old_path or not old_file.endswith('.py'):
                continue
            
            # Convert file paths to import paths
            old_import = os.path.splitext(old_file)[0].replace('/', '.')
            new_import = os.path.splitext(new_file)[0].replace('/', '.')
            
            # Add to the import map
            if old_import != new_import:
                import_map[old_import] = new_import
        
        # Update imports
        updated_content = content
        for old_import, new_import in import_map.items():
            # Regular imports
            updated_content = re.sub(
                rf'import\s+{re.escape(old_import)}',
                f'import {new_import}',
                updated_content
            )
            
            # From imports
            updated_content = re.sub(
                rf'from\s+{re.escape(old_import)}\s+import',
                f'from {new_import} import',
                updated_content
            )
        
        # Only write if changes were made
        if updated_content != content:
            with open(target_path, 'w') as f:
                f.write(updated_content)
    except Exception as e:
        print(f"Error updating imports in {target_path}: {e}")

def reorganize_codebase(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """Reorganize the codebase based on inventory results"""
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'moved_files': [],
        'preserved_files': [],
        'skipped_files': [],
        'errors': []
    }
    
    # Mapping of old to new paths (for import updates)
    file_mapping = {}
    
    # Process all categories
    for category in inventory['categories'].values():
        for file_info in category:
            file_path = file_info['path']
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
            
            # Skip already processed files
            if file_path in file_mapping:
                continue
            
            # Check if file should be preserved
            if should_preserve(file_path):
                result['preserved_files'].append(file_path)
                continue
            
            # Categorize the file
            target_path = categorize_file(file_path)
            
            # Skip if no target path
            if not target_path:
                result['skipped_files'].append(file_path)
                continue
            
            # If target is a directory, keep the filename
            if os.path.exists(target_path) and os.path.isdir(target_path):
                target_path = os.path.join(target_path, os.path.basename(file_path))
            
            # Copy the file
            success = copy_file(file_path, target_path)
            
            if success:
                result['moved_files'].append({
                    'source': file_path,
                    'target': target_path
                })
                file_mapping[file_path] = target_path
            else:
                result['errors'].append({
                    'file': file_path,
                    'error': f"Failed to copy to {target_path}"
                })
    
    # Update imports in copied files
    for move_info in result['moved_files']:
        update_imports(move_info['target'], move_info['source'], file_mapping)
    
    return result

def print_summary(result: Dict[str, Any]) -> None:
    """Print a summary of the reorganization"""
    print(f"\n{'=' * 80}")
    print(f"CODEBASE REORGANIZATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Timestamp: {result['timestamp']}")
    
    print(f"\nMoved files: {len(result['moved_files'])}")
    for i, move_info in enumerate(result['moved_files'][:10], 1):
        print(f"  {i}. {move_info['source']} -> {move_info['target']}")
    if len(result['moved_files']) > 10:
        print(f"  ... and {len(result['moved_files']) - 10} more")
    
    print(f"\nPreserved files: {len(result['preserved_files'])}")
    for i, file_path in enumerate(result['preserved_files'][:5], 1):
        print(f"  {i}. {file_path}")
    if len(result['preserved_files']) > 5:
        print(f"  ... and {len(result['preserved_files']) - 5} more")
    
    print(f"\nSkipped files: {len(result['skipped_files'])}")
    for i, file_path in enumerate(result['skipped_files'][:5], 1):
        print(f"  {i}. {file_path}")
    if len(result['skipped_files']) > 5:
        print(f"  ... and {len(result['skipped_files']) - 5} more")
    
    print(f"\nErrors: {len(result['errors'])}")
    for i, error_info in enumerate(result['errors'], 1):
        print(f"  {i}. {error_info['file']}: {error_info['error']}")
    
    print(f"\n{'=' * 80}")
    print("Full results saved to 'reorganization_results.json'")
    print(f"{'=' * 80}")

def save_results(result: Dict[str, Any], output_file: str) -> None:
    """Save reorganization results to a JSON file"""
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

def main() -> None:
    """Main function"""
    print(f"{'=' * 80}")
    print("CODEBASE REORGANIZATION")
    print(f"{'=' * 80}")
    
    # Check if inventory file exists
    inventory_file = 'inventory_results.json'
    if not os.path.exists(inventory_file):
        print(f"Error: Inventory file '{inventory_file}' not found.")
        print("Run 'inventory_codebase.py' first to generate the inventory.")
        sys.exit(1)
    
    print(f"Loading inventory from: {inventory_file}")
    inventory = load_inventory(inventory_file)
    
    print("Reorganizing codebase...")
    print("This may take a few moments...")
    
    # Reorganize the codebase
    result = reorganize_codebase(inventory)
    
    # Save results
    save_results(result, 'reorganization_results.json')
    
    # Print summary
    print_summary(result)

if __name__ == "__main__":
    main()