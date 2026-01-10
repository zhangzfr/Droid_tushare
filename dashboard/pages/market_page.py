"""
Market Data Page
===============
Visualizations for stock market data including Listing Statistics and Uplift Detection.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import importlib
from dashboard.components.headers import render_header

# Import stock data modules
from dashboard.stock_data_loader import get_listing_delisting_stats, load_stock_basic_sample
from dashboard.stock_charts import plot_listing_delisting_trend, plot_listing_summary

def render_market_page(subcategory_key):
    """
    Render the market data page based on the selected subcategory.
    """
    # --- Listing Statistics Sub-category ---
    if subcategory_key == "listing_stats":
        render_header("Listing Statistics", "listing")
        
        with st.spinner('Calculating statistics...'):
            df_stats = get_listing_delisting_stats()
            
        if df_stats.empty:
            st.warning("No stock basic data available to calculate statistics.")
        else:
            df_stats['year'] = df_stats['month'].dt.year
            years = sorted(df_stats['year'].unique().tolist(), reverse=True)
            
            # Left-right layout
            left_col, right_col = st.columns([1, 5])
            
            with left_col:
                st.markdown("**Year Filter**")
                # Modified to Radio with ranges for better UI
                period_opt = st.radio(
                    "Select Period", 
                    ["Last 5 Years", "Last 10 Years", "All History"], 
                    index=0, 
                    key="listing_period"
                )
                
                current_year = df_stats['year'].max()
                if period_opt == "Last 5 Years":
                    start_year = current_year - 4
                elif period_opt == "Last 10 Years":
                    start_year = current_year - 9
                else:
                    start_year = df_stats['year'].min()
            
            df_f = df_stats[df_stats['year'] >= start_year]
            
            with right_col:
                # Key Metrics
                total_listings = df_f['listings'].sum()
                total_delistings = df_f['delistings'].sum()
                net_growth = total_listings - total_delistings
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Listings", int(total_listings))
                with col2:
                    st.metric("Total Delistings", int(total_delistings))
                with col3:
                    st.metric("Net Growth", int(net_growth))
                    
                st.divider()
                
                tab1, tab2, tab3 = st.tabs(["Trends", "Growth", "Monthly Data"])
                
                with tab1:
                    fig_trend = plot_listing_delisting_trend(df_f)
                    if fig_trend:
                        st.plotly_chart(fig_trend, use_container_width=True, key="listing_trend")
                        st.caption("Source: stock_basic")
                        
                with tab2:
                    fig_growth = plot_listing_summary(df_f)
                    if fig_growth:
                        st.plotly_chart(fig_growth, use_container_width=True, key="listing_growth")
                        st.caption("Source: stock_basic")
                        
                with tab3:
                    st.markdown("**Monthly Statistics (Sorted by Date)**")
                    st.dataframe(
                        df_f.sort_values('month', ascending=False),
                        use_container_width=True,
                        column_config={
                            "month": st.column_config.DatetimeColumn("Month", format="YYYY-MM"),
                            "listings": "New Listings",
                            "delistings": "Delistings",
                            "net_growth": "Net Growth",
                            "year": None
                    }
                )

    # --- Main Uplift Detection Sub-category ---
    # Trigger reload
    elif subcategory_key == "uplift_detect":
        render_header("Main Uplift Detection", "pulse")
        
        # Add project root to path to allow importing from utils
        current_dir = os.path.dirname(os.path.abspath(__file__)) # dashboard/pages
        dashboard_dir = os.path.dirname(current_dir) # dashboard
        project_root = os.path.dirname(dashboard_dir) # Droid_tushare
        
        if project_root not in sys.path:
            sys.path.append(project_root)
            
        import utils.uplift_detector
        importlib.reload(utils.uplift_detector)
        from utils.uplift_detector import fetch_stock_data, detect_main_uplift, detect_main_decline, calculate_technical_indicators
        
        # Adjust import since we are in a package now? 
        # dashboard.uplift_charts vs uplift_charts
        # In app.py it was `import uplift_charts`. app.py is in dashboard/.
        # Now we are in dashboard/pages/.
        # `import dashboard.uplift_charts` should work if dashboard is a package (has __init__.py).
        # We need to ensure dashboard has __init__.py.
        # But wait, original code used sys.path or relative imports?
        # app.py is in dashboard/, so `import uplift_charts` worked because `.` was implicitly in path or dashboard was cwd.
        # Streamlit execution makes the script's dir the main path.
        # If we run `streamlit run dashboard/app.py`, `dashboard/` is added to path.
        # When extracting to `dashboard/pages/market_page.py`, we import `dashboard.stock_data_loader`.
        # So we should import `dashboard.uplift_charts`.
        
        import dashboard.uplift_charts as uplift_charts
        importlib.reload(uplift_charts)
        from dashboard.uplift_charts import plot_uplift_analysis
        
        # Left-right layout
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.markdown("**Parameters**")
            ts_code = st.text_input("Stock Code", value="000001.SZ", help="e.g. 000001.SZ, 600519.SH")
            
            today = datetime.now()
            start_default = today - timedelta(days=365)
            
            start_date = st.date_input("Start Date", start_default, key="uplift_start")
            end_date = st.date_input("End Date", today, key="uplift_end")
            
            with st.expander("Strategy Hyperparameters"):
                st.markdown("**Moving Averages**")
                ma_short = st.number_input("Short Window", min_value=1, value=5, key="hp_ma_short")
                ma_mid = st.number_input("Mid Window", min_value=1, value=20, key="hp_ma_mid")
                ma_long = st.number_input("Long Window", min_value=1, value=60, key="hp_ma_long")
                
                st.divider()
                st.markdown("**Volume & Thresholds**")
                vma_window = st.number_input("Volume MA Window", min_value=1, value=20, key="hp_vma_window")
                volume_factor = st.slider("Volume Factor (x VMA)", 1.0, 5.0, 1.5, step=0.1, key="hp_vol_factor")
            
            run_btn = st.button("Detect Uplift", type="primary", use_container_width=True)
            
        with col2:
            if run_btn or ts_code: # Auto-run if code is present (optional, but button is better for resource control)
                 if run_btn:
                    if not ts_code:
                        st.warning("Please enter a stock code.")
                    else:
                        with st.spinner(f"Fetching data and detecting uplift for {ts_code}..."):
                            # Fetch Data
                            df = fetch_stock_data(ts_code, start_date, end_date)
                            
                            if df.empty:
                                st.error(f"No data found for {ts_code} in the selected range. Please check the code and database.")
                            else:
                                # Calculate Indicators with custom params
                                df = calculate_technical_indicators(
                                    df, 
                                    ma_short=ma_short, 
                                    ma_mid=ma_mid, 
                                    ma_long=ma_long, 
                                    vma_window=vma_window
                                )
                                
                                # Detect Uplift and Decline with custom factor
                                df_analyzed = detect_main_uplift(df, volume_factor=volume_factor)
                                df_analyzed = detect_main_decline(df_analyzed, volume_factor=volume_factor)
                                
                                # Visualize
                                fig = plot_uplift_analysis(df_analyzed, ts_code)
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    st.caption("Source: stock_daily")
                                    
                                    # Summary stats
                                    uplift_days = df_analyzed[df_analyzed['main_uplift']]
                                    decline_days = df_analyzed[df_analyzed['main_decline']] if 'main_decline' in df_analyzed.columns else pd.DataFrame()
                                    
                                    st.divider()
                                    metric_cols = st.columns(4)
                                    metric_cols[0].metric("Total Data Points", len(df_analyzed))
                                    metric_cols[1].metric("Uplift Signals", len(uplift_days))
                                    metric_cols[2].metric("Decline Signals", len(decline_days))
                                    
                                    if len(uplift_days) > 0:
                                        last_signal = uplift_days.index.max().strftime('%Y-%m-%d')
                                        metric_cols[3].metric("Last Uplift", last_signal)
                                    
                                    if len(decline_days) > 0:
                                         with st.expander("View Decline Signal Dates"):
                                            st.write(decline_days.index.strftime('%Y-%m-%d').tolist())
                                        
                                    if len(uplift_days) > 0:
                                        with st.expander("View Uplift Signal Dates"):
                                            st.write(uplift_days.index.strftime('%Y-%m-%d').tolist())
