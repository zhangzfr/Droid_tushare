import pandas as pd
import duckdb
import os
import sys

# Add project root to path
sys.path.append('/Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare')

from dashboard.market_insights_loader import process_opt_basic_data

DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_opt.db'

def test_loader():
    print(f"Connecting to {DB_PATH}...")
    conn = duckdb.connect(DB_PATH)
    
    # 1. Test Raw Data
    print("\n[Test 1] Raw opt_basic Sample:")
    query = "SELECT name, list_date, delist_date, exercise_price, maturity_date FROM opt_basic LIMIT 5"
    df_raw = conn.execute(query).fetchdf()
    print(df_raw)
    
    # 2. Test Processing Logic
    print("\n[Test 2] Processing Logic:")
    if not df_raw.empty:
        # Simulate the Date conversion I added
        for col in ['maturity_date', 'list_date', 'delist_date']:
             if col in df_raw.columns:
                 df_raw[col] = pd.to_datetime(df_raw[col], format='%Y%m%d', errors='coerce')
                 
        df_proc = process_opt_basic_data(df_raw)
        print("Processed Columns:", df_proc.columns.tolist())
        print("Sample Underlying:", df_proc['underlying'].tolist())
        print("Sample Maturity Clean:", df_proc['maturity_ym_clean'].tolist())
    
    # 3. Test Full Aggregation Function Logic (Simulation)
    print("\n[Test 3] Simulating get_opt_stats_underlying_counts:")
    query_full = "SELECT name, list_date, delist_date, exercise_price, maturity_date FROM opt_basic"
    df_full = conn.execute(query_full).fetchdf()
    
    if df_full.empty:
        print("ERROR: Full table is empty!")
    else:
        # Convert dates
        for col in ['maturity_date', 'list_date', 'delist_date']:
             if col in df_full.columns:
                 df_full[col] = pd.to_datetime(df_full[col], format='%Y%m%d', errors='coerce')
        
        df_full = process_opt_basic_data(df_full)
        
        if 'underlying' in df_full.columns:
            counts = df_full['underlying'].value_counts().reset_index()
            counts.columns = ['underlying', 'count']
            print("\nTop 10 Underlyings Found:")
            print(counts.head(10))
            
            # Check for mapping matches
            print("\nChecking for specific mapping keys:")
            for key in ['华夏上证50ETF', '50ETF', '菜粕', '豆粕']:
                found = key in counts['underlying'].values
                print(f"- {key}: {'FOUND' if found else 'MISSING'}")
        else:
            print("ERROR: 'underlying' column missing after processing.")

    conn.close()

if __name__ == "__main__":
    test_loader()
