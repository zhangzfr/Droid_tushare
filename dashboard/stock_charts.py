import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def plot_listing_delisting_trend(df):
    """Plot monthly trend of listings and delistings."""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    # Listings (Positive bars)
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['listings'],
        name='Listings',
        marker_color='#D97757'  # Anthropic orange
    ))
    
    # Delistings (Negative bars or distinct color)
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['delistings'],
        name='Delistings',
        marker_color='#5C5653'  # Anthropic gray
    ))
    
    fig.update_layout(
        title='Monthly Listing & Delisting Trend',
        xaxis_title='Month',
        yaxis_title='Company Count',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def plot_listing_summary(df):
    """Cumulative listed companies over time."""
    if df.empty:
        return None
        
    df = df.sort_values('month')
    df['net_growth'] = df['listings'] - df['delistings']
    df['total_companies'] = df['net_growth'].cumsum()
    
    fig = px.area(
        df, 
        x='month', 
        y='total_companies',
        title='Total Listed Companies (Cumulative)',
        labels={'total_companies': 'Total Companies', 'month': 'Date'}
    )
    
    fig.update_traces(line_color='#D97757')
    fig.update_layout(template='plotly_white')
    
    return fig
