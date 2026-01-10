import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def plot_uplift_analysis(df, ts_code):
    """
    Plot stock price, technical indicators, and uplift signals.
    
    Args:
        df (pd.DataFrame): DataFrame with index 'trade_date' and columns:
                           ['close', 'open', 'high', 'low', 'ma5', 'ma20', 'ma60', 
                            'upper_band', 'volume', 'vma20', 'main_uplift'].
        ts_code (str): Stock code for title.
        
    Returns:
        plotly.graph_objects.Figure: The interactive chart.
    """
    if df.empty:
        return None
        
    # Create subplot with 2 rows (Price and Volume)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.7, 0.3]
    )
    
    # --- Price Chart (Top) ---
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'] if 'open' in df.columns else df['close'], # Fallback if open/high/low missing
        high=df['high'] if 'high' in df.columns else df['close'],
        low=df['low'] if 'low' in df.columns else df['close'],
        close=df['close'],
        name='Price',
        increasing_line_color='#26A69A', # Green
        decreasing_line_color='#EF5350'  # Red
    ), row=1, col=1)
    
    # Moving Averages
    if 'ma_short' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ma_short'], 
            name='MA Short', 
            line=dict(color='#FFA726', width=1) # Orange
        ), row=1, col=1)
    
    if 'ma_mid' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ma_mid'], 
            name='MA Mid', 
            line=dict(color='#42A5F5', width=1) # Blue
        ), row=1, col=1)
    
    if 'ma_long' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ma_long'], 
            name='MA Long', 
            line=dict(color='#66BB6A', width=1) # Green
        ), row=1, col=1)
    
    # Bollinger Upper Band (Dotted)
    if 'upper_band' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['upper_band'], 
            name='Bollinger Upper', 
            line=dict(color='#AB47BC', width=1, dash='dot') # Purple
        ), row=1, col=1)
        
    # Uplift Signals (Markers)
    uplift_points = df[df['main_uplift']]
    if not uplift_points.empty:
        fig.add_trace(go.Scatter(
            x=uplift_points.index, 
            y=uplift_points['high'] * 1.02, # Place slightly above high
            mode='markers',
            name='Main Uplift Signal',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='#E91E63', # Pink/Magenta
                line=dict(width=1, color='white')
            )
        ), row=1, col=1)

    # Decline Signals (Markers)
    if 'main_decline' in df.columns:
        decline_points = df[df['main_decline']]
        if not decline_points.empty:
            fig.add_trace(go.Scatter(
                x=decline_points.index, 
                y=decline_points['low'] * 0.98, # Place slightly below low
                mode='markers',
                name='Main Decline Signal',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color='#00C853', # Green
                    line=dict(width=1, color='white')
                )
            ), row=1, col=1)

    # --- Volume Chart (Bottom) ---
    
    # Color volume bars based on price change
    colors = ['#26A69A' if row['close'] >= row['open'] else '#EF5350' 
              for index, row in df.iterrows()] if 'open' in df.columns else '#78909C'

    fig.add_trace(go.Bar(
        x=df.index, 
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        opacity=0.8
    ), row=2, col=1)
    
    # VMA
    if 'vma' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['vma'],
            name='VMA',
            line=dict(color='#7E57C2', width=1) # Deep Purple
        ), row=2, col=1)
        
    # Highlight Volume on Uplift days
    if not uplift_points.empty:
         fig.add_trace(go.Scatter(
            x=uplift_points.index, 
            y=uplift_points['volume'],
            mode='markers',
            name='Uplift Volume',
            showlegend=False,
            marker=dict(
                symbol='star',
                size=8,
                color='#E91E63'
            )
        ), row=2, col=1)

    # --- Layout Update ---
    fig.update_layout(
        title=dict(text=f'{ts_code} Main Uplift Detection Analysis', x=0.05),
        template='plotly_white',
        hovermode='x unified',
        height=700,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Remove range slider from bottom axis (volume)
    fig.update_xaxes(matches='x')
    
    return fig
