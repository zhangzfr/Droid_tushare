import streamlit as st
import pandas as pd
from data_loader import load_pmi_data
from charts import plot_pmi_trend, plot_sub_indicators_bar, plot_heatmap

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
        st.experimental_rerun()

# Load Data
with st.spinner('Loading data...'):
    df = load_pmi_data()

if df.empty:
    st.error("No data available. Please check the database connection and path configuration.")
    st.stop()

# Date Filtering (Optional enhancement)
min_date = df['month'].min().date()
max_date = df['month'].max().date()

st.sidebar.subheader("Date Range")
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Filter data based on selection
mask = (df['month'].dt.date >= start_date) & (df['month'].dt.date <= end_date)
df_filtered = df.loc[mask]

# Tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Deep Dive", "Data Explorer"])

with tab1:
    st.header("PMI Trends")
    fig_trend = plot_pmi_trend(df_filtered)
    if fig_trend:
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Not enough data to plot trends.")

with tab2:
    st.header("Deep Dive Analysis")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Sub-indicators Heatmap")
        fig_heatmap = plot_heatmap(df_filtered)
        if fig_heatmap:
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("No sub-indicator data available.")
            
    with col2:
        st.subheader("Latest Month Breakdown")
        latest_month_dt = df_filtered['month'].max()
        st.markdown(f"**Reporting Period:** {latest_month_dt.strftime('%Y-%m')}")
        
        df_latest = df_filtered[df_filtered['month'] == latest_month_dt]
        fig_bar = plot_sub_indicators_bar(df_latest)
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No data for the latest month.")

with tab3:
    st.header("Raw Data")
    st.dataframe(df_filtered.sort_values(by='month', ascending=False), use_container_width=True)
