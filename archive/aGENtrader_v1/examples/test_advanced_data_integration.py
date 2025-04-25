"""
Test Advanced Data Integration

This script tests the advanced data integration with Santiment and Alternative.me APIs.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check for Santiment API key
SANTIMENT_API_KEY = os.environ.get("SANTIMENT_API_KEY")

def test_alternative_me_provider():
    """Test the Alternative.me provider for Fear & Greed Index"""
    print("Testing Alternative.me Provider")
    print("==============================")
    
    try:
        from utils.providers.alternative_me import test_provider
        test_provider()
        return True
    except ImportError as e:
        logger.error(f"Error importing Alternative.me provider: {str(e)}")
        print(f"Error importing Alternative.me provider: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error testing Alternative.me provider: {str(e)}")
        print(f"Error testing Alternative.me provider: {str(e)}")
        return False

def test_santiment_provider(api_key=None):
    """Test the Santiment provider"""
    if not api_key:
        print("No Santiment API key provided. Skipping Santiment provider test.")
        return False
    
    print("\nTesting Santiment Provider")
    print("=========================")
    
    try:
        from utils.providers.santiment import test_provider
        test_provider(api_key)
        return True
    except ImportError as e:
        logger.error(f"Error importing Santiment provider: {str(e)}")
        print(f"Error importing Santiment provider: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error testing Santiment provider: {str(e)}")
        print(f"Error testing Santiment provider: {str(e)}")
        return False

def test_integrated_provider(api_key=None):
    """Test the integrated advanced data provider"""
    print("\nTesting Integrated Advanced Data Provider")
    print("=======================================")
    
    try:
        from utils.integrated_advanced_data import test_provider
        test_provider(api_key)
        return True
    except ImportError as e:
        logger.error(f"Error importing integrated provider: {str(e)}")
        print(f"Error importing integrated provider: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error testing integrated provider: {str(e)}")
        print(f"Error testing integrated provider: {str(e)}")
        return False

def test_database_schema():
    """Test the database schema creation"""
    print("\nTesting Database Schema Creation")
    print("==============================")
    
    try:
        from utils.database.advanced_data_schema import create_all_tables
        
        print("Creating database tables...")
        success = create_all_tables()
        print(f"Tables created successfully: {success}")
        return success
    except ImportError as e:
        logger.error(f"Error importing database schema: {str(e)}")
        print(f"Error importing database schema: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        print(f"Error creating database tables: {str(e)}")
        return False

def test_query_functions():
    """Test the AutoGen query functions"""
    print("\nTesting AutoGen Query Functions")
    print("=============================")
    
    try:
        from agents.query_advanced_data import test_query_functions
        
        print("Running query function tests...")
        test_query_functions()
        return True
    except ImportError as e:
        logger.error(f"Error importing query functions: {str(e)}")
        print(f"Error importing query functions: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error testing query functions: {str(e)}")
        print(f"Error testing query functions: {str(e)}")
        return False

def test_function_registration():
    """Test the AutoGen function registration"""
    print("\nTesting AutoGen Function Registration")
    print("===================================")
    
    try:
        from agents.register_advanced_data_functions import create_function_mapping
        
        print("Creating function mapping...")
        function_map = create_function_mapping()
        print(f"Successfully created function mapping with {len(function_map)} functions:")
        for func in function_map:
            print(f"- {func['name']}: {func['description']}")
        return True
    except ImportError as e:
        logger.error(f"Error importing function registration: {str(e)}")
        print(f"Error importing function registration: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error testing function registration: {str(e)}")
        print(f"Error testing function registration: {str(e)}")
        return False

def test_all_components(api_key=None):
    """Test all components of the advanced data integration"""
    print("TESTING ADVANCED DATA INTEGRATION")
    print("================================")
    print(f"Using Santiment API key: {'Yes' if api_key else 'No'}")
    print()
    
    # Test the individual components
    results = {
        "database_schema": test_database_schema(),
        "alternative_me": test_alternative_me_provider(),
        "santiment": test_santiment_provider(api_key) if api_key else "Skipped",
        "integrated_provider": test_integrated_provider(api_key),
        "query_functions": test_query_functions(),
        "function_registration": test_function_registration()
    }
    
    # Print summary
    print("\nTEST SUMMARY")
    print("===========")
    for component, result in results.items():
        status = "PASSED" if result is True else "FAILED" if result is False else result
        print(f"{component}: {status}")
    
    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r != True and r != False)
    
    print(f"\nOverall: {passed} passed, {failed} failed, {skipped} skipped")
    
    return failed == 0

def ask_for_api_key():
    """Ask the user for a Santiment API key if not provided"""
    api_key = SANTIMENT_API_KEY
    
    if not api_key:
        print("No Santiment API key found in environment variables.")
        print("The API key is required for full functionality.")
        print("You can either:")
        print("1. Set the SANTIMENT_API_KEY environment variable")
        print("2. Provide the API key as a command line argument")
        print("3. Enter the API key now")
        print("4. Continue without an API key (limited functionality)")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "3":
            api_key = input("Enter your Santiment API key: ").strip()
        elif choice == "1" or choice == "2":
            print("Please restart the script after setting the API key.")
            sys.exit(0)
    
    return api_key

def main():
    """Main entry point"""
    # Check for API key in command line arguments
    api_key = SANTIMENT_API_KEY
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    # If no API key, ask the user
    if not api_key:
        api_key = ask_for_api_key()
    
    # Run the tests
    success = test_all_components(api_key)
    
    if success:
        print("\nAll tests completed successfully!")
        print("The advanced data integration is ready to use with AutoGen agents.")
    else:
        print("\nSome tests failed. Please check the logs for details.")

if __name__ == "__main__":
    main()