"""
TDX Index Analysis Page

Multi-dimensional sector analysis dashboard with 6 core tabs:
1. Rotation Analysis
2. Capital Flow
3. Sentiment
4. Valuation
5. Hot Topics
6. Constituents
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dashboard.tdx_data_loader import (
    load_tdx_daily, load_tdx_index, load_tdx_member,
    get_idx_type_stats, get_latest_trade_date
)
from dashboard.tdx_charts import (
    plot_sector_rotation_heatmap, plot_top_gainers_ranking, plot_idx_type_leadership,
    plot_capital_flow_bars, plot_capital_vs_return_scatter,
    plot_sentiment_gauges, plot_limit_up_analysis
)


def render_tdx_index_page():
    """Main entry point for TDX Index Analysis page"""
    
    st.title("📊 TDX Sector Index Analysis")
    st.markdown("""
    **Comprehensive Sector Analysis**: From macro market rotation to micro constituent contributions, 
    tracking capital flows, sentiment shifts, and valuation opportunities.
    """)
    
    # Load index metadata early (needed for sidebar selectors)
    df_index = load_tdx_index()
    
    # ============ Sidebar: Filters ============
    with st.sidebar:
        st.header("Filter Conditions")
        
        # 1. idx_type Classifier (CRITICAL)
        st.subheader("Sector Category")
        idx_type_options = {
            "all": "📊 All Sectors",
            "行业板块": "🏭 Industry Sectors",
            "概念板块": "💡 Theme/Concept Sectors",
            "地区板块": "🗺️ Regional Sectors",
            "风格板块": "🎨 Style Sectors"
        }
        
        selected_idx_type = st.selectbox(
            "Select Sector Type",
            options=list(idx_type_options.keys()),
            format_func=lambda x: idx_type_options[x],
            index=1,  # Default to "行业板块" (Industry)
            help="Different sector types represent different market dimensions:\n🏭 Industry: Traditional industry classification\n💡 Theme/Concept: Thematic investment directions\n🗺️ Regional: Geographic economic characteristics\n🎨 Style: Investment style classification"
        )
        
        # Show stats
        stats = get_idx_type_stats()
        if selected_idx_type != "all" and selected_idx_type in stats:
            st.caption(f"Current category contains **{stats[selected_idx_type]:,}** sectors")
        
        # 1b. Specific Index Selector (NEW)
        st.subheader("Select Specific Indices")
        
        # Load index list for selected type
        if selected_idx_type == "all":
            available_indices = df_index[['ts_code', 'display_name']].drop_duplicates()
        else:
            available_indices = df_index[df_index['idx_type'] == selected_idx_type][['ts_code', 'display_name']].drop_duplicates()
        
        # Create searchable multi-select
        if not available_indices.empty:
            index_options = available_indices.set_index('ts_code')['display_name'].to_dict()
            
            selected_indices = st.multiselect(
                "Choose indices to analyze (leave empty for all)",
                options=list(index_options.keys()),
                format_func=lambda x: index_options.get(x, x),
                help="Select one or more specific indices. If empty, all indices in the selected category will be shown.",
                max_selections=20  # Limit to prevent performance issues
            )
            
            if selected_indices:
                st.caption(f"**{len(selected_indices)}** indices selected")
        else:
            selected_indices = []
            st.info("No indices available for current filter")
        
        # 2. Date Range
        st.subheader("Analysis Period")
        latest_date_str = get_latest_trade_date()
        try:
            latest_date = datetime.strptime(latest_date_str, "%Y%m%d")
        except:
            latest_date = datetime.now()
        
        default_start = latest_date - timedelta(days=252)
        
        date_range = st.date_input(
            "Select Time Range",
            value=(default_start, latest_date),
            help="Start and end dates for analysis, defaults to the past year"
        )
        
        # Calculate limit_days
        if isinstance(date_range, tuple) and len(date_range) == 2:
            limit_days = (date_range[1] - date_range[0]).days
        else:
            limit_days = 252
        
        # 3. Advanced Filters
        with st.expander("Advanced Filters"):
            min_idx_count = st.slider(
                "Minimum Constituents",
                min_value=5, max_value=100, value=10,
                help="Filter out small sectors with too few constituents"
            )
            min_float_mv = st.number_input(
                "Minimum Market Cap (100M CNY)",
                min_value=0, max_value=10000, value=100,
                help="Filter out sectors with too small float market cap"
            )
    
    # ============ Load Data ============
    with st.spinner("Loading sector data..."):
        idx_type_filter = None if selected_idx_type == "all" else selected_idx_type
        
        df_daily = load_tdx_daily(limit_days=limit_days, idx_type_filter=idx_type_filter)
        
        # Apply specific index selection filter
        if selected_indices:
            df_daily = df_daily[df_daily['ts_code'].isin(selected_indices)]
            df_index = df_index[df_index['ts_code'].isin(selected_indices)]
        
        # Note: Advanced filters disabled temporarily due to data coverage issues
        # Will be re-enabled after validating data quality
        # if not df_index.empty:
        #     df_index = df_index[
        #         (df_index['idx_count'].fillna(0) >= min_idx_count) &
        #         (df_index['float_mv'].fillna(0) >= min_float_mv * 1e8)
        #     ]
        #     valid_codes = df_index['ts_code'].unique()
        #     df_daily = df_daily[df_daily['ts_code'].isin(valid_codes)]
    
    if df_daily.empty:
        st.warning("⚠️ No data available for current filter conditions. Please adjust filters.")
        return
    
    # Display data summary
    st.success(f"✅ Loaded **{len(df_daily):,}** quote records for **{df_daily['ts_code'].nunique()}** sectors")
    
    # ============ Latest Trading Day Overview ============
    st.markdown("---")
    st.subheader("📈 Latest Trading Day - Top Performers by Category")
    
    # Get latest trading date
    latest_date = df_daily['trade_date'].max()
    latest_date_dt = pd.to_datetime(latest_date, format='%Y%m%d')
    st.caption(f"Trading Date: {latest_date_dt.strftime('%Y-%m-%d')}")
    
    # Create tabs for each idx_type
    overview_tab1, overview_tab2, overview_tab3, overview_tab4 = st.tabs([
        "🏭 Industry Sectors",
        "💡 Theme/Concept Sectors", 
        "🗺️ Regional Sectors",
        "🎨 Style Sectors"
    ])
    
    idx_type_mapping = {
        0: "行业板块",
        1: "概念板块",
        2: "地区板块",
        3: "风格板块"
    }
    
    overview_tabs = [overview_tab1, overview_tab2, overview_tab3, overview_tab4]
    
    for tab_idx, tab in enumerate(overview_tabs):
        with tab:
            current_idx_type = idx_type_mapping[tab_idx]
            
            # Filter data for this idx_type
            type_codes = df_index[df_index['idx_type'] == current_idx_type]['ts_code'].unique()
            type_daily = df_daily[
                (df_daily['ts_code'].isin(type_codes)) & 
                (df_daily['trade_date'] == latest_date)
            ]
            
            if type_daily.empty:
                st.info(f"No data available for {current_idx_type}")
                continue
            
            # Merge with index info for names (use unique subset to avoid duplicates)
            unique_index_names = df_index[['ts_code', 'name']].drop_duplicates(subset=['ts_code'])
            type_merged = type_daily.merge(
                unique_index_names, 
                on='ts_code', 
                how='left'
            )
            
            # Drop any remaining duplicates by ts_code
            type_merged = type_merged.drop_duplicates(subset=['ts_code'])
            
            # Display Top Gainers and Losers side by side
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔥 Top 10 Gainers**")
                top_gainers = type_merged.nlargest(10, 'pct_change')[['name', 'pct_change', 'close']]
                top_gainers.columns = ['Sector Name', 'Return (%)', 'Close']
                st.dataframe(
                    top_gainers.style.format({
                        'Return (%)': '{:.2f}',
                        'Close': '{:.2f}'
                    }).background_gradient(cmap='Greens', subset=['Return (%)']),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                st.markdown("**❄️ Top 10 Losers**")
                top_losers = type_merged.nsmallest(10, 'pct_change')[['name', 'pct_change', 'close']]
                top_losers.columns = ['Sector Name', 'Return (%)', 'Close']
                st.dataframe(
                    top_losers.style.format({
                        'Return (%)': '{:.2f}',
                        'Close': '{:.2f}'
                    }).background_gradient(cmap='Reds_r', subset=['Return (%)']),
                    use_container_width=True,
                    hide_index=True
                )
    
    st.markdown("---")
    
    # ============ Main Tabs ============
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔄 Rotation",
        "💰 Capital Flow", 
        "🎭 Sentiment",
        "💎 Valuation",
        "🔥 Hot Topics",
        "🧩 Constituents"
    ])
    
    # --- Tab 1: Rotation Analysis ---
    with tab1:
        render_rotation_tab(df_daily, df_index)
    
    # --- Tab 2: Capital Flow ---
    with tab2:
        render_capital_tab(df_daily, df_index)
    
    # --- Tab 3: Sentiment ---
    with tab3:
        render_sentiment_tab(df_daily, df_index)
    
    # --- Tab 4-6: Placeholders ---
    with tab4:
        st.info("Valuation analysis features under development...")
    
    with tab5:
        st.info("Hot topics tracking features under development...")
    
    with tab6:
        st.info("Constituent analysis features under development...")


def render_rotation_tab(df_daily: pd.DataFrame, df_index: pd.DataFrame):
    """Render Rotation Analysis tab"""
    
    st.header("🔄 Sector Rotation Analysis")
    st.markdown("Identify leading/lagging sectors to determine market theme shifts")
    
    # Heatmap
    st.subheader("1. Return Distribution Heatmap")
    fig_heatmap = plot_sector_rotation_heatmap(df_daily, df_index, periods=[1, 5, 10, 20])
    if fig_heatmap:
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Top Gainers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("2. Gainers/Losers Ranking")
        period_col = st.selectbox(
            "Select Period",
            options=['pct_change', '5day', '10day', '20day'],
            format_func=lambda x: {'pct_change': 'Today', '5day': '5-Day', '10day': '10-Day', '20day': '20-Day'}[x],
            key="rotation_period"
        )
        
        fig_ranking = plot_top_gainers_ranking(df_daily, df_index, period_col=period_col, top_n=10)
        if fig_ranking:
            st.plotly_chart(fig_ranking, use_container_width=True)
    
    with col2:
        st.subheader("3. Sector Type Leadership Stats")
        fig_leadership = plot_idx_type_leadership(df_daily, df_index, window=20)
        if fig_leadership:
            st.plotly_chart(fig_leadership, use_container_width=True)


def render_capital_tab(df_daily: pd.DataFrame, df_index: pd.DataFrame):
    """Render Capital Flow tab"""
    
    st.header("💰 Capital Flow Analysis")
    st.markdown("Track institutional money flow to predict trend continuation")
    
    # Capital Flow Bars
    st.subheader("1. Net Capital Flow Ranking")
    fig_capital_bars = plot_capital_flow_bars(df_daily, df_index, top_n=15)
    if fig_capital_bars:
        st.plotly_chart(fig_capital_bars, use_container_width=True)
    else:
        st.warning("⚠️ Capital flow data has ~50% coverage, some sectors may have missing data")
    
    # Capital vs Return Scatter
    st.subheader("2. Capital-Driven Validation (Capital vs. Return)")
    period_days = st.slider("Accumulation Period (days)", 3, 20, 5, key="capital_period")
    
    fig_scatter = plot_capital_vs_return_scatter(df_daily, df_index, period_days=period_days)
    if fig_scatter:
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("💡 The more linear the scatter plot, the stronger the capital-driven effect on returns")


def render_sentiment_tab(df_daily: pd.DataFrame, df_index: pd.DataFrame):
    """Render Sentiment Analysis tab"""
    
    st.header("🎭 Market Sentiment Analysis")
    st.markdown("Quantify the money-making effect and assess market heat")
    
    # Sentiment Gauges
    st.subheader("1. Market Sentiment Dashboard")
    fig_gauges = plot_sentiment_gauges(df_daily)
    if fig_gauges:
        st.plotly_chart(fig_gauges, use_container_width=True)
    
    # Limit Up Analysis
    st.subheader("2. Limit-Up Stock Analysis")
    fig_limit_up = plot_limit_up_analysis(df_daily, df_index, top_n=10)
    if fig_limit_up:
        st.plotly_chart(fig_limit_up, use_container_width=True)
        st.caption("💡 High limit-up counts reflect strong market sentiment and money-making effects")
