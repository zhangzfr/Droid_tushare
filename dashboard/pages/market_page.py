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

    # --- Equity Pledge Sub-category ---
    elif subcategory_key == "pledge_data":
        render_header("Equity Pledge Analysis", "pulse")
        
        from dashboard.pledge_data_loader import get_pledge_stat_top, get_stock_pledge_history, get_pledge_details, get_pledge_industry_distribution
        from dashboard.pledge_charts import plot_top_pledge_ratio, plot_pledge_history, plot_pledge_industry_dist, plot_shareholder_distribution
        
        # Tabs for different views
        tab_risk, tab_trend, tab_industry, tab_details = st.tabs([
            "Risk Screening", "Trend Analysis", "Industry Distribution", "Pledge Details"
        ])
        
        with tab_risk:
            st.markdown("### High Pledge Risk Stocks")
            col1, col2 = st.columns([1, 4])
            with col1:

                top_n = st.slider("Display Top N", 10, 500, 20, key="pledge_top_n")
                
                # Styled Legend
                st.markdown("""
                <div style="padding: 10px; background-color: #f0f2f6; border-radius: 8px; font-size: 0.85rem;">
                    <strong>Pledge Thresholds</strong>
                    <div style="margin-top: 5px; display: flex; flex-direction: column; gap: 4px;">
                        <span style="color: #EF5350; font-weight: 600;">■ High Risk (> 50%)</span>
                        <span style="color: #FFA726; font-weight: 600;">■ Warning (30-50%)</span>
                        <span style="color: #66BB6A; font-weight: 600;">■ Safe (< 30%)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                df_top = get_pledge_stat_top(limit=top_n)
                if not df_top.empty:
                    fig_top = plot_top_pledge_ratio(df_top, top_n=top_n)
                    st.plotly_chart(fig_top, use_container_width=True)
                else:
                    st.warning("No pledge statistics data found.")

        with tab_trend:
            st.markdown("### Stock Pledge History")
            # Stock selector
            df_names = get_pledge_stat_top(limit=100) # Use top 100 as candidates
            if not df_names.empty:
                stock_options = [f"{row['ts_code']} - {row['name']}" for _, row in df_names.iterrows()]
                selected_stock = st.selectbox("Select Stock", stock_options, key="pledge_stock_sel")
                ts_code = selected_stock.split(' - ')[0]
                name = selected_stock.split(' - ')[1]
                
                df_hist = get_stock_pledge_history(ts_code)
                if not df_hist.empty:
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        fig_hist = plot_pledge_history(df_hist, ts_code, name)
                        st.plotly_chart(fig_hist, use_container_width=True)
                    with col_b:
                        # Shareholder breakdown for this stock
                        df_det = get_pledge_details(ts_code)
                        if not df_det.empty:
                            fig_pie = plot_shareholder_distribution(df_det)
                            st.plotly_chart(fig_pie, use_container_width=True)
                        else:
                            st.info("No detailed shareholder data for this stock.")
                else:
                    st.warning("No history data for the selected stock.")
            else:
                st.warning("No data available for selection.")

        with tab_industry:
            st.markdown("### Industry Risk Heatmap")
            df_ind = get_pledge_industry_distribution()
            if not df_ind.empty:
                fig_ind = plot_pledge_industry_dist(df_ind)
                st.plotly_chart(fig_ind, use_container_width=True)
                st.dataframe(df_ind.style.background_gradient(subset=['avg_pledge_ratio'], cmap='Reds'), use_container_width=True)
            else:
                st.warning("No industry distribution data found.")

        with tab_details:
            st.markdown("### Recent Pledge & Release Events")
            df_details = get_pledge_details(limit=200)
            if not df_details.empty:
                st.dataframe(
                    df_details.style.format({
                        'pledge_amount': '{:,.0f}',
                        'p_total_ratio': '{:.2f}%',
                        'h_total_ratio': '{:.2f}%'
                    }),
                    use_container_width=True,
                    column_config={
                        "ann_date": st.column_config.DateColumn("Announcement Date"),
                        "start_date": st.column_config.DateColumn("Start Date"),
                        "end_date": st.column_config.DateColumn("End Date"),
                        "release_date": st.column_config.DateColumn("Release Date"),
                        "is_release": "Released?",
                        "is_buyback": "Buyback?"
                    }
                )
            else:
                st.warning("No detailed pledge events found.")

    # --- Block Trade Sub-category ---
    elif subcategory_key == "block_trade":
        render_header("Block Trade Analysis", "chart")
        
        from dashboard.block_trade_data_loader import load_market_block_activity, load_top_block_trades, load_stock_block_history, load_broker_activity
        from dashboard.block_trade_charts import plot_market_block_trend, plot_top_block_trades, plot_stock_block_details, plot_broker_ranking
        
        # Date filter for overview
        st.sidebar.divider()
        st.sidebar.markdown("**Block Trade Range**")
        today = datetime.now()
        start_default = today - timedelta(days=90)
        bt_start = st.sidebar.date_input("Start", start_default, key="bt_start")
        bt_end = st.sidebar.date_input("End", today, key="bt_end")
        
        tab_market, tab_stock, tab_broker, tab_list = st.tabs([
            "Market Overview", "Stock Analysis", "Institutions & Brokers", "Detailed List"
        ])
        
        with tab_market:
            st.markdown("### Market Block Trade Activity")
            df_mkt = load_market_block_activity(bt_start.strftime('%Y%m%d'), bt_end.strftime('%Y%m%d'))
            if not df_mkt.empty:
                fig_mkt = plot_market_block_trend(df_mkt)
                st.plotly_chart(fig_mkt, use_container_width=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Total Transactions", f"{df_mkt['trade_count'].sum():,}")
                with c2:
                    st.metric("Total Amount (10k)", f"{df_mkt['total_amount'].sum():,.0f}")
            else:
                st.warning("No market-wide block trade data found for the selected period.")

        with tab_stock:
            st.markdown("### Individual Stock Analysis")
            col_sel, col_chart = st.columns([1, 4])
            
            with col_sel:
                # Use recent active stocks as options
                df_top_recent = load_top_block_trades(bt_end.strftime('%Y%m%d'), limit=100)
                if df_top_recent.empty:
                    # Fallback to some common stocks if no data for today
                    df_top_recent = load_top_block_trades((bt_end - timedelta(days=1)).strftime('%Y%m%d'), limit=100)
                
                if not df_top_recent.empty:
                    stock_options = [f"{row['ts_code']} - {row['name']}" for _, row in df_top_recent.iterrows()]
                    selected_stock = st.selectbox("Select Active Stock", stock_options, key="bt_stock_sel")
                    ts_code = selected_stock.split(' - ')[0]
                    name = selected_stock.split(' - ')[1]
                else:
                    ts_code = st.text_input("Enter Stock Code", "600519.SH", key="bt_stock_input")
                    name = ts_code
                
                st.info("Discount analysis compares block price vs. daily close.")

            with col_chart:
                df_hist = load_stock_block_history(ts_code, bt_start.strftime('%Y%m%d'), bt_end.strftime('%Y%m%d'))
                if not df_hist.empty:
                    fig_hist = plot_stock_block_details(df_hist, ts_code, name)
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.warning(f"No block trade history for {ts_code} in this period.")

        with tab_broker:
            st.markdown("### Top Brokers & Departments")
            df_buyer, df_seller = load_broker_activity(bt_start.strftime('%Y%m%d'), bt_end.strftime('%Y%m%d'))
            
            col_b, col_s = st.columns(2)
            with col_b:
                if not df_buyer.empty:
                    fig_b = plot_broker_ranking(df_buyer, "Top Buyer Departments", color='#26A69A')
                    st.plotly_chart(fig_b, use_container_width=True)
                else: st.info("No buyer data.")
            with col_s:
                if not df_seller.empty:
                    fig_s = plot_broker_ranking(df_seller, "Top Seller Departments", color='#EF5350')
                    st.plotly_chart(fig_s, use_container_width=True)
                else: st.info("No seller data.")

        with tab_list:
            st.markdown("### Detailed Transaction List")
            # Fetch latest data for list
            df_list = load_top_block_trades(bt_end.strftime('%Y%m%d'), limit=200)
            if not df_list.empty:
                st.dataframe(
                    df_list.style.format({'total_amount': '{:,.0f}', 'total_vol': '{:,.2f}', 'avg_price': '{:.2f}'}),
                    use_container_width=True,
                    column_config={
                        "ts_code": "Stock Code",
                        "name": "Name",
                        "trade_count": "Trades",
                        "total_vol": "Total Vol (10k)",
                        "total_amount": "Total Amount (10k)",
                        "avg_price": "Avg Price"
                    }
                )
            else:
                st.info("No transactions recorded for the end date.")
    
    # --- Risk Radar (Combined Analysis) ---
    elif subcategory_key == "risk_radar":
        render_header("Market Risk Radar", "alert")
        st.markdown("Combines **Equity Pledge** (Liquidity Pressure) and **Block Trade** (Selling Pressure) to identify high-risk stocks.")
        
        from dashboard.risk_radar_data_loader import get_combined_risk_data, calculate_risk_score
        from dashboard.risk_radar_charts import plot_risk_scatter, plot_risk_distribution
        
        # Controls
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            days_lookback = st.slider("Block Trade Lookback (Days)", 30, 365, 90)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_lookback)
        
        with st.spinner("Calculating composite risk scores..."):
            df_risk = get_combined_risk_data(start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
            df_risk = calculate_risk_score(df_risk)
            
        if not df_risk.empty:
            tab_radar, tab_list = st.tabs(["Risk Quadrant", "High Risk List"])
            
            with tab_radar:
                col_chart1, col_chart2 = st.columns([3, 2])
                with col_chart1:
                    st.markdown("#### Pledge Ratio vs. Block Trade Amount")
                    fig_scatter = plot_risk_scatter(df_risk)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                with col_chart2:
                    st.markdown("#### Industry Risk Profile")
                    fig_dist = plot_risk_distribution(df_risk)
                    st.plotly_chart(fig_dist, use_container_width=True)
                    
            with tab_list:
                st.markdown("#### High Risk Stocks (Top 50)")
                st.dataframe(
                    df_risk.sort_values('total_risk_score', ascending=False).head(50),
                    column_config={
                        "pledge_ratio": st.column_config.NumberColumn("Pledge %", format="%.2f%%"),
                        "block_amount": st.column_config.NumberColumn("Block Trade Amt", format="%d"),
                        "total_risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d")
                    },
                    use_container_width=True
                )
        else:
            st.warning("No data available for risk analysis.")
