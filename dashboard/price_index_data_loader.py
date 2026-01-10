"""
Price Index Data Loader
=======================
Load CPI (Consumer Price Index) and PPI (Producer Price Index) data 
from DuckDB for dashboard visualization.
"""
import duckdb
import pandas as pd
import streamlit as st

# Database path
MACRO_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_macro.db'


def get_db_connection():
    """Establish connection to DuckDB."""
    try:
        conn = duckdb.connect(MACRO_DB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None


@st.cache_data
def load_cpi_data():
    """
    Load CPI (Consumer Price Index) data from cn_cpi table.
    
    Returns:
        DataFrame with columns: month, nt_val, nt_yoy, nt_mom, nt_accu,
                                town_val, town_yoy, town_mom, town_accu,
                                cnt_val, cnt_yoy, cnt_mom, cnt_accu
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("SELECT * FROM cn_cpi").fetchdf()
    except Exception as e:
        st.error(f"Error loading CPI data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    # Convert 'month' (e.g., 202301) to datetime
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'].astype(str) + '01', format='%Y%m%d', errors='coerce')
    
    # Convert numeric columns
    numeric_cols = ['nt_val', 'nt_yoy', 'nt_mom', 'nt_accu',
                    'town_val', 'town_yoy', 'town_mom', 'town_accu',
                    'cnt_val', 'cnt_yoy', 'cnt_mom', 'cnt_accu']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('month')


@st.cache_data
def load_ppi_data():
    """
    Load PPI (Producer Price Index) data from cn_ppi table.
    
    Returns:
        DataFrame with PPI metrics (YoY, MoM, cumulative)
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.execute("SELECT * FROM cn_ppi").fetchdf()
    except Exception as e:
        st.error(f"Error loading PPI data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df

    # Convert 'month' to datetime
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'].astype(str) + '01', format='%Y%m%d', errors='coerce')
    
    # Convert all numeric columns
    for col in df.columns:
        if col != 'month' and col != 'last_updated':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df.sort_values('month')


def prepare_cpi_breakdown(df_cpi: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare CPI data with breakdown by region (national, urban, rural).
    
    Returns:
        DataFrame with region breakdowns suitable for comparison charts
    """
    if df_cpi.empty:
        return pd.DataFrame()
    
    # Create long format for comparison
    result = []
    
    for _, row in df_cpi.iterrows():
        result.append({
            'month': row['month'],
            'region': '全国',
            'yoy': row.get('nt_yoy'),
            'mom': row.get('nt_mom')
        })
        result.append({
            'month': row['month'],
            'region': '城市',
            'yoy': row.get('town_yoy'),
            'mom': row.get('town_mom')
        })
        result.append({
            'month': row['month'],
            'region': '农村',
            'yoy': row.get('cnt_yoy'),
            'mom': row.get('cnt_mom')
        })
    
    return pd.DataFrame(result)


def prepare_ppi_breakdown(df_ppi: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare PPI data with sector breakdown (production materials vs consumer goods).
    
    Returns:
        DataFrame with sector-level PPI comparisons
    """
    if df_ppi.empty:
        return pd.DataFrame()
    
    # Create long format for PPI sectors
    result = []
    
    for _, row in df_ppi.iterrows():
        month = row['month']
        
        # Main categories
        result.append({'month': month, 'category': 'PPI总指数', 'yoy': row.get('ppi_yoy'), 'mom': row.get('ppi_mom')})
        result.append({'month': month, 'category': '生产资料', 'yoy': row.get('ppi_mp_yoy'), 'mom': row.get('ppi_mp_mom')})
        result.append({'month': month, 'category': '生活资料', 'yoy': row.get('ppi_cg_yoy'), 'mom': row.get('ppi_cg_mom')})
        
        # Sub-categories - Production materials
        result.append({'month': month, 'category': '采掘业', 'yoy': row.get('ppi_mp_qm_yoy'), 'mom': row.get('ppi_mp_qm_mom')})
        result.append({'month': month, 'category': '原料业', 'yoy': row.get('ppi_mp_rm_yoy'), 'mom': row.get('ppi_mp_rm_mom')})
        result.append({'month': month, 'category': '加工业', 'yoy': row.get('ppi_mp_p_yoy'), 'mom': row.get('ppi_mp_p_mom')})
        
        # Sub-categories - Consumer goods
        result.append({'month': month, 'category': '食品类', 'yoy': row.get('ppi_cg_f_yoy'), 'mom': row.get('ppi_cg_f_mom')})
        result.append({'month': month, 'category': '衣着类', 'yoy': row.get('ppi_cg_c_yoy'), 'mom': row.get('ppi_cg_c_mom')})
        result.append({'month': month, 'category': '一般日用品', 'yoy': row.get('ppi_cg_adu_yoy'), 'mom': row.get('ppi_cg_adu_mom')})
        result.append({'month': month, 'category': '耐用消费品', 'yoy': row.get('ppi_cg_dcg_yoy'), 'mom': row.get('ppi_cg_dcg_mom')})
    
    return pd.DataFrame(result)


def prepare_seasonality_data(df: pd.DataFrame, metric_col: str = 'nt_mom') -> pd.DataFrame:
    """
    Prepare month-over-month data for seasonality analysis.
    Groups data by year and month for overlay comparison.
    
    Args:
        df: DataFrame with 'month' column and metric column
        metric_col: Column name for the MoM metric
    
    Returns:
        DataFrame pivoted for seasonality chart (columns = years, index = month 1-12)
    """
    if df.empty or metric_col not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['year'] = df['month'].dt.year
    df['month_num'] = df['month'].dt.month
    
    # Pivot: rows = month (1-12), columns = years
    pivot = df.pivot_table(
        index='month_num',
        columns='year',
        values=metric_col,
        aggfunc='first'
    )
    
    return pivot


def prepare_heatmap_data(df: pd.DataFrame, columns_map: dict, n_months: int = 12) -> pd.DataFrame:
    """
    Prepare data for heatmap visualization.
    
    Args:
        df: DataFrame with 'month' column
        columns_map: Dict mapping display names to column names
        n_months: Number of recent months to show
    
    Returns:
        DataFrame formatted for heatmap (rows = items, columns = months)
    """
    if df.empty:
        return pd.DataFrame()
    
    # Get most recent n_months
    df_recent = df.nlargest(n_months, 'month').sort_values('month')
    
    # Build heatmap data
    result = {}
    
    for _, row in df_recent.iterrows():
        month_str = row['month'].strftime('%Y-%m')
        result[month_str] = {}
        
        for display_name, col_name in columns_map.items():
            if col_name in row:
                result[month_str][display_name] = row[col_name]
    
    # Convert to DataFrame and transpose
    heatmap_df = pd.DataFrame(result)
    
    return heatmap_df


def prepare_ppi_chain_data(df_ppi: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare PPI industry chain transmission data.
    Chain: Mining (Upstream) -> Raw Materials (Midstream) -> Processing (Downstream)
    """
    if df_ppi.empty:
        return pd.DataFrame()
    
    # Select relevant columns for the chain
    # 采掘业 -> 原料业 -> 加工业
    chain_cols = {
        'month': 'month',
        'ppi_mp_qm_yoy': '采掘工业 (上游)',
        'ppi_mp_rm_yoy': '原材料工业 (中游)',
        'ppi_mp_p_yoy': '加工工业 (下游)',
        'ppi_cg_yoy': '生活资料 (终端)'
    }
    
    df_chain = df_ppi[list(chain_cols.keys())].copy()
    df_chain = df_chain.rename(columns=chain_cols)
    
    return df_chain


def prepare_scissors_data(df_cpi: pd.DataFrame, df_ppi: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare PPI-CPI scissors difference data.
    Scissors = PPI - CPI
    Also calculates PPI Production Materials - PPI Consumer Goods
    """
    if df_cpi.empty or df_ppi.empty:
        return pd.DataFrame()
    
    # Merge on month
    df_merged = pd.merge(df_cpi[['month', 'nt_yoy']], df_ppi[['month', 'ppi_yoy', 'ppi_mp_yoy', 'ppi_cg_yoy']], on='month', how='inner')
    
    # Calculate scissors
    df_merged['ppi_cpi_scissors'] = df_merged['ppi_yoy'] - df_merged['nt_yoy']
    df_merged['ppi_internal_scissors'] = df_merged['ppi_mp_yoy'] - df_merged['ppi_cg_yoy']
    
    return df_merged
