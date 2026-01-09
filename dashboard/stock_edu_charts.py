"""
A股市场教育图表模块
==================
中文界面的Plotly交互式图表函数。
按四个学习层次组织。
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ============================================================================
# 颜色方案
# ============================================================================
COLORS = {
    'primary': '#D97757',
    'secondary': '#5C5653',
    'accent': '#4A90A4',
    'success': '#6BBF59',
    'warning': '#E8A838',
    'danger': '#C75B5B',
    'background': '#FAF5F0',
    'text': '#1A1A1A',
}

# 多资产颜色序列
STOCK_COLORS = [
    '#D97757', '#4A90A4', '#6BBF59', '#E8A838', '#8B7355',
    '#C75B5B', '#7B68EE', '#20B2AA', '#FF6B6B', '#4ECDC4',
    '#9B59B6', '#3498DB', '#E74C3C', '#2ECC71', '#F39C12'
]

# 行业颜色（申万一级）
INDUSTRY_COLORS = px.colors.qualitative.Set3


def apply_chart_style(fig, title=None):
    """应用统一的图表样式。"""
    fig.update_layout(
        font_family="Inter, -apple-system, PingFang SC, Microsoft YaHei, sans-serif",
        font_color=COLORS['text'],
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=60 if title else 40, b=60),
        title=dict(
            text=title,
            font=dict(size=18, weight=600),
            x=0,
            xanchor='left'
        ) if title else None,
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            borderwidth=0,
            font=dict(size=11)
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#E8E0D8',
            showline=True,
            linewidth=1,
            linecolor='#E8E0D8'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#E8E0D8',
            showline=True,
            linewidth=1,
            linecolor='#E8E0D8'
        ),
        hoverlabel=dict(font_family="Inter, PingFang SC", font_size=12)
    )
    return fig


# ============================================================================
# 第1层：认识A股市场
# ============================================================================

def plot_market_pie(market_counts: dict):
    """
    板块分布饼图。
    """
    if not market_counts:
        return None
    
    df = pd.DataFrame(list(market_counts.items()), columns=['板块', '数量'])
    
    fig = px.pie(
        df,
        values='数量',
        names='板块',
        color_discrete_sequence=STOCK_COLORS,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='outside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
    )
    
    fig = apply_chart_style(fig, title="A股板块分布")
    fig.update_layout(legend=dict(orientation='h', yanchor='bottom', y=-0.15))
    
    return fig


def plot_status_pie(df_basic: pd.DataFrame):
    """
    上市状态分布饼图。
    """
    if df_basic.empty:
        return None
    
    counts = df_basic['status_name'].value_counts().reset_index()
    counts.columns = ['状态', '数量']
    
    fig = px.pie(
        counts,
        values='数量',
        names='状态',
        color_discrete_sequence=[COLORS['success'], COLORS['danger'], COLORS['warning']],
        hole=0.4
    )
    
    fig.update_traces(textposition='outside', textinfo='label+percent')
    fig = apply_chart_style(fig, title="上市状态分布")
    
    return fig


def plot_industry_bar(industry_counts: dict, top_n: int = 20):
    """
    行业分布柱状图。
    """
    if not industry_counts:
        return None
    
    df = pd.DataFrame(list(industry_counts.items()), columns=['行业', '数量'])
    df = df.sort_values('数量', ascending=True).tail(top_n)
    
    fig = px.bar(
        df,
        x='数量',
        y='行业',
        orientation='h',
        color='数量',
        color_continuous_scale=[[0, COLORS['accent']], [1, COLORS['primary']]]
    )
    
    fig = apply_chart_style(fig, title=f"行业分布 TOP{top_n}")
    fig.update_layout(
        coloraxis_showscale=False,
        yaxis_title='',
        xaxis_title='上市公司数量'
    )
    
    return fig


def plot_area_bar(area_counts: dict, top_n: int = 15):
    """
    地域分布柱状图。
    """
    if not area_counts:
        return None
    
    df = pd.DataFrame(list(area_counts.items()), columns=['省份', '数量'])
    df = df.sort_values('数量', ascending=True).tail(top_n)
    
    fig = px.bar(
        df,
        x='数量',
        y='省份',
        orientation='h',
        color='数量',
        color_continuous_scale=[[0, '#4A90A4'], [1, '#D97757']]
    )
    
    fig = apply_chart_style(fig, title=f"地域分布 TOP{top_n}")
    fig.update_layout(coloraxis_showscale=False, yaxis_title='', xaxis_title='上市公司数量')
    
    return fig


# ============================================================================
# 第2层：理解股票价格
# ============================================================================

def plot_candlestick(df: pd.DataFrame, ts_code: str, name_map: dict = None):
    """
    K线图。
    """
    if df.empty:
        return None
    
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return None
    
    stock_name = name_map.get(ts_code, ts_code) if name_map else ts_code
    
    fig = go.Figure(data=[go.Candlestick(
        x=data['trade_date'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        increasing_line_color=COLORS['danger'],  # 中国股市红涨
        decreasing_line_color=COLORS['success'],  # 绿跌
        name=stock_name
    )])
    
    fig = apply_chart_style(fig, title=f"{stock_name} K线图")
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return fig


def plot_price_lines(df_pivot: pd.DataFrame, normalize: bool = True, name_map: dict = None):
    """
    多股票价格走势对比。
    """
    if df_pivot.empty:
        return None
    
    if normalize:
        df_plot = df_pivot / df_pivot.iloc[0] * 100
        y_title = '归一化价格 (首日=100)'
    else:
        df_plot = df_pivot
        y_title = '收盘价'
    
    # 重命名列
    if name_map:
        df_plot.columns = [name_map.get(c, c) for c in df_plot.columns]
    
    fig = px.line(
        df_plot.reset_index(),
        x='trade_date',
        y=df_plot.columns.tolist(),
        color_discrete_sequence=STOCK_COLORS
    )
    
    fig = apply_chart_style(fig, title="股票价格走势对比")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title=y_title,
        legend_title='股票',
        hovermode='x unified'
    )
    
    return fig


def plot_return_distribution(df: pd.DataFrame, ts_code: str = None, name_map: dict = None):
    """
    收益率分布直方图。
    """
    if df.empty or 'return' not in df.columns:
        return None
    
    data = df.dropna(subset=['return']).copy()
    if ts_code:
        data = data[data['ts_code'] == ts_code]
    
    if data.empty:
        return None
    
    # 映射名称
    if name_map:
        data['stock_name'] = data['ts_code'].map(name_map)
    else:
        data['stock_name'] = data['ts_code']
    
    fig = px.histogram(
        data,
        x='return',
        color='stock_name',
        marginal='box',
        nbins=50,
        color_discrete_sequence=STOCK_COLORS,
        opacity=0.7
    )
    
    fig = apply_chart_style(fig, title="日收益率分布")
    fig.update_layout(
        xaxis_title='日收益率',
        yaxis_title='频数',
        xaxis_tickformat='.1%',
        barmode='overlay'
    )
    
    return fig


def plot_volatility_comparison(df_stats: pd.DataFrame, name_map: dict = None):
    """
    波动率对比柱状图。
    """
    if df_stats.empty or 'ann_volatility' not in df_stats.columns:
        return None
    
    df = df_stats.copy()
    if name_map:
        df['stock_name'] = df['ts_code'].map(name_map)
    else:
        df['stock_name'] = df['ts_code']
    
    df = df.sort_values('ann_volatility', ascending=True)
    
    fig = px.bar(
        df,
        x='ann_volatility',
        y='stock_name',
        orientation='h',
        color='ann_volatility',
        color_continuous_scale=[[0, '#6BBF59'], [0.5, '#E8A838'], [1, '#C75B5B']]
    )
    
    fig = apply_chart_style(fig, title="年化波动率对比")
    fig.update_layout(
        xaxis_title='年化波动率',
        yaxis_title='',
        xaxis_tickformat='.0%',
        coloraxis_showscale=False
    )
    
    return fig


# ============================================================================
# 第3层：分析估值指标
# ============================================================================

def plot_pe_timeseries(df: pd.DataFrame, ts_codes: list = None, name_map: dict = None):
    """
    PE时序图。
    """
    if df.empty or 'pe_ttm' not in df.columns:
        return None
    
    data = df.dropna(subset=['pe_ttm']).copy()
    if ts_codes:
        data = data[data['ts_code'].isin(ts_codes)]
    
    if data.empty:
        return None
    
    if name_map:
        data['stock_name'] = data['ts_code'].map(name_map)
    else:
        data['stock_name'] = data['ts_code']
    
    fig = px.line(
        data,
        x='trade_date',
        y='pe_ttm',
        color='stock_name',
        color_discrete_sequence=STOCK_COLORS
    )
    
    fig = apply_chart_style(fig, title="市盈率(PE-TTM)走势")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='PE-TTM',
        legend_title='股票',
        hovermode='x unified'
    )
    
    return fig


def plot_pb_timeseries(df: pd.DataFrame, ts_codes: list = None, name_map: dict = None):
    """
    PB时序图。
    """
    if df.empty or 'pb' not in df.columns:
        return None
    
    data = df.dropna(subset=['pb']).copy()
    if ts_codes:
        data = data[data['ts_code'].isin(ts_codes)]
    
    if data.empty:
        return None
    
    if name_map:
        data['stock_name'] = data['ts_code'].map(name_map)
    else:
        data['stock_name'] = data['ts_code']
    
    fig = px.line(
        data,
        x='trade_date',
        y='pb',
        color='stock_name',
        color_discrete_sequence=STOCK_COLORS
    )
    
    fig = apply_chart_style(fig, title="市净率(PB)走势")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='PB',
        legend_title='股票',
        hovermode='x unified'
    )
    
    return fig


def plot_valuation_boxplot(df: pd.DataFrame, metric: str = 'pe_ttm', name_map: dict = None):
    """
    估值指标箱线图对比。
    """
    if df.empty or metric not in df.columns:
        return None
    
    data = df.dropna(subset=[metric]).copy()
    if data.empty:
        return None
    
    if name_map:
        data['stock_name'] = data['ts_code'].map(name_map)
    else:
        data['stock_name'] = data['ts_code']
    
    metric_names = {
        'pe_ttm': '市盈率(PE-TTM)',
        'pb': '市净率(PB)',
        'turnover_rate': '换手率(%)'
    }
    
    fig = px.box(
        data,
        x='stock_name',
        y=metric,
        color='stock_name',
        color_discrete_sequence=STOCK_COLORS
    )
    
    fig = apply_chart_style(fig, title=f"{metric_names.get(metric, metric)}分布对比")
    fig.update_layout(
        xaxis_title='',
        yaxis_title=metric_names.get(metric, metric),
        showlegend=False
    )
    
    return fig


def plot_turnover_scatter(df: pd.DataFrame, ts_code: str, name_map: dict = None):
    """
    换手率与成交量散点图。
    """
    if df.empty:
        return None
    
    data = df[df['ts_code'] == ts_code].dropna(subset=['turnover_rate']).copy()
    if data.empty:
        return None
    
    stock_name = name_map.get(ts_code, ts_code) if name_map else ts_code
    
    fig = px.scatter(
        data,
        x='turnover_rate',
        y='close',
        color='trade_date',
        color_continuous_scale='Viridis',
        opacity=0.6
    )
    
    fig = apply_chart_style(fig, title=f"{stock_name} 换手率与价格关系")
    fig.update_layout(
        xaxis_title='换手率(%)',
        yaxis_title='收盘价',
        coloraxis_colorbar_title='日期'
    )
    
    return fig


def plot_market_cap_distribution(df: pd.DataFrame):
    """
    市值分布直方图。
    """
    if df.empty or 'total_mv_yi' not in df.columns:
        return None
    
    data = df.dropna(subset=['total_mv_yi']).copy()
    
    # 对数变换更好展示
    data['log_mv'] = np.log10(data['total_mv_yi'] + 1)
    
    fig = px.histogram(
        data,
        x='log_mv',
        nbins=50,
        color_discrete_sequence=[COLORS['primary']]
    )
    
    fig = apply_chart_style(fig, title="市值分布 (对数刻度)")
    fig.update_layout(
        xaxis_title='log10(总市值/亿元)',
        yaxis_title='股票数量'
    )
    
    return fig


# ============================================================================
# 第4层：行业分析与选股
# ============================================================================

def plot_industry_valuation(df_industry: pd.DataFrame):
    """
    行业估值对比柱状图。
    """
    if df_industry.empty:
        return None
    
    # 取PE中位数TOP20行业
    df = df_industry.dropna(subset=['PE中位数']).sort_values('PE中位数', ascending=True).head(25)
    
    fig = px.bar(
        df,
        x='PE中位数',
        y='行业',
        orientation='h',
        color='PE中位数',
        color_continuous_scale=[[0, '#4A90A4'], [1, '#D97757']]
    )
    
    fig = apply_chart_style(fig, title="行业PE中位数对比")
    fig.update_layout(
        xaxis_title='PE中位数',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    return fig


def plot_industry_correlation_heatmap(df_corr: pd.DataFrame):
    """
    行业相关性热力图。
    """
    if df_corr.empty:
        return None
    
    # 限制显示的行业数量
    if len(df_corr.columns) > 20:
        top_industries = df_corr.columns[:20]
        df_corr = df_corr.loc[top_industries, top_industries]
    
    fig = px.imshow(
        df_corr,
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#FFFFFF'], [1, '#4A90A4']],
        aspect='equal',
        zmin=-1,
        zmax=1,
        text_auto='.2f'
    )
    
    fig = apply_chart_style(fig, title="行业收益率相关性矩阵")
    fig.update_layout(coloraxis_colorbar_title='相关系数')
    
    return fig


def plot_risk_return_scatter(df_stats: pd.DataFrame, name_map: dict = None, color_by: str = None):
    """
    风险-收益散点图。
    """
    if df_stats.empty:
        return None
    
    df = df_stats.dropna(subset=['ann_return', 'ann_volatility']).copy()
    if df.empty:
        return None
    
    if name_map:
        df['stock_name'] = df['ts_code'].map(name_map)
    else:
        df['stock_name'] = df['ts_code']
    
    fig = px.scatter(
        df,
        x='ann_volatility',
        y='ann_return',
        text='stock_name',
        color='sharpe' if 'sharpe' in df.columns else None,
        size='count' if 'count' in df.columns else None,
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#E8A838'], [1, '#6BBF59']],
        hover_data=['ts_code', 'sharpe'] if 'sharpe' in df.columns else ['ts_code']
    )
    
    # 添加参考线
    fig.add_hline(y=0, line_dash='dash', line_color='#888888', line_width=1)
    fig.add_vline(x=0, line_dash='dash', line_color='#888888', line_width=1)
    
    fig.update_traces(textposition='top center', textfont_size=9)
    
    fig = apply_chart_style(fig, title="风险-收益分析")
    fig.update_layout(
        xaxis_title='年化波动率 (风险)',
        yaxis_title='年化收益率',
        xaxis_tickformat='.0%',
        yaxis_tickformat='.0%',
        coloraxis_colorbar_title='夏普比率'
    )
    
    return fig


def plot_industry_returns_heatmap(df_industry_daily: pd.DataFrame):
    """
    行业月度收益热力图。
    """
    if df_industry_daily.empty:
        return None
    
    df = df_industry_daily.copy()
    df['year_month'] = df['trade_date'].dt.to_period('M')
    
    # 按行业和月份聚合
    monthly = df.groupby(['industry', 'year_month'])['avg_return'].sum().reset_index()
    monthly['month'] = monthly['year_month'].astype(str)
    
    # 透视
    pivot = monthly.pivot_table(index='industry', columns='month', values='avg_return', aggfunc='first')
    
    # 限制行业数量
    if len(pivot) > 20:
        pivot = pivot.head(20)
    
    fig = px.imshow(
        pivot * 100,
        color_continuous_scale='RdYlGn',
        aspect='auto',
        text_auto='.1f'
    )
    
    fig = apply_chart_style(fig, title="行业月度收益率(%)")
    fig.update_layout(coloraxis_colorbar_title='收益率%')
    
    return fig
