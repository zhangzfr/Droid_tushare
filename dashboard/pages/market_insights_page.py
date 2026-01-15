import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import textwrap
from dashboard.components.headers import render_header

# Import Market Insights modules
from dashboard.market_insights_loader import (
    load_daily_info, get_available_market_codes, calculate_pe_percentile,
    load_index_global, get_available_global_indices, calculate_global_correlation,
    calculate_index_returns, create_normalized_pivot, calculate_market_sentiment,
    load_sz_daily_info, get_index_display_name,
    GLOBAL_INDICES, MARKET_CODES, SZ_DAILY_CODES
)
from dashboard.market_insights_charts import (
    plot_pe_trend, plot_pe_percentile_gauge, plot_pe_comparison_bar,
    plot_amount_trend, plot_turnover_heatmap, plot_volume_price_scatter,
    plot_global_indices_comparison, plot_global_indices_raw, plot_global_volume, plot_global_volume_trend,
    plot_global_correlation_heatmap,
    plot_index_returns_bar, plot_risk_return_global, plot_market_mv_trend,
    plot_trading_amount_trend, plot_sh_sz_comparison, plot_sector_heatmap,
    plot_risk_warning_box, plot_liquidity_score_gauge, plot_market_turnover_scatter
)

def render_market_insights_page(subcategory_key):
    """
    Render the Market Insights page based on the selected subcategory.
    """
    # 日期默认值
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- 市场估值 ---
    if subcategory_key == "mkt_valuation":
        render_header("市场估值分析", "gauge")
        
        with st.expander("📘 相关知识：什么是市场估值？"):
            st.markdown(textwrap.dedent("""
            ### 📊 什么是市场估值？
            
            **市盈率 (PE)** 是衡量整个市场估值水平的核心指标：
            - PE = 总市值 / 总净利润
            - PE偏高可能意味着市场估值过热
            - PE偏低可能意味着市场被低估
            
            **PE历史分位数**：当前PE在历史中处于什么位置
            - 低于30%分位：历史低估区域
            - 高于70%分位：历史高估区域
            """))
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            hist_years = st.radio("历史数据", [1, 3, 5, 10], index=2, format_func=lambda x: f"{x}年", key="mkt_pe_years", horizontal=True)
            hist_start = default_end - timedelta(days=365*hist_years)
            
            st.markdown("**板块选择**")
            # 主要板块 - Checkboxes for multi-select
            main_codes = ['SH_A', 'SZ_GEM', 'SH_STAR', 'SZ_MAIN']
            available_codes = [c for c, n in get_available_market_codes() if c in main_codes]
            if not available_codes:
                available_codes = ['SH_A', 'SZ_A']
            
            # Checkboxes for multi-selection
            sel_codes = []
            for code in available_codes:
                if st.checkbox(MARKET_CODES.get(code, code), value=code == 'SH_A', key=f"mkt_pe_cb_{code}"):
                    sel_codes.append(code)
        
        if not sel_codes:
            st.info("请选择至少一个板块进行分析。")
        else:
            with st.spinner('正在加载市场统计数据...'):
                start_str = hist_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                df_info = load_daily_info(start_str, end_str, sel_codes)
            
            if df_info.empty:
                st.warning("无法获取市场统计数据，请检查数据库是否已加载 daily_info 表。")
            else:
                with right_col:
                    tab1, tab2, tab3 = st.tabs(["📈 PE走势", "📊 PE分位", "📋 板块对比"])
                    
                    with tab1:
                        fig_pe = plot_pe_trend(df_info, sel_codes)
                        if fig_pe:
                            st.plotly_chart(fig_pe, use_container_width=True, key="mkt_pe_trend")
                            st.caption("Source: daily_info")
                        
                        st.caption("PE走势反映市场整体估值变化，可用于判断市场周期位置。")
                    
                    with tab2:
                        # 每个板块的PE分位数
                        cols = st.columns(min(len(sel_codes), 4))
                        for i, code in enumerate(sel_codes):
                            pe_stats = calculate_pe_percentile(df_info, code)
                            if pe_stats:
                                with cols[i % len(cols)]:
                                    fig_gauge = plot_pe_percentile_gauge(
                                        pe_stats['percentile'],
                                        pe_stats['current_pe'],
                                        title=MARKET_CODES.get(code, code)
                                    )
                                    if fig_gauge:
                                        st.plotly_chart(fig_gauge, use_container_width=True, key=f"mkt_pe_gauge_{i}_{code}")
                                        st.caption("Source: daily_info")
                        
                        st.markdown(textwrap.dedent("""
                        **如何解读PE分位数：**
                        - 🟢 **< 30%**：历史低估区域，可能是较好的买入时机
                        - 🟡 **30%-70%**：估值适中
                        - 🔴 **> 70%**：历史高估区域，需谨慎
                        """))
                    
                    with tab3:
                        fig_bar = plot_pe_comparison_bar(df_info)
                        if fig_bar:
                            st.plotly_chart(fig_bar, use_container_width=True, key="mkt_pe_bar")
                            st.caption("Source: daily_info")
                        
                        # 市值走势
                        fig_mv = plot_market_mv_trend(df_info, sel_codes)
                        if fig_mv:
                            st.plotly_chart(fig_mv, use_container_width=True, key="mkt_mv_trend")
                            st.caption("Source: daily_info")
    
    # --- 市场情绪 ---
    elif subcategory_key == "mkt_sentiment":
        render_header("市场情绪分析", "pulse")
        
        with st.expander("📘 相关知识：市场情绪指标"):
            st.markdown(textwrap.dedent("""
            ### 📈 市场情绪指标
            
            **成交额**反映市场活跃程度：
            - 放量上涨：多方力量强劲
            - 缩量下跌：空方力量衰竭，可能见底
            - 天量见天价：警惕风险
            
            **换手率**反映市场交易频率：
            - 高换手率：市场情绪高涨或有大资金进出
            - 低换手率：市场冷淡
            """))
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            date_mode = st.radio("选择方式", ["预设", "自定义"], index=0, key="mkt_sent_date_mode", horizontal=True)
            
            if date_mode == "预设":
                sent_years = st.radio("时间跨度", [1, 2, 3, 5, 10], index=1, format_func=lambda x: f"{x}年", key="mkt_sent_years", horizontal=True)
                sent_start = default_end - timedelta(days=365*sent_years)
            else:
                from datetime import date
                col1, col2 = st.columns(2)
                with col1:
                    sent_start = st.date_input("开始日期", value=default_end - timedelta(days=365*2), key="mkt_sent_start")
                with col2:
                    sent_end_input = st.date_input("结束日期", value=default_end, key="mkt_sent_end_input")
                default_end = sent_end_input
            
            st.markdown("**板块选择**")
            
            # daily_info 板块 (亿元)
            st.markdown("<small>*上海/深交所数据*</small>", unsafe_allow_html=True)
            daily_codes = ['SH_MARKET', 'SZ_MARKET', 'SH_A', 'SZ_GEM', 'SH_STAR', 'SH_FUND']
            sel_daily_codes = []
            for code in daily_codes:
                if st.checkbox(MARKET_CODES.get(code, code), value=code in ['SH_A', 'SZ_GEM'], key=f"mkt_sent_daily_{code}"):
                    sel_daily_codes.append(code)
            
            # sz_daily_info 板块 (需要转换)
            st.markdown("<small>*深交所分类*</small>", unsafe_allow_html=True)
            sz_codes = ['股票', '创业板A股', '主板A股', '债券', '基金']
            sel_sz_codes = []
            for code in sz_codes:
                if st.checkbox(SZ_DAILY_CODES.get(code, code), value=False, key=f"mkt_sent_sz_{code}"):
                    sel_sz_codes.append(code)
        
        if not sel_daily_codes and not sel_sz_codes:
            st.info("请选择至少一个板块进行分析。")
        else:
            with st.spinner('正在加载数据...'):
                start_str = sent_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                
                # 加载 daily_info 数据
                df_daily = pd.DataFrame()
                if sel_daily_codes:
                    df_daily = load_daily_info(start_str, end_str, sel_daily_codes)
                    if not df_daily.empty:
                        df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount', 'pe', 'tr']].copy()
                        df_daily['source'] = 'daily_info'
                
                # 加载 sz_daily_info 数据
                df_sz = pd.DataFrame()
                if sel_sz_codes:
                    df_sz = load_sz_daily_info(start_str, end_str, sel_sz_codes)
                    if not df_sz.empty:
                        df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount']].copy()
                        df_sz['pe'] = None
                        df_sz['tr'] = None
                        df_sz['source'] = 'sz_daily_info'
                
                # 合并数据
                if not df_daily.empty and not df_sz.empty:
                    df_info = pd.concat([df_daily, df_sz], ignore_index=True)
                elif not df_daily.empty:
                    df_info = df_daily
                elif not df_sz.empty:
                    df_info = df_sz
                else:
                    df_info = pd.DataFrame()
            
            if df_info.empty:
                st.warning("无法获取市场统计数据。")
            else:
                # Get all selected codes (combined)
                all_sel_codes = sel_daily_codes + sel_sz_codes
                
                with right_col:
                    tab1, tab2, tab3 = st.tabs(["📊 成交额走势", "🔥 换手率热力图", "📈 量价关系"])
                    
                    with tab1:
                        # 绘制所有选中板块的成交额走势
                        
                        fig_amount = px.line(
                            df_info.sort_values('trade_date'),
                            x='trade_date', 
                            y='amount',
                            color='market_name',
                            title='成交额走势对比 (单位: 亿元)'
                        )
                        fig_amount.update_layout(
                            xaxis_title='日期',
                            yaxis_title='成交额 (亿元)',
                            legend_title='板块',
                            height=500
                        )
                        st.plotly_chart(fig_amount, use_container_width=True, key="mkt_sent_amount_combined")
                        st.caption("Source: daily_info, sz_daily_info")
                        st.caption("成交额突破均线往往预示着趋势变化。")
                    
                    with tab2:
                        # 只显示有换手率数据的板块
                        df_with_tr = df_info[df_info['tr'].notna()]
                        if df_with_tr.empty:
                            st.info("选中的板块没有换手率数据。")
                        else:
                            for sel_code in sel_daily_codes:
                                fig_tr = plot_turnover_heatmap(df_with_tr, sel_code)
                                if fig_tr:
                                    st.plotly_chart(fig_tr, use_container_width=True, key=f"mkt_tr_heatmap_{sel_code}")
                                    st.caption(f"Source: daily_info ({MARKET_CODES.get(sel_code, sel_code)})")
                        
                        st.caption("通过月度换手率热力图观察市场情绪的季节性规律。")
                    
                    with tab3:
                        # 只显示有PE数据的板块
                        df_with_pe = df_info[df_info['pe'].notna()]
                        if df_with_pe.empty:
                            st.info("选中的板块没有PE数据。")
                        else:
                            for sel_code in sel_daily_codes:
                                fig_vp = plot_volume_price_scatter(df_with_pe, sel_code)
                                if fig_vp:
                                    st.plotly_chart(fig_vp, use_container_width=True, key=f"mkt_vp_scatter_{sel_code}")
                                    st.caption(f"Source: daily_info ({MARKET_CODES.get(sel_code, sel_code)})")
                        
                        st.markdown(textwrap.dedent("""
                        **量价关系洞察：**
                        - 成交额与PE变化的关系反映资金推动效果
                        - 放量时PE上涨幅度可观察市场效率
                        """))
    
    # --- 全球比较 ---
    elif subcategory_key == "mkt_global":
        render_header("全球市场比较", "globe")
        
        with st.expander("📘 相关知识：全球市场"):
            st.markdown(textwrap.dedent("""
            ### 🌍 为什么要关注全球市场？
            
            **全球化联动**：
            - 美股对A股有一定领先作用
            - 风险事件往往跨市场传导
            - 相关性分析有助于全球资产配置
            
            **主要指数**：
            - 🇨🇳 富时A50、恒生指数
            - 🇺🇸 道琼斯、标普500、纳斯达克
            - 🇯🇵 日经225 | 🇩🇪 德国DAX | 🇬🇧 富时100
            """))
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            global_years = st.radio("时间跨度", [1, 2, 3, 5], index=1, format_func=lambda x: f"{x}年", key="mkt_global_years", horizontal=True)
            global_start = default_end - timedelta(days=365*global_years)
            
            st.markdown("**指数选择**")
            available_indices = get_available_global_indices()
            
            # 使用checkbox实现多选
            
            # 分组展示
            st.markdown("<small>*亚太地区*</small>", unsafe_allow_html=True)
            asia_indices = ['XIN9', 'HSI', 'HKTECH', 'N225', 'KS11', 'TWII', 'AS51', 'SENSEX']
            sel_asia = []
            for idx in asia_indices:
                if idx in available_indices:
                    if st.checkbox(get_index_display_name(idx), value=idx in ['XIN9', 'HSI', 'N225'], key=f"cb_{idx}"):
                        sel_asia.append(idx)
            
            st.markdown("<small>*欧美地区*</small>", unsafe_allow_html=True)
            west_indices = ['DJI', 'SPX', 'IXIC', 'RUT', 'FTSE', 'GDAXI', 'FCHI', 'CSX5P', 'SPTSX']
            sel_west = []
            for idx in west_indices:
                if idx in available_indices:
                    if st.checkbox(get_index_display_name(idx), value=idx in ['DJI', 'SPX', 'IXIC'], key=f"cb_{idx}"):
                        sel_west.append(idx)
            
            st.markdown("<small>*新兴市场*</small>", unsafe_allow_html=True)
            em_indices = ['IBOVESPA', 'RTS', 'CKLSE', 'HKAH']
            sel_em = []
            for idx in em_indices:
                if idx in available_indices:
                    if st.checkbox(get_index_display_name(idx), value=False, key=f"cb_{idx}"):
                        sel_em.append(idx)
            
            sel_indices = sel_asia + sel_west + sel_em
        
        if not sel_indices:
            st.info("请选择至少一个指数进行分析。")
        else:
            with st.spinner('正在加载全球指数数据...'):
                start_str = global_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                df_global = load_index_global(start_str, end_str, sel_indices)
            
            if df_global.empty:
                st.warning("无法获取全球指数数据，请检查数据库是否已加载 index_global 表。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 走势对比", "📊 成交量", "🔗 相关性", "📊 收益对比", "⚖️ 风险收益"])
                    
                    with tab1:
                        # 归一化走势
                        st.subheader("归一化指数走势")
                        df_pivot = create_normalized_pivot(df_global, 'close')
                        fig_lines = plot_global_indices_comparison(df_pivot)
                        if fig_lines:
                            st.plotly_chart(fig_lines, use_container_width=True, key="mkt_global_lines")
                            st.caption("Source: index_global")
                        
                        st.caption("归一化后可直观对比各指数的相对表现（起点=100）。")
                        
                        st.divider()
                        
                        # 原始价格走势
                        st.subheader("原始价格走势")
                        fig_raw = plot_global_indices_raw(df_global)
                        if fig_raw:
                            st.plotly_chart(fig_raw, use_container_width=True, key="mkt_global_raw")
                        
                        st.caption("分子图展示各指数原始价格，便于观察绝对数值。")
                    
                    with tab2:
                        st.subheader("平均成交量对比")
                        fig_vol = plot_global_volume(df_global)
                        if fig_vol:
                            st.plotly_chart(fig_vol, use_container_width=True, key="mkt_global_vol_bar")
                        else:
                            st.info("部分指数无成交量数据。")
                        
                        st.divider()
                        
                        st.subheader("成交量走势")
                        fig_vol_trend = plot_global_volume_trend(df_global)
                        if fig_vol_trend:
                            st.plotly_chart(fig_vol_trend, use_container_width=True, key="mkt_global_vol_trend")
                        else:
                            st.info("选中的指数无成交量走势数据。")
                    
                    with tab3:
                        df_corr = calculate_global_correlation(df_global)
                        fig_corr = plot_global_correlation_heatmap(df_corr)
                        if fig_corr:
                            # 根据指数数量动态调整图表高度
                            chart_height = max(500, len(sel_indices) * 45)
                            fig_corr.update_layout(height=chart_height)
                            st.plotly_chart(fig_corr, use_container_width=True, key="mkt_global_corr")
                        
                        st.markdown(textwrap.dedent("""
                        **相关性洞察：**
                        - 美股三大指数（道琼斯、标普、纳指）高度相关
                        - A50与恒生相关性较高
                        - 低相关性的市场组合可分散风险
                        """))
                    
                    with tab4:
                        df_stats = calculate_index_returns(df_global)
                        fig_returns = plot_index_returns_bar(df_stats)
                        if fig_returns:
                            st.plotly_chart(fig_returns, use_container_width=True, key="mkt_global_returns")
                        
                        if not df_stats.empty:
                            st.dataframe(
                                df_stats[['index_name', 'total_return', 'ann_return', 'ann_volatility', 'sharpe_ratio', 'max_drawdown']],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "index_name": "指数",
                                    "total_return": st.column_config.NumberColumn("区间收益", format="%.1%"),
                                    "ann_return": st.column_config.NumberColumn("年化收益", format="%.1%"),
                                    "ann_volatility": st.column_config.NumberColumn("年化波动", format="%.1%"),
                                    "sharpe_ratio": st.column_config.NumberColumn("夏普比率", format="%.2f"),
                                    "max_drawdown": st.column_config.NumberColumn("最大回撤", format="%.1%")
                                }
                            )
                        
                        # 添加计算公式说明
                        with st.expander("📐 指标计算公式"):
                            st.markdown(textwrap.dedent(r"""
                            **区间收益 (Total Return)**
                            $$R = \frac{P_{end} - P_{start}}{P_{start}}$$
                            - $P_{end}$：期末收盘价
                            - $P_{start}$：期初收盘价
                            
                            ---
                            
                            **年化收益 (Annualized Return)**
                            $$R_{annual} = (1 + R)^{\frac{252}{n}} - 1$$
                            - $R$：区间收益
                            - $n$：交易日天数
                            - 252：一年的交易日数
                            
                            ---
                            
                            **年化波动率 (Annualized Volatility)**
                            $$\sigma_{annual} = \sigma_{daily} \times \sqrt{252}$$
                            - $\sigma_{daily}$：日收益率的标准差
                            
                            ---
                            
                            **夏普比率 (Sharpe Ratio)**
                            $$Sharpe = \frac{R_{annual}}{\sigma_{annual}}$$
                            - 简化计算，假设无风险收益率为0
                            - 反映单位风险获得的超额收益
                            
                            ---
                            
                            **最大回撤 (Maximum Drawdown)**
                            $$MDD = \max_{t} \left( \frac{Peak_t - P_t}{Peak_t} \right)$$
                            - $Peak_t$：截至时点t的历史最高价
                            - 反映从高点到低点的最大跌幅
                            """))
                    
                    with tab5:
                        df_stats = calculate_index_returns(df_global)
                        fig_rr = plot_risk_return_global(df_stats)
                        if fig_rr:
                            st.plotly_chart(fig_rr, use_container_width=True, key="mkt_global_rr")
                        
                        st.markdown(textwrap.dedent("""
                        **风险-收益洞察：**
                        - 右上角：高风险高收益（如新兴市场）
                        - 左上角：低风险高收益（理想区域）
                        - 夏普比率越高说明单位风险获得的收益越高
                        """))

    # --- 两市交易数据 ---
    elif subcategory_key == "mkt_trading":
        render_header("两市交易数据分析", "exchange")
        
        with st.expander("📘 相关知识：两市交易数据"):
            st.markdown(textwrap.dedent("""
            ### 📊 两市交易数据
            
            **市场交易统计** (daily_info) 提供上海和深圳交易所的总体数据：
            - amount（成交金额，亿元）
            - tr（换手率，%）
            - total_mv（总市值，亿元）
            - float_mv（流通市值，亿元）
            
            **深圳市场每日概况** (sz_daily_info) 深化深圳细分板块：
            - amount（成交金额，需要从元转换为亿元）
            - total_mv（总市值）
            - float_mv（流通市值）
            
            **关键指标**：
            - 金额换手率 = amount / float_mv （衡量交易热度）
            - 上海 vs 深圳对比（交易所异同）
            - 板块细分与热点追踪
            """))
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            trading_years = st.radio("时间跨度", [1, 2, 3, 5], index=1, format_func=lambda x: f"{x}年", key="mkt_trading_years", horizontal=True)
            trading_start = default_end - timedelta(days=365*trading_years)
            
            st.markdown("**板块选择**")
            
            # daily_info 板块
            st.markdown("<small>*上海/深交所数据*</small>", unsafe_allow_html=True)
            daily_codes = ['SH_MARKET', 'SZ_MARKET', 'SH_A', 'SZ_GEM', 'SH_STAR', 'SZ_MAIN', 'SH_FUND']
            sel_daily_codes = []
            for code in daily_codes:
                if st.checkbox(MARKET_CODES.get(code, code), value=code in ['SH_A', 'SZ_GEM'], key=f"mkt_trading_daily_{code}"):
                    sel_daily_codes.append(code)
            
            # sz_daily_info 板块
            st.markdown("<small>*深交所分类*</small>", unsafe_allow_html=True)
            sz_codes = ['股票', '创业板A股', '主板A股', '债券', '基金']
            sel_sz_codes = []
            for code in sz_codes:
                if st.checkbox(SZ_DAILY_CODES.get(code, code), value=False, key=f"mkt_trading_sz_{code}"):
                    sel_sz_codes.append(code)
        
        if not sel_daily_codes and not sel_sz_codes:
            st.info("请选择至少一个板块进行分析。")
        else:
            with st.spinner('正在加载交易数据...'):
                start_str = trading_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                
                # 加载数据
                df_daily = pd.DataFrame()
                if sel_daily_codes:
                    df_daily = load_daily_info(start_str, end_str, sel_daily_codes)
                    if not df_daily.empty:
                        df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount', 'tr', 'total_mv', 'float_mv']].copy()
                        df_daily['source'] = 'daily_info'
                        # 计算金额换手率
                        df_daily['amount_turnover'] = df_daily['amount'] / df_daily['float_mv'] * 100  # 百分比
                
                # 加载 sz_daily_info 数据
                df_sz = pd.DataFrame()
                if sel_sz_codes:
                    df_sz = load_sz_daily_info(start_str, end_str, sel_sz_codes)
                    if not df_sz.empty:
                        df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount', 'total_mv', 'float_mv', 'source']].copy()
                        # 计算金额换手率
                        df_sz['amount_turnover'] = df_sz['amount'] / df_sz['float_mv'] * 100  # 百分比
                        df_sz['tr'] = None
                
                # 合并数据
                if not df_daily.empty and not df_sz.empty:
                    df_info = pd.concat([df_daily, df_sz], ignore_index=True)
                elif not df_daily.empty:
                    df_info = df_daily
                elif not df_sz.empty:
                    df_info = df_sz
                else:
                    df_info = pd.DataFrame()
            
            if df_info.empty:
                st.warning("无法获取交易统计数据。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 整体活跃度", "🔄 沪深对比", "🔥 板块热点", "⚠️ 风险预警", "📊 综合框架"])
                    
                    with tab1:
                        st.subheader("成交金额与换手率动态监测")
                        
                        # 成交金额与换手率趋势图
                        fig_trend = plot_trading_amount_trend(df_info, sel_daily_codes + sel_sz_codes)
                        if fig_trend:
                            st.plotly_chart(fig_trend, use_container_width=True, key="mkt_trading_trend")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("无法生成趋势图，请确保选择了有效的板块。")
                        
                        st.markdown(textwrap.dedent("""
                        **洞察：**
                        - 成交额放大且换手率上升：市场情绪高涨
                        - 成交额萎缩但换手率上升：可能为出货信号
                        - 成交额与换手率同向变化反映市场一致性
                        """))
                        
                    with tab2:
                        st.subheader("上海 vs 深圳对比分析")
                        
                        # 上海深圳对比图
                        fig_comparison = plot_sh_sz_comparison(df_info)
                        if fig_comparison:
                            st.plotly_chart(fig_comparison, use_container_width=True, key="mkt_trading_comparison")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("无法生成对比图。")
                        
                        # 市值与换手率散点图
                        fig_scatter = plot_market_turnover_scatter(df_info)
                        if fig_scatter:
                            st.plotly_chart(fig_scatter, use_container_width=True, key="mkt_trading_scatter")
                            st.caption("Source: daily_info, sz_daily_info")
                        
                        st.markdown(textwrap.dedent("""
                        **洞察：**
                        - 上海市场通常市值更大、换手率较低（机构主导）
                        - 深圳市场尤其是创业板，换手率较高（散户活跃）
                        - 小市值高换手率板块可能存在短期机会
                        """))
                        
                    with tab3:
                        st.subheader("板块细分与热点追踪")
                        
                        # 选择指标
                        metric = st.selectbox(
                            "选择热力图指标",
                            options=['amount', 'amount_turnover', 'total_mv'],
                            format_func=lambda x: {'amount': '成交金额', 'amount_turnover': '金额换手率', 'total_mv': '总市值'}[x],
                            key="mkt_trading_heatmap_metric"
                        )
                        
                        # 板块热力图
                        fig_heatmap = plot_sector_heatmap(df_info, metric)
                        if fig_heatmap:
                            st.plotly_chart(fig_heatmap, use_container_width=True, key="mkt_trading_heatmap")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("无法生成热力图。")
                        
                        st.markdown(textwrap.dedent("""
                        **洞察：**
                        - 热力图颜色深浅反映板块热度
                        - 横向对比可发现板块轮动规律
                        - 纵向对比可观察季节性规律
                        """))
                        
                    with tab4:
                        st.subheader("风险预警与择时决策")
                        
                        # 选择风险指标
                        risk_metric = st.selectbox(
                            "选择风险指标",
                            options=['tr', 'amount_turnover'],
                            format_func=lambda x: {'tr': '换手率', 'amount_turnover': '金额换手率'}[x],
                            key="mkt_trading_risk_metric"
                        )
                        
                        # 风险预警箱线图
                        fig_box = plot_risk_warning_box(df_info, risk_metric)
                        if fig_box:
                            st.plotly_chart(fig_box, use_container_width=True, key="mkt_trading_box")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("无法生成风险预警图。")
                        
                        st.markdown(textwrap.dedent("""
                        **风险阈值参考：**
                        - 换手率 > 2%：高风险区域，警惕回调
                        - 换手率 < 0.5%：低风险区域，可能见底
                        - 金额换手率异常高：警惕资金过度炒作
                        """))
                        
                    with tab5:
                        st.subheader("综合市场框架")
                        
                        # 流动性评分
                        st.markdown("#### 流动性评分")
                        
                        # 选择板块计算流动性评分
                        score_codes = sel_daily_codes + sel_sz_codes
                        if score_codes:
                            cols = st.columns(min(len(score_codes), 3))
                            for i, code in enumerate(score_codes):
                                with cols[i % len(cols)]:
                                    fig_gauge = plot_liquidity_score_gauge(df_info, code)
                                    if fig_gauge:
                                        st.plotly_chart(fig_gauge, use_container_width=True, key=f"mkt_trading_gauge_{i}_{code}")
                                    else:
                                        st.info(f"无法计算{code}的流动性评分。")
                        else:
                            st.info("请选择至少一个板块计算流动性评分。")
                        
                        st.markdown(textwrap.dedent("""
                        **流动性评分说明：**
                        - 综合成交额、换手率、市值等因素
                        - 高分(>70)：流动性优秀，适合大资金进出
                        - 中分(40-70)：流动性良好，平衡区域
                        - 低分(<40)：流动性一般，注意冲击成本
                        """))
