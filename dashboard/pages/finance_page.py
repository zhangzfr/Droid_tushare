import streamlit as st
import pandas as pd
from typing import Optional

from dashboard.components.headers import render_header
from dashboard.finance_charts import (
    plot_balance_sankey,
    plot_balance_stack,
    plot_cashflow_timeseries,
    plot_cashflow_waterfall,
    plot_dupont_treemap,
    plot_financial_health_gauge,
    plot_forecast_vs_actual,
    plot_indicator_heatmap,
    plot_leverage_trend,
    plot_mainbz_pie,
    plot_profitability_trend,
)
from dashboard.finance_data_loader import (
    load_audit,
    load_balancesheet,
    load_cashflow,
    load_disclosure_dates,
    load_dividend,
    load_express,
    load_fina_indicator,
    load_forecast,
    load_income,
    load_mainbz,
    load_stock_universe,
)


def _pick_latest(df: pd.DataFrame) -> Optional[pd.Series]:
    if df is None or df.empty or "end_date_dt" not in df.columns:
        return None
    d = df.dropna(subset=["end_date_dt"]).sort_values("end_date_dt")
    if d.empty:
        return None
    return d.iloc[-1]


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _compute_health_score(df_indicator: pd.DataFrame, df_forecast: pd.DataFrame, df_express: pd.DataFrame, df_income: pd.DataFrame, df_dividend: pd.DataFrame):
    latest = _pick_latest(df_indicator)
    if latest is None:
        return None

    roe = _to_float(latest.get("roe"))
    ocf_to_or = _to_float(latest.get("ocf_to_or"))
    debt_to_assets = _to_float(latest.get("debt_to_assets"))

    subscores = {}
    weights = {
        "roe": 30,
        "cash": 20,
        "debt": 20,
        "forecast": 20,
        "dividend": 10,
    }

    if roe is not None:
        subscores["roe"] = max(0.0, min(roe, 20.0)) / 20.0 * 100.0

    if ocf_to_or is not None:
        subscores["cash"] = max(0.0, min(ocf_to_or, 20.0)) / 20.0 * 100.0

    if debt_to_assets is not None:
        subscores["debt"] = (1.0 - (max(0.0, min(debt_to_assets, 80.0)) / 80.0)) * 100.0

    # Forecast accuracy: latest forecast end_date actual in [min, max] => 100 else 0
    f_latest = _pick_latest(df_forecast)
    if f_latest is not None:
        end_date = str(f_latest.get("end_date"))
        min_wan = _to_float(f_latest.get("net_profit_min"))
        max_wan = _to_float(f_latest.get("net_profit_max"))
        if min_wan is not None and max_wan is not None:
            min_yi = min_wan / 1e4
            max_yi = max_wan / 1e4
            actual_yi = None
            if df_express is not None and not df_express.empty and "end_date" in df_express.columns:
                hit = df_express[df_express["end_date"].astype(str) == end_date]
                if not hit.empty:
                    actual = _to_float(hit.sort_values("ann_date").iloc[-1].get("n_income"))
                    if actual is not None:
                        actual_yi = actual / 1e8
            if actual_yi is None and df_income is not None and not df_income.empty and "end_date" in df_income.columns:
                hit = df_income[df_income["end_date"].astype(str) == end_date]
                if not hit.empty:
                    actual = _to_float(hit.sort_values("ann_date").iloc[-1].get("n_income"))
                    if actual is not None:
                        actual_yi = actual / 1e8

            if actual_yi is not None:
                subscores["forecast"] = 100.0 if (min_yi <= actual_yi <= max_yi) else 0.0

    # Dividend: latest year cash_div>0 => 100 else 0
    if df_dividend is not None and not df_dividend.empty and "cash_div" in df_dividend.columns:
        cash_div = pd.to_numeric(df_dividend.sort_values("end_date").iloc[-1].get("cash_div"), errors="coerce")
        if pd.notna(cash_div):
            subscores["dividend"] = 100.0 if cash_div > 0 else 0.0

    if not subscores:
        return None

    active_weight_sum = sum(weights[k] for k in subscores.keys())
    if active_weight_sum <= 0:
        return None

    score = 0.0
    for k, v in subscores.items():
        score += (weights[k] / active_weight_sum) * v
    return score


def render_finance_page(subcategory_key=None):
    render_header("Financial Analysis / 财务分析", "finance")

    st.markdown(
        "数据源：本地 DuckDB `tushare_duck_finance.db`（income / balance / cashflow / forecast / express / dividend / fina_indicator / fina_audit / fina_mainbz / disclosure_date）"
    )
    st.divider()

    left_col, right_col = st.columns([1, 5])

    with left_col:
        st.markdown("**Stock / 个股选择**")
        universe = load_stock_universe(limit=3000)

        options = []
        if not universe.empty:
            options = [
                f"{r.ts_code} - {r.name}" + (f" ({r.industry})" if getattr(r, "industry", None) else "")
                for r in universe.itertuples(index=False)
            ]
        picked = st.selectbox(
            "A-share (sample)",
            options=options,
            index=0 if options else None,
            key="fin_stock_pick",
        )
        ts_code_default = picked.split(" - ", 1)[0] if picked else ""
        ts_code = st.text_input("TS Code", value=ts_code_default, key="fin_ts_code").strip()

        st.markdown("**Report periods / 报告期数量**")
        periods = st.slider("Quarters", min_value=4, max_value=24, value=12, step=4, key="fin_periods")

    if not ts_code:
        st.info("请先选择或输入 ts_code。")
        return

    with st.spinner("Loading financial data..."):
        df_income = load_income(ts_code, periods)
        df_balance = load_balancesheet(ts_code, periods)
        df_cashflow = load_cashflow(ts_code, periods)
        df_ind = load_fina_indicator(ts_code, periods)
        df_forecast = load_forecast(ts_code, periods)
        df_express = load_express(ts_code, periods)
        df_div = load_dividend(ts_code)
        df_mainbz = load_mainbz(ts_code)
        df_audit = load_audit(ts_code)
        df_disc = load_disclosure_dates(ts_code)

    if df_income.empty and df_balance.empty and df_cashflow.empty and df_ind.empty:
        st.warning("未查询到该股票的财务数据（请确认 finance DB 已加载且包含该 ts_code）。")
        return

    latest_ind = _pick_latest(df_ind)
    latest_bal = _pick_latest(df_balance)
    latest_cf = _pick_latest(df_cashflow)

    with right_col:
        tab_overview, tab_profit, tab_balance, tab_cash, tab_events, tab_biz = st.tabs(
            [
                "📊 Overview",
                "💰 Profitability",
                "🏦 Balance Sheet",
                "💧 Cashflow",
                "🔭 Forecast & Audit",
                "🧩 Dividend & Business",
            ]
        )

        with tab_overview:
            c1, c2, c3, c4 = st.columns(4)
            if latest_ind is not None:
                roe = latest_ind.get("roe")
                debt = latest_ind.get("debt_to_assets")
                ocf = latest_ind.get("ocf_to_or")
                npm = latest_ind.get("netprofit_margin")
                c1.metric("ROE", f"{roe:.2f}%" if pd.notna(roe) else "-")
                c2.metric("Debt/Assets", f"{debt:.2f}%" if pd.notna(debt) else "-")
                c3.metric("OCF/Revenue", f"{ocf:.2f}%" if pd.notna(ocf) else "-")
                c4.metric("Net Profit Margin", f"{npm:.2f}%" if pd.notna(npm) else "-")
            else:
                st.info("fina_indicator 缺失，Overview 指标将不完整。")

            score = _compute_health_score(df_ind, df_forecast, df_express, df_income, df_div)
            col_g, col_hm = st.columns([1, 2])
            with col_g:
                fig_g = plot_financial_health_gauge(score)
                if fig_g:
                    st.plotly_chart(fig_g, use_container_width=True, key="fin_health_gauge")
                else:
                    st.info("无法计算综合评分（缺少关键指标）。")
            with col_hm:
                fig_hm = plot_indicator_heatmap(df_ind)
                if fig_hm:
                    st.plotly_chart(fig_hm, use_container_width=True, key="fin_indicator_heatmap")
                else:
                    st.info("无法生成指标热力图。")

        with tab_profit:
            fig_p = plot_profitability_trend(df_income)
            if fig_p:
                st.plotly_chart(fig_p, use_container_width=True, key="fin_profit_trend")
            else:
                st.info("利润表数据不足，无法绘制趋势图。")

            fig_dupont = plot_dupont_treemap(df_ind)
            if fig_dupont:
                st.plotly_chart(fig_dupont, use_container_width=True, key="fin_dupont")
            else:
                st.info("杜邦分解所需指标不足。")

            with st.expander("Raw tables"):
                if not df_income.empty:
                    st.dataframe(df_income.sort_values("end_date", ascending=False), use_container_width=True)
                if not df_ind.empty:
                    st.dataframe(df_ind.sort_values("end_date", ascending=False), use_container_width=True)

        with tab_balance:
            fig_l = plot_leverage_trend(df_balance)
            if fig_l:
                st.plotly_chart(fig_l, use_container_width=True, key="fin_leverage")

            fig_stack = plot_balance_stack(df_balance)
            if fig_stack:
                st.plotly_chart(fig_stack, use_container_width=True, key="fin_balance_stack")

            fig_sankey = plot_balance_sankey(df_balance)
            if fig_sankey:
                st.plotly_chart(fig_sankey, use_container_width=True, key="fin_balance_sankey")

            if latest_bal is None:
                st.info("balance 数据缺失。")

        with tab_cash:
            fig_ts = plot_cashflow_timeseries(df_cashflow)
            if fig_ts:
                st.plotly_chart(fig_ts, use_container_width=True, key="fin_cash_ts")
            else:
                st.info("现金流数据不足。")

            fig_wf = plot_cashflow_waterfall(df_cashflow)
            if fig_wf:
                st.plotly_chart(fig_wf, use_container_width=True, key="fin_cash_wf")

            if latest_cf is None:
                st.info("cashflow 数据缺失。")

        with tab_events:
            fig_fa = plot_forecast_vs_actual(df_forecast, df_express, df_income)
            if fig_fa:
                st.plotly_chart(fig_fa, use_container_width=True, key="fin_forecast_actual")
            else:
                st.info("forecast/express 数据不足，无法生成对比图。")

            col_a, col_d = st.columns(2)
            with col_a:
                st.markdown("#### Audit (fina_audit)")
                if not df_audit.empty:
                    st.dataframe(df_audit.head(10), use_container_width=True)
                else:
                    st.info("No audit records.")
            with col_d:
                st.markdown("#### Disclosure Schedule")
                if not df_disc.empty:
                    st.dataframe(df_disc.head(10), use_container_width=True)
                else:
                    st.info("No disclosure schedule records.")

        with tab_biz:
            col_div, col_bz = st.columns(2)
            with col_div:
                st.markdown("#### Dividend")
                if not df_div.empty:
                    st.dataframe(
                        df_div.sort_values(["end_date", "ann_date"], ascending=False).head(15),
                        use_container_width=True,
                    )
                else:
                    st.info("No dividend records.")
            with col_bz:
                fig_bz = plot_mainbz_pie(df_mainbz)
                if fig_bz:
                    st.plotly_chart(fig_bz, use_container_width=True, key="fin_mainbz_pie")
                else:
                    st.info("No main business breakdown.")
