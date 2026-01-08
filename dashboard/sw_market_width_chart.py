import plotly.graph_objects as go
import pandas as pd


def plot_market_width_heatmap(df: pd.DataFrame, level: str, ma_period: int):
    """
    Plot a heatmap of market width (% stocks above MA) by industry over time.
    Matches the style of plot_index_heatmap in index_charts.py.
    """
    if df.empty:
        return None
    
    # Pivot to create matrix: rows=industries, cols=dates
    pivot = df.pivot_table(
        index='index_code',
        columns='trade_date',
        values='width_ratio',
        aggfunc='first'
    ).sort_index(ascending=True)  # Ascending by code
    
    # Get industry names for y-axis labels
    name_map = df.set_index('index_code')['index_name'].to_dict()
    y_labels = [f"{code} - {name_map.get(code, code)}" for code in pivot.index]
    
    # Format dates as YYYYMMDD strings
    x_labels = [str(d) for d in pivot.columns]
    
    # Colorscale matching index heatmap style (Green -> Yellow -> Red)
    colorscale = [
        [0.0, 'rgb(0, 128, 0)'],      # Sharp Green
        [0.45, 'rgb(240, 255, 240)'], # Fade Green
        [0.5, 'rgb(255, 255, 200)'],  # Light Yellow
        [0.55, 'rgb(255, 240, 240)'], # Fade Red
        [1.0, 'rgb(220, 0, 0)']       # Sharp Red
    ]
    
    # Create heatmap matching index heatmap style
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=x_labels,
        y=y_labels,
        colorscale=colorscale,
        zmid=50,
        zmin=0,
        zmax=100,
        text=pivot.values,
        texttemplate="%{text:.0f}",
        textfont={"size": 9, "color": "#4A4A4A"},
        hovertemplate='<b>%{y}</b><br>%{x}<br>宽度: %{z:.1f}%<extra></extra>',
        showscale=True,
        colorbar=dict(
            title=dict(
                text=f"宽度%<br>(>MA{ma_period})",
                font=dict(color='#4A4A4A', size=10)
            ),
            thickness=15,
            len=0.8,
            x=-0.08,
            ticksuffix="%",
            tickfont=dict(color='#4A4A4A'),
            outlinewidth=0,
            borderwidth=0
        )
    ))
    
    # Calculate height based on number of industries
    height = max(500, len(pivot.index) * 22 + 100)
    
    fig.update_layout(
        title=None,
        xaxis_title=None,
        yaxis_title=None,
        height=height,
        margin=dict(l=50, r=200, t=20, b=50),
        xaxis=dict(
            type='category',
            tickangle=-45,
            tickfont=dict(size=10, color='#4A4A4A')
        ),
        yaxis=dict(
            tickfont=dict(size=10, color='#4A4A4A'),
            autorange='reversed',
            side='right'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig
