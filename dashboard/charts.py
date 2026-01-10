import plotly.express as px
import pandas as pd

def plot_pmi_trend(df):
    """Plot the main PMI trends (Manufacturing, Non-Manufacturing, Composite)."""
    if df.empty:
        return None
    
    # Ensure data is sorted by month to avoid disconnected/looped lines
    df = df.sort_values('month')
    
    # Mapping based on notebook
    # pmi010000: Manufacturing
    # pmi020100: Non-Manufacturing
    # pmi030000: Composite (assuming based on notebook context, need to verify if column exists)
    
    cols_to_plot = ['pmi010000', 'pmi020100']
    if 'pmi030000' in df.columns:
        cols_to_plot.append('pmi030000')
        
    # Check if columns exist
    valid_cols = [c for c in cols_to_plot if c in df.columns]
    
    if not valid_cols:
        return None

    fig = px.line(df, x='month', y=valid_cols,
                  title='China PMI Trends',
                  labels={'month': 'Date', 'value': 'PMI Value', 'variable': 'Indicator'})

    # Custom naming logic
    names = {
        'pmi010000': 'Manufacturing PMI',
        'pmi020100': 'Non-Manufacturing PMI',
        'pmi030000': 'Composite PMI'
    }
    
    # Update trace names
    fig.for_each_trace(lambda t: t.update(name = names.get(t.name, t.name)))
    
    fig.update_layout(
        legend_title_text='PMI Indices',
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_sub_indicators_bar(df_latest):
    """Plot bar chart for sub-indicators of a specific (latest) month."""
    if df_latest.empty:
        return None

    sub_indicators = ['pmi010100', 'pmi010200', 'pmi010300', 'pmi010400',
                      'pmi010500', 'pmi010600', 'pmi010700', 'pmi010800']
    
    # Filter only existing columns
    sub_indicators = [col for col in sub_indicators if col in df_latest.columns]
    if not sub_indicators:
        return None

    # Transform to long format
    df_melted = df_latest[sub_indicators].melt(var_name='indicator', value_name='value')
    
    sub_labels = {
        'pmi010100': 'Large Enterprise',
        'pmi010200': 'Medium Enterprise',
        'pmi010300': 'Small Enterprise',
        'pmi010400': 'Production',
        'pmi010500': 'New Orders',
        'pmi010600': 'Supplier Delivery Time',
        'pmi010700': 'Raw Material Inventory',
        'pmi010800': 'Employment'
    }
    
    df_melted['indicator_name'] = df_melted['indicator'].map(sub_labels).fillna(df_melted['indicator'])
    
    fig = px.bar(df_melted, x='indicator_name', y='value',
                 title='Manufacturing PMI Sub-indicators',
                 labels={'indicator_name': 'Indicator', 'value': 'Value'},
                 color='value',
                 color_continuous_scale='RdYlGn',
                 color_continuous_midpoint=50)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

def plot_heatmap(df):
    """Plot heatmap for sub-indicators over time."""
    sub_indicators = ['pmi010100', 'pmi010200', 'pmi010300', 'pmi010400',
                      'pmi010500', 'pmi010600', 'pmi010700', 'pmi010800']
    
    valid_cols = [c for c in sub_indicators if c in df.columns]
    if not valid_cols:
        return None
        
    heatmap_data = df[['month'] + valid_cols].sort_values('month').set_index('month')
    
    # Transpose so indicators are Y-axis, time is X-axis
    heatmap_data = heatmap_data.T
    
    sub_labels = {
        'pmi010100': 'Large Enterprise',
        'pmi010200': 'Medium Enterprise',
        'pmi010300': 'Small Enterprise',
        'pmi010400': 'Production',
        'pmi010500': 'New Orders',
        'pmi010600': 'Supplier Delivery Time',
        'pmi010700': 'Raw Material Inventory',
        'pmi010800': 'Employment'
    }
    
    # Rename index
    heatmap_data.index = heatmap_data.index.map(lambda x: sub_labels.get(x, x))
    
    fig = px.imshow(heatmap_data,
                    labels=dict(x="Date", y="Indicator", color="PMI Value"),
                    title='Manufacturing PMI Sub-indicators Heatmap',
                    color_continuous_scale='RdYlGn',
                    color_continuous_midpoint=50,
                    aspect='auto')
    
    fig.update_xaxes(tickformat='%Y-%m')
    
    fig.update_layout(
        height=400 + 20 * len(heatmap_data.index),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_sf_charts(df):
    """Return 3 charts for Social Financing: inc_month, inc_cumval, stk_endval."""
    if df.empty:
        return None, None, None
    
    # inc_month
    fig_inc = px.line(df, x='month', y='inc_month', 
                      title='Social Financing: New Monthly Increase (inc_month)',
                      labels={'month': 'Date', 'inc_month': 'Billion RMB'})
    
    # inc_cumval
    fig_cum = px.line(df, x='month', y='inc_cumval',
                      title='Social Financing: Cumulative Increase (inc_cumval)',
                      labels={'month': 'Date', 'inc_cumval': 'Billion RMB'})
    
    # stk_endval
    fig_stk = px.line(df, x='month', y='stk_endval',
                      title='Social Financing: Stock End Value (stk_endval)',
                      labels={'month': 'Date', 'stk_endval': 'Trillion RMB'})
    
    for fig in [fig_inc, fig_cum, fig_stk]:
        if fig:
            fig.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)'
            )
    
    return fig_inc, fig_cum, fig_stk

def plot_m_levels(df):
    """Plot M0, M1, M2 levels as a bar chart."""
    if df.empty:
        return None
    
    cols = [c for c in ['m0', 'm1', 'm2'] if c in df.columns]
    if not cols:
        return None
        
    fig = px.bar(df, x='month', y=cols, 
                 title='Money Supply: M0, M1, M2 Levels',
                 labels={'month': 'Date', 'value': 'Level', 'variable': 'Category'},
                 barmode='group')
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_m_yoy(df):
    """Plot M0, M1, M2 YoY growth."""
    if df.empty:
        return None
        
    cols = [c for c in ['m0_yoy', 'm1_yoy', 'm2_yoy'] if c in df.columns]
    if not cols:
        return None
        
    fig = px.line(df, x='month', y=cols,
                  title='Money Supply: YoY Growth (%)',
                  labels={'month': 'Date', 'value': 'YoY (%)', 'variable': 'Indicator'})
    
    names = {'m0_yoy': 'M0 YoY', 'm1_yoy': 'M1 YoY', 'm2_yoy': 'M2 YoY'}
    fig.for_each_trace(lambda t: t.update(name = names.get(t.name, t.name)))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_m_mom(df):
    """Plot M0, M1, M2 MoM growth."""
    if df.empty:
        return None
        
    cols = [c for c in ['m0_mom', 'm1_mom', 'm2_mom'] if c in df.columns]
    if not cols:
        return None
        
    fig = px.line(df, x='month', y=cols,
                  title='Money Supply: MoM Growth (%)',
                  labels={'month': 'Date', 'value': 'MoM (%)', 'variable': 'Indicator'})
    
    names = {'m0_mom': 'M0 MoM', 'm1_mom': 'M1 MoM', 'm2_mom': 'M2 MoM'}
    fig.for_each_trace(lambda t: t.update(name = names.get(t.name, t.name)))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def plot_gdp_trend(df):
    """Plot GDP absolute value and structure (PI, SI, TI)."""
    if df.empty:
        return None
    
    # Ensure date column exists
    if 'quarter_date' not in df.columns:
        return None
        
    df = df.sort_values('quarter_date')
    
    # Primary, Secondary, Tertiary Industry
    cols = ['pi', 'si', 'ti']
    valid_cols = [c for c in cols if c in df.columns]
    
    if not valid_cols:
         # Fallback to just GDP if components missing
         if 'gdp' in df.columns:
             fig = px.bar(df, x='quarter_date', y='gdp', title='China GDP (Accumulated)')
             fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
             return fig
         return None

    # Stacked bar for structure
    fig = px.bar(df, x='quarter_date', y=valid_cols, 
                 title='China GDP Composition (Accumulated)',
                 labels={'quarter_date': 'Quarter', 'value': 'GDP (100 Million RMB)', 'variable': 'Industry'},
                 barmode='stack')
    
    # Customize names
    names = {'pi': 'Primary Industry', 'si': 'Secondary Industry', 'ti': 'Tertiary Industry'}
    fig.for_each_trace(lambda t: t.update(name = names.get(t.name, t.name)))
    
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def plot_gdp_yoy(df):
    """Plot GDP YoY Growth."""
    if df.empty or 'gdp_yoy' not in df.columns:
        return None
        
    if 'quarter_date' not in df.columns:
        return None
        
    df = df.sort_values('quarter_date')
    
    fig = px.line(df, x='quarter_date', y='gdp_yoy',
                  title='GDP YoY Growth (%)',
                  labels={'quarter_date': 'Quarter', 'gdp_yoy': 'YoY (%)'},
                  markers=True)
    
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


