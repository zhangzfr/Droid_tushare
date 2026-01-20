import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from dashboard.components.headers import render_header
from dashboard.dc_data_loader import (
    get_dc_counts, get_dc_latest_trade_date, load_dc_top_bottom,
    load_dc_index_list, load_dc_history
)
from dashboard.dc_charts import (
    plot_dc_price, plot_dc_amount, plot_dc_pct, plot_dc_turnover
)


def render_dc_page(_):
    render_header("DC 指数分析", "trend")

    counts = get_dc_counts()
    latest_trade_date = counts.get('latest_trade_date') or datetime.now().strftime('%Y%m%d')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("指数总数", counts.get('total_index', 0))
    c2.metric("有行情指数", counts.get('total_daily', 0))
    c3.metric("最新交易日", latest_trade_date)
    c4.metric("最新有行情数量", counts.get('latest_daily', 0))

    left, right = st.columns([1, 3])
    with left:
        trade_date = st.text_input("交易日 (YYYYMMDD)", value=latest_trade_date, key="dc_trade_date")
        top_n = st.number_input("Top/Bottom N", min_value=3, max_value=20, value=10, step=1, key="dc_topn")
    with right:
        top_df, bottom_df = load_dc_top_bottom(trade_date, int(top_n))
        st.subheader(f"{trade_date} 涨幅TOP{top_n}")
        if top_df.empty:
            st.warning("当日无行情数据")
        else:
            st.dataframe(top_df[['ts_code', 'name', 'pct_change', 'vol', 'amount', 'turnover_rate']], use_container_width=True)
        st.subheader(f"{trade_date} 跌幅BOTTOM{top_n}")
        if bottom_df.empty:
            st.warning("当日无行情数据")
        else:
            st.dataframe(bottom_df[['ts_code', 'name', 'pct_change', 'vol', 'amount', 'turnover_rate']], use_container_width=True)

    st.divider()

    idx_df = load_dc_index_list()
    options = idx_df['ts_code'].tolist() if not idx_df.empty else []
    name_map = dict(zip(idx_df['ts_code'], idx_df['name'])) if not idx_df.empty else {}

    # 分类：地区(BK01), 行业(BK04), 概念(BK05+ 默认), 综合(特殊列表)
    composite_codes = {"BK0742", "BK0743", "BK070", "BK0636", "BK062", "BK0611", "BK0500", "BK0499", "BK0498"}
    def classify(code: str) -> str:
        if code in composite_codes:
            return "综合"
        if code.startswith("BK01"):
            return "地区"
        if code.startswith("BK04"):
            return "行业"
        if code.startswith("BK05"):
            return "概念"
        return "其他"

    if not idx_df.empty:
        idx_df['category'] = idx_df['ts_code'].apply(classify)

    filt_col, chart_col = st.columns([1, 3])
    with filt_col:
        start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=180), key="dc_start")
        end_date = st.date_input("结束日期", value=datetime.now(), key="dc_end")
        keyword = st.text_input("关键词过滤 (代码或名称包含)", value="", key="dc_kw")
        cat_selected = st.multiselect("类别过滤", ["地区", "行业", "概念", "综合", "其他"], default=["地区", "行业", "概念", "综合", "其他"], key="dc_cat")

        filtered_df = idx_df.copy()
        if cat_selected:
            filtered_df = filtered_df[filtered_df['category'].isin(cat_selected)]
        if keyword:
            kw = keyword.lower()
            filtered_df = filtered_df[
                filtered_df['ts_code'].str.lower().str.contains(kw) |
                filtered_df['name'].str.lower().str.contains(kw)
            ]

        filt_options = filtered_df['ts_code'].tolist() if not filtered_df.empty else []
        default_sel = filt_options[: min(5, len(filt_options))]
        selected = st.multiselect(
            "选择指数",
            filt_options,
            default=default_sel,
            format_func=lambda x: f"{x} {name_map.get(x, '')}",
            key="dc_idx_sel"
        )
        normalized = st.checkbox("归一化价格/金额 (Base=100)", value=False, key="dc_norm")
    with chart_col:
        if not selected:
            st.info("请选择至少一个指数")
        else:
            s_str = pd.to_datetime(start_date).strftime('%Y%m%d')
            e_str = pd.to_datetime(end_date).strftime('%Y%m%d')
            hist = load_dc_history(selected, s_str, e_str)
            if hist.empty:
                st.warning("所选区间无数据")
            else:
                hist['trade_date'] = pd.to_datetime(hist['trade_date'])
                tabs = st.tabs(["价格", "成交金额", "涨跌幅", "换手率"])
                with tabs[0]:
                    fig = plot_dc_price(hist, name_map, normalized)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with tabs[1]:
                    fig = plot_dc_amount(hist, name_map, normalized)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with tabs[2]:
                    fig = plot_dc_pct(hist, name_map)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with tabs[3]:
                    fig = plot_dc_turnover(hist, name_map)
                    if fig: st.plotly_chart(fig, use_container_width=True)
