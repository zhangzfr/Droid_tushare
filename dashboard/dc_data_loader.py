import duckdb
import pandas as pd
import streamlit as st

DC_DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_index.db'


def get_dc_connection():
    try:
        return duckdb.connect(DC_DB_PATH, read_only=True)
    except Exception as e:
        st.error(f"连接 DC 数据库失败: {e}")
        return None


@st.cache_data
def get_dc_latest_trade_date():
    conn = get_dc_connection()
    if not conn:
        return None
    try:
        row = conn.execute("SELECT max(trade_date) FROM dc_daily").fetchone()
        return row[0] if row else None
    except Exception as e:
        st.error(f"查询最新交易日失败: {e}")
        return None
    finally:
        conn.close()


@st.cache_data
def get_dc_counts():
    conn = get_dc_connection()
    if not conn:
        return {}
    try:
        total_idx = conn.execute("SELECT count(DISTINCT ts_code) FROM dc_index").fetchone()[0]
        total_daily = conn.execute("SELECT count(DISTINCT ts_code) FROM dc_daily").fetchone()[0]
        latest = get_dc_latest_trade_date()
        latest_cnt = 0
        if latest:
            latest_cnt = conn.execute(
                "SELECT count(DISTINCT ts_code) FROM dc_daily WHERE trade_date = ?",
                [latest]
            ).fetchone()[0]
        return {
            'total_index': total_idx or 0,
            'total_daily': total_daily or 0,
            'latest_trade_date': latest,
            'latest_daily': latest_cnt or 0
        }
    except Exception as e:
        st.error(f"统计 DC 数据失败: {e}")
        return {}
    finally:
        conn.close()


@st.cache_data
def load_dc_index_list():
    conn = get_dc_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            WITH latest AS (
                SELECT ts_code, name,
                       ROW_NUMBER() OVER(PARTITION BY ts_code ORDER BY trade_date DESC) AS rn
                FROM dc_index
            )
            SELECT ts_code, name FROM latest WHERE rn = 1 ORDER BY ts_code
            """
        ).fetchdf()
        return df
    except Exception as e:
        st.error(f"加载 DC 指数列表失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data
def load_dc_top_bottom(trade_date: str, top_n: int = 10):
    conn = get_dc_connection()
    if not conn:
        return pd.DataFrame(), pd.DataFrame()
    try:
        base_name = conn.execute(
            """
            WITH latest AS (
                SELECT ts_code, name,
                       ROW_NUMBER() OVER(PARTITION BY ts_code ORDER BY trade_date DESC) AS rn
                FROM dc_index
            )
            SELECT ts_code, name FROM latest WHERE rn = 1
            """
        ).fetchdf()
        name_map = dict(zip(base_name['ts_code'], base_name['name'])) if not base_name.empty else {}

        df = conn.execute(
            """
            SELECT ts_code, trade_date, pct_change, vol, amount, turnover_rate, close
            FROM dc_daily
            WHERE trade_date = ?
            """,
            [trade_date]
        ).fetchdf()
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        df['name'] = df['ts_code'].map(name_map)
        df = df.sort_values('pct_change', ascending=False)
        top_df = df.head(top_n)
        bottom_df = df.tail(top_n).sort_values('pct_change')
        return top_df, bottom_df
    except Exception as e:
        st.error(f"加载涨跌榜失败: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()


@st.cache_data
def load_dc_history(ts_codes: list, start_date: str, end_date: str):
    if not ts_codes:
        return pd.DataFrame()
    conn = get_dc_connection()
    if not conn:
        return pd.DataFrame()
    codes_placeholder = ",".join([f"'{c}'" for c in ts_codes])
    try:
        df = conn.execute(
            f"""
            SELECT ts_code, trade_date, close, pct_change, vol, amount, turnover_rate
            FROM dc_daily
            WHERE trade_date >= '{start_date}' AND trade_date <= '{end_date}'
              AND ts_code IN ({codes_placeholder})
            ORDER BY trade_date
            """
        ).fetchdf()
        return df
    except Exception as e:
        st.error(f"加载历史数据失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
