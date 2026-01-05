"""
Unified Dashboard Entry Point
============================
This is the main entry point for all visualizations.
Navigation hierarchy:
- Level 1: Data Category (Macro, Index, etc.)
- Level 2: Sub-category (PMI, Money Supply, etc.)
- Level 3: Specific content/charts
"""
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="📊 Tushare Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better navigation styling
st.markdown("""
<style>
    .nav-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #1f77b4;
    }
    .nav-description {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Tushare 数据可视化平台")
st.markdown("集成宏观经济、指数数据等多维度金融数据可视化")

# ================================
# Navigation Structure
# ================================
NAVIGATION = {
    "🏠 首页": {
        "key": "home",
        "subcategories": {}
    },
    "📈 宏观数据 (Macro)": {
        "key": "macro",
        "subcategories": {
            "PMI 制造业指数": "pmi",
            "货币供应量 (M0/M1/M2)": "money_supply",
            "社会融资规模": "social_financing"
        }
    },
    "📊 指数数据 (Index)": {
        "key": "index",
        "subcategories": {
            "指数列表": "index_list",
            "指数成分股详情": "index_details"
        }
    }
}

# ================================
# Sidebar Navigation
# ================================
st.sidebar.title("🧭 导航")

# Level 1: Category Selection
category_names = list(NAVIGATION.keys())
selected_category = st.sidebar.selectbox(
    "选择数据类别",
    category_names,
    index=0,
    key="nav_category"
)

category_config = NAVIGATION[selected_category]

# Level 2: Sub-category Selection (if applicable)
selected_subcategory = None
subcategories = category_config.get("subcategories", {})

if subcategories:
    subcategory_names = list(subcategories.keys())
    selected_subcategory = st.sidebar.selectbox(
        "选择子类别",
        subcategory_names,
        key="nav_subcategory"
    )
    subcategory_key = subcategories[selected_subcategory]
else:
    subcategory_key = None

st.sidebar.divider()

# ================================
# Main Content Area
# ================================

# --- HOME PAGE ---
if category_config["key"] == "home":
    st.header("欢迎使用 Tushare 数据可视化平台")
    
    st.markdown("""
    ### 📌 功能概览
    
    本平台整合了多种金融数据的可视化分析功能，帮助您快速了解市场动态。
    
    #### 当前支持的数据类别：
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ##### 📈 宏观数据
        - **PMI 制造业指数**：追踪制造业景气度变化
        - **货币供应量 (M0/M1/M2)**：分析货币政策走向
        - **社会融资规模**：监测实体经济融资状况
        """)
    
    with col2:
        st.markdown("""
        ##### 📊 指数数据
        - **指数列表**：浏览所有指数基础信息
        - **指数成分股详情**：查看成分股权重及历史变化
        """)
    
    st.info("💡 使用左侧导航栏选择您要查看的数据类别")

# --- MACRO DATA ---
elif category_config["key"] == "macro":
    # Import macro data modules
    from data_loader import load_pmi_data, load_sf_data, load_m_data
    from charts import (plot_pmi_trend, plot_sub_indicators_bar, plot_heatmap, 
                        plot_sf_charts, plot_m_levels, plot_m_yoy, plot_m_mom)
    import pandas as pd
    
    # Load all macro data
    with st.spinner('加载宏观数据...'):
        df_pmi = load_pmi_data()
        df_sf = load_sf_data()
        df_m = load_m_data()
    
    # Date filtering in sidebar
    all_dates = pd.concat([df_pmi['month'], df_sf['month'], df_m['month']]).dropna()
    if not all_dates.empty:
        min_date = all_dates.min().date()
        max_date = all_dates.max().date()
        
        st.sidebar.subheader("📅 日期筛选")
        start_date = st.sidebar.date_input("开始日期", min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("结束日期", max_date, min_value=min_date, max_value=max_date)
        
        # Filter helper
        def filter_df(df, start, end):
            if df.empty: return df
            mask = (df['month'].dt.date >= start) & (df['month'].dt.date <= end)
            return df.loc[mask]
        
        df_pmi_f = filter_df(df_pmi, start_date, end_date)
        df_sf_f = filter_df(df_sf, start_date, end_date)
        df_m_f = filter_df(df_m, start_date, end_date)
    else:
        df_pmi_f, df_sf_f, df_m_f = df_pmi, df_sf, df_m
    
    # --- PMI Sub-category ---
    if subcategory_key == "pmi":
        st.header("📈 PMI 制造业指数")
        
        if df_pmi_f.empty:
            st.warning("暂无 PMI 数据")
        else:
            tab1, tab2, tab3 = st.tabs(["趋势图", "热力图分析", "原始数据"])
            
            with tab1:
                fig_trend = plot_pmi_trend(df_pmi_f)
                if fig_trend:
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            with tab2:
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("分项指标热力图")
                    fig_heatmap = plot_heatmap(df_pmi_f)
                    if fig_heatmap:
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                
                with col2:
                    st.subheader("最新月份分项对比")
                    if not df_pmi_f.empty:
                        latest = df_pmi_f['month'].max()
                        st.markdown(f"**报告期:** {latest.strftime('%Y-%m')}")
                        df_latest = df_pmi_f[df_pmi_f['month'] == latest]
                        fig_bar = plot_sub_indicators_bar(df_latest)
                        if fig_bar:
                            st.plotly_chart(fig_bar, use_container_width=True)
            
            with tab3:
                st.dataframe(df_pmi_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Money Supply Sub-category ---
    elif subcategory_key == "money_supply":
        st.header("💰 货币供应量 (M0/M1/M2)")
        
        if df_m_f.empty:
            st.warning("暂无货币供应量数据")
        else:
            tab1, tab2, tab3 = st.tabs(["存量水平", "同比增速", "原始数据"])
            
            with tab1:
                fig_levels = plot_m_levels(df_m_f)
                if fig_levels:
                    st.plotly_chart(fig_levels, use_container_width=True)
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("同比增速 (YoY)")
                    fig_yoy = plot_m_yoy(df_m_f)
                    if fig_yoy:
                        st.plotly_chart(fig_yoy, use_container_width=True)
                with col2:
                    st.subheader("环比增速 (MoM)")
                    fig_mom = plot_m_mom(df_m_f)
                    if fig_mom:
                        st.plotly_chart(fig_mom, use_container_width=True)
            
            with tab3:
                st.dataframe(df_m_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Social Financing Sub-category ---
    elif subcategory_key == "social_financing":
        st.header("📊 社会融资规模")
        
        if df_sf_f.empty:
            st.warning("暂无社会融资数据")
        else:
            tab1, tab2 = st.tabs(["趋势图表", "原始数据"])
            
            with tab1:
                fig_inc, fig_cum, fig_stk = plot_sf_charts(df_sf_f)
                if fig_inc:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("当月新增")
                        st.plotly_chart(fig_inc, use_container_width=True)
                        st.subheader("累计值")
                        st.plotly_chart(fig_cum, use_container_width=True)
                    with col2:
                        st.subheader("存量期末值")
                        st.plotly_chart(fig_stk, use_container_width=True)
            
            with tab2:
                st.dataframe(df_sf_f.sort_values('month', ascending=False), use_container_width=True)

# --- INDEX DATA ---
elif category_config["key"] == "index":
    # Import index data modules
    from index_data_loader import (
        load_index_basic, get_indices_with_weight_data,
        get_constituent_count_per_date, get_available_trade_dates,
        get_constituents_for_date
    )
    from index_charts import plot_constituent_count_over_time
    
    # Load index data
    with st.spinner('加载指数数据...'):
        df_indices = load_index_basic()
        indices_with_weight = get_indices_with_weight_data()
    
    if df_indices.empty:
        st.error("无法加载指数数据，请检查数据库连接")
        st.stop()
    
    # --- Index List Sub-category ---
    if subcategory_key == "index_list":
        st.header("📋 指数列表")
        
        # Filters in sidebar
        st.sidebar.subheader("🔍 筛选条件")
        markets = ['全部'] + sorted(df_indices['market'].dropna().unique().tolist())
        publishers = ['全部'] + sorted(df_indices['publisher'].dropna().unique().tolist())
        
        sel_market = st.sidebar.selectbox("市场", markets)
        sel_publisher = st.sidebar.selectbox("发布商", publishers)
        
        df_filtered = df_indices.copy()
        if sel_market != '全部':
            df_filtered = df_filtered[df_filtered['market'] == sel_market]
        if sel_publisher != '全部':
            df_filtered = df_filtered[df_filtered['publisher'] == sel_publisher]
        
        df_filtered['has_weight'] = df_filtered['ts_code'].isin(indices_with_weight)
        
        st.markdown(f"**共 {len(df_filtered)} 个指数，其中 {df_filtered['has_weight'].sum()} 个有成分股权重数据**")
        
        display_cols = ['ts_code', 'name', 'market', 'publisher', 'index_type', 'category',
                        'base_date', 'base_point', 'list_date', 'has_weight']
        
        st.dataframe(
            df_filtered[display_cols],
            use_container_width=True,
            height=600,
            column_config={
                "ts_code": "代码",
                "name": "名称",
                "market": "市场",
                "publisher": "发布商",
                "index_type": "类型",
                "category": "类别",
                "base_date": "基准日期",
                "base_point": st.column_config.NumberColumn("基点", format="%.2f"),
                "list_date": "上市日期",
                "has_weight": st.column_config.CheckboxColumn("有权重数据")
            }
        )
    
    # --- Index Details Sub-category ---
    elif subcategory_key == "index_details":
        st.header("🔬 指数成分股详情")
        
        if not indices_with_weight:
            st.warning("数据库中暂无指数权重数据")
            st.stop()
        
        # Index selection
        selected_index = st.selectbox(
            "选择指数",
            indices_with_weight,
            format_func=lambda x: f"{x} - {df_indices[df_indices['ts_code'] == x]['name'].values[0] if len(df_indices[df_indices['ts_code'] == x]) > 0 else x}"
        )
        
        if selected_index:
            # Show index basic info
            idx_info = df_indices[df_indices['ts_code'] == selected_index]
            if not idx_info.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("指数代码", selected_index)
                with col2:
                    st.metric("名称", idx_info['name'].values[0])
                with col3:
                    st.metric("市场", idx_info['market'].values[0])
                with col4:
                    st.metric("基点", idx_info['base_point'].values[0])
            
            st.divider()
            
            tab1, tab2 = st.tabs(["📈 成分股数量趋势", "📋 成分股明细"])
            
            with tab1:
                st.subheader("成分股数量随时间变化")
                st.caption("可用于发现数据缺失日期（成分股数量突然下降）")
                
                df_counts = get_constituent_count_per_date(selected_index)
                if not df_counts.empty:
                    fig = plot_constituent_count_over_time(df_counts)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("覆盖交易日数", len(df_counts))
                    with col2:
                        st.metric("平均成分股数", f"{df_counts['constituent_count'].mean():.0f}")
                    with col3:
                        st.metric("最小/最大", f"{df_counts['constituent_count'].min()} / {df_counts['constituent_count'].max()}")
            
            with tab2:
                trade_dates = get_available_trade_dates(selected_index)
                if trade_dates:
                    selected_date = st.selectbox("选择交易日期", trade_dates)
                    
                    if selected_date:
                        df_cons = get_constituents_for_date(selected_index, selected_date)
                        if not df_cons.empty:
                            st.markdown(f"**{selected_date} 共 {len(df_cons)} 只成分股**")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.dataframe(
                                    df_cons,
                                    use_container_width=True,
                                    height=400,
                                    column_config={
                                        "con_code": "成分股代码",
                                        "weight": st.column_config.NumberColumn("权重 (%)", format="%.4f")
                                    }
                                )
                            with col2:
                                st.markdown("**权重分布 (Top 10)**")
                                top10 = df_cons.head(10)
                                st.bar_chart(top10.set_index('con_code')['weight'])
                else:
                    st.info("该指数暂无交易日期数据")

# Sidebar footer
st.sidebar.divider()
st.sidebar.caption("📊 Tushare Data Dashboard v1.1")
st.sidebar.caption("数据来源: Tushare Pro")
