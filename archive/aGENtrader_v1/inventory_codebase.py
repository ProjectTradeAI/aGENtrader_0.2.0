#!/usr/bin/env python3
"""
Codebase Inventory Script

This script analyzes the project structure, categorizes files,
and helps identify redundant or unused files.
"""
import os
import re
import sys
import json
import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

# Configuration
IGNORED_DIRS = [
    '.git', 'node_modules', '__pycache__', 
    '.vscode', '.idea', 'venv', 'env',
    'attached_assets', 'chunk_a'
]
IGNORED_FILES = [
    '.DS_Store', '.gitignore', 'Thumbs.db',
    'inventory_results.json', 'inventory_codebase.py'
]
IGNORED_EXTENSIONS = [
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.class',
    '.log', '.bak', '.swp', '.swo', '.tmp', '.temp'
]

# File categories
CATEGORIES = {
    'CORE': [
        'decision_session.py',
        'market_data.py',
        'agent_framework.py',
        'schema.ts',
        'storage.ts',
        'config.py',
        'environment.py'
    ],
    'ORCHESTRATION': [
        r'orchestration/.*\.py$',
        r'agents/.*\.py$'
    ],
    'BACKTESTING': [
        r'backtest.*\.py$',
        r'backtesting/.*\.py$'
    ],
    'DEPLOYMENT': [
        r'deploy.*\.sh$',
        r'ec2.*\.sh$'
    ],
    'DATA': [
        r'data/.*\.py$',
        r'market_data.*\.py$',
        r'database.*\.py$'
    ],
    'SCRIPTS': [
        r'\.sh$',
        r'run_.*\.py$'
    ],
    'DOCUMENTATION': [
        r'\.md$',
        r'docs/.*\.md$',
        r'README.*'
    ],
    'TESTS': [
        r'test_.*\.py$',
        r'tests/.*\.py$',
        r'check_.*\.py$'
    ],
    'CONFIGURATION': [
        r'\.env$',
        r'config\..*$',
        r'settings\..*$',
        r'.*\.json$'
    ],
    'UNUSED': []  # Will be determined during analysis
}

def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def get_modification_time(file_path: str) -> float:
    """Get the last modification time of a file"""
    try:
        return os.path.getmtime(file_path)
    except:
        return 0

def format_timestamp(timestamp: float) -> str:
    """Format a timestamp as a readable string"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def get_file_category(file_path: str) -> str:
    """Determine the category of a file based on its path and name"""
    file_name = os.path.basename(file_path)
    
    # Check for exact matches in CORE
    if file_name in CATEGORIES['CORE']:
        return 'CORE'
    
    # Check for pattern matches in other categories
    for category, patterns in CATEGORIES.items():
        if category == 'CORE' or category == 'UNUSED':
            continue
        
        for pattern in patterns:
            if re.search(pattern, file_path):
                return category
    
    # Default to UNUSED
    return 'UNUSED'

def find_dependencies(file_path: str) -> Set[str]:
    """Find dependencies (imports, requires) in a file"""
    dependencies = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Python imports
            if file_path.endswith('.py'):
                # Regular imports
                for match in re.finditer(r'import\s+([a-zA-Z0-9_.,\s]+)', content):
                    for name in match.group(1).split(','):
                        name = name.strip().split('.')[0].split(' as ')[0]
                        if name:
                            dependencies.add(name)
                
                # From imports
                for match in re.finditer(r'from\s+([a-zA-Z0-9_.]+)\s+import', content):
                    name = match.group(1).split('.')[0]
                    if name:
                        dependencies.add(name)
            
            # JavaScript/TypeScript requires
            elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                # import statements
                for match in re.finditer(r'import\s+.*from\s+[\'"]([^\'"]*)[\'"]\s*;?', content):
                    dependencies.add(match.group(1))
                
                # require statements
                for match in re.finditer(r'require\s*\(\s*[\'"]([^\'"]*)[\'"]\s*\)', content):
                    dependencies.add(match.group(1))
            
            # Shell script sources
            elif file_path.endswith('.sh'):
                for match in re.finditer(r'source\s+([^\s;]+)', content):
                    dependencies.add(match.group(1))
        
        return dependencies
    except:
        return set()

def detect_similar_files(files: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Detect groups of similar files based on name patterns"""
    # Group files by name patterns
    pattern_groups = defaultdict(list)
    
    for file in files:
        name = os.path.basename(file['path'])
        
        # Extract base name without numbers and extensions
        base_name = re.sub(r'[0-9]+', '', name.split('.')[0])
        pattern_groups[base_name].append(file)
    
    # Filter groups with more than one file
    similar_groups = [group for group in pattern_groups.values() if len(group) > 1]
    
    # Sort groups by number of files
    similar_groups.sort(key=len, reverse=True)
    
    return similar_groups

def inventory_codebase(root_dir: str) -> Dict[str, Any]:
    """Analyze the codebase structure and categorize files"""
    start_time = time.time()
    
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'root_directory': os.path.abspath(root_dir),
        'categories': {},
        'statistics': {
            'total_files': 0,
            'total_size': 0,
            'by_extension': {},
            'by_category': {}
        },
        'similar_files': [],
    }
    
    all_files = []
    
    # Walk through the directory structure
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        
        for filename in filenames:
            # Skip ignored files
            if filename in IGNORED_FILES:
                continue
                
            # Skip ignored extensions
            ext = os.path.splitext(filename)[1]
            if ext in IGNORED_EXTENSIONS:
                continue
            
            # Get full file path
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root_dir)
            
            # Get file info
            size = get_file_size(file_path)
            mod_time = get_modification_time(file_path)
            category = get_file_category(rel_path)
            dependencies = find_dependencies(file_path)
            
            # Compile file info
            file_info = {
                'path': rel_path,
                'size': size,
                'last_modified': format_timestamp(mod_time),
                'last_modified_timestamp': mod_time,
                'category': category,
                'dependencies': list(dependencies)
            }
            
            all_files.append(file_info)
            
            # Update statistics
            result['statistics']['total_files'] += 1
            result['statistics']['total_size'] += size
            
            # Update extension statistics
            ext = os.path.splitext(filename)[1] or 'no_extension'
            if ext not in result['statistics']['by_extension']:
                result['statistics']['by_extension'][ext] = {
                    'count': 0,
                    'size': 0
                }
            result['statistics']['by_extension'][ext]['count'] += 1
            result['statistics']['by_extension'][ext]['size'] += size
            
            # Update category statistics
            if category not in result['statistics']['by_category']:
                result['statistics']['by_category'][category] = {
                    'count': 0,
                    'size': 0
                }
            result['statistics']['by_category'][category]['count'] += 1
            result['statistics']['by_category'][category]['size'] += size
    
    # Group files by category
    for category in CATEGORIES.keys():
        result['categories'][category] = [
            file for file in all_files if file['category'] == category
        ]
    
    # Find similar files
    result['similar_files'] = detect_similar_files(all_files)
    
    # Compute redundancy metrics
    result['redundancy_metrics'] = {
        'similar_file_groups': len(result['similar_files']),
        'total_similar_files': sum(len(group) for group in result['similar_files']),
        'largest_similar_group': max([len(group) for group in result['similar_files']]) if result['similar_files'] else 0
    }
    
    # Sort files by modification time (newest first)
    for category in result['categories']:
        result['categories'][category].sort(key=lambda x: x['last_modified_timestamp'], reverse=True)
    
    # Add timing information
    result['analysis_time'] = time.time() - start_time
    
    return result

def print_summary(result: Dict[str, Any]) -> None:
    """Print a summary of the analysis results"""
    print(f"\n{'=' * 80}")
    print(f"CODEBASE INVENTORY SUMMARY")
    print(f"{'=' * 80}")
    print(f"Root directory: {result['root_directory']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Analysis time: {result['analysis_time']:.2f} seconds\n")
    
    print(f"Total files: {result['statistics']['total_files']}")
    print(f"Total size: {result['statistics']['total_size'] / 1024:.2f} KB\n")
    
    print("Files by category:")
    for category, stats in result['statistics']['by_category'].items():
        print(f"  {category}: {stats['count']} files ({stats['size'] / 1024:.2f} KB)")
    
    print("\nTop 5 extensions:")
    sorted_extensions = sorted(
        result['statistics']['by_extension'].items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    for ext, stats in sorted_extensions[:5]:
        print(f"  {ext}: {stats['count']} files ({stats['size'] / 1024:.2f} KB)")
    
    print("\nRedundancy metrics:")
    print(f"  Similar file groups: {result['redundancy_metrics']['similar_file_groups']}")
    print(f"  Total similar files: {result['redundancy_metrics']['total_similar_files']}")
    print(f"  Largest similar group: {result['redundancy_metrics']['largest_similar_group']} files")
    
    print("\nTop 5 similar file groups:")
    for i, group in enumerate(result['similar_files'][:5], 1):
        base_name = os.path.basename(group[0]['path'])
        base_name = re.sub(r'[0-9]+', '', base_name.split('.')[0])
        print(f"  Group {i} ({base_name}*): {len(group)} files")
        for file in group[:3]:  # Show first 3 files in group
            print(f"    - {file['path']}")
        if len(group) > 3:
            print(f"    - ... and {len(group) - 3} more")
    
    print(f"\n{'=' * 80}")
    print("Full results saved to 'inventory_results.json'")
    print(f"{'=' * 80}")

def save_results(result: Dict[str, Any], output_file: str) -> None:
    """Save analysis results to a JSON file"""
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

def main() -> None:
    """Main function"""
    print(f"{'=' * 80}")
    print("CODEBASE INVENTORY")
    print(f"{'=' * 80}")
    
    # Get root directory
    root_dir = '.'  # Default to current directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    
    print(f"Analyzing codebase in: {os.path.abspath(root_dir)}")
    print("This may take a few moments...")
    
    # Run the analysis
    result = inventory_codebase(root_dir)
    
    # Save results
    save_results(result, 'inventory_results.json')
    
    # Print summary
    print_summary(result)

if __name__ == "__main__":
    main()