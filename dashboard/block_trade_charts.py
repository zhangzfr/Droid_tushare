import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

def plot_market_block_trend(df):
    """
    Combined line/bar chart for market block trade activity.
    """
    if df.empty:
        return None
        
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Amount Bar
    fig.add_trace(
        go.Bar(x=df['trade_date'], y=df['total_amount'], name="Total Amount (10k)", 
               marker_color='rgba(217, 119, 87, 0.7)'),
        secondary_y=False
    )
    
    # Trade Count Line
    fig.add_trace(
        go.Scatter(x=df['trade_date'], y=df['trade_count'], name="Trade Count",
                   mode='lines+markers', line=dict(color='#5C5653', width=2)),
        secondary_y=True
    )
    
    fig.update_layout(
        title="Market Block Trade Trend",
        xaxis_title="Trade Date",
        yaxis_title="Total Amount (10k CNY)",
        yaxis2_title="Number of Trades",
        template='plotly_white',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def plot_top_block_trades(df, top_n=20):
    """
    Bar chart for stocks with highest block trade amount.
    """
    if df.empty:
        return None
        
    df_plot = df.head(top_n).copy()
    df_plot['display_name'] = df_plot['name'] + ' (' + df_plot['ts_code'] + ')'
    df_plot = df_plot.sort_values('total_amount', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df_plot['total_amount'],
        y=df_plot['display_name'],
        orientation='h',
        marker_color='#D97757',
        text=df_plot['total_amount'].apply(lambda x: f'{x:,.0f}'),
        textposition='auto'
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Stocks by Block Trade Amount",
        xaxis_title="Total Amount (10k CNY)",
        yaxis_title="Stock",
        template='plotly_white',
        height=600
    )
    
    return fig

def plot_stock_block_details(df, ts_code, name=""):
    """
    Detailed plot for a single stock's block trades with discount analysis.
    """
    if df.empty:
        return None
    
    # Bubble chart: X=Date, Y=Discount Rate, Size=Amount
    fig = px.scatter(
        df,
        x='trade_date',
        y='discount_rate',
        size='amount',
        color='discount_rate',
        hover_data=['block_price', 'daily_close', 'vol', 'amount', 'buyer', 'seller'],
        color_continuous_scale='RdYlGn_r', # Red for premium, Green for large discount? Wait, discount > 0 is good for buyer
        range_color=[-10, 10],
        title=f"Block Trade Analysis: {name} ({ts_code})",
        labels={'discount_rate': 'Discount Rate (%)', 'trade_date': 'Trade Date'}
    )
    
    # Add horizontal line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(template='plotly_white', height=500)
    
    return fig

def plot_broker_ranking(df, title, color='#78909C'):
    """Bar chart for top buyer/seller brokers."""
    if df.empty:
        return None
        
    df_plot = df.head(15).copy()
    df_plot = df_plot.sort_values('total_amount', ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df_plot['total_amount'],
        y=df_plot['broker'],
        orientation='h',
        marker_color=color,
        text=df_plot['total_amount'].apply(lambda x: f'{x:,.0f}'),
        textposition='auto'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Total Amount (10k CNY)",
        yaxis_title="Broker / Department",
        template='plotly_white',
        height=500
    )
    
    return fig
