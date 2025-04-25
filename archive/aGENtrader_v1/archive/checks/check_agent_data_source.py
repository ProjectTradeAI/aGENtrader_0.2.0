"""
Advanced Data Source Validation Tool

This script performs a comprehensive check to confirm that AutoGen agents
are using real market data and not operating in simulation mode.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal

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

def check_database_schema(conn):
    """Check the database schema to understand what tables and data are available"""
    results = {}
    
    try:
        # Get a list of tables
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
        
        # For each table, get structure and row count
        table_details = {}
        for table in tables:
            # Get column info
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in cursor.fetchall()]
            
            # Get row count
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
            
            # For market data tables, get first and last timestamp
            time_range = None
            if "market_data" in table:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(f"""
                            SELECT MIN(timestamp), MAX(timestamp) 
                            FROM {table}
                        """)
                        min_time, max_time = cursor.fetchone()
                        if min_time and max_time:
                            time_range = {
                                "earliest": min_time.isoformat(), 
                                "latest": max_time.isoformat(),
                                "span_days": (max_time - min_time).days
                            }
                except Exception as e:
                    logger.warning(f"Error getting time range for {table}: {str(e)}")
            
            table_details[table] = {
                "columns": columns,
                "row_count": row_count,
                "time_range": time_range
            }
            
            # Sample data for market_data table
            if table == "market_data" and row_count > 0:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(f"""
                        SELECT * FROM {table} 
                        ORDER BY timestamp DESC
                        LIMIT 5
                    """)
                    sample_rows = [dict(row) for row in cursor.fetchall()]
                    # Convert timestamps and decimals for JSON serialization
                    for row in sample_rows:
                        for key, value in row.items():
                            if isinstance(value, datetime):
                                row[key] = value.isoformat()
                            elif isinstance(value, Decimal):
                                row[key] = float(value)
                
                table_details[table]["sample_data"] = sample_rows
        
        results["table_details"] = table_details
        return results
    
    except Exception as e:
        logger.error(f"Error checking database schema: {str(e)}")
        return {"error": str(e)}

def validate_market_data_authenticity(conn):
    """Perform extended validation of market data to confirm it's authentic"""
    results = {}
    
    try:
        # Check for common properties of authentic market data
        
        # 1. Check for realistic price movements - calculate daily returns
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    timestamp::date as date,
                    symbol,
                    AVG(close) as avg_close
                FROM market_data
                WHERE interval = 'D'
                GROUP BY timestamp::date, symbol
                ORDER BY date
            """)
            daily_data = cursor.fetchall()
        
        if not daily_data:
            results["daily_returns_check"] = {
                "status": "SKIP",
                "reason": "No daily data available"
            }
        else:
            # Convert to list of dicts with python types
            daily_data = [
                {
                    "date": row["date"].isoformat() if isinstance(row["date"], datetime) else row["date"],
                    "symbol": row["symbol"],
                    "avg_close": float(row["avg_close"]) if isinstance(row["avg_close"], Decimal) else row["avg_close"]
                }
                for row in daily_data
            ]
            
            # Calculate daily returns
            returns = []
            prev_price = None
            prev_date = None
            for row in daily_data:
                if prev_price:
                    daily_return = (row["avg_close"] - prev_price) / prev_price
                    days_diff = (datetime.fromisoformat(row["date"]) - datetime.fromisoformat(prev_date)).days
                    returns.append({
                        "date": row["date"],
                        "daily_return": daily_return,
                        "days_diff": days_diff
                    })
                prev_price = row["avg_close"]
                prev_date = row["date"]
            
            # Analyze returns for realism
            if returns:
                # Real crypto data typically has both positive and negative returns
                pos_returns = sum(1 for r in returns if r["daily_return"] > 0)
                neg_returns = sum(1 for r in returns if r["daily_return"] < 0)
                zero_returns = sum(1 for r in returns if r["daily_return"] == 0)
                
                # Calculate volatility (standard deviation of returns)
                import math
                avg_return = sum(r["daily_return"] for r in returns) / len(returns)
                variance = sum((r["daily_return"] - avg_return) ** 2 for r in returns) / len(returns)
                volatility = math.sqrt(variance)
                
                # Check if returns look realistic
                has_mixed_returns = pos_returns > 0 and neg_returns > 0
                has_realistic_volatility = 0.005 < volatility < 0.1  # Typical crypto daily volatility range
                
                results["daily_returns_check"] = {
                    "status": "PASS" if has_mixed_returns and has_realistic_volatility else "FAIL",
                    "positive_returns": pos_returns,
                    "negative_returns": neg_returns,
                    "zero_returns": zero_returns,
                    "volatility": volatility,
                    "sample_returns": returns[:5]  # First 5 returns
                }
            else:
                results["daily_returns_check"] = {
                    "status": "SKIP",
                    "reason": "Could not calculate returns"
                }
        
        # 2. Check volume patterns - real market data should have variable volume
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    MIN(volume) as min_vol,
                    MAX(volume) as max_vol,
                    AVG(volume) as avg_vol,
                    STDDEV(volume) as std_vol
                FROM market_data
                WHERE volume IS NOT NULL
            """)
            volume_stats = cursor.fetchone()
        
        if volume_stats and volume_stats[0] is not None:
            min_vol, max_vol, avg_vol, std_vol = [float(v) if v else 0 for v in volume_stats]
            
            # Calculate coefficient of variation (CV) - measure of volume variability
            cv = std_vol / avg_vol if avg_vol > 0 else 0
            
            # In real market data, volumes vary significantly (high CV)
            # and there's a significant difference between min and max
            volume_variation = max_vol / min_vol if min_vol > 0 else 0
            
            results["volume_check"] = {
                "status": "PASS" if cv > 0.3 and volume_variation > 3 else "FAIL",
                "min_volume": min_vol,
                "max_volume": max_vol,
                "avg_volume": avg_vol,
                "std_dev": std_vol,
                "coefficient_of_variation": cv,
                "max_min_ratio": volume_variation
            }
        else:
            results["volume_check"] = {
                "status": "SKIP",
                "reason": "No volume data available"
            }
        
        # 3. Check for weekend patterns - crypto trading happens 24/7
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    EXTRACT(DOW FROM timestamp) as day_of_week,
                    COUNT(*) as record_count
                FROM market_data
                GROUP BY day_of_week
                ORDER BY day_of_week
            """)
            dow_counts = cursor.fetchall()
        
        if dow_counts:
            dow_data = {int(row[0]): int(row[1]) for row in dow_counts}
            
            # Check if weekend (Sat=6, Sun=0) data exists - crypto trades on weekends
            has_weekend_data = 6 in dow_data and 0 in dow_data
            
            # For simulated data, often there's less data on weekends
            weekend_ratio = (dow_data.get(6, 0) + dow_data.get(0, 0)) / sum(dow_data.values()) if dow_data else 0
            weekday_avg = sum(dow_data.get(i, 0) for i in range(1, 6)) / 5 if dow_data else 0
            weekend_avg = (dow_data.get(6, 0) + dow_data.get(0, 0)) / 2 if dow_data else 0
            
            # In real crypto data, weekend volume is comparable to weekday volume
            weekend_to_weekday_ratio = weekend_avg / weekday_avg if weekday_avg > 0 else 0
            
            results["weekend_trading_check"] = {
                "status": "PASS" if has_weekend_data and weekend_to_weekday_ratio > 0.7 else "FAIL",
                "has_weekend_data": has_weekend_data,
                "weekend_data_ratio": weekend_ratio,
                "weekend_to_weekday_ratio": weekend_to_weekday_ratio,
                "day_of_week_counts": dow_data
            }
        else:
            results["weekend_trading_check"] = {
                "status": "SKIP",
                "reason": "Could not determine day-of-week patterns"
            }
        
        # Overall assessment
        passed_checks = sum(1 for check in results.values() if isinstance(check, dict) and check.get("status") == "PASS")
        total_checks = sum(1 for check in results.values() if isinstance(check, dict) and check.get("status") != "SKIP")
        
        results["overall"] = {
            "status": "PASS" if passed_checks == total_checks else "FAIL",
            "passed_checks": passed_checks,
            "total_checks": total_checks
        }
        
        return results
    
    except Exception as e:
        logger.error(f"Error validating market data authenticity: {str(e)}")
        return {"error": str(e)}

def check_agent_data_sources():
    """
    Examine what data sources are available to agents and whether they
    are using real market data or any kind of simulation.
    """
    results = {}
    
    try:
        # Connect to the database
        conn = get_database_connection()
        
        # 1. First, check database schema
        logger.info("Checking database schema...")
        schema_results = check_database_schema(conn)
        results["database_schema"] = schema_results
        
        # 2. Validate market data authenticity
        logger.info("Validating market data authenticity...")
        authenticity_results = validate_market_data_authenticity(conn)
        results["data_authenticity"] = authenticity_results
        
        # 3. Check agent configurations
        logger.info("Checking agent configurations...")
        
        # Look for simulation flags or config files
        import glob
        
        # Check for any files that might suggest simulation mode
        simulation_files = glob.glob("*simulation*.py") + glob.glob("*simulated*.py") + glob.glob("*mock*.py")
        
        results["simulation_check"] = {
            "simulation_files_found": len(simulation_files) > 0,
            "simulation_files": simulation_files,
            "status": "FAIL" if len(simulation_files) > 0 else "PASS"
        }
        
        # Look for market data access in agent code
        agent_files = glob.glob("agents/*.py")
        
        # Simplified code analysis to check if agents use database
        uses_real_data = False
        uses_simulation = False
        
        for agent_file in agent_files:
            with open(agent_file, 'r') as f:
                content = f.read().lower()
                if 'database' in content and ('market_data' in content or 'query' in content):
                    uses_real_data = True
                if 'simulation' in content or 'simulated' in content or 'mock' in content:
                    uses_simulation = True
        
        results["agent_code_check"] = {
            "agent_files_analyzed": len(agent_files),
            "uses_database_queries": uses_real_data,
            "uses_simulation_terms": uses_simulation,
            "status": "PASS" if uses_real_data and not uses_simulation else "FAIL"
        }
        
        # Check for database connection in agent modules
        try:
            logger.info("Testing database access from agent modules...")
            from agents.database_integration import DatabaseQueryManager
            from agents.database_query_agent import DatabaseQueryAgent
            
            # Test if agent can query real data
            agent = DatabaseQueryAgent()
            test_data = agent.query_market_data("BTCUSDT", "1h", 1)
            
            results["agent_query_test"] = {
                "status": "PASS" if test_data and len(test_data) > 10 else "FAIL",
                "data_received": test_data is not None,
                "data_length": len(test_data) if test_data else 0
            }
        except Exception as e:
            results["agent_query_test"] = {
                "status": "FAIL",
                "error": str(e)
            }
        
        # Close connection
        conn.close()
        logger.info("Database connection closed")
        
        # Overall verification
        verifications = [
            results["data_authenticity"]["overall"]["status"] == "PASS",
            results["simulation_check"]["status"] == "PASS",
            results["agent_code_check"]["status"] == "PASS",
            results.get("agent_query_test", {}).get("status") == "PASS"
        ]
        
        results["overall_verification"] = {
            "status": "PASS" if all(verifications) else "FAIL",
            "passed_checks": sum(1 for v in verifications if v),
            "total_checks": len(verifications)
        }
        
        logger.info(f"Overall verification: {results['overall_verification']['status']}")
        
        # Save results
        os.makedirs("data", exist_ok=True)
        with open("data/agent_data_source_verification.json", "w") as f:
            json.dump(results, f, indent=2, cls=CustomJSONEncoder)
        
        return results
    
    except Exception as e:
        logger.error(f"Error checking agent data sources: {str(e)}")
        return {"error": str(e)}

def main():
    """Main entry point"""
    print("\n==== AGENT DATA SOURCE VERIFICATION ====")
    print("Checking if agents are using real market data...")
    
    verification_results = check_agent_data_sources()
    
    if "error" in verification_results:
        print(f"\n❌ ERROR: {verification_results['error']}")
        return
    
    # Print summary results
    overall_result = verification_results.get("overall_verification", {})
    data_authenticity = verification_results.get("data_authenticity", {}).get("overall", {})
    simulation_check = verification_results.get("simulation_check", {})
    agent_code_check = verification_results.get("agent_code_check", {})
    agent_query_test = verification_results.get("agent_query_test", {})
    
    print("\n=== Results Summary ===")
    print(f"Data Authenticity: {data_authenticity.get('status', 'UNKNOWN')} ({data_authenticity.get('passed_checks', 0)}/{data_authenticity.get('total_checks', 0)} checks passed)")
    print(f"Simulation Check: {simulation_check.get('status', 'UNKNOWN')}")
    print(f"Agent Code Check: {agent_code_check.get('status', 'UNKNOWN')}")
    print(f"Agent Query Test: {agent_query_test.get('status', 'UNKNOWN')}")
    print(f"\nOVERALL RESULT: {overall_result.get('status', 'UNKNOWN')} ({overall_result.get('passed_checks', 0)}/{overall_result.get('total_checks', 0)} checks passed)")
    
    if overall_result.get("status") == "PASS":
        print("\n✅ VERIFICATION PASSED: Agents are using real market data, not simulation!")
    else:
        print("\n❌ VERIFICATION FAILED: Issues were found with agent data sources")
        
        if simulation_check.get("status") != "PASS":
            print(f"  - Simulation files detected: {simulation_check.get('simulation_files')}")
        
        if agent_code_check.get("status") != "PASS":
            if not agent_code_check.get("uses_database_queries"):
                print("  - Agents may not be using database queries")
            if agent_code_check.get("uses_simulation_terms"):
                print("  - Agent code contains simulation-related terms")
        
        if agent_query_test.get("status") != "PASS":
            print(f"  - Agent query test failed: {agent_query_test.get('error', 'No data received')}")
    
    print("\nDetailed results saved to data/agent_data_source_verification.json")

if __name__ == "__main__":
    main()