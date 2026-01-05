import streamlit as st
import pandas as pd
from data_loader import load_pmi_data, load_sf_data, load_m_data
from charts import (plot_pmi_trend, plot_sub_indicators_bar, plot_heatmap, 
                    plot_sf_charts, plot_m_levels, plot_m_yoy, plot_m_mom)

# Page Configuration
st.set_page_config(
    page_title="China Macro Economic Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("China Macro Economic Dashboard")
st.markdown("Visualizing PMI trends and economic indicators from Tushare data.")

# Sidebar
st.sidebar.header("Configuration")
with st.sidebar:
    st.info("Data loaded from local DuckDB instance.")
    if st.button("Reload Data"):
        st.cache_data.clear()
        st.rerun()

# Load Data
with st.spinner('Loading data...'):
    df_pmi = load_pmi_data()
    df_sf = load_sf_data()
    df_m = load_m_data()

if df_pmi.empty and df_sf.empty and df_m.empty:
    st.error("No data available. Please check the database connection and path configuration.")
    st.stop()

# Date Filtering
all_dates = pd.concat([df_pmi['month'], df_sf['month'], df_m['month']]).dropna()
min_date = all_dates.min().date()
max_date = all_dates.max().date()

st.sidebar.subheader("Date Range")
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Filter data
def filter_df(df, start, end):
    if df.empty: return df
    mask = (df['month'].dt.date >= start) & (df['month'].dt.date <= end)
    return df.loc[mask]

df_pmi_f = filter_df(df_pmi, start_date, end_date)
df_sf_f = filter_df(df_sf, start_date, end_date)
df_m_f = filter_df(df_m, start_date, end_date)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["PMI Overview", "Money & Credit", "PMI Deep Dive", "Data Explorer"])

with tab1:
    st.header("PMI Trends")
    fig_trend = plot_pmi_trend(df_pmi_f)
    if fig_trend:
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Not enough PMI data to plot trends.")

with tab2:
    st.header("Money & Credit Analysis")
    
    # --- Social Financing Section ---
    st.subheader("Social Financing (TS: sf_month)")
    fig_sf_inc, fig_sf_cum, fig_sf_stk = plot_sf_charts(df_sf_f)
    if fig_sf_inc:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_sf_inc, use_container_width=True)
            st.plotly_chart(fig_sf_cum, use_container_width=True)
        with col2:
            st.plotly_chart(fig_sf_stk, use_container_width=True)
    else:
        st.info("No Social Financing data available.")
        
    st.divider()
    
    # --- Money Supply Section ---
    st.subheader("Money Supply (TS: cn_m)")
    fig_m_levels = plot_m_levels(df_m_f)
    fig_m_yoy = plot_m_yoy(df_m_f)
    fig_m_mom = plot_m_mom(df_m_f)
    
    if fig_m_levels:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_m_levels, use_container_width=True)
        with col2:
            st.plotly_chart(fig_m_yoy, use_container_width=True)
            st.plotly_chart(fig_m_mom, use_container_width=True)
    else:
        st.info("No Money Supply data available.")

with tab3:
    st.header("PMI Deep Dive Analysis")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Sub-indicators Heatmap")
        fig_heatmap = plot_heatmap(df_pmi_f)
        if fig_heatmap:
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("No sub-indicator data available.")
            
    with col2:
        st.subheader("Latest Month Breakdown")
        if not df_pmi_f.empty:
            latest_month_dt = df_pmi_f['month'].max()
            st.markdown(f"**Reporting Period:** {latest_month_dt.strftime('%Y-%m')}")
            
            df_latest = df_pmi_f[df_pmi_f['month'] == latest_month_dt]
            fig_bar = plot_sub_indicators_bar(df_latest)
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No data for the latest month.")
        else:
            st.info("No PMI data for breakdown.")

with tab4:
    st.header("Raw Data Explorer")
    dataset = st.selectbox("Select Dataset", ["PMI", "Social Financing", "Money Supply"])
    
    if dataset == "PMI":
        st.dataframe(df_pmi_f.sort_values(by='month', ascending=False), use_container_width=True)
    elif dataset == "Social Financing":
        st.dataframe(df_sf_f.sort_values(by='month', ascending=False), use_container_width=True)
    elif dataset == "Money Supply":
        st.dataframe(df_m_f.sort_values(by='month', ascending=False), use_container_width=True)
