import os

import duckdb
import pandas as pd
import streamlit as st


def _default_db_root() -> str:
    return os.getenv("DB_ROOT", "/Users/robert/Developer/DuckDB")


FINANCE_DB_PATH = os.getenv(
    "FINANCE_DB_PATH", os.path.join(_default_db_root(), "tushare_duck_finance.db")
)

STOCK_DB_PATH = os.getenv(
    "STOCK_DB_PATH", os.path.join(_default_db_root(), "tushare_duck_stock.db")
)


def get_finance_db_connection():
    try:
        return duckdb.connect(FINANCE_DB_PATH, read_only=True)
    except Exception as e:
        st.error(f"Error connecting to finance database at {FINANCE_DB_PATH}: {e}")
        return None


def get_stock_db_connection():
    try:
        return duckdb.connect(STOCK_DB_PATH, read_only=True)
    except Exception as e:
        st.error(f"Error connecting to stock database at {STOCK_DB_PATH}: {e}")
        return None


def _parse_yyyymmdd(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype(str), format="%Y%m%d", errors="coerce")


def _dedup_by_end_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "end_date" not in df.columns:
        return df
    out = df.copy()
    if "update_flag" in out.columns:
        out["_update_flag_rank"] = (
            out["update_flag"].fillna("0").astype(str).str.replace("[^0-9]", "0", regex=True).astype(int)
        )
    else:
        out["_update_flag_rank"] = 0
    if "ann_date" in out.columns:
        out["_ann_date_dt"] = _parse_yyyymmdd(out["ann_date"]) 
    else:
        out["_ann_date_dt"] = pd.NaT

    out["_end_date_dt"] = _parse_yyyymmdd(out["end_date"]) 
    out = out.sort_values(["_end_date_dt", "_ann_date_dt", "_update_flag_rank"], ascending=[False, False, False])
    out = out.drop_duplicates(["end_date"], keep="first")
    return out.drop(columns=["_update_flag_rank", "_ann_date_dt", "_end_date_dt"], errors="ignore")


@st.cache_data(ttl=3600)
def load_stock_universe(limit: int = 3000) -> pd.DataFrame:
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            SELECT ts_code, name, industry, list_status
            FROM stock_basic
            WHERE list_status = 'L'
            ORDER BY ts_code
            LIMIT ?
            """,
            [limit],
        ).fetchdf()
        return df
    except Exception as e:
        st.error(f"Failed to load stock universe: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def _load_finance_table(ts_code: str, table: str, columns: list[str], limit_periods: int) -> pd.DataFrame:
    conn = get_finance_db_connection()
    if not conn:
        return pd.DataFrame()
    cols_sql = ", ".join(columns)
    try:
        df = conn.execute(
            f"""
            SELECT {cols_sql}
            FROM {table}
            WHERE ts_code = ?
            ORDER BY end_date DESC
            LIMIT ?
            """,
            [ts_code, int(limit_periods)],
        ).fetchdf()
    except Exception as e:
        st.error(f"Failed to load {table} for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df
    if "end_date" in df.columns:
        df["end_date_dt"] = _parse_yyyymmdd(df["end_date"])
    if "ann_date" in df.columns:
        df["ann_date_dt"] = _parse_yyyymmdd(df["ann_date"])
    df = _dedup_by_end_date(df)
    return df.sort_values("end_date", ascending=True)


@st.cache_data(ttl=3600)
def load_income(ts_code: str, limit_periods: int = 12) -> pd.DataFrame:
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        "revenue",
        "total_revenue",
        "total_cogs",
        "operate_profit",
        "total_profit",
        "n_income",
        "ebit",
        "ebitda",
    ]
    return _load_finance_table(ts_code, "income", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_balancesheet(ts_code: str, limit_periods: int = 12) -> pd.DataFrame:
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        "total_assets",
        "total_liab",
        "total_hldr_eqy_exc_min_int",
        "total_cur_assets",
        "total_nca",
        "total_cur_liab",
        "total_ncl",
    ]
    # NOTE: In the local finance DB the table name is `balance` (not `balancesheet`).
    return _load_finance_table(ts_code, "balance", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_cashflow(ts_code: str, limit_periods: int = 12) -> pd.DataFrame:
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        "n_cashflow_act",
        "n_cashflow_inv_act",
        "n_cash_flows_fnc_act",
        "eff_fx_flu_cash",
        "c_cash_equ_beg_period",
        "c_cash_equ_end_period",
        "free_cashflow",
    ]
    return _load_finance_table(ts_code, "cashflow", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_fina_indicator(ts_code: str, limit_periods: int = 12) -> pd.DataFrame:
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        "roe",
        "profit_to_gr",
        "netprofit_margin",
        "assets_turn",
        "dp_assets_to_eqt",
        "debt_to_assets",
        "current_ratio",
        "quick_ratio",
        "ocf_to_or",
    ]
    return _load_finance_table(ts_code, "fina_indicator", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_forecast(ts_code: str, limit_periods: int = 12) -> pd.DataFrame:
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        "type",
        "p_change_min",
        "p_change_max",
        "net_profit_min",
        "net_profit_max",
        "summary",
    ]
    return _load_finance_table(ts_code, "forecast", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_express(ts_code: str, limit_periods: int = 12) -> pd.DataFrame:
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        "revenue",
        "n_income",
        "diluted_roe",
        "yoy_sales",
        "yoy_dedu_np",
        "perf_summary",
        "is_audit",
    ]
    return _load_finance_table(ts_code, "express", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_dividend(ts_code: str, limit_rows: int = 200) -> pd.DataFrame:
    conn = get_finance_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            SELECT ts_code, end_date, ann_date, div_proc, cash_div, cash_div_tax, stk_div,
                   record_date, ex_date, pay_date
            FROM dividend
            WHERE ts_code = ?
            ORDER BY end_date DESC, ann_date DESC
            LIMIT ?
            """,
            [ts_code, int(limit_rows)],
        ).fetchdf()
    except Exception as e:
        st.error(f"Failed to load dividend for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df
    df["end_date_dt"] = _parse_yyyymmdd(df["end_date"])
    df["ann_date_dt"] = _parse_yyyymmdd(df["ann_date"])
    return df.sort_values(["end_date_dt", "ann_date_dt"], ascending=[True, True])


@st.cache_data(ttl=3600)
def load_mainbz(ts_code: str, limit_rows: int = 200) -> pd.DataFrame:
    conn = get_finance_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            SELECT ts_code, end_date, bz_item, bz_sales, bz_profit, bz_cost, curr_type
            FROM fina_mainbz
            WHERE ts_code = ?
            ORDER BY end_date DESC, bz_sales DESC
            LIMIT ?
            """,
            [ts_code, int(limit_rows)],
        ).fetchdf()
    except Exception as e:
        st.error(f"Failed to load main business for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df
    df["end_date_dt"] = _parse_yyyymmdd(df["end_date"])
    return df


@st.cache_data(ttl=3600)
def load_audit(ts_code: str, limit_rows: int = 50) -> pd.DataFrame:
    conn = get_finance_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            SELECT ts_code, ann_date, end_date, audit_result, audit_fees, audit_agency, audit_sign
            FROM fina_audit
            WHERE ts_code = ?
            ORDER BY end_date DESC, ann_date DESC
            LIMIT ?
            """,
            [ts_code, int(limit_rows)],
        ).fetchdf()
    except Exception as e:
        st.error(f"Failed to load audit for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df
    df["end_date_dt"] = _parse_yyyymmdd(df["end_date"])
    df["ann_date_dt"] = _parse_yyyymmdd(df["ann_date"])
    return df.sort_values(["end_date_dt", "ann_date_dt"], ascending=[False, False])


@st.cache_data(ttl=3600)
def load_disclosure_dates(ts_code: str, limit_rows: int = 80) -> pd.DataFrame:
    conn = get_finance_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            SELECT ts_code, ann_date, end_date, pre_date, actual_date, modify_date
            FROM disclosure_date
            WHERE ts_code = ?
            ORDER BY end_date DESC, ann_date DESC
            LIMIT ?
            """,
            [ts_code, int(limit_rows)],
        ).fetchdf()
    except Exception as e:
        st.error(f"Failed to load disclosure dates for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return df
    for c in ["ann_date", "end_date", "pre_date", "actual_date", "modify_date"]:
        if c in df.columns:
            df[f"{c}_dt"] = _parse_yyyymmdd(df[c])
    if "pre_date_dt" in df.columns and "actual_date_dt" in df.columns:
        df["disclosure_delay_days"] = (df["actual_date_dt"] - df["pre_date_dt"]).dt.days
    return df.sort_values("end_date_dt", ascending=False)
