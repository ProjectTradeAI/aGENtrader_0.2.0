#!/usr/bin/env python3
"""
Setup script for liquidity analysis tables

This script creates the necessary database tables for liquidity analysis.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get a connection to the PostgreSQL database"""
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable not set")
            return None
        
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info(f"Connected to database {DATABASE_URL[:35]}...")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def create_tables(conn):
    """Create the liquidity analysis tables"""
    try:
        # Read SQL file
        with open('agents/liquidity_data_tables.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL commands
        with conn.cursor() as cur:
            cur.execute(sql)
        
        logger.info("Liquidity analysis tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating liquidity analysis tables: {str(e)}")
        return False

def main():
    """Main entry point"""
    logger.info("Setting up liquidity analysis tables...")
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    # Create tables
    success = create_tables(conn)
    
    # Close connection
    conn.close()
    
    if success:
        logger.info("Liquidity analysis tables setup complete")
    else:
        logger.error("Failed to set up liquidity analysis tables")
        sys.exit(1)

if __name__ == "__main__":
    main()