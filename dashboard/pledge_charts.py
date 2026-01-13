import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

def plot_top_pledge_ratio(df, top_n=20):
    """Horizontal bar chart for top pledge ratios."""
    if df.empty:
        return None
    
    df_plot = df.head(top_n).copy()
    df_plot['display_name'] = df_plot['name'] + ' (' + df_plot['ts_code'] + ')'
    
    # Sort for horizontal bar (largest at top)
    df_plot = df_plot.sort_values('pledge_ratio', ascending=True)
    
    # Define colors based on ratio
    def get_color(ratio):
        if ratio > 50: return '#EF5350' # Red
        if ratio > 30: return '#FFA726' # Orange
        return '#66BB6A' # Green
        
    colors = [get_color(r) for r in df_plot['pledge_ratio']]
    
    fig = go.Figure(go.Bar(
        x=df_plot['pledge_ratio'],
        y=df_plot['display_name'],
        orientation='h',
        marker_color=colors,
        text=df_plot['pledge_ratio'].apply(lambda x: f'{x:.1f}%'),
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Pledge Ratio: %{x:.2f}%<br>Pledge Count: %{customdata}',
        customdata=df_plot['pledge_count']
    ))
    
    # Calculate dynamic height
    chart_height = max(600, top_n * 25)

    fig.update_layout(
        title=f"Top {top_n} Stocks by Pledge Ratio",
        xaxis_title="Pledge Ratio (%)",
        yaxis_title="Stock",
        template='plotly_white',
        height=chart_height,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    
    return fig

def plot_pledge_history(df, ts_code, name=""):
    """Line chart for pledge ratio history."""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['end_date'],
        y=df['pledge_ratio'],
        mode='lines+markers',
        name='Pledge Ratio',
        line=dict(color='#D97757', width=3),
        marker=dict(size=6),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title=f"Pledge Ratio Trend: {name} ({ts_code})",
        xaxis_title="Date",
        yaxis_title="Pledge Ratio (%)",
        template='plotly_white',
        height=400,
        hovermode="x unified"
    )
    
    return fig

def plot_pledge_industry_dist(df):
    """Bubble chart or bar chart for industry distribution."""
    if df.empty:
        return None
        
    # Using bubble chart: X=Avg Ratio, Y=Total Shares, Size=Stock Count
    fig = px.scatter(
        df,
        x='avg_pledge_ratio',
        y='total_pledged_shares',
        size='stock_count',
        color='avg_pledge_ratio',
        hover_name='industry',
        text='industry',
        labels={
            'avg_pledge_ratio': 'Average Pledge Ratio (%)',
            'total_pledged_shares': 'Total Pledged Shares',
            'stock_count': 'Number of Stocks'
        },
        title="Industry Pledge Risk Distribution",
        color_continuous_scale="Reds"
    )
    
    fig.update_traces(textposition='top center')
    fig.update_layout(template='plotly_white', height=500)
    
    return fig

def plot_shareholder_distribution(df):
    """Pie chart for pledge distribution by shareholder types or top holders."""
    if df.empty:
        return None
    
    # Aggregating by holder_name
    agg = df.groupby('holder_name')['pledge_amount'].sum().reset_index()
    agg = agg.sort_values('pledge_amount', ascending=False)
    
    # Take top 10 and group others
    top_10 = agg.head(10).copy()
    others_val = agg.iloc[10:]['pledge_amount'].sum() if len(agg) > 10 else 0
    if others_val > 0:
        top_10 = pd.concat([top_10, pd.DataFrame({'holder_name': ['Others'], 'pledge_amount': [others_val]})])
    
    fig = px.pie(
        top_10, 
        values='pledge_amount', 
        names='holder_name',
        title="Pledge Distribution by Shareholders",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(template='plotly_white', height=500)
    
    return fig
