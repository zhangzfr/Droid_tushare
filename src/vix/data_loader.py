import duckdb
import pandas as pd
import numpy as np
import warnings
import functools
import sys
import os

# Adjust path to allow importing from src based on project structure if needed
# However, if running as module from root, it should be fine.
from .config import OPT_DB_PATH, MACRO_DB_PATH, ETF_OPTIONS, INDEX_OPTIONS

# Constants
YEARS = 365

def fetch_option_data(start_date: str, end_date: str, underlying: str = '510050.SH') -> pd.DataFrame:
    """
    Fetches and prepares option data from DuckDB for VIX calculation.
    
    Args:
        start_date (str): Start date in 'YYYYMMDD' format.
        end_date (str): End date in 'YYYYMMDD' format.
        underlying (str): Underlying ETF or Index code. Default '510050.SH'.
        
    Returns:
        pd.DataFrame: Formatted option data with columns:
            ['date', 'exercise_date', 'close', 'contract_type', 'exercise_price', 'maturity']
    """
    if not OPT_DB_PATH:
        raise ValueError("OPT_DB_PATH is not defined in configuration.")

    print(f"Connecting to Option DB at {OPT_DB_PATH}...")
    conn = duckdb.connect(OPT_DB_PATH, read_only=True)
    
    try:
        # 1. Fetch Basic Info (opt_basic)
        # We need to filter contracts that are relevant for the period.
        # list_date <= end_date AND (last_edate >= start_date OR maturity_date >= start_date)
        # However, checking existence in opt_daily within range is safer/easier if volume is manageable.
        # Let's filter basic info first to reduce join size.
        
        # Note: opt_basic has 'ts_code', 'call_put', 'exercise_price', 'maturity_date', 'list_date'
        # underlying_code check? opt_basic might not have underlying_code column in the simple schema I saw earlier? 
        # Checking schema.py: opt_basic has: ts_code, exchange, name, ..., opt_code, ...
        # Resolve Underlying Config
        target_config = ETF_OPTIONS.get(underlying) or INDEX_OPTIONS.get(underlying)
        
        if not target_config:
            print(f"Warning: Underlying {underlying} not found in config. Using generic filter if possible or failing.")
            # Fallback or strict fail? Let's fail for now to be safe.
            raise ValueError(f"Underlying {underlying} not supported.")
            
        exchange = target_config['exchange']
        # Use name prefix for filtering. 
        # Note: opt_basic name usually starts with the ETF name. 
        # e.g. "华夏上证50ETF" -> "华夏上证50ETF期权..."
        name_filter = target_config['name']
        
        print(f"Fetching options for {name_filter} ({underlying}) on {exchange}...")
        
        # 1. Fetch Basic Info (Contract details)
        # Filter by Exchange and Name pattern
        query_basic = f"""
                SELECT ts_code, call_put, exercise_price, maturity_date
                FROM opt_basic
                WHERE list_date <= '{end_date}'
                  AND maturity_date >= '{start_date}'
                  AND exchange = '{exchange}'
                  AND name LIKE '{name_filter}%'
            """
        df_basic = conn.execute(query_basic).fetchdf()
        
        # 2. Fetch Daily Prices (opt_daily)
        query_daily = f"""
            SELECT ts_code, trade_date, close
            FROM opt_daily
            WHERE trade_date BETWEEN '{start_date}' AND '{end_date}'
        """
        df_daily = conn.execute(query_daily).fetchdf()
        
    finally:
        conn.close()
        
    if df_basic.empty or df_daily.empty:
        print("No option data found.")
        return pd.DataFrame()

    # Merge
    opt_data = pd.merge(df_daily, df_basic, on='ts_code', how='inner')
    
    if opt_data.empty:
         print("Merged option data is empty.")
         return pd.DataFrame()

    # Format Data
    opt_data.rename(columns={
        'trade_date': 'date',
        'maturity_date': 'exercise_date',
        'call_put': 'contract_type'
    }, inplace=True)
    
    # Map contract type if needed (DB usually stores 'C'/'P')
    # Tushare stores 'C'/'P'. VIX calc usually expects 'call'/'put' or 'C'/'P'?
    # Checking `calc_func.py` (impl plan says I'll port it). 
    # `utils/VIX/get_tushare_data.py` maps 'C'->'call', 'P'->'put'.
    opt_data['contract_type'] = opt_data['contract_type'].map({'C': 'call', 'P': 'put'})
    
    # Ensure types
    opt_data['date'] = pd.to_datetime(opt_data['date'].astype(str))
    opt_data['exercise_date'] = pd.to_datetime(opt_data['exercise_date'].astype(str))
    opt_data['exercise_price'] = opt_data['exercise_price'].astype(float)
    opt_data['close'] = opt_data['close'].astype(float)
    
    # Calculate maturity in years
    # Logic from original code: (exercise_date - date) / 365 ?
    # Original: calc_maturity(opt_data['exercise_date'], opt_data['date'], days=YEARS)
    # We can implement simple calculation here or import.
    # Let's do it inline for simplicity or define helper.
    opt_data['maturity'] = (opt_data['exercise_date'] - opt_data['date']).dt.days / YEARS
    
    # Handle expiring same day? VIX calc usually avoids maturity=0.
    # We'll filter later or let calc handle it.
    
    # Select columns
    required_cols = ['date', 'exercise_date', 'close', 'contract_type', 'exercise_price', 'maturity']
    opt_data = opt_data[required_cols].copy()
    
    opt_data.sort_values(by='date', inplace=True)
    
    return opt_data

def get_shibor_interpolated(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches Shibor data from DuckDB and interpolates it to daily tenors.
    
    Args:
        start_date (str): Start date 'YYYYMMDD'.
        end_date (str): End date 'YYYYMMDD'.
        
    Returns:
        pd.DataFrame: Interpolated daily Shibor rates (index=date, columns=1..365).
                      Rates are in decimals (e.g. 0.03).
    """
    if not MACRO_DB_PATH:
        raise ValueError("MACRO_DB_PATH is not defined in configuration.")
        
    conn = duckdb.connect(MACRO_DB_PATH, read_only=True)
    try:
        # Schema in schema.py: date, on, 1w, 2w, 1m, 3m, 6m, 9m, 1y
        # Note: columns might be named "on", "1w" etc which are reserved/need quoting in SQL?
        # In schema.py: "on" DOUBLE, "1w" DOUBLE...
        # Let's select all and process in pandas
        query = f"""
            SELECT * FROM shibor 
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
        """
        shibor_df = conn.execute(query).fetchdf()
    finally:
        conn.close()
        
    if shibor_df.empty:
        print("No Shibor data found.")
        return pd.DataFrame()
        
    # Process
    shibor_df['date'] = pd.to_datetime(shibor_df['date'].astype(str))
    shibor_df.set_index('date', inplace=True)
    shibor_df.sort_index(inplace=True)
    
    # Map columns to days
    # Tushare columns: on, 1w, 2w, 1m, 3m, 6m, 9m, 1y
    # Check actual columns in df
    shibor_map = {
        'on': 1, '1w': 7, '2w': 14, '1m': 30, '3m': 90, '6m': 180, '9m': 270, '1y': 365
    }
    
    existing_cols = [c for c in shibor_map.keys() if c in shibor_df.columns]
    shibor_df = shibor_df[existing_cols]
    
    # Convert % to decimal
    shibor_df = shibor_df / 100.0
    
    # Fill NAs
    shibor_df.ffill(inplace=True)
    shibor_df.bfill(inplace=True)
    
    # Interpolation Logic
    def _interpld_fun(row):
        y_vals = row.values
        periods = [shibor_map[col] for col in row.index]
        
        # Sort
        sorted_indices = np.argsort(periods)
        periods_sorted = np.array(periods)[sorted_indices]
        y_vals_sorted = y_vals[sorted_indices]
        
        # Dedup
        unique_periods, unique_indices = np.unique(periods_sorted, return_index=True)
        if len(unique_periods) < len(periods_sorted):
             periods_sorted = unique_periods
             y_vals_sorted = y_vals_sorted[unique_indices]
             
        daily_range = np.arange(1, YEARS + 1) # 1 to 365
        
        try:
            # Replaced scipy interp1d with numpy interp (linear)
            interpolated_rates = np.interp(daily_range, periods_sorted, y_vals_sorted)
            return pd.Series(data=interpolated_rates, index=daily_range)
        except Exception as e:
            # print(f"Interpolation failed for {row.name}: {e}")
            return pd.Series(data=np.nan, index=daily_range)

    print("Interpolating Shibor data...")
    interpld_shibor = shibor_df.apply(_interpld_fun, axis=1)
    interpld_shibor.dropna(how='all', inplace=True)
    
    # Ensure column names are integers
    interpld_shibor.columns = interpld_shibor.columns.astype(int)
    
    return interpld_shibor
