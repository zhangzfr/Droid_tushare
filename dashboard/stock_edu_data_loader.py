"""
A股市场教育数据加载模块
========================
提供股票基本信息和行情数据的加载函数。
连接 tushare_duck_basic.db 和 tushare_duck_stock.db。
"""
import duckdb
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# 数据库路径
BASIC_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'
STOCK_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_stock.db'

# 默认股票列表（热门标的）
DEFAULT_STOCKS = [
    '600460.SH',  # 士兰微
    '000776.SZ',  # 广发证券
    '300480.SZ',  # 光力科技
    '300124.SZ',  # 汇川技术
    '002129.SH',  # 中环
]

# 板块映射
MARKET_NAMES = {
    '主板': '主板',
    '创业板': '创业板',
    '科创板': '科创板',
    'CDR': 'CDR',
    '北交所': '北交所'
}

# 上市状态映射
STATUS_NAMES = {
    'L': '正常上市',
    'D': '已退市',
    'P': '暂停上市'
}


def get_basic_db_connection():
    """连接 basic 数据库"""
    try:
        conn = duckdb.connect(BASIC_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"连接 basic 数据库失败: {e}")
        return None


def get_stock_db_connection():
    """连接 stock 数据库"""
    try:
        conn = duckdb.connect(STOCK_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"连接 stock 数据库失败: {e}")
        return None


# ============================================================================
# 第1层：认识A股市场 - 基本信息加载
# ============================================================================

@st.cache_data
def load_stock_basic():
    """
    加载所有股票基本信息。
    返回字段：ts_code, name, industry, market, exchange, list_status, list_date, area
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
        st.error(f"加载 stock_basic 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    # 添加中文状态名称
    df['status_name'] = df['list_status'].map(STATUS_NAMES).fillna('未知')
    
    return df


@st.cache_data
def load_stock_company():
    """
    加载公司详细信息。
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
        st.error(f"加载 stock_company 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    return df


@st.cache_data
def get_market_summary(df_basic: pd.DataFrame):
    """
    计算市场汇总统计。
    """
    if df_basic.empty:
        return {}
    
    total = len(df_basic)
    listed = len(df_basic[df_basic['list_status'] == 'L'])
    
    # 按板块统计
    market_counts = df_basic[df_basic['list_status'] == 'L']['market'].value_counts().to_dict()
    
    # 按行业统计（TOP10）
    industry_counts = df_basic[df_basic['list_status'] == 'L']['industry'].value_counts().head(20).to_dict()
    
    # 按地域统计（TOP10）
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
# 第2层：理解股票价格 - 行情数据加载
# ============================================================================

@st.cache_data
def load_stock_daily(ts_codes: list, start_date: str, end_date: str):
    """
    加载日线行情数据。
    
    Args:
        ts_codes: 股票代码列表
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
    
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
        st.error(f"加载 daily 数据失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if df.empty:
        return df
    
    # 转换日期
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    return df.sort_values(['ts_code', 'trade_date'])


@st.cache_data
def load_adj_factor(ts_codes: list, start_date: str, end_date: str):
    """
    加载复权因子。
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
        st.error(f"加载 adj_factor 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    return df


def calculate_adjusted_price(df_daily: pd.DataFrame, df_adj: pd.DataFrame):
    """
    计算后复权价格。
    """
    if df_daily.empty or df_adj.empty:
        return df_daily
    
    df = df_daily.merge(df_adj, on=['ts_code', 'trade_date'], how='left')
    
    # 后复权：价格 * 复权因子
    if 'adj_factor' in df.columns:
        df['adj_close'] = df['close'] * df['adj_factor']
        df['adj_open'] = df['open'] * df['adj_factor']
        df['adj_high'] = df['high'] * df['adj_factor']
        df['adj_low'] = df['low'] * df['adj_factor']
    
    return df


def calculate_returns(df: pd.DataFrame, price_col: str = 'close', method: str = 'simple'):
    """
    计算收益率。
    
    Args:
        df: 包含 ts_code, trade_date, price_col 的 DataFrame
        price_col: 价格列名
        method: 'simple' 简单收益率, 'log' 对数收益率
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
    计算滚动波动率。
    """
    if df.empty or 'return' not in df.columns:
        return df
    
    df = df.copy()
    df['volatility'] = df.groupby('ts_code')['return'].transform(
        lambda x: x.rolling(window=window, min_periods=window//2).std()
    )
    
    # 年化波动率
    df['volatility_ann'] = df['volatility'] * np.sqrt(252)
    
    return df


# ============================================================================
# 第3层：分析估值指标 - daily_basic 数据
# ============================================================================

@st.cache_data
def load_daily_basic(ts_codes: list, start_date: str, end_date: str):
    """
    加载每日估值指标。
    
    返回字段：pe, pe_ttm, pb, turnover_rate, total_mv, circ_mv 等
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
        st.error(f"加载 daily_basic 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if df.empty:
        return df
    
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    
    # 市值单位转换（万元 -> 亿元）
    if 'total_mv' in df.columns:
        df['total_mv_yi'] = df['total_mv'] / 10000
    if 'circ_mv' in df.columns:
        df['circ_mv_yi'] = df['circ_mv'] / 10000
    
    return df.sort_values(['ts_code', 'trade_date'])


@st.cache_data
def get_latest_valuation(ts_codes: list = None):
    """
    获取最新的估值数据（用于截面分析）。
    """
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # 获取最新交易日
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
        st.error(f"获取最新估值失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['total_mv_yi'] = df['total_mv'] / 10000
        df['circ_mv_yi'] = df['circ_mv'] / 10000
    
    return df


# ============================================================================
# 第4层：行业分析 - 聚合计算
# ============================================================================

def aggregate_by_industry(df_basic: pd.DataFrame, df_valuation: pd.DataFrame):
    """
    按行业聚合估值和收益数据。
    """
    if df_basic.empty or df_valuation.empty:
        return pd.DataFrame()
    
    # 合并基本信息和估值
    df = df_valuation.merge(
        df_basic[['ts_code', 'industry', 'name']], 
        on='ts_code', 
        how='left'
    )
    
    # 按行业聚合
    industry_stats = df.groupby('industry').agg({
        'ts_code': 'count',
        'pe': 'median',
        'pb': 'median',
        'turnover_rate': 'mean',
        'total_mv_yi': 'sum'
    }).reset_index()
    
    industry_stats.columns = ['行业', '股票数量', 'PE中位数', 'PB中位数', '平均换手率', '总市值(亿)']
    
    return industry_stats.sort_values('总市值(亿)', ascending=False)


def calculate_industry_returns(df_daily: pd.DataFrame, df_basic: pd.DataFrame):
    """
    计算各行业的平均收益率。
    """
    if df_daily.empty or df_basic.empty:
        return pd.DataFrame()
    
    # 合并
    df = df_daily.merge(df_basic[['ts_code', 'industry']], on='ts_code', how='left')
    
    if 'pct_chg' not in df.columns:
        return pd.DataFrame()
    
    # 按行业和日期聚合
    industry_daily = df.groupby(['industry', 'trade_date']).agg({
        'pct_chg': 'mean',
        'vol': 'sum',
        'amount': 'sum'
    }).reset_index()
    
    industry_daily.columns = ['industry', 'trade_date', 'avg_return', 'total_vol', 'total_amount']
    
    return industry_daily


def calculate_industry_correlation(df_industry_daily: pd.DataFrame):
    """
    计算行业间收益率相关性。
    """
    if df_industry_daily.empty:
        return pd.DataFrame()
    
    # 转换为透视表
    pivot = df_industry_daily.pivot_table(
        index='trade_date',
        columns='industry',
        values='avg_return',
        aggfunc='first'
    )
    
    return pivot.corr()


def calculate_annualized_stats_by_stock(df_daily: pd.DataFrame):
    """
    计算每只股票的年化收益和风险。
    """
    if df_daily.empty or 'pct_chg' not in df_daily.columns:
        return pd.DataFrame()
    
    stats = df_daily.groupby('ts_code').agg({
        'pct_chg': ['mean', 'std', 'count']
    }).reset_index()
    
    stats.columns = ['ts_code', 'daily_return', 'daily_std', 'count']
    
    # 年化
    stats['ann_return'] = stats['daily_return'] * 252
    stats['ann_volatility'] = stats['daily_std'] * np.sqrt(252)
    stats['sharpe'] = stats['ann_return'] / stats['ann_volatility']
    
    return stats


# ============================================================================
# 辅助函数
# ============================================================================

def create_price_pivot(df: pd.DataFrame, price_col: str = 'close'):
    """
    创建价格透视表（日期 x 股票）。
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
    归一化价格（首日 = 100）。
    """
    if df_pivot.empty:
        return df_pivot
    
    return df_pivot / df_pivot.iloc[0] * 100


def get_stock_name_map(df_basic: pd.DataFrame):
    """
    获取代码到名称的映射。
    """
    if df_basic.empty:
        return {}
    return dict(zip(df_basic['ts_code'], df_basic['name']))
