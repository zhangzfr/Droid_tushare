"""
FX & Commodity Data Loader Module
=================================
Provides data loading functions for the FX Education dashboard.
Connects to tushare_duck_fx.db and loads fx_obasic and fx_daily tables.
"""
import duckdb
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# Database path
FX_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_fx.db'

# Default assets for visualization
DEFAULT_FX_ASSETS = [
    'EURUSD.FXCM',   # Major forex pair
    'USDJPY.FXCM',   # Major forex pair
    'XAUUSD.FXCM',   # Gold
    'USOIL',         # Crude Oil
    'US30',          # Dow Jones
    'NAS100',        # NASDAQ
    'BUND',          # German Bonds
    'USDOLLAR'       # USD Index
]


def get_fx_db_connection():
    """Establish connection to FX DuckDB."""
    try:
        conn = duckdb.connect(FX_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to FX database at {FX_DB_PATH}: {e}")
        return None


@st.cache_data
def load_fx_obasic():
    """
    Fetch all FX basic info from DuckDB.
    Returns DataFrame with ts_code, name, classify, exchange, etc.
    """
    conn = get_fx_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, name, classify, exchange, 
                   min_unit, max_unit, pip, pip_cost, 
                   traget_spread, min_stop_distance, 
                   trading_hours, break_time
            FROM fx_obasic
            ORDER BY classify, ts_code
        """).fetchdf()
    except Exception as e:
        st.error(f"Error fetching fx_obasic: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    return df


@st.cache_data
def get_available_fx_codes():
    """
    Get list of available ts_codes grouped by classification.
    Returns dict: {classify: [ts_code1, ts_code2, ...]}
    """
    conn = get_fx_db_connection()
    if not conn:
        return {}
    
    try:
        df = conn.execute("""
            SELECT ts_code, classify FROM fx_obasic ORDER BY classify, ts_code
        """).fetchdf()
    except Exception as e:
        st.error(f"Error fetching FX codes: {e}")
        return {}
    finally:
        conn.close()

    if df.empty:
        return {}
    
    # Group by classify
    grouped = df.groupby('classify')['ts_code'].apply(list).to_dict()
    return grouped


@st.cache_data
def load_fx_daily(ts_codes: list, start_date: str, end_date: str):
    """
    Fetch daily FX data for specified codes and date range.
    
    Note: fx_obasic may have ts_codes with '.FXCM' suffix, but fx_daily uses
    different conventions based on asset classification:
    - FX: Keep '.FXCM' suffix (e.g., 'EURUSD.FXCM' -> query as 'EURUSD.FXCM')
    - INDEX, FX_BASKET, COMMODITY, BUND: Strip '.FXCM' suffix (e.g., 'US30.FXCM' -> query as 'US30')
    
    This function handles the mapping automatically based on classification.
    
    Args:
        ts_codes: List of ts_code strings (from fx_obasic)
        start_date: Start date in 'YYYYMMDD' format
        end_date: End date in 'YYYYMMDD' format
    
    Returns:
        DataFrame with columns: ts_code, trade_date, mid_close, mid_high, mid_low, mid_open, tick_qty
    """
    if not ts_codes:
        return pd.DataFrame()
    
    conn = get_fx_db_connection()
    if not conn:
        return pd.DataFrame()
    
    # Get classification info for the requested codes
    try:
        obasic_df = conn.execute("""
            SELECT ts_code, classify FROM fx_obasic
        """).fetchdf()
        code_to_classify = dict(zip(obasic_df['ts_code'], obasic_df['classify']))
    except:
        code_to_classify = {}
    
    # Categories that need suffix stripping (fx_daily uses codes without .FXCM for these)
    STRIP_SUFFIX_CATEGORIES = {'INDEX', 'FX_BASKET', 'COMMODITY', 'BUND'}
    
    # Create mapping: db_code -> original_code
    code_mapping = {}
    db_codes = []
    for code in ts_codes:
        classify = code_to_classify.get(code, '')
        
        # Only strip .FXCM suffix for specific categories
        if classify in STRIP_SUFFIX_CATEGORIES and code.endswith('.FXCM'):
            db_code = code.replace('.FXCM', '')
        else:
            db_code = code
        
        db_codes.append(db_code)
        code_mapping[db_code] = code
    
    # Remove duplicates while preserving order
    unique_db_codes = list(dict.fromkeys(db_codes))
    
    placeholders = ",".join(["?"] * len(unique_db_codes))
    
    try:
        query = f"""
            SELECT 
                ts_code, 
                trade_date,
                bid_open, bid_close, bid_high, bid_low,
                ask_open, ask_close, ask_high, ask_low,
                tick_qty
            FROM fx_daily
            WHERE ts_code IN ({placeholders})
              AND trade_date BETWEEN ? AND ?
            ORDER BY ts_code, trade_date
        """
        params = unique_db_codes + [start_date, end_date]
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Error fetching fx_daily: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    # Map database ts_codes back to original codes (with .FXCM suffix if applicable)
    df['ts_code'] = df['ts_code'].map(lambda x: code_mapping.get(x, x))

    # Convert trade_date to datetime
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    # Calculate mid-prices: (bid + ask) / 2
    df['mid_open'] = (df['bid_open'] + df['ask_open']) / 2
    df['mid_high'] = (df['bid_high'] + df['ask_high']) / 2
    df['mid_low'] = (df['bid_low'] + df['ask_low']) / 2
    df['mid_close'] = (df['bid_close'] + df['ask_close']) / 2
    
    # Fill missing values using forward fill per asset
    df = df.sort_values(['ts_code', 'trade_date'])
    df = df.groupby('ts_code', group_keys=False).apply(
        lambda x: x.ffill()
    ).reset_index(drop=True)
    
    return df


def calculate_returns(df: pd.DataFrame, price_col: str = 'mid_close', method: str = 'log'):
    """
    Calculate returns for each asset.
    
    Args:
        df: DataFrame with ts_code, trade_date, and price column
        price_col: Column to use for return calculation
        method: 'log' for log returns, 'simple' for simple returns
    
    Returns:
        DataFrame with added 'return' column
    """
    if df.empty:
        return df
    
    df = df.sort_values(['ts_code', 'trade_date']).copy()
    
    if method == 'log':
        df['return'] = df.groupby('ts_code')[price_col].transform(
            lambda x: np.log(x / x.shift(1))
        )
    else:
        df['return'] = df.groupby('ts_code')[price_col].transform(
            lambda x: (x - x.shift(1)) / x.shift(1)
        )
    
    return df


def calculate_volatility(df: pd.DataFrame, window: int = 20):
    """
    Calculate rolling volatility (standard deviation of returns).
    
    Args:
        df: DataFrame with 'return' column
        window: Rolling window size in days
    
    Returns:
        DataFrame with added 'volatility' column
    """
    if df.empty or 'return' not in df.columns:
        return df
    
    df = df.sort_values(['ts_code', 'trade_date']).copy()
    df['volatility'] = df.groupby('ts_code')['return'].transform(
        lambda x: x.rolling(window=window, min_periods=window//2).std()
    )
    
    return df


def create_price_pivot(df: pd.DataFrame, price_col: str = 'mid_close'):
    """
    Create a pivot table with dates as index and assets as columns.
    
    Args:
        df: DataFrame with ts_code, trade_date, and price column
        price_col: Column to use for pivot values
    
    Returns:
        DataFrame with dates as index, assets as columns
    """
    if df.empty:
        return pd.DataFrame()
    
    pivot = df.pivot_table(
        index='trade_date',
        columns='ts_code',
        values=price_col,
        aggfunc='first'
    )
    
    # Forward fill to handle weekends/holidays
    pivot = pivot.ffill()
    
    return pivot


def create_returns_pivot(df: pd.DataFrame):
    """
    Create a pivot table of returns with dates as index and assets as columns.
    
    Args:
        df: DataFrame with ts_code, trade_date, and return column
    
    Returns:
        DataFrame with dates as index, assets as columns for returns
    """
    if df.empty or 'return' not in df.columns:
        return pd.DataFrame()
    
    pivot = df.pivot_table(
        index='trade_date',
        columns='ts_code',
        values='return',
        aggfunc='first'
    )
    
    return pivot


def calculate_correlation_matrix(df_returns_pivot: pd.DataFrame):
    """
    Calculate correlation matrix from returns pivot table.
    
    Args:
        df_returns_pivot: Pivot table with assets as columns
    
    Returns:
        Correlation matrix DataFrame
    """
    if df_returns_pivot.empty:
        return pd.DataFrame()
    
    return df_returns_pivot.corr()


def calculate_rolling_correlation(df: pd.DataFrame, asset1: str, asset2: str, window: int = 30):
    """
    Calculate rolling correlation between two assets.
    
    Args:
        df: Pivot table of returns with assets as columns
        asset1, asset2: Column names (ts_codes)
        window: Rolling window size
    
    Returns:
        Series with rolling correlation
    """
    if df.empty or asset1 not in df.columns or asset2 not in df.columns:
        return pd.Series()
    
    return df[asset1].rolling(window=window, min_periods=window//2).corr(df[asset2])


def aggregate_monthly(df: pd.DataFrame):
    """
    Aggregate daily data to monthly frequency.
    
    Args:
        df: DataFrame with ts_code, trade_date, mid_close, mid_open, mid_high, mid_low
    
    Returns:
        DataFrame with monthly OHLC, returns, and volatility per asset
    """
    if df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    df['year_month'] = df['trade_date'].dt.to_period('M')
    
    monthly = df.groupby(['ts_code', 'year_month']).agg({
        'mid_open': 'first',
        'mid_high': 'max',
        'mid_low': 'min',
        'mid_close': 'last',
        'tick_qty': 'sum'
    }).reset_index()
    
    # Calculate monthly return
    monthly = monthly.sort_values(['ts_code', 'year_month'])
    monthly['monthly_return'] = monthly.groupby('ts_code')['mid_close'].transform(
        lambda x: x.pct_change()
    )
    
    # Convert period to timestamp for plotting
    monthly['month'] = monthly['year_month'].dt.to_timestamp()
    
    return monthly


def calculate_annualized_stats(df_returns_pivot: pd.DataFrame):
    """
    Calculate annualized return and volatility for each asset.
    
    Args:
        df_returns_pivot: Pivot table of daily returns
    
    Returns:
        DataFrame with mean_return, volatility, annualized_return, annualized_vol, sharpe
    """
    if df_returns_pivot.empty:
        return pd.DataFrame()
    
    # Assuming ~252 trading days
    stats = pd.DataFrame({
        'mean_daily_return': df_returns_pivot.mean(),
        'daily_volatility': df_returns_pivot.std(),
        'count': df_returns_pivot.count()
    })
    
    stats['annualized_return'] = stats['mean_daily_return'] * 252
    stats['annualized_volatility'] = stats['daily_volatility'] * np.sqrt(252)
    stats['sharpe_ratio'] = stats['annualized_return'] / stats['annualized_volatility']
    
    return stats.reset_index().rename(columns={'index': 'ts_code'})
