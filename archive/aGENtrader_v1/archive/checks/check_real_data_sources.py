"""
Real Data Sources Checker

This script verifies that agents are using real market data and not simulations.
"""

import os
import logging
import json
import glob
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# For JSON serialization
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def get_database_connection():
    """Establish connection to the database"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(database_url)
    logger.info("Connected to database")
    return conn

def check_database_tables(conn):
    """Check what tables exist in the database"""
    results = {}
    
    try:
        # Get list of tables
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
        
        results["tables"] = tables
        logger.info(f"Found {len(tables)} tables: {tables}")
        
        # Get row counts for each table
        table_counts = {}
        for table in tables:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
        
        results["table_counts"] = table_counts
        
        # Check if market_data table exists and has data
        has_market_data = "market_data" in tables and table_counts.get("market_data", 0) > 0
        results["has_market_data"] = has_market_data
        
        return results
    
    except Exception as e:
        logger.error(f"Error checking database tables: {str(e)}")
        return {"error": str(e)}

def sample_market_data(conn):
    """Get a sample of market data to verify its authenticity"""
    results = {}
    
    try:
        # Check if market_data table exists
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'market_data'
                )
            """)
            has_market_data = cursor.fetchone()[0]
        
        if not has_market_data:
            return {"error": "No market_data table found"}
        
        # Get available symbols and intervals
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT symbol FROM market_data")
            symbols = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT interval FROM market_data")
            intervals = [row[0] for row in cursor.fetchall()]
        
        results["available_symbols"] = symbols
        results["available_intervals"] = intervals
        
        # Get a sample of recent market data
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM market_data
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            sample_data = [dict(row) for row in cursor.fetchall()]
            
            # Convert timestamps and decimals for JSON serialization
            for row in sample_data:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
                    elif isinstance(value, Decimal):
                        row[key] = float(value)
        
        results["sample_data"] = sample_data
        
        # Check data quality indicators
        # 1. Check if high is always >= low (real data property)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM market_data
                WHERE high < low
            """)
            invalid_hl_count = cursor.fetchone()[0]
        
        results["high_low_check"] = {
            "invalid_count": invalid_hl_count,
            "status": "PASS" if invalid_hl_count == 0 else "FAIL"
        }
        
        # 2. Check if there's price variation (real data has variance)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    MIN(close) as min_close,
                    MAX(close) as max_close,
                    AVG(close) as avg_close,
                    STDDEV(close) as std_close
                FROM market_data
                WHERE close IS NOT NULL
            """)
            stats = cursor.fetchone()
            
            if stats[0] is not None:
                min_close, max_close, avg_close, std_close = [float(v) if v else 0 for v in stats]
                
                # Calculate coefficient of variation (CV)
                cv = std_close / avg_close if avg_close > 0 else 0
                
                # Real data should have some variability
                results["price_variation_check"] = {
                    "min": min_close,
                    "max": max_close,
                    "avg": avg_close,
                    "std_dev": std_close,
                    "coefficient_of_variation": cv,
                    "status": "PASS" if cv > 0.005 else "FAIL"  # Some minimal variability expected
                }
            else:
                results["price_variation_check"] = {
                    "status": "FAIL",
                    "reason": "No close price data available"
                }
        
        return results
    
    except Exception as e:
        logger.error(f"Error sampling market data: {str(e)}")
        return {"error": str(e)}

def check_agent_code_for_simulation():
    """Check agent code for signs of simulation use"""
    results = {}
    
    try:
        # Look for simulation-related files
        simulation_files = glob.glob("*simulation*.py") + glob.glob("*simulated*.py") + glob.glob("*mock*.py")
        results["simulation_files"] = simulation_files
        
        # Check agent files for database usage vs simulation
        agent_files = glob.glob("agents/*.py")
        
        db_usage_count = 0
        simulation_term_count = 0
        
        for agent_file in agent_files:
            with open(agent_file, 'r') as f:
                content = f.read().lower()
                if 'database' in content and ('market_data' in content or 'query' in content):
                    db_usage_count += 1
                if 'simulation' in content or 'simulated' in content or 'mock' in content:
                    simulation_term_count += 1
        
        results["agent_files_analyzed"] = len(agent_files)
        results["database_usage_count"] = db_usage_count
        results["simulation_term_count"] = simulation_term_count
        
        # Check if agent query functions exist and work
        try:
            from agents.database_query_agent import DatabaseQueryAgent
            
            agent = DatabaseQueryAgent()
            test_data = agent.query_market_data("BTCUSDT", "1h", 1)
            
            results["agent_query_test"] = {
                "works": test_data is not None and len(test_data) > 10,
                "sample": test_data[:100] if test_data else None  # First 100 chars
            }
        except Exception as e:
            results["agent_query_test"] = {
                "works": False,
                "error": str(e)
            }
        
        # Overall assessment
        using_real_data = (
            db_usage_count > 0 and
            results.get("agent_query_test", {}).get("works", False) and
            simulation_term_count < db_usage_count  # More database references than simulation terms
        )
        
        results["using_real_data"] = using_real_data
        
        return results
    
    except Exception as e:
        logger.error(f"Error checking agent code: {str(e)}")
        return {"error": str(e)}

def main():
    """Main function to check real data sources"""
    print("\n==== REAL DATA SOURCES CHECK ====")
    print("Verifying that agents are using real market data and not simulations...\n")
    
    results = {}
    
    try:
        # Connect to database
        conn = get_database_connection()
        
        # Check database tables
        print("Checking database tables...")
        db_tables = check_database_tables(conn)
        results["database_tables"] = db_tables
        
        # Check market data
        print("Sampling market data...")
        market_data = sample_market_data(conn)
        results["market_data"] = market_data
        
        # Check agent code
        print("Analyzing agent code...")
        agent_code = check_agent_code_for_simulation()
        results["agent_code"] = agent_code
        
        # Close database connection
        conn.close()
        logger.info("Database connection closed")
        
        # Determine overall result
        has_market_data = db_tables.get("has_market_data", False)
        data_checks_pass = (
            market_data.get("high_low_check", {}).get("status") == "PASS" and
            market_data.get("price_variation_check", {}).get("status") == "PASS"
        )
        using_real_data = agent_code.get("using_real_data", False)
        
        overall_pass = has_market_data and data_checks_pass and using_real_data
        
        results["overall_result"] = {
            "status": "PASS" if overall_pass else "FAIL",
            "has_market_data": has_market_data,
            "data_checks_pass": data_checks_pass,
            "using_real_data_in_code": using_real_data
        }
        
        # Save results to file
        os.makedirs("data", exist_ok=True)
        with open("data/real_data_sources_check.json", "w") as f:
            json.dump(results, f, indent=2, cls=CustomJSONEncoder)
        
        # Print summary
        print("\n=== Results Summary ===")
        print(f"Database Has Market Data: {'✅ YES' if has_market_data else '❌ NO'}")
        print(f"Market Data Quality Checks: {'✅ PASS' if data_checks_pass else '❌ FAIL'}")
        print(f"Agent Code Uses Real Data: {'✅ YES' if using_real_data else '❌ NO'}")
        print(f"\nOVERALL RESULT: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        
        if overall_pass:
            print("\n✅ VERIFICATION PASSED: Agents are using real market data, not simulations!")
        else:
            print("\n❌ VERIFICATION FAILED: Issues were found with data sources")
            
            if not has_market_data:
                print("  - No market data found in database")
            
            if not data_checks_pass:
                if market_data.get("high_low_check", {}).get("status") != "PASS":
                    print(f"  - High-low price relationship check failed")
                
                if market_data.get("price_variation_check", {}).get("status") != "PASS":
                    print(f"  - Price variation check failed")
            
            if not using_real_data:
                if agent_code.get("simulation_term_count", 0) >= agent_code.get("database_usage_count", 0):
                    print("  - Agent code has more simulation terms than database usage")
                
                if not agent_code.get("agent_query_test", {}).get("works", False):
                    print("  - Agent database query test failed")
        
        print("\nDetailed results saved to data/real_data_sources_check.json")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        print(f"\n❌ ERROR: {str(e)}")
        results["error"] = str(e)

if __name__ == "__main__":
    main()