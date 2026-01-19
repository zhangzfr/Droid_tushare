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
        print(f"DEBUG ERROR: {e}")
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
        "oper_cost",
        "sell_exp",
        "admin_exp",
        "fin_exp",
        "biz_tax_surchg",
        "income_tax",
        "rd_exp",
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
        "depr_fa_coga_dpba",     # Depreciation of Fixed Assets, Oil & Gas, Productive Bio Assets
        "amort_intang_assets",   # Amortization of Intangible Assets
        "lt_amort_deferred_exp", # Amortization of Long-term Deferred Expenses
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
def load_extended_indicator(ts_code: str, limit_periods: int = 20) -> pd.DataFrame:
    """Load extended financial indicators for deep insight analysis."""
    cols = [
        "ts_code",
        "ann_date",
        "end_date",
        "update_flag",
        # Profitability
        "roe", "roe_waa", "roa", "roic",
        "profit_to_gr", "netprofit_margin", "grossprofit_margin",
        # Cash Flow
        "fcff", "fcfe", "ocfps", "cfps",
        "ocf_to_or", "ocf_to_opincome", "ocf_to_profit",
        # Leverage & Coverage
        "debt_to_assets", "debt_to_eqt", "assets_to_eqt",
        "ebit_to_interest", "current_ratio", "quick_ratio", "cash_ratio",
        # Efficiency
        "assets_turn", "invturn_days", "arturn_days", "ca_turn", "fa_turn",
        # Growth YoY
        "netprofit_yoy", "tr_yoy", "or_yoy", "roe_yoy", "basic_eps_yoy", "ocf_yoy",
        # Growth QoQ
        "q_netprofit_qoq", "q_gr_qoq", "q_sales_qoq", "q_profit_qoq",
        # Per Share
        "eps", "bps",
    ]
    return _load_finance_table(ts_code, "fina_indicator", cols, limit_periods)


@st.cache_data(ttl=3600)
def load_industry_peers(ts_code: str, limit: int = 15) -> pd.DataFrame:
    """Load stocks in the same industry for peer comparison."""
    conn = get_stock_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            WITH target AS (
                SELECT industry FROM stock_basic WHERE ts_code = ?
            )
            SELECT sb.ts_code, sb.name, sb.industry
            FROM stock_basic sb, target t
            WHERE sb.industry = t.industry
              AND sb.list_status = 'L'
              AND sb.ts_code != ?
            ORDER BY sb.ts_code
            LIMIT ?
            """,
            [ts_code, ts_code, int(limit)],
        ).fetchdf()
        return df
    except Exception as e:
        st.error(f"Failed to load industry peers for {ts_code}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_peer_indicators_latest(ts_codes: tuple, period: str = None) -> pd.DataFrame:
    """Load latest fina_indicator for multiple stocks (for peer comparison)."""
    conn = get_finance_db_connection()
    if not conn or not ts_codes:
        return pd.DataFrame()
    
    placeholders = ", ".join(["?"] * len(ts_codes))
    try:
        if period:
            # Load specific period
            df = conn.execute(
                f"""
                SELECT ts_code, end_date, roe, roa, roic,
                       netprofit_margin, grossprofit_margin,
                       debt_to_assets, current_ratio, assets_turn,
                       netprofit_yoy, tr_yoy, fcff
                FROM fina_indicator
                WHERE ts_code IN ({placeholders}) AND end_date = ?
                """,
                list(ts_codes) + [period],
            ).fetchdf()
        else:
            # Load latest period per stock
            df = conn.execute(
                f"""
                WITH ranked AS (
                    SELECT *, ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY end_date DESC) as rn
                    FROM fina_indicator
                    WHERE ts_code IN ({placeholders})
                )
                SELECT ts_code, end_date, roe, roa, roic,
                       netprofit_margin, grossprofit_margin,
                       debt_to_assets, current_ratio, assets_turn,
                       netprofit_yoy, tr_yoy, fcff
                FROM ranked WHERE rn = 1
                """,
                list(ts_codes),
            ).fetchdf()
    except Exception as e:
        st.error(f"Failed to load peer indicators: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
    return df


def calculate_earnings_quality(df_income: pd.DataFrame, df_cashflow: pd.DataFrame, df_balance: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate earnings quality metrics:
    - Accrual Ratio = (Net Income - OCF) / Total Assets
    - Cash Conversion = OCF / Net Income
    """
    if df_income.empty or df_cashflow.empty or df_balance.empty:
        return pd.DataFrame()
    
    # Merge on end_date
    merged = df_income[["end_date", "n_income"]].merge(
        df_cashflow[["end_date", "n_cashflow_act"]], on="end_date", how="inner"
    ).merge(
        df_balance[["end_date", "total_assets"]], on="end_date", how="inner"
    )
    
    if merged.empty:
        return pd.DataFrame()
    
    for col in ["n_income", "n_cashflow_act", "total_assets"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
    
    # Accrual Ratio: high value may indicate low earnings quality
    merged["accrual_ratio"] = (merged["n_income"] - merged["n_cashflow_act"]) / merged["total_assets"]
    
    # Cash Conversion: OCF / NI, ideally > 0.7
    merged["cash_conversion"] = merged["n_cashflow_act"] / merged["n_income"].replace(0, float("nan"))
    
    return merged


def calculate_piotroski_score(df_ind: pd.DataFrame, df_income: pd.DataFrame, df_balance: pd.DataFrame) -> dict:
    """
    Calculate simplified Piotroski F-Score (9 criteria).
    Returns dict with individual scores and total.
    """
    if df_ind.empty or len(df_ind) < 2:
        return {"total": None, "details": {}}
    
    df = df_ind.sort_values("end_date_dt" if "end_date_dt" in df_ind.columns else "end_date", ascending=False).head(2)
    latest = df.iloc[0]
    prior = df.iloc[1]
    
    scores = {}
    
    # 1. ROA > 0
    roa = pd.to_numeric(latest.get("roa"), errors="coerce")
    scores["roa_positive"] = 1 if pd.notna(roa) and roa > 0 else 0
    
    # 2. Operating Cash Flow > 0
    ocf = pd.to_numeric(latest.get("ocf_to_or"), errors="coerce")
    scores["ocf_positive"] = 1 if pd.notna(ocf) and ocf > 0 else 0
    
    # 3. ROA improving
    roa_prior = pd.to_numeric(prior.get("roa"), errors="coerce")
    scores["roa_improving"] = 1 if pd.notna(roa) and pd.notna(roa_prior) and roa > roa_prior else 0
    
    # 4. OCF > Net Income (quality of earnings)
    ocf_to_profit = pd.to_numeric(latest.get("ocf_to_profit"), errors="coerce")
    scores["ocf_gt_ni"] = 1 if pd.notna(ocf_to_profit) and ocf_to_profit > 100 else 0
    
    # 5. Leverage decreasing
    debt = pd.to_numeric(latest.get("debt_to_assets"), errors="coerce")
    debt_prior = pd.to_numeric(prior.get("debt_to_assets"), errors="coerce")
    scores["leverage_down"] = 1 if pd.notna(debt) and pd.notna(debt_prior) and debt < debt_prior else 0
    
    # 6. Current ratio improving
    cr = pd.to_numeric(latest.get("current_ratio"), errors="coerce")
    cr_prior = pd.to_numeric(prior.get("current_ratio"), errors="coerce")
    scores["liquidity_up"] = 1 if pd.notna(cr) and pd.notna(cr_prior) and cr > cr_prior else 0
    
    # 7. No equity dilution (simplified: check if shares increased - not available, assume 1)
    scores["no_dilution"] = 1
    
    # 8. Gross margin improving
    gm = pd.to_numeric(latest.get("grossprofit_margin"), errors="coerce")
    gm_prior = pd.to_numeric(prior.get("grossprofit_margin"), errors="coerce")
    scores["margin_up"] = 1 if pd.notna(gm) and pd.notna(gm_prior) and gm > gm_prior else 0
    
    # 9. Asset turnover improving
    at = pd.to_numeric(latest.get("assets_turn"), errors="coerce")
    at_prior = pd.to_numeric(prior.get("assets_turn"), errors="coerce")
    scores["turnover_up"] = 1 if pd.notna(at) and pd.notna(at_prior) and at > at_prior else 0
    
    total = sum(scores.values())
    return {"total": total, "details": scores}


def detect_anomalies(df_ind: pd.DataFrame) -> list:
    """
    Detect financial anomalies and return list of warning messages.
    """
    if df_ind.empty or len(df_ind) < 2:
        return []
    
    alerts = []
    df = df_ind.sort_values("end_date_dt" if "end_date_dt" in df_ind.columns else "end_date", ascending=False)
    
    # 1. Gross margin compression: 2+ consecutive drops > 2pp
    if "grossprofit_margin" in df.columns and len(df) >= 3:
        gm = pd.to_numeric(df["grossprofit_margin"], errors="coerce").head(3).values
        if len(gm) >= 3 and all(pd.notna(gm)):
            if gm[0] < gm[1] - 2 and gm[1] < gm[2] - 2:
                alerts.append(("warning", "⚠️ 毛利率连续2期下降超过2个百分点，可能面临成本压力"))
    
    # 2. Leverage spike: single period jump > 5pp
    if "debt_to_assets" in df.columns and len(df) >= 2:
        debt = pd.to_numeric(df["debt_to_assets"], errors="coerce").head(2).values
        if len(debt) >= 2 and all(pd.notna(debt)):
            if debt[0] - debt[1] > 5:
                alerts.append(("error", "🚨 资产负债率单期上升超过5个百分点，杠杆风险上升"))
    
    # 3. AR turnover deterioration: days increased significantly
    if "arturn_days" in df.columns and len(df) >= 2:
        ar = pd.to_numeric(df["arturn_days"], errors="coerce").head(2).values
        if len(ar) >= 2 and all(pd.notna(ar)):
            if ar[0] > ar[1] * 1.3:  # 30% increase
                alerts.append(("warning", "⚠️ 应收账款周转天数显著延长，现金回收可能放缓"))
    
    # 4. Net profit margin vs gross margin divergence
    if "netprofit_margin" in df.columns and "grossprofit_margin" in df.columns:
        npm = pd.to_numeric(df["netprofit_margin"].iloc[0], errors="coerce")
        gpm = pd.to_numeric(df["grossprofit_margin"].iloc[0], errors="coerce")
        if pd.notna(npm) and pd.notna(gpm) and gpm > 0:
            if npm < gpm * 0.1:  # Net margin < 10% of gross margin
                alerts.append(("info", "ℹ️ 净利率占毛利率比例较低，费用控制可能是关键"))
    
    return alerts


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
def load_mainbz(ts_code: str, limit_periods: int = 200) -> pd.DataFrame:
    conn = get_finance_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = conn.execute(
            """
            SELECT ts_code, end_date, bz_item, bz_sales, bz_profit, bz_cost, curr_type, bz_code
            FROM fina_mainbz
            WHERE ts_code = ?
            ORDER BY end_date DESC, bz_sales DESC
            LIMIT ?
            """,
            [ts_code, int(limit_periods)],
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
