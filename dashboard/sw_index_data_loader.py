import duckdb
import pandas as pd
import streamlit as st

# Database paths
INDEX_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_index.db'
STOCK_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'

def get_db_connection():
    """Establish connection to index DuckDB."""
    try:
        conn = duckdb.connect(INDEX_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database at {INDEX_DB_PATH}: {e}")
        return None

def get_stock_db_connection():
    """Establish connection to stock DuckDB."""
    try:
        conn = duckdb.connect(STOCK_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database at {STOCK_DB_PATH}: {e}")
        return None

@st.cache_data
def get_sw_hierarchy():
    """
    Fetch Shenwan Index Hierarchy (L1 -> L2 -> L3) mapping.
    Returns dictionaries for different levels.
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Get unique L1-L2-L3 relationships
        # l1: code, name
        # l2: code, name, parent(l1)
        # l3: code, name, parent(l2)
        df_all = conn.execute("""
            SELECT DISTINCT 
                l1_code, l1_name, 
                l2_code, l2_name, 
                l3_code, l3_name
            FROM sw_index_member_all
            WHERE last_updated IS NOT NULL -- filter usually active ones if possible, but structure changes rarely
        """).fetchdf()
        
    except Exception as e:
        st.error(f"Error fetching hierarchy: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return df_all

@st.cache_data
def get_sw_members():
    """
    Fetch Shenwan Index Member All data (L3 -> Stock mapping).
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT 
                l1_code, l1_name, 
                l2_code, l2_name, 
                l3_code, l3_name,
                ts_code, name
            FROM sw_index_member_all
            WHERE is_new = 'Y' -- only current members
        """).fetchdf()
    except Exception as e:
        st.error(f"Error fetching members: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return df

@st.cache_data
def load_sw_daily_data(date_str: str, codes: list):
    """
    Fetch daily data (pct_change, amount) for specific index codes on a specific date.
    
    Args:
        date_str (str): YYYYMMDD
        codes (list): List of index (ts_code) to fetch
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    if not codes:
        return pd.DataFrame()
        
    # DuckDB list handling
    # Create temp table or direct IN clause if list isn't too huge. 
    # SW Indices count: L1 ~31, L2 ~134, L3 ~346. Total ~500. IN clause is fine.
    
    codes_placeholder = ",".join([f"'{c}'" for c in codes])
    
    try:
        query = f"""
            SELECT ts_code, name, pct_change, amount, pe, pb
            FROM sw_daily
            WHERE trade_date = '{date_str}'
              AND ts_code IN ({codes_placeholder})
        """
        df = conn.execute(query).fetchdf()
        
    except Exception as e:
        st.error(f"Error fetching SW daily data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return df


@st.cache_data
def load_stock_daily_data(date_str: str, codes: list):
    """
    Fetch daily data for stocks.
    """
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    if not codes:
        return pd.DataFrame()
        
    # Split codes into chunks if too many? DuckDB handles large IN clauses well usually.
    # But just in case, let's just do it.
    
    codes_placeholder = ",".join([f"'{c}'" for c in codes])
    
    try:
        # We need name from stock_basic? sw_index_member already has name.
        # But stock daily table doesn't usually have name always? Wait, user provided daily schema:
        # 0 ts_code, 1 trade_date, 2 name ...
        # So 'name' IS in daily table!
        
        query = f"""
            SELECT ts_code, pct_chg, amount
            FROM daily
            WHERE trade_date = '{date_str}'
              AND ts_code IN ({codes_placeholder})
        """
        df = conn.execute(query).fetchdf()
        
        # Rename pct_chg to pct_change to match SW daily format for consistent plotting downstream
        df = df.rename(columns={'pct_chg': 'pct_change'})
        
    except Exception as e:
        st.error(f"Error fetching stock daily data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return df


@st.cache_data
def get_stocks_for_l3(l3_code: str):
    """
    Get the list of stock codes that belong to a specific L3 industry.
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, name
            FROM sw_index_member_all
            WHERE l3_code = ? AND is_new = 'Y'
        """, [l3_code]).fetchdf()
        return df
    except Exception as e:
        st.error(f"Error fetching stocks for L3 {l3_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data
def load_stocks_by_l3(date_str: str, l3_code: str):
    """
    Fetch daily stock data for stocks belonging to a specific L3 industry.
    This is much faster than loading all stocks since L3 typically has 15-50 stocks.
    """
    # First get the stock codes for this L3
    df_stocks = get_stocks_for_l3(l3_code)
    if df_stocks.empty:
        return pd.DataFrame()
    
    stock_codes = df_stocks['ts_code'].tolist()
    
    # Now fetch daily data for just these stocks
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    codes_placeholder = ",".join([f"'{c}'" for c in stock_codes])
    
    try:
        query = f"""
            SELECT ts_code, pct_chg, amount
            FROM daily
            WHERE trade_date = '{date_str}'
              AND ts_code IN ({codes_placeholder})
        """
        df_daily = conn.execute(query).fetchdf()
        df_daily = df_daily.rename(columns={'pct_chg': 'pct_change'})
        
        # Merge with stock names from the member table
        df_result = df_daily.merge(df_stocks, on='ts_code', how='left')
        
    except Exception as e:
        st.error(f"Error fetching stock daily data for L3 {l3_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    return df_result


@st.cache_data
def load_top_stocks(date_str: str, top_n: int = 100):
    """
    D1 Optimization: Load only top N stocks by transaction amount.
    Much faster than loading all stocks.
    """
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = f"""
            SELECT ts_code, pct_chg, amount
            FROM daily
            WHERE trade_date = '{date_str}'
            ORDER BY amount DESC
            LIMIT {top_n}
        """
        df = conn.execute(query).fetchdf()
        df = df.rename(columns={'pct_chg': 'pct_change'})
        
    except Exception as e:
        st.error(f"Error fetching top stocks: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    # Get stock names from sw_index_member_all
    df_members = get_sw_members()
    if not df_members.empty:
        name_map = dict(zip(df_members['ts_code'], df_members['name']))
        l3_map = dict(zip(df_members['ts_code'], df_members['l3_name']))
        df['name'] = df['ts_code'].map(name_map)
        df['l3_name'] = df['ts_code'].map(l3_map)
    
    return df


@st.cache_data
def get_stocks_for_l2(l2_code: str):
    """
    Get the list of stock codes that belong to a specific L2 industry (all L3s under it).
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, name, l3_code, l3_name
            FROM sw_index_member_all
            WHERE l2_code = ? AND is_new = 'Y'
        """, [l2_code]).fetchdf()
        return df
    except Exception as e:
        st.error(f"Error fetching stocks for L2 {l2_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data
def load_stocks_by_l2(date_str: str, l2_code: str):
    """
    D2 Optimization: Load all stocks under a specific L2 industry.
    When user selects L2, auto-load all stocks in all L3s under it.
    L2 typically has ~100-300 stocks, much faster than all 5000.
    """
    df_stocks = get_stocks_for_l2(l2_code)
    if df_stocks.empty:
        return pd.DataFrame()
    
    stock_codes = df_stocks['ts_code'].tolist()
    
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    codes_placeholder = ",".join([f"'{c}'" for c in stock_codes])
    
    try:
        query = f"""
            SELECT ts_code, pct_chg, amount
            FROM daily
            WHERE trade_date = '{date_str}'
              AND ts_code IN ({codes_placeholder})
        """
        df_daily = conn.execute(query).fetchdf()
        df_daily = df_daily.rename(columns={'pct_chg': 'pct_change'})
        
        # Merge with stock names and L3 info
        df_result = df_daily.merge(df_stocks, on='ts_code', how='left')
        
    except Exception as e:
        st.error(f"Error fetching stock data for L2 {l2_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    return df_result


@st.cache_data
def get_stocks_for_l1(l1_code: str):
    """
    Get the list of stock codes that belong to a specific L1 industry.
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, name, l2_code, l2_name, l3_code, l3_name
            FROM sw_index_member_all
            WHERE l1_code = ? AND is_new = 'Y'
        """, [l1_code]).fetchdf()
        return df
    except Exception as e:
        st.error(f"Error fetching stocks for L1 {l1_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data
def load_stocks_by_l1(date_str: str, l1_code: str):
    """
    Load all stocks under a specific L1 industry.
    L1 typically has ~300-500 stocks, much faster than all 5000.
    """
    df_stocks = get_stocks_for_l1(l1_code)
    if df_stocks.empty:
        return pd.DataFrame()
    
    stock_codes = df_stocks['ts_code'].tolist()
    
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    codes_placeholder = ",".join([f"'{c}'" for c in stock_codes])
    
    try:
        query = f"""
            SELECT ts_code, pct_chg, amount
            FROM daily
            WHERE trade_date = '{date_str}'
              AND ts_code IN ({codes_placeholder})
        """
        df_daily = conn.execute(query).fetchdf()
        df_daily = df_daily.rename(columns={'pct_chg': 'pct_change'})
        
        # Merge with stock info (name, L2, L3)
        df_result = df_daily.merge(df_stocks, on='ts_code', how='left')
        
    except Exception as e:
        st.error(f"Error fetching stock data for L1 {l1_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    return df_result


@st.cache_data(ttl=3600)
def calculate_market_width(end_date_str: str, days: int = 30, ma_period: int = 20, level: str = 'L1'):
    """
    Calculate market width for each industry over a date range.
    Market width = % of stocks with close > MA(ma_period)
    
    Args:
        end_date_str: End date in YYYYMMDD format
        days: Number of trading days to display
        ma_period: MA period (e.g., 20, 50, 90)
        level: 'L1', 'L2', or 'L3'
    
    Returns:
        DataFrame with columns: trade_date, index_code, index_name, width_ratio
    """
    # 1. Get industry member mapping
    df_members = get_sw_members()
    if df_members.empty:
        return pd.DataFrame()
    
    # Get unique stock codes
    stock_codes = df_members['ts_code'].unique().tolist()
    
    # Determine which level column to use
    if level == 'L1':
        code_col, name_col = 'l1_code', 'l1_name'
    elif level == 'L2':
        code_col, name_col = 'l2_code', 'l2_name'
    else:
        code_col, name_col = 'l3_code', 'l3_name'
    
    # 2. Fetch historical stock data (need ma_period + days of data)
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    codes_placeholder = ",".join([f"'{c}'" for c in stock_codes])
    
    try:
        # Fetch enough data for MA calculation
        query = f"""
            SELECT ts_code, trade_date, close
            FROM daily
            WHERE trade_date <= '{end_date_str}'
            ORDER BY trade_date DESC
            LIMIT {len(stock_codes) * (days + ma_period + 10)}
        """
        df_daily = conn.execute(query).fetchdf()
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if df_daily.empty:
        return pd.DataFrame()
    
    # 3. Calculate MA for each stock
    df_daily = df_daily.sort_values(['ts_code', 'trade_date'])
    df_daily['ma'] = df_daily.groupby('ts_code')['close'].transform(
        lambda x: x.rolling(window=ma_period, min_periods=ma_period).mean()
    )
    df_daily['above_ma'] = (df_daily['close'] > df_daily['ma']).astype(int)
    
    # 4. Get the target date range
    trade_dates = df_daily['trade_date'].drop_duplicates().sort_values(ascending=False).head(days).tolist()
    df_daily = df_daily[df_daily['trade_date'].isin(trade_dates)]
    
    # 5. Merge with industry info
    df_merged = df_daily.merge(df_members[['ts_code', code_col, name_col]], on='ts_code', how='left')
    df_merged = df_merged.dropna(subset=[code_col])
    
    # 6. Calculate width ratio for each industry on each date
    grouped = df_merged.groupby(['trade_date', code_col, name_col]).agg(
        total_stocks=('above_ma', 'count'),
        above_ma_count=('above_ma', 'sum')
    ).reset_index()
    
    grouped['width_ratio'] = (grouped['above_ma_count'] / grouped['total_stocks'] * 100).round(1)
    grouped = grouped.rename(columns={code_col: 'index_code', name_col: 'index_name'})
    
    return grouped[['trade_date', 'index_code', 'index_name', 'width_ratio']]
