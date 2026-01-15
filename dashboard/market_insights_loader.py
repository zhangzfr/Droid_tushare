"""
市场洞察数据加载模块
===================
加载市场交易统计和全球指数数据，用于专业级市场分析。
"""
import duckdb
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# 数据库路径
INDEX_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_index.db'

# 全球指数代码与名称映射 (完整版)
GLOBAL_INDICES = {
    'XIN9': '富时中国A50指数',
    'HSI': '恒生指数',
    'HKTECH': '恒生科技指数',
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
    """获取指数显示名称：代码 - 名称"""
    name = GLOBAL_INDICES.get(code, code)
    return f"{code} - {name}"

# A股板块代码映射 - daily_info table (单位: 亿元)
MARKET_CODES = {
    'SH_A': '上海A股',
    'SH_STAR': '科创板',
    'SZ_A': '深圳A股',
    'SZ_MAIN': '深市主板',
    'SZ_GEM': '创业板',
    'SZ_SME': '中小板',
    'SH_MARKET': '上海市场',
    'SZ_MARKET': '深圳市场',
    'SH_FUND': '上海基金'
}

# sz_daily_info table codes mapping (单位: 元, 需要转换为亿元)
SZ_DAILY_CODES = {
    '股票': '深圳股票',
    '创业板A股': '深圳创业板A股',
    '主板A股': '深圳主板A股',
    '债券': '深圳债券',
    '基金': '深圳基金'
}


def get_index_db_connection():
    """连接Index数据库"""
    try:
        conn = duckdb.connect(INDEX_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"连接数据库失败: {e}")
        return None


# ============================================================================
# 市场统计数据 - daily_info
# ============================================================================

@st.cache_data(ttl=3600)
def load_daily_info(start_date: str = None, end_date: str = None, ts_codes: list = None):
    """
    加载市场交易统计数据。
    
    Args:
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
        ts_codes: 板块代码列表（如 ['SH_A', 'SZ_GEM']）
    
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
        st.error(f"加载 daily_info 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        # 添加中文名称
        df['market_name'] = df['ts_code'].map(MARKET_CODES).fillna(df['ts_name'])
    
    return df


@st.cache_data(ttl=3600)
def get_available_market_codes():
    """获取可用的板块代码列表"""
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
    加载深圳市场统计数据 (sz_daily_info)。
    注意：此表的amount单位是元，需要转换为亿元。
    
    Args:
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
        ts_codes: 板块代码列表（如 ['股票', '创业板A股']）
    
    Returns:
        DataFrame: trade_date, ts_code, count, amount (已转换为亿元)
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
        st.error(f"加载 sz_daily_info 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        # 转换单位：元 -> 亿元
        df['amount'] = df['amount'] / 1e8
        # 添加中文名称
        df['market_name'] = df['ts_code'].map(SZ_DAILY_CODES).fillna(df['ts_code'])
        df['source'] = 'sz_daily_info'
    
    return df


@st.cache_data(ttl=3600)
def load_combined_amount_data(start_date: str, end_date: str):
    """
    加载合并的成交额数据，包括:
    - daily_info: SH_MARKET, SZ_MARKET, SH_A, SZ_GEM, SH_STAR, SH_FUND (亿元)
    - sz_daily_info: 股票, 创业板A股, 主板A股, 债券, 基金 (转换后亿元)
    
    Returns:
        DataFrame: trade_date, ts_code, market_name, amount (亿元), source
    """
    # 从 daily_info 加载
    daily_codes = ['SH_MARKET', 'SZ_MARKET', 'SH_A', 'SZ_GEM', 'SH_STAR', 'SH_FUND']
    df_daily = load_daily_info(start_date, end_date, daily_codes)
    if not df_daily.empty:
        df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount']].copy()
        df_daily['source'] = 'daily_info'
    
    # 从 sz_daily_info 加载
    sz_codes = ['股票', '创业板A股', '主板A股', '债券', '基金']
    df_sz = load_sz_daily_info(start_date, end_date, sz_codes)
    if not df_sz.empty:
        df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount', 'source']].copy()
    
    # 合并
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
    计算PE历史分位数。
    
    Args:
        df: daily_info数据
        ts_code: 板块代码
    
    Returns:
        dict: 当前PE, 历史分位数, 最小/最大PE
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
    计算市场汇总统计。
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
# 全球指数数据 - index_global
# ============================================================================

@st.cache_data(ttl=3600)
def load_index_global(start_date: str = None, end_date: str = None, ts_codes: list = None):
    """
    加载全球指数行情数据。
    
    Args:
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
        ts_codes: 指数代码列表
    
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
        st.error(f"加载 index_global 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
        # 添加统一格式的显示名称：代码 - 名称
        df['index_name'] = df['ts_code'].apply(get_index_display_name)
    
    return df


@st.cache_data(ttl=3600)
def get_available_global_indices():
    """获取可用的全球指数代码"""
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
    计算全球指数收益率相关性矩阵。
    """
    if df.empty or 'pct_chg' not in df.columns:
        return pd.DataFrame()
    
    # 透视表
    pivot = df.pivot_table(
        index='trade_date',
        columns='index_name',
        values='pct_chg',
        aggfunc='first'
    )
    
    return pivot.corr()


def calculate_index_returns(df: pd.DataFrame):
    """
    计算各指数的累计收益和年化统计。
    """
    if df.empty:
        return pd.DataFrame()
    
    # 按指数分组计算
    stats = []
    for code in df['ts_code'].unique():
        data = df[df['ts_code'] == code].sort_values('trade_date')
        if len(data) < 10:
            continue
        
        # 累计收益
        first_close = data.iloc[0]['close']
        last_close = data.iloc[-1]['close']
        total_return = (last_close - first_close) / first_close
        
        # 日收益率
        daily_returns = data['pct_chg'].dropna() / 100
        
        # 年化
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
    """计算最大回撤"""
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
    """创建归一化价格透视表"""
    if df.empty:
        return pd.DataFrame()
    
    pivot = df.pivot_table(
        index='trade_date',
        columns='index_name',
        values=value_col,
        aggfunc='first'
    )
    
    # 归一化到100
    normalized = pivot / pivot.iloc[0] * 100
    
    return normalized.ffill()


# ============================================================================
# 市场情绪指标
# ============================================================================

def calculate_market_sentiment(df: pd.DataFrame, ts_code: str = 'SH_A'):
    """
    基于成交额和换手率计算市场情绪。
    """
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return pd.DataFrame()
    
    data = data.sort_values('trade_date')
    
    # 成交额MA
    data['amount_ma20'] = data['amount'].rolling(20).mean()
    data['amount_ma60'] = data['amount'].rolling(60).mean()
    
    # 成交额相对强度
    data['amount_ratio'] = data['amount'] / data['amount_ma20']
    
    # 换手率MA
    if 'tr' in data.columns:
        data['tr_ma20'] = data['tr'].rolling(20).mean()
    
    return data


def aggregate_monthly_stats(df: pd.DataFrame, ts_code: str):
    """按月聚合统计"""
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
# 两市交易数据分析辅助函数
# ============================================================================

def calculate_amount_turnover(df: pd.DataFrame):
    """
    计算金额换手率 (amount / float_mv * 100)。
    """
    if df.empty or 'amount' not in df.columns or 'float_mv' not in df.columns:
        return df
    
    df = df.copy()
    df['amount_turnover'] = df['amount'] / df['float_mv'] * 100
    return df


def load_combined_trading_data(start_date: str = None, end_date: str = None, 
                              daily_codes: list = None, sz_codes: list = None):
    """
    加载合并的交易数据（daily_info + sz_daily_info）。
    
    Args:
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
        daily_codes: daily_info板块代码列表
        sz_codes: sz_daily_info板块代码列表
    
    Returns:
        DataFrame: 合并后的交易数据
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
    
    # 合并数据
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
    计算流动性评分。
    
    评分逻辑：
    - amount_score: 成交额得分 (0-100)
    - turnover_score: 换手率得分 (0-100)
    - market_cap_score: 流通市值得分 (0-100)
    - 综合得分 = amount_score * 0.5 + turnover_score * 0.3 + market_cap_score * 0.2
    """
    if df.empty:
        return None
    
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return None
    
    latest = data.iloc[-1]
    
    # 成交额得分 (假设1000亿为满分)
    amount_score = min(latest['amount'] / 1000 * 100, 100) if 'amount' in latest and latest['amount'] > 0 else 50
    
    # 换手率得分
    if 'tr' in latest and not pd.isna(latest['tr']):
        turnover_score = min(latest['tr'] * 50, 100)  # 2%换手率为满分
    elif 'amount_turnover' in latest and not pd.isna(latest['amount_turnover']):
        turnover_score = min(latest['amount_turnover'] * 50, 100)
    else:
        turnover_score = 50
    
    # 流通市值得分 (假设5万亿为满分)
    if 'float_mv' in latest and not pd.isna(latest['float_mv']) and latest['float_mv'] > 0:
        market_cap_score = min(latest['float_mv'] / 50000 * 100, 100)
    else:
        market_cap_score = 50
    
    # 综合得分
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

