import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

def plot_risk_scatter(df, top_n=100):
    """
    Scatter plot: X=Pledge Ratio, Y=Block Trade Amount
    Color=Risk Score, Size=Block Count
    """
    if df.empty:
        return None
    
    # Filter for top risk or top amounts to avoid overcrowding
    df_plot = df.sort_values('total_risk_score', ascending=False).head(top_n).copy()
    
    fig = px.scatter(
        df_plot,
        x='pledge_ratio',
        y='block_amount',
        size='block_count',
        color='total_risk_score',
        hover_name='name',
        hover_data=['ts_code', 'industry', 'pledge_ratio', 'block_amount'],
        labels={
            'pledge_ratio': 'Pledge Ratio (%)',
            'block_amount': 'Block Trade Amount (10k)',
            'total_risk_score': 'Risk Score',
            'block_count': 'Trade Count'
        },
        title=f"Risk Radar: Top {top_n} Stocks (High Pledge + High Block Selling)",
        color_continuous_scale='RdYlGn_r' # Red is high risk
    )
    
    # Add quadrants lines
    # X line at 30% pledge
    fig.add_vline(x=30, line_dash="dash", line_color="orange", annotation_text="High Pledge > 30%")
    # Y line at median of visible block trade
    # fig.add_hline(y=df_plot['block_amount'].median(), line_dash="dash", line_color="gray")
    
    fig.update_layout(template='plotly_white', height=600)
    
    return fig

def plot_risk_distribution(df):
    """
    Heatmap or Boxplot showing risk distribution by Industry.
    """
    if df.empty:
        return None
        
    # Aggr risk score by industry
    ind_risk = df.groupby('industry')['total_risk_score'].mean().reset_index()
    ind_risk = ind_risk.sort_values('total_risk_score', ascending=False).head(20)
    
    fig = go.Figure(go.Bar(
        x=ind_risk['total_risk_score'],
        y=ind_risk['industry'],
        orientation='h',
        marker_color=ind_risk['total_risk_score'],
        marker_colorscale='Reds'
    ))
    
    fig.update_layout(
        title="Average Risk Score by Industry (Top 20)",
        xaxis_title="Avg Risk Score",
        yaxis_title="Industry",
        template='plotly_white',
        height=500
    )
    return fig
