"""
Price Index Charts Module
=========================
Plotly-based interactive chart functions for CPI and PPI visualization.
Based on the Price Index Visualization Handbook.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ============================================================================
# Color Schemes (Anthropic-inspired + inflation/deflation semantics)
# ============================================================================
COLORS = {
    'primary': '#D97757',      # Warm coral (accent)
    'secondary': '#5C5653',    # Warm gray
    'cpi': '#4A90A4',          # Blue for CPI
    'ppi': '#E8A838',          # Yellow for PPI
    'positive': '#C75B5B',     # Red for inflation/positive values
    'negative': '#6BBF59',     # Green for deflation/negative values
    'neutral': '#8C8580',      # Neutral gray
    'background': '#FAF5F0',   # Warm off-white
    'text': '#1A1A1A',         # Near black
}

# For multi-line charts
LINE_COLORS = ['#4A90A4', '#D97757', '#6BBF59', '#E8A838', '#8B7355', '#7B68EE']

# For heatmaps - diverging scale (green = deflation, red = inflation)
HEATMAP_COLORSCALE = [
    [0.0, '#2E7D32'],   # Dark green (strong deflation)
    [0.3, '#81C784'],   # Light green
    [0.5, '#FFFFFF'],   # White (neutral)
    [0.7, '#E57373'],   # Light red
    [1.0, '#C62828']    # Dark red (strong inflation)
]


def apply_chart_style(fig, title=None):
    """Apply consistent styling to Plotly figures."""
    fig.update_layout(
        font_family="Inter, -apple-system, sans-serif",
        font_color=COLORS['text'],
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=60 if title else 40, b=60),
        title=dict(
            text=title,
            font=dict(size=18, weight=600),
            x=0,
            xanchor='left'
        ) if title else None,
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor=COLORS['secondary'],
            borderwidth=0,
            font=dict(size=11)
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#E8E0D8',
            showline=True,
            linewidth=1,
            linecolor='#E8E0D8'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#E8E0D8',
            showline=True,
            linewidth=1,
            linecolor='#E8E0D8'
        ),
        hoverlabel=dict(
            font_family="Inter",
            font_size=12
        )
    )
    return fig


# ============================================================================
# Long-term Trend Charts
# ============================================================================

def plot_cpi_ppi_trend(df_cpi: pd.DataFrame, df_ppi: pd.DataFrame):
    """
    Create dual-line chart comparing CPI and PPI YoY trends.
    
    Based on Image 1 from visualization guide: "China Inflation Long-Term Cycle"
    """
    if df_cpi.empty and df_ppi.empty:
        return None
    
    fig = go.Figure()
    
    # CPI line
    if not df_cpi.empty and 'nt_yoy' in df_cpi.columns:
        fig.add_trace(go.Scatter(
            x=df_cpi['month'],
            y=df_cpi['nt_yoy'],
            name='CPI 同比',
            mode='lines',
            line=dict(color=COLORS['cpi'], width=2),
            hovertemplate='%{x|%Y-%m}<br>CPI: %{y:.1f}%<extra></extra>'
        ))
    
    # PPI line
    if not df_ppi.empty and 'ppi_yoy' in df_ppi.columns:
        fig.add_trace(go.Scatter(
            x=df_ppi['month'],
            y=df_ppi['ppi_yoy'],
            name='PPI 同比',
            mode='lines',
            line=dict(color=COLORS['ppi'], width=2),
            hovertemplate='%{x|%Y-%m}<br>PPI: %{y:.1f}%<extra></extra>'
        ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash='dash', line_color=COLORS['neutral'], line_width=1)
    
    fig = apply_chart_style(fig, title="CPI vs PPI 同比走势")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="同比变化 (%)",
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def plot_cpi_components(df_cpi: pd.DataFrame):
    """
    Create comparison chart of CPI components (National, Urban, Rural).
    """
    if df_cpi.empty:
        return None
    
    fig = go.Figure()
    
    components = [
        ('nt_yoy', '全国', COLORS['cpi']),
        ('town_yoy', '城市', COLORS['primary']),
        ('cnt_yoy', '农村', COLORS['ppi'])
    ]
    
    for col, name, color in components:
        if col in df_cpi.columns:
            fig.add_trace(go.Scatter(
                x=df_cpi['month'],
                y=df_cpi[col],
                name=name,
                mode='lines',
                line=dict(color=color, width=2)
            ))
    
    fig.add_hline(y=0, line_dash='dash', line_color=COLORS['neutral'], line_width=1)
    
    fig = apply_chart_style(fig, title="CPI 同比: 全国 vs 城市 vs 农村")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="同比 (%)",
        hovermode='x unified'
    )
    
    return fig


def plot_ppi_sectors(df_ppi: pd.DataFrame):
    """
    Create comparison chart of PPI by sector.
    """
    if df_ppi.empty:
        return None
    
    fig = go.Figure()
    
    sectors = [
        ('ppi_yoy', 'PPI总指数', COLORS['cpi']),
        ('ppi_mp_yoy', '生产资料', COLORS['primary']),
        ('ppi_cg_yoy', '生活资料', COLORS['ppi'])
    ]
    
    for col, name, color in sectors:
        if col in df_ppi.columns:
            fig.add_trace(go.Scatter(
                x=df_ppi['month'],
                y=df_ppi[col],
                name=name,
                mode='lines',
                line=dict(color=color, width=2)
            ))
    
    fig.add_hline(y=0, line_dash='dash', line_color=COLORS['neutral'], line_width=1)
    
    fig = apply_chart_style(fig, title="PPI 分类同比走势")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="同比 (%)",
        hovermode='x unified'
    )
    
    return fig


# ============================================================================
# Heatmap Charts
# ============================================================================

def plot_cpi_heatmap(df_cpi: pd.DataFrame, n_months: int = 12):
    """
    Create heatmap of CPI sub-items over recent months.
    
    Based on Image 8-9 from visualization guide.
    Colors: Red = inflation (positive), Green = deflation (negative)
    """
    if df_cpi.empty:
        return None
    
    # Get most recent n months
    df_recent = df_cpi.nlargest(n_months, 'month').sort_values('month')
    
    # Build heatmap matrix
    items_map = {
        'CPI 全国同比': 'nt_yoy',
        'CPI 城市同比': 'town_yoy',
        'CPI 农村同比': 'cnt_yoy',
        'CPI 全国环比': 'nt_mom',
        'CPI 城市环比': 'town_mom',
        'CPI 农村环比': 'cnt_mom'
    }
    
    # Create matrix
    matrix = []
    item_names = []
    
    for display_name, col_name in items_map.items():
        if col_name in df_recent.columns:
            row_values = df_recent[col_name].tolist()
            matrix.append(row_values)
            item_names.append(display_name)
    
    if not matrix:
        return None
    
    # Month labels
    month_labels = df_recent['month'].dt.strftime('%Y-%m').tolist()
    
    # Determine color scale range (symmetric around 0)
    all_values = [v for row in matrix for v in row if pd.notna(v)]
    if not all_values:
        return None
    max_abs = max(abs(min(all_values)), abs(max(all_values)))
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=month_labels,
        y=item_names,
        colorscale=HEATMAP_COLORSCALE,
        zmid=0,
        zmin=-max_abs,
        zmax=max_abs,
        text=[[f'{v:.1f}' if pd.notna(v) else '' for v in row] for row in matrix],
        texttemplate='%{text}',
        textfont=dict(size=10),
        hovertemplate='%{y}<br>%{x}: %{z:.2f}%<extra></extra>'
    ))
    
    fig = apply_chart_style(fig, title="CPI 分项热力图")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=300 + len(item_names) * 30
    )
    
    return fig


def plot_ppi_heatmap(df_ppi: pd.DataFrame, n_months: int = 12):
    """
    Create heatmap of PPI sub-sectors over recent months.
    
    Based on Image 10 from visualization guide.
    """
    if df_ppi.empty:
        return None
    
    # Get most recent n months
    df_recent = df_ppi.nlargest(n_months, 'month').sort_values('month')
    
    # PPI items mapping
    items_map = {
        'PPI 总指数同比': 'ppi_yoy',
        '生产资料同比': 'ppi_mp_yoy',
        '  - 采掘业': 'ppi_mp_qm_yoy',
        '  - 原料业': 'ppi_mp_rm_yoy',
        '  - 加工业': 'ppi_mp_p_yoy',
        '生活资料同比': 'ppi_cg_yoy',
        '  - 食品类': 'ppi_cg_f_yoy',
        '  - 衣着类': 'ppi_cg_c_yoy',
        '  - 日用品': 'ppi_cg_adu_yoy',
        '  - 耐用品': 'ppi_cg_dcg_yoy'
    }
    
    # Create matrix
    matrix = []
    item_names = []
    
    for display_name, col_name in items_map.items():
        if col_name in df_recent.columns:
            row_values = df_recent[col_name].tolist()
            matrix.append(row_values)
            item_names.append(display_name)
    
    if not matrix:
        return None
    
    month_labels = df_recent['month'].dt.strftime('%Y-%m').tolist()
    
    # Symmetric color scale
    all_values = [v for row in matrix for v in row if pd.notna(v)]
    if not all_values:
        return None
    max_abs = max(abs(min(all_values)), abs(max(all_values)))
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=month_labels,
        y=item_names,
        colorscale=HEATMAP_COLORSCALE,
        zmid=0,
        zmin=-max_abs,
        zmax=max_abs,
        text=[[f'{v:.1f}' if pd.notna(v) else '' for v in row] for row in matrix],
        texttemplate='%{text}',
        textfont=dict(size=10),
        hovertemplate='%{y}<br>%{x}: %{z:.2f}%<extra></extra>'
    ))
    
    fig = apply_chart_style(fig, title="PPI 分项热力图")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        height=350 + len(item_names) * 25
    )
    
    return fig


# ============================================================================
# Seasonality Charts
# ============================================================================

def plot_seasonality_chart(df: pd.DataFrame, metric_col: str = 'nt_mom', 
                           title: str = "CPI 环比季节性", n_years: int = 3):
    """
    Create seasonality overlay chart showing month-over-month patterns.
    
    Based on Image 4 from visualization guide: "CPI 环比季节"
    """
    if df.empty or metric_col not in df.columns:
        return None
    
    df = df.copy()
    df['year'] = df['month'].dt.year
    df['month_num'] = df['month'].dt.month
    
    # Get recent years
    recent_years = sorted(df['year'].unique())[-n_years:]
    
    fig = go.Figure()
    
    month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
                   '7月', '8月', '9月', '10月', '11月', '12月']
    
    for i, year in enumerate(recent_years):
        year_data = df[df['year'] == year].sort_values('month_num')
        
        fig.add_trace(go.Scatter(
            x=list(range(1, 13)),
            y=[year_data[year_data['month_num'] == m][metric_col].values[0] 
               if m in year_data['month_num'].values else None 
               for m in range(1, 13)],
            name=str(year),
            mode='lines+markers',
            line=dict(color=LINE_COLORS[i % len(LINE_COLORS)], width=2),
            marker=dict(size=6)
        ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash='dash', line_color=COLORS['neutral'], line_width=1)
    
    fig = apply_chart_style(fig, title=title)
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=month_names
        ),
        xaxis_title="",
        yaxis_title="环比 (%)",
        hovermode='x unified'
    )
    
    return fig


# ============================================================================
# MoM Trend Charts
# ============================================================================

def plot_mom_trend(df: pd.DataFrame, col: str, title: str):
    """
    Create month-over-month trend bar chart with color coding.
    Positive = red, Negative = green
    """
    if df.empty or col not in df.columns:
        return None
    
    df = df.copy()
    
    # Color based on value
    colors = [COLORS['positive'] if v >= 0 else COLORS['negative'] 
              for v in df[col].fillna(0)]
    
    fig = go.Figure(data=go.Bar(
        x=df['month'],
        y=df[col],
        marker_color=colors,
        hovertemplate='%{x|%Y-%m}<br>环比: %{y:.2f}%<extra></extra>'
    ))
    
    fig.add_hline(y=0, line_width=1, line_color=COLORS['neutral'])
    
    fig = apply_chart_style(fig, title=title)
    fig.update_layout(
        xaxis_title="",
        yaxis_title="环比 (%)",
        bargap=0.1
    )
    
    return fig


# ============================================================================
# Summary Metrics
# ============================================================================

def get_latest_metrics(df_cpi: pd.DataFrame, df_ppi: pd.DataFrame) -> dict:
    """
    Get latest CPI and PPI metrics for summary display.
    """
    metrics = {
        'cpi_yoy': None,
        'cpi_mom': None,
        'ppi_yoy': None,
        'ppi_mom': None,
        'cpi_date': None,
        'ppi_date': None,
        'cpi_yoy_change': None,
        'ppi_yoy_change': None
    }
    
    if not df_cpi.empty:
        latest = df_cpi.nlargest(1, 'month').iloc[0]
        prev = df_cpi.nlargest(2, 'month').iloc[1] if len(df_cpi) > 1 else None
        
        metrics['cpi_yoy'] = latest.get('nt_yoy')
        metrics['cpi_mom'] = latest.get('nt_mom')
        metrics['cpi_date'] = latest['month'].strftime('%Y-%m')
        
        if prev is not None and pd.notna(latest.get('nt_yoy')) and pd.notna(prev.get('nt_yoy')):
            metrics['cpi_yoy_change'] = latest.get('nt_yoy') - prev.get('nt_yoy')
    
    if not df_ppi.empty:
        latest = df_ppi.nlargest(1, 'month').iloc[0]
        prev = df_ppi.nlargest(2, 'month').iloc[1] if len(df_ppi) > 1 else None
        
        metrics['ppi_yoy'] = latest.get('ppi_yoy')
        metrics['ppi_mom'] = latest.get('ppi_mom')
        metrics['ppi_date'] = latest['month'].strftime('%Y-%m')
        
        if prev is not None and pd.notna(latest.get('ppi_yoy')) and pd.notna(prev.get('ppi_yoy')):
            metrics['ppi_yoy_change'] = latest.get('ppi_yoy') - prev.get('ppi_yoy')
    
    return metrics


# ============================================================================
# Deep Dive Charts
# ============================================================================

def plot_ppi_chain_trend(df_chain: pd.DataFrame):
    """
    Plot trends for PPI industry chain: Mining -> Raw Materials -> Processing.
    Shows the transmission of price changes from upstream to downstream.
    """
    if df_chain.empty:
        return None
    
    fig = go.Figure()
    
    chain_config = [
        ('采掘工业 (上游)', '#D97757'),  # Primary/Red
        ('原材料工业 (中游)', '#E8A838'),  # Warning/Yellow
        ('加工工业 (下游)', '#4A90A4'),  # CPI/Blue
        ('生活资料 (终端)', '#5C5653')   # Secondary/Gray
    ]
    
    for col, color in chain_config:
        if col in df_chain.columns:
            fig.add_trace(go.Scatter(
                x=df_chain['month'],
                y=df_chain[col],
                name=col,
                mode='lines',
                line=dict(color=color, width=2),
                hovertemplate='%{x|%Y-%m}<br>' + f'{col}: %{{y:.2f}}%<extra></extra>'
            ))
            
    fig.add_hline(y=0, line_dash='dash', line_color=COLORS['neutral'], line_width=1)
    
    fig = apply_chart_style(fig, title="PPI 产业链传导分析 (上游 -> 下游)")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="同比 (%)",
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def plot_scissors_difference(df_scissors: pd.DataFrame):
    """
    Plot PPI-CPI Scissors Difference.
    Scissors = PPI - CPI.
    Positive gap usually means upstream inflation squeezing downstream profits.
    Negative gap usually means downstream demand recovery or upstream deflation.
    """
    if df_scissors.empty:
        return None
    
    fig = go.Figure()
    
    # Add Scissors Line (PPI - CPI)
    fig.add_trace(go.Scatter(
        x=df_scissors['month'],
        y=df_scissors['ppi_cpi_scissors'],
        name='PPI - CPI 剪刀差',
        mode='lines',
        line=dict(color=COLORS['primary'], width=2),
        fill='tozeroy',  # Fill to zero to show positive/negative clearly
        fillcolor='rgba(217, 119, 87, 0.1)' # Light primary color
    ))
    
    # Add Internal Scissors (Production - Living)
    fig.add_trace(go.Scatter(
        x=df_scissors['month'],
        y=df_scissors['ppi_internal_scissors'],
        name='生产资料 - 生活资料 剪刀差',
        mode='lines',
        line=dict(color=COLORS['cpi'], width=1.5, dash='dot'),
        visible='legendonly' # Hide by default to keep it clean, user can toggle
    ))
    
    fig.add_hline(y=0, line_dash='dash', line_color=COLORS['neutral'], line_width=1)
    
    fig = apply_chart_style(fig, title="价格剪刀差分析 (PPI - CPI)")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="差值 (百分点)",
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

