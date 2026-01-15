"""
Macro Data Page
==============
Visualizations for macroeconomic indicators including PMI, Money Supply, Social Financing, and Price Indices.
"""
import streamlit as st
import textwrap
import pandas as pd
from datetime import date
from dashboard.components.headers import render_header

# Import data loaders and charts
from dashboard.data_loader import load_pmi_data, load_sf_data, load_m_data, load_gdp_data
from dashboard.charts import (plot_pmi_trend, plot_sub_indicators_bar, plot_heatmap, 
                    plot_sf_charts, plot_m_levels, plot_m_yoy, plot_m_mom,
                    plot_gdp_trend, plot_gdp_yoy)

# Import Price Index modules
from dashboard.price_index_data_loader import (
    load_cpi_data, load_ppi_data,
    prepare_ppi_chain_data, prepare_scissors_data
)
from dashboard.price_index_charts import (
    plot_cpi_ppi_trend, plot_cpi_components, plot_ppi_sectors,
    plot_cpi_heatmap, plot_ppi_heatmap, plot_seasonality_chart,
    plot_mom_trend, get_latest_metrics,
    plot_ppi_chain_trend, plot_scissors_difference
)

def render_macro_page(subcategory_key):
    """
    Render the macro data page based on the selected subcategory.
    """
    # Load all macro data (common for some subcats, specific for others)
    # To optimize, we could load only what's needed, but for now we follow existing logic
    # or better, load lazily based on subcategory.
    
    # Common filter helper
    def filter_df(df, start, end):
        if df.empty: return df
        mask = (df['month'].dt.date >= start) & (df['month'].dt.date <= end)
        return df.loc[mask]

    # --- GDP Sub-category ---
    if subcategory_key == "gdp":
        with st.spinner('Loading GDP data...'):
            df_gdp = load_gdp_data()
        
        render_header("Gross Domestic Product (GDP)", "gdp")
        
        if not df_gdp.empty and 'quarter_date' in df_gdp.columns:
            min_date = df_gdp['quarter_date'].min().date()
            max_date = df_gdp['quarter_date'].max().date()
        else:
            min_date, max_date = date(1990, 1, 1), date.today()
            
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="gdp_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="gdp_end")
            
        # Filter helper for quarter_date
        def filter_gdp(df, start, end):
             if df.empty or 'quarter_date' not in df.columns: return df
             mask = (df['quarter_date'].dt.date >= start) & (df['quarter_date'].dt.date <= end)
             return df.loc[mask]

        df_gdp_f = filter_gdp(df_gdp, start_date, end_date)
        
        with right_col:
            if df_gdp_f.empty:
                 st.warning("No GDP data available")
            else:
                 tab1, tab2 = st.tabs(["Trends", "Raw Data"])
                 with tab1:
                     st.subheader("GDP Growth & Structure")
                     fig_trend = plot_gdp_trend(df_gdp_f)
                     if fig_trend:
                         st.plotly_chart(fig_trend, use_container_width=True)
                         st.caption("Source: cn_gdp")
                     
                     st.markdown("---")
                     
                     st.subheader("YoY Growth Rate")
                     fig_yoy = plot_gdp_yoy(df_gdp_f)
                     if fig_yoy:
                         st.plotly_chart(fig_yoy, use_container_width=True)
                         st.caption("Source: cn_gdp")
                         
                 with tab2:
                     st.dataframe(df_gdp_f.sort_values('quarter_date', ascending=False), use_container_width=True)

    # --- PMI Sub-category ---
    elif subcategory_key == "pmi":
        with st.spinner('Loading PMI data...'):
            df_pmi = load_pmi_data()
            
        render_header("PMI Manufacturing Index", "pmi")
        
        # Calculate date range
        if not df_pmi.empty:
            min_date = df_pmi['month'].min().date()
            max_date = df_pmi['month'].max().date()
        else:
            min_date, max_date = date(2010, 1, 1), date.today()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="pmi_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="pmi_end")
        
        df_pmi_f = filter_df(df_pmi, start_date, end_date)
        
        with right_col:
            if df_pmi_f.empty:
                st.warning("No PMI data available")
            else:
                tab1, tab2, tab3 = st.tabs(["Trend", "Heatmap Analysis", "Raw Data"])
                
                with tab1:
                    fig_trend = plot_pmi_trend(df_pmi_f)
                    if fig_trend:
                        st.plotly_chart(fig_trend, use_container_width=True, key="pmi_trend")
                        st.caption("Source: cn_pmi")
                
                with tab2:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.subheader("Sub-indicators Heatmap")
                        fig_heatmap = plot_heatmap(df_pmi_f)
                        if fig_heatmap:
                            st.plotly_chart(fig_heatmap, use_container_width=True, key="pmi_heatmap")
                            st.caption("Source: cn_pmi")
                    
                    with col2:
                        st.subheader("Latest Month Breakdown")
                        if not df_pmi_f.empty:
                            latest = df_pmi_f['month'].max()
                            st.markdown(f"**Report Period:** {latest.strftime('%Y-%m')}")
                            df_latest = df_pmi_f[df_pmi_f['month'] == latest]
                            fig_bar = plot_sub_indicators_bar(df_latest)
                            if fig_bar:
                                st.plotly_chart(fig_bar, use_container_width=True, key="pmi_bar")
                                st.caption("Source: cn_pmi")
                
                with tab3:
                    st.dataframe(df_pmi_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Money Supply Sub-category ---
    elif subcategory_key == "money_supply":
        with st.spinner('Loading Money Supply data...'):
            df_m = load_m_data()
            
        render_header("Money Supply (M0/M1/M2)", "money")
        
        if not df_m.empty:
            min_date = df_m['month'].min().date()
            max_date = df_m['month'].max().date()
        else:
            min_date, max_date = date(2010, 1, 1), date.today()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="m_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="m_end")
        
        df_m_f = filter_df(df_m, start_date, end_date)
        
        with right_col:
            if df_m_f.empty:
                st.warning("No money supply data available")
            else:
                tab1, tab2, tab3 = st.tabs(["Levels", "Growth Rates", "Raw Data"])
                
                with tab1:
                    fig_levels = plot_m_levels(df_m_f)
                    if fig_levels:
                        st.plotly_chart(fig_levels, use_container_width=True, key="m_levels")
                        st.caption("Source: cn_m")
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Year-over-Year (YoY)")
                        fig_yoy = plot_m_yoy(df_m_f)
                        if fig_yoy:
                            st.plotly_chart(fig_yoy, use_container_width=True, key="m_yoy")
                            st.caption("Source: cn_m")
                    with col2:
                        st.subheader("Month-over-Month (MoM)")
                        fig_mom = plot_m_mom(df_m_f)
                        if fig_mom:
                            st.plotly_chart(fig_mom, use_container_width=True, key="m_mom")
                            st.caption("Source: cn_m")
                
                with tab3:
                    st.dataframe(df_m_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Social Financing Sub-category ---
    elif subcategory_key == "social_financing":
        with st.spinner('Loading Social Financing data...'):
            df_sf = load_sf_data()
            
        render_header("Social Financing", "social")
        
        if not df_sf.empty:
            min_date = df_sf['month'].min().date()
            max_date = df_sf['month'].max().date()
        else:
            min_date, max_date = date(2010, 1, 1), date.today()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="sf_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="sf_end")
        
        df_sf_f = filter_df(df_sf, start_date, end_date)
        
        with right_col:
            if df_sf_f.empty:
                st.warning("No social financing data available")
            else:
                tab1, tab2 = st.tabs(["Charts", "Raw Data"])
                
                with tab1:
                    fig_inc, fig_cum, fig_stk = plot_sf_charts(df_sf_f)
                    if fig_inc:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Monthly Increment")
                            st.plotly_chart(fig_inc, use_container_width=True, key="sf_inc")
                            st.caption("Source: cn_sf")
                            st.subheader("Cumulative Value")
                            st.plotly_chart(fig_cum, use_container_width=True, key="sf_cum")
                            st.caption("Source: cn_sf")
                        with col2:
                            st.subheader("Stock End Value")
                            st.plotly_chart(fig_stk, use_container_width=True, key="sf_stk")
                            st.caption("Source: cn_sf")
                
                with tab2:
                    st.dataframe(df_sf_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Price Index Sub-category ---
    elif subcategory_key == "price_index":
        render_header("Price Index (CPI / PPI)", "price")
        
        # Load data
        with st.spinner('Loading price index data...'):
            df_cpi = load_cpi_data()
            df_ppi = load_ppi_data()
        
        if df_cpi.empty and df_ppi.empty:
            st.warning("No price index data available. Please ensure cn_cpi and cn_ppi tables are populated.")
        else:
            # Calculate date range
            all_months = pd.concat([
                df_cpi['month'] if not df_cpi.empty else pd.Series(dtype='datetime64[ns]'),
                df_ppi['month'] if not df_ppi.empty else pd.Series(dtype='datetime64[ns]')
            ]).dropna()
            
            if not all_months.empty:
                min_date = all_months.min().date()
                max_date = all_months.max().date()
            else:
                min_date, max_date = date(2010, 1, 1), date.today()
            
            # Get latest metrics
            metrics = get_latest_metrics(df_cpi, df_ppi)
            
            # Left-right layout
            left_col, right_col = st.columns([1, 7])
            
            with left_col:
                st.markdown("**Date Range**")
                start_date = st.date_input("Start", min_date, min_value=min_date, max_value=max_date, key="pi_start")
                end_date = st.date_input("End", max_date, min_value=min_date, max_value=max_date, key="pi_end")
                
                st.markdown("---")
                st.markdown("**Latest Data**")
                
                if metrics['cpi_yoy'] is not None:
                    delta = f"{metrics['cpi_yoy_change']:+.1f}" if metrics['cpi_yoy_change'] else None
                    st.metric("CPI YoY", f"{metrics['cpi_yoy']:.1f}%", delta=delta)
                
                if metrics['ppi_yoy'] is not None:
                    delta = f"{metrics['ppi_yoy_change']:+.1f}" if metrics['ppi_yoy_change'] else None
                    st.metric("PPI YoY", f"{metrics['ppi_yoy']:.1f}%", delta=delta)
                
                if metrics['cpi_date']:
                    st.caption(f"Updated to: {metrics['cpi_date']}")
            
            df_cpi_f = filter_df(df_cpi, start_date, end_date)
            df_ppi_f = filter_df(df_ppi, start_date, end_date)
            
            with right_col:
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "📈 Overview", "🌡️ CPI Analysis", "🏭 PPI Analysis", 
                    "📊 Heatmaps", "🔄 Seasonality", "🔍 Deep Dive"
                ])
                
                with tab1:
                    st.subheader("CPI vs PPI Long-term Trend")
                    fig_trend = plot_cpi_ppi_trend(df_cpi_f, df_ppi_f)
                    if fig_trend:
                        st.plotly_chart(fig_trend, use_container_width=True, key="cpi_ppi_trend")
                    else:
                        st.info("No data available for trend chart")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("CPI MoM Trend")
                        fig_cpi_mom = plot_mom_trend(df_cpi_f, 'nt_mom', "CPI National MoM")
                        if fig_cpi_mom:
                            st.plotly_chart(fig_cpi_mom, use_container_width=True, key="cpi_mom")
                    
                    with col2:
                        st.subheader("PPI MoM Trend")
                        fig_ppi_mom = plot_mom_trend(df_ppi_f, 'ppi_mom', "PPI Overall Index MoM")
                        if fig_ppi_mom:
                            st.plotly_chart(fig_ppi_mom, use_container_width=True, key="ppi_mom")
                
                with tab2:
                    st.subheader("CPI Regional Comparison")
                    fig_cpi_comp = plot_cpi_components(df_cpi_f)
                    if fig_cpi_comp:
                        st.plotly_chart(fig_cpi_comp, use_container_width=True, key="cpi_components")
                    
                    st.markdown("---")
                    st.subheader("Raw CPI Data")
                    if not df_cpi_f.empty:
                        display_cols = ['month', 'nt_yoy', 'nt_mom', 'town_yoy', 'town_mom', 'cnt_yoy', 'cnt_mom']
                        display_df = df_cpi_f[[c for c in display_cols if c in df_cpi_f.columns]].sort_values('month', ascending=False)
                        st.dataframe(display_df, use_container_width=True)
                
                with tab3:
                    st.subheader("PPI Sector Comparison")
                    fig_ppi_sectors = plot_ppi_sectors(df_ppi_f)
                    if fig_ppi_sectors:
                        st.plotly_chart(fig_ppi_sectors, use_container_width=True, key="ppi_sectors")
                    
                    st.markdown("---")
                    st.subheader("Raw PPI Data")
                    if not df_ppi_f.empty:
                        display_cols = ['month', 'ppi_yoy', 'ppi_mom', 'ppi_mp_yoy', 'ppi_cg_yoy']
                        display_df = df_ppi_f[[c for c in display_cols if c in df_ppi_f.columns]].sort_values('month', ascending=False)
                        st.dataframe(display_df, use_container_width=True)
                
                with tab4:
                    st.markdown(textwrap.dedent("""
                    > **Color Legend**: 🔴 Red = Inflation (positive) | 🟢 Green = Deflation (negative)
                    """))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("CPI Heatmap")
                        fig_cpi_heat = plot_cpi_heatmap(df_cpi_f, n_months=12)
                        if fig_cpi_heat:
                            st.plotly_chart(fig_cpi_heat, use_container_width=True, key="cpi_heatmap")
                    
                    with col2:
                        st.subheader("PPI Heatmap")
                        fig_ppi_heat = plot_ppi_heatmap(df_ppi_f, n_months=12)
                        if fig_ppi_heat:
                            st.plotly_chart(fig_ppi_heat, use_container_width=True, key="ppi_heatmap")
                
                with tab5:
                    st.markdown(textwrap.dedent("""
                    Seasonality analysis shows month-over-month patterns across different years.
                    This helps identify predictable seasonal effects in inflation data.
                    """))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("CPI MoM Seasonality")
                        fig_cpi_season = plot_seasonality_chart(df_cpi_f, 'nt_mom', "CPI MoM Seasonality", n_years=3)
                        if fig_cpi_season:
                            st.plotly_chart(fig_cpi_season, use_container_width=True, key="cpi_seasonality")
                    
                    with col2:
                        st.subheader("PPI MoM Seasonality")
                        fig_ppi_season = plot_seasonality_chart(df_ppi_f, 'ppi_mom', "PPI MoM Seasonality", n_years=3)
                        if fig_ppi_season:
                            st.plotly_chart(fig_ppi_season, use_container_width=True, key="ppi_seasonality")

                with tab6:
                    st.markdown(textwrap.dedent("""
                    ### 🏭 PPI Industry Chain & Scissors Analysis
                    
                    **Deep dive analysis** into the transmission of price changes through the industrial chain and the relationship between upstream/downstream prices.
                    """))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Scissors (PPI-CPI)", 
                                 f"{metrics['ppi_yoy'] - metrics['cpi_yoy']:.1f}%" if metrics['ppi_yoy'] is not None and metrics['cpi_yoy'] is not None else "N/A",
                                 delta=None, help="Positive = Upstream Inflation > Downstream Cost")
                    
                    st.subheader("PPI Industry Chain Transmission (Mining → Raw → Processing)")
                    df_chain = prepare_ppi_chain_data(df_ppi_f)
                    fig_chain = plot_ppi_chain_trend(df_chain)
                    if fig_chain:
                        st.plotly_chart(fig_chain, use_container_width=True, key="ppi_chain")
                    
                    st.markdown("---")
                    
                    st.subheader("Scissors Gap Analysis (PPI - CPI)")
                    df_scissors = prepare_scissors_data(df_cpi_f, df_ppi_f)
                    fig_scissors = plot_scissors_difference(df_scissors)
                    if fig_scissors:
                        st.plotly_chart(fig_scissors, use_container_width=True, key="ppi_scissors")
