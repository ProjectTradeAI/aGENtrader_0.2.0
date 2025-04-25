#!/usr/bin/env python3
"""
Debug Decision Session Script

This script diagnoses why the decision session is using a simplified framework
instead of the full agent framework.
"""
import os
import sys
import inspect
import logging
import importlib
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'debug_decision_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("debug_decision_session")

def inspect_module_path(module_name: str) -> Dict[str, Any]:
    """Inspect a module's path and existence"""
    logger.info(f"Inspecting module path: {module_name}")
    
    try:
        # Try to find the module without importing
        spec = importlib.util.find_spec(module_name)
        
        if spec is None:
            logger.warning(f"Module {module_name} does not exist in sys.path")
            return {"exists": False, "error": "Module not found"}
        
        logger.info(f"Module {module_name} found at: {spec.origin}")
        
        # Try to import it
        module = importlib.import_module(module_name)
        
        # Check module attributes
        attributes = dir(module)
        
        return {
            "exists": True,
            "path": spec.origin,
            "attributes": attributes,
            "file": getattr(module, "__file__", "Unknown")
        }
    
    except ImportError as e:
        logger.error(f"Failed to import module {module_name}: {e}")
        return {"exists": False, "error": f"Import error: {e}"}
    except Exception as e:
        logger.error(f"Error inspecting module {module_name}: {e}")
        return {"exists": False, "error": str(e)}

def print_sys_path():
    """Print sys.path to debug import issues"""
    logger.info("Current sys.path:")
    for i, path in enumerate(sys.path):
        logger.info(f"  {i}: {path}")

def check_class_implementation(module_name: str, class_name: str) -> Dict[str, Any]:
    """Check a class implementation for issues"""
    logger.info(f"Checking implementation of {module_name}.{class_name}")
    
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Check if the class exists
        if not hasattr(module, class_name):
            logger.error(f"Class {class_name} not found in module {module_name}")
            return {"exists": False, "error": "Class not found"}
        
        # Get the class
        cls = getattr(module, class_name)
        
        # Get methods
        methods = {}
        simplifications = []
        
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('__'):
                try:
                    source = inspect.getsource(method)
                    # Check if the method contains signs of simplification
                    if "simplif" in source.lower():
                        simplifications.append({
                            "method": name,
                            "evidence": source
                        })
                    
                    methods[name] = {
                        "signature": str(inspect.signature(method)),
                        "doc": inspect.getdoc(method),
                        "source_snippet": source[:200] + "..." if len(source) > 200 else source
                    }
                except Exception as e:
                    methods[name] = {
                        "signature": str(inspect.signature(method)),
                        "doc": inspect.getdoc(method),
                        "source_error": str(e)
                    }
        
        # Check for dependencies
        dependencies = []
        
        if hasattr(cls, 'run_session'):
            method = getattr(cls, 'run_session')
            source = inspect.getsource(method)
            
            # Check common dependencies
            deps = {
                "autogen": "autogen" in source,
                "openai": "openai" in source,
                "langchain": "langchain" in source,
                "flaml": "flaml" in source,
                "llamaindex": "llamaindex" in source or "llama_index" in source
            }
            
            # Add dependencies found in the source
            for dep, found in deps.items():
                if found:
                    dependencies.append(dep)
        
        # Check if initialization requires any special parameters
        init_params = []
        if hasattr(cls, '__init__'):
            init_signature = inspect.signature(cls.__init__)
            for param_name, param in init_signature.parameters.items():
                if param_name != 'self':
                    init_params.append({
                        "name": param_name,
                        "default": str(param.default) if param.default is not inspect.Parameter.empty else None,
                        "required": param.default is inspect.Parameter.empty
                    })
        
        return {
            "exists": True,
            "methods": methods,
            "simplifications": simplifications,
            "dependencies": dependencies,
            "init_params": init_params
        }
    
    except ImportError as e:
        logger.error(f"Failed to import module {module_name}: {e}")
        return {"exists": False, "error": f"Import error: {e}"}
    except Exception as e:
        logger.error(f"Error checking class implementation: {e}")
        logger.error(traceback.format_exc())
        return {"exists": False, "error": str(e)}

def check_dependencies():
    """Check for required dependencies"""
    logger.info("Checking dependencies...")
    
    dependencies = [
        "autogen",
        "flaml",
        "openai",
        "langchain",
        "psycopg2"
    ]
    
    results = {}
    
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            version = getattr(module, "__version__", "Unknown")
            results[dep] = {"installed": True, "version": version}
            logger.info(f"✅ {dep} is installed (version: {version})")
        except ImportError:
            results[dep] = {"installed": False}
            logger.warning(f"❌ {dep} is not installed")
    
    return results

def check_environment_variables():
    """Check for required environment variables"""
    logger.info("Checking environment variables...")
    
    variables = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "ALPACA_API_KEY",
        "ALPACA_API_SECRET"
    ]
    
    results = {}
    
    for var in variables:
        value = os.environ.get(var)
        if value:
            masked_value = value[:3] + "..." + value[-3:] if len(value) > 10 else "***"
            results[var] = {"exists": True, "value": masked_value}
            logger.info(f"✅ {var} is set")
        else:
            results[var] = {"exists": False}
            logger.warning(f"❌ {var} is not set")
    
    return results

def debug_decision_session():
    """Debug the DecisionSession class to understand why it's using simplified framework"""
    logger.info("Debugging DecisionSession class...")
    
    # Print sys.path
    print_sys_path()
    
    # Check orchestration module path
    orchestration_info = inspect_module_path("orchestration")
    if not orchestration_info.get("exists", False):
        # Try to find orchestration directory manually
        logger.info("Trying to find orchestration directory manually...")
        for path in sys.path:
            orchestration_dir = os.path.join(path, "orchestration")
            if os.path.isdir(orchestration_dir):
                logger.info(f"Found orchestration directory at: {orchestration_dir}")
                # Add to sys.path
                if orchestration_dir not in sys.path:
                    sys.path.append(orchestration_dir)
                    logger.info(f"Added {orchestration_dir} to sys.path")
                    # Try again
                    orchestration_info = inspect_module_path("orchestration")
    
    # Check decision_session module path
    decision_session_info = inspect_module_path("orchestration.decision_session")
    
    # Check DecisionSession class implementation
    decision_session_class_info = check_class_implementation("orchestration.decision_session", "DecisionSession")
    
    # Check dependencies
    dependency_info = check_dependencies()
    
    # Check environment variables
    env_var_info = check_environment_variables()
    
    # Compile results
    results = {
        "orchestration_module": orchestration_info,
        "decision_session_module": decision_session_info,
        "decision_session_class": decision_session_class_info,
        "dependencies": dependency_info,
        "environment_variables": env_var_info
    }
    
    # Look for "simplified agent framework" text in the implementation
    simplifications = decision_session_class_info.get("simplifications", [])
    
    if simplifications:
        logger.warning(f"Found {len(simplifications)} methods with signs of simplification:")
        for simple in simplifications:
            method = simple["method"]
            evidence = simple["evidence"]
            logger.warning(f"Method '{method}' contains simplification:")
            logger.warning(f"Evidence: {evidence[:200]}...")
    else:
        logger.info("No explicit signs of simplification found in the code")
    
    # Check why it might be using a simplified framework
    reasons = []
    
    # Reason 1: Missing dependencies
    missing_deps = [dep for dep, info in dependency_info.items() if not info.get("installed", False)]
    if missing_deps:
        reasons.append(f"Missing dependencies: {', '.join(missing_deps)}")
    
    # Reason 2: Missing OpenAI API key
    if not env_var_info.get("OPENAI_API_KEY", {}).get("exists", False):
        reasons.append("Missing OPENAI_API_KEY environment variable")
    
    # Reason 3: Explicit simplified implementation
    if simplifications:
        reasons.append("Explicit simplified implementation in the code")
    
    # Reason 4: Missing autogen dependency
    if not dependency_info.get("autogen", {}).get("installed", False):
        reasons.append("Missing autogen dependency for multi-agent framework")
    
    if reasons:
        logger.warning("Potential reasons for using simplified framework:")
        for i, reason in enumerate(reasons, 1):
            logger.warning(f"  {i}. {reason}")
    else:
        logger.info("No obvious reasons found for using simplified framework")
    
    return results

def main():
    """Main function"""
    logger.info("Starting decision session debug")
    
    try:
        # Debug the decision session
        results = debug_decision_session()
        
        # Print summary
        print("\n===== DEBUG SUMMARY =====")
        print(f"Orchestration module exists: {results['orchestration_module'].get('exists', False)}")
        print(f"Decision session module exists: {results['decision_session_module'].get('exists', False)}")
        print(f"DecisionSession class exists: {results['decision_session_class'].get('exists', False)}")
        
        if results['decision_session_class'].get('exists', False):
            simplifications = results['decision_session_class'].get('simplifications', [])
            if simplifications:
                print(f"Found {len(simplifications)} methods with signs of simplification")
            else:
                print("No explicit signs of simplification found in the code")
            
            dependencies = results['decision_session_class'].get('dependencies', [])
            print(f"Dependencies used in class: {', '.join(dependencies) if dependencies else 'None detected'}")
        
        missing_deps = [dep for dep, info in results['dependencies'].items() if not info.get("installed", False)]
        if missing_deps:
            print(f"Missing dependencies: {', '.join(missing_deps)}")
        else:
            print("All checked dependencies are installed")
        
        missing_vars = [var for var, info in results['environment_variables'].items() if not info.get("exists", False)]
        if missing_vars:
            print(f"Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("All checked environment variables are set")
        
        print("=======================")
        
        # Attempt to create a test instance
        print("\nAttempting to create test DecisionSession instance...")
        try:
            from orchestration.decision_session import DecisionSession
            session = DecisionSession()
            print("✅ Successfully created DecisionSession instance")
            
            # Try to access methods
            if hasattr(session, 'run_session'):
                print("✅ DecisionSession has run_session method")
                
                # Examine method signature
                import inspect
                signature = inspect.signature(session.run_session)
                print(f"Method signature: {signature}")
            else:
                print("❌ DecisionSession does not have run_session method")
            
            # Check for AutoGen usage
            if hasattr(session, 'agents') and session.agents:
                print("✅ DecisionSession has agents attribute with value")
            elif hasattr(session, 'agents'):
                print("⚠️ DecisionSession has agents attribute but it's empty")
            else:
                print("❌ DecisionSession does not have agents attribute")
            
            # Try to get source code of run_session method
            if hasattr(session, 'run_session'):
                try:
                    source = inspect.getsource(session.run_session)
                    is_simplified = "simplified" in source.lower()
                    print(f"Is run_session explicitly marked as simplified: {is_simplified}")
                except Exception as e:
                    print(f"⚠️ Could not get source code: {e}")
        except Exception as e:
            print(f"❌ Failed to create DecisionSession instance: {e}")
            print(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("Decision session debug completed")

if __name__ == "__main__":
    main()