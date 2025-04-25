
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def execute_market_query(query: str) -> str:
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('PGDATABASE'),
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            host=os.environ.get('PGHOST'),
            port=os.environ.get('PGPORT')
        )

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            data = cur.fetchall()
            return json.dumps([dict(row) for row in data], default=str)
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        return "[]"
