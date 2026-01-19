import duckdb
import os

db_path = "/Users/robert/Developer/DuckDB/tushare_duck_finance.db"
conn = duckdb.connect(db_path)
# Get a stock with both region and product data likely (e.g., Ping An Bank 000001.SZ or similar)
# Just looking for any data
try:
    rows = conn.execute("SELECT * FROM fina_mainbz LIMIT 20").fetchall()
    print("Sample rows:")
    for row in rows:
        print(row)
        
    # Check distinct bz_item for a single stock to see key patterns
    # Pick a ts_code from the rows
    ts_code = rows[0][0]
    print(f"\nData for {ts_code}:")
    stock_rows = conn.execute(f"SELECT * FROM fina_mainbz WHERE ts_code='{ts_code}' LIMIT 100").fetchall()
    for row in stock_rows:
        print(row)
finally:
    conn.close()
