import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Union


COLORS = {
    "primary": "#D97757",
    "accent": "#26A69A",
    "danger": "#EF5350",
    "muted": "#5C5653",
    "border": "#E8E0D8",
}


def _apply_style(fig, title: Optional[str] = None):
    fig.update_layout(
        title=title,
        font_family="Inter, PingFang SC",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=60 if title else 10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLORS["border"], zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["border"], zeroline=False)
    return fig


def _to_yi(value: Union[pd.Series, float, int]) -> Union[pd.Series, float]:
    return value / 1e8


def plot_profitability_trend(df_income: pd.DataFrame):
    if df_income.empty or "end_date_dt" not in df_income.columns:
        return None

    data = df_income.copy().sort_values("end_date_dt")
    for col in ["revenue", "n_income"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    data["revenue_yi"] = _to_yi(data.get("revenue"))
    data["n_income_yi"] = _to_yi(data.get("n_income"))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["end_date_dt"],
            y=data["revenue_yi"],
            name="Revenue (亿元)",
            line=dict(color=COLORS["primary"], width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["end_date_dt"],
            y=data["n_income_yi"],
            name="Net Income (亿元)",
            line=dict(color=COLORS["accent"], width=2),
        )
    )
    fig = _apply_style(fig, title="Profitability Trend (Revenue vs Net Income)")
    fig.update_yaxes(title_text="亿元")
    fig.update_xaxes(title_text="Report Period")
    return fig


def plot_dupont_treemap(df_indicator: pd.DataFrame):
    if df_indicator.empty:
        return None

    latest = df_indicator.dropna(subset=["end_date_dt"]).sort_values("end_date_dt").iloc[-1]

    profit_to_gr = pd.to_numeric(latest.get("profit_to_gr"), errors="coerce")
    assets_turn = pd.to_numeric(latest.get("assets_turn"), errors="coerce")
    eq_mult = pd.to_numeric(latest.get("dp_assets_to_eqt"), errors="coerce")
    roe = pd.to_numeric(latest.get("roe"), errors="coerce")

    # profit_to_gr is typically percentage-like in Tushare; keep display as %.
    if pd.notna(profit_to_gr) and pd.notna(assets_turn) and pd.notna(eq_mult):
        dupont_roe = (profit_to_gr / 100.0) * assets_turn * eq_mult * 100.0
    else:
        dupont_roe = np.nan

    rows = [
        {"factor": "Profit Margin (profit_to_gr, %)", "value": float(profit_to_gr) if pd.notna(profit_to_gr) else np.nan},
        {"factor": "Asset Turnover (assets_turn)", "value": float(assets_turn) if pd.notna(assets_turn) else np.nan},
        {"factor": "Equity Multiplier (dp_assets_to_eqt)", "value": float(eq_mult) if pd.notna(eq_mult) else np.nan},
    ]
    df = pd.DataFrame(rows)
    df["size"] = 1

    fig = px.treemap(
        df,
        path=["factor"],
        values="size",
        color="value",
        color_continuous_scale="RdYlGn",
    )
    fig = _apply_style(fig, title="DuPont ROE Decomposition (Latest Period)")
    fig.update_traces(texttemplate="%{label}<br>%{color:.2f}")
    fig.update_layout(coloraxis_colorbar_title="Value")

    subtitle = ""
    if pd.notna(roe):
        subtitle += f"ROE: {roe:.2f}%"
    if pd.notna(dupont_roe):
        subtitle += (" | " if subtitle else "") + f"DuPont ROE (calc): {dupont_roe:.2f}%"
    if subtitle:
        fig.update_layout(title={"text": f"DuPont ROE Decomposition (Latest Period)<br><sup>{subtitle}</sup>"})
    return fig


def plot_leverage_trend(df_balance: pd.DataFrame):
    if df_balance.empty or "end_date_dt" not in df_balance.columns:
        return None

    data = df_balance.copy().sort_values("end_date_dt")
    for col in ["total_assets", "total_liab"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    data["debt_ratio"] = data["total_liab"] / data["total_assets"]

    fig = px.line(data, x="end_date_dt", y="debt_ratio", markers=True)
    fig = _apply_style(fig, title="Balance Sheet Leverage (Total Liabilities / Total Assets)")
    fig.update_yaxes(title_text="Debt Ratio", tickformat=".0%")
    fig.update_xaxes(title_text="Report Period")
    return fig


def plot_balance_stack(df_balance: pd.DataFrame):
    if df_balance.empty or "end_date_dt" not in df_balance.columns:
        return None
    data = df_balance.copy().sort_values("end_date_dt")
    for col in ["total_liab", "total_hldr_eqy_exc_min_int"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data["end_date_dt"],
            y=_to_yi(data["total_liab"]),
            name="Total Liabilities (亿元)",
            marker_color=COLORS["danger"],
            opacity=0.7,
        )
    )
    fig.add_trace(
        go.Bar(
            x=data["end_date_dt"],
            y=_to_yi(data["total_hldr_eqy_exc_min_int"]),
            name="Equity (亿元)",
            marker_color=COLORS["accent"],
            opacity=0.7,
        )
    )
    fig.update_layout(barmode="stack")
    fig = _apply_style(fig, title="Assets Composition Proxy (Liabilities + Equity)")
    fig.update_yaxes(title_text="亿元")
    fig.update_xaxes(title_text="Report Period")
    return fig


def plot_balance_sankey(df_balance: pd.DataFrame):
    if df_balance.empty:
        return None
    latest = df_balance.dropna(subset=["end_date_dt"]).sort_values("end_date_dt").iloc[-1]
    assets = pd.to_numeric(latest.get("total_assets"), errors="coerce")
    liab = pd.to_numeric(latest.get("total_liab"), errors="coerce")
    eq = pd.to_numeric(latest.get("total_hldr_eqy_exc_min_int"), errors="coerce")
    if pd.isna(assets) or (pd.isna(liab) and pd.isna(eq)):
        return None

    assets_yi = float(_to_yi(assets)) if pd.notna(assets) else 0.0
    liab_yi = float(_to_yi(liab)) if pd.notna(liab) else 0.0
    eq_yi = float(_to_yi(eq)) if pd.notna(eq) else 0.0

    labels = ["Total Assets", "Liabilities", "Equity"]
    sources = [0, 0]
    targets = [1, 2]
    values = [liab_yi, eq_yi]

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(label=labels, pad=15, thickness=18, color=[COLORS["primary"], COLORS["danger"], COLORS["accent"]]),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=["rgba(239,83,80,0.35)", "rgba(38,166,154,0.35)"]
                ),
            )
        ]
    )
    fig = _apply_style(fig, title="Balance Sheet Sankey (Latest Period, 亿元)")
    fig.update_layout(height=420)
    return fig


def plot_cashflow_timeseries(df_cashflow: pd.DataFrame):
    if df_cashflow.empty or "end_date_dt" not in df_cashflow.columns:
        return None

    data = df_cashflow.copy().sort_values("end_date_dt")
    for col in ["n_cashflow_act", "n_cashflow_inv_act", "n_cash_flows_fnc_act"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
            data[f"{col}_yi"] = _to_yi(data[col])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["end_date_dt"], y=data.get("n_cashflow_act_yi"), name="Operating (亿元)", line=dict(color=COLORS["accent"], width=2)))
    fig.add_trace(go.Scatter(x=data["end_date_dt"], y=data.get("n_cashflow_inv_act_yi"), name="Investing (亿元)", line=dict(color=COLORS["primary"], width=2)))
    fig.add_trace(go.Scatter(x=data["end_date_dt"], y=data.get("n_cash_flows_fnc_act_yi"), name="Financing (亿元)", line=dict(color=COLORS["danger"], width=2)))
    fig = _apply_style(fig, title="Cashflow Net (Operating / Investing / Financing)")
    fig.update_yaxes(title_text="亿元")
    fig.update_xaxes(title_text="Report Period")
    return fig


def plot_cashflow_waterfall(df_cashflow: pd.DataFrame):
    if df_cashflow.empty:
        return None
    latest = df_cashflow.dropna(subset=["end_date_dt"]).sort_values("end_date_dt").iloc[-1]

    beg = pd.to_numeric(latest.get("c_cash_equ_beg_period"), errors="coerce")
    op = pd.to_numeric(latest.get("n_cashflow_act"), errors="coerce")
    inv = pd.to_numeric(latest.get("n_cashflow_inv_act"), errors="coerce")
    fin = pd.to_numeric(latest.get("n_cash_flows_fnc_act"), errors="coerce")
    fx = pd.to_numeric(latest.get("eff_fx_flu_cash"), errors="coerce")
    end = pd.to_numeric(latest.get("c_cash_equ_end_period"), errors="coerce")

    measures = ["absolute", "relative", "relative", "relative", "relative", "total"]
    labels = ["Begin", "Operating", "Investing", "Financing", "FX", "End"]
    values = [beg, op, inv, fin, fx, end]
    values_yi = [float(_to_yi(v)) if pd.notna(v) else 0.0 for v in values]

    fig = go.Figure(
        go.Waterfall(
            measure=measures,
            x=labels,
            y=values_yi,
            connector={"line": {"color": COLORS["border"]}},
            increasing={"marker": {"color": COLORS["accent"]}},
            decreasing={"marker": {"color": COLORS["danger"]}},
            totals={"marker": {"color": COLORS["primary"]}},
        )
    )
    fig = _apply_style(fig, title="Cashflow Waterfall (Latest Period, 亿元)")
    fig.update_yaxes(title_text="亿元")
    return fig


def plot_forecast_vs_actual(df_forecast: pd.DataFrame, df_express: pd.DataFrame, df_income: pd.DataFrame):
    if df_forecast.empty:
        return None

    fc = df_forecast.dropna(subset=["end_date_dt"]).sort_values("end_date_dt").iloc[-1]
    end_date = fc.get("end_date")

    min_wan = pd.to_numeric(fc.get("net_profit_min"), errors="coerce")
    max_wan = pd.to_numeric(fc.get("net_profit_max"), errors="coerce")
    # forecast net profit is 万元
    min_yi = float(min_wan) / 1e4 if pd.notna(min_wan) else np.nan
    max_yi = float(max_wan) / 1e4 if pd.notna(max_wan) else np.nan

    actual_yi = np.nan
    if not df_express.empty and end_date is not None and "end_date" in df_express.columns:
        hit = df_express[df_express["end_date"].astype(str) == str(end_date)]
        if not hit.empty:
            actual = pd.to_numeric(hit.sort_values("ann_date").iloc[-1].get("n_income"), errors="coerce")
            actual_yi = float(_to_yi(actual)) if pd.notna(actual) else np.nan

    if pd.isna(actual_yi) and not df_income.empty and end_date is not None and "end_date" in df_income.columns:
        hit = df_income[df_income["end_date"].astype(str) == str(end_date)]
        if not hit.empty:
            actual = pd.to_numeric(hit.sort_values("ann_date").iloc[-1].get("n_income"), errors="coerce")
            actual_yi = float(_to_yi(actual)) if pd.notna(actual) else np.nan

    fig = go.Figure()
    if pd.notna(min_yi) and pd.notna(max_yi):
        fig.add_trace(
            go.Bar(
                x=["Forecast Range"],
                y=[max_yi - min_yi],
                base=[min_yi],
                marker_color="rgba(217,119,87,0.35)",
                name="Forecast Range",
                hovertemplate="Min: %{base:.2f} 亿<br>Max: %{y:.2f} 亿<extra></extra>",
            )
        )
    if pd.notna(actual_yi):
        fig.add_trace(
            go.Scatter(
                x=["Forecast Range"],
                y=[actual_yi],
                mode="markers",
                marker=dict(size=12, color=COLORS["accent"], line=dict(color="white", width=1)),
                name="Actual (Express/Income)",
                hovertemplate="Actual: %{y:.2f} 亿<extra></extra>",
            )
        )
    fig = _apply_style(fig, title=f"Forecast vs Actual Net Profit (End Date: {end_date})")
    fig.update_yaxes(title_text="Net Profit (亿元)")
    return fig


def plot_mainbz_pie(df_mainbz: pd.DataFrame):
    if df_mainbz.empty or "end_date_dt" not in df_mainbz.columns:
        return None
    latest_end = df_mainbz["end_date_dt"].max()
    data = df_mainbz[df_mainbz["end_date_dt"] == latest_end].copy()
    if data.empty:
        return None
    data["bz_sales"] = pd.to_numeric(data["bz_sales"], errors="coerce")
    fig = px.pie(data, names="bz_item", values="bz_sales", hole=0.45)
    fig = _apply_style(fig, title=f"Main Business Revenue Mix (Latest: {latest_end.date()})")
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def plot_indicator_heatmap(df_indicator: pd.DataFrame):
    if df_indicator.empty or "end_date_dt" not in df_indicator.columns:
        return None

    data = df_indicator.copy().sort_values("end_date_dt")
    cols = [
        ("roe", "ROE%"),
        ("debt_to_assets", "Debt/Assets%"),
        ("ocf_to_or", "OCF/Revenue%"),
        ("netprofit_margin", "Net Profit Margin%"),
        ("current_ratio", "Current Ratio"),
        ("quick_ratio", "Quick Ratio"),
    ]
    keep = [c for c, _ in cols if c in data.columns]
    if not keep:
        return None

    hm = data.set_index("end_date_dt")[keep]
    hm = hm.apply(pd.to_numeric, errors="coerce")
    hm = hm.T
    label_map = {c: lbl for c, lbl in cols}
    hm.index = [label_map.get(i, i) for i in hm.index]

    fig = px.imshow(
        hm,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="Key Financial Indicators Heatmap",
    )
    fig = _apply_style(fig)
    fig.update_layout(coloraxis_colorbar_title="Value")
    return fig


def plot_financial_health_gauge(score: Optional[float], title: str = "Financial Health Score"):
    if score is None or np.isnan(score):
        return None
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score),
            number={"suffix": "/100"},
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": COLORS["primary"]},
                "steps": [
                    {"range": [0, 40], "color": "#FFEBEE"},
                    {"range": [40, 70], "color": "#FFF8E1"},
                    {"range": [70, 100], "color": "#E8F5E9"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=60, b=20), font_family="Inter, PingFang SC")
    return fig
