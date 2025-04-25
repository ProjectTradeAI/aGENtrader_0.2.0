#!/usr/bin/env python3
"""
Apply Data Integrity Measures to Trading System

This script applies data integrity measures to the trading system, ensuring
that analyst agents explicitly state when they don't have access to real data
instead of providing simulated responses.

Usage:
  python apply_data_integrity.py [--import-path MODULE_PATH] [--apply]
  
Options:
  --import-path  Optional import path to the trading system (e.g., "orchestration.decision_session")
  --apply        Apply immediately rather than just showing instructions
"""

import os
import sys
import json
import logging
import importlib
import argparse
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("apply_data_integrity")

# Import the data integrity module
try:
    from agents.data_integrity import ensure_data_integrity_for_agents
    DATA_INTEGRITY_AVAILABLE = True
    logger.info("Successfully imported data integrity module")
except ImportError as e:
    logger.error(f"Could not import data integrity module: {str(e)}")
    DATA_INTEGRITY_AVAILABLE = False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Apply data integrity measures to trading system")
    parser.add_argument("--import-path", type=str, help="Import path to the trading system module")
    parser.add_argument("--apply", action="store_true", help="Apply data integrity measures immediately")
    return parser.parse_args()

def import_module_safe(module_path: str) -> Optional[Any]:
    """
    Safely import a module without raising exceptions
    
    Args:
        module_path: Path to the module to import
        
    Returns:
        Module or None if import failed
    """
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        logger.warning(f"Could not import {module_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error importing {module_path}: {str(e)}")
        return None

def find_trading_system_class(module) -> Optional[str]:
    """
    Find a trading system class in a module
    
    Args:
        module: Module to search
        
    Returns:
        Class name or None if not found
    """
    if not module:
        return None
        
    for class_name in dir(module):
        if any(keyword in class_name.lower() for keyword in 
               ["decision", "trading", "system", "framework", "session"]):
            return class_name
    
    return None

def find_and_apply(import_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Find and apply data integrity measures to a trading system
    
    Args:
        import_path: Import path to the trading system module
        
    Returns:
        Dictionary with results
    """
    if not DATA_INTEGRITY_AVAILABLE:
        return {
            "success": False,
            "error": "Data integrity module not available"
        }
    
    # If import path is provided, try to import and apply
    if import_path:
        module = import_module_safe(import_path)
        if not module:
            return {
                "success": False,
                "error": f"Could not import module: {import_path}"
            }
        
        # Find a trading system class
        class_name = find_trading_system_class(module)
        if not class_name:
            return {
                "success": False,
                "error": f"Could not find trading system class in module: {import_path}"
            }
        
        # Try to instantiate the class
        try:
            class_obj = getattr(module, class_name)
            instance = class_obj()
            
            # Apply data integrity measures
            results = ensure_data_integrity_for_agents(instance)
            
            return {
                "success": True,
                "module": import_path,
                "class": class_name,
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error instantiating {class_name}: {str(e)}"
            }
    
    # If no import path is provided, check common locations
    common_paths = [
        "orchestration.decision_session",
        "orchestration.decision_session_fixed",
        "orchestration.decision_session_new",
        "orchestration.decision_session_updated",
        "agents.trading_agent_framework",
        "agents.collaborative_trading_framework",
        "agents.structured_decision_agent"
    ]
    
    results = {}
    for path in common_paths:
        module = import_module_safe(path)
        if module:
            class_name = find_trading_system_class(module)
            if class_name:
                results[f"{path}.{class_name}"] = {
                    "module": path,
                    "class": class_name,
                    "importable": True
                }
    
    return {
        "success": True,
        "found_modules": results
    }

def show_instructions():
    """Show instructions for applying data integrity measures"""
    print("\nTo apply data integrity measures to your trading system:")
    print("\n1. Direct application in your code:")
    print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Your trading system instance
trading_system = YourTradingSystem()

# Apply data integrity measures
results = ensure_data_integrity_for_agents(trading_system)

# Check results
if results["success"]:
    print("Successfully applied data integrity measures")
else:
    print(f"Failed to apply data integrity measures: {results.get('error')}")
""")
    
    print("\n2. Monkey patching during initialization:")
    print("""
from agents.data_integrity import ensure_data_integrity_for_agents

# Store the original __init__ method
original_init = YourTradingSystem.__init__

# Define the patched __init__ method
def patched_init(self, *args, **kwargs):
    # Call the original __init__ method
    original_init(self, *args, **kwargs)
    
    # Apply data integrity measures
    ensure_data_integrity_for_agents(self)

# Apply the monkey patch
YourTradingSystem.__init__ = patched_init
""")
    
    print("\n3. Using this script:")
    print("""
# Apply to a specific module
python apply_data_integrity.py --import-path orchestration.decision_session --apply

# Check available modules
python apply_data_integrity.py
""")

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print("Data Integrity Application for Trading System")
    print("============================================")
    
    if not DATA_INTEGRITY_AVAILABLE:
        print("\nERROR: Data integrity module is not available")
        print("Make sure agents/data_integrity.py exists and is properly implemented")
        return
    
    # If apply flag is set and import path is provided, apply immediately
    if args.apply and args.import_path:
        print(f"\nApplying data integrity measures to: {args.import_path}")
        results = find_and_apply(args.import_path)
        
        if results["success"]:
            print("✅ Successfully applied data integrity measures")
            print(f"  Module: {results['module']}")
            print(f"  Class: {results['class']}")
            
            # Print agent-specific results
            if "results" in results:
                agent_results = results["results"]
                for agent_type, status in agent_results.items():
                    if agent_type != "success":
                        print(f"  - {agent_type}: {'Applied' if status is True else status}")
        else:
            print("❌ Failed to apply data integrity measures")
            print(f"  Error: {results.get('error', 'Unknown error')}")
    
    # Otherwise, find available modules
    else:
        print("\nChecking for available trading system modules...")
        results = find_and_apply()
        
        if results["success"] and "found_modules" in results:
            modules = results["found_modules"]
            if modules:
                print(f"Found {len(modules)} potential trading system modules:")
                for module_class, info in modules.items():
                    print(f"  - {module_class}")
                
                print("\nTo apply data integrity measures to a specific module:")
                print(f"  python apply_data_integrity.py --import-path {list(modules.keys())[0].split('.')[0]} --apply")
            else:
                print("No trading system modules found in common locations")
        else:
            print("❌ Failed to check for available modules")
            print(f"  Error: {results.get('error', 'Unknown error')}")
    
    # Show instructions
    show_instructions()

if __name__ == "__main__":
    main()