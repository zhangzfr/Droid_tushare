import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import itertools

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
        
    df = df.copy()
    if pd.api.types.is_datetime64_any_dtype(df['trade_date']):
        df['trade_date'] = df['trade_date'].dt.strftime('%Y%m%d')

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
        xaxis=dict(
            title='Date',
            type='category',
            tickmode='auto',
            tickangle=-45,
            showgrid=False
        ),
        yaxis=dict(title='Index Point'),
        yaxis2=dict(
            title='Amount',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, borderwidth=0),
        height=500,
        margin=dict(l=10, r=10, t=40, b=80),
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
    
    df = df.copy()
    if pd.api.types.is_datetime64_any_dtype(df['trade_date']):
        df['trade_date'] = df['trade_date'].dt.strftime('%Y%m%d')

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
        xaxis=dict(
            title='Date',
            type='category',
            tickmode='auto',
            tickangle=-45,
            showgrid=False
        ),
        yaxis=dict(title='PE Ratio'),
        yaxis2=dict(
            title='PB Ratio',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, borderwidth=0),
        height=400,
        margin=dict(l=10, r=10, t=40, b=80),
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


def plot_corr_heatmap(corr_df: pd.DataFrame):
    """行业收益率相关性热力图。"""
    if corr_df.empty:
        return None

    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns,
        y=corr_df.index,
        zmin=-1,
        zmax=1,
        colorscale='RdBu',
        reversescale=True,
        text=corr_df.round(2).values,
        texttemplate="%{text}",
        hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title='相关性矩阵',
        height=600,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(borderwidth=0)
    )
    return fig


def plot_rank_trend(rank_df: pd.DataFrame):
    """行业涨跌幅排名走势，纵轴为排名(1为最高)。"""
    if rank_df.empty:
        return None

    # 日期格式化为字符串以作类别轴，跳过无数据自然日
    if pd.api.types.is_datetime64_any_dtype(rank_df['trade_date']):
        rank_df = rank_df.copy()
        rank_df['trade_date'] = rank_df['trade_date'].dt.strftime('%Y%m%d')

    fig = go.Figure()
    industries = rank_df['l1_name'].unique()
    last_date = rank_df['trade_date'].max()

    for name in industries:
        sub = rank_df[rank_df['l1_name'] == name].sort_values('trade_date')
        fig.add_trace(go.Scatter(
            x=sub['trade_date'],
            y=sub['rank'],
            mode='lines+markers',
            name=name,
            line=dict(width=2),
            marker=dict(size=6)
        ))

    # 在右侧添加类似坐标轴的标注，避免与数据点重叠
    last_points = rank_df[rank_df['trade_date'] == last_date]
    if not last_points.empty:
        annotations = []
        for _, row in last_points.iterrows():
            annotations.append(dict(
                x=1.01,
                xref='paper',
                xanchor='left',
                y=row['rank'],
                yref='y',
                text=row['l1_name'],
                showarrow=False,
                align='left',
                font=dict(size=11)
            ))
        fig.update_layout(annotations=annotations)

    fig.update_layout(
        title='行业涨跌幅排名走势 (数值越小排名越高)',
        xaxis=dict(
            title='Date', 
            type='category', 
            tickmode='auto',
            tickangle=-45,
            showgrid=False
        ),
        yaxis=dict(title='Rank', autorange='reversed', showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        height=800,
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, borderwidth=0),
        margin=dict(l=40, r=160, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x'
    )

    fig.update_traces(
        hoverinfo='skip',
        hovertemplate=None,
        line=dict(width=2),
        marker=dict(size=6, line=dict(width=0))
    )
    return fig


def plot_rank_sankey(rank_df: pd.DataFrame):
    """行业排名流（Sankey）。"""
    if rank_df.empty:
        return None

    if pd.api.types.is_datetime64_any_dtype(rank_df['trade_date']):
        rank_df = rank_df.copy()
        rank_df['trade_date'] = rank_df['trade_date'].dt.strftime('%Y%m%d')

    # 仅展示最新交易日排名前10和后10的行业，但排名计算保持全量
    last_date = rank_df['trade_date'].max()
    df_last = rank_df[rank_df['trade_date'] == last_date]
    if df_last.empty:
        return None
    max_rank_all = int(rank_df['rank'].max()) if not rank_df.empty else 1

    top_names = df_last[df_last['rank'] <= 10]['l1_name'].unique().tolist()
    bottom_names = df_last[df_last['rank'] >= max_rank_all - 9]['l1_name'].unique().tolist()
    display_names = sorted(set(top_names + bottom_names))
    if not display_names:
        return None

    rank_df = rank_df[rank_df['l1_name'].isin(display_names)]

    dates = sorted(rank_df['trade_date'].unique())
    industries = sorted(rank_df['l1_name'].unique())
    max_rank = int(rank_df['rank'].max()) if not rank_df.empty else 1

    # 颜色映射
    palette = px.colors.qualitative.Dark24 + px.colors.qualitative.Safe + px.colors.qualitative.Set3
    color_cycle = itertools.cycle(palette)
    color_map = {name: next(color_cycle) for name in industries}

    node_labels = []
    node_colors = []
    node_custom = []
    node_x = []
    node_y = []
    node_index = {}

    # 坐标：x 按日期均分，y 按排名映射（排名越高 y 越小）
    x_map = {d: (i / (len(dates) - 1)) if len(dates) > 1 else 0.5 for i, d in enumerate(dates)}

    for d in dates:
        df_d = rank_df[rank_df['trade_date'] == d]
        for _, row in df_d.iterrows():
            label = ""
            key = (row['l1_name'], d)
            node_index[key] = len(node_labels)
            node_labels.append(label)
            node_colors.append(color_map[row['l1_name']])
            node_custom.append(None)
            node_x.append(x_map[d])
            # rank 从 1 开始，映射到 0-1；越高排名 y 越小
            node_y.append(1 - (int(row['rank']) - 1) / max_rank)

    sources, targets, values, link_colors, link_custom = [], [], [], [], []
    for name in industries:
        df_i = rank_df[rank_df['l1_name'] == name].sort_values('trade_date')
        prev_key = None
        for _, row in df_i.iterrows():
            key = (name, row['trade_date'])
            if prev_key is not None and key in node_index and prev_key in node_index:
                sources.append(node_index[prev_key])
                targets.append(node_index[key])
                values.append(1)
                link_colors.append(color_map[name])
                link_custom.append(name)
            prev_key = key

    if not sources:
        return None

    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=6,
            thickness=10,
            line=dict(width=0.5, color='gray'),
            label=node_labels,
            color=node_colors,
            customdata=node_custom,
            x=node_x,
            y=node_y,
            hovertemplate="<extra></extra>"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            customdata=link_custom,
            hovertemplate='<extra></extra>'
        )
    )])

    fig.update_layout(
        title='行业排名流 (Sankey)',
        height=max(600, 25 * len(industries)),
        margin=dict(l=10, r=220, t=60, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # 方向提示与行业图例
    legend_ann = []
    
    # 底部日期标注
    for i, d in enumerate(dates):
        # 仅显示部分日期以避免重叠 (e.g., first, last, and some in between)
        # 或者全部显示如果数量不多。这里简单处理：显示全部但旋转
        # Simple Logic: Add date text at bottom
        legend_ann.append(dict(
            x=x_map[d], 
            y=-0.05, # Below chart
            xref='paper', yref='paper',
            text=str(d),
            showarrow=False,
            align='center', 
            textangle=-45,
            font=dict(size=10, color='#666')
        ))

    # Top Direction Text
    legend_ann.append(dict(
        x=0.0, y=1.08, xref='paper', yref='paper',
        text='Left = 最早交易日 → Right = 最新交易日',
        showarrow=False, align='left', font=dict(size=12, color='#888')
    ))
    
    # Right Side Industry Labels
    for i, name in enumerate(display_names):
        legend_ann.append(dict(
            x=1.02, y=1 - i * 0.04,
            xref='paper', yref='paper',
            text=name,
            showarrow=False,
            font=dict(size=11, color=color_map.get(name, '#333')),
            align='left'
        ))
    fig.update_layout(annotations=legend_ann, margin=dict(b=80)) # Increase bottom margin for dates
    return fig


def plot_multi_index_amount_normalized(df):
    """成交额归一化走势。"""
    if df.empty or 'amount' not in df.columns:
        return None

    fig = go.Figure()
    indices = df['ts_code'].unique()

    for code in indices:
        sub_df = df[df['ts_code'] == code].sort_values('trade_date')
        if sub_df.empty:
            continue

        base = sub_df['amount'].iloc[0]
        if base == 0:
            continue

        sub_df = sub_df.copy()
        sub_df['norm_amount'] = sub_df['amount'] / base * 100

        name = code
        if 'l1_name' in sub_df.columns:
            name = sub_df['l1_name'].iloc[0]

        fig.add_trace(go.Scatter(
            x=sub_df['trade_date'],
            y=sub_df['norm_amount'],
            mode='lines',
            name=name
        ))

    if not fig.data:
        return None

    fig.update_layout(
        title='Normalized Amount Trend (Base=100)',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Normalized Amount'),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=500,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


def plot_sw_l1_valuation_quantiles(df):
    """单个行业估值走势并叠加分位数辅助线。"""
    if df.empty or 'pe' not in df.columns or 'pb' not in df.columns:
        return None

    df_sorted = df.sort_values('trade_date').copy()
    if pd.api.types.is_datetime64_any_dtype(df_sorted['trade_date']):
        df_sorted['trade_date'] = df_sorted['trade_date'].dt.strftime('%Y%m%d')

    def _quantiles(series):
        series = series.dropna()
        if series.empty:
            return None
        return {
            '100%': series.max(),
            '75%': series.quantile(0.75),
            '50%': series.quantile(0.5),
            '25%': series.quantile(0.25),
            '0%': series.min()
        }

    pe_q = _quantiles(df_sorted['pe'])
    pb_q = _quantiles(df_sorted['pb'])

    if pe_q is None and pb_q is None:
        return None

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=("PE", "PB"))

    fig.add_trace(
        go.Scatter(x=df_sorted['trade_date'], y=df_sorted['pe'], mode='lines', name='PE'),
        row=1, col=1
    )
    if pe_q:
        for label, val in pe_q.items():
            fig.add_trace(
                go.Scatter(
                    x=df_sorted['trade_date'],
                    y=[val] * len(df_sorted),
                    mode='lines',
                    name=f"PE {label}",
                    line=dict(color='#B0BEC5', dash='dot')
                ),
                row=1, col=1
            )

    fig.add_trace(
        go.Scatter(x=df_sorted['trade_date'], y=df_sorted['pb'], mode='lines', name='PB', line=dict(color='#00B8D4')),
        row=2, col=1
    )
    if pb_q:
        for label, val in pb_q.items():
            fig.add_trace(
                go.Scatter(
                    x=df_sorted['trade_date'],
                    y=[val] * len(df_sorted),
                    mode='lines',
                    name=f"PB {label}",
                    line=dict(color='#B0BEC5', dash='dot')
                ),
                row=2, col=1
            )

    fig.update_layout(
        height=650,
        margin=dict(l=10, r=10, t=40, b=80),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, borderwidth=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_xaxes(
        title_text='Date', 
        row=2, col=1,
        type='category',
        tickmode='auto',
        tickangle=-45,
        showgrid=False
    )
    fig.update_xaxes(
        type='category',
        tickmode='auto',
        showgrid=False,
        row=1, col=1
    )
    
    fig.update_yaxes(title_text='PE', row=1, col=1)
    fig.update_yaxes(title_text='PB', row=2, col=1)

    return fig
