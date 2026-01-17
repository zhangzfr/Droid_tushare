"""
Index Data Page
==============
Visualizations for index data including Index List, Heatmaps, SW Industries, Market Width, and Constituents.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dashboard.components.headers import render_header

# Import index data modules
from dashboard.index_data_loader import (
    load_index_basic, get_indices_with_weight_data,
    get_constituent_count_per_date, get_available_trade_dates,
    get_constituents_for_date, load_major_indices_daily
)
from dashboard.index_charts import plot_constituent_count_over_time, plot_index_heatmap, plot_cumulative_returns

# Import SW Index modules
from dashboard.sw_index_data_loader import (
    get_sw_hierarchy, get_sw_members, calculate_market_width, load_sw_l1_daily_history,
    get_top_l1_gainers, get_latest_sw_trade_date
)
from dashboard.sw_index_charts import (
    plot_multi_index_price_normalized, plot_multi_index_amount_normalized,
    plot_sw_l1_price_volume, plot_sw_l1_valuation_quantiles, plot_corr_heatmap, plot_rank_trend, plot_rank_sankey
)
from dashboard.sw_market_width_chart import plot_market_width_heatmap


def render_index_page(subcategory_key):
    """
    Render the index data page based on the selected subcategory.
    """
    # Load index data
    with st.spinner('Loading index data...'):
        df_indices = load_index_basic()
        indices_with_weight = get_indices_with_weight_data()
    
    if df_indices.empty:
        st.error("Unable to load index data. Please check database connection.")
        st.stop()
    
    # --- Index List Sub-category ---
    if subcategory_key == "index_list":
        render_header("Index List", "list")
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Filters**")
            markets = sorted(df_indices['market'].dropna().unique().tolist())
            publishers = sorted(df_indices['publisher'].dropna().unique().tolist())
            
            # Market checkboxes
            st.markdown("*Market*")
            sel_market = []
            for mkt in markets:
                if st.checkbox(mkt, value=True, key=f"idx_mkt_cb_{mkt}"):
                    sel_market.append(mkt)
            
            st.divider()
            
            # Publisher checkboxes (group top publishers)
            st.markdown("*Publisher*")
            sel_publisher = []
            top_publishers = ['SSE', 'SZSE', 'CSINDEX', 'SW', 'CICC']
            other_publishers = [p for p in publishers if p not in top_publishers]
            
            for pub in top_publishers:
                if pub in publishers:
                    if st.checkbox(pub, value=True, key=f"idx_pub_cb_{pub}"):
                        sel_publisher.append(pub)
            
            if other_publishers:
                st.markdown("<small>*Others*</small>", unsafe_allow_html=True)
                for pub in other_publishers:
                    if st.checkbox(pub, value=False, key=f"idx_pub_cb_{pub}"):
                        sel_publisher.append(pub)
        
        df_filtered = df_indices.copy()
        if sel_market:
            df_filtered = df_filtered[df_filtered['market'].isin(sel_market)]
        if sel_publisher:
            df_filtered = df_filtered[df_filtered['publisher'].isin(sel_publisher)]
        
        df_filtered['has_weight'] = df_filtered['ts_code'].isin(indices_with_weight)
        
        with right_col:
            st.markdown(f"**Total {len(df_filtered)} indices, {df_filtered['has_weight'].sum()} with weight data**")
            
            display_cols = ['ts_code', 'name', 'market', 'publisher', 'index_type', 'category',
                            'base_date', 'base_point', 'list_date', 'has_weight']
            
            st.dataframe(
                df_filtered[display_cols],
                use_container_width=True,
                height=600,
                column_config={
                    "ts_code": "Code",
                    "name": "Name",
                    "market": "Market",
                    "publisher": "Publisher",
                    "index_type": "Type",
                    "category": "Category",
                    "base_date": "Base Date",
                    "base_point": st.column_config.NumberColumn("Base Point", format="%.2f"),
                    "list_date": "List Date",
                    "has_weight": st.column_config.CheckboxColumn("Has Weight")
                }
            )
    
    # --- Index Heatmap Sub-category ---
    elif subcategory_key == "index_map":
        render_header("Major Indices Performance", "heatmap")
        
        default_end = datetime.now()
        default_start = default_end - timedelta(days=60)
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", default_start, key="idx_start")
            end_date = st.date_input("End Date", default_end, key="idx_end")
            
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        with st.spinner('Fetching performance data...'):
            df_heatmap = load_major_indices_daily(start_str, end_str)
        
        with right_col:
            if df_heatmap.empty:
                st.warning(f"No performance data found between {start_str} and {end_str}")
            else:
                tab1, tab2, tab3 = st.tabs(["Heatmap Analysis", "Cumulative Returns", "Raw Data"])
                
                with tab1:
                    fig_heatmap = plot_index_heatmap(df_heatmap)
                    if fig_heatmap:
                        st.plotly_chart(fig_heatmap, use_container_width=True, key="idx_heatmap")
                        st.caption("Source: index_daily, index_basic")
                
                with tab2:
                    all_indices = sorted(df_heatmap['ts_code'].unique().tolist())
                    default_selection = [x for x in ['000001.SH', '000300.SH', '000905.SH', '399006.SZ', '000688.SH'] if x in all_indices]
                    if not default_selection:
                        default_selection = all_indices[:5]
                    
                    selected_codes = st.multiselect("Select Indices to Compare:", all_indices, default=default_selection, key="idx_compare")
                    
                    if selected_codes:
                        df_line = df_heatmap[df_heatmap['ts_code'].isin(selected_codes)]
                        fig_line = plot_cumulative_returns(df_line)
                        if fig_line:
                            st.plotly_chart(fig_line, use_container_width=True, key="idx_returns")
                            st.caption("Source: index_daily")
                        
                        st.caption("Note: Cumulative returns are calculated from the first available date in the selected range, indexed to 100.")
                    else:
                        st.info("Please select at least one index to compare performance.")
                
                with tab3:
                    pivot_display = df_heatmap.pivot(index='trade_date', columns='ts_code', values='pct_chg').sort_index(ascending=False)
                    st.dataframe(pivot_display, use_container_width=True)

    # --- Shenwan Industry + Market Width (combined) ---
    elif subcategory_key == "sw_index":
        render_header("Shenwan Industry Dashboard", "treemap")

        df_hier = get_sw_hierarchy()
        df_members = get_sw_members()
        latest_trade_date = get_latest_sw_trade_date()

        if df_hier.empty or df_members.empty:
            st.error("申万行业数据加载失败，请检查数据库连接。")
            st.stop()

        l1_options = df_hier[['l1_code', 'l1_name']].drop_duplicates().sort_values('l1_code')
        l1_dict = dict(zip(l1_options['l1_code'], l1_options['l1_name']))
        l1_all_codes = list(l1_dict.keys())

        latest_dt = pd.to_datetime(latest_trade_date) if latest_trade_date else datetime.now()

        # 行业分组
        def pick(names):
            return [code for code, name in l1_dict.items() if name in names]

        category_map = {
            '消费': pick(['食品饮料', '家用电器', '商贸零售', '纺织服饰', '社会服务', '美容护理', '农林牧渔']),
            '制造': pick(['电子', '机械设备', '汽车', '电力设备', '国防军工', '轻工制造', '建筑材料', '建筑装饰', '交通运输', '环保', '公用事业']),
            '金融': pick(['银行', '非银金融', '房地产']),
            '科技': pick(['计算机', '传媒', '通信']),
            '资源': pick(['有色金属', '钢铁', '基础化工', '石油石化', '煤炭']),
            '其他': pick(['医药生物', '综合'])
        }

        top_gainers = get_top_l1_gainers(latest_trade_date, 5)
        default_codes = top_gainers['ts_code'].tolist() if not top_gainers.empty else l1_options['l1_code'].tolist()[:5]
        default_primary = default_codes[0] if default_codes else None

        def resolve_range(mode: str, preset: str, latest: pd.Timestamp, c_start, c_end):
            if mode == "自定义区间" and c_start and c_end:
                start_dt = pd.to_datetime(c_start)
                end_dt = pd.to_datetime(c_end)
            else:
                delta_map = {
                    "最近一周": 7,
                    "最近一月": 30,
                    "最近三月": 90,
                    "最近半年": 180,
                    "最近一年": 365
                }
                if preset == "YTD":
                    start_dt = datetime(latest.year, 1, 1)
                else:
                    start_dt = latest - timedelta(days=delta_map.get(preset, 180))
                end_dt = latest

            if end_dt > latest:
                end_dt = latest
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, end_dt
            return start_dt, end_dt

        def render_filters(key_prefix: str, default_sel: list):
            st.markdown("**日期范围**")
            preset_label = st.radio(
                "快捷区间",
                ["最近一周", "最近一月", "最近三月", "最近半年", "最近一年", "YTD"],
                index=5,
                key=f"{key_prefix}_range_preset"
            )
            custom_start = st.date_input("自定义开始日期", value=latest_dt - timedelta(days=180), key=f"{key_prefix}_custom_start")
            custom_end = st.date_input("自定义结束日期", value=latest_dt, key=f"{key_prefix}_custom_end")
            use_custom = st.checkbox("使用自定义区间", value=False, key=f"{key_prefix}_use_custom")

            st.divider()
            st.markdown(
                """
                <style>
                /* Checkbox Group Styling */
                [data-testid="stCheckbox"] {
                    margin-bottom: 0.5rem;
                }
                div.stButton > button {
                    width: 100%;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                </style>
                """, unsafe_allow_html=True
            )
            st.markdown("**一级行业筛选（复选）**")

            # --- Logic Update: Default to ALL, and Link Categories ---
            
            # Session State Initialization
            state_key_selected = f"{key_prefix}_selected"
            state_key_cat_states = f"{key_prefix}_cat_states" # Store per-category checkbox states
            
            # If not initialized, select ALL by default
            if state_key_selected not in st.session_state:
                st.session_state[state_key_selected] = list(l1_all_codes)
            
            if state_key_cat_states not in st.session_state:
                st.session_state[state_key_cat_states] = {cat: True for cat in category_map.keys()} 
            
            current_selected_set = set(st.session_state[state_key_selected])

            # Global Controls
            col_all, col_none = st.columns(2)
            
            # "Select All" Button Logic
            if col_all.button("全选", key=f"{key_prefix}_btn_all"):
                current_selected_set = set(l1_all_codes)
                st.session_state[state_key_selected] = list(l1_all_codes)
                for cat in category_map:
                    st.session_state[state_key_cat_states][cat] = True
                st.rerun()

            if col_none.button("全不选", key=f"{key_prefix}_btn_none"):
                current_selected_set = set()
                st.session_state[state_key_selected] = []
                for cat in category_map:
                    st.session_state[state_key_cat_states][cat] = False
                st.rerun()

            new_selected_set = set(current_selected_set)
            
            # Check if all children of a category are present/absent
            def are_all_children_selected(cat_codes, current_set):
                return all(c in current_set for c in cat_codes)

            for cat_name, cat_codes in category_map.items():
                if not cat_codes: continue
                
                # Checkbox logic:
                # We track the "Category Checkbox" state in session_state[state_key_cat_states][cat_name]
                # If interaction flips this state, we apply to all children.
                
                prev_cat_state = st.session_state[state_key_cat_states].get(cat_name, False)
                
                # Render Category Checkbox directly (No extra column nesting to avoid Level 3 depth error)
                cat_key = f"{key_prefix}_cat_cb_{cat_name}"
                cat_checked = st.checkbox(f"**{cat_name}**", value=prev_cat_state, key=cat_key)
                
                if cat_checked != prev_cat_state:
                     # State Changed by User Click
                     if cat_checked: 
                         new_selected_set.update(cat_codes)
                     else:
                         new_selected_set.difference_update(cat_codes)
                     
                     st.session_state[state_key_cat_states][cat_name] = cat_checked
                     st.session_state[state_key_selected] = list(new_selected_set)
                     st.rerun()

                # Render Children
                with st.container():
                    st.markdown('<div style="margin-left: 20px;">', unsafe_allow_html=True)
                    child_cols = st.columns(3)
                    for i, code in enumerate(cat_codes):
                        label = f"{l1_dict.get(code, code)}"
                        child_key = f"{key_prefix}_l1_{code}"
                        is_sel = code in current_selected_set
                        
                        with child_cols[i % 3]:
                            child_checked = st.checkbox(label, value=is_sel, key=child_key)
                            
                            if child_checked != is_sel:
                                # Child state changed by user interaction
                                if child_checked:
                                    new_selected_set.add(code)
                                else:
                                    new_selected_set.discard(code)
                                
                                # Update Global Set immediately
                                st.session_state[state_key_selected] = list(new_selected_set)
                                
                                # Logic to update Parent State
                                if not child_checked:
                                     st.session_state[state_key_cat_states][cat_name] = False
                                else:
                                    if are_all_children_selected(cat_codes, new_selected_set):
                                        st.session_state[state_key_cat_states][cat_name] = True
                                    else:
                                        st.session_state[state_key_cat_states][cat_name] = False
                                
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # Return final list.
            start_dt, end_dt = resolve_range("自定义区间" if use_custom else "快捷区间", preset_label, latest_dt, custom_start if use_custom else None, custom_end if use_custom else None)
            return list(new_selected_set), start_dt, end_dt

        tab_price, tab_amount, tab_corr_merged, tab_rank, tab_rank_flow, tab_detail, tab_valuation, tab_width = st.tabs([
            "Price Trends",
            "Turnover Trends",
            "Correlation",
            "Rank Trends",
            "Rank Flow",
            "Industry Price/Vol",
            "Industry Valuation",
            "Market Breadth"
        ])

        with tab_price:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                sel_codes, s_dt, e_dt = render_filters("sw_price", default_codes)
            with col_r:
                if not sel_codes:
                    st.info("请选择至少一个行业。")
                else:
                    df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d'))
                    if df_history.empty:
                        st.warning("未查询到数据，请调整日期或选择。")
                    else:
                        df_history['l1_name'] = df_history['ts_code'].map(l1_dict)
                        fig = plot_multi_index_price_normalized(df_history)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        st.caption("默认展示最近交易日涨幅Top5；可通过左侧筛选调整。")

        with tab_amount:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                sel_codes, s_dt, e_dt = render_filters("sw_amount", default_codes)
            with col_r:
                if not sel_codes:
                    st.info("请选择至少一个行业。")
                else:
                    df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d'))
                    if df_history.empty:
                        st.warning("未查询到数据，请调整日期或选择。")
                    else:
                        df_history['l1_name'] = df_history['ts_code'].map(l1_dict)
                        fig = plot_multi_index_amount_normalized(df_history)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)

        with tab_corr_merged:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                sel_codes, s_dt, e_dt = render_filters("sw_corr", default_codes)
            with col_r:
                if not sel_codes:
                    st.info("请选择至少一个行业。")
                else:
                    df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d'))
                    if df_history.empty:
                        st.warning("未查询到数据，请调整日期或选择。")
                    else:
                        df_history = df_history.sort_values('trade_date')
                        
                        # Merged Logic: Radio button to select metric
                        corr_metric = st.radio("Correlation Metric", ["Price Return", "PE", "PB"], horizontal=True, key="sw_corr_metric_select")
                        
                        pivot_data = pd.DataFrame()
                        
                        if corr_metric == "Price Return":
                            pivot_close = df_history.pivot(index='trade_date', columns='ts_code', values='close')
                            pivot_data = pivot_close.pct_change().dropna(how='all')
                            caption_text = "相关性基于日度收益率（收盘价PctChange）。"
                        else:
                            metric_col = corr_metric.lower()
                            if metric_col not in df_history.columns:
                                st.error(f"Missing {corr_metric} data.")
                            else:
                                pivot_data = df_history.pivot(index='trade_date', columns='ts_code', values=metric_col)
                                pivot_data = pivot_data.dropna(how='all')
                                caption_text = f"相关性基于日度{corr_metric}绝对值。"

                        if pivot_data.empty or len(pivot_data) < 2:
                             st.warning("有效数据不足以计算相关性。")
                        else:
                            corr = pivot_data.corr()
                            corr.index = [l1_dict.get(c, c) for c in corr.index]
                            corr.columns = [l1_dict.get(c, c) for c in corr.columns]
                            fig = plot_corr_heatmap(corr)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            st.caption(caption_text)

        with tab_rank:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                # 默认全选
                sel_codes, s_dt, e_dt = render_filters("sw_rank", l1_all_codes)
            with col_r:
                df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d')) if sel_codes else pd.DataFrame()
                if df_history.empty:
                    st.warning("未查询到数据，请调整日期或选择。")
                else:
                    df_history['l1_name'] = df_history['ts_code'].map(l1_dict)
                    df_history = df_history.sort_values('trade_date')
                    # 计算每日涨跌幅排名
                    df_history['pct_change'] = df_history.groupby('ts_code')['close'].pct_change()
                    rank_list = []
                    for dt, grp in df_history.groupby('trade_date'):
                        grp = grp.dropna(subset=['pct_change'])
                        if grp.empty:
                            continue
                        grp = grp.sort_values('pct_change', ascending=False)
                        grp['rank'] = range(1, len(grp) + 1)
                        rank_list.append(grp[['trade_date', 'ts_code', 'l1_name', 'rank']])
                    df_rank = pd.concat(rank_list) if rank_list else pd.DataFrame()
                    if df_rank.empty:
                        st.warning("区间内无法计算排名。")
                    else:
                        fig = plot_rank_trend(df_rank)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        st.caption("纵轴为排名，数值越小表示涨幅越靠前。默认展示全部一级行业。")

        with tab_rank_flow:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                sel_codes, s_dt, e_dt = render_filters("sw_rank_flow", l1_all_codes)
            with col_r:
                df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d')) if sel_codes else pd.DataFrame()
                if df_history.empty:
                    st.warning("未查询到数据，请调整日期或选择。")
                else:
                    df_history['l1_name'] = df_history['ts_code'].map(l1_dict)
                    df_history = df_history.sort_values('trade_date')
                    df_history['pct_change'] = df_history.groupby('ts_code')['close'].pct_change()
                    rank_list = []
                    for dt, grp in df_history.groupby('trade_date'):
                        grp = grp.dropna(subset=['pct_change'])
                        if grp.empty:
                            continue
                        grp = grp.sort_values('pct_change', ascending=False)
                        grp['rank'] = range(1, len(grp) + 1)
                        rank_list.append(grp[['trade_date', 'ts_code', 'l1_name', 'rank']])
                    df_rank = pd.concat(rank_list) if rank_list else pd.DataFrame()
                    if df_rank.empty:
                        st.warning("区间内无法计算排名。")
                    else:
                        fig = plot_rank_sankey(df_rank)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        st.caption("Sankey 展示行业在各交易日的排名流动情况。")

        with tab_detail:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                sel_codes, s_dt, e_dt = render_filters("sw_detail", [default_primary] if default_primary else [])
            with col_r:
                if not sel_codes:
                    st.info("请选择至少一个行业。")
                else:
                    df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d'))
                    if df_history.empty:
                        st.warning("未查询到数据，请调整日期或选择。")
                    else:
                        df_history['l1_name'] = df_history['ts_code'].map(l1_dict)
                        for code in sel_codes:
                            df_single = df_history[df_history['ts_code'] == code]
                            if df_single.empty:
                                st.warning(f"{code} 暂无数据")
                                continue
                            name = l1_dict.get(code, code)
                            st.subheader(f"{name} ({code})")
                            fig = plot_sw_l1_price_volume(df_single)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True, key=f"pv_{code}")

        with tab_valuation:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                sel_codes, s_dt, e_dt = render_filters("sw_val", [default_primary] if default_primary else [])
            with col_r:
                if not sel_codes:
                    st.info("请选择至少一个行业。")
                else:
                    df_history = load_sw_l1_daily_history(sel_codes, s_dt.strftime('%Y%m%d'), e_dt.strftime('%Y%m%d'))
                    if df_history.empty:
                        st.warning("未查询到数据，请调整日期或选择。")
                    else:
                        df_history['l1_name'] = df_history['ts_code'].map(l1_dict)
                        for code in sel_codes:
                            df_single = df_history[df_history['ts_code'] == code]
                            if df_single.empty:
                                st.warning(f"{code} 暂无估值数据")
                                continue
                            name = l1_dict.get(code, code)
                            st.subheader(f"{name} ({code})")
                            fig = plot_sw_l1_valuation_quantiles(df_single)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True, key=f"val_{code}")

        with tab_width:
            col_l, col_r = st.columns([1, 4])
            with col_l:
                st.markdown("**Market Width 参数**")
                mw_level = st.radio("行业级别", ["L1", "L2", "L3"], index=0, horizontal=True, key="sw_mw_level")
                mw_ma = st.number_input("MA Period", min_value=1, value=20, step=1, key="sw_mw_ma")
                mw_days = st.number_input("显示天数", min_value=5, max_value=500, value=30, step=5, key="sw_mw_days")
            with col_r:
                with st.spinner(f"计算MA{mw_ma}宽度中..."):
                    df_width = calculate_market_width(None, int(mw_days), int(mw_ma), mw_level)

                if df_width.empty:
                    st.warning("暂无Market Width数据")
                else:
                    fig = plot_market_width_heatmap(df_width, mw_level, int(mw_ma))
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key="market_width_heatmap")
                    st.caption("Market Width = 收盘价高于MA的占比。默认截止最近交易日。")
    elif subcategory_key == "index_const":
        render_header("Index Constituents", "detail")
        
        if not indices_with_weight:
            st.warning("No index weight data available in database")
            st.stop()
        
        # Index selection filters - Cascading logic
        st.subheader("Filter Indices")
        
        # Initialize filtered dataframe with full dataset
        df_filter_step = df_indices.copy()
        
        col1, col2, col3, col4 = st.columns(4)
        
        # 1. Market Filter
        with col1:
            markets = ['All'] + sorted(df_filter_step['market'].dropna().unique().tolist())
            sel_market = st.selectbox("Market", markets, key="detail_market")
            
        # Apply Market filter immediately if selected
        if sel_market != 'All':
            df_filter_step = df_filter_step[df_filter_step['market'] == sel_market]
            
        # 2. Publisher Filter (Options depend on Market)
        with col2:
            publishers = ['All'] + sorted(df_filter_step['publisher'].dropna().unique().tolist())
            # Reset selection if previously selected option is no longer valid (handled by Streamlit usually, but good to be safe)
            sel_publisher = st.selectbox("Publisher", publishers, key="detail_publisher")
            
        # Apply Publisher filter
        if sel_publisher != 'All':
            df_filter_step = df_filter_step[df_filter_step['publisher'] == sel_publisher]
            
        # 3. Index Type Filter (Options depend on Market + Publisher)
        with col3:
            types = ['All'] + sorted(df_filter_step['index_type'].dropna().unique().tolist())
            sel_type = st.selectbox("Index Type", types, key="detail_type")
            
        # Apply Type filter
        if sel_type != 'All':
            df_filter_step = df_filter_step[df_filter_step['index_type'] == sel_type]
            
        # 4. Category Filter (Options depend on previous 3)
        with col4:
            categories = ['All'] + sorted(df_filter_step['category'].dropna().unique().tolist())
            sel_category = st.selectbox("Category", categories, key="detail_category")
            
        # Apply Category filter
        if sel_category != 'All':
            df_filter_step = df_filter_step[df_filter_step['category'] == sel_category]
            
        # Final filtered dataframe
        df_filtered = df_filter_step
            
        # Then maximize intersection with indices that actually have weight data
        filtered_indices_with_weight = [x for x in indices_with_weight if x in df_filtered['ts_code'].values]
        
        if not filtered_indices_with_weight:
            st.warning("No indices found matching filters that have weight data.")
            st.stop()

        # Index selection dropdown
        selected_index = st.selectbox(
            "Select Index",
            filtered_indices_with_weight,
            format_func=lambda x: f"{x} - {df_filtered[df_filtered['ts_code'] == x]['name'].values[0]}"
        )
        
        if selected_index:
            # Show index basic info
            idx_info = df_indices[df_indices['ts_code'] == selected_index]
            if not idx_info.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Index Code", selected_index)
                with col2:
                    st.metric("Name", idx_info['name'].values[0])
                with col3:
                    st.metric("Market", idx_info['market'].values[0])
                with col4:
                    st.metric("Base Point", idx_info['base_point'].values[0])
            
            st.divider()
            
            tab1, tab2 = st.tabs(["Constituent Count Trend", "Constituent Details"])
            
            with tab1:
                st.subheader("Constituent Count Over Time")
                st.caption("Use this chart to identify missing data (sudden drops in count)")
                
                df_counts = get_constituent_count_per_date(selected_index)
                if not df_counts.empty:
                    fig = plot_constituent_count_over_time(df_counts)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("Source: index_composition")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Trade Days Covered", len(df_counts))
                    with col2:
                        st.metric("Avg Constituents", f"{df_counts['constituent_count'].mean():.0f}")
                    with col3:
                        st.metric("Min/Max", f"{df_counts['constituent_count'].min()} / {df_counts['constituent_count'].max()}")
            
            with tab2:
                trade_dates = get_available_trade_dates(selected_index)
                if trade_dates:
                    selected_date = st.selectbox("Select Trade Date", trade_dates)
                    
                    if selected_date:
                        df_cons = get_constituents_for_date(selected_index, selected_date)
                        if not df_cons.empty:
                            st.markdown(f"**{len(df_cons)} constituents on {selected_date}**")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.dataframe(
                                    df_cons,
                                    use_container_width=True,
                                    height=400,
                                    column_config={
                                        "con_code": "Constituent Code",
                                        "weight": st.column_config.NumberColumn("Weight (%)", format="%.4f")
                                    }
                                )
                            with col2:
                                st.markdown("**Weight Distribution (Top 10)**")
                                top10 = df_cons.head(10)
                                st.bar_chart(top10.set_index('con_code')['weight'])
                else:
                    st.info("No trade date data available for this index")
