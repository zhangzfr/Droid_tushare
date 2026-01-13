import duckdb
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Database paths
# Note: From settings.yaml, pledge data is in tushare_duck_ref.db
REF_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_ref.db'
STOCK_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'

def get_ref_db_connection():
    """Establish connection to reference DuckDB."""
    try:
        conn = duckdb.connect(REF_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to reference database: {e}")
        return None

def get_stock_db_connection():
    """Establish connection to stock DuckDB (for names)."""
    try:
        conn = duckdb.connect(STOCK_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to stock database: {e}")
        return None

@st.cache_data
def get_pledge_stat_top(limit=50):
    """Fetch top stocks by pledge ratio."""
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Get latest data for each stock
        query = f"""
            SELECT p1.ts_code, p1.end_date, p1.pledge_count, p1.unrest_pledge, 
                   p1.rest_pledge, p1.total_share, p1.pledge_ratio
            FROM pledge_stat p1
            INNER JOIN (
                SELECT ts_code, MAX(end_date) as max_date
                FROM pledge_stat
                GROUP BY ts_code
            ) p2 ON p1.ts_code = p2.ts_code AND p1.end_date = p2.max_date
            ORDER BY p1.pledge_ratio DESC
            LIMIT {limit}
        """
        df = conn.execute(query).fetchdf()
        
        # Merge with stock names
        names_df = get_stock_names()
        if not names_df.empty:
            df = df.merge(names_df, on='ts_code', how='left')
            
        return df
    except Exception as e:
        st.error(f"Error fetching pledge stats: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def get_stock_names():
    """Fetch stock names from stock_basic."""
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute("SELECT ts_code, name FROM stock_basic").fetchdf()
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def get_stock_pledge_history(ts_code):
    """Fetch pledge ratio history for a specific stock."""
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(f"""
            SELECT end_date, pledge_ratio, pledge_count
            FROM pledge_stat
            WHERE ts_code = '{ts_code}'
            ORDER BY end_date ASC
        """).fetchdf()
        df['end_date'] = pd.to_datetime(df['end_date'])
        return df
    except Exception as e:
        st.error(f"Error fetching history for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def get_pledge_details(ts_code=None, limit=100):
    """Fetch pledge details."""
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        where_clause = f"WHERE ts_code = '{ts_code}'" if ts_code else ""
        query = f"""
            SELECT ts_code, ann_date, holder_name, pledge_amount, 
                   start_date, end_date, is_release, release_date, 
                   pledgor, holding_amount, pledged_amount, 
                   p_total_ratio, h_total_ratio, is_buyback
            FROM pledge_detail
            {where_clause}
            ORDER BY ann_date DESC
            LIMIT {limit}
        """
        df = conn.execute(query).fetchdf()
        
        # Convert dates
        for col in ['ann_date', 'start_date', 'end_date', 'release_date']:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
        # Merge names if not stock-specific (optional, for global list)
        if not ts_code:
            names_df = get_stock_names()
            if not names_df.empty:
                df = df.merge(names_df, on='ts_code', how='left')
                
        return df
    except Exception as e:
        st.error(f"Error fetching details: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def get_pledge_industry_distribution():
    """Aggregated industry view (needs industry from stock_basic)."""
    # This involves joining across two databases
    # DuckDB can ATTACH databases
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        conn.execute(f"ATTACH '{STOCK_DB_PATH}' AS stock_db")
        query = """
            WITH latest_stat AS (
                SELECT p1.ts_code, p1.pledge_ratio, p1.unrest_pledge, p1.rest_pledge
                FROM pledge_stat p1
                INNER JOIN (
                    SELECT ts_code, MAX(end_date) as max_date
                    FROM pledge_stat
                    GROUP BY ts_code
                ) p2 ON p1.ts_code = p2.ts_code AND p1.end_date = p2.max_date
            )
            SELECT b.industry, 
                   COUNT(*) as stock_count,
                   AVG(s.pledge_ratio) as avg_pledge_ratio,
                   SUM(s.unrest_pledge + s.rest_pledge) as total_pledged_shares
            FROM latest_stat s
            JOIN stock_db.stock_basic b ON s.ts_code = b.ts_code
            WHERE b.industry IS NOT NULL
            GROUP BY b.industry
            ORDER BY avg_pledge_ratio DESC
        """
        df = conn.execute(query).fetchdf()
        return df
    except Exception as e:
        st.error(f"Error fetching industry distribution: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
