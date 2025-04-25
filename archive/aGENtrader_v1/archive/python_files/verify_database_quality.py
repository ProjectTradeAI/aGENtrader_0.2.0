"""
Database Quality Verification

This script verifies that the database contains real market data
by examining data patterns and consistency indicators.
"""

import os
import json
import logging
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Establish connection to the database"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(database_url)
    logger.info("Connected to database")
    return conn

def verify_market_data_quality(conn):
    """
    Verify the quality of market data in the database.
    
    Checks for:
    1. Timestamp sequence consistency
    2. Price relationship rules (high >= open/close >= low)
    3. Realistic price movements and volatility
    4. Data density and completeness
    """
    results = {}
    
    try:
        # Query available symbols and intervals
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT symbol FROM market_data")
            symbols = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT interval FROM market_data")
            intervals = [row[0] for row in cursor.fetchall()]
        
        results["available_symbols"] = symbols
        results["available_intervals"] = intervals
        
        if not symbols or not intervals:
            logger.warning("No symbols or intervals found")
            results["status"] = "FAIL"
            results["reason"] = "No market data found"
            return results
        
        # Select a symbol and interval to verify
        test_symbol = "BTCUSDT" if "BTCUSDT" in symbols else symbols[0]
        test_intervals = ["1h", "4h", "D"] if all(i in intervals for i in ["1h", "4h", "D"]) else [intervals[0]]
        
        logger.info(f"Verifying data quality for {test_symbol} with intervals: {test_intervals}")
        interval_results = {}
        
        for interval in test_intervals:
            # Get a significant sample of data
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT timestamp, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = %s AND interval = %s
                    ORDER BY timestamp DESC
                    LIMIT 500
                """, (test_symbol, interval))
                
                data = cursor.fetchall()
                
            if not data:
                logger.warning(f"No data found for {test_symbol} with {interval} interval")
                interval_results[interval] = {
                    "status": "FAIL",
                    "reason": "No data found",
                    "records": 0
                }
                continue
            
            # Convert to list of dictionaries
            data = [dict(row) for row in data]
            
            # 1. Check timestamp sequence
            timestamps = [row["timestamp"] for row in data]
            timestamps.sort(reverse=True)  # Sort in descending order
            
            time_diffs = []
            for i in range(1, len(timestamps)):
                diff = abs((timestamps[i-1] - timestamps[i]).total_seconds())
                time_diffs.append(diff)
            
            # Calculate the most common time difference
            if time_diffs:
                from collections import Counter
                counter = Counter(time_diffs)
                most_common_diff = counter.most_common(1)[0][0]
                time_consistency = sum(1 for diff in time_diffs if abs(diff - most_common_diff) < 10) / len(time_diffs)
            else:
                time_consistency = 0
            
            # 2. Check price relationships (OHLC rules)
            price_rule_valid = []
            for row in data:
                high = float(row["high"])
                low = float(row["low"])
                open_price = float(row["open"])
                close = float(row["close"])
                
                # High should be >= open, close, and low
                # Low should be <= open, close, and high
                valid = (high >= open_price and 
                         high >= close and 
                         low <= open_price and 
                         low <= close)
                
                price_rule_valid.append(valid)
            
            price_rule_consistency = sum(price_rule_valid) / len(data) if data else 0
            
            # 3. Calculate price volatility
            closes = [float(row["close"]) for row in data]
            
            if closes:
                avg_price = sum(closes) / len(closes)
                variance = sum((price - avg_price) ** 2 for price in closes) / len(closes)
                volatility = (variance ** 0.5) / avg_price  # Normalized volatility
            else:
                avg_price = 0
                volatility = 0
            
            # 4. Check price changes - real data shouldn't be too smooth or too jumpy
            price_changes = []
            for i in range(1, len(closes)):
                pct_change = abs((closes[i-1] - closes[i]) / closes[i])
                price_changes.append(pct_change)
            
            if price_changes:
                avg_pct_change = sum(price_changes) / len(price_changes)
                max_pct_change = max(price_changes)
            else:
                avg_pct_change = 0
                max_pct_change = 0
            
            # Determine if the data appears to be real
            # Real crypto data typically has:
            # 1. Consistent time intervals
            # 2. Valid OHLC rules (high>open/close>low)
            # 3. Some volatility but not extreme
            # 4. Some non-zero price changes
            is_real_data = (
                time_consistency > 0.9 and
                price_rule_consistency > 0.95 and
                0.0001 < volatility < 0.3 and
                0 < avg_pct_change < 0.05
            )
            
            interval_results[interval] = {
                "status": "PASS" if is_real_data else "FAIL",
                "records": len(data),
                "time_consistency": time_consistency,
                "price_rule_consistency": price_rule_consistency,
                "volatility": volatility,
                "avg_percent_change": avg_pct_change,
                "max_percent_change": max_pct_change,
                "price_range": {
                    "min": min(closes) if closes else None,
                    "max": max(closes) if closes else None,
                    "avg": avg_price
                },
                # Convert sample data with timestamp handling
                "sample_data": [{
                    **{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in row.items()}
                } for row in data[:5]]  # First 5 records
            }
        
        # Overall result
        results["interval_results"] = interval_results
        
        # Overall status
        passing_intervals = sum(1 for result in interval_results.values() if result["status"] == "PASS")
        results["status"] = "PASS" if passing_intervals > 0 else "FAIL"
        results["passing_intervals"] = passing_intervals
        results["total_intervals"] = len(interval_results)
        
        if results["status"] == "PASS":
            logger.info("✅ Database quality verification PASSED - data appears to be real market data")
        else:
            logger.warning("❌ Database quality verification FAILED - data does not appear to be real")
        
        return results
    
    except Exception as e:
        logger.error(f"Error verifying market data quality: {str(e)}")
        results["status"] = "ERROR"
        results["error"] = str(e)
        return results

def verify_autogen_database_integration(conn):
    """
    Verify that the database can be accessed by AutoGen agents
    by checking that the necessary tables and functions exist.
    """
    results = {}
    
    try:
        # Check for market_data table
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'market_data'
                )
            """)
            has_market_data = cursor.fetchone()[0]
            
        results["has_market_data_table"] = has_market_data
        
        # Check if the required modules exist
        import os.path
        
        modules_to_check = [
            "agents/database_integration.py",
            "agents/database_query_agent.py",
            "agents/database_retrieval_tool.py"
        ]
        
        module_exists = {}
        for module in modules_to_check:
            module_exists[module] = os.path.isfile(module)
        
        results["required_modules"] = module_exists
        
        # Try to import key AutoGen database functions
        import_results = {}
        
        try:
            from agents.database_query_agent import DatabaseQueryAgent
            agent = DatabaseQueryAgent()
            import_results["DatabaseQueryAgent"] = "SUCCESS"
            
            try:
                # Test a basic function call
                data = agent.query_market_data("BTCUSDT", "1h", 1)
                
                if data and len(data) > 10:  # Should have some meaningful content
                    import_results["query_market_data"] = "SUCCESS"
                else:
                    import_results["query_market_data"] = "FAILED - No data returned"
            except Exception as e:
                import_results["query_market_data"] = f"ERROR - {str(e)}"
            
        except Exception as e:
            import_results["DatabaseQueryAgent"] = f"ERROR - {str(e)}"
        
        results["import_tests"] = import_results
        
        # Overall status
        if (has_market_data and 
            all(module_exists.values()) and 
            import_results.get("DatabaseQueryAgent") == "SUCCESS" and
            import_results.get("query_market_data") == "SUCCESS"):
            results["status"] = "PASS"
            logger.info("✅ AutoGen database integration verification PASSED")
        else:
            results["status"] = "FAIL"
            logger.warning("❌ AutoGen database integration verification FAILED")
        
        return results
    
    except Exception as e:
        logger.error(f"Error verifying AutoGen database integration: {str(e)}")
        results["status"] = "ERROR"
        results["error"] = str(e)
        return results

def main():
    """Main function to verify database quality and integration"""
    logger.info("Starting database quality and integration verification")
    
    results = {}
    
    try:
        # Connect to database
        conn = get_database_connection()
        
        # Verify market data quality
        logger.info("Verifying market data quality...")
        market_data_results = verify_market_data_quality(conn)
        results["market_data_quality"] = market_data_results
        
        # Verify AutoGen integration
        logger.info("Verifying AutoGen database integration...")
        integration_results = verify_autogen_database_integration(conn)
        results["autogen_integration"] = integration_results
        
        # Close connection
        conn.close()
        logger.info("Database connection closed")
        
        # Overall verification result
        overall_status = (
            market_data_results.get("status") == "PASS" and
            integration_results.get("status") == "PASS"
        )
        
        results["overall_status"] = "PASS" if overall_status else "FAIL"
        
        # Save results to file with datetime handling
        os.makedirs("data", exist_ok=True)
        
        # Custom JSON encoder for datetime and Decimal objects
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, o):
                from decimal import Decimal
                if isinstance(o, datetime):
                    return o.isoformat()
                if isinstance(o, Decimal):
                    return float(o)
                return super().default(o)
        
        with open("data/database_verification_results.json", "w") as f:
            json.dump(results, f, indent=2, cls=CustomJSONEncoder)
        
        logger.info(f"Results saved to data/database_verification_results.json")
        
        # Print conclusion
        print("\n==== DATABASE VERIFICATION RESULTS ====")
        print(f"Market Data Quality: {market_data_results.get('status', 'UNKNOWN')}")
        print(f"AutoGen Integration: {integration_results.get('status', 'UNKNOWN')}")
        print(f"Overall Status: {results['overall_status']}")
        
        if results["overall_status"] == "PASS":
            print("\n✅ VERIFICATION PASSED: The database contains real market data and is properly integrated with AutoGen")
        else:
            print("\n❌ VERIFICATION FAILED: Issues were found with the database or AutoGen integration")
            
            if market_data_results.get("status") != "PASS":
                print(f"  - Market data quality issue: {market_data_results.get('reason', 'See detailed results')}")
            
            if integration_results.get("status") != "PASS":
                print(f"  - Integration issue: {integration_results.get('reason', 'See detailed results')}")
        
        print("\nDetailed results saved to data/database_verification_results.json")
        
    except Exception as e:
        logger.error(f"Error in verification process: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()