import plotly.graph_objects as go


def _line_chart(df, y_col, name_map, title, normalized=False):
    if df.empty:
        return None
    fig = go.Figure()
    for code, sub in df.groupby('ts_code'):
        sub = sub.sort_values('trade_date')
        y = sub[y_col]
        if normalized and not sub.empty:
            base = y.iloc[0]
            if base == 0:
                continue
            y = y / base * 100
            y_title = f"{y_col} (Base=100)"
        else:
            y_title = y_col
        fig.add_trace(go.Scatter(
            x=sub['trade_date'],
            y=y,
            mode='lines',
            name=name_map.get(code, code)
        ))
    if not fig.data:
        return None
    fig.update_layout(
        title=title,
        xaxis=dict(title='Date'),
        yaxis=dict(title=y_title),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        height=500,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def plot_dc_price(df, name_map, normalized=False):
    return _line_chart(df, 'close', name_map, 'DC 指数价格走势', normalized)


def plot_dc_amount(df, name_map, normalized=False):
    return _line_chart(df, 'amount', name_map, '成交金额走势', normalized)


def plot_dc_pct(df, name_map):
    return _line_chart(df, 'pct_change', name_map, '涨跌幅走势', normalized=False)


def plot_dc_turnover(df, name_map):
    return _line_chart(df, 'turnover_rate', name_map, '换手率走势', normalized=False)
