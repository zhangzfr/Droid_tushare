import duckdb
import pandas as pd
import streamlit as st

# Database paths
STOCK_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'

def get_stock_db_connection():
    """Establish connection to stock basic info DuckDB."""
    try:
        conn = duckdb.connect(STOCK_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to stock database at {STOCK_DB_PATH}: {e}")
        return None

@st.cache_data
def get_listing_delisting_stats():
    """Calculate monthly listing and delisting counts."""
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Load dates
        df = conn.execute("""
            SELECT ts_code, list_date, delist_date
            FROM stock_basic
        """).fetchdf()
        
        if df.empty:
            return pd.DataFrame(columns=['month', 'listings', 'delistings'])
            
        # Parse dates YYYYMMDD
        df['list_date'] = pd.to_datetime(df['list_date'], format='%Y%m%d', errors='coerce')
        df['delist_date'] = pd.to_datetime(df['delist_date'], format='%Y%m%d', errors='coerce')
        
        # Monthly listings
        listings = df.dropna(subset=['list_date']).copy()
        listings['month'] = listings['list_date'].dt.to_period('M').dt.to_timestamp()
        list_counts = listings.groupby('month').size().reset_index(name='listings')
        
        # Monthly delistings
        delistings = df.dropna(subset=['delist_date']).copy()
        delistings['month'] = delistings['delist_date'].dt.to_period('M').dt.to_timestamp()
        delist_counts = delistings.groupby('month').size().reset_index(name='delistings')
        
        # Merge
        stats = pd.merge(list_counts, delist_counts, on='month', how='outer').fillna(0)
        stats = stats.sort_values('month')
        
        return stats
        
    except Exception as e:
        st.error(f"Error calculating stats: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_stock_basic_sample(n=1000):
    """Load sample of stock basic info."""
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute(f"SELECT * FROM stock_basic LIMIT {n}").fetchdf()
        return df
    except Exception as e:
        st.error(f"Error loading sample: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
