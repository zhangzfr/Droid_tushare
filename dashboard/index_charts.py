import plotly.express as px
import pandas as pd


def plot_constituent_count_over_time(df):
    """
    Plot bar chart showing number of constituents per trade date.
    Helps identify missing data (sudden drops in count).
    """
    if df.empty:
        return None
    
    # Ensure date column is properly formatted
    df = df.copy()
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    df = df.sort_values('trade_date')
    
    fig = px.bar(df, x='trade_date', y='constituent_count',
                 title='Constituent Count per Trade Date',
                 labels={'trade_date': 'Date', 'constituent_count': 'Number of Constituents'})
    
    fig.update_layout(
        xaxis_tickformat='%Y-%m-%d',
        bargap=0.1,
        height=400
    )
    
    return fig


def plot_index_heatmap(df):
    """
    Plot heatmap of percentage changes for major indices.
    """
    import plotly.graph_objects as go
    
    if df.empty:
        return None
    
    # Pre-processing
    df = df.copy()
    df['display_name'] = df['name'] + " (" + df['ts_code'] + ")"
    
    # Pivot for heatmap: rows = indices, cols = dates
    pivot_df = df.pivot(index='display_name', columns='trade_date', values='pct_chg')
    
    # Define custom colorscale: Green (Negative) -> White (Zero) -> Red (Positive)
    # Following China market convention
    colorscale = [
        [0.0, 'rgb(0, 128, 0)'],      # Sharp Green
        [0.45, 'rgb(240, 255, 240)'], # Fade Green
        [0.5, 'rgb(255, 255, 255)'],  # White
        [0.55, 'rgb(255, 240, 240)'], # Fade Red
        [1.0, 'rgb(220, 0, 0)']       # Sharp Red
    ]
    
    # We want 0 to be exactly in the middle of the colorscale
    # But pct_chg might not be symmetric. We'll set zmid=0.
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale=colorscale,
        zmid=0,
        zmin=-5, # Cap color range for better contrast
        zmax=5,
        text=pivot_df.values,
        texttemplate="%{text:.1f}",
        textfont={"size": 10},
        hovertemplate='<b>%{y}</b><br>Date: %{x}<br>Change: %{z:.2f}%<extra></extra>',
        showscale=True,
        colorbar=dict(title="Change %", thickness=15, len=0.8)
    ))
    
    fig.update_layout(
        title={
            'text': "Major Indices Performance Heatmap (%)",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Trade Date',
        yaxis_title=None,
        height=600,
        margin=dict(l=150, r=20, t=100, b=50),
        xaxis=dict(
            type='category', 
            tickangle=-45,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            autorange='reversed' # Usually indices are listed top-down
        )
    )
    
    return fig


def plot_cumulative_returns(df):
    """
    Plot line chart of cumulative returns for selected indices.
    """
    import plotly.express as px
    
    if df.empty:
        return None
    
    # Pre-processing
    df = df.copy()
    df['trade_date_dt'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce')
    df = df.sort_values(['ts_code', 'trade_date'])
    
    # Calculate cumulative returns
    # Formula: (1 + r1)(1 + r2)...
    df['ret_val'] = 1 + (df['pct_chg'] / 100.0)
    
    # Group by ts_code and calculate cumulative product
    df['cum_ret'] = df.groupby('ts_code')['ret_val'].cumprod()
    # Normalize to start at 100 (Index base)
    df['cum_ret_indexed'] = df.groupby('ts_code')['cum_ret'].transform(lambda x: (x / x.iloc[0]) * 100)
    
    df['display_name'] = df['name'] + " (" + df['ts_code'] + ")"
    
    fig = px.line(df, x='trade_date_dt', y='cum_ret_indexed', color='display_name',
                  title="Cumulative Performance (Base = 100)",
                  labels={'trade_date_dt': 'Date', 'cum_ret_indexed': 'Index Value', 'display_name': 'Index'})
    
    fig.update_layout(
        xaxis_tickformat='%Y-%m-%d',
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=20, t=100, b=50)
    )
    
    fig.update_traces(hovertemplate='%{y:.2f}')
    
    return fig
