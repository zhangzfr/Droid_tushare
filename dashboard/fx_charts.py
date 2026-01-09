"""
FX & Commodity Charts Module
============================
Plotly-based interactive chart functions for the FX Education dashboard.
Organized by the four learning levels.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ============================================================================
# Color Schemes (Anthropic-inspired)
# ============================================================================
COLORS = {
    'primary': '#D97757',     # Warm coral
    'secondary': '#5C5653',   # Warm gray
    'accent': '#4A90A4',      # Muted blue
    'success': '#6BBF59',     # Muted green
    'warning': '#E8A838',     # Warm yellow
    'danger': '#C75B5B',      # Muted red
    'background': '#FAF5F0',  # Warm off-white
    'text': '#1A1A1A',        # Near black
}

# Qualitative color sequence for multiple assets
ASSET_COLORS = [
    '#D97757', '#4A90A4', '#6BBF59', '#E8A838', '#8B7355',
    '#C75B5B', '#7B68EE', '#20B2AA', '#FF6B6B', '#4ECDC4'
]

# Diverging color scale for correlations
CORRELATION_COLORSCALE = [
    [0, '#C75B5B'],      # Red for negative
    [0.5, '#FFFFFF'],    # White for zero
    [1, '#4A90A4']       # Blue for positive
]

# Sequential color scale for heatmaps
HEATMAP_COLORSCALE = 'RdYlGn'


def apply_chart_style(fig, title=None):
    """Apply consistent styling to Plotly figures."""
    fig.update_layout(
        font_family="Inter, -apple-system, sans-serif",
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
            bordercolor=COLORS['secondary'],
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
        hoverlabel=dict(
            font_family="Inter",
            font_size=12
        )
    )
    return fig


# ============================================================================
# Level 1: Asset Overview Charts
# ============================================================================

def plot_classify_pie(df_obasic: pd.DataFrame):
    """
    Create a pie chart showing asset classification distribution.
    
    Args:
        df_obasic: DataFrame with 'classify' column
    
    Returns:
        Plotly figure
    """
    if df_obasic.empty:
        return None
    
    counts = df_obasic['classify'].value_counts().reset_index()
    counts.columns = ['Category', 'Count']
    
    fig = px.pie(
        counts,
        values='Count',
        names='Category',
        color_discrete_sequence=ASSET_COLORS,
        hole=0.4  # Donut chart
    )
    
    fig.update_traces(
        textposition='outside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>'
    )
    
    fig = apply_chart_style(fig, title="Asset Classification Distribution")
    fig.update_layout(showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=-0.15))
    
    return fig


def plot_asset_table_summary(df_obasic: pd.DataFrame):
    """
    Create a summary bar chart by exchange or classification.
    
    Args:
        df_obasic: DataFrame with asset info
    
    Returns:
        Plotly figure
    """
    if df_obasic.empty:
        return None
    
    # Create stacked bar by classify and exchange
    summary = df_obasic.groupby(['classify', 'exchange']).size().reset_index(name='count')
    
    fig = px.bar(
        summary,
        x='classify',
        y='count',
        color='exchange',
        color_discrete_sequence=ASSET_COLORS,
        barmode='stack'
    )
    
    fig = apply_chart_style(fig, title="Assets by Classification & Exchange")
    fig.update_layout(xaxis_title="Asset Category", yaxis_title="Number of Assets")
    
    return fig


# ============================================================================
# Level 2: Price Dynamics Charts
# ============================================================================

def plot_price_lines(df_daily: pd.DataFrame, ts_codes: list = None, normalize: bool = True):
    """
    Create multi-line price chart for selected assets.
    
    Args:
        df_daily: DataFrame with trade_date, ts_code, mid_close
        ts_codes: List of asset codes to plot (optional filter)
        normalize: If True, normalize prices to 100 at start for comparison
    
    Returns:
        Plotly figure
    """
    if df_daily.empty:
        return None
    
    df = df_daily.copy()
    if ts_codes:
        df = df[df['ts_code'].isin(ts_codes)]
    
    if df.empty:
        return None
    
    # Normalize if requested
    if normalize:
        df = df.sort_values(['ts_code', 'trade_date'])
        df['normalized'] = df.groupby('ts_code')['mid_close'].transform(
            lambda x: 100 * x / x.iloc[0]
        )
        y_col = 'normalized'
        y_title = 'Normalized Price (Base = 100)'
    else:
        y_col = 'mid_close'
        y_title = 'Price'
    
    fig = px.line(
        df,
        x='trade_date',
        y=y_col,
        color='ts_code',
        color_discrete_sequence=ASSET_COLORS
    )
    
    fig = apply_chart_style(fig, title="Price Comparison")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=y_title,
        legend_title="Asset",
        hovermode='x unified'
    )
    
    return fig


def plot_log_returns(df_returns: pd.DataFrame, ts_codes: list = None):
    """
    Create line chart of log returns.
    
    Args:
        df_returns: DataFrame with trade_date, ts_code, return
        ts_codes: List of asset codes to plot
    
    Returns:
        Plotly figure
    """
    if df_returns.empty or 'return' not in df_returns.columns:
        return None
    
    df = df_returns.copy()
    if ts_codes:
        df = df[df['ts_code'].isin(ts_codes)]
    
    if df.empty:
        return None
    
    fig = px.line(
        df,
        x='trade_date',
        y='return',
        color='ts_code',
        color_discrete_sequence=ASSET_COLORS
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash='dash', line_color='#888888', line_width=1)
    
    fig = apply_chart_style(fig, title="Daily Log Returns")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Log Return",
        yaxis_tickformat='.2%',
        legend_title="Asset",
        hovermode='x unified'
    )
    
    return fig


def plot_price_distribution(df_returns: pd.DataFrame, ts_code: str = None):
    """
    Create histogram and box plot of returns distribution.
    
    Args:
        df_returns: DataFrame with return column
        ts_code: Single asset code to analyze (if None, uses all)
    
    Returns:
        Plotly figure with histogram
    """
    if df_returns.empty or 'return' not in df_returns.columns:
        return None
    
    df = df_returns.dropna(subset=['return']).copy()
    if ts_code:
        df = df[df['ts_code'] == ts_code]
    
    if df.empty:
        return None
    
    fig = px.histogram(
        df,
        x='return',
        color='ts_code',
        marginal='box',
        nbins=50,
        color_discrete_sequence=ASSET_COLORS,
        opacity=0.7
    )
    
    fig = apply_chart_style(fig, title="Returns Distribution")
    fig.update_layout(
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        xaxis_tickformat='.1%',
        barmode='overlay'
    )
    
    return fig


def plot_volatility_bar(df_stats: pd.DataFrame):
    """
    Create bar chart comparing volatility across assets.
    
    Args:
        df_stats: DataFrame with ts_code, daily_volatility
    
    Returns:
        Plotly figure
    """
    if df_stats.empty:
        return None
    
    df = df_stats.sort_values('daily_volatility', ascending=True)
    
    fig = px.bar(
        df,
        x='daily_volatility',
        y='ts_code',
        orientation='h',
        color='daily_volatility',
        color_continuous_scale=[[0, '#6BBF59'], [0.5, '#E8A838'], [1, '#C75B5B']]
    )
    
    fig = apply_chart_style(fig, title="Daily Volatility by Asset")
    fig.update_layout(
        xaxis_title="Daily Volatility (Std Dev)",
        yaxis_title="",
        xaxis_tickformat='.2%',
        coloraxis_showscale=False
    )
    
    return fig


# ============================================================================
# Level 3: Correlation Analysis Charts
# ============================================================================

def plot_correlation_heatmap(df_corr: pd.DataFrame):
    """
    Create correlation matrix heatmap.
    
    Args:
        df_corr: Correlation matrix DataFrame
    
    Returns:
        Plotly figure
    """
    if df_corr.empty:
        return None
    
    fig = px.imshow(
        df_corr,
        color_continuous_scale=CORRELATION_COLORSCALE,
        aspect='equal',
        zmin=-1,
        zmax=1,
        text_auto='.2f'
    )
    
    fig = apply_chart_style(fig, title="Return Correlation Matrix")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        coloraxis_colorbar_title="Correlation"
    )
    
    return fig


def plot_scatter_matrix(df_returns_pivot: pd.DataFrame, ts_codes: list = None):
    """
    Create scatter plot matrix for selected assets.
    
    Args:
        df_returns_pivot: Pivot table with assets as columns
        ts_codes: List of assets to include (max 5 recommended)
    
    Returns:
        Plotly figure
    """
    if df_returns_pivot.empty:
        return None
    
    df = df_returns_pivot.copy()
    if ts_codes:
        cols = [c for c in ts_codes if c in df.columns]
        df = df[cols]
    
    # Limit to first 5 columns for readability
    if len(df.columns) > 5:
        df = df[df.columns[:5]]
    
    fig = px.scatter_matrix(
        df.dropna(),
        dimensions=df.columns.tolist(),
        color_discrete_sequence=[COLORS['primary']],
        opacity=0.5
    )
    
    fig = apply_chart_style(fig, title="Returns Scatter Matrix")
    fig.update_traces(diagonal_visible=False, showupperhalf=False)
    fig.update_layout(height=600)
    
    return fig


def plot_rolling_correlation(df_rolling: pd.Series, asset1: str, asset2: str):
    """
    Create line chart of rolling correlation.
    
    Args:
        df_rolling: Series of rolling correlation values (index is date)
        asset1, asset2: Asset names for title
    
    Returns:
        Plotly figure
    """
    if df_rolling.empty:
        return None
    
    df = df_rolling.reset_index()
    df.columns = ['Date', 'Correlation']
    
    fig = px.line(
        df,
        x='Date',
        y='Correlation',
        color_discrete_sequence=[COLORS['primary']]
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_dash='dash', line_color='#888888', line_width=1)
    fig.add_hline(y=0.5, line_dash='dot', line_color='#4A90A4', line_width=1, opacity=0.5)
    fig.add_hline(y=-0.5, line_dash='dot', line_color='#C75B5B', line_width=1, opacity=0.5)
    
    fig = apply_chart_style(fig, title=f"30-Day Rolling Correlation: {asset1} vs {asset2}")
    fig.update_layout(
        yaxis_title="Correlation",
        yaxis_range=[-1, 1]
    )
    
    return fig


# ============================================================================
# Level 4: Advanced Analysis Charts
# ============================================================================

def plot_monthly_return_heatmap(df_monthly: pd.DataFrame, ts_code: str):
    """
    Create monthly returns heatmap (year x month).
    
    Args:
        df_monthly: DataFrame with ts_code, month, monthly_return
        ts_code: Asset to display
    
    Returns:
        Plotly figure
    """
    if df_monthly.empty:
        return None
    
    df = df_monthly[df_monthly['ts_code'] == ts_code].copy()
    if df.empty:
        return None
    
    df['year'] = df['month'].dt.year
    df['month_num'] = df['month'].dt.month
    
    # Pivot for heatmap
    pivot = df.pivot_table(index='year', columns='month_num', values='monthly_return', aggfunc='first')
    
    # Rename columns to month names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pivot.columns = [month_names[i-1] for i in pivot.columns]
    
    fig = px.imshow(
        pivot * 100,  # Convert to percentage
        color_continuous_scale=HEATMAP_COLORSCALE,
        aspect='auto',
        text_auto='.1f'
    )
    
    fig = apply_chart_style(fig, title=f"Monthly Returns Heatmap: {ts_code}")
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Year",
        coloraxis_colorbar_title="Return %"
    )
    
    return fig


def plot_volatility_line(df_vol: pd.DataFrame, ts_codes: list = None):
    """
    Create line chart of rolling volatility over time.
    
    Args:
        df_vol: DataFrame with trade_date, ts_code, volatility
        ts_codes: List of assets to plot
    
    Returns:
        Plotly figure
    """
    if df_vol.empty or 'volatility' not in df_vol.columns:
        return None
    
    df = df_vol.dropna(subset=['volatility']).copy()
    if ts_codes:
        df = df[df['ts_code'].isin(ts_codes)]
    
    if df.empty:
        return None
    
    fig = px.line(
        df,
        x='trade_date',
        y='volatility',
        color='ts_code',
        color_discrete_sequence=ASSET_COLORS
    )
    
    fig = apply_chart_style(fig, title="Rolling 20-Day Volatility")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Volatility (Std Dev)",
        yaxis_tickformat='.2%',
        legend_title="Asset",
        hovermode='x unified'
    )
    
    return fig


def plot_risk_return_scatter(df_stats: pd.DataFrame):
    """
    Create risk-return scatter plot.
    
    Args:
        df_stats: DataFrame with ts_code, annualized_return, annualized_volatility
    
    Returns:
        Plotly figure
    """
    if df_stats.empty:
        return None
    
    # Create the scatter plot
    fig = px.scatter(
        df_stats,
        x='annualized_volatility',
        y='annualized_return',
        text='ts_code',
        size='count',
        color='sharpe_ratio',
        color_continuous_scale=[[0, '#C75B5B'], [0.5, '#E8A838'], [1, '#6BBF59']],
        hover_data=['mean_daily_return', 'daily_volatility', 'sharpe_ratio']
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_dash='dash', line_color='#888888', line_width=1)
    fig.add_vline(x=0, line_dash='dash', line_color='#888888', line_width=1)
    
    # Adjust text position
    fig.update_traces(textposition='top center', textfont_size=10)
    
    fig = apply_chart_style(fig, title="Risk-Return Profile")
    fig.update_layout(
        xaxis_title="Annualized Volatility",
        yaxis_title="Annualized Return",
        xaxis_tickformat='.0%',
        yaxis_tickformat='.0%',
        coloraxis_colorbar_title="Sharpe Ratio"
    )
    
    return fig


def plot_seasonality_bar(df_monthly: pd.DataFrame, ts_code: str):
    """
    Create bar chart showing average return by month (seasonality).
    
    Args:
        df_monthly: DataFrame with month and monthly_return
        ts_code: Asset to analyze
    
    Returns:
        Plotly figure
    """
    if df_monthly.empty:
        return None
    
    df = df_monthly[df_monthly['ts_code'] == ts_code].copy()
    if df.empty:
        return None
    
    df['month_num'] = df['month'].dt.month
    
    # Calculate average return by month
    seasonality = df.groupby('month_num')['monthly_return'].agg(['mean', 'std', 'count']).reset_index()
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    seasonality['month_name'] = seasonality['month_num'].apply(lambda x: month_names[x-1])
    
    # Color by positive/negative
    seasonality['color'] = seasonality['mean'].apply(
        lambda x: COLORS['success'] if x >= 0 else COLORS['danger']
    )
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=seasonality['month_name'],
        y=seasonality['mean'] * 100,
        marker_color=seasonality['color'],
        text=[f"{v:.1f}%" for v in seasonality['mean'] * 100],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Avg Return: %{y:.2f}%<extra></extra>'
    ))
    
    fig = apply_chart_style(fig, title=f"Seasonal Pattern: {ts_code}")
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Monthly Return (%)",
        showlegend=False
    )
    
    return fig
