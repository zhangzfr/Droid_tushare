"""
FX Education Page
================
Educational content and visualizations for foreign exchange and commodities.
"""
import streamlit as st
import textwrap
import pandas as pd
from datetime import datetime, timedelta
from dashboard.components.headers import render_header

# Import FX data modules
from dashboard.fx_data_loader import (
    load_fx_obasic, load_fx_daily, get_available_fx_codes,
    calculate_returns, calculate_volatility, create_price_pivot,
    create_returns_pivot, calculate_correlation_matrix,
    calculate_rolling_correlation, aggregate_monthly, calculate_annualized_stats,
    DEFAULT_FX_ASSETS
)
from dashboard.fx_charts import (
    plot_classify_pie, plot_asset_table_summary,
    plot_price_lines, plot_log_returns, plot_price_distribution, plot_volatility_bar,
    plot_correlation_heatmap, plot_scatter_matrix, plot_rolling_correlation,
    plot_monthly_return_heatmap, plot_volatility_line, plot_risk_return_scatter,
    plot_seasonality_bar
)

def render_fx_edu_page(subcategory_key):
    """
    Render the FX Education page based on the selected subcategory.
    """
    # Load basic info (always needed)
    with st.spinner('Loading FX asset data...'):
        df_obasic = load_fx_obasic()
    
    if df_obasic.empty:
        st.error("Unable to load FX data. Please check database connection.")
        st.stop()
    
    # Get available codes grouped by classification
    available_codes = get_available_fx_codes()
    all_codes = df_obasic['ts_code'].tolist()
    
    # Calculate date range defaults
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- Level 1: Asset Overview ---
    if subcategory_key == "fx_assets":
        render_header("Level 1: Asset Overview", "asset")
        
        # Educational intro
        st.markdown(textwrap.dedent("""
        ### 📚 What Are Financial Assets?
        
        Financial markets trade different types of assets, each representing a different form of value:
        
        - **FX (Foreign Exchange)**: Currency pairs like EUR/USD represent the exchange rate between two currencies
        - **Commodities**: Physical goods like Gold (XAUUSD) and Oil (USOIL) that are traded on global markets  
        - **Indices**: Stock market benchmarks like the Dow Jones (US30) and NASDAQ (NAS100)
        
        Understanding these asset classes is the first step to learning about global financial markets!
        """))
        
        st.divider()
        
        # Layout
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Filters**")
            classifications = df_obasic['classify'].dropna().unique().tolist()
            
            # Category checkboxes
            st.markdown("*Category*")
            sel_classify = []
            for cls in classifications:
                if st.checkbox(cls, value=True, key=f"fx_cls_cb_{cls}"):
                    sel_classify.append(cls)
        
        # Filter data
        df_filtered = df_obasic.copy()
        if sel_classify:
            df_filtered = df_filtered[df_filtered['classify'].isin(sel_classify)]
        
        with right_col:
            tab1, tab2 = st.tabs(["📊 Overview", "📋 Asset Details"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_pie = plot_classify_pie(df_filtered)
                    if fig_pie:
                        st.plotly_chart(fig_pie, use_container_width=True, key="fx_pie")
                        st.caption("Source: fx_obasic")
                
                with col2:
                    fig_bar = plot_asset_table_summary(df_filtered)
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True, key="fx_bar")
                        st.caption("Source: fx_obasic")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Assets", len(df_filtered))
                col2.metric("Categories", len(df_filtered['classify'].unique()))
                col3.metric("Exchanges", len(df_filtered['exchange'].dropna().unique()))
            
            with tab2:
                st.dataframe(
                    df_filtered[['ts_code', 'name', 'classify', 'exchange', 'pip', 'pip_cost', 'trading_hours']],
                    use_container_width=True,
                    height=500,
                    column_config={
                        "ts_code": "Symbol",
                        "name": "Name",
                        "classify": "Category",
                        "exchange": "Exchange",
                        "pip": st.column_config.NumberColumn("Pip Value", format="%.5f"),
                        "pip_cost": st.column_config.NumberColumn("Pip Cost", format="%.2f"),
                        "trading_hours": "Trading Hours"
                    }
                )
        
        # Thought questions
        with st.expander("🤔 Think About It"):
            st.markdown(textwrap.dedent("""
            1. Why do you think FX pairs like EURUSD have different trading characteristics than commodities like Gold?
            2. What determines the 'pip' value for different assets?
            3. How might trading hours affect price volatility?
            """))
    
    # --- Level 2: Price Dynamics ---
    elif subcategory_key == "fx_price":
        render_header("Level 2: Price Dynamics", "chart")
        
        # Educational intro
        st.markdown(textwrap.dedent("""
        ### 📈 Understanding Price Movements
        
        Prices of financial assets constantly fluctuate based on supply and demand, economic news, and market sentiment.
        
        **Key Concepts:**
        - **Time Series**: A sequence of prices over time
        - **Returns**: The percentage change in price (how much you gain or lose)
        - **Log Returns**: ln(P_t / P_{t-1}) - mathematically preferred for analysis
        - **Volatility**: How much prices fluctuate - higher volatility means higher risk AND potential reward
        """))
        
        st.divider()
        
        # Sidebar filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start", default_start.date(), key="fx_price_start")
            end_date = st.date_input("End", default_end.date(), key="fx_price_end")
            
            st.markdown("**Select Assets**")
            # Filter by category first - checkboxes
            classifications = df_obasic['classify'].dropna().unique().tolist()
            st.markdown("*Category Filter*")
            sel_classify = []
            for cls in classifications:
                if st.checkbox(cls, value=True, key=f"fx_price_cls_{cls}"):
                    sel_classify.append(cls)
            
            # Filter codes
            available = df_obasic[df_obasic['classify'].isin(sel_classify)]['ts_code'].tolist() if sel_classify else all_codes
            
            # Group assets by classification for checkbox selection
            st.markdown("*Assets*")
            sel_codes = []
            default_assets = DEFAULT_FX_ASSETS[:4]
            for cls in sel_classify:
                cls_assets = [a for a in available if df_obasic[df_obasic['ts_code'] == a]['classify'].values[0] == cls if len(df_obasic[df_obasic['ts_code'] == a]) > 0]
                if cls_assets:
                    st.markdown(f"_{cls}_")
                    for asset in cls_assets[:10]:  # Limit per group
                        if st.checkbox(asset, value=asset in default_assets, key=f"fx_price_ast_{asset}"):
                            sel_codes.append(asset)
        
        if not sel_codes:
            st.info("Please select at least one asset to analyze.")
        else:
            with st.spinner('Loading price data...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_fx_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("No price data available for the selected assets and date range.")
            else:
                # Calculate returns
                df_returns = calculate_returns(df_daily, 'mid_close', 'log')
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Trend", "📉 Returns", "📊 Volatility", "📋 Raw Data"])
                    
                    with tab1:
                        normalize = st.toggle("Normalize prices (base = 100)", value=True, key="fx_normalize")
                        fig_lines = plot_price_lines(df_daily, sel_codes, normalize=normalize)
                        if fig_lines:
                            st.plotly_chart(fig_lines, use_container_width=True, key="fx_price_lines")
                            st.caption("Source: fx_daily")
                    
                    with tab2:
                        fig_returns = plot_log_returns(df_returns, sel_codes)
                        if fig_returns:
                            st.plotly_chart(fig_returns, use_container_width=True, key="fx_returns")
                            st.caption("Source: fx_daily")
                        
                        st.subheader("Returns Distribution")
                        fig_dist = plot_price_distribution(df_returns.dropna(), None)
                        if fig_dist:
                            st.plotly_chart(fig_dist, use_container_width=True, key="fx_dist")
                            st.caption("Source: fx_daily")
                    
                    with tab3:
                        # Calculate annualized stats
                        df_pivot = create_returns_pivot(df_returns)
                        df_stats = calculate_annualized_stats(df_pivot)
                        
                        if not df_stats.empty:
                            # Metrics
                            st.subheader("Daily Volatility Comparison")
                            fig_vol_bar = plot_volatility_bar(df_stats)
                            if fig_vol_bar:
                                st.plotly_chart(fig_vol_bar, use_container_width=True, key="fx_vol_bar")
                                st.caption("Source: fx_daily")
                            
                            # Stats table
                            st.subheader("Summary Statistics")
                            st.dataframe(
                                df_stats[['ts_code', 'annualized_return', 'annualized_volatility', 'sharpe_ratio']],
                                use_container_width=True,
                                column_config={
                                    "ts_code": "Asset",
                                    "annualized_return": st.column_config.NumberColumn("Annualized Return", format="%.2%"),
                                    "annualized_volatility": st.column_config.NumberColumn("Annualized Vol", format="%.2%"),
                                    "sharpe_ratio": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f")
                                }
                            )
                    
                    with tab4:
                        st.dataframe(
                            df_daily[['ts_code', 'trade_date', 'mid_open', 'mid_high', 'mid_low', 'mid_close', 'tick_qty']].sort_values(['ts_code', 'trade_date'], ascending=[True, False]),
                            use_container_width=True,
                            height=500
                        )
                
                # Thought questions
                with st.expander("🤔 Think About It"):
                    st.markdown(textwrap.dedent("""
                    1. Why might crude oil (USOIL) show higher volatility than EUR/USD?
                    2. What does a Sharpe Ratio > 1 indicate about an asset's risk-adjusted performance?
                    3. Why do we normalize prices to compare assets with different price levels?
                    """))
    
    # --- Level 3: Correlations ---
    elif subcategory_key == "fx_corr":
        render_header("Level 3: Correlations", "correlation")
        
        # Educational intro
        st.markdown(textwrap.dedent("""
        ### 🔗 Understanding Asset Correlations
        
        **Correlation** measures how two assets move together:
        - **+1.0**: Perfect positive correlation (move together)
        - **0.0**: No correlation (move independently)
        - **-1.0**: Perfect negative correlation (move opposite)
        
        **Why It Matters:**
        - **Portfolio Diversification**: Combining negatively correlated assets reduces overall risk
        - **Hedging**: Using one asset to offset risk in another
        - **Trading Signals**: Strong correlations can break down during market stress
        
        Example: Gold (XAUUSD) often moves opposite to the US Dollar - investors buy gold as a "safe haven" when USD weakens.
        """))
        
        st.divider()
        
        # Sidebar filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start", default_start.date(), key="fx_corr_start")
            end_date = st.date_input("End", default_end.date(), key="fx_corr_end")
            
            st.markdown("**Select Assets**")
            # Group assets by category for checkbox selection
            classifications = df_obasic['classify'].dropna().unique().tolist()
            sel_codes = []
            default_assets = DEFAULT_FX_ASSETS[:6]
            
            for cls in classifications:
                cls_assets = df_obasic[df_obasic['classify'] == cls]['ts_code'].tolist()
                if cls_assets:
                    st.markdown(f"*{cls}*")
                    for asset in cls_assets[:8]:  # Limit per group
                        if st.checkbox(asset, value=asset in default_assets, key=f"fx_corr_ast_{asset}"):
                            sel_codes.append(asset)
        
        if len(sel_codes) < 2:
            st.info("Please select at least 2 assets to analyze correlations.")
        else:
            with st.spinner('Loading data and calculating correlations...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_fx_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("No data available for the selected assets and date range.")
            else:
                # Calculate returns and correlations
                df_returns = calculate_returns(df_daily, 'mid_close', 'log')
                df_pivot = create_returns_pivot(df_returns)
                df_corr = calculate_correlation_matrix(df_pivot)
                
                with right_col:
                    tab1, tab2, tab3 = st.tabs(["🔥 Correlation Heatmap", "🔄 Rolling Correlation", "⚡ Scatter Matrix"])
                    
                    with tab1:
                        if not df_corr.empty:
                            fig_heatmap = plot_correlation_heatmap(df_corr)
                            if fig_heatmap:
                                st.plotly_chart(fig_heatmap, use_container_width=True, key="fx_corr_heatmap")
                                st.caption("Source: fx_daily")
                            
                            # Highlight interesting pairs
                            st.subheader("Notable Correlations")
                            corr_pairs = []
                            for i in range(len(df_corr.columns)):
                                for j in range(i+1, len(df_corr.columns)):
                                    corr_val = df_corr.iloc[i, j]
                                    corr_pairs.append({
                                        'Pair': f"{df_corr.columns[i]} vs {df_corr.columns[j]}",
                                        'Correlation': corr_val,
                                        'Relationship': 'Positive' if corr_val > 0.3 else ('Negative' if corr_val < -0.3 else 'Weak')
                                    })
                            
                            import pandas as pd
                            df_pairs = pd.DataFrame(corr_pairs).sort_values('Correlation', key=abs, ascending=False).head(5)
                            st.dataframe(df_pairs, use_container_width=True, hide_index=True)
                    
                    with tab2:
                        st.markdown("**Select Two Assets for Rolling Correlation**")
                        col1, col2 = st.columns(2)
                        with col1:
                            asset1 = st.selectbox("Asset 1", sel_codes, key="fx_roll_asset1")
                        with col2:
                            asset2 = st.selectbox("Asset 2", [c for c in sel_codes if c != asset1], key="fx_roll_asset2")
                        
                        if asset1 and asset2:
                            rolling_corr = calculate_rolling_correlation(df_pivot, asset1, asset2, window=30)
                            fig_roll = plot_rolling_correlation(rolling_corr, asset1, asset2)
                            if fig_roll:
                                st.plotly_chart(fig_roll, use_container_width=True, key="fx_roll_corr")
                                st.caption("Source: fx_daily")
                    
                    with tab3:
                        # Limit to 5 assets for readability
                        scatter_codes = sel_codes[:5]
                        fig_scatter = plot_scatter_matrix(df_pivot, scatter_codes)
                        if fig_scatter:
                            st.plotly_chart(fig_scatter, use_container_width=True, key="fx_scatter")
                            st.caption("Source: fx_daily")
                
                # Thought questions
                with st.expander("🤔 Think About It"):
                    st.markdown(textwrap.dedent("""
                    1. Why might Gold (XAUUSD) and the US Dollar Index (USDOLLAR) be negatively correlated?
                    2. If two assets have a correlation of 0.8, does buying both provide good diversification?
                    3. Why might correlations change during market stress events (like a financial crisis)?
                    4. How would you use correlation analysis to build a diversified portfolio?
                    """))
    
    # --- Level 4: Advanced Analysis ---
    elif subcategory_key == "fx_advanced":
        render_header("Level 4: Advanced Analysis", "analysis")
        
        # Educational intro
        st.markdown(textwrap.dedent("""
        ### 🎓 Advanced Financial Analysis
        
        This section covers more sophisticated concepts used by professional traders and analysts:
        
        - **Seasonality**: Recurring patterns at specific times of year (e.g., energy prices in winter)
        - **Volatility Clustering**: High volatility tends to follow high volatility
        - **Risk-Return Tradeoff**: Higher expected returns usually come with higher risk
        - **Monthly/Annual Patterns**: Identifying trends over longer time horizons
        
        These tools help analysts predict future behavior and make informed investment decisions.
        """))
        
        st.divider()
        
        # Sidebar filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            # Use longer default for advanced analysis
            adv_start = default_end - timedelta(days=730)  # 2 years
            start_date = st.date_input("Start", adv_start.date(), key="fx_adv_start")
            end_date = st.date_input("End", default_end.date(), key="fx_adv_end")
            
            st.markdown("**Select Assets**")
            # Group assets by category for checkbox selection
            classifications = df_obasic['classify'].dropna().unique().tolist()
            sel_codes = []
            default_assets = DEFAULT_FX_ASSETS[:4]
            
            for cls in classifications:
                cls_assets = df_obasic[df_obasic['classify'] == cls]['ts_code'].tolist()
                if cls_assets:
                    st.markdown(f"*{cls}*")
                    for asset in cls_assets[:6]:  # Limit per group
                        if st.checkbox(asset, value=asset in default_assets, key=f"fx_adv_ast_{asset}"):
                            sel_codes.append(asset)
        
        if not sel_codes:
            st.info("Please select at least one asset for advanced analysis.")
        else:
            with st.spinner('Loading data for advanced analysis...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_fx_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("No data available for the selected assets and date range.")
            else:
                # Calculate various metrics
                df_returns = calculate_returns(df_daily, 'mid_close', 'log')
                df_vol = calculate_volatility(df_returns, window=20)
                df_monthly = aggregate_monthly(df_daily)
                df_pivot = create_returns_pivot(df_returns)
                df_stats = calculate_annualized_stats(df_pivot)
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📅 Seasonality", "📊 Volatility Trends", "⚖️ Risk-Return", "📋 Monthly Data"])
                    
                    with tab1:
                        st.subheader("Monthly Performance Heatmap")
                        sel_asset = st.selectbox("Select Asset", sel_codes, key="fx_season_asset")
                        
                        if sel_asset:
                            fig_monthly = plot_monthly_return_heatmap(df_monthly, sel_asset)
                            if fig_monthly:
                                st.plotly_chart(fig_monthly, use_container_width=True, key="fx_monthly_heatmap")
                                st.caption("Source: fx_daily")
                            
                            # Seasonality bar
                            st.subheader("Average Return by Month")
                            fig_season = plot_seasonality_bar(df_monthly, sel_asset)
                            if fig_season:
                                st.plotly_chart(fig_season, use_container_width=True, key="fx_season_bar")
                                st.caption("Source: fx_daily")
                    
                    with tab2:
                        st.subheader("Rolling 20-Day Volatility")
                        fig_vol_line = plot_volatility_line(df_vol, sel_codes)
                        if fig_vol_line:
                            st.plotly_chart(fig_vol_line, use_container_width=True, key="fx_vol_line")
                            st.caption("Source: fx_daily")
                        
                        st.caption("Notice how volatility tends to cluster - periods of high volatility are often followed by more high volatility.")
                    
                    with tab3:
                        st.subheader("Risk vs Return Profile")
                        if not df_stats.empty:
                            fig_rr = plot_risk_return_scatter(df_stats)
                            if fig_rr:
                                st.plotly_chart(fig_rr, use_container_width=True, key="fx_risk_return")
                                st.caption("Source: fx_daily")
                            
                            st.markdown(textwrap.dedent("""
                            **How to Read This Chart:**
                            - **X-axis (Volatility)**: Higher = more risky
                            - **Y-axis (Return)**: Higher = better performance
                            - **Color (Sharpe Ratio)**: Green = better risk-adjusted return
                            - **Ideal position**: Top-left (high return, low risk)
                            """))
                    
                    with tab4:
                        st.dataframe(
                            df_monthly[['ts_code', 'month', 'mid_open', 'mid_high', 'mid_low', 'mid_close', 'monthly_return']].sort_values(['ts_code', 'month'], ascending=[True, False]),
                            use_container_width=True,
                            height=500,
                            column_config={
                                "monthly_return": st.column_config.NumberColumn("Monthly Return", format="%.2%")
                            }
                        )
                
                # Thought questions
                with st.expander("🤔 Think About It"):
                    st.markdown(textwrap.dedent("""
                    1. Why might energy commodities show strong seasonality patterns?
                    2. What causes volatility clustering? (Hint: think about news and market psychology)
                    3. Is the Sharpe Ratio > 1 indicate about an asset's risk-adjusted performance? What are its limitations?
                    4. How might macroeconomic events (interest rate changes, elections) affect these patterns?
                    """))
