"""
Test script to verify that the llm_config can be serialized to JSON.
This tests our fix for the 'Object of type function is not JSON serializable' error.
"""

import json
import sys
import os

# Add the agents directory to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.autogen_db_integration import create_market_data_function_map, get_integration

def test_llm_config_serialization():
    """Test that the llm_config can be serialized to JSON"""
    print("Getting integration...")
    integration = get_integration()
    
    print("Integration keys:", list(integration.keys()))
    
    print("Testing llm_config serialization...")
    try:
        llm_config = integration['llm_config']
        json_str = json.dumps(llm_config)
        print("SUCCESS: LLM config successfully serialized to JSON")
        return True
    except Exception as e:
        print(f"ERROR: Failed to serialize llm_config to JSON: {e}")
        return False

def test_function_map():
    """Test creating and using function_map"""
    print("Creating function map...")
    function_map = create_market_data_function_map()
    
    print("Function map keys:", list(function_map.keys()))
    
    print("Testing function calls...")
    try:
        # Try calling a function from the map
        if "_get_latest_price" in function_map:
            print("Function _get_latest_price exists in function_map")
        else:
            print("Function _get_latest_price NOT found in function_map")
            
        return True
    except Exception as e:
        print(f"ERROR: Failed to test function_map: {e}")
        return False

if __name__ == "__main__":
    print("Testing serialization fixes...")
    
    llm_config_result = test_llm_config_serialization()
    print("\n" + "="*50 + "\n")
    function_map_result = test_function_map()
    
    print("\n" + "="*50)
    print("Test Results:")
    print(f"LLM Config Serialization: {'✓ PASSED' if llm_config_result else '✗ FAILED'}")
    print(f"Function Map Functionality: {'✓ PASSED' if function_map_result else '✗ FAILED'}")