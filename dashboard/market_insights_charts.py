"""
Market Insights Chart Module
===============
Plotly visualization functions for market valuation, sentiment, and global comparison analysis.
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

PALETTE = [
    '#D97757', '#4A90A4', '#6BBF59', '#E8A838', '#8B7355',
    '#C75B5B', '#7B68EE', '#20B2AA', '#FF6B6B', '#4ECDC4',
    '#9B59B6', '#3498DB', '#E74C3C', '#2ECC71', '#F39C12'
]


def apply_chart_style(fig, title=None):
    """Apply unified chart style"""
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
# Market Valuation Analysis
# ============================================================================

def plot_pe_trend(df: pd.DataFrame, ts_codes: list = None):
    """
    PE Trend Comparison by Sector。
    """
    if df.empty:
        return None
    
    data = df.dropna(subset=['pe']).copy()
    if ts_codes:
        data = data[data['ts_code'].isin(ts_codes)]
    
    if data.empty:
        return None
    
    # Use display name
    name_col = 'market_name' if 'market_name' in data.columns else 'ts_name'
    
    fig = px.line(
        data,
        x='trade_date',
        y='pe',
        color=name_col,
        color_discrete_sequence=PALETTE
    )
    
    fig = apply_chart_style(fig, title="A-Share Sector PE Trend")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='P/E Ratio',
        legend_title='Sector',
        hovermode='x unified'
    )
    
    return fig


def plot_pe_percentile_gauge(percentile: float, current_pe: float, title: str = "PE Historical Percentile"):
    """
    PE Percentile Dashboard。
    """
    # Determine color based on percentile
    if percentile < 30:
        color = COLORS['success']
        level = "Undervalued"
    elif percentile < 70:
        color = COLORS['warning']
        level = "Fair Value"
    else:
        color = COLORS['danger']
        level = "Overvalued"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=percentile,
        title={'text': f"{title}<br><span style='font-size:0.8em;color:gray'>CurrentPE: {current_pe:.1f}</span>"},
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
    各SectorPEComparison Bar Chart。
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
    
    fig = apply_chart_style(fig, title="各SectorPE对比")
    fig.update_layout(
        xaxis_title='P/E Ratio',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    return fig


# ============================================================================
# Market Sentiment Analysis
# ============================================================================

def plot_amount_trend(df: pd.DataFrame, ts_code: str):
    """
    Trading AmountTrend图（带Moving Average）。
    """
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return None
    
    data = data.sort_values('trade_date')
    data['amount_ma20'] = data['amount'].rolling(20).mean()
    data['amount_ma60'] = data['amount'].rolling(60).mean()
    
    fig = go.Figure()
    
    # Trading Amount Bar Chart
    fig.add_trace(go.Bar(
        x=data['trade_date'],
        y=data['amount'],
        name='Trading Amount',
        marker_color='rgba(74, 144, 164, 0.5)'
    ))
    
    # Moving Average
    fig.add_trace(go.Scatter(
        x=data['trade_date'],
        y=data['amount_ma20'],
        name='20Daily Average',
        line=dict(color=COLORS['primary'], width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=data['trade_date'],
        y=data['amount_ma60'],
        name='60Daily Average',
        line=dict(color=COLORS['warning'], width=2)
    ))
    
    fig = apply_chart_style(fig, title="Trading AmountTrend (100M CNY)")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Trading Amount (100M CNY)',
        barmode='overlay',
        hovermode='x unified'
    )
    
    return fig


def plot_turnover_heatmap(df: pd.DataFrame, ts_code: str):
    """
    Monthly Turnover Heatmap。
    """
    data = df[df['ts_code'] == ts_code].dropna(subset=['tr']).copy()
    if data.empty:
        return None
    
    data['year'] = data['trade_date'].dt.year
    data['month'] = data['trade_date'].dt.month
    
    # Aggregate by year-month
    monthly = data.groupby(['year', 'month'])['tr'].mean().reset_index()
    pivot = monthly.pivot(index='year', columns='month', values='tr')
    
    # Month Name
    month_names = ['1Month', '2Month', '3Month', '4Month', '5Month', '6Month', 
                   '7Month', '8Month', '9Month', '10Month', '11Month', '12Month']
    pivot.columns = [month_names[i-1] for i in pivot.columns]
    
    fig = px.imshow(
        pivot,
        color_continuous_scale='YlOrRd',
        aspect='auto',
        text_auto='.1f'
    )
    
    fig = apply_chart_style(fig, title="Monthly Turnover Heatmap (%)")
    fig.update_layout(coloraxis_colorbar_title='Turnover Rate%')
    
    return fig


# ============================================================================
# Options Data Analysis
# ============================================================================

def plot_opt_distribution_heatmap(df: pd.DataFrame, metric: str = 'oi'):
    """
    Option Contract Distribution Heatmap (Strike Price vs Month).
    
    Args:
        df: DataFrame with columns [exercise_price, s_month, oi/vol]
        metric: 'oi' (Open Interest) or 'vol' (Volume)
    """
    if df.empty:
        return None
    
    data = df.copy()
    
    # Filter valid data
    if metric not in data.columns:
        return None
        
    pivot = data.pivot_table(
        index='exercise_price',
        columns='s_month',
        values=metric,
        aggfunc='sum'
    ).fillna(0)
    
    if pivot.empty:
        return None
        
    # Heatmap
    fig = px.imshow(
        pivot,
        color_continuous_scale='Reds' if metric == 'vol' else 'Blues',
        aspect='auto',
        text_auto='.0f' if metric == 'oi' else '.0f'
    )
    
    metric_name = "Open Interest (OI)" if metric == 'oi' else "Volume"
    title = f"Options {metric_name} Heatmap (Strike vs Maturity)"
    
    fig = apply_chart_style(fig, title=title)
    fig.update_layout(
        xaxis_title='Maturity Month',
        yaxis_title='Strike Price',
        coloraxis_colorbar_title=metric_name if metric != 'cnt' else 'Count'
    )
    
    return fig


def plot_opt_trend(df: pd.DataFrame, ts_code: str):
    """
    Option Price/Volume/OI Trend.
    """
    if df.empty:
        return None
        
    data = df.sort_values('trade_date').copy()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Close Price
    fig.add_trace(
        go.Scatter(
            x=data['trade_date'],
            y=data['close'],
            name="Close Price",
            line=dict(color=COLORS['primary'], width=2)
        ),
        secondary_y=False
    )
    
    # Open Interest (Area)
    if 'oi' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data['trade_date'],
                y=data['oi'],
                name="Open Interest (OI)",
                fill='tozeroy',
                line=dict(width=0),
                marker_color='rgba(180, 180, 180, 0.3)'
            ),
            secondary_y=True
        )
        
    # Volume (Bar)
    if 'vol' in data.columns:
        fig.add_trace(
            go.Bar(
                x=data['trade_date'],
                y=data['vol'],
                name="Volume",
                marker_color=COLORS['accent'],
                opacity=0.5
            ),
            secondary_y=True
        )
        
    fig = apply_chart_style(fig, title=f"Contract Trend ({ts_code})")
    
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.update_yaxes(title_text="Vol / OI", secondary_y=True)
    fig.update_xaxes(title_text="Date", tickformat='%Y%m%d')
    
    fig.update_layout(
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def plot_opt_liquidity_scatter(df: pd.DataFrame):
    """
    Option Liquidity Scatter (Strike vs OI vs Volume).
    """
    if df.empty:
        return None
        
    data = df.copy()
    
    # Ensure columns
    needed = ['exercise_price', 'oi', 'vol', 'call_put', 's_month']
    if not all(col in data.columns for col in needed):
        return None
        
    # Create scatter
    fig = px.scatter(
        data,
        x='exercise_price',
        y='oi',
        size='vol',
        color='call_put',
        hover_data=['s_month', 'ts_code'],
        color_discrete_map={'Call': COLORS['danger'], 'Put': COLORS['success'], 'C': COLORS['danger'], 'P': COLORS['success']},
        title="Liquidity Analysis (Strike vs OI vs Vol)"
    )
    
    fig = apply_chart_style(fig, title=None)
    fig.update_layout(
        xaxis_title='Strike Price',
        yaxis_title='Open Interest (OI)',
        legend_title='Type'
    )
    
    return fig


def plot_volume_price_scatter(df: pd.DataFrame, ts_code: str):
    """
    Volume-Price Scatter Plot。
    """
    data = df[df['ts_code'] == ts_code].dropna(subset=['amount', 'pe']).copy()
    if data.empty or len(data) < 10:
        return None
    
    # PEChange
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
    
    # Add trend line
    fig.add_trace(go.Scatter(
        x=[data['amount'].min(), data['amount'].max()],
        y=[0, 0],
        mode='lines',
        line=dict(color='gray', dash='dash'),
        showlegend=False
    ))
    
    fig = apply_chart_style(fig, title="Trading Amount vs PE Change")
    fig.update_layout(
        xaxis_title='Trading Amount (100M CNY)',
        yaxis_title='PE Change Rate',
        yaxis_tickformat='.1%',
        coloraxis_colorbar_title='Date'
    )
    
    return fig


# ============================================================================
# Global Market Comparison
# ============================================================================

def plot_global_indices_comparison(df_pivot: pd.DataFrame):
    """
    全球IndexTrend对比（Normalized）。
    """
    if df_pivot.empty:
        return None
    
    fig = px.line(
        df_pivot.reset_index(),
        x='trade_date',
        y=df_pivot.columns.tolist(),
        color_discrete_sequence=PALETTE
    )
    
    fig = apply_chart_style(fig, title="Major Global Index Trend Comparison (Normalized)")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Index (Starting Point=100)',
        legend_title='Index',
        hovermode='x unified'
    )
    
    return fig


def plot_global_indices_raw(df: pd.DataFrame):
    """
    全球Index原始PriceTrend（不Normalized）。
    Use Subplots for Different ScalesIndex。
    """
    if df.empty:
        return None
    
    # Indexpoints
    indices = df['index_name'].unique()
    n_indices = len(indices)
    
    if n_indices == 0:
        return None
    
    # Create subplot
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
        title=dict(text="Global Index Raw Price Trend", font=dict(size=18)),
        font_family="Inter, PingFang SC",
        height=max(400, rows * 200),
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def plot_global_volume(df: pd.DataFrame):
    """
    全球IndexVolume对比。
    """
    if df.empty or 'vol' not in df.columns:
        return None
    
    # VolumeIndex
    vol_data = df.dropna(subset=['vol'])
    if vol_data.empty:
        return None
    
    # IndexTimeAverage Volume
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
    
    fig = apply_chart_style(fig, title="Global Index Average Volume Comparison")
    fig.update_layout(
        xaxis_title='Average Volume',
        yaxis_title='',
        coloraxis_showscale=False
    )
    
    return fig


def plot_global_volume_trend(df: pd.DataFrame):
    """
    全球IndexVolumeTrend。
    """
    if df.empty or 'vol' not in df.columns:
        return None
    
    # VolumeIndex
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
    
    fig = apply_chart_style(fig, title="Global Index Volume Trend")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Volume',
        legend_title='Index',
        hovermode='x unified'
    )
    
    return fig


def plot_global_correlation_heatmap(df_corr: pd.DataFrame):
    """
    全球IndexCorrelation Heatmap。
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
    
    fig = apply_chart_style(fig, title="Global Index Return Correlation Matrix")
    fig.update_layout(coloraxis_colorbar_title='Correlation Coefficient')
    
    return fig


def plot_index_returns_bar(df_stats: pd.DataFrame):
    """
    全球IndexReturnComparison Bar Chart。
    """
    if df_stats.empty:
        return None
    
    df = df_stats.sort_values('total_return', ascending=True).copy()
    
    # Color: Green for positive, Red for negative returns
    colors = [COLORS['success'] if x >= 0 else COLORS['danger'] for x in df['total_return']]
    
    fig = px.bar(
        df,
        x='total_return',
        y='index_name',
        orientation='h',
        color='total_return',
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#FFFFFF'], [1, '#6BBF59']]
    )
    
    fig = apply_chart_style(fig, title="Global Index Period Return Comparison")
    fig.update_layout(
        xaxis_title='Cumulative Return',
        yaxis_title='',
        xaxis_tickformat='.1%',
        coloraxis_showscale=False
    )
    
    return fig


def plot_risk_return_global(df_stats: pd.DataFrame):
    """
    全球Index风险Return Scatter Plot。
    """
    if df_stats.empty:
        return None
    
    # ，size（）
    df = df_stats.copy()
    # +size
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
    
    # Add reference line
    fig.add_hline(y=0, line_dash='dash', line_color='gray', line_width=1)
    
    fig.update_traces(textposition='top center', textfont_size=10)
    
    fig = apply_chart_style(fig, title="Global Index Risk-Return Analysis")
    fig.update_layout(
        xaxis_title='Annualized Volatility (Risk)',
        yaxis_title='Annualized Return',
        xaxis_tickformat='.0%',
        yaxis_tickformat='.0%',
        coloraxis_colorbar_title='Sharpe Ratio'
    )
    
    return fig


def plot_market_mv_trend(df: pd.DataFrame, ts_codes: list = None):
    """
    Total Market Cap Trend。
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
    
    fig = apply_chart_style(fig, title="Total Market Cap Trend by Sector (100M CNY)")
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Total Market Cap (100M CNY)',
        legend_title='Sector',
        hovermode='x unified'
    )
    
    return fig


# ============================================================================
# Two-Market Trading Data Analysis
# ============================================================================

def plot_trading_amount_trend(df: pd.DataFrame, ts_codes: list = None):
    """
    Trading Amount与Turnover Rate双Y轴趋势图。
    """
    if df.empty:
        return None
    
    data = df.copy()
    if ts_codes:
        data = data[data['ts_code'].isin(ts_codes)]
    
    if data.empty:
        return None
    
    # Ensure required columns exist
    if 'amount' not in data.columns or ('tr' not in data.columns and 'amount_turnover' not in data.columns):
        return None
    
    name_col = 'market_name' if 'market_name' in data.columns else 'ts_name'
    
    # Create chart with secondary axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # SectorTrading Amount（）Turnover Rate（）
    colors = PALETTE
    
    for i, code in enumerate(data['ts_code'].unique()):
        code_data = data[data['ts_code'] == code].sort_values('trade_date')
        market_name = code_data[name_col].iloc[0] if not code_data[name_col].empty else code
        
        # Trading Amount（Y）
        fig.add_trace(
            go.Bar(
                x=code_data['trade_date'],
                y=code_data['amount'],
                name=f"{market_name} Trading Amount",
                marker_color=colors[i % len(colors)],
                opacity=0.6,
                showlegend=True
            ),
            secondary_y=False
        )
        
        # Turnover Rate（Y）
        if 'tr' in code_data.columns and not code_data['tr'].isna().all():
            fig.add_trace(
                go.Scatter(
                    x=code_data['trade_date'],
                    y=code_data['tr'],
                    name=f"{market_name} Turnover Rate",
                    line=dict(color=colors[i % len(colors)], width=2, dash='dash'),
                    showlegend=True
                ),
                secondary_y=True
            )
        elif 'amount_turnover' in code_data.columns and not code_data['amount_turnover'].isna().all():
            fig.add_trace(
                go.Scatter(
                    x=code_data['trade_date'],
                    y=code_data['amount_turnover'],
                    name=f"{market_name} AmountTurnover Rate",
                    line=dict(color=colors[i % len(colors)], width=2, dash='dash'),
                    showlegend=True
                ),
                secondary_y=True
            )
    
    # Set axis labels
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Trading Amount (100M CNY)', secondary_y=False)
    fig.update_yaxes(title_text='Turnover Rate (%)', secondary_y=True)
    
    # Apply style
    fig = apply_chart_style(fig, title="Trading Amount vs Turnover Rate Trend")
    fig.update_layout(
        barmode='group',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def plot_sh_sz_comparison(df: pd.DataFrame, date: str = None):
    """
    Shanghai vs ShenzhenComparison Bar Chart。
    """
    if df.empty:
        return None
    
    # Date
    if date:
        data = df[df['trade_date'] == pd.to_datetime(date)]
    else:
        data = df.groupby('ts_code').last().reset_index()
    
    if data.empty:
        return None
    
    # pointsShanghaiShenzhen（sz_daily_info  ts_code points， source ）
    if 'source' in data.columns:
        data['exchange'] = data.apply(
            lambda r: 'Shenzhen' if r.get('source') == 'sz_daily_info' else (
                'Shanghai' if 'SH' in str(r.get('ts_code', '')) else (
                    'Shenzhen' if 'SZ' in str(r.get('ts_code', '')) else '其他'
                )
            ),
            axis=1
        )
    else:
        data['exchange'] = data['ts_code'].apply(lambda x: 'Shanghai' if 'SH' in x else ('Shenzhen' if 'SZ' in x else '其他'))
    
    # Group by exchange
    exchange_data = data.groupby('exchange').agg({
        'amount': 'sum',
        'total_mv': 'sum',
        'float_mv': 'sum'
    }).reset_index()
    
    if exchange_data.empty:
        return None
    
    # Turnover Rate
    exchange_data['amount_turnover'] = exchange_data['amount'] / exchange_data['float_mv'] * 100
    
    # Create grouped bar chart
    fig = go.Figure()
    
    metrics = ['amount', 'total_mv', 'amount_turnover']
    metric_names = ['Trading Amount (100M CNY)', 'Total Market Cap (100M CNY)', 'AmountTurnover Rate (%)']
    colors = [COLORS['primary'], COLORS['accent'], COLORS['warning']]
    
    for i, (metric, name, color) in enumerate(zip(metrics, metric_names, colors)):
        fig.add_trace(go.Bar(
            x=exchange_data['exchange'],
            y=exchange_data[metric],
            name=name,
            marker_color=color,
            text=exchange_data[metric].apply(lambda x: f'{x:,.1f}'),
            textposition='auto'
        ))
    
    fig = apply_chart_style(fig, title="Shanghai vs Shenzhen Market Comparison")
    fig.update_layout(
        xaxis_title='Exchange',
        yaxis_title='Value',
        barmode='group',
        hovermode='x unified'
    )
    
    return fig


def plot_sector_heatmap(df: pd.DataFrame, metric: str = 'amount'):
    """
    Sector热力图，Show DifferentSectorAcross DifferentTime的热度。
    """
    if df.empty:
        return None
    
    data = df.copy()
    
    # YearMonth
    data['year'] = data['trade_date'].dt.year
    data['month'] = data['trade_date'].dt.month
    
    # Sector、YearMonth
    pivot = data.pivot_table(
        index='market_name',
        columns=['year', 'month'],
        values=metric,
        aggfunc='mean'
    )
    
    if pivot.empty:
        return None
    
    # Rename columns
    col_names = []
    for year, month in pivot.columns:
        col_names.append(f"{year}Year{month}Month")
    
    # Create heatmap
    fig = px.imshow(
        pivot,
        color_continuous_scale='YlOrRd',
        aspect='auto',
        text_auto='.1f'
    )
    
    fig = apply_chart_style(fig, title=f"Sector {metric} Heatmap")
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Sector'
    )
    
    return fig


def plot_risk_warning_box(df: pd.DataFrame, metric: str = 'tr'):
    """
    风险预警箱线图，显示Turnover Ratepoints布。
    """
    if df.empty:
        return None
    
    data = df.copy()
    
    # Month
    data['month'] = data['trade_date'].dt.month
    
    # Month Name
    month_names = ['1Month', '2Month', '3Month', '4Month', '5Month', '6Month', 
                   '7Month', '8Month', '9Month', '10Month', '11Month', '12Month']
    
    fig = px.box(
        data,
        x='month',
        y=metric,
        color='ts_code',
        points='outliers',
        category_orders={'month': list(range(1, 13))}
    )
    
    fig = apply_chart_style(fig, title=f"{metric} Monthly Distribution Box Plot")
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title=metric,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=month_names
        )
    )
    
    # Add threshold line
    if metric == 'tr':
        fig.add_hline(y=2, line_dash='dash', line_color='red', annotation_text='High Risk Threshold (2%)')
        fig.add_hline(y=0.5, line_dash='dash', line_color='green', annotation_text='Low Risk Threshold (0.5%)')
    
    return fig


def plot_liquidity_score_gauge(df: pd.DataFrame, ts_code: str):
    """
    Liquidity Score Dashboard。
    """
    if df.empty:
        return None
    
    data = df[df['ts_code'] == ts_code].copy()
    if data.empty:
        return None
    
    # Calculate Liquidity Score (Simple Example)
    latest = data.iloc[-1]
    
    # points：Trading Amount、Turnover Rate、
    amount_score = min(latest['amount'] / 1000 * 100, 100) if 'amount' in latest else 50  # Assume 100B CNY = full score
    
    if 'tr' in latest and not pd.isna(latest['tr']):
        turnover_score = min(latest['tr'] * 50, 100)  # 2%Turnover Ratepoints
    elif 'amount_turnover' in latest and not pd.isna(latest['amount_turnover']):
        turnover_score = min(latest['amount_turnover'] * 50, 100)
    else:
        turnover_score = 50
    
    if 'float_mv' in latest and not pd.isna(latest['float_mv']):
        market_cap_score = min(latest['float_mv'] / 50000 * 100, 100)  # 510T Circulating Market Cap = full score
    else:
        market_cap_score = 50
    
    # Combined Score
    liquidity_score = (amount_score * 0.5 + turnover_score * 0.3 + market_cap_score * 0.2)
    
    # Determine color
    if liquidity_score >= 70:
        color = COLORS['success']
        level = "Excellent"
    elif liquidity_score >= 40:
        color = COLORS['warning']
        level = "Good"
    else:
        color = COLORS['danger']
        level = "Fair"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=liquidity_score,
        title={'text': f"Liquidity Score<br><span style='font-size:0.8em;color:gray'>{level}</span>"},
        number={'suffix': 'points', 'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 40], 'color': '#FFEBEE'},
                {'range': [40, 70], 'color': '#FFF8E1'},
                {'range': [70, 100], 'color': '#E8F5E9'}
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 2},
                'thickness': 0.75,
                'value': liquidity_score
            }
        }
    ))
    
    fig.update_layout(
        font_family="Inter, PingFang SC",
        height=280,
        margin=dict(l=30, r=30, t=80, b=30)
    )
    
    return fig


def plot_market_turnover_scatter(df: pd.DataFrame):
    """
    Market Cap vsTurnover Rate散点图。
    """
    if df.empty:
        return None
    
    data = df.copy()
    
    # Use latest data
    latest = data.groupby('ts_code').last().reset_index()
    
    if latest.empty:
        return None
    
    # pointsShanghaiShenzhen（sz_daily_info  ts_code points， source ）
    if 'source' in latest.columns:
        latest['exchange'] = latest.apply(
            lambda r: 'Shenzhen' if r.get('source') == 'sz_daily_info' else (
                'Shanghai' if 'SH' in str(r.get('ts_code', '')) else (
                    'Shenzhen' if 'SZ' in str(r.get('ts_code', '')) else '其他'
                )
            ),
            axis=1
        )
    else:
        latest['exchange'] = latest['ts_code'].apply(lambda x: 'Shanghai' if 'SH' in x else ('Shenzhen' if 'SZ' in x else '其他'))
    
    # Turnover Rate
    if 'tr' in latest.columns and not latest['tr'].isna().all():
        turnover_col = 'tr'
    elif 'amount_turnover' in latest.columns and not latest['amount_turnover'].isna().all():
        turnover_col = 'amount_turnover'
    else:
        return None
    
    fig = px.scatter(
        latest,
        x='float_mv',
        y=turnover_col,
        color='exchange',
        size='amount',
        hover_name='market_name',
        color_discrete_map={'Shanghai': COLORS['primary'], 'Shenzhen': COLORS['accent']}
    )
    
    fig = apply_chart_style(fig, title="Market Cap vsTurnover Rate关系")
    fig.update_layout(
        xaxis_title='Circulating Market Cap (100M CNY)',
        yaxis_title='Turnover Rate (%)',
        hovermode='closest'
    )
    
    return fig

# ============================================================================
# Advanced Options Analytics (Requested by User)
# ============================================================================


# ============================================================================
# Advanced Options Analytics (Requested by User) -- Optimized English Version
# ============================================================================

def plot_opt_underlying_counts(df: pd.DataFrame, top_n: int = 50):
    """
    Top Underlyings by Number of Option Contracts (Bar Chart).
    """
    if df.empty or 'underlying' not in df.columns:
        return None
        
    counts = df.groupby('underlying')['ts_code'].count().sort_values(ascending=False).head(top_n).reset_index()
    counts.columns = ['underlying', 'total_contracts']
    
    fig = px.bar(
        counts,
        x='underlying',
        y='total_contracts',
        text='total_contracts',
        color='total_contracts',
        color_continuous_scale='Blues'
    )
    
    fig = apply_chart_style(fig, title=f"Total Contracts by Underlying (Top {top_n if 'top_n' in locals() else 20})")
    fig.update_layout(
        xaxis_title='Underlying Asset',
        yaxis_title='Total Contracts',
        coloraxis_showscale=False
    )
    
    return fig


def plot_opt_strike_distribution(df: pd.DataFrame):
    """
    Strike Price Distribution - Top 10 Underlyings.
    """
    if df.empty or 'underlying' not in df.columns or 'strike' not in df.columns:
        return None
        
    # Get Top 10
    top10 = df.groupby('underlying')['ts_code'].count().sort_values(ascending=False).head(10).index
    data = df[df['underlying'].isin(top10)].copy()
    
    if data.empty:
        return None
        
    fig = px.box(
        data,
        x='underlying',
        y='strike',
        color='call_put',
        color_discrete_map={'C': COLORS['danger'], 'P': COLORS['success']},
        notched=True
    )
    
    fig = apply_chart_style(fig, title="Strike Price Distribution (Top 10 Underlyings)")
    fig.update_layout(
        xaxis_title='Underlying Asset',
        yaxis_title='Strike Price',
        legend_title='Call/Put'
    )
    
    return fig


def plot_opt_maturity_heatmap(df: pd.DataFrame):
    """
    Number of Contracts by Underlying and Maturity Year.
    """
    if df.empty or 'maturity_year' not in df.columns:
        return None
        
    # Aggregate
    pivot = df.pivot_table(
        index='underlying',
        columns='maturity_year',
        values='ts_code',
        aggfunc='count',
        fill_value=0
    )
    
    # Sort by total count
    pivot['total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('total', ascending=False).head(30) # Limit to top 30
    pivot = pivot.drop(columns=['total'])
    
    if pivot.empty:
        return None
        
    fig = px.imshow(
        pivot,
        color_continuous_scale='YlOrRd',
        aspect='auto',
        text_auto='d'
    )
    
    fig = apply_chart_style(fig, title="Contract Count by Maturity Year (Top 30)")
    fig.update_layout(
        xaxis_title='Maturity Year (20XX)',
        yaxis_title='Underlying Asset'
    )
    
    return fig


def plot_opt_strike_maturity_scatter(df: pd.DataFrame, underlying: str):
    """
    Strike Price vs Maturity Date Scatter Plot.
    """
    if df.empty or 'strike' not in df.columns:
        return None
        
    data = df[df['underlying'] == underlying].copy()
    
    if data.empty:
        return None
        
    fig = px.scatter(
        data,
        x='maturity_date',
        y='strike',
        color='call_put',
        size_max=10,
        opacity=0.7,
        color_discrete_map={'C': COLORS['danger'], 'P': COLORS['success']},
        hover_data=['ts_code', 'name']
    )
    
    fig = apply_chart_style(fig, title=f"{underlying}: Strike Price vs Maturity Date")
    fig.update_layout(
        xaxis_title='Maturity Date (YYYYMMDD)',
        yaxis_title='Strike Price',
        legend_title='Call/Put'
    )
    fig.update_xaxes(tickformat='%Y%m%d')
    
    return fig
