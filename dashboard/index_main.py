import streamlit as st
import pandas as pd
from index_data_loader import (
    load_index_basic, get_indices_with_weight_data, 
    get_constituent_count_per_date, get_available_trade_dates,
    get_constituents_for_date
)
from index_charts import plot_constituent_count_over_time

# Page Configuration
st.set_page_config(
    page_title="Index Data Explorer",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Index Data Explorer")
st.markdown("Browse index metadata and constituent weights from Tushare data.")

# Load index basic data
with st.spinner('Loading index data...'):
    df_indices = load_index_basic()
    indices_with_weight = get_indices_with_weight_data()

if df_indices.empty:
    st.error("No index data available. Please check the database connection.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filter Indices")

# Get unique values for filters
markets = ['All'] + sorted(df_indices['market'].dropna().unique().tolist())
publishers = ['All'] + sorted(df_indices['publisher'].dropna().unique().tolist())
index_types = ['All'] + sorted(df_indices['index_type'].dropna().unique().tolist())
categories = ['All'] + sorted(df_indices['category'].dropna().unique().tolist())

selected_market = st.sidebar.selectbox("Market", markets)
selected_publisher = st.sidebar.selectbox("Publisher", publishers)
selected_index_type = st.sidebar.selectbox("Index Type", index_types)
selected_category = st.sidebar.selectbox("Category", categories)

# Apply filters
df_filtered = df_indices.copy()
if selected_market != 'All':
    df_filtered = df_filtered[df_filtered['market'] == selected_market]
if selected_publisher != 'All':
    df_filtered = df_filtered[df_filtered['publisher'] == selected_publisher]
if selected_index_type != 'All':
    df_filtered = df_filtered[df_filtered['index_type'] == selected_index_type]
if selected_category != 'All':
    df_filtered = df_filtered[df_filtered['category'] == selected_category]

# Add column to indicate weight data availability
df_filtered['has_weight'] = df_filtered['ts_code'].isin(indices_with_weight)

st.sidebar.markdown(f"**Showing {len(df_filtered)} indices**")
st.sidebar.markdown(f"*(with weight data: {df_filtered['has_weight'].sum()})*")

# --- Main Content ---
tab1, tab2 = st.tabs(["📋 Index List", "🔬 Index Details"])

with tab1:
    st.header("Index List")
    
    # Display columns selection
    display_cols = ['ts_code', 'name', 'market', 'publisher', 'index_type', 'category', 
                    'base_date', 'base_point', 'list_date', 'weight_rule', 'desc', 'exp_date', 'has_weight']
    
    st.dataframe(
        df_filtered[display_cols],
        use_container_width=True,
        height=500,
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
            "weight_rule": "Weight Rule",
            "desc": "Description",
            "exp_date": "Expiry Date",
            "has_weight": st.column_config.CheckboxColumn("Weight Data")
        }
    )

with tab2:
    st.header("Index Details")
    
    # Select an index with weight data
    indices_with_weight_in_filter = df_filtered[df_filtered['has_weight']]['ts_code'].tolist()
    
    if not indices_with_weight_in_filter:
        st.info("No indices with weight data in current filter. Adjust filters or select from all indices with weight data.")
        indices_with_weight_in_filter = indices_with_weight
    
    if not indices_with_weight_in_filter:
        st.warning("No index weight data available in the database.")
    else:
        selected_index = st.selectbox(
            "Select Index (with weight data)", 
            indices_with_weight_in_filter,
            format_func=lambda x: f"{x} - {df_indices[df_indices['ts_code'] == x]['name'].values[0] if len(df_indices[df_indices['ts_code'] == x]) > 0 else x}"
        )
        
        if selected_index:
            # Show index info
            idx_info = df_indices[df_indices['ts_code'] == selected_index]
            if not idx_info.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Index Code", selected_index)
                    st.metric("Name", idx_info['name'].values[0])
                with col2:
                    st.metric("Market", idx_info['market'].values[0])
                    st.metric("Publisher", idx_info['publisher'].values[0])
                with col3:
                    st.metric("Base Date", idx_info['base_date'].values[0])
                    st.metric("Base Point", idx_info['base_point'].values[0])
            
            st.divider()
            
            # Constituent count chart
            st.subheader("📈 Constituent Count Over Time")
            st.markdown("*Use this chart to identify potential missing data (sudden drops in count)*")
            
            df_counts = get_constituent_count_per_date(selected_index)
            if not df_counts.empty:
                fig = plot_constituent_count_over_time(df_counts)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Trade Dates", len(df_counts))
                with col2:
                    st.metric("Avg Constituents", f"{df_counts['constituent_count'].mean():.0f}")
                with col3:
                    st.metric("Min/Max", f"{df_counts['constituent_count'].min()} / {df_counts['constituent_count'].max()}")
            else:
                st.info("No constituent count data available.")
            
            st.divider()
            
            # Trade date selection for detailed view
            st.subheader("📋 Constituents by Trade Date")
            
            trade_dates = get_available_trade_dates(selected_index)
            if trade_dates:
                selected_date = st.selectbox("Select Trade Date", trade_dates)
                
                if selected_date:
                    df_constituents = get_constituents_for_date(selected_index, selected_date)
                    if not df_constituents.empty:
                        st.markdown(f"**{len(df_constituents)} constituents on {selected_date}**")
                        st.dataframe(
                            df_constituents,
                            use_container_width=True,
                            height=400,
                            column_config={
                                "con_code": "Constituent Code",
                                "weight": st.column_config.NumberColumn("Weight (%)", format="%.4f")
                            }
                        )
                        
                        # Weight distribution
                        st.markdown("**Weight Distribution (Top 10)**")
                        top10 = df_constituents.head(10)
                        st.bar_chart(top10.set_index('con_code')['weight'])
                    else:
                        st.warning("No constituent data for this date.")
            else:
                st.info("No trade dates available for this index.")
