"""
AA-Share Market Education Data Loading Module
========================
Provide data loading functions for stock basic info and market data。
Connect tushare_duck_basic.db 和 tushare_duck_stock.db。
"""
import duckdb
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# Database Paths
BASIC_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'
STOCK_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'

# Default stock list (popular targets)
DEFAULT_STOCKS = [
    '600460.SH',  # 
    '000776.SZ',  # 
    '300480.SZ',  # 
    '300124.SZ',  # 
    '002129.SH',  # 
]

# Board Mapping
MARKET_NAMES = {
    'Main Board': 'Main Board',
    'ChiNext': 'ChiNext',
    'STAR Market': 'STAR Market',
    'CDR': 'CDR',
    'BES': 'BES'
}

# Listing Status Mapping
STATUS_NAMES = {
    'L': 'Normal',
    'D': 'Delisted',
    'P': 'Suspended'
}


def get_basic_db_connection():
    """Connect basic Database"""
    try:
        conn = duckdb.connect(BASIC_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Connect basic Database Connection Failed: {e}")
        return None


def get_stock_db_connection():
    """Connect stock Database"""
    try:
        conn = duckdb.connect(STOCK_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Connect stock Database Connection Failed: {e}")
        return None


# ============================================================================
# Level 1：Understanding A-Share - 
# ============================================================================

@st.cache_data
def load_stock_basic():
    """
    Load all stock basic information。
    Return fields：ts_code, name, industry, market, exchange, list_status, list_date, area
    """
    conn = get_basic_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, symbol, name, area, industry, market, exchange, 
                   list_status, list_date, delist_date, is_hs
            FROM stock_basic
            ORDER BY ts_code
        """).fetchdf()
    except Exception as e:
        st.error(f"Load stock_basic 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    # Add status name in Chinese
    df['status_name'] = df['list_status'].map(STATUS_NAMES).fillna('Unknown')
    
    return df


@st.cache_data
def load_stock_company():
    """
    Load company detailed information。
    """
    conn = get_basic_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("""
            SELECT ts_code, com_name, exchange, chairman, manager, 
                   reg_capital, setup_date, province, city, employees
            FROM stock_company
            ORDER BY ts_code
        """).fetchdf()
    except Exception as e:
        st.error(f"Load stock_company 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    return df


@st.cache_data
def get_market_summary(df_basic: pd.DataFrame):
    """
    Calculate market summary statistics。
    """
    if df_basic.empty:
        return {}
    
    total = len(df_basic)
    listed = len(df_basic[df_basic['list_status'] == 'L'])
    
    # Statistics by sector
    market_counts = df_basic[df_basic['list_status'] == 'L']['market'].value_counts().to_dict()
    
    # Statistics by industry（TOP10）
    industry_counts = df_basic[df_basic['list_status'] == 'L']['industry'].value_counts().head(20).to_dict()
    
    # Statistics by region（TOP10）
    area_counts = df_basic[df_basic['list_status'] == 'L']['area'].value_counts().head(15).to_dict()
    
    return {
        'total': total,
        'listed': listed,
        'delisted': len(df_basic[df_basic['list_status'] == 'D']),
        'suspended': len(df_basic[df_basic['list_status'] == 'P']),
        'by_market': market_counts,
        'by_industry': industry_counts,
        'by_area': area_counts
    }


# ============================================================================
# 2： - 
# ============================================================================

@st.cache_data
def load_stock_daily(ts_codes: list, start_date: str, end_date: str):
    """
    Load daily market data。
    
    Args:
        ts_codes: Stock code list
        start_date: Start date 'YYYYMMDD'
        end_date: End date 'YYYYMMDD'
    
    Returns:
        DataFrame: ts_code, trade_date, open, high, low, close, pct_chg, vol, amount
    """
    if not ts_codes:
        return pd.DataFrame()
    
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    placeholders = ",".join(["?"] * len(ts_codes))
    
    try:
        query = f"""
            SELECT ts_code, trade_date, open, high, low, close, 
                   pre_close, change, pct_chg, vol, amount
            FROM daily
            WHERE ts_code IN ({placeholders})
              AND trade_date BETWEEN ? AND ?
            ORDER BY ts_code, trade_date
        """
        params = ts_codes + [start_date, end_date]
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Load daily 数据失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if df.empty:
        return df
    
    # Convert dates
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    return df.sort_values(['ts_code', 'trade_date'])


@st.cache_data
def load_adj_factor(ts_codes: list, start_date: str, end_date: str):
    """
    Load adjustment factors。
    """
    if not ts_codes:
        return pd.DataFrame()
    
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    placeholders = ",".join(["?"] * len(ts_codes))
    
    try:
        query = f"""
            SELECT ts_code, trade_date, adj_factor
            FROM adj_factor
            WHERE ts_code IN ({placeholders})
              AND trade_date BETWEEN ? AND ?
            ORDER BY ts_code, trade_date
        """
        params = ts_codes + [start_date, end_date]
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Load adj_factor 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    return df


def calculate_adjusted_price(df_daily: pd.DataFrame, df_adj: pd.DataFrame):
    """
    Calculate post-adjustment prices。
    """
    if df_daily.empty or df_adj.empty:
        return df_daily
    
    df = df_daily.merge(df_adj, on=['ts_code', 'trade_date'], how='left')
    
    # ： * 
    if 'adj_factor' in df.columns:
        df['adj_close'] = df['close'] * df['adj_factor']
        df['adj_open'] = df['open'] * df['adj_factor']
        df['adj_high'] = df['high'] * df['adj_factor']
        df['adj_low'] = df['low'] * df['adj_factor']
    
    return df


def calculate_returns(df: pd.DataFrame, price_col: str = 'close', method: str = 'simple'):
    """
    Calculate returns。
    
    Args:
        df: 包含 ts_code, trade_date, price_col 的 DataFrame
        price_col: Price column name
        method: 'simple' Simple Return, 'log' 对数Return率
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
            lambda x: x.pct_change()
        )
    
    return df


def calculate_volatility(df: pd.DataFrame, window: int = 20):
    """
    Calculate rolling volatility。
    """
    if df.empty or 'return' not in df.columns:
        return df
    
    df = df.copy()
    df['volatility'] = df.groupby('ts_code')['return'].transform(
        lambda x: x.rolling(window=window, min_periods=window//2).std()
    )
    
    # Annualized volatility
    df['volatility_ann'] = df['volatility'] * np.sqrt(252)
    
    return df


# ============================================================================
# 3： - daily_basic 
# ============================================================================

@st.cache_data
def load_daily_basic(ts_codes: list, start_date: str, end_date: str):
    """
    Load daily valuation indicators。
    
    Return fields：pe, pe_ttm, pb, turnover_rate, total_mv, circ_mv 等
    """
    if not ts_codes:
        return pd.DataFrame()
    
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    placeholders = ",".join(["?"] * len(ts_codes))
    
    try:
        query = f"""
            SELECT ts_code, trade_date, close, 
                   turnover_rate, turnover_rate_f, volume_ratio,
                   pe, pe_ttm, pb, ps, ps_ttm,
                   dv_ratio, dv_ttm,
                   total_share, float_share, free_share,
                   total_mv, circ_mv
            FROM daily_basic
            WHERE ts_code IN ({placeholders})
              AND trade_date BETWEEN ? AND ?
            ORDER BY ts_code, trade_date
        """
        params = ts_codes + [start_date, end_date]
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Load daily_basic 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if df.empty:
        return df
    
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    # （ -> ）
    if 'total_mv' in df.columns:
        df['total_mv_yi'] = df['total_mv'] / 10000
    if 'circ_mv' in df.columns:
        df['circ_mv_yi'] = df['circ_mv'] / 10000
    
    return df.sort_values(['ts_code', 'trade_date'])


@st.cache_data
def get_latest_valuation(ts_codes: list = None):
    """
    Get Latest Valuation Data（用于截面Analysis）。
    """
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Get latest trading day
        latest = conn.execute("SELECT MAX(trade_date) FROM daily_basic").fetchone()[0]
        
        if ts_codes:
            placeholders = ",".join(["?"] * len(ts_codes))
            query = f"""
                SELECT ts_code, trade_date, pe, pe_ttm, pb, 
                       turnover_rate, total_mv, circ_mv
                FROM daily_basic
                WHERE trade_date = ? AND ts_code IN ({placeholders})
            """
            params = [latest] + ts_codes
        else:
            query = """
                SELECT ts_code, trade_date, pe, pe_ttm, pb, 
                       turnover_rate, total_mv, circ_mv
                FROM daily_basic
                WHERE trade_date = ?
            """
            params = [latest]
        
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Failed to get latest valuation: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['total_mv_yi'] = df['total_mv'] / 10000
        df['circ_mv_yi'] = df['circ_mv'] / 10000
    
    return df


# ============================================================================
# 4： - 
# ============================================================================

def aggregate_by_industry(df_basic: pd.DataFrame, df_valuation: pd.DataFrame):
    """
    Aggregate valuation and return data by industry。
    """
    if df_basic.empty or df_valuation.empty:
        return pd.DataFrame()
    
    # Merge basic info and valuation
    df = df_valuation.merge(
        df_basic[['ts_code', 'industry', 'name']], 
        on='ts_code', 
        how='left'
    )
    
    # Aggregate by industry
    industry_stats = df.groupby('industry').agg({
        'ts_code': 'count',
        'pe': 'median',
        'pb': 'median',
        'turnover_rate': 'mean',
        'total_mv_yi': 'sum'
    }).reset_index()
    
    industry_stats.columns = ['行业', '股票数量', 'PE中位数', 'PB中位数', '平均换手率', 'Total Market Cap(亿)']
    
    return industry_stats.sort_values('Total Market Cap(亿)', ascending=False)


def calculate_industry_returns(df_daily: pd.DataFrame, df_basic: pd.DataFrame):
    """
    Calculate average return for each industry。
    """
    if df_daily.empty or df_basic.empty:
        return pd.DataFrame()
    
    # Merge
    df = df_daily.merge(df_basic[['ts_code', 'industry']], on='ts_code', how='left')
    
    if 'pct_chg' not in df.columns:
        return pd.DataFrame()
    
    # Aggregate by industry and date
    industry_daily = df.groupby(['industry', 'trade_date']).agg({
        'pct_chg': 'mean',
        'vol': 'sum',
        'amount': 'sum'
    }).reset_index()
    
    industry_daily.columns = ['industry', 'trade_date', 'avg_return', 'total_vol', 'total_amount']
    
    return industry_daily


def calculate_industry_correlation(df_industry_daily: pd.DataFrame):
    """
    Calculate return correlation between industries。
    """
    if df_industry_daily.empty:
        return pd.DataFrame()
    
    # Convert to pivot table
    pivot = df_industry_daily.pivot_table(
        index='trade_date',
        columns='industry',
        values='avg_return',
        aggfunc='first'
    )
    
    return pivot.corr()


def calculate_annualized_stats_by_stock(df_daily: pd.DataFrame):
    """
    Calculate annualized return and risk for each stock。
    """
    if df_daily.empty or 'pct_chg' not in df_daily.columns:
        return pd.DataFrame()
    
    stats = df_daily.groupby('ts_code').agg({
        'pct_chg': ['mean', 'std', 'count']
    }).reset_index()
    
    stats.columns = ['ts_code', 'daily_return', 'daily_std', 'count']
    
    # Annualized
    stats['ann_return'] = stats['daily_return'] * 252
    stats['ann_volatility'] = stats['daily_std'] * np.sqrt(252)
    stats['sharpe'] = stats['ann_return'] / stats['ann_volatility']
    
    return stats


# ============================================================================
# Helper functions
# ============================================================================

def create_price_pivot(df: pd.DataFrame, price_col: str = 'close'):
    """
    CreatePricePivot Table（日期 x 股票）。
    """
    if df.empty:
        return pd.DataFrame()
    
    pivot = df.pivot_table(
        index='trade_date',
        columns='ts_code',
        values=price_col,
        aggfunc='first'
    )
    
    return pivot.ffill()


def normalize_prices(df_pivot: pd.DataFrame):
    """
    Normalized Price（First Day = 100）。
    """
    if df_pivot.empty:
        return df_pivot
    
    return df_pivot / df_pivot.iloc[0] * 100


def get_stock_name_map(df_basic: pd.DataFrame):
    """
    Get code-to-name mapping。
    """
    if df_basic.empty:
        return {}
    return dict(zip(df_basic['ts_code'], df_basic['name']))
