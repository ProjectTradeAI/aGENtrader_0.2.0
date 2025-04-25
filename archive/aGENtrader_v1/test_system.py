"""
System Verification Test Script

This script tests the reorganized trading system to ensure all components
are properly set up and can be imported.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    """Check if all core components can be imported"""
    import_errors = []
    
    # Test agent imports
    try:
        from agents.technical.structured_decision_agent import TechnicalAnalysisAgent
        print("✓ Technical Analysis Agent imported successfully")
    except ImportError as e:
        import_errors.append(f"✗ Technical Analysis Agent import error: {str(e)}")
    
    try:
        from agents.fundamental.collaborative_decision_agent import FundamentalAnalysisAgent
        print("✓ Fundamental Analysis Agent imported successfully")
    except ImportError as e:
        import_errors.append(f"✗ Fundamental Analysis Agent import error: {str(e)}")
    
    try:
        from agents.portfolio.portfolio_agents import PortfolioManagementAgent
        print("✓ Portfolio Management Agent imported successfully")
    except ImportError as e:
        import_errors.append(f"✗ Portfolio Management Agent import error: {str(e)}")
    
    # Test data imports
    try:
        from data.sources.market_data import get_market_data, compute_technical_indicators
        print("✓ Market Data module imported successfully")
    except ImportError as e:
        import_errors.append(f"✗ Market Data module import error: {str(e)}")
    
    try:
        from data.storage.database import get_available_symbols, get_available_intervals
        print("✓ Database module imported successfully")
    except ImportError as e:
        import_errors.append(f"✗ Database module import error: {str(e)}")
    
    # Test orchestration import
    try:
        from orchestration.decision_session import DecisionSession, make_trading_decision
        print("✓ Decision Session imported successfully")
    except ImportError as e:
        import_errors.append(f"✗ Decision Session import error: {str(e)}")
    
    # Report any errors
    if import_errors:
        print("\nImport errors found:")
        for error in import_errors:
            print(f"  {error}")
        return False
    else:
        print("\nAll core components imported successfully!")
        return True

def test_system_structure():
    """Test that the system structure is valid"""
    structure_errors = []
    
    # Check key directories
    for directory in ["agents", "data", "orchestration", "backtesting"]:
        if not os.path.isdir(directory):
            structure_errors.append(f"Missing directory: {directory}")
    
    # Check key files
    key_files = [
        "agents/technical/structured_decision_agent.py",
        "agents/fundamental/collaborative_decision_agent.py",
        "agents/portfolio/portfolio_agents.py",
        "data/sources/market_data.py",
        "data/storage/database.py",
        "orchestration/decision_session.py",
        "backtesting/scripts/run_backtest.sh"
    ]
    
    for file_path in key_files:
        if not os.path.isfile(file_path):
            structure_errors.append(f"Missing file: {file_path}")
    
    # Report any errors
    if structure_errors:
        print("\nStructure errors found:")
        for error in structure_errors:
            print(f"  {error}")
        return False
    else:
        print("\nSystem structure is valid!")
        return True

def check_basic_functionality():
    """Test basic system functionality"""
    try:
        from orchestration.decision_session import make_trading_decision
        
        print("\nTesting minimal functionality...")
        print("Attempting to import necessary modules...")
        print("✓ Imports successful")
        
        # We won't actually run the decision function as it requires API keys
        # and database setup, but we'll check if the function exists
        print("✓ Decision function exists")
        
        # Check if backtesting scripts exist
        if os.path.isfile("backtesting/scripts/run_backtest.sh"):
            print("✓ Backtesting scripts exist")
        else:
            print("✗ Backtesting scripts missing")
        
        print("\nBasic functionality checks complete")
        return True
        
    except Exception as e:
        print(f"\n✗ Basic functionality error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== SYSTEM VERIFICATION TEST ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("")
    
    # Test system structure
    structure_valid = test_system_structure()
    
    # Test imports
    imports_valid = check_imports()
    
    # Test basic functionality
    functionality_valid = check_basic_functionality()
    
    # Overall result
    if structure_valid and imports_valid and functionality_valid:
        print("\n✅ System verification passed!")
        return 0
    else:
        print("\n❌ System verification failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)