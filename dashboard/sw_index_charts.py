import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_sw_treemap(df_hier, df_daily, level='L1'):
    """
    Plot Treemap for Shenwan Indices.
    
    Args:
        df_hier (pd.DataFrame): Hierarchy data (L1, L2, L3 cols)
        df_daily (pd.DataFrame): Daily data (ts_code, pct_change, amount)
        level (str): 'L1', 'L2', 'L3', or 'Stock'
    """
    if df_hier.empty or df_daily.empty:
        return None
        
    # Prepare data for Treemap
    # We need: id, label, parent, value (amount), color (pct_change)
    
    # 1. Map Hierarchy to list of nodes based on selected Level
    # Nodes needed: 
    #   - The Leaves (the selected level indices)
    #   - The Parents (the upper level indices, to create structure)
    
    data = []
    
    # Pre-process daily data for quick lookup
    # Only keep relevant columns: ts_code, pct_change, amount, name (from daily which might be fresher)
    # daily maps: ts_code -> {pct: ..., amt: ...}
    # Ensure no duplicates in daily
    df_daily = df_daily.drop_duplicates(subset=['ts_code'])
    daily_map = df_daily.set_index('ts_code')[['pct_change', 'amount']].to_dict('index')
    
    # Helper to get data safely
    def get_node_data(code):
        d = daily_map.get(code, {})
        val = d.get('amount', 0)
        pct = d.get('pct_change', 0)
        # Handle NaN
        if pd.isna(val): val = 0
        if pd.isna(pct): pct = 0
        return val, pct

    # Build nodes based on Level
    if level == 'L1':
        # Just L1 nodes (Root)
        # Distinct L1
        l1_nodes = df_hier[['l1_code', 'l1_name']].drop_duplicates()
        
        for _, row in l1_nodes.iterrows():
            code = row['l1_code']
            val, color = get_node_data(code)
            data.append({
                'id': code,
                'label': row['l1_name'],
                'parent': '',
                'value': val,
                'color': color,
                'customdata': [code, val, color]
            })
            
    elif level == 'L2':
        # L1 (Parents) + L2 (Leaves)
        l1_nodes = df_hier[['l1_code', 'l1_name']].drop_duplicates()
        l2_nodes = df_hier[['l2_code', 'l2_name', 'l1_code']].drop_duplicates()
        
        # Add L1 parents (Value/Color optional, purely for grouping)
        for _, row in l1_nodes.iterrows():
            data.append({
                'id': row['l1_code'],
                'label': row['l1_name'],
                'parent': '',
                'value': 0, # Placeholder, will be summed from children if branchvalues='total'?? No, usually 0 for container
                'color': None
            })
            
        # Add L2 leaves
        for _, row in l2_nodes.iterrows():
            code = row['l2_code']
            val, color = get_node_data(code)
            data.append({
                'id': code,
                'label': row['l2_name'],
                'parent': row['l1_code'],
                'value': val,
                'color': color,
                'customdata': [code, val, color]
            })
            
    elif level == 'L3':
        # L1 -> L2 -> L3
        l1_nodes = df_hier[['l1_code', 'l1_name']].drop_duplicates()
        l2_nodes = df_hier[['l2_code', 'l2_name', 'l1_code']].drop_duplicates()
        l3_nodes = df_hier[['l3_code', 'l3_name', 'l2_code']].drop_duplicates()
        
        # Add L1
        for _, row in l1_nodes.iterrows():
            data.append({'id': row['l1_code'], 'label': row['l1_name'], 'parent': '', 'value': 0, 'color': 0})
        # Add L2 (Middle parents)
        for _, row in l2_nodes.iterrows():
            data.append({'id': row['l2_code'], 'label': row['l2_name'], 'parent': row['l1_code'], 'value': 0, 'color': 0})
        # Add L3 leaves
        for _, row in l3_nodes.iterrows():
            code = row['l3_code']
            val, color = get_node_data(code)
            data.append({
                'id': code,
                'label': row['l3_name'],
                'parent': row['l2_code'],
                'value': val,
                'color': color,
                'customdata': [code, val, color]
            })

    elif level == 'Stock':
        # L1 -> L2 -> L3 -> Stock
        # Warning: This can be a LOT of nodes (~5000 stocks). Performance might be heavy.
        l1_nodes = df_hier[['l1_code', 'l1_name']].drop_duplicates()
        l2_nodes = df_hier[['l2_code', 'l2_name', 'l1_code']].drop_duplicates()
        l3_nodes = df_hier[['l3_code', 'l3_name', 'l2_code']].drop_duplicates()
        stock_nodes = df_hier[['ts_code', 'name', 'l3_code']].drop_duplicates()
        
        # Add L1
        for _, row in l1_nodes.iterrows():
            data.append({'id': row['l1_code'], 'label': row['l1_name'], 'parent': '', 'value': 0, 'color': 0})
        # Add L2
        for _, row in l2_nodes.iterrows():
            data.append({'id': row['l2_code'], 'label': row['l2_name'], 'parent': row['l1_code'], 'value': 0, 'color': 0})
        # Add L3
        for _, row in l3_nodes.iterrows():
            data.append({'id': row['l3_code'], 'label': row['l3_name'], 'parent': row['l2_code'], 'value': 0, 'color': 0})
        # Add Stock Leaves
        for _, row in stock_nodes.iterrows():
            code = row['ts_code']
            val, color = get_node_data(code)
            # Only add if we have data or if we want to show everything (might clutter without data)
            # To optimize, maybe only add if val > 0 ?
            if val > 0:
                data.append({
                    'id': code,
                    'label': row['name'],
                    'parent': row['l3_code'],
                    'value': val,
                    'color': color,
                    'customdata': [code, val, color]
                })

    df_plot = pd.DataFrame(data)
    
    if df_plot.empty:
        return None

    # Ensure customdata exists for all rows (parents might not have it)
    # Fill missing customdata with default values
    if 'customdata' not in df_plot.columns:
        df_plot['customdata'] = [[None, 0, 0]] * len(df_plot)
    else:
        df_plot['customdata'] = df_plot['customdata'].apply(
            lambda x: x if isinstance(x, list) else [None, 0, 0]
        )
    
    # Build customdata array for Plotly
    customdata_list = df_plot['customdata'].tolist()

    # Color Scale: Green (neg) -> Red (pos)
    # Range: usually -10 to 10 for daily limit
    
    fig = go.Figure(go.Treemap(
        ids=df_plot['id'],
        labels=df_plot['label'],
        parents=df_plot['parent'],
        values=df_plot['value'],
        customdata=customdata_list,
        marker=dict(
            colors=df_plot['color'],
            colorscale=[
                [0.0, 'rgb(0, 128, 0)'],      # -10% Green
                [0.5, 'rgb(255, 255, 255)'],  # 0% White
                [1.0, 'rgb(220, 0, 0)']       # +10% Red
            ],
            cmid=0,
            cmin=-7, # Soften the range slightly so extreme moves pop, but typical moves (-3 to 3) are visible
            cmax=7,
            colorbar=dict(title="Pct Change %"),
            line=dict(width=0.5 if level!='L1' else 0, color='grey')
        ),
        texttemplate="<b>%{label}</b><br>%{customdata[2]:.2f}%",
        hovertemplate='<b>%{label}</b><br>Amount: %{value:,.0f}<br>Change: %{customdata[2]:.2f}%<extra></extra>',
        branchvalues="total" if level == 'L1' else None 
        # "total" requires parents to sum up exactly. 
    ))
    
    fig.update_layout(
        title=f"Shenwan Market Map ({level})",
        height=800,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_sw_stock_treemap(df_stocks, l3_name: str):
    """
    Plot a simple Treemap for stocks within a single L3 industry.
    Much simpler than the hierarchical version since there's no parent structure.
    
    Args:
        df_stocks (pd.DataFrame): Stock data with ts_code, name, pct_change, amount
        l3_name (str): Name of the L3 industry for the title
    """
    if df_stocks.empty:
        return None
    
    df = df_stocks.copy()
    
    # Handle NaN
    df['pct_change'] = df['pct_change'].fillna(0)
    df['amount'] = df['amount'].fillna(0)
    
    # Filter out zero-amount stocks for cleaner display
    df = df[df['amount'] > 0]
    
    if df.empty:
        return None
    
    # Build customdata
    customdata = df[['ts_code', 'amount', 'pct_change']].values.tolist()
    
    fig = go.Figure(go.Treemap(
        ids=df['ts_code'],
        labels=df['name'],
        parents=[''] * len(df),  # No hierarchy, all at root level
        values=df['amount'],
        customdata=customdata,
        marker=dict(
            colors=df['pct_change'],
            colorscale=[
                [0.0, 'rgb(0, 128, 0)'],      # -10% Green
                [0.5, 'rgb(255, 255, 255)'],  # 0% White
                [1.0, 'rgb(220, 0, 0)']       # +10% Red
            ],
            cmid=0,
            cmin=-7,
            cmax=7,
            colorbar=dict(title="Pct Change %"),
            line=dict(width=0.5, color='grey')
        ),
        texttemplate="<b>%{customdata[0]}</b><br>%{label}<br>%{customdata[2]:.2f}%",
        hovertemplate='<b>%{customdata[0]}</b> - %{label}<br>Amount: %{value:,.0f}<br>Change: %{customdata[2]:.2f}%<extra></extra>',
    ))
    
    fig.update_layout(
        title=f"Stocks in {l3_name}",
        height=600,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_l2_stock_treemap(df_stocks, l2_name: str):
    """
    Plot Treemap for stocks within a L2 industry, grouped by L3.
    Used for D2 optimization.
    
    Args:
        df_stocks (pd.DataFrame): Stock data with ts_code, name, pct_change, amount, l3_name
        l2_name (str): Name of the L2 industry for the title
    """
    if df_stocks.empty:
        return None
    
    df = df_stocks.copy()
    
    # Handle NaN
    df['pct_change'] = df['pct_change'].fillna(0)
    df['amount'] = df['amount'].fillna(0)
    df['l3_name'] = df['l3_name'].fillna('Others')
    
    # Filter out zero-amount stocks
    df = df[df['amount'] > 0]
    
    if df.empty:
        return None
    
    # Build hierarchical data: L3 -> Stock
    data = []
    
    # Add L3 parent nodes
    l3_list = df['l3_name'].unique().tolist()
    for l3 in l3_list:
        data.append({
            'id': l3,
            'label': l3,
            'parent': '',
            'value': 0,
            'color': 0,
            'customdata': [l3, 0, 0]
        })
    
    # Add stock leaves
    for _, row in df.iterrows():
        data.append({
            'id': row['ts_code'],
            'label': row['name'] if pd.notna(row['name']) else row['ts_code'],
            'parent': row['l3_name'],
            'value': row['amount'],
            'color': row['pct_change'],
            'customdata': [row['ts_code'], row['amount'], row['pct_change']]
        })
    
    df_plot = pd.DataFrame(data)
    customdata_list = df_plot['customdata'].tolist()
    
    fig = go.Figure(go.Treemap(
        ids=df_plot['id'],
        labels=df_plot['label'],
        parents=df_plot['parent'],
        values=df_plot['value'],
        customdata=customdata_list,
        marker=dict(
            colors=df_plot['color'],
            colorscale=[
                [0.0, 'rgb(0, 128, 0)'],
                [0.5, 'rgb(255, 255, 255)'],
                [1.0, 'rgb(220, 0, 0)']
            ],
            cmid=0,
            cmin=-7,
            cmax=7,
            colorbar=dict(title="Pct Change %"),
            line=dict(width=0.5, color='grey')
        ),
        texttemplate="<b>%{customdata[0]}</b><br>%{label}<br>%{customdata[2]:.2f}%",
        hovertemplate='<b>%{customdata[0]}</b> - %{label}<br>Amount: %{value:,.0f}<br>Change: %{customdata[2]:.2f}%<extra></extra>',
    ))
    
    fig.update_layout(
        title=f"Stocks in {l2_name} (Grouped by L3)",
        height=700,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_l1_stock_treemap(df_stocks, l1_name: str):
    """
    Plot Treemap for stocks within a L1 industry, grouped by L2→L3.
    Used for L1-based drill-down.
    
    Args:
        df_stocks (pd.DataFrame): Stock data with ts_code, name, pct_change, amount, l2_name, l3_name
        l1_name (str): Name of the L1 industry for the title
    """
    if df_stocks.empty:
        return None
    
    df = df_stocks.copy()
    
    # Handle NaN
    df['pct_change'] = df['pct_change'].fillna(0)
    df['amount'] = df['amount'].fillna(0)
    df['l2_name'] = df['l2_name'].fillna('Others')
    df['l3_name'] = df['l3_name'].fillna('Others')
    
    # Filter out zero-amount stocks
    df = df[df['amount'] > 0]
    
    if df.empty:
        return None
    
    # Build hierarchical data: L2 → L3 → Stock
    data = []
    
    # Add L2 parent nodes
    l2_list = df['l2_name'].unique().tolist()
    for l2 in l2_list:
        data.append({
            'id': f"L2_{l2}",
            'label': l2,
            'parent': '',
            'value': 0,
            'color': 0,
            'customdata': [l2, 0, 0]
        })
    
    # Add L3 middle nodes
    l3_groups = df[['l2_name', 'l3_name']].drop_duplicates()
    for _, row in l3_groups.iterrows():
        data.append({
            'id': f"L3_{row['l3_name']}",
            'label': row['l3_name'],
            'parent': f"L2_{row['l2_name']}",
            'value': 0,
            'color': 0,
            'customdata': [row['l3_name'], 0, 0]
        })
    
    # Add stock leaves
    for _, row in df.iterrows():
        data.append({
            'id': row['ts_code'],
            'label': row['name'] if pd.notna(row['name']) else row['ts_code'],
            'parent': f"L3_{row['l3_name']}",
            'value': row['amount'],
            'color': row['pct_change'],
            'customdata': [row['ts_code'], row['amount'], row['pct_change']]
        })
    
    df_plot = pd.DataFrame(data)
    customdata_list = df_plot['customdata'].tolist()
    
    fig = go.Figure(go.Treemap(
        ids=df_plot['id'],
        labels=df_plot['label'],
        parents=df_plot['parent'],
        values=df_plot['value'],
        customdata=customdata_list,
        marker=dict(
            colors=df_plot['color'],
            colorscale=[
                [0.0, 'rgb(0, 128, 0)'],
                [0.5, 'rgb(255, 255, 255)'],
                [1.0, 'rgb(220, 0, 0)']
            ],
            cmid=0,
            cmin=-7,
            cmax=7,
            colorbar=dict(title="Pct Change %"),
            line=dict(width=0.5, color='grey')
        ),
        texttemplate="<b>%{customdata[0]}</b><br>%{label}<br>%{customdata[2]:.2f}%",
        hovertemplate='<b>%{customdata[0]}</b> - %{label}<br>Amount: %{value:,.0f}<br>Change: %{customdata[2]:.2f}%<extra></extra>',
    ))
    
    fig.update_layout(
        title=f"Stocks in {l1_name} (L2→L3→Stock)",
        height=800,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    
    return fig


def plot_sw_l1_price_volume(df):
    """
    Plot Price (Close) and Volume/Amount trend.
    """
    if df.empty:
        return None
        
    # Dual Axis: Left=Close, Right=Amount
    fig = go.Figure()

    # Bar for Amount (Right Axis)
    fig.add_trace(go.Bar(
        x=df['trade_date'],
        y=df['amount'],
        name='Amount (RMB)',
        marker_color='rgba(200, 200, 200, 0.5)', # Light grey
        yaxis='y2'
    ))

    # Line for Close (Left Axis)
    fig.add_trace(go.Scatter(
        x=df['trade_date'],
        y=df['close'],
        name='Close Point',
        line=dict(color='#2962FF', width=2)
    ))

    fig.update_layout(
        title='Price & Amount Trend',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Index Point'),
        yaxis2=dict(
            title='Amount',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=500,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def plot_sw_l1_valuation(df):
    """
    Plot PE and PB trends.
    """
    if df.empty or 'pe' not in df.columns or 'pb' not in df.columns:
        return None
    
    # Dual Axis: Left=PE, Right=PB
    fig = go.Figure()

    # Line for PE
    fig.add_trace(go.Scatter(
        x=df['trade_date'],
        y=df['pe'],
        name='PE Ratio',
        line=dict(color='#FF6D00', width=2)
    ))

    # Line for PB (Right Axis)
    fig.add_trace(go.Scatter(
        x=df['trade_date'],
        y=df['pb'],
        name='PB Ratio',
        line=dict(color='#00B8D4', width=2),
        yaxis='y2'
    ))

    fig.update_layout(
        title='Valuation Trend (PE & PB)',
        xaxis=dict(title='Date'),
        yaxis=dict(title='PE Ratio'),
        yaxis2=dict(
            title='PB Ratio',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def plot_multi_index_price_normalized(df):
    """
    Plot Normalized Price Trend for multiple indices.
    Base 100 at the start date.
    """
    if df.empty:
        return None
    
    fig = go.Figure()
    
    indices = df['ts_code'].unique()
    
    for code in indices:
        sub_df = df[df['ts_code'] == code].sort_values('trade_date')
        if sub_df.empty:
            continue
            
        base_value = sub_df['close'].iloc[0]
        if base_value == 0: continue
            
        sub_df['norm_close'] = sub_df['close'] / base_value * 100
        
        # Determine Name (Ideally passed in, but we can use code or try to map if provided. 
        name = code
        if 'l1_name' in sub_df.columns:
            name = sub_df['l1_name'].iloc[0]
        
        fig.add_trace(go.Scatter(
            x=sub_df['trade_date'],
            y=sub_df['norm_close'],
            mode='lines',
            name=name
        ))

    fig.update_layout(
        title='Normalized Price Trend (Base=100)',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Normalized Index'),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=500,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_multi_index_valuation(df, metric='pe'):
    """
    Plot PE or PB trend for multiple indices.
    metric: 'pe' or 'pb'
    """
    if df.empty or metric not in df.columns:
        return None
        
    fig = go.Figure()
    indices = df['ts_code'].unique()
    
    for code in indices:
        sub_df = df[df['ts_code'] == code].sort_values('trade_date')
        if sub_df.empty: continue
            
        name = code
        if 'l1_name' in sub_df.columns:
            name = sub_df['l1_name'].iloc[0]
            
        fig.add_trace(go.Scatter(
            x=sub_df['trade_date'],
            y=sub_df[metric],
            mode='lines',
            name=name
        ))

    title_map = {'pe': 'PE Ratio Trend', 'pb': 'PB Ratio Trend'}
    
    fig.update_layout(
        title=title_map.get(metric, 'Valuation Trend'),
        xaxis=dict(title='Date'),
        yaxis=dict(title=metric.upper()),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plot_multi_index_amount(df):
    """
    Plot Transaction Amount trend for multiple indices.
    """
    if df.empty:
        return None
        
    fig = go.Figure()
    indices = df['ts_code'].unique()
    
    for code in indices:
        sub_df = df[df['ts_code'] == code].sort_values('trade_date')
        if sub_df.empty: continue
            
        name = code
        if 'l1_name' in sub_df.columns:
            name = sub_df['l1_name'].iloc[0]
            
        fig.add_trace(go.Scatter(
            x=sub_df['trade_date'],
            y=sub_df['amount'],
            mode='lines',
            name=name
        ))
        
    fig.update_layout(
        title='Transaction Amount Trend',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Amount (RMB)'),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
