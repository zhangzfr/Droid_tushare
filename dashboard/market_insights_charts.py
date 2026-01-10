"""
市场洞察图表模块
===============
中文界面的Plotly可视化函数，用于市场估值、情绪和全球比较分析。
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

PALETTE = [
    '#D97757', '#4A90A4', '#6BBF59', '#E8A838', '#8B7355',
    '#C75B5B', '#7B68EE', '#20B2AA', '#FF6B6B', '#4ECDC4',
    '#9B59B6', '#3498DB', '#E74C3C', '#2ECC71', '#F39C12'
]


def apply_chart_style(fig, title=None):
    """应用统一图表样式"""
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
        legend=dict(bgcolor='rgba(255,255,255,0.9)', borderwidth=0, font=dict(size=11)),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E8E0D8', showline=True, linewidth=1, linecolor='#E8E0D8'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#E8E0D8', showline=True, linewidth=1, linecolor='#E8E0D8'),
        hoverlabel=dict(font_family="Inter, PingFang SC", font_size=12)
    )
    return fig


# ============================================================================
# 市场估值分析
# ============================================================================

def plot_pe_trend(df: pd.DataFrame, ts_codes: list = None):
    """
    各板块PE走势对比图。
    """
    if df.empty:
        return None
    
    data = df.dropna(subset=['pe']).copy()
    if ts_codes:
        data = data[data['ts_code'].isin(ts_codes)]
    
    if data.empty:
        return None
    
    # 使用中文名称
    name_col = 'market_name' if 'market_name' in data.columns else 'ts_name'
    
    fig = px.line(
        data,
        x='trade_date',
        y='pe',
        color=name_col,
        color_discrete_sequence=PALETTE
    )
    
    fig = apply_chart_style(fig, title="A股各板块PE走势")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='市盈率 (PE)',
        legend_title='板块',
        hovermode='x unified'
    )
    
    return fig


def plot_pe_percentile_gauge(percentile: float, current_pe: float, title: str = "PE历史分位"):
    """
    PE分位数仪表盘。
    """
    # 根据分位数决定颜色
    if percentile < 30:
        color = COLORS['success']
        level = "低估"
    elif percentile < 70:
        color = COLORS['warning']
        level = "适中"
    else:
        color = COLORS['danger']
        level = "高估"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=percentile,
        title={'text': f"{title}<br><span style='font-size:0.8em;color:gray'>当前PE: {current_pe:.1f}</span>"},
        number={'suffix': '%', 'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 30], 'color': '#E8F5E9'},
                {'range': [30, 70], 'color': '#FFF8E1'},
                {'range': [70, 100], 'color': '#FFEBEE'}
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 2},
                'thickness': 0.75,
                'value': percentile
            }
        }
    ))
    
    fig.update_layout(
        font_family="Inter, PingFang SC",
        height=280,
        margin=dict(l=30, r=30, t=80, b=30)
    )
    
    return fig


def plot_pe_comparison_bar(df: pd.DataFrame, date: str = None):
    """
    各板块PE对比柱状图。
    """
    if df.empty:
        return None
    
    if date:
        data = df[df['trade_date'] == pd.to_datetime(date)]
    else:
        data = df.groupby('ts_code').last().reset_index()
    
    data = data.dropna(subset=['pe']).copy()
    if data.empty:
        return None
    
    name_col = 'market_name' if 'market_name' in data.columns else 'ts_name'
    data = data.sort_values('pe', ascending=True)
    
    fig = px.bar(
        data,
        x='pe',
        y=name_col,
        orientation='h',
        color='pe',
        color_continuous_scale=[[0, '#6BBF59'], [0.5, '#E8A838'], [1, '#C75B5B']]
    )
    
    fig = apply_chart_style(fig, title="各板块PE对比")
    fig.update_layout(
        xaxis_title='市盈率 (PE)',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    return fig


# ============================================================================
# 市场情绪分析
# ============================================================================

def plot_amount_trend(df: pd.DataFrame, ts_code: str):
    """
    成交额走势图（带均线）。
    """
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return None
    
    data = data.sort_values('trade_date')
    data['amount_ma20'] = data['amount'].rolling(20).mean()
    data['amount_ma60'] = data['amount'].rolling(60).mean()
    
    fig = go.Figure()
    
    # 成交额柱状图
    fig.add_trace(go.Bar(
        x=data['trade_date'],
        y=data['amount'],
        name='成交额',
        marker_color='rgba(74, 144, 164, 0.5)'
    ))
    
    # 均线
    fig.add_trace(go.Scatter(
        x=data['trade_date'],
        y=data['amount_ma20'],
        name='20日均值',
        line=dict(color=COLORS['primary'], width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=data['trade_date'],
        y=data['amount_ma60'],
        name='60日均值',
        line=dict(color=COLORS['warning'], width=2)
    ))
    
    fig = apply_chart_style(fig, title="成交额走势 (亿元)")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='成交额 (亿元)',
        barmode='overlay',
        hovermode='x unified'
    )
    
    return fig


def plot_turnover_heatmap(df: pd.DataFrame, ts_code: str):
    """
    换手率月度热力图。
    """
    data = df[df['ts_code'] == ts_code].dropna(subset=['tr']).copy()
    if data.empty:
        return None
    
    data['year'] = data['trade_date'].dt.year
    data['month'] = data['trade_date'].dt.month
    
    # 按年月聚合
    monthly = data.groupby(['year', 'month'])['tr'].mean().reset_index()
    pivot = monthly.pivot(index='year', columns='month', values='tr')
    
    # 月份名称
    month_names = ['1月', '2月', '3月', '4月', '5月', '6月', 
                   '7月', '8月', '9月', '10月', '11月', '12月']
    pivot.columns = [month_names[i-1] for i in pivot.columns]
    
    fig = px.imshow(
        pivot,
        color_continuous_scale='YlOrRd',
        aspect='auto',
        text_auto='.1f'
    )
    
    fig = apply_chart_style(fig, title="换手率月度热力图 (%)")
    fig.update_layout(coloraxis_colorbar_title='换手率%')
    
    return fig


def plot_volume_price_scatter(df: pd.DataFrame, ts_code: str):
    """
    量价关系散点图。
    """
    data = df[df['ts_code'] == ts_code].dropna(subset=['amount', 'pe']).copy()
    if data.empty or len(data) < 10:
        return None
    
    # 计算PE变化
    data['pe_change'] = data['pe'].pct_change()
    data = data.dropna(subset=['pe_change'])
    
    fig = px.scatter(
        data,
        x='amount',
        y='pe_change',
        color='trade_date',
        color_continuous_scale='Viridis',
        opacity=0.6
    )
    
    # 添加趋势线
    fig.add_trace(go.Scatter(
        x=[data['amount'].min(), data['amount'].max()],
        y=[0, 0],
        mode='lines',
        line=dict(color='gray', dash='dash'),
        showlegend=False
    ))
    
    fig = apply_chart_style(fig, title="成交额与PE变化关系")
    fig.update_layout(
        xaxis_title='成交额 (亿元)',
        yaxis_title='PE变化率',
        yaxis_tickformat='.1%',
        coloraxis_colorbar_title='日期'
    )
    
    return fig


# ============================================================================
# 全球市场比较
# ============================================================================

def plot_global_indices_comparison(df_pivot: pd.DataFrame):
    """
    全球指数走势对比（归一化）。
    """
    if df_pivot.empty:
        return None
    
    fig = px.line(
        df_pivot.reset_index(),
        x='trade_date',
        y=df_pivot.columns.tolist(),
        color_discrete_sequence=PALETTE
    )
    
    fig = apply_chart_style(fig, title="全球主要指数走势对比 (归一化)")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='指数 (起点=100)',
        legend_title='指数',
        hovermode='x unified'
    )
    
    return fig


def plot_global_indices_raw(df: pd.DataFrame):
    """
    全球指数原始价格走势（不归一化）。
    使用子图展示不同量级的指数。
    """
    if df.empty:
        return None
    
    # 按指数分组
    indices = df['index_name'].unique()
    n_indices = len(indices)
    
    if n_indices == 0:
        return None
    
    # 创建子图
    rows = (n_indices + 1) // 2
    fig = make_subplots(
        rows=rows, cols=2,
        subplot_titles=list(indices),
        vertical_spacing=0.08,
        horizontal_spacing=0.08
    )
    
    for i, idx_name in enumerate(indices):
        row = i // 2 + 1
        col = i % 2 + 1
        data = df[df['index_name'] == idx_name].sort_values('trade_date')
        
        fig.add_trace(
            go.Scatter(
                x=data['trade_date'],
                y=data['close'],
                mode='lines',
                name=idx_name,
                line=dict(color=PALETTE[i % len(PALETTE)], width=1.5),
                showlegend=False
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        title=dict(text="全球指数原始价格走势", font=dict(size=18)),
        font_family="Inter, PingFang SC",
        height=max(400, rows * 200),
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def plot_global_volume(df: pd.DataFrame):
    """
    全球指数成交量对比。
    """
    if df.empty or 'vol' not in df.columns:
        return None
    
    # 筛选有成交量数据的指数
    vol_data = df.dropna(subset=['vol'])
    if vol_data.empty:
        return None
    
    # 获取每个指数最新一段时间的平均成交量用于柱状图
    latest = vol_data.groupby('index_name').agg({
        'vol': 'mean',
        'ts_code': 'first'
    }).reset_index()
    latest = latest.sort_values('vol', ascending=True)
    
    fig = px.bar(
        latest,
        x='vol',
        y='index_name',
        orientation='h',
        color='vol',
        color_continuous_scale='Blues'
    )
    
    fig = apply_chart_style(fig, title="全球指数平均成交量对比")
    fig.update_layout(
        xaxis_title='平均成交量',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    return fig


def plot_global_volume_trend(df: pd.DataFrame):
    """
    全球指数成交量走势。
    """
    if df.empty or 'vol' not in df.columns:
        return None
    
    # 筛选有成交量数据的指数
    vol_data = df.dropna(subset=['vol']).copy()
    if vol_data.empty:
        return None
    
    fig = px.line(
        vol_data,
        x='trade_date',
        y='vol',
        color='index_name',
        color_discrete_sequence=PALETTE
    )
    
    fig = apply_chart_style(fig, title="全球指数成交量走势")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='成交量',
        legend_title='指数',
        hovermode='x unified'
    )
    
    return fig


def plot_global_correlation_heatmap(df_corr: pd.DataFrame):
    """
    全球指数相关性热力图。
    """
    if df_corr.empty:
        return None
    
    fig = px.imshow(
        df_corr,
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#FFFFFF'], [1, '#4A90A4']],
        aspect='equal',
        zmin=-1,
        zmax=1,
        text_auto='.2f'
    )
    
    fig = apply_chart_style(fig, title="全球指数收益率相关性矩阵")
    fig.update_layout(coloraxis_colorbar_title='相关系数')
    
    return fig


def plot_index_returns_bar(df_stats: pd.DataFrame):
    """
    全球指数收益对比柱状图。
    """
    if df_stats.empty:
        return None
    
    df = df_stats.sort_values('total_return', ascending=True).copy()
    
    # 颜色：正收益绿，负收益红
    colors = [COLORS['success'] if x >= 0 else COLORS['danger'] for x in df['total_return']]
    
    fig = px.bar(
        df,
        x='total_return',
        y='index_name',
        orientation='h',
        color='total_return',
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#FFFFFF'], [1, '#6BBF59']]
    )
    
    fig = apply_chart_style(fig, title="全球指数区间收益对比")
    fig.update_layout(
        xaxis_title='累计收益率',
        yaxis_title='',
        xaxis_tickformat='.1%',
        coloraxis_showscale=False
    )
    
    return fig


def plot_risk_return_global(df_stats: pd.DataFrame):
    """
    全球指数风险收益散点图。
    """
    if df_stats.empty:
        return None
    
    # 创建副本，计算用于显示的size列（必须为正数）
    df = df_stats.copy()
    # 使用绝对值+偏移确保size为正且有意义
    df['size_value'] = df['sharpe_ratio'].abs() + 0.5
    
    fig = px.scatter(
        df,
        x='ann_volatility',
        y='ann_return',
        text='index_name',
        size='size_value',
        size_max=30,
        color='sharpe_ratio',
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#E8A838'], [1, '#6BBF59']]
    )
    
    # 添加参考线
    fig.add_hline(y=0, line_dash='dash', line_color='gray', line_width=1)
    
    fig.update_traces(textposition='top center', textfont_size=10)
    
    fig = apply_chart_style(fig, title="全球指数风险-收益分析")
    fig.update_layout(
        xaxis_title='年化波动率 (风险)',
        yaxis_title='年化收益率',
        xaxis_tickformat='.0%',
        yaxis_tickformat='.0%',
        coloraxis_colorbar_title='夏普比率'
    )
    
    return fig


def plot_market_mv_trend(df: pd.DataFrame, ts_codes: list = None):
    """
    市场总市值走势。
    """
    if df.empty:
        return None
    
    data = df.dropna(subset=['total_mv']).copy()
    if ts_codes:
        data = data[data['ts_code'].isin(ts_codes)]
    
    if data.empty:
        return None
    
    name_col = 'market_name' if 'market_name' in data.columns else 'ts_name'
    
    fig = px.area(
        data,
        x='trade_date',
        y='total_mv',
        color=name_col,
        color_discrete_sequence=PALETTE
    )
    
    fig = apply_chart_style(fig, title="各板块总市值走势 (亿元)")
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='总市值 (亿元)',
        legend_title='板块',
        hovermode='x unified'
    )
    
    return fig
