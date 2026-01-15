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
    # Date Default
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- Market Valuation ---
    if subcategory_key == "mkt_valuation":
        render_header("Market ValuationAnalysis", "gauge")
        
        with st.expander("📘 Related Knowledge：What isMarket Valuation？"):
            st.markdown(textwrap.dedent("""
            ### 📊 What isMarket Valuation？
            
            **市盈率 (PE)** 是衡量整个Market Valuation水平的核心指标：
            - PE = Total Market Cap / Total Net Profit
            - PE偏高可能意味着Market Valuation过热
            - PELow value may indicate market undervaluation
            
            **PEHistorical Percentile**：当前PEHistorical Position
            - 低于30%Percentile：历史低估区域
            - 高于70%Percentile：历史高估区域
            """))
        
        st.divider()
        
        # Filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            hist_years = st.radio("历史数据", [1, 3, 5, 10], index=2, format_func=lambda x: f"{x}年", key="mkt_pe_years", horizontal=True)
            hist_start = default_end - timedelta(days=365*hist_years)
            
            st.markdown("**Sector Selection**")
            # Major Sectors - Checkboxes for multi-select
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
            st.info("Please select at least one sector for analysis。")
        else:
            with st.spinner('Loading market statistics data...'):
                start_str = hist_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                df_info = load_daily_info(start_str, end_str, sel_codes)
            
            if df_info.empty:
                st.warning("Unable to fetch market statistics，请检查Database是否已Load daily_info 表。")
            else:
                with right_col:
                    tab1, tab2, tab3 = st.tabs(["📈 PETrend", "📊 PEPercentile", "📋 Sector Comparison"])
                    
                    with tab1:
                        fig_pe = plot_pe_trend(df_info, sel_codes)
                        if fig_pe:
                            st.plotly_chart(fig_pe, use_container_width=True, key="mkt_pe_trend")
                            st.caption("Source: daily_info")
                        
                        st.caption("PETrend反映市场整体估值Change，可用于判断市场周期位置。")
                    
                    with tab2:
                        # SectorPEPercentile
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
                        **如何解读PEPercentile数：**
                        - 🟢 **< 30%**：历史低估区域，可能是较好的买入时机
                        - 🟡 **30%-70%**：Fair Valuation
                        - 🔴 **> 70%**：历史高估区域，需谨慎
                        """))
                    
                    with tab3:
                        fig_bar = plot_pe_comparison_bar(df_info)
                        if fig_bar:
                            st.plotly_chart(fig_bar, use_container_width=True, key="mkt_pe_bar")
                            st.caption("Source: daily_info")
                        
                        # Trend
                        fig_mv = plot_market_mv_trend(df_info, sel_codes)
                        if fig_mv:
                            st.plotly_chart(fig_mv, use_container_width=True, key="mkt_mv_trend")
                            st.caption("Source: daily_info")
    
    # --- Market Sentiment ---
    elif subcategory_key == "mkt_sentiment":
        render_header("Market SentimentAnalysis", "pulse")
        
        with st.expander("📘 Related Knowledge：Market Sentiment指标"):
            st.markdown(textwrap.dedent("""
            ### 📈 Market Sentiment
            
            **成交额**反映市场活跃程度：
            - Price Rise with Volume：多方力量强劲
            - 缩量下跌：空方力量衰竭，可能见底
            - Peak Volume at Peak Price：警惕风险
            
            **Turnover Rate**反映市场交易频率：
            - 高Turnover Rate：Market SentimentEnthusiasm or Large Fund Activity
            - 低Turnover Rate：市场冷淡
            """))
        
        st.divider()
        
        # Filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            date_mode = st.radio("Selection Mode", ["Preset", "Custom"], index=0, key="mkt_sent_date_mode", horizontal=True)
            
            if date_mode == "Preset":
                sent_years = st.radio("时间跨度", [1, 2, 3, 5, 10], index=1, format_func=lambda x: f"{x}年", key="mkt_sent_years", horizontal=True)
                sent_start = default_end - timedelta(days=365*sent_years)
            else:
                from datetime import date
                col1, col2 = st.columns(2)
                with col1:
                    sent_start = st.date_input("Start Date", value=default_end - timedelta(days=365*2), key="mkt_sent_start")
                with col2:
                    sent_end_input = st.date_input("End Date", value=default_end, key="mkt_sent_end_input")
                default_end = sent_end_input
            
            st.markdown("**Sector Selection**")
            
            # daily_info Sector ()
            st.markdown("<small>*上海/深交所数据*</small>", unsafe_allow_html=True)
            daily_codes = ['SH_MARKET', 'SZ_MARKET', 'SH_A', 'SZ_GEM', 'SH_STAR', 'SH_FUND']
            sel_daily_codes = []
            for code in daily_codes:
                if st.checkbox(MARKET_CODES.get(code, code), value=code in ['SH_A', 'SZ_GEM'], key=f"mkt_sent_daily_{code}"):
                    sel_daily_codes.append(code)
            
            # sz_daily_info Sector ()
            st.markdown("<small>*Shenzhen Exchange Classification*</small>", unsafe_allow_html=True)
            sz_codes = ['股票', '创业板A-Share', '主板A-Share', '债券', '基金']
            sel_sz_codes = []
            for code in sz_codes:
                if st.checkbox(SZ_DAILY_CODES.get(code, code), value=False, key=f"mkt_sent_sz_{code}"):
                    sel_sz_codes.append(code)
        
        if not sel_daily_codes and not sel_sz_codes:
            st.info("Please select at least one sector for analysis。")
        else:
            with st.spinner('Loading data...'):
                start_str = sent_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                
                #  daily_info 
                df_daily = pd.DataFrame()
                if sel_daily_codes:
                    df_daily = load_daily_info(start_str, end_str, sel_daily_codes)
                    if not df_daily.empty:
                        df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount', 'pe', 'tr']].copy()
                        df_daily['source'] = 'daily_info'
                
                #  sz_daily_info 
                df_sz = pd.DataFrame()
                if sel_sz_codes:
                    df_sz = load_sz_daily_info(start_str, end_str, sel_sz_codes)
                    if not df_sz.empty:
                        df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount']].copy()
                        df_sz['pe'] = None
                        df_sz['tr'] = None
                        df_sz['source'] = 'sz_daily_info'
                
                # Merge data
                if not df_daily.empty and not df_sz.empty:
                    df_info = pd.concat([df_daily, df_sz], ignore_index=True)
                elif not df_daily.empty:
                    df_info = df_daily
                elif not df_sz.empty:
                    df_info = df_sz
                else:
                    df_info = pd.DataFrame()
            
            if df_info.empty:
                st.warning("Unable to fetch market statistics。")
            else:
                # Get all selected codes (combined)
                all_sel_codes = sel_daily_codes + sel_sz_codes
                
                with right_col:
                    tab1, tab2, tab3 = st.tabs(["📊 成交额Trend", "🔥 Turnover Rate热力图", "📈 量价关系"])
                    
                    with tab1:
                        # SectorTrend
                        
                        fig_amount = px.line(
                            df_info.sort_values('trade_date'),
                            x='trade_date', 
                            y='amount',
                            color='market_name',
                            title='成交额Trend对比 (单位: 100M CNY)'
                        )
                        fig_amount.update_layout(
                            xaxis_title='日期',
                            yaxis_title='成交额 (100M CNY)',
                            legend_title='Sector',
                            height=500
                        )
                        st.plotly_chart(fig_amount, use_container_width=True, key="mkt_sent_amount_combined")
                        st.caption("Source: daily_info, sz_daily_info")
                        st.caption("Trading amount breaking through MA often indicates trend change。")
                    
                    with tab2:
                        # Only show sectors with turnover data
                        df_with_tr = df_info[df_info['tr'].notna()]
                        if df_with_tr.empty:
                            st.info("Selected sectors have no turnover data。")
                        else:
                            for sel_code in sel_daily_codes:
                                fig_tr = plot_turnover_heatmap(df_with_tr, sel_code)
                                if fig_tr:
                                    st.plotly_chart(fig_tr, use_container_width=True, key=f"mkt_tr_heatmap_{sel_code}")
                                    st.caption(f"Source: daily_info ({MARKET_CODES.get(sel_code, sel_code)})")
                        
                        st.caption("通过月度Turnover Rate热力图观察Market SentimentSeasonal Pattern。")
                    
                    with tab3:
                        # PESector
                        df_with_pe = df_info[df_info['pe'].notna()]
                        if df_with_pe.empty:
                            st.info("选中的Sector没有PE数据。")
                        else:
                            for sel_code in sel_daily_codes:
                                fig_vp = plot_volume_price_scatter(df_with_pe, sel_code)
                                if fig_vp:
                                    st.plotly_chart(fig_vp, use_container_width=True, key=f"mkt_vp_scatter_{sel_code}")
                                    st.caption(f"Source: daily_info ({MARKET_CODES.get(sel_code, sel_code)})")
                        
                        st.markdown(textwrap.dedent("""
                        **Volume-Price Relationship Insights：**
                        - 成交额与PEChange的关系反映资金推动效果
                        - When Volume IncreasesPE上涨幅度可观察市场效率
                        """))
    
    # --- Global Comparison ---
    elif subcategory_key == "mkt_global":
        render_header("Global Market Comparison", "globe")
        
        with st.expander("📘 Related Knowledge：全球市场"):
            st.markdown(textwrap.dedent("""
            ### 🌍 Why Focus on Global Markets？
            
            **Global Integration**：
            - US stocks may have leading effect on A-shares
            - Risk events often spread across markets
            - Correlation analysis helps global asset allocation
            
            **Major Indices**：
            - 🇨🇳 富时A50、恒生Index
            - 🇺🇸 道琼斯、标普500、纳斯达克
            - 🇯🇵 日经225 | 🇩🇪 德国DAX | 🇬🇧 富时100
            """))
        
        st.divider()
        
        # Filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            global_years = st.radio("时间跨度", [1, 2, 3, 5], index=1, format_func=lambda x: f"{x}年", key="mkt_global_years", horizontal=True)
            global_start = default_end - timedelta(days=365*global_years)
            
            st.markdown("**Index Selection**")
            available_indices = get_available_global_indices()
            
            # checkbox
            
            # Group Display
            st.markdown("<small>*Asia Pacific*</small>", unsafe_allow_html=True)
            asia_indices = ['XIN9', 'HSI', 'HKTECH', 'N225', 'KS11', 'TWII', 'AS51', 'SENSEX']
            sel_asia = []
            for idx in asia_indices:
                if idx in available_indices:
                    if st.checkbox(get_index_display_name(idx), value=idx in ['XIN9', 'HSI', 'N225'], key=f"cb_{idx}"):
                        sel_asia.append(idx)
            
            st.markdown("<small>*Europe/Americas*</small>", unsafe_allow_html=True)
            west_indices = ['DJI', 'SPX', 'IXIC', 'RUT', 'FTSE', 'GDAXI', 'FCHI', 'CSX5P', 'SPTSX']
            sel_west = []
            for idx in west_indices:
                if idx in available_indices:
                    if st.checkbox(get_index_display_name(idx), value=idx in ['DJI', 'SPX', 'IXIC'], key=f"cb_{idx}"):
                        sel_west.append(idx)
            
            st.markdown("<small>*Emerging Markets*</small>", unsafe_allow_html=True)
            em_indices = ['IBOVESPA', 'RTS', 'CKLSE', 'HKAH']
            sel_em = []
            for idx in em_indices:
                if idx in available_indices:
                    if st.checkbox(get_index_display_name(idx), value=False, key=f"cb_{idx}"):
                        sel_em.append(idx)
            
            sel_indices = sel_asia + sel_west + sel_em
        
        if not sel_indices:
            st.info("Please select at least one index for analysis。")
        else:
            with st.spinner('Loading global index data...'):
                start_str = global_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                df_global = load_index_global(start_str, end_str, sel_indices)
            
            if df_global.empty:
                st.warning("Cannot Fetch GlobalIndex数据，请检查Database是否已Load index_global 表。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Trend对比", "📊 成交量", "🔗 相关性", "📊 Return对比", "⚖️ 风险Return"])
                    
                    with tab1:
                        # Trend
                        st.subheader("NormalizedIndexTrend")
                        df_pivot = create_normalized_pivot(df_global, 'close')
                        fig_lines = plot_global_indices_comparison(df_pivot)
                        if fig_lines:
                            st.plotly_chart(fig_lines, use_container_width=True, key="mkt_global_lines")
                            st.caption("Source: index_global")
                        
                        st.caption("Normalized后可直观对比各Index的相对表现（起点=100）。")
                        
                        st.divider()
                        
                        # Trend
                        st.subheader("原始PriceTrend")
                        fig_raw = plot_global_indices_raw(df_global)
                        if fig_raw:
                            st.plotly_chart(fig_raw, use_container_width=True, key="mkt_global_raw")
                        
                        st.caption("Subplots show raw prices of each index, easy to observe absolute values。")
                    
                    with tab2:
                        st.subheader("Average Volume Comparison")
                        fig_vol = plot_global_volume(df_global)
                        if fig_vol:
                            st.plotly_chart(fig_vol, use_container_width=True, key="mkt_global_vol_bar")
                        else:
                            st.info("Some indices have no volume data。")
                        
                        st.divider()
                        
                        st.subheader("成交量Trend")
                        fig_vol_trend = plot_global_volume_trend(df_global)
                        if fig_vol_trend:
                            st.plotly_chart(fig_vol_trend, use_container_width=True, key="mkt_global_vol_trend")
                        else:
                            st.info("选中的IndexNo VolumeTrend数据。")
                    
                    with tab3:
                        df_corr = calculate_global_correlation(df_global)
                        fig_corr = plot_global_correlation_heatmap(df_corr)
                        if fig_corr:
                            # Dynamically adjust chart height based on number of indices
                            chart_height = max(500, len(sel_indices) * 45)
                            fig_corr.update_layout(height=chart_height)
                            st.plotly_chart(fig_corr, use_container_width=True, key="mkt_global_corr")
                        
                        st.markdown(textwrap.dedent("""
                        **Correlation Insights：**
                        - 美股三大Index（道琼斯、标普、纳指）高度相关
                        - A50High correlation with Hang Seng
                        - Low correlation market combinations can diversify risk
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
                                    "index_name": "Index",
                                    "total_return": st.column_config.NumberColumn("Period Return", format="%.1%"),
                                    "ann_return": st.column_config.NumberColumn("Annualized Return", format="%.1%"),
                                    "ann_volatility": st.column_config.NumberColumn("Annualized Volatility", format="%.1%"),
                                    "sharpe_ratio": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f"),
                                    "max_drawdown": st.column_config.NumberColumn("Max Drawdown", format="%.1%")
                                }
                            )
                        
                        # Add calculation formula explanation
                        with st.expander("📐 Indicator Calculation Formulas"):
                            st.markdown(textwrap.dedent(r"""
                            **Period Return (Total Return)**
                            $$R = \frac{P_{end} - P_{start}}{P_{start}}$$
                            - $P_{end}$：Ending Close Price
                            - $P_{start}$：Starting Close Price
                            
                            ---
                            
                            **Annualized Return (Annualized Return)**
                            $$R_{annual} = (1 + R)^{\frac{252}{n}} - 1$$
                            - $R$：Period Return
                            - $n$：Trading Days
                            - 252：Trading Days Per Year
                            
                            ---
                            
                            **Annualized Volatility率 (Annualized Volatility)**
                            $$\sigma_{annual} = \sigma_{daily} \times \sqrt{252}$$
                            - $\sigma_{daily}$：Standard Deviation of Daily Returns
                            
                            ---
                            
                            **Sharpe Ratio (Sharpe Ratio)**
                            $$Sharpe = \frac{R_{annual}}{\sigma_{annual}}$$
                            - 简化Calculate，假设无风险Return率为0
                            - Reflects excess return per unit of risk
                            
                            ---
                            
                            **Max Drawdown (Maximum Drawdown)**
                            $$MDD = \max_{t} \left( \frac{Peak_t - P_t}{Peak_t} \right)$$
                            - $Peak_t$：截至时点t的历史最高价
                            - Reflects maximum decline from peak to trough
                            """))
                    
                    with tab5:
                        df_stats = calculate_index_returns(df_global)
                        fig_rr = plot_risk_return_global(df_stats)
                        if fig_rr:
                            st.plotly_chart(fig_rr, use_container_width=True, key="mkt_global_rr")
                        
                        st.markdown(textwrap.dedent("""
                        **风险-ReturnInsights：**
                        - Upper Right：高风险高Return（如Emerging Markets）
                        - Upper Left：低风险高Return（理想区域）
                        - Sharpe Ratio越高说明单位风险获得的Return越高
                        """))

    # --- Two-Market Trading Data ---
    elif subcategory_key == "mkt_trading":
        render_header("Two-Market Trading DataAnalysis", "exchange")
        
        with st.expander("📘 Related Knowledge：Two-Market Trading Data"):
            st.markdown(textwrap.dedent("""
            ### 📊 Two-Market Trading Data
            
            **市场交易统计** (daily_info) 提供上海和深圳交易所的总体数据：
            - amount（成交Amount，100M CNY）
            - tr（Turnover Rate，%）
            - total_mv（Total Market Cap，100M CNY）
            - float_mv（Circulating Market Cap，100M CNY）
            
            **深圳市场每日概况** (sz_daily_info) 深化深圳细分Sector：
            - amount（成交Amount，需要从元转换为100M CNY）
            - total_mv（Total Market Cap）
            - float_mv（Circulating Market Cap）
            
            **Key Indicators**：
            - AmountTurnover Rate = amount / float_mv （衡量交易热度）
            - 上海 vs 深圳对比（交易所异同）
            - Sector Breakdown and Hotspot Tracking
            """))
        
        st.divider()
        
        # Filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            trading_years = st.radio("时间跨度", [1, 2, 3, 5], index=1, format_func=lambda x: f"{x}年", key="mkt_trading_years", horizontal=True)
            trading_start = default_end - timedelta(days=365*trading_years)
            
            st.markdown("**Sector Selection**")
            
            # daily_info Sector
            st.markdown("<small>*上海/深交所数据*</small>", unsafe_allow_html=True)
            daily_codes = ['SH_MARKET', 'SZ_MARKET', 'SH_A', 'SZ_GEM', 'SH_STAR', 'SZ_MAIN', 'SH_FUND']
            sel_daily_codes = []
            for code in daily_codes:
                if st.checkbox(MARKET_CODES.get(code, code), value=code in ['SH_A', 'SZ_GEM'], key=f"mkt_trading_daily_{code}"):
                    sel_daily_codes.append(code)
            
            # sz_daily_info Sector
            st.markdown("<small>*Shenzhen Exchange Classification*</small>", unsafe_allow_html=True)
            sz_codes = ['股票', '创业板A-Share', '主板A-Share', '债券', '基金']
            sel_sz_codes = []
            for code in sz_codes:
                if st.checkbox(SZ_DAILY_CODES.get(code, code), value=False, key=f"mkt_trading_sz_{code}"):
                    sel_sz_codes.append(code)
        
        if not sel_daily_codes and not sel_sz_codes:
            st.info("Please select at least one sector for analysis。")
        else:
            with st.spinner('Loading trading data...'):
                start_str = trading_start.strftime('%Y%m%d')
                end_str = default_end.strftime('%Y%m%d')
                
                # Load Data
                df_daily = pd.DataFrame()
                if sel_daily_codes:
                    df_daily = load_daily_info(start_str, end_str, sel_daily_codes)
                    if not df_daily.empty:
                        df_daily = df_daily[['trade_date', 'ts_code', 'market_name', 'amount', 'tr', 'total_mv', 'float_mv']].copy()
                        df_daily['source'] = 'daily_info'
                        # Turnover Rate
                        df_daily['amount_turnover'] = df_daily['amount'] / df_daily['float_mv'] * 100  # Percentage
                
                #  sz_daily_info 
                df_sz = pd.DataFrame()
                if sel_sz_codes:
                    df_sz = load_sz_daily_info(start_str, end_str, sel_sz_codes)
                    if not df_sz.empty:
                        df_sz = df_sz[['trade_date', 'ts_code', 'market_name', 'amount', 'total_mv', 'float_mv', 'source']].copy()
                        # Turnover Rate
                        df_sz['amount_turnover'] = df_sz['amount'] / df_sz['float_mv'] * 100  # Percentage
                        df_sz['tr'] = None
                
                # Merge data
                if not df_daily.empty and not df_sz.empty:
                    df_info = pd.concat([df_daily, df_sz], ignore_index=True)
                elif not df_daily.empty:
                    df_info = df_daily
                elif not df_sz.empty:
                    df_info = df_sz
                else:
                    df_info = pd.DataFrame()
            
            if df_info.empty:
                st.warning("Unable to fetch trading statistics。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overall Activity", "🔄 沪深对比", "🔥 Sector热点", "⚠️ 风险预警", "📊 综合框架"])
                    
                    with tab1:
                        st.subheader("成交Amount与Turnover Rate动态监测")
                        
                        # Turnover Rate
                        fig_trend = plot_trading_amount_trend(df_info, sel_daily_codes + sel_sz_codes)
                        if fig_trend:
                            st.plotly_chart(fig_trend, use_container_width=True, key="mkt_trading_trend")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("无法生成趋势图，请确保选择了有效的Sector。")
                        
                        st.markdown(textwrap.dedent("""
                        **Insights：**
                        - 成交额放大且Turnover Rate上升：Market Sentiment高涨
                        - 成交额萎缩但Turnover Rate上升：可能为出货信号
                        - 成交额与Turnover Rate同向Change反映市场一致性
                        """))
                        
                    with tab2:
                        st.subheader("上海 vs 深圳对比Analysis")
                        
                        # Shanghai vs Shenzhen Comparison Chart
                        fig_comparison = plot_sh_sz_comparison(df_info)
                        if fig_comparison:
                            st.plotly_chart(fig_comparison, use_container_width=True, key="mkt_trading_comparison")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("Unable to generate comparison chart。")
                        
                        # Turnover Rate
                        fig_scatter = plot_market_turnover_scatter(df_info)
                        if fig_scatter:
                            st.plotly_chart(fig_scatter, use_container_width=True, key="mkt_trading_scatter")
                            st.caption("Source: daily_info, sz_daily_info")
                        
                        st.markdown(textwrap.dedent("""
                        **Insights：**
                        - 上海市场通常市值更大、Turnover Rate较低（机构主导）
                        - 深圳市场尤其是创业板，Turnover Rate较高（散户活跃）
                        - 小市值高Turnover RateSector可能存在短期机会
                        """))
                        
                    with tab3:
                        st.subheader("Sector Breakdown and Hotspot Tracking")
                        
                        # Select Indicator
                        metric = st.selectbox(
                            "Select Heatmap Indicator",
                            options=['amount', 'amount_turnover', 'total_mv'],
                            format_func=lambda x: {'amount': '成交Amount', 'amount_turnover': 'AmountTurnover Rate', 'total_mv': 'Total Market Cap'}[x],
                            key="mkt_trading_heatmap_metric"
                        )
                        
                        # Sector
                        fig_heatmap = plot_sector_heatmap(df_info, metric)
                        if fig_heatmap:
                            st.plotly_chart(fig_heatmap, use_container_width=True, key="mkt_trading_heatmap")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("Unable to generate heatmap。")
                        
                        st.markdown(textwrap.dedent("""
                        **Insights：**
                        - 热力图颜色深浅反映Sector热度
                        - 横向对比可发现Sector轮动规律
                        - Vertical comparison reveals seasonal patterns
                        """))
                        
                    with tab4:
                        st.subheader("Risk Warning and Timing Decisions")
                        
                        # Select Risk Indicator
                        risk_metric = st.selectbox(
                            "Select Risk Indicator",
                            options=['tr', 'amount_turnover'],
                            format_func=lambda x: {'tr': 'Turnover Rate', 'amount_turnover': 'AmountTurnover Rate'}[x],
                            key="mkt_trading_risk_metric"
                        )
                        
                        # Risk Warning Box Plot
                        fig_box = plot_risk_warning_box(df_info, risk_metric)
                        if fig_box:
                            st.plotly_chart(fig_box, use_container_width=True, key="mkt_trading_box")
                            st.caption("Source: daily_info, sz_daily_info")
                        else:
                            st.info("Unable to generate risk warning chart。")
                        
                        st.markdown(textwrap.dedent("""
                        **Risk Threshold Reference：**
                        - Turnover Rate > 2%：高风险区域，警惕回调
                        - Turnover Rate < 0.5%：低风险区域，可能见底
                        - AmountTurnover Rate异常高：Beware of Excessive Speculation
                        """))
                        
                    with tab5:
                        st.subheader("Comprehensive Market Framework")
                        
                        # Liquidity Score
                        st.markdown("#### Liquidity Score")
                        
                        # SectorLiquidity Score
                        score_codes = sel_daily_codes + sel_sz_codes
                        if score_codes:
                            cols = st.columns(min(len(score_codes), 3))
                            for i, code in enumerate(score_codes):
                                with cols[i % len(cols)]:
                                    fig_gauge = plot_liquidity_score_gauge(df_info, code)
                                    if fig_gauge:
                                        st.plotly_chart(fig_gauge, use_container_width=True, key=f"mkt_trading_gauge_{i}_{code}")
                                    else:
                                        st.info(f"Cannot Calculate{code}的Liquidity Score。")
                        else:
                            st.info("请选择至少一个SectorCalculateLiquidity Score。")
                        
                        st.markdown(textwrap.dedent("""
                        **Liquidity Score说明：**
                        - 综合成交额、Turnover Rate、市值等因素
                        - High Score(>70)：流动性优秀，适合大资金进出
                        - 中分(40-70)：流动性良好，平衡区域
                        - 低分(<40)：流动性一般，注意冲击成本
                        """))
