#!/usr/bin/env python3
"""
Patch to fix schema mismatch in authentic_backtest.py

This script modifies the authentic_backtest.py file to use the market_data table
instead of the klines_* tables expected in the original code.
"""
import os
import re
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("patch_script")

def patch_authentic_backtest(file_path):
    """
    Patch authentic_backtest.py to use the market_data table.
    
    Args:
        file_path: Path to the authentic_backtest.py file
    
    Returns:
        bool: True if patch was successful, False otherwise
    """
    try:
        logger.info(f"Patching {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            return False
        
        # Read original file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Create backup
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup at {backup_path}")
        
        # Replace the get_historical_market_data method to use the market_data table
        get_historical_data_pattern = r"def get_historical_market_data\(self[^}]*?\).*?return market_data"
        
        # Define the replacement function
        replacement = """def get_historical_market_data(self, symbol, interval, start_date, end_date):
        \"\"\"Get historical market data from the database.\"\"\"
        self.logger.info(f"Getting historical market data for {symbol} {interval} from {start_date} to {end_date}")
        
        # Convert dates to strings in format YYYY-MM-DD
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Connect to the database
        conn = None
        try:
            # Use the database URL from environment if available
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                self.logger.error("DATABASE_URL environment variable is not set")
                return None
                
            self.logger.info(f"Using database URL: {db_url[:10]}...{db_url[-10:]}")
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Query to get historical market data directly from market_data table
            query = \"\"\"
                SELECT 
                    timestamp, 
                    open, 
                    high, 
                    low, 
                    close, 
                    volume 
                FROM 
                    market_data 
                WHERE 
                    symbol = %s 
                    AND interval = %s
                    AND timestamp >= %s 
                    AND timestamp <= %s 
                ORDER BY 
                    timestamp
            \"\"\"
            
            cursor.execute(query, (symbol, interval, start_str, end_str))
            
            # Get results
            results = cursor.fetchall()
            
            if not results:
                self.logger.warning(f"No market data found for {symbol} {interval} from {start_date} to {end_date}")
                return None
            
            # Convert results to list of dictionaries
            market_data = []
            for row in results:
                market_data.append({
                    "timestamp": row[0],
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })
            
            self.logger.info(f"Found {len(market_data)} candles for {symbol} {interval}")
            
            return market_data
        
        except Exception as e:
            self.logger.error(f"Error getting historical market data: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            if conn:
                conn.close()
            return None
        
        finally:
            if conn:
                conn.close()"""
        
        # Use re.DOTALL to match across multiple lines
        patched_content = re.sub(get_historical_data_pattern, replacement, content, flags=re.DOTALL)
        
        # If the content hasn't changed, try an alternative approach
        if patched_content == content:
            logger.warning("Failed to replace get_historical_market_data method using regex pattern")
            logger.info("Trying alternative approach...")
            
            # Look for the function signature and then append our replacement
            function_signature = "def get_historical_market_data(self, symbol, interval, start_date, end_date):"
            if function_signature in content:
                # Find the position of the function signature
                pos = content.find(function_signature)
                
                # Find the end of the function
                # This is a simplistic approach - we look for the next method definition
                next_def = content.find("def ", pos + len(function_signature))
                if next_def != -1:
                    # Extract the function body
                    function_body = content[pos:next_def]
                    
                    # Replace the function body with our replacement
                    patched_content = content.replace(function_body, replacement)
                    
                    if patched_content != content:
                        logger.info("Successfully patched get_historical_market_data method using alternative approach")
                    else:
                        logger.error("Failed to patch get_historical_market_data method using alternative approach")
                        return False
                else:
                    logger.error("Could not find the end of the get_historical_market_data method")
                    return False
            else:
                logger.error("Could not find get_historical_market_data method")
                return False
        
        # Remove any mentions of interval_table conversion
        interval_table_pattern = r"interval_table = interval\.replace\('([^']+)', '([^']+)'\)"
        patched_content = re.sub(interval_table_pattern, "# Interval is used directly now", patched_content)
        
        # Fix references to interval_table in method calls
        method_call_pattern = r"self\.get_historical_market_data\(symbol, interval_table,"
        patched_content = re.sub(method_call_pattern, "self.get_historical_market_data(symbol, interval,", patched_content)
        
        # Write the patched content back to the file
        with open(file_path, 'w') as f:
            f.write(patched_content)
        
        logger.info(f"Successfully patched {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error patching authentic_backtest.py: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "backtesting/core/authentic_backtest.py"
    
    success = patch_authentic_backtest(file_path)
    
    if success:
        print(f"✅ Successfully patched {file_path}")
        return 0
    else:
        print(f"❌ Failed to patch {file_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
