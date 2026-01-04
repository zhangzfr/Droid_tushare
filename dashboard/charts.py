import plotly.express as px
import pandas as pd

def plot_pmi_trend(df):
    """Plot the main PMI trends (Manufacturing, Non-Manufacturing, Composite)."""
    if df.empty:
        return None
    
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
    
    fig.update_layout(legend_title_text='PMI Indices')
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
                 color_continuous_midpoint=50) # 50 is the boom/bust line
    
    return fig

def plot_heatmap(df):
    """Plot heatmap for sub-indicators over time."""
    sub_indicators = ['pmi010100', 'pmi010200', 'pmi010300', 'pmi010400',
                      'pmi010500', 'pmi010600', 'pmi010700', 'pmi010800']
    
    valid_cols = [c for c in sub_indicators if c in df.columns]
    if not valid_cols:
        return None
        
    heatmap_data = df[['month'] + valid_cols].set_index('month')
    
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
    
    # Adjust height based on number of indicators
    fig.update_layout(height=400 + 20 * len(heatmap_data.index))
    
    return fig
