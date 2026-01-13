import duckdb
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Database paths
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
    """Establish connection to stock DuckDB."""
    try:
        conn = duckdb.connect(STOCK_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to stock database: {e}")
        return None

@st.cache_data
def get_combined_risk_data(start_date: str, end_date: str):
    """
    Fetch and combine Pledge Ratio and Block Trade Selling Pressure.
    
    Returns DataFrame with:
    - ts_code, name, industry
    - pledge_ratio, pledge_count
    - block_trade_vol, block_trade_amount, avg_discount, trade_count
    - risk_score (calculated)
    """
    ref_conn = get_ref_db_connection()
    if not ref_conn:
        return pd.DataFrame()
        
    try:
        # 1. Get Stock Basic Info (attach stock db)
        ref_conn.execute(f"ATTACH '{STOCK_DB_PATH}' AS stock_db")
        
        # 2. Get Latest Pledge Stats
        # Use subquery to get latest date per stock
        pledge_query = """
            SELECT p1.ts_code, p1.pledge_ratio, p1.pledge_count, p1.unrest_pledge
            FROM pledge_stat p1
            INNER JOIN (
                SELECT ts_code, MAX(end_date) as max_date
                FROM pledge_stat
                GROUP BY ts_code
            ) p2 ON p1.ts_code = p2.ts_code AND p1.end_date = p2.max_date
        """
        
        # 3. Get Aggregated Block Trade Stats for the period
        block_query = f"""
            SELECT ts_code, 
                   SUM(vol) as block_vol,
                   SUM(amount) as block_amount,
                   COUNT(*) as block_count,
                   AVG(price) as avg_block_price
            FROM block_trade
            WHERE trade_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY ts_code
        """
        
        # 4. Combine Everything
        combined_query = f"""
            WITH 
            latest_pledge AS ({pledge_query}),
            period_block AS ({block_query})
            
            SELECT 
                COALESCE(p.ts_code, b.ts_code) as ts_code,
                s.name,
                s.industry,
                COALESCE(p.pledge_ratio, 0) as pledge_ratio,
                COALESCE(p.pledge_count, 0) as pledge_count,
                COALESCE(b.block_vol, 0) as block_vol,
                COALESCE(b.block_amount, 0) as block_amount,
                COALESCE(b.block_count, 0) as block_count
            FROM latest_pledge p
            FULL OUTER JOIN period_block b ON p.ts_code = b.ts_code
            LEFT JOIN stock_db.stock_basic s ON COALESCE(p.ts_code, b.ts_code) = s.ts_code
            WHERE p.pledge_ratio > 0 OR b.block_amount > 0
        """
        
        df = ref_conn.execute(combined_query).fetchdf()
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching combined risk data: {e}")
        return pd.DataFrame()
    finally:
        ref_conn.close()

def calculate_risk_score(df: pd.DataFrame):
    """
    Calculate a composite risk score (0-100).
    Simple Logic:
    - Pledge Risk (0-50): Based on ratio (e.g. ratio/100 * 50, capped at 50)
    - Block Risk (0-50): Based on relative volume or just normalized amount ranking
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    # 1. Pledge Score
    # Logically, >50% pledge is very high risk. map 0-60% to 0-50 pts.
    df['pledge_score'] = (df['pledge_ratio'] / 60 * 50).clip(upper=50)
    
    # 2. Block Trade Score
    # This is harder to normalize without total share context. 
    # Use percentile ranking of Amount for now.
    # Top 90th percentile gets 50 pts, linear scale below.
    if df['block_amount'].max() > 0:
        # Use simple rank pct
        df['block_rank'] = df['block_amount'].rank(pct=True)
        df['block_score'] = df['block_rank'] * 50
    else:
        df['block_score'] = 0
        
    df['total_risk_score'] = df['pledge_score'] + df['block_score']
    
    return df
