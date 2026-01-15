import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import textwrap
import sys
import os
import importlib
from dashboard.components.headers import render_header

# ... (imports continue)

# ... (inside render_vix_page function, at the end)

from dashboard.vix_data_loader import get_available_underlyings, calculate_vix_series, get_default_date_range
from dashboard.vix_charts import (
    plot_vix_trend, plot_vix_components, plot_vix_distribution,
    plot_forward_prices, plot_weight_trend
)

def render_vix_page(subcategory_key):
    """
    Render the VIX calculator page.
    """
    if subcategory_key == "vix_calc":
        render_header("VIX Calculator", "vix")
        
        # Get available underlyings
        underlyings = get_available_underlyings()
        underlying_codes = list(underlyings.keys())
        
        # Default date range
        default_start, default_end = get_default_date_range()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 4])
        
        with left_col:
            # ETF Options group
            st.markdown("<small>*ETF Options*</small>", unsafe_allow_html=True)
            etf_codes = ['510050.SH', '510300.SH', '510500.SH', '159919.SZ', '159915.SZ', '159922.SZ']
            sel_etf = []
            for code in etf_codes:
                if code in underlying_codes:
                    if st.checkbox(underlyings.get(code, code), value=code == '510050.SH', key=f"vix_cb_{code}"):
                        sel_etf.append(code)
            
            st.markdown("<small>*Index Options*</small>", unsafe_allow_html=True)
            index_codes = ['000300.SH', '000016.SH', '000852.SH', '000905.SH', '000510.SH']
            sel_index = []
            for code in index_codes:
                if code in underlying_codes:
                    if st.checkbox(underlyings.get(code, code), value=False, key=f"vix_cb_{code}"):
                        sel_index.append(code)
            
            selected_underlyings = sel_etf + sel_index
            
            st.markdown("---")
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", default_start, key="vix_start")
            end_date = st.date_input("End Date", default_end, key="vix_end")
            
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                calculate_btn = st.button("Calculate", type="primary", use_container_width=True)
            with col_btn2:
                if st.button("Clear Cache", use_container_width=True):
                    st.cache_data.clear()
                    st.session_state['vix_calculated'] = False
                    st.rerun()
        
        # Convert dates to strings
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        # Create a unique key for current parameters to detect changes
        current_params = f"{'-'.join(selected_underlyings)}_{start_str}_{end_str}"
        
        with right_col:
            # Calculate when button is clicked
            if calculate_btn:
                # Store current params and mark as calculated
                st.session_state['vix_params'] = current_params
                st.session_state['vix_calculated'] = True
            
            # Show results if calculated with current params
            if st.session_state.get('vix_calculated', False) and st.session_state.get('vix_params') == current_params:
                with st.spinner(f"Calculating VIX for {', '.join(selected_underlyings)}..."):
                    # Loop calculation
                    results_map = {}
                    df_summary = pd.DataFrame() # Combined summary for table (maybe just last one? or concat)
                    df_near_all = pd.DataFrame()
                    df_next_all = pd.DataFrame()
                    
                    for code in selected_underlyings:
                         s_df, n_df, nx_df = calculate_vix_series(start_str, end_str, code)
                         if not s_df.empty:
                             s_df['underlying'] = code
                             results_map[code] = s_df
                             df_summary = pd.concat([df_summary, s_df])
                             df_near_all = pd.concat([df_near_all, n_df])
                             df_next_all = pd.concat([df_next_all, nx_df])
                
                if df_summary.empty:
                    st.warning("No VIX data could be calculated. Please check if option data and Shibor data are available for the selected period.")
                else:
                    # Show data coverage info
                    actual_start = df_summary['date'].min().strftime('%Y-%m-%d')
                    actual_end = df_summary['date'].max().strftime('%Y-%m-%d')
                    if actual_end != end_date.strftime('%Y-%m-%d'):
                        st.caption(f"ℹ️ Data available for {len(results_map)} assets. VIX requires both option and Shibor data.")
                    
                    # Key Metrics (Aggregated or for first asset)
                    if results_map:
                         # Just display first one or average? Let's display metrics for the first selected asset as primary
                         primary_code = selected_underlyings[0]
                         if primary_code in results_map:
                            prim_df = results_map[primary_code]
                            latest_vix = prim_df['vix'].iloc[-1]
                            avg_vix = prim_df['vix'].mean()
                            max_vix = prim_df['vix'].max()
                            min_vix = prim_df['vix'].min()
                            
                            st.markdown(f"**Metrics for {underlyings.get(primary_code, primary_code)}**")
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("Latest VIX", f"{latest_vix:.2f}")
                            col2.metric("Average", f"{avg_vix:.2f}")
                            col3.metric("Maximum", f"{max_vix:.2f}")
                            col4.metric("Minimum", f"{min_vix:.2f}")
                    
                    st.divider()
                    
                    # Tabs for different views
                    tab1, tab2, tab3, tab4 = st.tabs(["VIX Trend", "Components", "Analysis", "Raw Data"])
                    
                    with tab1:
                        if len(results_map) > 1:
                            # Plot multiple lines
                            fig_trend = px.line(df_summary, x='date', y='vix', color='underlying', title="VIX Trend Comparison")
                            st.plotly_chart(fig_trend, use_container_width=True, key="vix_trend_multi")
                        elif primary_code in results_map:
                            fig_trend = plot_vix_trend(results_map[primary_code], primary_code)
                            if fig_trend:
                                st.plotly_chart(fig_trend, use_container_width=True, key="vix_trend")
                        
                        st.caption("Source: opt_daily, shibor")
                        
                        # Distribution
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_dist = plot_vix_distribution(df_summary)
                            if fig_dist:
                                st.plotly_chart(fig_dist, use_container_width=True, key="vix_dist")
                                st.caption("Source: opt_daily")
                        with col2:
                            fig_weight = plot_weight_trend(df_summary)
                            if fig_weight:
                                st.plotly_chart(fig_weight, use_container_width=True, key="vix_weight")
                                st.caption("Source: opt_daily")
                    
                    with tab2:
                        fig_comp = plot_vix_components(df_summary)
                        if fig_comp:
                            st.plotly_chart(fig_comp, use_container_width=True, key="vix_comp")
                            st.caption("Source: opt_daily")
                        
                        fig_fwd = plot_forward_prices(df_summary)
                        if fig_fwd:
                            st.plotly_chart(fig_fwd, use_container_width=True, key="vix_fwd")
                            st.caption("Source: opt_daily")
                    
                    with tab3:
                        st.subheader("VIX Statistics")
                        
                        stats_data = {
                            "Metric": ["Count", "Mean", "Std Dev", "Min", "25%", "50%", "75%", "Max"],
                            "Value": [
                                str(len(df_summary)),
                                f"{df_summary['vix'].mean():.4f}",
                                f"{df_summary['vix'].std():.4f}",
                                f"{df_summary['vix'].min():.4f}",
                                f"{df_summary['vix'].quantile(0.25):.4f}",
                                f"{df_summary['vix'].quantile(0.50):.4f}",
                                f"{df_summary['vix'].quantile(0.75):.4f}",
                                f"{df_summary['vix'].max():.4f}"
                            ]
                        }
                        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
                        
                        st.subheader("Calculation Details")
                        st.caption("The VIX is calculated using near-term and next-term options with interpolation to 30-day implied volatility.")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Near Term σ² Statistics**")
                            st.metric("Avg σ² Near", f"{df_summary['sigma_sq_near'].mean():.6f}")
                        with col2:
                            st.markdown("**Next Term σ² Statistics**")
                            st.metric("Avg σ² Next", f"{df_summary['sigma_sq_next'].mean():.6f}")
                    
                    with tab4:
                        st.subheader("VIX Summary Data")
                        display_cols = ['date_str', 'vix', 'near_term', 'next_term', 'r_near', 'r_next', 
                                       'sigma_sq_near', 'sigma_sq_next', 'F_near', 'F_next', 'weight']
                        st.dataframe(
                            df_summary[display_cols].sort_values('date_str', ascending=False),
                            use_container_width=True,
                            column_config={
                                "date_str": "Date",
                                "vix": st.column_config.NumberColumn("VIX", format="%.4f"),
                                "near_term": st.column_config.NumberColumn("Near Term", format="%.4f"),
                                "next_term": st.column_config.NumberColumn("Next Term", format="%.4f"),
                                "r_near": st.column_config.NumberColumn("R Near", format="%.4f"),
                                "r_next": st.column_config.NumberColumn("R Next", format="%.4f"),
                                "sigma_sq_near": st.column_config.NumberColumn("σ² Near", format="%.6f"),
                                "sigma_sq_next": st.column_config.NumberColumn("σ² Next", format="%.6f"),
                                "F_near": st.column_config.NumberColumn("F Near", format="%.4f"),
                                "F_next": st.column_config.NumberColumn("F Next", format="%.4f"),
                                "weight": st.column_config.NumberColumn("Weight", format="%.4f")
                            }
                        )
            else:
                # Show instructions when no calculation or parameters changed
                if st.session_state.get('vix_calculated', False) and st.session_state.get('vix_params') != current_params:
                    st.info("Parameters changed. Click 'Calculate VIX' to recalculate with new settings.")
                else:
                    st.info("Select an underlying asset and date range, then click 'Calculate VIX' to compute the volatility index.")
                
                st.markdown(textwrap.dedent("""
                ### About VIX Calculation
                
                The VIX (Volatility Index) measures the market's expectation of 30-day forward-looking volatility.
                It is calculated using option prices on the selected underlying asset.
                
                **Key Parameters:**
                - **Near Term**: Options expiring in less than 30 days
                - **Next Term**: Options expiring after 30 days
                - **Interpolation**: Weighted average to target 30-day volatility
                
                **Supported Underlyings:**
                - ETF Options: 300ETF, 50ETF, 500ETF, etc.
                - Index Options: CSI 300, SSE 50, CSI 1000
                """))

    elif subcategory_key == "uplift_detect":
        render_header("Main Uplift Detection", "pulse")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_dir = os.path.dirname(current_dir)
        project_root = os.path.dirname(dashboard_dir)
        
        if project_root not in sys.path:
            sys.path.append(project_root)
            
        import utils.uplift_detector
        importlib.reload(utils.uplift_detector)
        from utils.uplift_detector import fetch_stock_data, detect_main_uplift, detect_main_decline, calculate_technical_indicators
        
        import dashboard.uplift_charts as uplift_charts
        importlib.reload(uplift_charts)
        from dashboard.uplift_charts import plot_uplift_analysis
        
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
            if run_btn or ts_code:
                 if run_btn:
                    if not ts_code:
                        st.warning("Please enter a stock code.")
                    else:
                        with st.spinner(f"Fetching data and detecting uplift for {ts_code}..."):
                            df = fetch_stock_data(ts_code, start_date, end_date)
                            
                            if df.empty:
                                st.error(f"No data found for {ts_code} in the selected range. Please check the code and database.")
                            else:
                                df = calculate_technical_indicators(
                                    df, 
                                    ma_short=ma_short, 
                                    ma_mid=ma_mid, 
                                    ma_long=ma_long, 
                                    vma_window=vma_window
                                )
                                
                                df_analyzed = detect_main_uplift(df, volume_factor=volume_factor)
                                df_analyzed = detect_main_decline(df_analyzed, volume_factor=volume_factor)
                                
                                fig = plot_uplift_analysis(df_analyzed, ts_code)
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                    st.caption("Source: stock_daily")
                                    
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
