import streamlit as st
import pandas as pd
from typing import Optional

from dashboard.components.headers import render_header
from dashboard.finance_charts import (
    plot_balance_stack,
    plot_cashflow_timeseries,
    plot_cashflow_waterfall,
    plot_dupont_treemap,
    plot_dupont_trend,
    plot_forecast_vs_actual,
    plot_growth_quality_scatter,
    plot_leverage_trend,
    plot_mainbz_structure_trend,
    plot_income_sankey,
    plot_income_waterfall,
    plot_profitability_trend,
    # Deep Insights charts
    plot_ocf_ni_divergence,
    plot_piotroski_score_radar,
    plot_margin_trend_with_alerts,
    plot_peer_percentile_bars,
    plot_growth_quality_scatter,
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
    # Deep Insights functions
    load_extended_indicator,
    load_industry_peers,
    load_peer_indicators_latest,
    calculate_earnings_quality,
    calculate_piotroski_score,
    detect_anomalies,
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


def _get_cash_health_label(ocf_to_or):
    """Convert OCF/Revenue ratio to user-friendly label."""
    if ocf_to_or is None or pd.isna(ocf_to_or):
        return "-", "off"
    if ocf_to_or >= 15:
        return "优秀", "normal"
    elif ocf_to_or >= 8:
        return "良好", "normal"
    elif ocf_to_or >= 0:
        return "一般", "off"
    else:
        return "偏弱", "inverse"


def render_finance_page(subcategory_key=None):
    render_header("财务分析 / Financial Analysis", "finance")

    st.markdown(
        "数据源：本地 DuckDB `tushare_duck_finance.db`"
    )
    st.divider()

    left_col, right_col = st.columns([1, 5])

    with left_col:
        st.markdown("**选择股票**")
        universe = load_stock_universe(limit=3000)

        options = []
        if not universe.empty:
            options = [
                f"{r.ts_code} - {r.name}" + (f" ({r.industry})" if getattr(r, "industry", None) else "")
                for r in universe.itertuples(index=False)
            ]
        picked = st.selectbox(
            "A股 (示例)",
            options=options,
            index=0 if options else None,
            key="fin_stock_pick",
        )
        ts_code_default = picked.split(" - ", 1)[0] if picked else ""
        ts_code = st.text_input("股票代码", value=ts_code_default, key="fin_ts_code").strip()

        st.markdown("**报告期数量**")
        periods = st.slider("季度数", min_value=4, max_value=24, value=12, step=4, key="fin_periods")

    if not ts_code:
        st.info("请先选择或输入股票代码。")
        return

    with st.spinner("加载财务数据..."):
        df_income = load_income(ts_code, limit_periods=60)
        df_balance = load_balancesheet(ts_code, limit_periods=60)
        df_cashflow = load_cashflow(ts_code, limit_periods=60)
        df_ind = load_fina_indicator(ts_code, limit_periods=60)
        df_forecast = load_forecast(ts_code, periods)
        df_express = load_express(ts_code, periods)
        df_div = load_dividend(ts_code)
        df_mainbz = load_mainbz(ts_code, limit_periods=500) # Need more rows for mainbz details
        df_audit = load_audit(ts_code)
        df_disc = load_disclosure_dates(ts_code)
        df_ext = load_extended_indicator(ts_code, periods + 4)

    if df_income.empty and df_balance.empty and df_cashflow.empty and df_ind.empty:
        st.warning("未查询到该股票的财务数据（请确认数据库已加载）。")
        return

    latest_ind = _pick_latest(df_ind)

    with right_col:
        # ========== 4 TABS ==========
        tab_overview, tab_profit, tab_balance, tab_details = st.tabs([
            "📊 综合概览",
            "💰 盈利分析",
            "🏦 资产与现金",
            "📋 更多详情",
        ])

        # ========== TAB 1: 综合概览 ==========
        with tab_overview:
            # --- 异常预警置顶 ---
            alerts = detect_anomalies(df_ext)
            if alerts:
                for alert_type, msg in alerts:
                    if alert_type == "error":
                        st.error(msg)
                    elif alert_type == "warning":
                        st.warning(msg)
                    else:
                        st.info(msg)
            
            # --- 核心指标卡 (简单直观) ---
            st.markdown("### 核心指标")
            c1, c2, c3, c4 = st.columns(4)
            
            if latest_ind is not None:
                npm = latest_ind.get("netprofit_margin")
                roe = latest_ind.get("roe")
                debt = latest_ind.get("debt_to_assets")
                ocf = latest_ind.get("ocf_to_or")
                
                with c1:
                    st.metric(
                        "净利率",
                        f"{npm:.1f}%" if pd.notna(npm) else "-",
                        help="净利润/营业收入。表示每100元收入能赚多少钱。越高越好。"
                    )
                    st.caption("💡 赚钱能力")
                
                with c2:
                    st.metric(
                        "ROE (净资产收益率)",
                        f"{roe:.1f}%" if pd.notna(roe) else "-",
                        help="净利润/股东权益。衡量股东投入资金的回报率。一般10%以上较好。"
                    )
                    st.caption("💡 股东回报")
                
                with c3:
                    # 资产负债率 - 较低为好
                    delta_color = "normal" if pd.notna(debt) and debt < 60 else "inverse"
                    st.metric(
                        "资产负债率",
                        f"{debt:.1f}%" if pd.notna(debt) else "-",
                        delta="稳健" if pd.notna(debt) and debt < 60 else "偏高" if pd.notna(debt) else None,
                        delta_color=delta_color,
                        help="总负债/总资产。低于60%一般认为财务稳健。"
                    )
                    st.caption("💡 财务杠杆")
                
                with c4:
                    label, color = _get_cash_health_label(ocf)
                    st.metric(
                        "现金流健康度",
                        label,
                        help="基于经营现金流/营收比率。正向现金流说明企业能把利润变成真金白银。"
                    )
                    st.caption("💡 现金充裕度")
            else:
                st.info("财务指标数据缺失。")
            
            # --- 收入利润趋势 (最直观) ---
            st.markdown("### 收入与利润趋势")
            fig_p = plot_profitability_trend(df_income)
            if fig_p:
                st.plotly_chart(fig_p, use_container_width=True, key="fin_profit_trend")
            else:
                st.info("收入利润数据不足。")
            
            # --- 行业排名 ---
            st.markdown("### 行业排名")
            st.caption("您的股票在同行业中处于什么水平？")
            peers = load_industry_peers(ts_code, limit=15)
            if not peers.empty:
                all_codes = tuple([ts_code] + peers["ts_code"].tolist())
                df_peer_ind = load_peer_indicators_latest(all_codes)
                
                if not df_peer_ind.empty:
                    stock_name = None
                    if not universe.empty:
                        match = universe[universe["ts_code"] == ts_code]
                        if not match.empty:
                            stock_name = match.iloc[0].get("name")
                    
                    fig_peer = plot_peer_percentile_bars(ts_code, df_peer_ind, target_name=stock_name)
                    if fig_peer:
                        st.plotly_chart(fig_peer, use_container_width=True, key="fin_peer_rank")
                    else:
                        st.info("同行排名数据不足。")
                else:
                    st.info("同行财务数据不足。")
            else:
                st.info("未找到同行业公司进行比较。")

        # ========== TAB 2: 盈利分析 ==========
        with tab_profit:
            # --- 利润率趋势 ---
            st.markdown("### 利润率趋势")
            st.caption("毛利率和净利率的变化反映公司盈利能力的稳定性")
            fig_margin = plot_margin_trend_with_alerts(df_ext)
            if fig_margin:
                st.plotly_chart(fig_margin, use_container_width=True, key="fin_margin_alerts")
            else:
                st.info("利润率数据不足。")
            
            # --- 增长质量 ---
            st.markdown("### 增长质量")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.caption("收入增速 vs 利润增速对比")
                fig_growth = plot_growth_quality_scatter(df_ext)
                if fig_growth:
                    st.plotly_chart(fig_growth, use_container_width=True, key="fin_growth_quality")
                else:
                    st.info("增长数据不足。")
            
            with col_g2:
                st.caption("利润增速持续高于收入增速可能不可持续")
                if latest_ind is not None and "netprofit_yoy" in df_ext.columns:
                    latest_ext = df_ext.sort_values("end_date", ascending=False).iloc[0] if not df_ext.empty else None
                    if latest_ext is not None:
                        np_yoy = pd.to_numeric(latest_ext.get("netprofit_yoy"), errors="coerce")
                        tr_yoy = pd.to_numeric(latest_ext.get("tr_yoy"), errors="coerce")
                        if pd.notna(np_yoy) and pd.notna(tr_yoy):
                            st.metric("收入同比增速", f"{tr_yoy:.1f}%")
                            st.metric("净利润同比增速", f"{np_yoy:.1f}%")
            
            # --- 盈利质量 ---
            st.markdown("### 盈利质量")
            st.caption("利润能否转化为真金白银？")
            
            df_eq = calculate_earnings_quality(df_income, df_cashflow, df_balance)
            col_eq1, col_eq2 = st.columns(2)
            
            if not df_eq.empty:
                latest_eq = df_eq.sort_values("end_date", ascending=False).iloc[0]
                cash_conv = latest_eq.get("cash_conversion")
                accrual = latest_eq.get("accrual_ratio")
                
                with col_eq1:
                    if pd.notna(cash_conv):
                        pct = cash_conv * 100
                        status = "✅ 良好" if cash_conv >= 0.7 else "⚠️ 偏低"
                        st.metric(
                            "现金转换率",
                            f"{pct:.0f}%",
                            delta=status,
                            delta_color="normal" if cash_conv >= 0.7 else "inverse",
                        )
                        st.caption("经营现金流 / 净利润。理想值 > 70%")
                    else:
                        st.metric("现金转换率", "-")
                
                with col_eq2:
                    if pd.notna(accrual):
                        pct = accrual * 100
                        status = "✅ 正常" if accrual <= 0.05 else "⚠️ 偏高"
                        st.metric(
                            "应计比率",
                            f"{pct:.1f}%",
                            delta=status,
                            delta_color="normal" if accrual <= 0.05 else "inverse",
                        )
                        st.caption("(净利润-经营现金流)/总资产。高值可能暗示盈利质量低")
                    else:
                        st.metric("应计比率", "-")
            else:
                st.info("盈利质量数据不足。")
            
            # --- OCF/NI背离图 (可选) ---
            with st.expander("📊 查看 现金流与净利润背离图"):
                fig_div = plot_ocf_ni_divergence(df_eq)
                if fig_div:
                    st.plotly_chart(fig_div, use_container_width=True, key="fin_ocf_ni_div")
                else:
                    st.info("背离数据不足。")

        # ========== TAB 3: 资产与现金 ==========
        with tab_balance:
            # --- 杠杆趋势 ---
            st.markdown("### 杠杆趋势")
            st.caption("资产负债率的变化反映财务风险")
            fig_l = plot_leverage_trend(df_balance)
            if fig_l:
                st.plotly_chart(fig_l, use_container_width=True, key="fin_leverage")
            else:
                st.info("资产负债数据不足。")
            
            # --- 资产结构 ---
            st.markdown("### 资产结构")
            st.caption("负债 vs 股东权益的构成")
            fig_stack = plot_balance_stack(df_balance)
            if fig_stack:
                st.plotly_chart(fig_stack, use_container_width=True, key="fin_balance_stack")
            
            # --- 现金流趋势 ---
            st.markdown("### 现金流趋势")
            st.caption("经营活动、投资活动、筹资活动的现金流向")
            fig_ts = plot_cashflow_timeseries(df_cashflow)
            if fig_ts:
                st.plotly_chart(fig_ts, use_container_width=True, key="fin_cash_ts")
            else:
                st.info("现金流数据不足。")
            
            # --- 现金流瀑布 (可选) ---
            with st.expander("📊 查看 最新期现金流瀑布图"):
                fig_wf = plot_cashflow_waterfall(df_cashflow)
                if fig_wf:
                    st.plotly_chart(fig_wf, use_container_width=True, key="fin_cash_wf")
                else:
                    st.info("瀑布图数据不足。")

        # ========== TAB 4: 更多详情 ==========
        with tab_details:
            # --- Piotroski F-Score (带解释) ---
            st.markdown("### 📈 财务稳健性评分 (Piotroski F-Score)")
            
            with st.container():
                st.info("""
                **什么是 Piotroski F-Score？**
                
                由美国会计学教授 Joseph Piotroski 在2000年提出的财务健康评分系统。
                通过9个财务指标综合评估公司的盈利能力、财务杠杆和运营效率。
                
                - **7-9分**: 财务状况强健 ✅
                - **4-6分**: 财务状况中等 ⚠️
                - **0-3分**: 财务状况较弱 ❌
                """)
            
            piotroski = calculate_piotroski_score(df_ext, df_income, df_balance)
            
            if piotroski["total"] is not None:
                score = piotroski["total"]
                
                # Display score prominently
                col_score, col_radar = st.columns([1, 2])
                
                with col_score:
                    if score >= 7:
                        st.success(f"### 评分: {score}/9\n财务状况: **强健** ✅")
                    elif score >= 4:
                        st.warning(f"### 评分: {score}/9\n财务状况: **中等** ⚠️")
                    else:
                        st.error(f"### 评分: {score}/9\n财务状况: **较弱** ❌")
                
                with col_radar:
                    if piotroski["details"]:
                        fig_pio = plot_piotroski_score_radar(piotroski["details"])
                        if fig_pio:
                            st.plotly_chart(fig_pio, use_container_width=True, key="fin_piotroski_radar")
                
                # Show breakdown
                with st.expander("🔍 查看9项指标详情"):
                    details = piotroski["details"]
                    labels = {
                        "roa_positive": ("ROA > 0", "盈利为正"),
                        "ocf_positive": ("OCF > 0", "经营现金流为正"),
                        "roa_improving": ("ROA 改善", "盈利能力提升"),
                        "ocf_gt_ni": ("OCF > 净利润", "现金流质量好"),
                        "leverage_down": ("杠杆下降", "负债减少"),
                        "liquidity_up": ("流动性改善", "短期偿债能力提升"),
                        "no_dilution": ("无股权稀释", "未增发股票"),
                        "margin_up": ("毛利率改善", "盈利效率提升"),
                        "turnover_up": ("周转率改善", "资产使用效率提升"),
                    }
                    
                    for key, (name, desc) in labels.items():
                        val = details.get(key, 0)
                        icon = "✅" if val == 1 else "❌"
                        st.markdown(f"- {icon} **{name}**: {desc}")
            else:
                st.info("Piotroski 评分数据不足。")
            
            st.divider()
            
            # --- 杜邦分解 (五因素) ---
            with st.expander("📊 杜邦分解 (五因素模型)"):
                st.caption("ROE = 税负系数 × 利息负担 × 经营利润率 × 资产周转率 × 权益乘数")
                
                dupont_data = plot_dupont_treemap(df_ind, df_income, df_balance)
                
                if dupont_data and dupont_data.get("factors"):
                    # Display ROE header
                    roe_val = dupont_data.get("roe")
                    dupont_roe = dupont_data.get("dupont_roe")
                    
                    if roe_val is not None:
                        col_roe1, col_roe2 = st.columns(2)
                        with col_roe1:
                            st.metric("实际 ROE", f"{roe_val:.2f}%")
                        with col_roe2:
                            if dupont_roe is not None:
                                st.metric("杜邦计算 ROE", f"{dupont_roe:.2f}%")
                    
                    st.divider()
                    
                    # Display 5 factors in a structured layout
                    factors = dupont_data["factors"]
                    
                    for i, factor in enumerate(factors):
                        col1, col2, col3 = st.columns([1.5, 2, 3])
                        
                        with col1:
                            st.markdown(f"**{factor['name']}**")
                            st.markdown(f"### {factor['value']}")
                        
                        with col2:
                            st.caption(f"公式: {factor['formula']}")
                            st.caption(f"计算: {factor['components']}")
                        
                        with col3:
                            st.caption(factor['desc'])
                        
                        if i < len(factors) - 1:
                            st.markdown("---")
                    
                    # Formula summary
                    if dupont_data.get("formula"):
                        st.divider()
                        st.markdown(f"**计算公式:** {dupont_data['formula']}")
                    
                    # Trend chart
                    st.divider()
                    st.markdown("### 📈 趋势变化")
                    fig_trend = plot_dupont_trend(df_income, df_balance, df_ind)
                    if fig_trend:
                        st.plotly_chart(fig_trend, use_container_width=True, key="fin_dupont_trend")
                    else:
                        st.caption("趋势数据不足（需要至少2个期间）")
                else:
                    st.info("杜邦分解数据不足。")
            
            # --- 业绩预告 vs 实际 ---
            with st.expander("📊 业绩预告 vs 实际"):
                fig_fa = plot_forecast_vs_actual(df_forecast, df_express, df_income)
                if fig_fa:
                    st.plotly_chart(fig_fa, use_container_width=True, key="fin_forecast_actual")
                else:
                    st.info("业绩预告数据不足。")
            
            # --- 其他数据表 ---
            st.markdown("### 📋 原始数据")
            
            col_div, col_audit = st.columns(2)
            
            with col_div:
                with st.expander("💰 分红记录"):
                    if not df_div.empty:
                        st.dataframe(
                            df_div.sort_values(["end_date", "ann_date"], ascending=False).head(10),
                            use_container_width=True,
                        )
                    else:
                        st.info("暂无分红记录。")
            
            with col_audit:
                with st.expander("📝 审计意见"):
                    if not df_audit.empty:
                        st.dataframe(df_audit.head(10), use_container_width=True)
                    else:
                        st.info("暂无审计记录。")
            
            # --- 🏭 主营业务分析 (新) ---
            st.markdown("---")
            st.subheader("🏭 主营业务与利润流向")
            
            # 1. Main Business Structure & Trend
            st.markdown("#### 1. 主营业务分析 (Main Business Structure)")
            st.info("展示各个产品和地区对总收入的贡献及其随时间的变化趋势。")
            
            col_prod, col_region = st.columns(2)
            
            with col_prod:
                st.markdown("**按产品 (By Product)**")
                fig_prod = plot_mainbz_structure_trend(df_mainbz, type_filter='P')
                if fig_prod:
                    st.plotly_chart(fig_prod, use_container_width=True)
                else:
                    st.info("暂无产品明细数据")

            with col_region:
                st.markdown("**按地区 (By Region)**")
                fig_r = plot_mainbz_structure_trend(df_mainbz, type_filter='D')
                if fig_r:
                    st.plotly_chart(fig_r, use_container_width=True)
                else:
                    st.info("暂无地区明细数据")
                    
            # 2. Income Statement Flow (Sankey & Waterfall)
            st.markdown("#### 2. 利润流向分析 (Profit Flow)")
            st.info("展示从【收入】到【净利润】的层层转化过程。")
            
            tab_sankey, tab_waterfall = st.tabs(["🔄 桑基图 (Sankey)", "💧 瀑布图 (Waterfall)"])
            
            with tab_sankey:
                fig_sankey = plot_income_sankey(df_mainbz, df_income)
                if fig_sankey:
                    st.info("利润流向数据不足。")

            st.markdown("### 📋 原始数据")
            
            col_div, col_audit = st.columns(2)
            
            with col_div:
                with st.expander("💰 分红记录"):
                    if not df_div.empty:
                        st.dataframe(
                            df_div.sort_values(["end_date", "ann_date"], ascending=False).head(10),
                            use_container_width=True,
                        )
                    else:
                        st.info("暂无分红记录。")
            
            with col_audit:
                with st.expander("📝 审计意见"):
                    if not df_audit.empty:
                        st.dataframe(df_audit.head(10), use_container_width=True)
                    else:
                        st.info("暂无审计记录。")
            
            col_disc = st.columns(1)[0]
            with col_disc:
                with st.expander("📅 财报披露计划"):
                    if not df_disc.empty:
                        st.dataframe(df_disc.head(10), use_container_width=True)
                    else:
                        st.info("暂无披露计划。")
