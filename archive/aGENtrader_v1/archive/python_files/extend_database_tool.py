#!/usr/bin/env python3
"""
Extend Database Retrieval Tool

This script extends the DatabaseRetrievalTool class with liquidity data functions.
"""

import os
import sys
import logging
import inspect
from importlib import reload
from types import FunctionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extend_database_tool():
    """Extend the DatabaseRetrievalTool class with liquidity data functions"""
    try:
        # Import the DatabaseRetrievalTool
        from agents.database_retrieval_tool import DatabaseRetrievalTool
        
        # Import the liquidity data functions
        from agents.liquidity_data import get_tool_extension_functions
        
        # Get the functions to add
        extension_functions = get_tool_extension_functions()
        
        # Add each function to the DatabaseRetrievalTool class
        for name, func in extension_functions.items():
            # Create a wrapper method for the class
            def create_wrapper(f):
                sig = inspect.signature(f)
                params = list(sig.parameters.values())
                
                # Remove the first parameter (typically 'self')
                if params and params[0].name == 'self':
                    params = params[1:]
                
                # Create a new signature for the wrapper method
                wrapper_sig = sig.replace(parameters=params)
                
                # Create the wrapper method
                def wrapper(self, *args, **kwargs):
                    return f(*args, **kwargs)
                
                # Add the signature to the wrapper
                wrapper.__signature__ = wrapper_sig
                wrapper.__name__ = f.__name__
                wrapper.__doc__ = f.__doc__
                
                return wrapper
            
            # Add the method to the class
            setattr(DatabaseRetrievalTool, name, create_wrapper(func))
        
        logger.info(f"Added {len(extension_functions)} liquidity data functions to DatabaseRetrievalTool")
        return True
    except Exception as e:
        logger.error(f"Error extending DatabaseRetrievalTool: {str(e)}")
        return False

def main():
    """Main entry point"""
    logger.info("Extending DatabaseRetrievalTool with liquidity data functions...")
    
    # Extend the DatabaseRetrievalTool
    success = extend_database_tool()
    
    if success:
        logger.info("DatabaseRetrievalTool extension complete")
    else:
        logger.error("Failed to extend DatabaseRetrievalTool")
        sys.exit(1)

if __name__ == "__main__":
    main()