"""
AA-Share Market Education Chart Module
==================
For English UIPlotly交互式图表函数。
Organized by four learning levels。
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ============================================================================
# Color Scheme
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

# Multi-asset Color Sequence
STOCK_COLORS = [
    '#D97757', '#4A90A4', '#6BBF59', '#E8A838', '#8B7355',
    '#C75B5B', '#7B68EE', '#20B2AA', '#FF6B6B', '#4ECDC4',
    '#9B59B6', '#3498DB', '#E74C3C', '#2ECC71', '#F39C12'
]

# IndustryColors (Shenwan Level 1)
INDUSTRY_COLORS = px.colors.qualitative.Set3


def apply_chart_style(fig, title=None):
    """Apply unified chart style。"""
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
# Level 1：Understanding A-Share
# ============================================================================

def plot_market_pie(market_counts: dict):
    """
    Sector Distribution Pie Chart。
    """
    if not market_counts:
        return None
    
    df = pd.DataFrame(list(market_counts.items()), columns=['Sector', 'Count'])
    
    fig = px.pie(
        df,
        values='Count',
        names='Sector',
        color_discrete_sequence=STOCK_COLORS,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='outside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig = apply_chart_style(fig, title="A-ShareSector分布")
    fig.update_layout(legend=dict(orientation='h', yanchor='bottom', y=-0.15))
    
    return fig


def plot_status_pie(df_basic: pd.DataFrame):
    """
    Listing Status Distribution Pie Chart。
    """
    if df_basic.empty:
        return None
    
    counts = df_basic['status_name'].value_counts().reset_index()
    counts.columns = ['Status', 'Count']
    
    fig = px.pie(
        counts,
        values='Count',
        names='Status',
        color_discrete_sequence=[COLORS['success'], COLORS['danger'], COLORS['warning']],
        hole=0.4
    )
    
    fig.update_traces(textposition='outside', textinfo='label+percent')
    fig = apply_chart_style(fig, title="上市Status分布")
    
    return fig


def plot_industry_bar(industry_counts: dict, top_n: int = 20):
    """
    Industry Distribution Bar Chart。
    """
    if not industry_counts:
        return None
    
    df = pd.DataFrame(list(industry_counts.items()), columns=['Industry', 'Count'])
    df = df.sort_values('Count', ascending=True).tail(top_n)
    
    fig = px.bar(
        df,
        x='Count',
        y='Industry',
        orientation='h',
        color='Count',
        color_continuous_scale=[[0, COLORS['accent']], [1, COLORS['primary']]]
    )
    
    fig = apply_chart_style(fig, title=f"Industry分布 TOP{top_n}")
    fig.update_layout(
        coloraxis_showscale=False,
        yaxis_title='',
        xaxis_title='Listed CompaniesCount'
    )
    
    return fig


def plot_area_bar(area_counts: dict, top_n: int = 15):
    """
    Region Distribution Bar Chart。
    """
    if not area_counts:
        return None
    
    df = pd.DataFrame(list(area_counts.items()), columns=['Province', 'Count'])
    df = df.sort_values('Count', ascending=True).tail(top_n)
    
    fig = px.bar(
        df,
        x='Count',
        y='Province',
        orientation='h',
        color='Count',
        color_continuous_scale=[[0, '#4A90A4'], [1, '#D97757']]
    )
    
    fig = apply_chart_style(fig, title=f"Region Distribution TOP{top_n}")
    fig.update_layout(coloraxis_showscale=False, yaxis_title='', xaxis_title='Listed CompaniesCount')
    
    return fig


# ============================================================================
# 2：Stock
# ============================================================================

def plot_candlestick(df: pd.DataFrame, ts_code: str, name_map: dict = None):
    """
    KLine Chart。
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
        increasing_line_color=COLORS['danger'],  # 
        decreasing_line_color=COLORS['success'],  # 
        name=stock_name
    )])
    
    fig = apply_chart_style(fig, title=f"{stock_name} KLine Chart")
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return fig


def plot_price_lines(df_pivot: pd.DataFrame, normalize: bool = True, name_map: dict = None):
    """
    Multi-Stock Price Trend Comparison。
    """
    if df_pivot.empty:
        return None
    
    if normalize:
        df_plot = df_pivot / df_pivot.iloc[0] * 100
        y_title = 'Normalized Price (First Day=100)'
    else:
        df_plot = df_pivot
        y_title = 'Closing Price'
    
    # Rename columns
    if name_map:
        df_plot.columns = [name_map.get(c, c) for c in df_plot.columns]
    
    fig = px.line(
        df_plot.reset_index(),
        x='trade_date',
        y=df_plot.columns.tolist(),
        color_discrete_sequence=STOCK_COLORS
    )
    
    fig = apply_chart_style(fig, title="Stock Price Trend Comparison")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title=y_title,
        legend_title='Stock',
        hovermode='x unified'
    )
    
    return fig


def plot_return_distribution(df: pd.DataFrame, ts_code: str = None, name_map: dict = None):
    """
    Return Distribution Histogram。
    """
    if df.empty or 'return' not in df.columns:
        return None
    
    data = df.dropna(subset=['return']).copy()
    if ts_code:
        data = data[data['ts_code'] == ts_code]
    
    if data.empty:
        return None
    
    # Map names
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
    
    fig = apply_chart_style(fig, title="Daily Return Distribution")
    fig.update_layout(
        xaxis_title='Daily Return',
        yaxis_title='Frequency',
        xaxis_tickformat='.1%',
        barmode='overlay'
    )
    
    return fig


def plot_volatility_comparison(df_stats: pd.DataFrame, name_map: dict = None):
    """
    Volatility Comparison Bar Chart。
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
    
    fig = apply_chart_style(fig, title="Annualized Volatility Comparison")
    fig.update_layout(
        xaxis_title='Annualized Volatility',
        yaxis_title='',
        xaxis_tickformat='.0%',
        coloraxis_showscale=False
    )
    
    return fig


# ============================================================================
# 3：
# ============================================================================

def plot_pe_timeseries(df: pd.DataFrame, ts_codes: list = None, name_map: dict = None):
    """
    PETime Series Chart。
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
    
    fig = apply_chart_style(fig, title="P/E Ratio(PE-TTM)Trend")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='PE-TTM',
        legend_title='Stock',
        hovermode='x unified'
    )
    
    return fig


def plot_pb_timeseries(df: pd.DataFrame, ts_codes: list = None, name_map: dict = None):
    """
    PBTime Series Chart。
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
    
    fig = apply_chart_style(fig, title="P/B Ratio(PB)Trend")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='PB',
        legend_title='Stock',
        hovermode='x unified'
    )
    
    return fig


def plot_valuation_boxplot(df: pd.DataFrame, metric: str = 'pe_ttm', name_map: dict = None):
    """
    估值指标箱Line Chart对比。
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
        'pe_ttm': 'P/E Ratio(PE-TTM)',
        'pb': 'P/B Ratio(PB)',
        'turnover_rate': 'Turnover Rate(%)'
    }
    
    fig = px.box(
        data,
        x='stock_name',
        y=metric,
        color='stock_name',
        color_discrete_sequence=STOCK_COLORS
    )
    
    fig = apply_chart_style(fig, title=f"{metric_names.get(metric, metric)}Distribution Comparison")
    fig.update_layout(
        xaxis_title='',
        yaxis_title=metric_names.get(metric, metric),
        showlegend=False
    )
    
    return fig


def plot_turnover_scatter(df: pd.DataFrame, ts_code: str, name_map: dict = None):
    """
    Turnover Rate与成交量散点图。
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
    
    fig = apply_chart_style(fig, title=f"{stock_name} Turnover Ratevs Price")
    fig.update_layout(
        xaxis_title='Turnover Rate(%)',
        yaxis_title='Closing Price',
        coloraxis_colorbar_title='Date'
    )
    
    return fig


def plot_market_cap_distribution(df: pd.DataFrame):
    """
    Market Cap Distribution Histogram。
    """
    if df.empty or 'total_mv_yi' not in df.columns:
        return None
    
    data = df.dropna(subset=['total_mv_yi']).copy()
    
    # Log transformation for better display
    data['log_mv'] = np.log10(data['total_mv_yi'] + 1)
    
    fig = px.histogram(
        data,
        x='log_mv',
        nbins=50,
        color_discrete_sequence=[COLORS['primary']]
    )
    
    fig = apply_chart_style(fig, title="Market Cap Distribution (Log Scale)")
    fig.update_layout(
        xaxis_title='log10(Total Market Cap/100M CNY)',
        yaxis_title='StockCount'
    )
    
    return fig


# ============================================================================
# 4：Industry
# ============================================================================

def plot_industry_valuation(df_industry: pd.DataFrame):
    """
    IndustryValuation Comparison Bar Chart。
    """
    if df_industry.empty:
        return None
    
    df = df_industry.copy()

    # Normalize column names (loader returns中文列名)
    if 'PEMedian' not in df.columns and 'PE中位数' in df.columns:
        df = df.rename(columns={'PE中位数': 'PEMedian'})
    if 'Industry' not in df.columns and '行业' in df.columns:
        df = df.rename(columns={'行业': 'Industry'})

    if 'PEMedian' not in df.columns or 'Industry' not in df.columns:
        return None

    # PEMedianTOP20Industry
    df = df.dropna(subset=['PEMedian']).sort_values('PEMedian', ascending=True).head(25)
    
    fig = px.bar(
        df,
        x='PEMedian',
        y='Industry',
        orientation='h',
        color='PEMedian',
        color_continuous_scale=[[0, '#4A90A4'], [1, '#D97757']]
    )
    
    fig = apply_chart_style(fig, title="IndustryPEMedian对比")
    fig.update_layout(
        xaxis_title='PEMedian',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    return fig


def plot_industry_correlation_heatmap(df_corr: pd.DataFrame):
    """
    IndustryCorrelation Heatmap。
    """
    if df_corr.empty:
        return None
    
    # IndustryCount
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
    
    fig = apply_chart_style(fig, title="IndustryReturnCorrelation Matrix")
    fig.update_layout(coloraxis_colorbar_title='Correlation Coefficient')
    
    return fig


def plot_risk_return_scatter(df_stats: pd.DataFrame, name_map: dict = None, color_by: str = None):
    """
    风险-Return Scatter Plot。
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
    
    # Add reference line
    fig.add_hline(y=0, line_dash='dash', line_color='#888888', line_width=1)
    fig.add_vline(x=0, line_dash='dash', line_color='#888888', line_width=1)
    
    fig.update_traces(textposition='top center', textfont_size=9)
    
    fig = apply_chart_style(fig, title="风险-ReturnAnalysis")
    fig.update_layout(
        xaxis_title='Annualized Volatility (风险)',
        yaxis_title='Annualized Return',
        xaxis_tickformat='.0%',
        yaxis_tickformat='.0%',
        coloraxis_colorbar_title='Sharpe Ratio'
    )
    
    return fig


def plot_industry_returns_heatmap(df_industry_daily: pd.DataFrame):
    """
    IndustryMonthly Return Heatmap。
    """
    if df_industry_daily.empty:
        return None
    
    df = df_industry_daily.copy()
    df['year_month'] = df['trade_date'].dt.to_period('M')
    
    # Industry
    monthly = df.groupby(['industry', 'year_month'])['avg_return'].sum().reset_index()
    monthly['month'] = monthly['year_month'].astype(str)
    
    # Pivot
    pivot = monthly.pivot_table(index='industry', columns='month', values='avg_return', aggfunc='first')
    
    # IndustryCount
    if len(pivot) > 20:
        pivot = pivot.head(20)
    
    fig = px.imshow(
        pivot * 100,
        color_continuous_scale='RdYlGn',
        aspect='auto',
        text_auto='.1f'
    )
    
    fig = apply_chart_style(fig, title="Industry月度Return(%)")
    fig.update_layout(coloraxis_colorbar_title='Return%')
    
    return fig
