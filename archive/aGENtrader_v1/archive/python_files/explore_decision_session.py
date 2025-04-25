#!/usr/bin/env python3
"""
Explore Decision Session Structure

This script explores the structure of the DecisionSession class to
understand how agents are organized and where to apply data integrity.
"""

import os
import sys
import json
import logging
import inspect
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("explore_decision_session")

def explore_object(obj, prefix="", max_depth=3, current_depth=0):
    """Explore an object's structure recursively"""
    if current_depth > max_depth:
        return {}
    
    # Skip exploring common Python objects
    if obj.__class__.__module__ in ['builtins']:
        return {}
    
    result = {}
    
    # Get all attributes
    for attr_name in dir(obj):
        # Skip private attributes and methods
        if attr_name.startswith('_'):
            continue
        
        try:
            # Get the attribute
            attr = getattr(obj, attr_name)
            
            # Skip if it's a method
            if callable(attr):
                continue
            
            # Build the full attribute path
            full_path = f"{prefix}.{attr_name}" if prefix else attr_name
            
            # Store the attribute type
            attr_type = type(attr).__name__
            result[full_path] = attr_type
            
            # Recursively explore objects
            if attr_type in ['dict', 'list', 'tuple']:
                pass
            elif hasattr(attr, '__dict__'):
                # Recursively explore the attribute
                nested = explore_object(attr, full_path, max_depth, current_depth + 1)
                result.update(nested)
        except:
            # Ignore errors when accessing attributes
            continue
    
    return result

def explore_decision_session():
    """Explore DecisionSession structure"""
    try:
        # Import the decision_session module
        from orchestration import decision_session
        logger.info("Successfully imported decision_session module")
        
        # Check if DecisionSession exists
        if not hasattr(decision_session, "DecisionSession"):
            logger.error("DecisionSession class not found in decision_session module")
            return {
                "success": False,
                "error": "DecisionSession class not found"
            }
        
        # Initialize a DecisionSession instance
        session = decision_session.DecisionSession()
        logger.info("Successfully initialized DecisionSession instance")
        
        # Explore the session object
        structure = explore_object(session)
        
        # Get methods that might create agents
        methods = {}
        for name, method in inspect.getmembers(session.__class__, predicate=inspect.isfunction):
            if 'agent' in name.lower() or 'create' in name.lower() or 'init' in name.lower():
                try:
                    methods[name] = inspect.getdoc(method) or "No docstring"
                except:
                    methods[name] = "Error getting docstring"
        
        # Check for methods that run a decision session
        for name, method in inspect.getmembers(session.__class__, predicate=inspect.isfunction):
            if 'run' in name.lower() or 'start' in name.lower() or 'decision' in name.lower():
                try:
                    if name not in methods:
                        methods[name] = inspect.getdoc(method) or "No docstring"
                except:
                    if name not in methods:
                        methods[name] = "Error getting docstring"
        
        # Look for where agents might be stored
        agent_locations = {}
        for path, type_name in structure.items():
            if 'agent' in path.lower():
                agent_locations[path] = type_name
            elif 'analyst' in path.lower():
                agent_locations[path] = type_name
        
        # Get information about run_decision method if it exists
        run_info = None
        if hasattr(session, "run_decision"):
            try:
                source = inspect.getsource(session.run_decision)
                run_info = {
                    "source_preview": source[:500] + "..." if len(source) > 500 else source
                }
            except:
                run_info = {
                    "error": "Could not get source code"
                }
        
        return {
            "success": True,
            "structure": structure,
            "methods": methods,
            "agent_locations": agent_locations,
            "run_info": run_info
        }
    except Exception as e:
        logger.error(f"Error exploring DecisionSession: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point"""
    print("Exploring DecisionSession Structure")
    print("=================================")
    
    # Explore DecisionSession
    result = explore_decision_session()
    
    if result["success"]:
        print("\n✅ Successfully explored DecisionSession structure")
        
        # Print agent-related methods
        print("\nMethods that might create or use agents:")
        for name, docstring in result["methods"].items():
            print(f"  - {name}: {docstring[:100]}..." if len(docstring) > 100 else f"  - {name}: {docstring}")
        
        # Print potential agent locations
        print("\nPotential locations where agents might be stored:")
        for path, type_name in result["agent_locations"].items():
            print(f"  - {path} ({type_name})")
        
        # Print run_decision info
        if result.get("run_info"):
            print("\nInformation about run_decision method:")
            for key, value in result["run_info"].items():
                print(f"  - {key}: {value[:200]}..." if isinstance(value, str) and len(value) > 200 else f"  - {key}: {value}")
        
        print("\nBased on this exploration, we can modify our data integrity implementation to:")
        print("1. Apply data integrity during the run_decision method rather than initialization")
        print("2. Target the specific locations where analyst agents are created/stored")
    else:
        print("\n❌ Failed to explore DecisionSession structure")
        print(f"  Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()