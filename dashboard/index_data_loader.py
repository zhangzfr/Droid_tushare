import duckdb
import pandas as pd
import streamlit as st

# Database paths
INDEX_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_index.db'
INDEX_WEIGHT_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_index_weight.db'


def get_index_db_connection():
    """Establish connection to index info DuckDB."""
    try:
        conn = duckdb.connect(INDEX_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to index database at {INDEX_DB_PATH}: {e}")
        return None


def get_weight_db_connection():
    """Establish connection to index weight DuckDB."""
    try:
        conn = duckdb.connect(INDEX_WEIGHT_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to weight database at {INDEX_WEIGHT_DB_PATH}: {e}")
        return None


@st.cache_data
def load_index_basic():
    """Fetch all index basic info from DuckDB."""
    conn = get_index_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, name, fullname, market, publisher, index_type, category,
                   base_date, base_point, list_date, weight_rule, "desc", exp_date
            FROM index_basic
            ORDER BY ts_code
        """).fetchdf()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    return df


@st.cache_data
def get_indices_with_weight_data():
    """Get list of index codes that have weight data available."""
    conn = get_weight_db_connection()
    if not conn:
        return []
    
    try:
        result = conn.execute("""
            SELECT DISTINCT index_code FROM index_weight ORDER BY index_code
        """).fetchdf()
        return result['index_code'].tolist()
    except Exception as e:
        st.error(f"Error fetching indices with weight: {e}")
        return []
    finally:
        conn.close()


@st.cache_data
def load_index_weight_for_index(index_code: str):
    """Load all weight data for a specific index."""
    conn = get_weight_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT index_code, con_code, trade_date, weight
            FROM index_weight
            WHERE index_code = ?
            ORDER BY trade_date DESC, con_code
        """, [index_code]).fetchdf()
    except Exception as e:
        st.error(f"Error fetching weight for {index_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    return df


@st.cache_data
def get_available_trade_dates(index_code: str):
    """Get distinct trade dates for an index, sorted descending."""
    conn = get_weight_db_connection()
    if not conn:
        return []
    
    try:
        result = conn.execute("""
            SELECT DISTINCT trade_date FROM index_weight
            WHERE index_code = ?
            ORDER BY trade_date DESC
        """, [index_code]).fetchdf()
        return result['trade_date'].tolist()
    except Exception as e:
        st.error(f"Error fetching dates: {e}")
        return []
    finally:
        conn.close()


@st.cache_data
def get_constituents_for_date(index_code: str, trade_date: str):
    """Get constituent codes and weights for a specific date."""
    conn = get_weight_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT con_code, weight
            FROM index_weight
            WHERE index_code = ? AND trade_date = ?
            ORDER BY weight DESC
        """, [index_code, trade_date]).fetchdf()
    except Exception as e:
        st.error(f"Error fetching constituents: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    return df


@st.cache_data
def get_constituent_count_per_date(index_code: str):
    """Get count of constituents per trade date for an index."""
    conn = get_weight_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT trade_date, COUNT(DISTINCT con_code) as constituent_count
            FROM index_weight
            WHERE index_code = ?
            GROUP BY trade_date
            ORDER BY trade_date
        """, [index_code]).fetchdf()
    except Exception as e:
        st.error(f"Error fetching constituent counts: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    return df
