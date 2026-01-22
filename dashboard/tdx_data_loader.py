"""
TDX Index Data Loader

Handles data loading from TDX DuckDB database containing:
- tdx_daily: 板块行情 (sector quotes)
- tdx_index: 板块信息 (sector metadata)  
- tdx_member: 成分股 (constituents)
"""

import duckdb
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

# Database path
TDX_DB_PATH = "/Users/robert/Developer/DuckDB/tushare_duck_index.db"


def get_tdx_db_connection():
    """
    Get connection to TDX DuckDB database.
    
    Returns:
        duckdb.DuckDBPyConnection or None
    """
    try:
        db_path = Path(TDX_DB_PATH)
        if not db_path.exists():
            st.error(f"TDX database not found at {TDX_DB_PATH}")
            return None
        return duckdb.connect(str(db_path), read_only=True)
    except Exception as e:
        st.error(f"Failed to connect to TDX database: {e}")
        return None


@st.cache_data(ttl=1800)
def load_tdx_daily(limit_days: int = 252, idx_type_filter: str = None) -> pd.DataFrame:
    """
    Load tdx_daily (板块行情) data.
    
    Args:
        limit_days: Number of recent trading days to load
        idx_type_filter: Filter by idx_type ('行业板块', '概念板块', '地区板块', '风格板块')
        
    Returns:
        DataFrame with columns: ts_code, trade_date, close, pct_change, vol_ratio, 
                                bm_net, limit_up_num, pe, pb, float_mv, etc.
    """
    conn = get_tdx_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Calculate date threshold
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=limit_days * 1.5)).strftime("%Y%m%d")
        
        # Base query
        query = """
            SELECT d.*
            FROM tdx_daily d
        """
        
        # Add idx_type filter if specified
        if idx_type_filter:
            query += """
                INNER JOIN (
                    SELECT DISTINCT ts_code, idx_type
                    FROM tdx_index
                    WHERE idx_type = ?
                ) i ON d.ts_code = i.ts_code
                WHERE d.trade_date >= ?
                AND d.trade_date <= ?
            """
            params = [idx_type_filter, start_date, end_date]
        else:
            query += """
                WHERE d.trade_date >= ?
                AND d.trade_date <= ?
            """
            params = [start_date, end_date]
        
        query += " ORDER BY d.trade_date DESC, d.ts_code"
        
        df = conn.execute(query, params).fetchdf()
        
        # Preprocess
        df = preprocess_tdx_daily(df)
        
        return df
        
    except Exception as e:
        st.error(f"Failed to load tdx_daily: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_tdx_index() -> pd.DataFrame:
    """
    Load tdx_index (板块信息) metadata.
    
    Returns:
        DataFrame with columns: ts_code, name, idx_type, idx_count, float_mv, etc.
    """
    conn = get_tdx_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
            SELECT DISTINCT ts_code, name, idx_type, idx_count, 
                   total_share, float_share, total_mv, float_mv
            FROM tdx_index
            ORDER BY idx_type, name
        """
        
        df = conn.execute(query).fetchdf()
        
        # Add display name with emoji
        idx_type_emoji = {
            '行业板块': '🏭',
            '概念板块': '💡',
            '地区板块': '🗺️',
            '风格板块': '🎨'
        }
        df['display_name'] = df.apply(
            lambda x: f"{idx_type_emoji.get(x['idx_type'], '')} {x['name']}", 
            axis=1
        )
        
        return df
        
    except Exception as e:
        st.error(f"Failed to load tdx_index: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_tdx_member(ts_code: str = None, trade_date: str = None, limit: int = 5000) -> pd.DataFrame:
    """
    Load tdx_member (成分股) data.
    
    Args:
        ts_code: Filter by specific index code
        trade_date: Filter by trade date (YYYYMMDD format)
        limit: Maximum rows to return (default 5000 to handle 17M records)
        
    Returns:
        DataFrame with columns: ts_code, trade_date, con_code, con_name
    """
    conn = get_tdx_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = "SELECT ts_code, trade_date, con_code, con_name FROM tdx_member WHERE 1=1"
        params = []
        
        if ts_code:
            query += " AND ts_code = ?"
            params.append(ts_code)
        
        if trade_date:
            query += " AND trade_date = ?"
            params.append(trade_date)
        
        query += f" ORDER BY trade_date DESC LIMIT {limit}"
        
        df = conn.execute(query, params).fetchdf()
        
        return df
        
    except Exception as e:
        st.error(f"Failed to load tdx_member: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def preprocess_tdx_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess tdx_daily data:
    - Convert pe/pb from object to float
    - Parse trade_date to datetime
    - Handle NaN values
    - Filter outliers
    
    Args:
        df: Raw tdx_daily DataFrame
        
    Returns:
        Preprocessed DataFrame
    """
    if df.empty:
        return df
    
    # Convert trade_date to datetime
    df['trade_date_dt'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    # Convert pe/pb from object to float (handle non-numeric values)
    for col in ['pe', 'pb']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Filter extreme outliers (pe>1000 or pb>50)
            if col == 'pe':
                df.loc[df[col] > 1000, col] = pd.NA
            elif col == 'pb':
                df.loc[df[col] > 50, col] = pd.NA
    
    # Ensure numeric columns are float
    numeric_cols = ['pct_change', 'vol_ratio', 'turnover_rate', 'swing', 
                    'bm_net', 'bm_buy_net', 'bm_ratio', 'float_mv']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Fill NaN in capital flow fields with 0 (約50%覆盖率)
    for col in ['bm_net', 'bm_buy_net', 'bm_ratio']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df


@st.cache_data(ttl=3600)
def get_idx_type_stats() -> dict:
    """
    Get statistics for each idx_type.
    
    Returns:
        Dict with idx_type as key and count as value
    """
    df_index = load_tdx_index()
    if df_index.empty:
        return {}
    
    stats = df_index.groupby('idx_type').size().to_dict()
    return stats


@st.cache_data(ttl=1800)
def get_latest_trade_date() -> str:
    """
    Get the latest trade_date from tdx_daily.
    
    Returns:
        Latest trade_date in YYYYMMDD format
    """
    conn = get_tdx_db_connection()
    if not conn:
        return datetime.now().strftime("%Y%m%d")
    
    try:
        query = "SELECT MAX(trade_date) as max_date FROM tdx_daily"
        result = conn.execute(query).fetchone()
        return result[0] if result and result[0] else datetime.now().strftime("%Y%m%d")
    except:
        return datetime.now().strftime("%Y%m%d")
    finally:
        conn.close()
