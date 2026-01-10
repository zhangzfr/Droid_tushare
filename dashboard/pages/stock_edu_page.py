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
    # 加载基本信息
    with st.spinner('正在加载A股数据...'):
        df_basic = load_stock_basic()
    
    if df_basic.empty:
        st.error("无法加载股票基本信息，请检查数据库连接。")
        st.stop()
    
    # 获取名称映射
    name_map = get_stock_name_map(df_basic)
    
    # 只保留正常上市的股票供选择
    listed_stocks = df_basic[df_basic['list_status'] == 'L']['ts_code'].tolist()
    
    # 计算日期默认值
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- 第1层：认识A股 ---
    if subcategory_key == "stock_overview":
        render_header("第1层：认识A股市场", "market")
        
        # 教育内容
        with st.expander("📘 相关知识：什么是A股市场？"):
            st.markdown(textwrap.dedent("""
            ### 📚 什么是A股市场？
            
            **A股**是指在中国境内上市、以人民币计价交易的股票。主要交易场所：
            
            - **上海证券交易所 (SSE)**：主板、科创板
            - **深圳证券交易所 (SZSE)**：主板、创业板
            - **北京证券交易所 (BSE)**：北交所
            
            **板块分类**：
            - **主板**：成熟大型企业，盈利要求较高
            - **创业板**：成长型创新企业
            - **科创板**：科技创新企业，注册制
            """))
        
        st.divider()
        
        # 获取市场统计
        summary = get_market_summary(df_basic)
        
        # 指标卡
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("上市公司总数", f"{summary.get('total', 0):,}")
        col2.metric("正常上市", f"{summary.get('listed', 0):,}")
        col3.metric("已退市", f"{summary.get('delisted', 0):,}")
        col4.metric("暂停上市", f"{summary.get('suspended', 0):,}")
        
        st.divider()
        
        # 布局
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**筛选**")
            show_listed_only = st.checkbox("仅显示上市中", value=True)
        
        df_display = df_basic.copy()
        if show_listed_only:
            df_display = df_display[df_display['list_status'] == 'L']
        
        with right_col:
            tab1, tab2, tab3, tab4 = st.tabs(["📊 板块分布", "🏭 行业分布", "🗺️ 地域分布", "📋 股票列表"])
            
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
                        "ts_code": "股票代码",
                        "name": "股票名称",
                        "industry": "所属行业",
                        "market": "板块",
                        "area": "地域",
                        "list_date": "上市日期"
                    }
                )
        
        # 思考题
        with st.expander("🤔 思考题"):
            st.markdown(textwrap.dedent("""
            1. 为什么中国要设立多个不同的股票板块（主板、创业板、科创板）？
            2. 从行业分布来看，A股市场的结构有什么特点？
            3. 地域分布与经济发展水平有什么关系？
            """))
    
    # --- 第2层：理解价格 ---
    elif subcategory_key == "stock_price":
        render_header("第2层：理解股票价格", "chart")
        
        # 教育内容
        with st.expander("📘 相关知识：股票价格概念"):
            st.markdown(textwrap.dedent("""
            ### 📈 股票价格的基本概念
            
            **K线图（蜡烛图）**是展示价格走势的经典方式：
            - **开盘价 (Open)**：当日第一笔交易价格
            - **收盘价 (Close)**：当日最后一笔交易价格
            - **最高价 (High)**：当日最高成交价
            - **最低价 (Low)**：当日最低成交价
            
            **收益率**衡量投资回报：
            - 简单收益率：(P_t - P_{t-1}) / P_{t-1}
            - 对数收益率：ln(P_t / P_{t-1})
            
            **波动率**反映价格变化的剧烈程度，是衡量风险的重要指标。
            """))
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            start_date = st.date_input("开始", default_start.date(), key="stock_price_start")
            end_date = st.date_input("结束", default_end.date(), key="stock_price_end")
            
            st.markdown("**选择股票**")
            # 筛选行业 - checkboxes
            industries = sorted(df_basic[df_basic['list_status'] == 'L']['industry'].dropna().unique().tolist())
            
            st.markdown("*行业筛选*")
            sel_industry = []
            # Group by first character for organization
            for ind in industries[:20]:  # Limit display
                if st.checkbox(ind, value=False, key=f"stock_price_ind_{ind}"):
                    sel_industry.append(ind)
            
            if sel_industry:
                available = df_basic[(df_basic['list_status'] == 'L') & (df_basic['industry'].isin(sel_industry))]['ts_code'].tolist()
            else:
                available = listed_stocks
            
            # 默认选择
            defaults = [c for c in DEFAULT_STOCKS if c in available][:4]
            sel_codes = st.multiselect("股票", available, default=defaults, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_price_codes")
        
        if not sel_codes:
            st.info("请选择至少一只股票进行分析。")
        else:
            with st.spinner('正在加载行情数据...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_stock_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("所选股票在该日期范围内无行情数据。")
            else:
                # 计算收益率
                df_returns = calculate_returns(df_daily, 'close', 'simple')
                df_stats = calculate_annualized_stats_by_stock(df_daily)
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 K线图", "📈 价格走势", "📉 收益分布", "📋 原始数据"])
                    
                    with tab1:
                        sel_kline = st.selectbox("选择股票查看K线", sel_codes, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_kline_select")
                        fig_kline = plot_candlestick(df_daily, sel_kline, name_map)
                        if fig_kline:
                            st.plotly_chart(fig_kline, use_container_width=True, key="stock_kline")
                            st.caption("Source: stock_daily")
                    
                    with tab2:
                        normalize = st.toggle("归一化价格 (首日=100)", value=True, key="stock_normalize")
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
                                "ts_code": "代码",
                                "trade_date": "日期",
                                "pct_chg": st.column_config.NumberColumn("涨跌幅%", format="%.2f"),
                                "vol": st.column_config.NumberColumn("成交量", format="%.0f"),
                                "amount": st.column_config.NumberColumn("成交额", format="%.0f")
                            }
                        )
                
                # 思考题
                with st.expander("🤔 思考题"):
                    st.markdown(textwrap.dedent("""
                    1. 为什么A股市场中红色代表上涨、绿色代表下跌？与西方市场有何不同？
                    2. 高波动率的股票一定是不好的投资吗？
                    3. 为什么要用归一化价格来比较不同股票的走势？
                    """))
    
    # --- 第3层：分析估值 ---
    elif subcategory_key == "stock_valuation":
        render_header("第3层：分析估值指标", "valuation")
        
        # 教育内容
        with st.expander("📘 相关知识：核心估值指标"):
            st.markdown(textwrap.dedent("""
            ### 💰 核心估值指标
            
            **市盈率 (PE - Price to Earnings)**
            - 公式：股价 / 每股收益 = 总市值 / 净利润
            - 含义：投资者愿意为每1元利润支付多少钱
            - PE高可能意味着高成长预期，也可能是高估
            
            **市净率 (PB - Price to Book)**
            - 公式：股价 / 每股净资产 = 总市值 / 净资产
            - 适用于重资产行业（银行、地产）
            - PB<1 可能意味着被低估
            
            **换手率 (Turnover Rate)**
            - 公式：成交量 / 流通股本 × 100%
            - 反映股票活跃度和市场情绪
            """))
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            start_date = st.date_input("开始", default_start.date(), key="stock_val_start")
            end_date = st.date_input("结束", default_end.date(), key="stock_val_end")
            
            st.markdown("**选择股票**")
            defaults = [c for c in DEFAULT_STOCKS if c in listed_stocks][:5]
            sel_codes = st.multiselect("股票", listed_stocks, default=defaults, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_val_codes")
        
        if not sel_codes:
            st.info("请选择至少一只股票进行估值分析。")
        else:
            with st.spinner('正在加载估值数据...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_valuation = load_daily_basic(sel_codes, start_str, end_str)
            
            if df_valuation.empty:
                st.warning("所选股票在该日期范围内无估值数据。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 PE走势", "📊 PB走势", "📉 估值分布", "📋 数据表"])
                    
                    with tab1:
                        fig_pe = plot_pe_timeseries(df_valuation, sel_codes, name_map)
                        if fig_pe:
                            st.plotly_chart(fig_pe, use_container_width=True, key="stock_pe_line")
                            st.caption("Source: daily_basic")
                        
                        st.caption("PE-TTM：滚动12个月净利润计算的市盈率，更能反映最新盈利状况。")
                    
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
                                "ts_code": "代码",
                                "trade_date": "日期",
                                "close": st.column_config.NumberColumn("收盘价", format="%.2f"),
                                "pe_ttm": st.column_config.NumberColumn("PE-TTM", format="%.2f"),
                                "pb": st.column_config.NumberColumn("PB", format="%.2f"),
                                "turnover_rate": st.column_config.NumberColumn("换手率%", format="%.2f"),
                                "total_mv_yi": st.column_config.NumberColumn("总市值(亿)", format="%.2f")
                            }
                        )
                
                # 思考题
                with st.expander("🤔 思考题"):
                    st.markdown(textwrap.dedent("""
                    1. 茅台的PE为什么可以长期高于银行股？这合理吗？
                    2. 为什么银行股的PB经常低于1？
                    3. 高换手率是好事还是坏事？对于不同类型投资者意义不同吗？
                    """))
    
    # --- 第4层：行业选股 ---
    elif subcategory_key == "stock_industry":
        render_header("第4层：行业分析与选股", "industry")
        
        # 教育内容
        with st.expander("📘 相关知识：行业分析框架"):
            st.markdown(textwrap.dedent("""
            ### 🏭 行业分析框架
            
            **为什么要分析行业？**
            - 不同行业有不同的商业周期和估值逻辑
            - 行业轮动是重要的投资策略
            - 分散投资于低相关行业可以降低组合风险
            
            **关键指标**：
            - **行业PE中位数**：反映行业整体估值水平
            - **行业收益率**：衡量行业表现
            - **行业相关性**：用于构建分散组合
            
            **风险-收益分析**：
            - 高收益伴随高风险是普遍规律
            - 夏普比率 = (收益率 - 无风险收益率) / 波动率
            """))
        
        st.divider()
        
        # 筛选
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            adv_start = default_end - timedelta(days=180)  # 半年
            start_date = st.date_input("开始", adv_start.date(), key="stock_ind_start")
            end_date = st.date_input("结束", default_end.date(), key="stock_ind_end")
            
            st.markdown("**行业筛选**")
            all_industries = sorted(df_basic[df_basic['list_status'] == 'L']['industry'].dropna().unique().tolist())
            
            # Checkboxes with defaults
            sel_industries = []
            default_industries = all_industries[:10]
            
            for ind in all_industries[:25]:  # Limit display
                if st.checkbox(ind, value=ind in default_industries, key=f"stock_ind_sel_{ind}"):
                    sel_industries.append(ind)
        
        if not sel_industries:
            st.info("请选择至少一个行业进行分析。")
        else:
            with st.spinner('正在加载行业数据...'):
                # 获取行业内股票
                industry_stocks = df_basic[(df_basic['list_status'] == 'L') & (df_basic['industry'].isin(sel_industries))]['ts_code'].tolist()
                
                # 限制数量
                if len(industry_stocks) > 200:
                    industry_stocks = industry_stocks[:200]
                
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                
                df_daily = load_stock_daily(industry_stocks, start_str, end_str)
                df_valuation = get_latest_valuation(industry_stocks)
            
            with right_col:
                tab1, tab2, tab3, tab4 = st.tabs(["📊 行业估值", "🔥 收益分析", "🔗 相关性", "⚖️ 风险收益"])
                
                with tab1:
                    if not df_valuation.empty:
                        df_industry_val = aggregate_by_industry(df_basic, df_valuation)
                        if not df_industry_val.empty:
                            fig_ind_val = plot_industry_valuation(df_industry_val)
                            if fig_ind_val:
                                st.plotly_chart(fig_ind_val, use_container_width=True, key="stock_ind_val")
                                st.caption("Source: daily_basic, stock_basic")
                            
                            st.subheader("行业估值一览")
                            st.dataframe(df_industry_val, use_container_width=True, hide_index=True)
                    else:
                        st.warning("无法获取估值数据。")
                
                with tab2:
                    if not df_daily.empty:
                        df_ind_daily = calculate_industry_returns(df_daily, df_basic)
                        if not df_ind_daily.empty:
                            fig_heatmap = plot_industry_returns_heatmap(df_ind_daily)
                            if fig_heatmap:
                                st.plotly_chart(fig_heatmap, use_container_width=True, key="stock_ind_ret")
                                st.caption("Source: stock_daily")
                    else:
                        st.warning("无法获取行情数据。")
                
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
                                
                                st.caption("低相关性的行业组合可以有效分散风险。")
                
                with tab4:
                    if not df_daily.empty:
                        df_stats = calculate_annualized_stats_by_stock(df_daily)
                        if not df_stats.empty:
                            # 合并名称
                            df_stats = df_stats.merge(df_basic[['ts_code', 'name', 'industry']], on='ts_code', how='left')
                            
                            fig_rr = plot_risk_return_scatter(df_stats, name_map)
                            if fig_rr:
                                st.plotly_chart(fig_rr, use_container_width=True, key="stock_risk_return")
                                st.caption("Source: stock_daily")
                            
                            st.markdown(textwrap.dedent("""
                            **如何解读风险-收益图：**
                            - **X轴（波动率）**：越靠右风险越高
                            - **Y轴（收益率）**：越靠上收益越高
                            - **理想位置**：左上角（高收益低风险）
                            - **颜色（夏普比率）**：绿色代表更好的风险调整后收益
                            """))
            
            # 思考题
            with st.expander("🤔 思考题"):
                st.markdown(textwrap.dedent("""
                1. 为什么有些行业的PE长期高于其他行业？这与行业特性有何关系？
                2. 如何利用行业相关性构建一个分散化的投资组合？
                3. 高夏普比率的股票一定是好的投资标的吗？有什么局限性？
                4. 宏观经济周期如何影响不同行业的轮动？
                """))
