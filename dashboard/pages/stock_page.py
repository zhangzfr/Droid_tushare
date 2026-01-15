"""
Stock Education Page (A-Share)
=============================
Educational content and visualizations for A-Share market analysis.
"""
import streamlit as st
import textwrap
import pandas as pd
from datetime import datetime, timedelta
from dashboard.components.headers import render_header

# Import Stock Education modules
from dashboard.stock_edu_data_loader import (
    load_stock_basic, load_stock_company, get_market_summary,
    load_stock_daily, load_adj_factor, calculate_adjusted_price,
    calculate_returns, calculate_volatility,
    load_daily_basic, get_latest_valuation,
    aggregate_by_industry, calculate_industry_returns, calculate_industry_correlation,
    calculate_annualized_stats_by_stock, create_price_pivot, normalize_prices,
    get_stock_name_map, DEFAULT_STOCKS
)
from dashboard.stock_edu_charts import (
    plot_market_pie, plot_status_pie, plot_industry_bar, plot_area_bar,
    plot_candlestick, plot_price_lines, plot_return_distribution, plot_volatility_comparison,
    plot_pe_timeseries, plot_pb_timeseries, plot_valuation_boxplot, plot_turnover_scatter,
    plot_market_cap_distribution, plot_industry_valuation, plot_industry_correlation_heatmap,
    plot_risk_return_scatter, plot_industry_returns_heatmap
)

def render_stock_edu_page(subcategory_key):
    """
    Render the Stock Education page based on the selected subcategory.
    """
    # Loading basic information
    with st.spinner('Loading A-Share data...'):
        df_basic = load_stock_basic()
    
    if df_basic.empty:
        st.error("Unable to load stock basic information, please check database connection。")
        st.stop()
    
    # Get name mapping
    name_map = get_stock_name_map(df_basic)
    
    # Keep only normally listed stocks for selection
    listed_stocks = df_basic[df_basic['list_status'] == 'L']['ts_code'].tolist()
    
    # Calculate date defaults
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- Level 1：Understanding A-Share ---
    if subcategory_key == "stock_overview":
        render_header("Level 1：Understanding A-Share市场", "market")
        
        # Educational Content
        with st.expander("📘 Related Knowledge：What is A-Share Market？"):
            st.markdown(textwrap.dedent("""
            ### 📚 What is A-Share Market？
            
            **A-Share**refers to在中国境内上市、traded in RMB,Stock。main trading venues：
            
            - **Shanghai Stock Exchange (SSE)**：主板、科创板
            - **Shenzhen Stock Exchange (SZSE)**：主板、创业板
            - **北京证券交易所 (BSE)**：北交所
            
            **Sector Classification**：
            - **主板**：成熟大型企业，盈利要求较高
            - **创业板**：成长型创新企业
            - **科创板**：Technology创新企业，注册制
            """))
        
        st.divider()
        
        # Get market statistics
        summary = get_market_summary(df_basic)
        
        # Metrics Card
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Listed Companies", f"{summary.get('total', 0):,}")
        col2.metric("Normal Listing", f"{summary.get('listed', 0):,}")
        col3.metric("Delisted", f"{summary.get('delisted', 0):,}")
        col4.metric("Suspended", f"{summary.get('suspended', 0):,}")
        
        st.divider()
        
        # Layout
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Filter**")
            show_listed_only = st.checkbox("Show only listed", value=True)
        
        df_display = df_basic.copy()
        if show_listed_only:
            df_display = df_display[df_display['list_status'] == 'L']
        
        with right_col:
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Sector分布", "🏭 行业分布", "🗺️ Region分布", "📋 Stock列表"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    fig_market = plot_market_pie(summary.get('by_market', {}))
                    if fig_market:
                        st.plotly_chart(fig_market, use_container_width=True, key="stock_market_pie")
                        st.caption("Source: stock_basic")
                with col2:
                    fig_status = plot_status_pie(df_basic)
                    if fig_status:
                        st.plotly_chart(fig_status, use_container_width=True, key="stock_status_pie")
                        st.caption("Source: stock_basic")
            
            with tab2:
                fig_industry = plot_industry_bar(summary.get('by_industry', {}))
                if fig_industry:
                    st.plotly_chart(fig_industry, use_container_width=True, key="stock_industry_bar")
                    st.caption("Source: stock_basic")
            
            with tab3:
                fig_area = plot_area_bar(summary.get('by_area', {}))
                if fig_area:
                    st.plotly_chart(fig_area, use_container_width=True, key="stock_area_bar")
                    st.caption("Source: stock_basic")
            
            with tab4:
                st.dataframe(
                    df_display[['ts_code', 'name', 'industry', 'market', 'area', 'list_date']],
                    use_container_width=True,
                    height=500,
                    column_config={
                        "ts_code": "Stock Code",
                        "name": "Stock Name",
                        "industry": "Industry",
                        "market": "Sector",
                        "area": "Region",
                        "list_date": "Listing Date"
                    }
                )
        
        # Discussion Questions
        with st.expander("🤔 Discussion Questions"):
            st.markdown(textwrap.dedent("""
            1. 为什么中国要设立多个不同的StockSector（主板、创业板、科创板）？
            2. 从行业分布来看，A-Share市场的结构有什么特点？
            3. Region分布与经济发展水平有什么关系？
            """))
    
    # --- 2： ---
    elif subcategory_key == "stock_price":
        render_header("第2层：理解StockPrice", "chart")
        
        # Educational Content
        with st.expander("📘 Related Knowledge：StockPrice概念"):
            st.markdown(textwrap.dedent("""
            ### 📈 Basic Concepts of Stock Prices
            
            **K线图（蜡烛图）**是展示PriceTrend的经典方式：
            - **开盘价 (Open)**：当日第一笔交易Price
            - **Closing Price (Close)**：Last Trade of the DayPrice
            - **最高价 (High)**：当日最高成交价
            - **最低价 (Low)**：当日最低成交价
            
            **Return率**衡量投资回报：
            - Simple Return：(P_t - P_{t-1}) / P_{t-1}
            - Log Return：ln(P_t / P_{t-1})
            
            **波动率**反映PriceChangeIntensity of，是衡量风险的重要指标。
            """))
        
        st.divider()
        
        # Filter
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start", default_start.date(), key="stock_price_start")
            end_date = st.date_input("End", default_end.date(), key="stock_price_end")
            
            st.markdown("**Select Stock**")
            # Filter - checkboxes
            industries = sorted(df_basic[df_basic['list_status'] == 'L']['industry'].dropna().unique().tolist())
            
            st.markdown("*行业Filter*")
            sel_industry = []
            # Group by first character for organization
            for ind in industries[:20]:  # Limit display
                if st.checkbox(ind, value=False, key=f"stock_price_ind_{ind}"):
                    sel_industry.append(ind)
            
            if sel_industry:
                available = df_basic[(df_basic['list_status'] == 'L') & (df_basic['industry'].isin(sel_industry))]['ts_code'].tolist()
            else:
                available = listed_stocks
            
            # Default Selection
            defaults = [c for c in DEFAULT_STOCKS if c in available][:4]
            sel_codes = st.multiselect("Stock", available, default=defaults, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_price_codes")
        
        if not sel_codes:
            st.info("请选择至少一只Stock进行Analysis。")
        else:
            with st.spinner('Loading market data...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_stock_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("SelectedStock在该Date Range内无行情数据。")
            else:
                # Calculate returns
                df_returns = calculate_returns(df_daily, 'close', 'simple')
                df_stats = calculate_annualized_stats_by_stock(df_daily)
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 K线图", "📈 PriceTrend", "📉 Return分布", "📋 原始数据"])
                    
                    with tab1:
                        sel_kline = st.selectbox("Select Stock查看K线", sel_codes, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_kline_select")
                        fig_kline = plot_candlestick(df_daily, sel_kline, name_map)
                        if fig_kline:
                            st.plotly_chart(fig_kline, use_container_width=True, key="stock_kline")
                            st.caption("Source: stock_daily")
                    
                    with tab2:
                        normalize = st.toggle("Normalized Price (First Day=100)", value=True, key="stock_normalize")
                        df_pivot = create_price_pivot(df_daily, 'close')
                        fig_lines = plot_price_lines(df_pivot, normalize=normalize, name_map=name_map)
                        if fig_lines:
                            st.plotly_chart(fig_lines, use_container_width=True, key="stock_price_lines")
                            st.caption("Source: stock_daily")
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_dist = plot_return_distribution(df_returns, name_map=name_map)
                            if fig_dist:
                                st.plotly_chart(fig_dist, use_container_width=True, key="stock_return_dist")
                                st.caption("Source: stock_daily")
                        with col2:
                            fig_vol = plot_volatility_comparison(df_stats, name_map=name_map)
                            if fig_vol:
                                st.plotly_chart(fig_vol, use_container_width=True, key="stock_vol_compare")
                                st.caption("Source: stock_daily")
                    
                    with tab4:
                        st.dataframe(
                            df_daily[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pct_chg', 'vol', 'amount']].sort_values(['ts_code', 'trade_date'], ascending=[True, False]),
                            use_container_width=True,
                            height=500,
                            column_config={
                                "ts_code": "Code",
                                "trade_date": "日期",
                                "pct_chg": st.column_config.NumberColumn("Change %%", format="%.2f"),
                                "vol": st.column_config.NumberColumn("Volume", format="%.0f"),
                                "amount": st.column_config.NumberColumn("Trading Amount", format="%.0f")
                            }
                        )
                
                # Discussion Questions
                with st.expander("🤔 Discussion Questions"):
                    st.markdown(textwrap.dedent("""
                    1. 为什么A-Share市场中红色代表上涨、绿色代表下跌？与西方市场有何不同？
                    2. 高波动率的Stock一定是不好的投资吗？
                    3. 为什么要用Normalized Price来比较不同Stock的Trend？
                    """))
    
    # --- 3： ---
    elif subcategory_key == "stock_valuation":
        render_header("第3层：Analysis估值指标", "valuation")
        
        # Educational Content
        with st.expander("📘 Related Knowledge：Core Valuation Metrics"):
            st.markdown(textwrap.dedent("""
            ### 💰 Core Valuation Metrics
            
            **P/E Ratio (PE - Price to Earnings)**
            - 公式：股价 / 每股Return = Total Market Cap / 净利润
            - Meaning：投资者愿意为每1元利润支付多少钱
            - PEHigh may indicate high growth expectations，也可能是高估
            
            **P/B Ratio (PB - Price to Book)**
            - 公式：股价 / 每股净资产 = Total Market Cap / 净资产
            - 适用于重资产行业（银行、地产）
            - PB<1 May indicate undervaluation
            
            **Turnover Rate (Turnover Rate)**
            - 公式：Volume / 流通股本 × 100%
            - 反映Stock活跃度和市场情绪
            """))
        
        st.divider()
        
        # Filter
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start", default_start.date(), key="stock_val_start")
            end_date = st.date_input("End", default_end.date(), key="stock_val_end")
            
            st.markdown("**Select Stock**")
            defaults = [c for c in DEFAULT_STOCKS if c in listed_stocks][:5]
            sel_codes = st.multiselect("Stock", listed_stocks, default=defaults, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_val_codes")
        
        if not sel_codes:
            st.info("请选择至少一只StockPerform ValuationAnalysis。")
        else:
            with st.spinner('Loading valuation data...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_valuation = load_daily_basic(sel_codes, start_str, end_str)
            
            if df_valuation.empty:
                st.warning("SelectedStock在该Date RangeNo Valuation Data Within。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 PETrend", "📊 PBTrend", "📉 估值分布", "📋 数据表"])
                    
                    with tab1:
                        fig_pe = plot_pe_timeseries(df_valuation, sel_codes, name_map)
                        if fig_pe:
                            st.plotly_chart(fig_pe, use_container_width=True, key="stock_pe_line")
                            st.caption("Source: daily_basic")
                        
                        st.caption("PE-TTM：滚动12个月净利润Calculate的P/E Ratio，更能反映最新盈利状况。")
                    
                    with tab2:
                        fig_pb = plot_pb_timeseries(df_valuation, sel_codes, name_map)
                        if fig_pb:
                            st.plotly_chart(fig_pb, use_container_width=True, key="stock_pb_line")
                            st.caption("Source: daily_basic")
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_pe_box = plot_valuation_boxplot(df_valuation, 'pe_ttm', name_map)
                            if fig_pe_box:
                                st.plotly_chart(fig_pe_box, use_container_width=True, key="stock_pe_box")
                                st.caption("Source: daily_basic")
                        with col2:
                            fig_pb_box = plot_valuation_boxplot(df_valuation, 'pb', name_map)
                            if fig_pb_box:
                                st.plotly_chart(fig_pb_box, use_container_width=True, key="stock_pb_box")
                                st.caption("Source: daily_basic")
                    
                    with tab4:
                        st.dataframe(
                            df_valuation[['ts_code', 'trade_date', 'close', 'pe_ttm', 'pb', 'turnover_rate', 'total_mv_yi']].sort_values(['ts_code', 'trade_date'], ascending=[True, False]),
                            use_container_width=True,
                            height=500,
                            column_config={
                                "ts_code": "Code",
                                "trade_date": "日期",
                                "close": st.column_config.NumberColumn("Closing Price", format="%.2f"),
                                "pe_ttm": st.column_config.NumberColumn("PE-TTM", format="%.2f"),
                                "pb": st.column_config.NumberColumn("PB", format="%.2f"),
                                "turnover_rate": st.column_config.NumberColumn("Turnover Rate%", format="%.2f"),
                                "total_mv_yi": st.column_config.NumberColumn("Total Market Cap(亿)", format="%.2f")
                            }
                        )
                
                # Discussion Questions
                with st.expander("🤔 Discussion Questions"):
                    st.markdown(textwrap.dedent("""
                    1. 茅台的PE为什么可以长期高于银行股？这合理吗？
                    2. 为什么银行股的PB经常低于1？
                    3. 高Turnover Rate是好事还是坏事？对于不同类型投资者意义不同吗？
                    """))
    
    # --- 4： ---
    elif subcategory_key == "stock_industry":
        render_header("第4层：行业Analysis与选股", "industry")
        
        # Educational Content
        with st.expander("📘 Related Knowledge：Industry Analysis Framework"):
            st.markdown(textwrap.dedent("""
            ### 🏭 Industry Analysis Framework
            
            **Why Analyze Industries？**
            - Different industries have different business cycles and valuation logic
            - Industry rotation is an important investment strategy
            - Diversification into low-correlation industries can reduce portfolio risk
            
            **Key Indicators**：
            - **行业PE中位数**：反映行业整体估值水平
            - **Industry Return**：衡量行业表现
            - **行业相关性**：用于构建分散组合
            
            **风险-ReturnAnalysis**：
            - High return comes with high risk is a general rule
            - 夏普比率 = (Return率 - 无风险Return率) / 波动率
            """))
        
        st.divider()
        
        # Filter
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            adv_start = default_end - timedelta(days=180)  # Half Year
            start_date = st.date_input("Start", adv_start.date(), key="stock_ind_start")
            end_date = st.date_input("End", default_end.date(), key="stock_ind_end")
            
            st.markdown("**行业Filter**")
            all_industries = sorted(df_basic[df_basic['list_status'] == 'L']['industry'].dropna().unique().tolist())
            
            # Checkboxes with defaults
            sel_industries = []
            default_industries = all_industries[:10]
            
            for ind in all_industries[:25]:  # Limit display
                if st.checkbox(ind, value=ind in default_industries, key=f"stock_ind_sel_{ind}"):
                    sel_industries.append(ind)
        
        if not sel_industries:
            st.info("Please select at least one industry for analysis。")
        else:
            with st.spinner('Loading industry data...'):
                # Stock
                industry_stocks = df_basic[(df_basic['list_status'] == 'L') & (df_basic['industry'].isin(sel_industries))]['ts_code'].tolist()
                
                # Limit quantity
                if len(industry_stocks) > 200:
                    industry_stocks = industry_stocks[:200]
                
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                
                df_daily = load_stock_daily(industry_stocks, start_str, end_str)
                df_valuation = get_latest_valuation(industry_stocks)
            
            with right_col:
                tab1, tab2, tab3, tab4 = st.tabs(["📊 行业估值", "🔥 ReturnAnalysis", "🔗 相关性", "⚖️ 风险Return"])
                
                with tab1:
                    if not df_valuation.empty:
                        df_industry_val = aggregate_by_industry(df_basic, df_valuation)
                        if not df_industry_val.empty:
                            fig_ind_val = plot_industry_valuation(df_industry_val)
                            if fig_ind_val:
                                st.plotly_chart(fig_ind_val, use_container_width=True, key="stock_ind_val")
                                st.caption("Source: daily_basic, stock_basic")
                            
                            st.subheader("Industry Valuation Overview")
                            st.dataframe(df_industry_val, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Unable to fetch valuation data。")
                
                with tab2:
                    if not df_daily.empty:
                        df_ind_daily = calculate_industry_returns(df_daily, df_basic)
                        if not df_ind_daily.empty:
                            fig_heatmap = plot_industry_returns_heatmap(df_ind_daily)
                            if fig_heatmap:
                                st.plotly_chart(fig_heatmap, use_container_width=True, key="stock_ind_ret")
                                st.caption("Source: stock_daily")
                    else:
                        st.warning("Unable to fetch market data。")
                
                with tab3:
                    if not df_daily.empty:
                        df_ind_daily = calculate_industry_returns(df_daily, df_basic)
                        if not df_ind_daily.empty:
                            df_corr = calculate_industry_correlation(df_ind_daily)
                            if not df_corr.empty:
                                fig_corr = plot_industry_correlation_heatmap(df_corr)
                                if fig_corr:
                                    st.plotly_chart(fig_corr, use_container_width=True, key="stock_ind_corr")
                                    st.caption("Source: stock_daily")
                                
                                st.caption("Low-correlation industry combinations can effectively diversify risk。")
                
                with tab4:
                    if not df_daily.empty:
                        df_stats = calculate_annualized_stats_by_stock(df_daily)
                        if not df_stats.empty:
                            # Merge names
                            df_stats = df_stats.merge(df_basic[['ts_code', 'name', 'industry']], on='ts_code', how='left')
                            
                            fig_rr = plot_risk_return_scatter(df_stats, name_map)
                            if fig_rr:
                                st.plotly_chart(fig_rr, use_container_width=True, key="stock_risk_return")
                                st.caption("Source: stock_daily")
                            
                            st.markdown(textwrap.dedent("""
                            **How to Interpret Risk-Return图：**
                            - **X轴（波动率）**：Higher Risk to the Right
                            - **Y轴（Return率）**：越靠上Return越高
                            - **理想位置**：Upper Left（高Return低风险）
                            - **颜色（夏普比率）**：Green Means Better Risk-adjusted Return
                            """))
            
            # Discussion Questions
            with st.expander("🤔 Discussion Questions"):
                st.markdown(textwrap.dedent("""
                1. Why Some IndustriesPE长期高于其他行业？这与行业特性有何关系？
                2. How to use industry correlation to build diversified portfolio？
                3. High Sharpe RatioStock一定是好的投资标的吗？有什么局限性？
                4. How economic cycles affect different industry rotations？
                """))
