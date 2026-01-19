import duckdb
import os

db_path = "/Users/robert/Developer/DuckDB/tushare_duck_finance.db"
if not os.path.exists(db_path):
    print(f"Error: DB not found at {db_path}")
else:
    try:
        conn = duckdb.connect(db_path)
        print("Schema for fina_mainbz:")
        schema = conn.execute("DESCRIBE fina_mainbz").fetchall()
        for col in schema:
            print(col)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
