import duckdb
import pandas as pd
import yaml
import streamlit as st

# Hardcoded path since YAML config is inaccessible in this environment
MARCO_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_marco.db'

def get_db_connection():
    """Establish connection to DuckDB."""
    try:
        conn = duckdb.connect(MARCO_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database at {MARCO_DB_PATH}: {e}")
        return None

@st.cache_data
def load_pmi_data():
    """Fetch and preprocess PMI data from DuckDB."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("SELECT * FROM cn_pmi").fetchdf()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    # Preprocessing
    # Convert 'month' (e.g., 202301) to datetime
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'].astype(str) + '01', format='%Y%m%d', errors='coerce')
    
    # Ensure numeric columns are actually numeric
    # List of columns to convert (add more as needed based on inspection)
    numeric_cols = [col for col in df.columns if col.startswith('pmi')]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
