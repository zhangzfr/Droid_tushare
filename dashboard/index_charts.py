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
