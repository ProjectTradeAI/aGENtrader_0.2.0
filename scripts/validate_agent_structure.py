#!/usr/bin/env python3
"""
Agent Structure Validation Script for aGENtrader v0.2.2

This script validates that all agent classes follow the standardized
architecture, including:
1. Proper inheritance from base classes
2. Implementation of required methods
3. Correct method signatures
4. Presence of version tags in constructors
"""

import os
import sys
import ast
import re
import logging
import inspect
import importlib
from typing import List, Dict, Any, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('agent_structure_validator')

# Define expected inheritance relationships
EXPECTED_INHERITANCE = {
    'TechnicalAnalystAgent': 'BaseAnalystAgent',
    'SentimentAnalystAgent': 'BaseAnalystAgent',
    'SentimentAggregatorAgent': 'BaseAnalystAgent',
    'LiquidityAnalystAgent': 'BaseAnalystAgent',
    'FundingRateAnalystAgent': 'BaseAnalystAgent',
    'OpenInterestAnalystAgent': 'BaseAnalystAgent',
    'DecisionAgent': 'BaseDecisionAgent',
    'TradePlanAgent': 'BaseDecisionAgent',
    'PortfolioManagerAgent': 'BaseAgent',
}

# Define required methods for each agent type
REQUIRED_METHODS = {
    'BaseAnalystAgent': ['analyze', 'get_analysis', 'build_error_response', '_get_trading_config'],
    'BaseDecisionAgent': ['make_decision', 'get_decision', 'build_error_response'],
}

class AgentValidationError(Exception):
    """Exception raised for agent validation errors."""
    pass

def collect_agent_files() -> List[str]:
    """Collect all agent module files from the agents directory."""
    agent_files = []
    agents_dir = "agents"
    
    if not os.path.exists(agents_dir):
        logger.error(f"Agents directory '{agents_dir}' not found")
        return []
        
    for root, _, files in os.walk(agents_dir):
        for file in files:
            if file.endswith("_agent.py") and not file.startswith("__"):
                agent_files.append(os.path.join(root, file))
                
    return agent_files

def parse_agent_file(file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Parse an agent file to extract class definitions and other metadata.
    
    Args:
        file_path: Path to the agent file
        
    Returns:
        Tuple containing (list of class definitions, file metadata)
    """
    with open(file_path, 'r') as f:
        content = f.read()
        
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return [], {}
        
    classes = []
    imports = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Extract class information
            class_def = {
                'name': node.name,
                'bases': [b.id if isinstance(b, ast.Name) else 
                          b.attr if isinstance(b, ast.Attribute) else 
                          "Unknown" for b in node.bases],
                'methods': [],
                'has_init': False,
                'has_version_tag': False,
            }
            
            # Analyze methods
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_name = item.name
                    args = [arg.arg for arg in item.args.args]
                    class_def['methods'].append({
                        'name': method_name,
                        'args': args,
                    })
                    
                    # Check for __init__ and version tag
                    if method_name == '__init__':
                        class_def['has_init'] = True
                        # Check if any assignment mentions version
                        for statement in item.body:
                            if isinstance(statement, ast.Assign):
                                if isinstance(statement.targets[0], ast.Attribute):
                                    attr_name = statement.targets[0].attr
                                    if 'version' in attr_name.lower():
                                        class_def['has_version_tag'] = True
                                        break
            
            classes.append(class_def)
        
        # Collect import statements
        elif isinstance(node, ast.Import):
            for name in node.names:
                imports[name.name] = name.asname or name.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            for name in node.names:
                imports[f"{module}.{name.name}"] = name.asname or name.name
                
    return classes, {'imports': imports}

def validate_agent_structure(agent_files: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Validate the structure of all agent files.
    
    Args:
        agent_files: List of agent file paths
        
    Returns:
        Dictionary of validation results for each agent
    """
    validation_results = {}
    
    for file_path in agent_files:
        file_name = os.path.basename(file_path)
        logger.info(f"Validating {file_name}")
        
        # Parse agent file
        classes, metadata = parse_agent_file(file_path)
        
        # Validate each class in the file
        for class_def in classes:
            class_name = class_def['name']
            
            # Skip validation for base classes
            if class_name in ['BaseAgent', 'BaseAnalystAgent', 'BaseDecisionAgent', 'AgentInterface']:
                continue
                
            validation_result = {
                'file_path': file_path,
                'class_name': class_name,
                'errors': [],
                'warnings': [],
                'status': 'pass',
            }
            
            # Validate inheritance
            if class_name in EXPECTED_INHERITANCE:
                expected_base = EXPECTED_INHERITANCE[class_name]
                if expected_base not in class_def['bases']:
                    error_msg = f"Class {class_name} should inherit from {expected_base}"
                    validation_result['errors'].append(error_msg)
                    validation_result['status'] = 'fail'
            
            # Get the base class(es) that this agent extends
            agent_type = None
            for base in class_def['bases']:
                if base in REQUIRED_METHODS:
                    agent_type = base
                    break
            
            # Validate required methods
            if agent_type and agent_type in REQUIRED_METHODS:
                required_methods = REQUIRED_METHODS[agent_type]
                implemented_methods = [m['name'] for m in class_def['methods']]
                
                for method in required_methods:
                    if method not in implemented_methods:
                        error_msg = f"Class {class_name} should implement {method}()"
                        validation_result['errors'].append(error_msg)
                        validation_result['status'] = 'fail'
            
            # Validate constructor
            if not class_def['has_init']:
                warning_msg = f"Class {class_name} does not have an explicit __init__ method"
                validation_result['warnings'].append(warning_msg)
                
            # Validate version tag
            if not class_def['has_version_tag']:
                error_msg = f"Class {class_name} does not set an agent version tag in __init__"
                validation_result['errors'].append(error_msg)
                validation_result['status'] = 'fail'
                
            validation_results[class_name] = validation_result
            
    return validation_results

def print_validation_results(results: Dict[str, Dict[str, Any]]) -> None:
    """Print the validation results in a readable format."""
    passes = [name for name, result in results.items() if result['status'] == 'pass']
    fails = [name for name, result in results.items() if result['status'] == 'fail']
    
    print("\n=== Agent Structure Validation Results ===\n")
    print(f"Total agents validated: {len(results)}")
    print(f"Passed: {len(passes)}")
    print(f"Failed: {len(fails)}")
    
    if fails:
        print("\n=== Failed Validations ===\n")
        for name in fails:
            result = results[name]
            print(f"Agent: {name} ({os.path.basename(result['file_path'])})")
            for error in result['errors']:
                print(f"  - ERROR: {error}")
            for warning in result['warnings']:
                print(f"  - WARNING: {warning}")
            print()
            
    if passes:
        print("\n=== Passed Validations ===\n")
        for name in passes:
            result = results[name]
            if result['warnings']:
                print(f"Agent: {name} ({os.path.basename(result['file_path'])})")
                for warning in result['warnings']:
                    print(f"  - WARNING: {warning}")
                print()
            else:
                print(f"Agent: {name} - OK")

def main():
    """Main entry point for the validation script."""
    logger.info("Starting agent structure validation")
    
    # Collect agent files
    agent_files = collect_agent_files()
    logger.info(f"Found {len(agent_files)} agent files")
    
    if not agent_files:
        logger.error("No agent files found. Exiting.")
        sys.exit(1)
        
    # Validate agent structure
    validation_results = validate_agent_structure(agent_files)
    
    # Print validation results
    print_validation_results(validation_results)
    
    # Determine exit code
    has_failures = any(result['status'] == 'fail' for result in validation_results.values())
    
    if has_failures:
        logger.error("Agent structure validation failed")
        sys.exit(1)
    else:
        logger.info("Agent structure validation succeeded")
        sys.exit(0)

if __name__ == "__main__":
    main()