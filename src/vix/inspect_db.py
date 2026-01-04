import duckdb
from .config import OPT_DB_PATH

conn = duckdb.connect(OPT_DB_PATH, read_only=True)
print("Columns in opt_basic:")
print(conn.execute("PRAGMA table_info('opt_basic')").fetchdf())
print("\nSample data from opt_basic:")
print(conn.execute("SELECT * FROM opt_basic LIMIT 5").fetchdf())
conn.close()
