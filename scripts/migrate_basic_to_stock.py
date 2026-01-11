import duckdb
import os
import sys

# Define Paths
DB_ROOT = os.getenv('DB_ROOT', '/Users/robert/Developer/DuckDB')
BASIC_DB_PATH = os.path.join(DB_ROOT, 'tushare_duck_basic.db')
STOCK_DB_PATH = os.path.join(DB_ROOT, 'tushare_duck_stock.db')

def migrate():
    print("Beginning migration of stock_basic and stock_company from basic.db to stock.db...")
    
    if not os.path.exists(BASIC_DB_PATH):
        print(f"Error: Source database not found at {BASIC_DB_PATH}")
        return
    
    # Connect to target DB (stock.db)
    con = duckdb.connect(STOCK_DB_PATH)
    print(f"Connected to target: {STOCK_DB_PATH}")
    
    try:
        # Attach source DB
        print(f"Attaching source: {BASIC_DB_PATH}")
        con.execute(f"ATTACH '{BASIC_DB_PATH}' AS src_db")
        
        # Get all tables from source
        print("Fetching table list from source...")
        try:
            # Try global information_schema filtering by catalog
            # Note: In DuckDB, the attached name (src_db) is the catalog name.
            tables_res = con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog='src_db' AND table_schema='main'").fetchall()
            
            # If that returns empty, maybe table_schema is different or it's just 'src_db' catalog
            if not tables_res:
                 # Try without schema filter or check what schemas exist
                 tables_res = con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog='src_db'").fetchall()

            tables_to_migrate = [t[0] for t in tables_res]
        except Exception as e:
            print(f"Error fetching table list: {e}")
            return
            
        print(f"Found {len(tables_to_migrate)} tables to migrate: {tables_to_migrate}")
        
        for table in tables_to_migrate:
            
            print(f"Migrating {table}...")
            
            # Check if table exists in target
            table_exists_tgt = False
            try:
                con.execute(f"DESCRIBE {table}")
                table_exists_tgt = True
                print(f"  Target table {table} already exists.")
            except:
                pass

            # Count source rows
            count_src = con.execute(f"SELECT count(*) FROM src_db.{table}").fetchone()[0]
            print(f"  Source rows: {count_src}")
            
            if table == 'metadata':
                print(f"  Merging {table} records (append mode)...")
                # For metadata, we want to keep existing target records and add source records
                # Assuming table_name is unique/primary key, and sets are disjoint.
                if not table_exists_tgt:
                     con.execute(f"CREATE TABLE {table} AS SELECT * FROM src_db.{table}")
                     print(f"  Created metadata table in target.")
                else:
                     # Append source metadata to target
                     # Use INSERT OR REPLACE or just INSERT depending on constraints. 
                     # DuckDB support INSERT INTO ... SELECT ...
                     # If conflicting keys exist, we might want newer? 
                     # But here we assume disjoint tables.
                     try:
                         con.execute(f"INSERT INTO {table} SELECT * FROM src_db.{table}")
                         print(f"  Appended source metadata to target.")
                     except Exception as e:
                         # Fallback for constraint errors
                         print(f"  Insert failed (possible duplicates), trying INSERT OR REPLACE/IGNORE logic via temp: {e}")
                         # Simple approach: Insert ignore
                         con.execute(f"INSERT OR IGNORE INTO {table} SELECT * FROM src_db.{table}")

            elif not table_exists_tgt:
                # Create as select
                con.execute(f"CREATE TABLE {table} AS SELECT * FROM src_db.{table}")
                print(f"  Created table {table} in target.")
            else:
                # Insert / Replace for regular tables
                try:
                    con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM src_db.{table}")
                    print(f"  Replaced table {table} in target with source data.")
                except Exception as e:
                    print(f"  Error migrating {table}: {e}")
            
            # Verify target
            count_tgt = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"  Target rows now: {count_tgt}")

        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    migrate()
