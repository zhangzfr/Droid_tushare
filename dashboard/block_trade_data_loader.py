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
def load_market_block_activity(start_date: str, end_date: str):
    """
    Fetch market-wide daily block trade totals.
    """
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = f"""
            SELECT trade_date, 
                   COUNT(*) as trade_count,
                   SUM(vol) as total_vol,
                   SUM(amount) as total_amount
            FROM block_trade
            WHERE trade_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY trade_date
            ORDER BY trade_date ASC
        """
        df = conn.execute(query).fetchdf()
        if not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df
    except Exception as e:
        st.error(f"Error loading market block activity: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_top_block_trades(date_str: str, limit: int = 20):
    """
    Fetch stocks with highest block trade amount on a specific date.
    """
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Join with stock names if possible, but let's do it simply first
        query = f"""
            SELECT ts_code, 
                   COUNT(*) as trade_count,
                   SUM(vol) as total_vol,
                   SUM(amount) as total_amount,
                   AVG(price) as avg_price
            FROM block_trade
            WHERE trade_date = '{date_str}'
            GROUP BY ts_code
            ORDER BY total_amount DESC
            LIMIT {limit}
        """
        df = conn.execute(query).fetchdf()
        
        # Add names
        if not df.empty:
            names_df = load_stock_names(df['ts_code'].tolist())
            df = df.merge(names_df, on='ts_code', how='left')
            
        return df
    except Exception as e:
        st.error(f"Error loading top block trades: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_stock_block_history(ts_code: str, start_date: str, end_date: str):
    """
    Fetch block trade history for a specific stock, including daily close for discount calculation.
    """
    ref_conn = get_ref_db_connection()
    if not ref_conn:
        return pd.DataFrame()
    
    try:
        # 1. Fetch block trade records
        query_block = f"""
            SELECT trade_date, price as block_price, vol, amount, buyer, seller
            FROM block_trade
            WHERE ts_code = '{ts_code}'
              AND trade_date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY trade_date ASC
        """
        df_block = ref_conn.execute(query_block).fetchdf()
        
        if df_block.empty:
            return pd.DataFrame()
            
        # 2. Fetch daily close prices for those dates to calculate discount
        stock_conn = get_stock_db_connection()
        if stock_conn:
            dates = df_block['trade_date'].unique().tolist()
            dates_str = ",".join([f"'{d}'" for d in dates])
            query_daily = f"""
                SELECT trade_date, close as daily_close
                FROM daily
                WHERE ts_code = '{ts_code}'
                  AND trade_date IN ({dates_str})
            """
            df_daily = stock_conn.execute(query_daily).fetchdf()
            stock_conn.close()
            
            # Merge
            df_merged = df_block.merge(df_daily, on='trade_date', how='left')
            
            # Calculate discount: (daily_close - block_price) / daily_close
            df_merged['discount_rate'] = (df_merged['daily_close'] - df_merged['block_price']) / df_merged['daily_close'] * 100
            
            df_merged['trade_date'] = pd.to_datetime(df_merged['trade_date'])
            return df_merged
            
        return df_block
    except Exception as e:
        st.error(f"Error loading stock block history: {e}")
        return pd.DataFrame()
    finally:
        ref_conn.close()

@st.cache_data
def load_stock_names(ts_codes: list):
    """Utility to load stock names for a list of codes."""
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        placeholders = ",".join(["?"] * len(ts_codes))
        df = conn.execute(f"SELECT ts_code, name FROM stock_basic WHERE ts_code IN ({placeholders})", ts_codes).fetchdf()
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_broker_activity(start_date: str, end_date: str, limit: int = 20):
    """
    Fetch top buyer/seller brokers by total amount.
    """
    conn = get_ref_db_connection()
    if not conn:
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        query_buyer = f"""
            SELECT buyer as broker, SUM(amount) as total_amount, COUNT(*) as trade_count
            FROM block_trade
            WHERE trade_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY buyer
            ORDER BY total_amount DESC
            LIMIT {limit}
        """
        df_buyer = conn.execute(query_buyer).fetchdf()
        
        query_seller = f"""
            SELECT seller as broker, SUM(amount) as total_amount, COUNT(*) as trade_count
            FROM block_trade
            WHERE trade_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY seller
            ORDER BY total_amount DESC
            LIMIT {limit}
        """
        df_seller = conn.execute(query_seller).fetchdf()
        
        return df_buyer, df_seller
    except Exception as e:
        st.error(f"Error loading broker activity: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()
