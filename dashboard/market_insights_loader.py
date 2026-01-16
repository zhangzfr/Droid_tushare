"""
Market Insights Data Loading Module
====================================
Loads market trading statistics and global index data for professional market analysis.
"""
import duckdb
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# Database paths
INDEX_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_index.db'
OPT_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_opt.db'

# Global Index Code to Name Mapping (Complete Version)
# Note: Index names are kept in Chinese as requested
GLOBAL_INDICES = {
    'XIN9': '富时中国A50指数',
    'HSI': '恒生指数',
    'HKTECH': '恒生Technology指数',
    'HKAH': '恒生AH股H指数',
    'DJI': '道琼斯工业指数',
    'SPX': '标普500指数',
    'IXIC': '纳斯达克指数',
    'FTSE': '富时100指数',
    'FCHI': '法国CAC40指数',
    'GDAXI': '德国DAX指数',
    'N225': '日经225指数',
    'KS11': '韩国综合指数',
    'AS51': '澳大利亚标普200指数',
    'SENSEX': '印度孟买SENSEX指数',
    'IBOVESPA': '巴西IBOVESPA指数',
    'RTS': '俄罗斯RTS指数',
    'TWII': '台湾加权指数',
    'CKLSE': '马来西亚指数',
    'SPTSX': '加拿大S&P/TSX指数',
    'CSX5P': 'STOXX欧洲50指数',
    'RUT': '罗素2000指数'
}


def get_index_display_name(code: str) -> str:
    """获取指数显示Name：Code - Name"""
    name = GLOBAL_INDICES.get(code, code)
    return f"{code} - {name}"

# A-Share Sector Code Mapping - daily_info table (Unit: 100M CNY)
MARKET_CODES = {
    'SH_A': 'Shanghai A-Share',
    'SH_STAR': 'STAR Market',
    'SZ_A': 'Shenzhen A-Share',
    'SZ_MAIN': 'Shenzhen Main Board',
    'SZ_GEM': 'ChiNext',
    'SZ_SME': 'SME Board',
    'SH_MARKET': 'Shanghai Market',
    'SZ_MARKET': 'Shenzhen Market',
    'SH_FUND': 'Shanghai Fund'
}

# sz_daily_info table codes mapping (Unit: CNY, need to convert to 100M CNY)
SZ_DAILY_CODES = {
    'Stock': 'Shenzhen Stock',
    'GEM A-Share': 'Shenzhen GEM A-Share',
    'Main Board A-Share': 'Shenzhen Main Board A-Share',
    'Bond': 'Shenzhen Bond',
    'Fund': 'Shenzhen Fund'
}


def get_index_db_connection():
    """Connect to Index database."""
    try:
        conn = duckdb.connect(INDEX_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def get_opt_db_connection():
    """Connect to Options database."""
    try:
        conn = duckdb.connect(OPT_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Options Database connection failed: {e}")
        return None


# ============================================================================
# Market Statistics Data - daily_info
# ============================================================================

@st.cache_data(ttl=3600)
def load_daily_info(start_date: str = None, end_date: str = None, ts_codes: list = None):
    """
    Load market trading statistics data.
    
    Args:
        start_date: Start date 'YYYYMMDD'
        end_date: End date 'YYYYMMDD'
        ts_codes: Sector code list (e.g., ['SH_A', 'SZ_GEM'])
    
    Returns:
        DataFrame: trade_date, ts_code, ts_name, com_count, total_mv, float_mv, amount, pe, tr
    """
    conn = get_index_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        conditions = []
        params = []
        
        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)
        if ts_codes:
            placeholders = ",".join(["?"] * len(ts_codes))
            conditions.append(f"ts_code IN ({placeholders})")
            params.extend(ts_codes)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT trade_date, ts_code, ts_name, com_count, 
                   total_share, float_share, total_mv, float_mv,
                   amount, vol, trans_count, pe, tr, exchange
            FROM daily_info
            WHERE {where_clause}
            ORDER BY trade_date, ts_code
        """
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Failed to load daily_info: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        # Add display name
        df['market_name'] = df['ts_code'].map(MARKET_CODES).fillna(df['ts_name'])
    
    return df


@st.cache_data(ttl=3600)
def get_available_market_codes():
    """Get available sector code list."""
    conn = get_index_db_connection()
    if not conn:
        return []
    
    try:
        # Use simple query and dedup in python or use GROUP BY
        df = conn.execute("""
            SELECT ts_code, MAX(ts_name) as ts_name FROM daily_info GROUP BY ts_code ORDER BY ts_code
        """).fetchdf()
    except:
        return []
    finally:
        conn.close()
    
    return list(zip(df['ts_code'], df['ts_name']))


@st.cache_data(ttl=3600)
def load_sz_daily_info(start_date: str = None, end_date: str = None, ts_codes: list = None):
    """
    Load Shenzhen market statistics (sz_daily_info).
    Note: The amount unit in this table is CNY, need to convert to 100M CNY.
    
    Args:
        start_date: Start date 'YYYYMMDD'
        end_date: End date 'YYYYMMDD'
        ts_codes: Sector code list (e.g., ['Stock', 'GEM A-Share'])
    
    Returns:
        DataFrame: trade_date, ts_code, count, amount (converted to 100M CNY)
    """
    conn = get_index_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        conditions = []
        params = []
        
        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)
        if ts_codes:
            placeholders = ",".join(["?"] * len(ts_codes))
            conditions.append(f"ts_code IN ({placeholders})")
            params.extend(ts_codes)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT trade_date, ts_code, count, amount, vol, total_mv, float_mv
            FROM sz_daily_info
            WHERE {where_clause}
            ORDER BY trade_date, ts_code
        """
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Failed to load sz_daily_info: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        # Convert unit: CNY -> 100M CNY
        df['amount'] = df['amount'] / 1e8
        # Add display name
        df['market_name'] = df['ts_code'].map(SZ_DAILY_CODES).fillna(df['ts_code'])
        df['source'] = 'sz_daily_info'
    
    return df


@st.cache_data(ttl=3600)
def load_combined_amount_data(start_date: str, end_date: str):
    """
    Load combined trading amount data, including:
    - daily_info: SH_MARKET, SZ_MARKET, SH_A, SZ_GEM, SH_STAR, SH_FUND (100M CNY)
    - sz_daily_info: Stock, GEM A-Share, Main Board A-Share, Bond, Fund (converted to 100M CNY)
    
    Returns:
        DataFrame: trade_date, ts_code, market_name, amount (100M CNY), source
    """
    # From daily_info load
    daily_codes = ['SH_MARKET', 'SZ_MARKET', 'SH_A', 'SZ_GEM', 'SH_STAR', 'SH_FUND']
    df_daily = load_daily_info(start_date, end_date, daily_codes)
    if not df_daily.empty:
        df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount']].copy()
        df_daily['source'] = 'daily_info'
    
    # From sz_daily_info load
    sz_codes = ['Stock', 'GEM A-Share', 'Main Board A-Share', 'Bond', 'Fund']
    df_sz = load_sz_daily_info(start_date, end_date, sz_codes)
    if not df_sz.empty:
        df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount', 'source']].copy()
    
    # Merge
    if not df_daily.empty and not df_sz.empty:
        df_combined = pd.concat([df_daily, df_sz], ignore_index=True)
    elif not df_daily.empty:
        df_combined = df_daily
    elif not df_sz.empty:
        df_combined = df_sz
    else:
        df_combined = pd.DataFrame()
    
    return df_combined


def calculate_pe_percentile(df: pd.DataFrame, ts_code: str):
    """
    Calculate PE historical percentile.
    
    Args:
        df: daily_info data
        ts_code: Sector code
    
    Returns:
        dict: current_pe, historical_percentile, min/max PE
    """
    data = df[df['ts_code'] == ts_code].dropna(subset=['pe']).copy()
    if data.empty:
        return None
    
    current_pe = data.iloc[-1]['pe']
    pe_values = data['pe'].values
    
    percentile = (pe_values < current_pe).sum() / len(pe_values) * 100
    
    return {
        'current_pe': current_pe,
        'percentile': percentile,
        'min_pe': pe_values.min(),
        'max_pe': pe_values.max(),
        'median_pe': np.median(pe_values),
        'mean_pe': pe_values.mean()
    }


def calculate_market_stats(df: pd.DataFrame):
    """
    Calculate market summary statistics.
    """
    if df.empty:
        return {}
    
    latest = df.groupby('ts_code').last().reset_index()
    
    return {
        'latest_date': df['trade_date'].max(),
        'total_mv_sum': latest['total_mv'].sum() if 'total_mv' in latest.columns else 0,
        'amount_sum': latest['amount'].sum() if 'amount' in latest.columns else 0,
    }


# ============================================================================
# Global Index Data - index_global
# ============================================================================

@st.cache_data(ttl=3600)
def load_index_global(start_date: str = None, end_date: str = None, ts_codes: list = None):
    """
    Load global index market data.
    
    Args:
        start_date: Start date 'YYYYMMDD'
        end_date: End date 'YYYYMMDD'
        ts_codes: Index code list
    
    Returns:
        DataFrame: ts_code, trade_date, open, close, high, low, pct_chg
    """
    conn = get_index_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        conditions = []
        params = []
        
        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)
        if ts_codes:
            placeholders = ",".join(["?"] * len(ts_codes))
            conditions.append(f"ts_code IN ({placeholders})")
            params.extend(ts_codes)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT ts_code, trade_date, open, close, high, low, 
                   pre_close, change, pct_chg, swing, vol, amount
            FROM index_global
            WHERE {where_clause}
            ORDER BY ts_code, trade_date
        """
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Failed to load index_global: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        # Add unified display name: code - name
        df['index_name'] = df['ts_code'].apply(get_index_display_name)
    
    return df


@st.cache_data(ttl=3600)
def get_available_global_indices():
    """Get available global index codes."""
    conn = get_index_db_connection()
    if not conn:
        return []
    
    try:
        df = conn.execute("""
            SELECT DISTINCT ts_code FROM index_global ORDER BY ts_code
        """).fetchdf()
    except:
        return []
    finally:
        conn.close()
    
    return df['ts_code'].tolist()


def calculate_global_correlation(df: pd.DataFrame):
    """
    Calculate global index return correlation matrix.
    """
    if df.empty or 'pct_chg' not in df.columns:
        return pd.DataFrame()
    
    # Pivot table
    pivot = df.pivot_table(
        index='trade_date',
        columns='index_name',
        values='pct_chg',
        aggfunc='first'
    )
    
    return pivot.corr()


def calculate_index_returns(df: pd.DataFrame):
    """
    Calculate cumulative returns and annualized statistics for each index.
    """
    if df.empty:
        return pd.DataFrame()
    
    # Calculate by index group
    stats = []
    for code in df['ts_code'].unique():
        data = df[df['ts_code'] == code].sort_values('trade_date')
        if len(data) < 10:
            continue
        
        # Cumulative return
        first_close = data.iloc[0]['close']
        last_close = data.iloc[-1]['close']
        total_return = (last_close - first_close) / first_close
        
        # Daily returns
        daily_returns = data['pct_chg'].dropna() / 100
        
        # Annualized
        trading_days = len(data)
        ann_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
        ann_vol = daily_returns.std() * np.sqrt(252)
        sharpe = ann_return / ann_vol if ann_vol > 0 else 0
        
        stats.append({
            'ts_code': code,
            'index_name': get_index_display_name(code),
            'total_return': total_return,
            'ann_return': ann_return,
            'ann_volatility': ann_vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': calculate_max_drawdown(data['close'].values)
        })
    
    return pd.DataFrame(stats)


def calculate_max_drawdown(prices):
    """Calculate maximum drawdown."""
    if len(prices) == 0:
        return 0
    peak = prices[0]
    max_dd = 0
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd


def create_normalized_pivot(df: pd.DataFrame, value_col: str = 'close'):
    """Create normalized price pivot table."""
    if df.empty:
        return pd.DataFrame()
    
    pivot = df.pivot_table(
        index='trade_date',
        columns='index_name',
        values=value_col,
        aggfunc='first'
    )
    
    # Normalize to 100
    normalized = pivot / pivot.iloc[0] * 100
    
    return normalized.ffill()


# ============================================================================
# Market Sentiment Indicators
# ============================================================================

def calculate_market_sentiment(df: pd.DataFrame, ts_code: str = 'SH_A'):
    """
    Calculate market sentiment based on trading amount and turnover rate.
    """
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return pd.DataFrame()
    
    data = data.sort_values('trade_date')
    
    # Amount MA
    data['amount_ma20'] = data['amount'].rolling(20).mean()
    data['amount_ma60'] = data['amount'].rolling(60).mean()
    
    # Amount relative strength
    data['amount_ratio'] = data['amount'] / data['amount_ma20']
    
    # Turnover rate MA
    if 'tr' in data.columns:
        data['tr_ma20'] = data['tr'].rolling(20).mean()
    
    return data


def aggregate_monthly_stats(df: pd.DataFrame, ts_code: str):
    """Aggregate statistics by month."""
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return pd.DataFrame()
    
    data['year_month'] = data['trade_date'].dt.to_period('M')
    
    monthly = data.groupby('year_month').agg({
        'pe': 'mean',
        'amount': 'sum',
        'tr': 'mean',
        'total_mv': 'last'
    }).reset_index()
    
    monthly['month'] = monthly['year_month'].dt.to_timestamp()
    
    return monthly


# ============================================================================
# Two-Market Trading Data Analysis Helper Functions
# ============================================================================

def calculate_amount_turnover(df: pd.DataFrame):
    """
    Calculate amount turnover rate (amount / float_mv * 100).
    """
    if df.empty or 'amount' not in df.columns or 'float_mv' not in df.columns:
        return df
    
    df = df.copy()
    df['amount_turnover'] = df['amount'] / df['float_mv'] * 100
    return df


def load_combined_trading_data(start_date: str = None, end_date: str = None, 
                              daily_codes: list = None, sz_codes: list = None):
    """
    Load combined trading data (daily_info + sz_daily_info).
    
    Args:
        start_date: Start date 'YYYYMMDD'
        end_date: End date 'YYYYMMDD'
        daily_codes: daily_info sector code list
        sz_codes: sz_daily_info sector code list
    
    Returns:
        DataFrame: Combined trading data
    """
    df_daily = pd.DataFrame()
    df_sz = pd.DataFrame()
    
    if daily_codes:
        df_daily = load_daily_info(start_date, end_date, daily_codes)
        if not df_daily.empty:
            df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount', 'tr', 'total_mv', 'float_mv']].copy()
            df_daily['source'] = 'daily_info'
            df_daily = calculate_amount_turnover(df_daily)
    
    if sz_codes:
        df_sz = load_sz_daily_info(start_date, end_date, sz_codes)
        if not df_sz.empty:
            df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount', 'total_mv', 'float_mv', 'source']].copy()
            df_sz['tr'] = None
            df_sz = calculate_amount_turnover(df_sz)
    
    # 
    if not df_daily.empty and not df_sz.empty:
        df_combined = pd.concat([df_daily, df_sz], ignore_index=True)
    elif not df_daily.empty:
        df_combined = df_daily
    elif not df_sz.empty:
        df_combined = df_sz
    else:
        df_combined = pd.DataFrame()
    
    return df_combined


def calculate_liquidity_score(df: pd.DataFrame, ts_code: str):
    """
    Calculate liquidity score.
    
    Scoring logic:
    - amount_score: Trading amount score (0-100)
    - turnover_score: Turnover rate score (0-100)
    - market_cap_score: Market cap score (0-100)
    - Combined score = amount_score * 0.5 + turnover_score * 0.3 + market_cap_score * 0.2
    """
    if df.empty:
        return None
    
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return None
    
    latest = data.iloc[-1]
    
    # Amount score (1000B CNY = full score)
    amount_score = min(latest['amount'] / 1000 * 100, 100) if 'amount' in latest and latest['amount'] > 0 else 50
    
    # Turnover rate score
    if 'tr' in latest and not pd.isna(latest['tr']):
        turnover_score = min(latest['tr'] * 50, 100)  # 2% turnover = full score
    elif 'amount_turnover' in latest and not pd.isna(latest['amount_turnover']):
        turnover_score = min(latest['amount_turnover'] * 50, 100)
    else:
        turnover_score = 50
    
    # Market cap score (50T CNY = full score)
    if 'float_mv' in latest and not pd.isna(latest['float_mv']) and latest['float_mv'] > 0:
        market_cap_score = min(latest['float_mv'] / 50000 * 100, 100)
    else:
        market_cap_score = 50
    
    # Combined score
    liquidity_score = (amount_score * 0.5 + turnover_score * 0.3 + market_cap_score * 0.2)
    
    return {
        'ts_code': ts_code,
        'market_name': latest.get('market_name', ts_code),
        'liquidity_score': liquidity_score,
        'amount_score': amount_score,
        'turnover_score': turnover_score,
        'market_cap_score': market_cap_score,
        'amount': latest.get('amount', 0),
        'turnover': latest.get('tr', latest.get('amount_turnover', 0)),
        'float_mv': latest.get('float_mv', 0)
    }


# ============================================================================
# Options Data - opt_basic, opt_daily
# ============================================================================

@st.cache_data(ttl=3600)
def load_opt_basic(exchange: str = None):
    """
    Load option basic information.
    
    Args:
        exchange: Exchange code (e.g., 'SSE', 'SZSE', 'CFFEX')
        
    Returns:
        DataFrame: ts_code, name, exercise_price, s_month, maturity_date, etc.
    """
    conn = get_opt_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        conditions = []
        params = []
        
        if exchange:
            conditions.append("exchange = ?")
            params.append(exchange)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Select key columns
        query = f"""
            SELECT ts_code, name, exchange, exercise_price, s_month, maturity_date, 
                   call_put, opt_code, list_date, delist_date
            FROM opt_basic
            WHERE {where_clause}
            ORDER BY s_month, exercise_price
        """
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        # Check if table exists
        try:
            conn.execute("SELECT * FROM opt_basic LIMIT 1")
            st.error(f"Failed to load opt_basic: {e}")
        except:
            # Table might not exist yet if data not synced
            pass
        return pd.DataFrame()
    finally:
        conn.close()
        
    if not df.empty:
        # Convert dates
        for col in ['maturity_date', 'list_date', 'delist_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')
    
    return df


@st.cache_data(ttl=3600)
def load_opt_daily(ts_code: str = None, start_date: str = None, end_date: str = None, ts_codes: list = None):
    """
    Load option daily quotes.
    """
    conn = get_opt_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        conditions = []
        params = []
        
        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)
        
        if ts_code:
            conditions.append("ts_code = ?")
            params.append(ts_code)
        elif ts_codes:
            placeholders = ",".join(["?"] * len(ts_codes))
            conditions.append(f"ts_code IN ({placeholders})")
            params.extend(ts_codes)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT ts_code, trade_date, close, open, high, low, 
                   vol, amount, oi
            FROM opt_daily
            WHERE {where_clause}
            ORDER BY trade_date, ts_code
        """
        df = conn.execute(query, params).fetchdf()
    except Exception as e:
        st.error(f"Failed to load opt_daily: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        
    return df


@st.cache_data(ttl=3600)
def get_available_opt_codes():
    """Get available option codes mapping (ts_code -> name)."""
    df = load_opt_basic()
    if df.empty:
        return []
        
    # Limit to subset if too many
    # For now return list of tuples (ts_code, display_name)
    # Display name format: "Name (Code) - Month Strike Type"
    
    df['display'] = df.apply(
        lambda x: f"{x['name']} ({x['ts_code']}) - {x['s_month']} {x['call_put']} {x['exercise_price']}", 
        axis=1
    )
    
    return list(zip(df['ts_code'], df['display']))
