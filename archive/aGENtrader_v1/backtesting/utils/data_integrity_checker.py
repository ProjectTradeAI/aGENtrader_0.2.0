#!/usr/bin/env python3
"""
Backtest Data Integrity Checker

This module verifies that data integrity measures are properly applied
to trading agents during backtesting, ensuring authentic responses.
"""

import os
import sys
import logging
import inspect
from typing import Any, Dict, List, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_integrity_checker')

def check_agent_for_data_integrity_wrapper(agent: Any) -> bool:
    """
    Check if an agent has data integrity wrappers applied
    
    Args:
        agent: Agent instance to check
        
    Returns:
        True if data integrity wrappers are detected, False otherwise
    """
    # Check run_analysis method if it exists
    if hasattr(agent, 'run_analysis'):
        func = agent.run_analysis
        source = inspect.getsource(func)
        
        # Look for data integrity patterns
        if 'data_integrity' in source or 'integrity_check' in source:
            return True
            
    # Check run_decision method if it exists
    if hasattr(agent, 'run_decision'):
        func = agent.run_decision
        source = inspect.getsource(func)
        
        # Look for data integrity patterns
        if 'data_integrity' in source or 'integrity_check' in source:
            return True
            
    # No data integrity wrappers found
    return False

def check_session_for_data_integrity(session: Any) -> Dict[str, bool]:
    """
    Check a trading session for data integrity measures
    
    Args:
        session: Trading session instance to check
        
    Returns:
        Dictionary with data integrity status for each agent type
    """
    results = {
        'technical_analyst': False,
        'fundamental_analyst': False, 
        'sentiment_analyst': False,
        'decision_session': False
    }
    
    # Check if session has data integrity measures
    if hasattr(session, 'run_session'):
        func = session.run_session
        try:
            source = inspect.getsource(func)
            if 'data_integrity' in source or 'integrity_check' in source:
                results['decision_session'] = True
        except (TypeError, OSError):
            # Can't get source for built-in/compiled functions
            pass
    
    # Check individual agents if they exist
    if hasattr(session, 'technical_analyst'):
        results['technical_analyst'] = check_agent_for_data_integrity_wrapper(session.technical_analyst)
        
    if hasattr(session, 'fundamental_analyst'):
        results['fundamental_analyst'] = check_agent_for_data_integrity_wrapper(session.fundamental_analyst)
        
    if hasattr(session, 'sentiment_analyst'):
        results['sentiment_analyst'] = check_agent_for_data_integrity_wrapper(session.sentiment_analyst)
        
    return results

def ensure_data_integrity_applied(trading_system: Any) -> Dict[str, Any]:
    """
    Ensure data integrity measures are applied to a trading system
    
    Args:
        trading_system: Trading system instance to check and fix
        
    Returns:
        Dictionary with results of the check and fix operations
    """
    # Add project root to sys.path if needed
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        
    # Try to import the data integrity module
    try:
        from agents.data_integrity import ensure_data_integrity_for_agents
        have_module = True
    except ImportError:
        have_module = False
        logger.error("Failed to import data integrity module")
    
    results = {
        'imported_module': have_module,
        'applied': False,
        'check_results': None
    }
    
    # Check if data integrity measures are already applied
    check_results = check_session_for_data_integrity(trading_system)
    results['check_results'] = check_results
    
    # Apply data integrity measures if not already applied
    if not all(check_results.values()) and have_module:
        try:
            from agents.data_integrity import ensure_data_integrity_for_agents
            ensure_data_integrity_for_agents(trading_system)
            
            # Check again after applying
            new_check_results = check_session_for_data_integrity(trading_system)
            results['applied'] = True
            results['check_results'] = new_check_results
            
            logger.info("Applied data integrity measures to trading system")
        except Exception as e:
            logger.error(f"Error applying data integrity measures: {str(e)}")
    
    return results

def check_database_access() -> Dict[str, Any]:
    """
    Check if database access is configured and working
    
    Returns:
        Dictionary with database access status
    """
    results = {
        'database_url_set': False,
        'can_connect': False,
        'tables_available': [],
        'data_available': False
    }
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        results['database_url_set'] = True
        
        # Try to connect to database
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            results['can_connect'] = True
            
            # Check available tables
            try:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                results['tables_available'] = tables
                
                # Check for kline tables
                kline_tables = [table for table in tables if table.startswith('klines_')]
                
                # Check for data availability in kline tables
                if kline_tables:
                    for table in kline_tables[:1]:  # Check just the first table
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            results['data_available'] = True
                            break
                
                cursor.close()
            except Exception as e:
                logger.error(f"Error checking tables: {str(e)}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
    
    return results

if __name__ == "__main__":
    # This can be run as a standalone script to check if data integrity
    # measures are being applied correctly in the backtesting environment
    
    print("Checking data integrity implementation...")
    
    # Check database access
    db_status = check_database_access()
    print(f"\nDatabase Status:")
    print(f"  DATABASE_URL set: {db_status['database_url_set']}")
    print(f"  Can connect: {db_status['can_connect']}")
    print(f"  Tables available: {len(db_status['tables_available'])}")
    if db_status['tables_available']:
        print(f"    Sample tables: {db_status['tables_available'][:5]}")
    print(f"  Data available: {db_status['data_available']}")
    
    # Try to import trading system components
    print("\nChecking trading system imports...")
    try:
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
            
        try:
            from orchestration.decision_session import DecisionSession
            print("  ✓ DecisionSession imported")
        except ImportError:
            print("  ✗ Failed to import DecisionSession")
            
        try:
            from agents.data_integrity import ensure_data_integrity_for_agents
            print("  ✓ Data integrity module imported")
        except ImportError:
            print("  ✗ Failed to import data integrity module")
            
        # Try creating a session and checking data integrity
        try:
            session = DecisionSession(config={})
            check_results = check_session_for_data_integrity(session)
            
            print("\nData Integrity Check Results:")
            for agent_type, has_integrity in check_results.items():
                status = "✓" if has_integrity else "✗"
                print(f"  {status} {agent_type}")
                
        except Exception as e:
            print(f"\nError creating session: {str(e)}")
            
    except Exception as e:
        print(f"Error checking imports: {str(e)}")
        
    print("\nData integrity check complete.")