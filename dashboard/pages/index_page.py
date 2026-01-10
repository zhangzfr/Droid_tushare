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
    get_sw_hierarchy, load_sw_daily_data, load_stocks_by_l3,
    load_top_stocks, load_stocks_by_l2, get_sw_members, load_stock_daily_data,
    load_stocks_by_l1, calculate_market_width
)
from dashboard.sw_index_charts import plot_sw_treemap, plot_sw_stock_treemap, plot_l1_stock_treemap
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
                st.markdown("<small>*其他*</small>", unsafe_allow_html=True)
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

    # --- Shenwan Index Heatmap Sub-category ---
    elif subcategory_key == "sw_index":
        render_header("Shenwan Industry Heatmap", "treemap")
        
        # Load Hierarchy
        df_hier = get_sw_hierarchy()
        if df_hier.empty:
            st.error("Failed to load Shenwan hierarchy data.")
            st.stop()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 4])
        
        with left_col:
            st.markdown("**Trading Date**")
            today = datetime.now()
            if today.weekday() >= 5:
                today = today - timedelta(days=today.weekday() - 4)
            selected_date = st.date_input("Select Date", today, key="sw_trade_date")
            date_str = selected_date.strftime('%Y%m%d')
            
            st.markdown("---")
            st.markdown("**View Mode**")
            view_mode = st.radio(
                "Select View",
                ["L1 Drill-down", "Full View", "Top 100 Hot Stocks"],
                index=0,
                key="sw_view_mode"
            )
            
            st.markdown("---")
            
            # Initialize option variables to avoid NameError
            selected_l1_drill = None
            level = None
            top_n = 100
            
            # --- Dynamic Controls moved to Left Column ---
            if view_mode == "L1 Drill-down":
                st.markdown("**Drill-down Options**")
                
                l1_options = df_hier[['l1_code', 'l1_name']].drop_duplicates().sort_values('l1_code')
                l1_dict = dict(zip(l1_options['l1_code'], l1_options['l1_name']))
                l1_codes = l1_options['l1_code'].tolist()
                
                # Group by sector category
                # Consumer, Manufacturing, Finance, Tech, Resources, Services
                consumer = [c for c in l1_codes if l1_dict.get(c, '') in ['食品饮料', '家用电器', '商贸零售', '纺织服饰', '社会服务', '美容护理']]
                mfg = [c for c in l1_codes if l1_dict.get(c, '') in ['电子', '机械设备', '汽车', '电力设备', '国防军工', '轻工制造', '建筑材料', '建筑装饰']]
                finance = [c for c in l1_codes if l1_dict.get(c, '') in ['银行', '非银金融', '房地产']]
                tech = [c for c in l1_codes if l1_dict.get(c, '') in ['计算机', '传媒', '通信']]
                resources = [c for c in l1_codes if l1_dict.get(c, '') in ['有色金属', '钢铁', '基础化工', '石油石化', '煤炭']]
                health = [c for c in l1_codes if l1_dict.get(c, '') in ['医药生物']]
                others = [c for c in l1_codes if c not in consumer + mfg + finance + tech + resources + health]
                
                selected_l1_drill = []
                
                # All option
                all_selected = st.checkbox("全选所有", value=True, key="l1_cb_all")
                if all_selected:
                    selected_l1_drill = ['All']
                else:
                    st.markdown("<small>*消费*</small>", unsafe_allow_html=True)
                    for code in consumer:
                        if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                            selected_l1_drill.append(code)
                    
                    st.markdown("<small>*制造*</small>", unsafe_allow_html=True)
                    for code in mfg:
                        if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                            selected_l1_drill.append(code)
                    
                    st.markdown("<small>*金融*</small>", unsafe_allow_html=True)
                    for code in finance:
                        if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                            selected_l1_drill.append(code)
                    
                    st.markdown("<small>*科技*</small>", unsafe_allow_html=True)
                    for code in tech:
                        if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                            selected_l1_drill.append(code)
                    
                    st.markdown("<small>*资源*</small>", unsafe_allow_html=True)
                    for code in resources:
                        if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                            selected_l1_drill.append(code)
                    
                    st.markdown("<small>*医药*</small>", unsafe_allow_html=True)
                    for code in health:
                        if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                            selected_l1_drill.append(code)
                    
                    if others:
                        st.markdown("<small>*其他*</small>", unsafe_allow_html=True)
                        for code in others:
                            if st.checkbox(f"{code} - {l1_dict.get(code, code)}", value=False, key=f"l1_cb_{code}"):
                                selected_l1_drill.append(code)
                
            elif view_mode == "Full View":
                st.markdown("**View Options**")
                level = st.radio(
                    "Select Level", 
                    ["L1", "L2", "L3", "Stock"], 
                    index=0, 
                    key="opt_a_level"
                )
                st.caption("Stock level might be slow to load.")
                
            elif view_mode == "Top 100 Hot Stocks":
                st.markdown("**Filter Options**")
                top_n = st.slider("Display Count", 50, 300, 100, step=50, key="top_n_slider")
        
        with right_col:
            if view_mode == "L1 Drill-down":
                st.caption(f"Viewing: {', '.join([str(x) for x in selected_l1_drill])}")
                
                if 'All' in selected_l1_drill or not selected_l1_drill:
                    with st.spinner("Loading L3 index data..."):
                        target_codes = df_hier['l3_code'].unique().tolist()
                        df_sw_daily = load_sw_daily_data(date_str, target_codes)
                    
                    if df_sw_daily.empty:
                        st.warning(f"No trading data for {date_str}.")
                    else:
                        up_count = len(df_sw_daily[df_sw_daily['pct_change'] > 0])
                        down_count = len(df_sw_daily[df_sw_daily['pct_change'] < 0])
                        
                        c1, c2 = st.columns(2)
                        c1.metric("Rising Indices", up_count)
                        c2.metric("Falling Indices", down_count)
                        
                        fig = plot_sw_treemap(df_hier, df_sw_daily, level='L3')
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key="l1_tab_index_chart")
                            st.caption("Source: sw_daily, sw_index_member")
                else:
                    # Handle multiple L1 selection
                    with st.spinner(f"Loading stocks for selected L1 industries..."):
                        df_l1_stocks = pd.DataFrame()
                        for l1_code in selected_l1_drill:
                            df_part = load_stocks_by_l1(date_str, l1_code)
                            df_l1_stocks = pd.concat([df_l1_stocks, df_part], ignore_index=True)
                    
                    if df_l1_stocks.empty:
                        st.warning(f"No stock data for selected industries on {date_str}.")
                    else:
                        up_count = len(df_l1_stocks[df_l1_stocks['pct_change'] > 0])
                        down_count = len(df_l1_stocks[df_l1_stocks['pct_change'] < 0])
                        total_amt = df_l1_stocks['amount'].sum()
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Rising", up_count)
                        c2.metric("Falling", down_count)
                        c3.metric("Amount", f"{total_amt/100000000:.2f} B")
                        c4.metric("Stocks", len(df_l1_stocks))
                        
                        fig = plot_l1_stock_treemap(df_l1_stocks, "Selected L1 Industries")
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key="l1_tab_stock_chart")
                            st.caption("Source: stock_daily, sw_index_member")
            
            # ==================== Original View ====================
            elif view_mode == "Full View":
                with st.spinner(f"Loading {level} data for {date_str}..."):
                    if level == 'Stock':
                        df_hier_full = get_sw_members()
                        target_codes = df_hier_full['ts_code'].unique().tolist()
                        df_sw_daily = load_stock_daily_data(date_str, target_codes)
                    else:
                        if level == 'L1':
                            target_codes = df_hier['l1_code'].unique().tolist()
                        elif level == 'L2':
                            target_codes = df_hier['l2_code'].unique().tolist()
                        elif level == 'L3':
                            target_codes = df_hier['l3_code'].unique().tolist()
                        df_sw_daily = load_sw_daily_data(date_str, target_codes)
                
                if df_sw_daily.empty:
                    st.warning(f"No trading data for {date_str}.")
                else:
                    up_count = len(df_sw_daily[df_sw_daily['pct_change'] > 0])
                    down_count = len(df_sw_daily[df_sw_daily['pct_change'] < 0])
                    total_amt = df_sw_daily['amount'].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"Rising {level}", up_count)
                    c2.metric(f"Falling {level}", down_count)
                    c3.metric("Amount", f"{total_amt/100000000:.2f} B")
                    
                    if level == 'Stock':
                        df_hier_full = get_sw_members()
                        fig = plot_sw_treemap(df_hier_full, df_sw_daily, level='Stock')
                    else:
                        fig = plot_sw_treemap(df_hier, df_sw_daily, level=level)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key="opt_a_chart")
                        st.caption("Source: sw_daily, sw_index_member")
            
            # ==================== Top N Stocks ====================
            elif view_mode == "Top 100 Hot Stocks":
                with st.spinner(f"Loading Top {top_n} stocks..."):
                    df_top = load_top_stocks(date_str, top_n)
                
                if df_top.empty:
                    st.warning(f"No stock data for {date_str}.")
                else:
                    up_count = len(df_top[df_top['pct_change'] > 0])
                    down_count = len(df_top[df_top['pct_change'] < 0])
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Rising", up_count)
                    c2.metric("Falling", down_count)
                    c3.metric("Display Count", len(df_top))
                    
                    fig_top = plot_sw_stock_treemap(df_top, f"Top {top_n} Stocks by Amount")
                    if fig_top:
                        st.plotly_chart(fig_top, use_container_width=True, key="top_n_chart")
                        st.caption("Source: stock_daily")
    
    # --- Market Width Sub-category ---
    elif subcategory_key == "market_width":
        render_header("SW Industry Market Width", "chart")
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Parameters**")
            level = st.radio("Industry Level", ["L1", "L2", "L3"], index=0, key="mw_level", horizontal=True)
            
            ma_period = st.number_input("MA Period", min_value=1, value=20, step=1, key="mw_ma")
            days = st.number_input("Display Days", min_value=5, max_value=500, value=30, step=5, key="mw_days")
            
            today = datetime.now()
            if today.weekday() >= 5:
                today = today - timedelta(days=today.weekday() - 4)
            end_date = st.date_input("End Date", today, key="mw_end_date")
            end_date_str = end_date.strftime('%Y%m%d')
        
        with st.spinner(f"Calculating MA{ma_period} market width for {level}..."):
            df_width = calculate_market_width(end_date_str, days, ma_period, level)
        
        with right_col:
            st.caption("Market Width = % of stocks with Close > MA. Heatmap shows changes across industries.")
            
            if df_width.empty:
                st.warning("No market width data available.")
            else:
                latest_date = df_width['trade_date'].max()
                df_latest = df_width[df_width['trade_date'] == latest_date]
                avg_width = df_latest['width_ratio'].mean()
                max_width_row = df_latest.loc[df_latest['width_ratio'].idxmax()]
                min_width_row = df_latest.loc[df_latest['width_ratio'].idxmin()]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Avg Market Width", f"{avg_width:.1f}%")
                c2.metric("Strongest Industry", f"{max_width_row['index_name']} ({max_width_row['width_ratio']:.1f}%)")
                c3.metric("Weakest Industry", f"{min_width_row['index_name']} ({min_width_row['width_ratio']:.1f}%)")
                
                fig = plot_market_width_heatmap(df_width, level, ma_period)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="market_width_heatmap")
                    st.caption("Source: stock_daily, sw_index_member")
    

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
