import duckdb
import pandas as pd
import yaml
import streamlit as st

# Hardcoded path since YAML config is inaccessible in this environment
MACRO_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_macro.db'

def get_db_connection():
    """Establish connection to DuckDB."""
    try:
        conn = duckdb.connect(MACRO_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database at {MACRO_DB_PATH}: {e}")
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
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('month')

@st.cache_data
def load_sf_data():
    """Fetch and preprocess Social Financing data from DuckDB."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("SELECT * FROM sf_month").fetchdf()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'].astype(str) + '01', format='%Y%m%d', errors='coerce')
    
    # Preprocessing numeric columns
    numeric_cols = ['inc_month', 'inc_cumval', 'stk_endval']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('month')

@st.cache_data
def load_m_data():
    """Fetch and preprocess Money Supply data from DuckDB."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("SELECT * FROM cn_m").fetchdf()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'].astype(str) + '01', format='%Y%m%d', errors='coerce')
    
    # Preprocessing numeric columns
    numeric_cols = ['m0', 'm0_yoy', 'm0_mom', 'm1', 'm1_yoy', 'm1_mom', 'm2', 'm2_yoy', 'm2_mom']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('month')


@st.cache_data
def load_gdp_data():
    """Fetch and preprocess GDP data from DuckDB."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("SELECT * FROM cn_gdp").fetchdf()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    # Convert 'quarter' (e.g., 2023Q1 or 20230101) to datetime
    if 'quarter' in df.columns:
        # Helper to convert Tushare quarter string to datetime (end of quarter)
        def parse_quarter(q_str):
            if pd.isna(q_str): return pd.NaT
            q_str = str(q_str)
            try:
                # Try YYYYQN format (e.g. 2023Q1)
                if 'Q' in q_str.upper():
                    return pd.Period(q_str, freq='Q').to_timestamp(how='end')
                # Try YYYYMMDD format (e.g. 20230101)
                else:
                    return pd.to_datetime(q_str, format='%Y%m%d', errors='coerce')
            except:
                return pd.NaT
        
        df['quarter_date'] = df['quarter'].apply(parse_quarter)

    # Preprocessing numeric columns
    numeric_cols = ['gdp', 'gdp_yoy', 'pi', 'pi_yoy', 'si', 'si_yoy', 'ti', 'ti_yoy']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('quarter_date')
