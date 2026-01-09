"""
VIX Charts for Dashboard
========================
Plotly visualizations for VIX calculation results.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots


def plot_vix_trend(df: pd.DataFrame, underlying: str = None):
    """
    Plot VIX trend over time.
    
    Args:
        df: DataFrame with 'date' and 'vix' columns
        underlying: Optional underlying name for title
    """
    if df.empty:
        return None
    
    fig = go.Figure()
    
    # VIX Line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['vix'],
        mode='lines+markers',
        name='VIX',
        line=dict(color='#D97757', width=2),
        marker=dict(size=6),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>VIX: %{y:.2f}<extra></extra>'
    ))
    
    # Add reference lines
    avg_vix = df['vix'].mean()
    fig.add_hline(
        y=avg_vix, 
        line_dash="dash", 
        line_color="#8C8580",
        annotation_text=f"Avg: {avg_vix:.2f}",
        annotation_position="right"
    )
    
    title = "VIX Trend"
    if underlying:
        title = f"VIX Trend ({underlying})"
    
    fig.update_layout(
        title=title,
        xaxis_title=None,
        yaxis_title="VIX Value",
        height=400,
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickformat='%Y-%m-%d',
            tickfont=dict(color='#4A4A4A')
        ),
        yaxis=dict(
            tickfont=dict(color='#4A4A4A'),
            gridcolor='rgba(200,200,200,0.3)'
        )
    )
    
    return fig


def plot_vix_components(df: pd.DataFrame):
    """
    Plot VIX component breakdown (near/next term sigma squared).
    """
    if df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Sigma² (Near vs Next Term)', 'Term Maturity')
    )
    
    # Sigma squared comparison
    fig.add_trace(
        go.Scatter(
            x=df['date'], y=df['sigma_sq_near'],
            mode='lines', name='σ² Near',
            line=dict(color='#4CAF50')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df['date'], y=df['sigma_sq_next'],
            mode='lines', name='σ² Next',
            line=dict(color='#2196F3')
        ),
        row=1, col=1
    )
    
    # Term Maturity
    fig.add_trace(
        go.Scatter(
            x=df['date'], y=df['near_term'] * 365,
            mode='lines', name='Near Term (Days)',
            line=dict(color='#4CAF50', dash='dot')
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df['date'], y=df['next_term'] * 365,
            mode='lines', name='Next Term (Days)',
            line=dict(color='#2196F3', dash='dot')
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=500,
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(tickformat='%Y-%m-%d')
    
    return fig


def plot_vix_distribution(df: pd.DataFrame):
    """
    Plot VIX distribution histogram.
    """
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=df['vix'],
        nbinsx=20,
        marker_color='#D97757',
        opacity=0.75,
        name='VIX Distribution'
    ))
    
    # Add mean line
    avg_vix = df['vix'].mean()
    fig.add_vline(
        x=avg_vix,
        line_dash="dash",
        line_color="#1A1A1A",
        annotation_text=f"Mean: {avg_vix:.2f}"
    )
    
    fig.update_layout(
        title="VIX Distribution",
        xaxis_title="VIX Value",
        yaxis_title="Frequency",
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_forward_prices(df: pd.DataFrame):
    """
    Plot Forward Prices (F) for near and next term.
    """
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['F_near'],
        mode='lines+markers',
        name='F Near',
        line=dict(color='#4CAF50'),
        marker=dict(size=4)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['F_next'],
        mode='lines+markers',
        name='F Next',
        line=dict(color='#2196F3'),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title="Forward Price (F)",
        xaxis_title=None,
        yaxis_title="Forward Price",
        height=350,
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def plot_weight_trend(df: pd.DataFrame):
    """
    Plot interpolation weight over time.
    """
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['weight'],
        mode='lines+markers',
        name='Weight (Near Term)',
        line=dict(color='#9C27B0'),
        fill='tozeroy',
        fillcolor='rgba(156, 39, 176, 0.1)'
    ))
    
    fig.update_layout(
        title="Term Interpolation Weight",
        xaxis_title=None,
        yaxis_title="Weight",
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(range=[0, 1])
    )
    
    return fig
