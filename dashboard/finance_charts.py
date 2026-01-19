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


def plot_dupont_five_factor(df_indicator: pd.DataFrame, df_income: pd.DataFrame = None, df_balance: pd.DataFrame = None):
    """
    Create a 5-factor DuPont ROE decomposition diagram using clean table/indicator style.
    
    五因素杜邦分解:
    ROE = 税负系数 × 利息负担 × 经营利润率 × 资产周转率 × 权益乘数
        = (净利润/税前利润) × (税前利润/息税前利润) × (息税前利润/营收) × (营收/资产) × (资产/权益)
    
    Returns dict with all factors for rendering in Streamlit.
    """
    result = {
        "roe": None,
        "factors": [],
        "formula": "",
        "dupont_roe": None,
    }
    
    if df_indicator.empty:
        return result

    latest = df_indicator.dropna(subset=["end_date_dt"]).sort_values("end_date_dt").iloc[-1]

    # Basic 3-factor data
    profit_margin = pd.to_numeric(latest.get("profit_to_gr"), errors="coerce")  # 净利率
    assets_turn = pd.to_numeric(latest.get("assets_turn"), errors="coerce")     # 资产周转率
    eq_mult = pd.to_numeric(latest.get("dp_assets_to_eqt"), errors="coerce")    # 权益乘数
    roe = pd.to_numeric(latest.get("roe"), errors="coerce")
    
    # Get detailed data for 5-factor
    net_income = ebt = ebit = revenue = total_assets = equity = None
    
    if df_income is not None and not df_income.empty:
        inc_latest = df_income.sort_values("end_date", ascending=False).iloc[0]
        net_income = pd.to_numeric(inc_latest.get("n_income"), errors="coerce")
        revenue = pd.to_numeric(inc_latest.get("revenue"), errors="coerce")
        # EBT = 税前利润 = 利润总额
        ebt = pd.to_numeric(inc_latest.get("total_profit"), errors="coerce")
        # EBIT ≈ 利润总额 + 财务费用
        fin_exp = pd.to_numeric(inc_latest.get("fin_exp"), errors="coerce")
        if pd.notna(ebt) and pd.notna(fin_exp):
            ebit = ebt + fin_exp
        elif pd.notna(ebt):
            ebit = ebt
    
    if df_balance is not None and not df_balance.empty:
        bal_latest = df_balance.sort_values("end_date", ascending=False).iloc[0]
        total_assets = pd.to_numeric(bal_latest.get("total_assets"), errors="coerce")
        equity = pd.to_numeric(bal_latest.get("total_hldr_eqy_exc_min_int"), errors="coerce")
        if pd.isna(equity):
            equity = pd.to_numeric(bal_latest.get("total_hldr_eqy_inc_min_int"), errors="coerce")
    
    result["roe"] = roe
    
    # Calculate 5 factors
    # 1. 税负系数 = 净利润 / 税前利润
    tax_burden = net_income / ebt if pd.notna(net_income) and pd.notna(ebt) and ebt != 0 else None
    
    # 2. 利息负担 = 税前利润 / 息税前利润
    interest_burden = ebt / ebit if pd.notna(ebt) and pd.notna(ebit) and ebit != 0 else None
    
    # 3. 经营利润率 = 息税前利润 / 营业收入
    operating_margin = (ebit / revenue * 100) if pd.notna(ebit) and pd.notna(revenue) and revenue != 0 else None
    
    # 4. 资产周转率 (from fina_indicator)
    asset_turnover = assets_turn
    
    # 5. 权益乘数 (from fina_indicator)
    equity_multiplier = eq_mult
    
    def fmt_yi(val):
        if pd.notna(val):
            return f"{val/1e8:.1f}亿"
        return "-"
    
    def fmt_pct(val):
        if pd.notna(val):
            return f"{val:.1f}%"
        return "-"
    
    def fmt_ratio(val):
        if pd.notna(val):
            return f"{val:.2f}"
        return "-"
    
    # Build factors list with explanation
    factors = [
        {
            "name": "税负系数",
            "value": fmt_ratio(tax_burden),
            "formula": "净利润 / 税前利润",
            "components": f"{fmt_yi(net_income)} / {fmt_yi(ebt)}",
            "desc": "税收对利润的影响，越接近1说明税负越轻",
            "raw": tax_burden,
        },
        {
            "name": "利息负担",
            "value": fmt_ratio(interest_burden),
            "formula": "税前利润 / 息税前利润",
            "components": f"{fmt_yi(ebt)} / {fmt_yi(ebit)}",
            "desc": "债务利息对利润的影响，越接近1说明利息负担越轻",
            "raw": interest_burden,
        },
        {
            "name": "经营利润率",
            "value": fmt_pct(operating_margin),
            "formula": "息税前利润 / 营业收入",
            "components": f"{fmt_yi(ebit)} / {fmt_yi(revenue)}",
            "desc": "核心业务盈利能力，不含税和利息影响",
            "raw": operating_margin,
        },
        {
            "name": "资产周转率",
            "value": fmt_ratio(asset_turnover),
            "formula": "营业收入 / 总资产",
            "components": f"{fmt_yi(revenue)} / {fmt_yi(total_assets)}",
            "desc": "资产运营效率，越高说明资产利用越充分",
            "raw": asset_turnover,
        },
        {
            "name": "权益乘数",
            "value": fmt_ratio(equity_multiplier),
            "formula": "总资产 / 股东权益",
            "components": f"{fmt_yi(total_assets)} / {fmt_yi(equity)}",
            "desc": "财务杠杆程度，越高说明负债越多",
            "raw": equity_multiplier,
        },
    ]
    
    result["factors"] = factors
    
    # Calculate DuPont ROE from 5 factors
    if all(f["raw"] is not None and pd.notna(f["raw"]) for f in factors):
        dupont_roe = (tax_burden * interest_burden * (operating_margin/100) * asset_turnover * equity_multiplier) * 100
        result["dupont_roe"] = dupont_roe
        result["formula"] = f"{fmt_ratio(tax_burden)} × {fmt_ratio(interest_burden)} × {fmt_pct(operating_margin)} × {fmt_ratio(asset_turnover)} × {fmt_ratio(equity_multiplier)} = {fmt_pct(dupont_roe)}"
    
    return result


def calculate_dupont_five_factor_series(df_income: pd.DataFrame, df_balance: pd.DataFrame, df_indicator: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 5-factor DuPont decomposition for all available periods.
    Returns DataFrame with columns: end_date, tax_burden, interest_burden, operating_margin, asset_turnover, equity_multiplier, roe
    """
    if df_income.empty or df_balance.empty or df_indicator.empty:
        return pd.DataFrame()
    
    # Merge income and balance by end_date
    df_inc = df_income.copy()
    df_bal = df_balance.copy()
    df_ind = df_indicator.copy()
    
    # Ensure end_date is string for merging
    for df in [df_inc, df_bal, df_ind]:
        if "end_date" in df.columns:
            df["end_date"] = df["end_date"].astype(str)
    
    # Merge datasets
    merged = df_inc.merge(df_bal, on="end_date", how="inner", suffixes=("_inc", "_bal"))
    merged = merged.merge(df_ind[["end_date", "assets_turn", "dp_assets_to_eqt", "roe"]], on="end_date", how="left")
    
    if merged.empty:
        return pd.DataFrame()
    
    results = []
    for _, row in merged.iterrows():
        end_date = row["end_date"]
        
        net_income = pd.to_numeric(row.get("n_income"), errors="coerce")
        revenue = pd.to_numeric(row.get("revenue"), errors="coerce")
        ebt = pd.to_numeric(row.get("total_profit"), errors="coerce")
        fin_exp = pd.to_numeric(row.get("fin_exp"), errors="coerce")
        ebit = ebt + fin_exp if pd.notna(ebt) and pd.notna(fin_exp) else ebt
        
        total_assets = pd.to_numeric(row.get("total_assets"), errors="coerce")
        equity = pd.to_numeric(row.get("total_hldr_eqy_exc_min_int"), errors="coerce")
        if pd.isna(equity):
            equity = pd.to_numeric(row.get("total_hldr_eqy_inc_min_int"), errors="coerce")
        
        assets_turn = pd.to_numeric(row.get("assets_turn"), errors="coerce")
        eq_mult = pd.to_numeric(row.get("dp_assets_to_eqt"), errors="coerce")
        roe = pd.to_numeric(row.get("roe"), errors="coerce")
        
        # Calculate 5 factors
        tax_burden = net_income / ebt if pd.notna(net_income) and pd.notna(ebt) and ebt != 0 else None
        interest_burden = ebt / ebit if pd.notna(ebt) and pd.notna(ebit) and ebit != 0 else None
        operating_margin = (ebit / revenue * 100) if pd.notna(ebit) and pd.notna(revenue) and revenue != 0 else None
        
        results.append({
            "end_date": end_date,
            "税负系数": tax_burden,
            "利息负担": interest_burden,
            "经营利润率": operating_margin,
            "资产周转率": assets_turn,
            "权益乘数": eq_mult,
            "ROE": roe,
        })
    
    df_result = pd.DataFrame(results)
    df_result = df_result.sort_values("end_date", ascending=True)
    return df_result


def plot_dupont_trend(df_income: pd.DataFrame, df_balance: pd.DataFrame, df_indicator: pd.DataFrame):
    """
    Create a line chart showing 5-factor DuPont trend over time.
    """
    df_trend = calculate_dupont_five_factor_series(df_income, df_balance, df_indicator)
    
    if df_trend.empty or len(df_trend) < 2:
        return None
    
    # Create subplot with 2 rows: ratios (top) and percentages (bottom)
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("比率型因素 (越接近1越好)", "百分比型因素"),
        row_heights=[0.5, 0.5],
    )
    
    # Row 1: Ratio factors (税负系数, 利息负担, 资产周转率, 权益乘数)
    ratio_factors = ["税负系数", "利息负担", "资产周转率", "权益乘数"]
    colors = ["#26A69A", "#5C9BD1", "#F4A261", "#CE93D8"]
    
    for i, (factor, color) in enumerate(zip(ratio_factors, colors)):
        if factor in df_trend.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_trend["end_date"],
                    y=df_trend[factor],
                    mode="lines+markers",
                    name=factor,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                ),
                row=1, col=1,
            )
    
    # Row 2: Percentage factors (经营利润率, ROE)
    pct_factors = ["经营利润率", "ROE"]
    pct_colors = ["#81C784", COLORS["primary"]]
    
    for factor, color in zip(pct_factors, pct_colors):
        if factor in df_trend.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_trend["end_date"],
                    y=df_trend[factor],
                    mode="lines+markers",
                    name=factor,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                ),
                row=2, col=1,
            )
    
    fig.update_layout(
        title=dict(text="杜邦五因素趋势", font=dict(size=14)),
        height=400,
        font=dict(family="Inter, PingFang SC", size=11),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=40, r=20, t=80, b=40),
        hovermode="x unified",
    )
    
    # Format dates as YYYY-MM-DD for display to be cleaner
    # Tushare dates are YYYYMMDD string, convert to Q format
    def format_date_q(d):
        s = str(d)
        if len(s) == 8:
            yyyy = s[:4]
            mm = s[4:6]
            if mm == "03": return f"{yyyy} Q1"
            if mm == "06": return f"{yyyy} H1"  # Or Q2
            if mm == "09": return f"{yyyy} Q3"
            if mm == "12": return f"{yyyy} Q4"
            return f"{yyyy}-{mm}"
        return s
        
    tick_vals = df_trend["end_date"].tolist()
    tick_text = [format_date_q(d) for d in tick_vals]
    
    # Grid styling
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor=COLORS["border"],
        tickmode="array", tickvals=tick_vals, ticktext=tick_text
    )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS["border"])
    fig.update_yaxes(title_text="比率", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    
    return fig


# Keep the old function name as alias for backward compatibility
def plot_dupont_treemap(df_indicator: pd.DataFrame, df_income: pd.DataFrame = None, df_balance: pd.DataFrame = None):
    """Deprecated: Use plot_dupont_five_factor instead. Returns data dict for Streamlit rendering."""
    return plot_dupont_five_factor(df_indicator, df_income, df_balance)


def plot_dupont_waterfall(df_indicator: pd.DataFrame):
    """
    Alternative: Create a waterfall chart showing DuPont decomposition.
    Shows how each factor contributes to the final ROE.
    """
    if df_indicator.empty:
        return None

    latest = df_indicator.dropna(subset=["end_date_dt"]).sort_values("end_date_dt").iloc[-1]

    profit_margin = pd.to_numeric(latest.get("profit_to_gr"), errors="coerce")
    assets_turn = pd.to_numeric(latest.get("assets_turn"), errors="coerce")
    eq_mult = pd.to_numeric(latest.get("dp_assets_to_eqt"), errors="coerce")
    roe = pd.to_numeric(latest.get("roe"), errors="coerce")
    
    if not all(pd.notna(x) for x in [profit_margin, assets_turn, eq_mult]):
        return None
    
    # Calculate contribution of each factor
    # ROE = NPM × AT × EM
    # Log decomposition: ln(ROE) = ln(NPM) + ln(AT) + ln(EM)
    
    npm_pct = profit_margin  # Already in %
    at_contribution = assets_turn * 100  # Convert to percentage impact
    em_contribution = eq_mult * 100  # Convert to percentage impact
    
    fig = go.Figure(go.Waterfall(
        name="DuPont",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["净利率", "× 资产周转率", "× 权益乘数", "= ROE"],
        textposition="outside",
        text=[f"{npm_pct:.1f}%", f"{assets_turn:.2f}", f"{eq_mult:.2f}", f"{roe:.1f}%"],
        y=[npm_pct, 0, 0, 0],  # Simplified visual
        connector={"line": {"color": COLORS["border"]}},
        increasing={"marker": {"color": COLORS["accent"]}},
        decreasing={"marker": {"color": COLORS["danger"]}},
        totals={"marker": {"color": COLORS["primary"]}},
    ))
    
    fig = _apply_style(fig, title="杜邦分解 / DuPont Decomposition")
    fig.update_layout(height=300, showlegend=False)
    
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


def plot_mainbz_structure_trend(df_mainbz: pd.DataFrame, type_filter: str = None):
    """
    Plot main business revenue composition trend as a stacked bar chart.
    type_filter: 'P' for Product, 'D' for Region
    """
    if df_mainbz.empty:
        return None

    # Filter by type
    data = df_mainbz.copy()
    if type_filter:
        if "bz_code" in data.columns:
            if type_filter == 'P':
                data = data[data["bz_code"] == 'P']
            elif type_filter == 'D':
                data = data[data["bz_code"] == 'D']
    
    if data.empty:
        return None
        
    # Process dates
    if "end_date_dt" not in data.columns and "end_date" in data.columns:
        data["end_date_dt"] = _parse_yyyymmdd(data["end_date"])
        
    # Filter last 5 years to keep it readable, or top N periods
    # data = data.sort_values("end_date_dt")
    
    # Handle "Others" grouping
    # Strategy: Find top N items by total revenue across all periods to keep colors consistent
    data["bz_sales"] = pd.to_numeric(data["bz_sales"], errors="coerce").fillna(0)
    
    # Aggregate sales by item
    item_totals = data.groupby("bz_item")["bz_sales"].sum().sort_values(ascending=False)
    
    top_n = 7
    if len(item_totals) > top_n:
        top_items = item_totals.head(top_n).index.tolist()
        data["bz_item_grouped"] = data["bz_item"].apply(lambda x: x if x in top_items else "Others")
    else:
        data["bz_item_grouped"] = data["bz_item"]
        
    # Aggregate by date and grouped item
    df_plot = data.groupby(["end_date_dt", "bz_item_grouped"])["bz_sales"].sum().reset_index()
    
    # Convert to 亿元
    df_plot["bz_sales_yi"] = df_plot["bz_sales"] / 1e8
    df_plot = df_plot.sort_values(["end_date_dt", "bz_sales_yi"], ascending=[True, False])

    fig = px.bar(
        df_plot,
        x="end_date_dt",
        y="bz_sales_yi",
        color="bz_item_grouped",
        title=f"Revenue Mix Trend ({'Product' if type_filter=='P' else 'Region' if type_filter=='D' else 'All'})",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    
    fig = _apply_style(fig)
    fig.update_layout(
        xaxis_title="Report Period",
        yaxis_title="Revenue (亿元)",
        legend_title=None,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


def plot_income_sankey(df_mainbz: pd.DataFrame, df_income: pd.DataFrame):
    """
    Create a detailed Income Statement Sankey diagram with hierarchical flow:
    Level 1: [Products] -> [Total Revenue]
    Level 2: [Total Revenue] -> [Operating Cost] & [Gross Profit]
    Level 3: [Gross Profit] -> [Expenses] & [Operating Profit]
             [Other Income] -> [Operating Profit]
    Level 4: [Operating Profit] -> [Income Tax] & [Net Profit]
    """
    if df_income.empty:
        return None
        
    # Standardize dates
    df_inc = df_income.copy()
    df_mb = df_mainbz.copy()
    
    if "end_date" in df_inc.columns:
        df_inc["end_date"] = df_inc["end_date"].astype(str)
    if not df_mb.empty and "end_date" in df_mb.columns:
        df_mb["end_date"] = df_mb["end_date"].astype(str)
        
    # Find latest date that exists in BOTH (for valid product breakdown)
    # If no mainbz data, we show total revenue    
    # 2. Match dates
    import streamlit as st
    if not df_mb.empty:
        # Filter for Products only
        bz_df = df_mb[df_mb["bz_code"] == 'P']
        
        bz_dates = set(bz_df["end_date"].unique())
        inc_dates = set(df_income["end_date"].unique())
        common_dates = bz_dates.intersection(inc_dates)
        
        if common_dates:
            target_date = max(common_dates)
        else:
            target_date = df_income["end_date"].max()
            # st.warning(f"Sankey: No common date found. Using latest income date: {target_date}")
    else:
        target_date = df_income["end_date"].max()
        
    # 3. Get Income Data
    inc_rows = df_income[df_income["end_date"] == target_date]
    if inc_rows.empty:
        st.warning(f"Sankey Error: No income data for {target_date}")
        return None
        
    inc = inc_rows.iloc[0]
    
    # 4. Get MainBz Data for that date
    if not df_mb.empty:
        bz_df = df_mb[(df_mb["end_date"] == target_date) & (df_mb["bz_code"] == 'P')]
        
    # --- Check Data Sufficiency ---
    # We need at least Revenue
    revenue_val = pd.to_numeric(inc.get("revenue"), errors="coerce")
    if pd.isna(revenue_val) or revenue_val == 0:
        revenue_val = pd.to_numeric(inc.get("total_revenue"), errors="coerce")
        
    if (pd.isna(revenue_val) or revenue_val <= 0) and bz_df.empty:
        st.warning("Sankey Error: No Revenue and No Product Data")
        return None
            
    # --- Prepare Data Values (Yi 元) ---
    
    # Revenue
    revenue_val = pd.to_numeric(inc.get("revenue"), errors="coerce")
    if pd.isna(revenue_val) or revenue_val == 0:
        revenue_val = pd.to_numeric(inc.get("total_revenue"), errors="coerce")
    val_rev_total = (revenue_val or 0) / 1e8
    
    # Cost
    val_cost_total = pd.to_numeric(inc.get("oper_cost"), errors="coerce")
    if pd.isna(val_cost_total):
        val_cost_total = 0 
    
    val_cost_total = val_cost_total / 1e8 
        
    # Gross Profit (Calculated)
    # If explicit GP is available, use it. But standard IS doesn't have "Gross Profit" field usually.
    # Revenue - Cost
    val_gp = val_rev_total - val_cost_total
    
    # Expenses
    def get_val_yi(col):
        v = pd.to_numeric(inc.get(col), errors="coerce")
        return v / 1e8 if pd.notna(v) else 0

    val_sell = get_val_yi("sell_exp")
    val_admin = get_val_yi("admin_exp")
    val_fin = get_val_yi("fin_exp") # Can be negative, get_val_yi handles it, we take max(0) later
    val_rd = get_val_yi("rd_exp")
    val_tax_surch = get_val_yi("biz_tax_surchg")
    
    # Operating Profit
    val_op_profit = pd.to_numeric(inc.get("operate_profit"), errors="coerce") / 1e8
    
    # Other Income / Investment Income (The bridge between GP-Expenses and OpProfit)
    # OpProfit = GP - Expenses + OtherIncome
    # OtherIncome = OpProfit - (GP - Expenses)
    total_expenses = val_sell + val_admin + val_rd + max(0, val_fin) + val_tax_surch
    
    val_gp_residual = val_gp - total_expenses
    val_other_income = 0
    
    # Flow from GP to OpProfit
    val_gp_to_op = max(0, val_gp_residual)
    
    # If OpProfit > Residual, implies Other Income positive
    if val_op_profit > val_gp_residual:
        val_other_income = val_op_profit - val_gp_residual
    
    # Net Profit
    val_income_tax = pd.to_numeric(inc.get("income_tax"), errors="coerce") / 1e8 or 0
    val_net_income = pd.to_numeric(inc.get("n_income"), errors="coerce") / 1e8
    
    # --- Build Sankey Nodes & Links ---
    
    nodes = []
    links = []
    node_map = {} 
    
    def get_node_idx(name, color=None):
        if name not in node_map:
            node_map[name] = len(nodes)
            nodes.append({"label": name, "color": color})
        return node_map[name]
    
    # Colors
    c_rev = COLORS["primary"]     # Total Revenue
    c_prod = "#90CAF9"           # Product (Lighter Blue)
    c_cost = COLORS["danger"]     # Cost
    c_gp = COLORS["accent"]       # GP (Teal)
    c_prof = "#66BB6A"           # Net Profit (Green)
    c_exp  = "#B0BEC5"           # Expense (Grey)
    c_other = "#FFB74D"          # Other Income (Orange)
    
    # --- Level 1: Products -> Total Revenue & Cost Details ---
    
    idx_total_rev = get_node_idx("主营业务收入", c_rev)
    
    # We need to track individual product costs to split the 'Operating Cost' node
    product_costs = [] # list of (name, value)
    
    processed_rev = 0
    if not bz_df.empty:
        bz_df.loc[:, "bz_sales"] = pd.to_numeric(bz_df["bz_sales"], errors="coerce").fillna(0)
        bz_df.loc[:, "bz_cost"] = pd.to_numeric(bz_df["bz_cost"], errors="coerce").fillna(0)
        bz_df = bz_df.sort_values("bz_sales", ascending=False)
        
        if len(bz_df) > 6:
            top = bz_df.iloc[:6]
            others = bz_df.iloc[6:]
            others_sales = others["bz_sales"].sum() / 1e8
            others_cost = others["bz_cost"].sum() / 1e8
            
            bz_rows = list(top.iterrows())
            if others_sales > 0:
                bz_rows.append((None, {
                    "bz_item": "其他产品", 
                    "bz_sales": others_sales * 1e8,
                    "bz_cost": others_cost * 1e8
                }))
        else:
            bz_rows = list(bz_df.iterrows())
            
        for _, row in bz_rows:
            p_name = row["bz_item"]
            p_sales = pd.to_numeric(row["bz_sales"], errors="coerce") / 1e8
            p_cost = pd.to_numeric(row["bz_cost"], errors="coerce") / 1e8
            
            if p_sales <= 0: continue
            
            processed_rev += p_sales
            p_idx = get_node_idx(p_name, c_prod)
            
            # Flow 1: Product -> Total Revenue
            links.append({
                "source": p_idx, 
                "target": idx_total_rev, 
                "value": p_sales, 
                "color": "rgba(144, 202, 249, 0.4)"
            })
            
            # Record cost for Level 2 split
            if p_cost > 0:
                product_costs.append((f"成本: {p_name}", p_cost))
            
    # Unallocated Revenue
    if val_rev_total > processed_rev * 1.01:
        diff = val_rev_total - processed_rev
        idx_diff = get_node_idx("其他/未分配收入", c_prod)
        links.append({
            "source": idx_diff, 
            "target": idx_total_rev, 
            "value": diff, 
            "color": "rgba(144, 202, 249, 0.4)"
        })
        # Estimate unallocated cost?
        # Use overall cost ratio
        ratio = val_cost_total / val_rev_total if val_rev_total > 0 else 0.8
        diff_cost = diff * ratio
        if diff_cost > 0:
            product_costs.append(("成本: 其他/未分配", diff_cost))
        
    # --- Level 2: Total Revenue -> Itemized Costs & GP ---
    
    idx_gp = get_node_idx("毛利", c_gp)
    
    # 2a. Split Costs
    # Instead of one "Operating Cost" node, we have multiple
    total_split_cost = 0
    for name, cost_val in product_costs:
        c_idx = get_node_idx(name, c_cost)
        links.append({
            "source": idx_total_rev,
            "target": c_idx,
            "value": cost_val,
            "color": "rgba(235, 87, 87, 0.2)"
        })
        total_split_cost += cost_val
        
    # If there is remaining cost (e.g. from total_oper_cost > sum(product_costs))
    # This happens if mainbz cost sum < total income statement cost
    if val_cost_total > total_split_cost * 1.05:
        rem_cost = val_cost_total - total_split_cost
        idx_rem = get_node_idx("其他营业成本", c_cost)
        links.append({
            "source": idx_total_rev,
            "target": idx_rem,
            "value": rem_cost,
            "color": "rgba(235, 87, 87, 0.2)"
        })
        
    # 2b. Gross Profit
    if val_gp > 0:
        links.append({
            "source": idx_total_rev,
            "target": idx_gp,
            "value": val_gp,
            "color": "rgba(38, 166, 154, 0.4)"
        })
        
    # --- Level 3: GP -> Expenses & Op Profit ---
    
    idx_op = get_node_idx("营业利润", c_gp)
    
    # Expenses
    expenses = [
        ("销售费用", val_sell),
        ("管理费用", val_admin),
        ("研发费用", val_rd),
        ("财务费用", max(0, val_fin)), # Only positive interest exp is flow out
        ("税金及附加", val_tax_surch)
    ]
    
    for name, val in expenses:
        if val > 0:
            e_idx = get_node_idx(name, c_exp)
            links.append({
                "source": idx_gp, # From GP
                "target": e_idx,
                "value": val,
                "color": "rgba(176, 190, 197, 0.3)"
            })
            
    # Flow to Op Profit from GP
    if val_gp_to_op > 0:
        links.append({
            "source": idx_gp,
            "target": idx_op,
            "value": val_gp_to_op,
            "color": "rgba(38, 166, 154, 0.4)" # Teal flow
        })
        
    # Other Income to Op Profit (e.g. Inv Income)
    if val_other_income > 0:
        idx_other = get_node_idx("其他/投资收益", c_other)
        links.append({
            "source": idx_other,
            "target": idx_op,
            "value": val_other_income,
            "color": "rgba(255, 183, 77, 0.5)" # Orange flow
        })
    
    # --- Level 4: Op Profit -> Tax & Net Profit ---
    
    idx_net = get_node_idx("净利润", c_prof)
    
    if val_income_tax > 0:
        idx_tax = get_node_idx("所得税", c_cost)
        links.append({
            "source": idx_op,
            "target": idx_tax,
            "value": val_income_tax,
            "color": "rgba(235, 87, 87, 0.3)"
        })
        
    if val_net_income > 0:
        links.append({
            "source": idx_op,
            "target": idx_net,
            "value": val_net_income,
            "color": "rgba(102, 187, 106, 0.6)"
        })
        
    # Build Plot
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color="white", width=0.5),
            label=[n["label"] for n in nodes],
            color=[n["color"] for n in nodes],
        ),
        link=dict(
            source=[l["source"] for l in links],
            target=[l["target"] for l in links],
            value=[l["value"] for l in links],
            color=[l["color"] for l in links],
        )
    )])
    
    fig.update_layout(
        title=dict(text=f"利润流向桑基图 (单位: 亿元) - {target_date}", font=dict(size=16)),
        font=dict(family="Inter, PingFang SC", size=12),
        height=600, # Taller to accommodate split costs
        margin=dict(l=10, r=10, t=60, b=40),
    )
    return fig

def plot_income_waterfall(df_income: pd.DataFrame, df_cashflow: pd.DataFrame = None):
    """
    Create a Waterfall chart for Income Statement:
    Revenue -> Deductions (Cost, Expenses, Tax) -> Net Profit
    Also shows D&A as annotation if available from cashflow.
    """
    if df_income.empty:
        return None
        
    # Get latest data
    inc = df_income.sort_values("end_date", ascending=False).iloc[0]
    date_str = inc.get("end_date")
    
    # Values (Yi Yuan)
    def val(col):
        v = pd.to_numeric(inc.get(col), errors="coerce")
        return v / 1e8 if pd.notna(v) else 0

    revenue = val("total_revenue")
    if revenue == 0: revenue = val("revenue")
    
    cost = val("oper_cost")
    sell_exp = val("sell_exp")
    admin_exp = val("admin_exp")
    rd_exp = val("rd_exp")
    fin_exp = val("fin_exp")
    tax_surch = val("biz_tax_surchg")
    
    # Other Income / Investment Income (Net)
    # Calculated as: Op Profit - (Rev - Cost - Expenses)
    op_profit = val("operate_profit")
    calc_op = revenue - cost - sell_exp - admin_exp - rd_exp - tax_surch - fin_exp
    other_income = op_profit - calc_op
    
    income_tax = val("income_tax")
    
    # Net Profit (Minority Interest + Parent)
    net_income = val("n_income")
    
    # Waterfall Measures
    measures = ["absolute", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"]
    x_labels = ["营业总收入", "营业成本", "销售费用", "管理费用", "研发费用", "财务费用", "税金及附加", "其他/投资收益", "所得税", "净利润"]
    
    # Waterfall Values (Expenses are negative)
    y_values = [
        revenue, 
        -cost, 
        -sell_exp, 
        -admin_exp, 
        -rd_exp, 
        -fin_exp, 
        -tax_surch, 
        other_income, # Can be pos or neg
        -income_tax, 
        net_income # Should match sum
    ]
    
    # Formatting text
    text_values = [f"{v:+.2f}" for v in y_values]
    text_values[0] = f"{y_values[0]:.2f}"
    text_values[-1] = f"{y_values[-1]:.2f}"
    
    # Plot
    fig = go.Figure(go.Waterfall(
        name="20", orientation="v",
        measure=measures,
        x=x_labels,
        textposition="outside",
        text=text_values,
        y=y_values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": COLORS["danger"]}},
        increasing={"marker": {"color": COLORS["success"]}},
        totals={"marker": {"color": COLORS["primary"]}}
    ))

    # D&A Annotation
    da_text = ""
    if df_cashflow is not None and not df_cashflow.empty:
        # Match date
        cf_rows = df_cashflow[df_cashflow["end_date"] == date_str]
        if not cf_rows.empty:
            cf = cf_rows.iloc[0]
            depr = pd.to_numeric(cf.get("depr_fa_coga_dpba"), errors="coerce") or 0
            amort1 = pd.to_numeric(cf.get("amort_intang_assets"), errors="coerce") or 0
            amort2 = pd.to_numeric(cf.get("lt_amort_deferred_exp"), errors="coerce") or 0
            
            total_da = (depr + amort1 + amort2) / 1e8
            if total_da > 0:
                da_text = f"折旧以摊销 (D&A): {total_da:.2f} 亿 (占净利润 {(total_da/net_income*100):.1f}%)"

    fig.update_layout(
        title=dict(
            text=f"利润表瀑布图 (P&L Waterfall) - {date_str}<br><span style='font-size:12px;color:gray'>{da_text}</span>", 
            font=dict(size=16)
        ),
        showlegend=False,
        height=500,
        margin=dict(l=20, r=20, t=80, b=20),
        yaxis=dict(title="金额 (亿元)", showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    )
    
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


def plot_ocf_ni_divergence(df_earnings_quality: pd.DataFrame):
    """Plot OCF vs Net Income divergence trend with highlighted divergence areas."""
    if df_earnings_quality.empty:
        return None
    
    data = df_earnings_quality.copy()
    if "end_date" in data.columns:
        data["end_date_dt"] = pd.to_datetime(data["end_date"].astype(str), format="%Y%m%d", errors="coerce")
    if "end_date_dt" not in data.columns:
        return None
    
    data = data.sort_values("end_date_dt")
    data["n_income_yi"] = data["n_income"] / 1e8
    data["ocf_yi"] = data["n_cashflow_act"] / 1e8
    
    fig = go.Figure()
    
    # Add area between lines to show divergence
    fig.add_trace(
        go.Scatter(
            x=data["end_date_dt"],
            y=data["n_income_yi"],
            name="Net Income (亿元)",
            line=dict(color=COLORS["primary"], width=2),
            fill=None,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["end_date_dt"],
            y=data["ocf_yi"],
            name="Operating Cash Flow (亿元)",
            line=dict(color=COLORS["accent"], width=2),
            fill="tonexty",
            fillcolor="rgba(217,119,87,0.15)",
        )
    )
    
    # Add warning zone where OCF < NI
    for i, row in data.iterrows():
        if row["ocf_yi"] < row["n_income_yi"] * 0.5:
            fig.add_vline(x=row["end_date_dt"], line_dash="dot", line_color=COLORS["danger"], opacity=0.5)
    
    fig = _apply_style(fig, title="OCF vs Net Income Divergence / 经营现金流与净利润背离")
    fig.update_yaxes(title_text="亿元")
    fig.update_xaxes(title_text="Report Period")
    return fig


def plot_piotroski_score_radar(score_details: dict):
    """Plot Piotroski F-Score breakdown as a radar chart."""
    if not score_details:
        return None
    
    labels = {
        "roa_positive": "ROA>0",
        "ocf_positive": "OCF>0",
        "roa_improving": "ROA↑",
        "ocf_gt_ni": "OCF>NI",
        "leverage_down": "杠杆↓",
        "liquidity_up": "流动性↑",
        "no_dilution": "无摊薄",
        "margin_up": "毛利率↑",
        "turnover_up": "周转率↑",
    }
    
    categories = list(labels.values())
    values = [score_details.get(k, 0) for k in labels.keys()]
    values.append(values[0])  # Close the radar
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(38,166,154,0.3)",
            line=dict(color=COLORS["accent"], width=2),
            name="Score",
        )
    )
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickvals=[0, 0.5, 1]),
        ),
        showlegend=False,
        title="Piotroski F-Score Breakdown / 财务稳健性评分",
        font_family="Inter, PingFang SC",
        height=350,
    )
    return fig


def plot_margin_trend_with_alerts(df_indicator: pd.DataFrame):
    """Plot gross and net profit margin trends with alert annotations."""
    if df_indicator.empty or "end_date_dt" not in df_indicator.columns:
        return None
    
    data = df_indicator.copy().sort_values("end_date_dt")
    
    for col in ["grossprofit_margin", "netprofit_margin"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    
    fig = go.Figure()
    
    if "grossprofit_margin" in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data["end_date_dt"],
                y=data["grossprofit_margin"],
                name="Gross Margin %",
                line=dict(color=COLORS["primary"], width=2),
            )
        )
    
    if "netprofit_margin" in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data["end_date_dt"],
                y=data["netprofit_margin"],
                name="Net Margin %",
                line=dict(color=COLORS["accent"], width=2),
            )
        )
    
    # Add alert annotations for margin compression
    if "grossprofit_margin" in data.columns and len(data) >= 3:
        gm = data["grossprofit_margin"].values
        for i in range(2, len(gm)):
            if pd.notna(gm[i]) and pd.notna(gm[i-1]) and pd.notna(gm[i-2]):
                if gm[i] < gm[i-1] - 2 and gm[i-1] < gm[i-2] - 2:
                    fig.add_annotation(
                        x=data["end_date_dt"].iloc[i],
                        y=gm[i],
                        text="⚠️",
                        showarrow=False,
                        font=dict(size=16),
                    )
    
    fig = _apply_style(fig, title="Profit Margin Trend / 利润率趋势")
    fig.update_yaxes(title_text="%")
    fig.update_xaxes(title_text="Report Period")
    return fig


def plot_peer_percentile_bars(target_ts: str, df_peers: pd.DataFrame, target_name: str = None):
    """Plot horizontal bar chart showing target company's percentile rank among peers."""
    if df_peers.empty or target_ts not in df_peers["ts_code"].values:
        return None
    
    metrics = {
        "roe": ("ROE %", True),
        "netprofit_margin": ("Net Margin %", True),
        "roic": ("ROIC %", True),
        "debt_to_assets": ("Debt Ratio %", False),  # Lower is better
        "assets_turn": ("Asset Turnover", True),
        "current_ratio": ("Current Ratio", True),
    }
    
    target_row = df_peers[df_peers["ts_code"] == target_ts].iloc[0]
    
    results = []
    for col, (label, higher_better) in metrics.items():
        if col not in df_peers.columns:
            continue
        col_data = pd.to_numeric(df_peers[col], errors="coerce").dropna()
        if col_data.empty:
            continue
        
        target_val = pd.to_numeric(target_row.get(col), errors="coerce")
        if pd.isna(target_val):
            continue
        
        if higher_better:
            percentile = (col_data < target_val).sum() / len(col_data) * 100
        else:
            percentile = (col_data > target_val).sum() / len(col_data) * 100
        
        results.append({"metric": label, "percentile": percentile, "value": target_val})
    
    if not results:
        return None
    
    df_plot = pd.DataFrame(results)
    
    # Color bars by performance
    colors = [
        COLORS["accent"] if p >= 75 else COLORS["primary"] if p >= 50 else COLORS["danger"]
        for p in df_plot["percentile"]
    ]
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df_plot["metric"],
            x=df_plot["percentile"],
            orientation="h",
            marker_color=colors,
            text=[f"{p:.0f}%" for p in df_plot["percentile"]],
            textposition="auto",
            hovertemplate="%{y}: %{x:.1f} percentile<extra></extra>",
        )
    )
    
    # Add 50th percentile line
    fig.add_vline(x=50, line_dash="dash", line_color=COLORS["muted"], opacity=0.7)
    
    title = f"Industry Percentile Ranking / 行业排名"
    if target_name:
        title = f"{target_name}: {title}"
    
    fig = _apply_style(fig, title=title)
    fig.update_xaxes(title_text="Percentile", range=[0, 100])
    fig.update_layout(height=300)
    return fig


def plot_growth_quality_scatter(df_indicator: pd.DataFrame):
    """Plot revenue growth vs profit growth scatter to assess growth quality."""
    if df_indicator.empty:
        return None
    
    latest = df_indicator.sort_values("end_date_dt" if "end_date_dt" in df_indicator.columns else "end_date", ascending=False).iloc[0]
    
    tr_yoy = pd.to_numeric(latest.get("tr_yoy"), errors="coerce")
    np_yoy = pd.to_numeric(latest.get("netprofit_yoy"), errors="coerce")
    
    if pd.isna(tr_yoy) or pd.isna(np_yoy):
        return None
    
    fig = go.Figure()
    
    # Reference lines
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["border"])
    fig.add_vline(x=0, line_dash="dash", line_color=COLORS["border"])
    
    # Diagonal (balanced growth)
    fig.add_shape(
        type="line",
        x0=-50, y0=-50, x1=100, y1=100,
        line=dict(color=COLORS["muted"], dash="dot", width=1),
    )
    
    # The point
    color = COLORS["accent"] if np_yoy >= tr_yoy else COLORS["danger"]
    fig.add_trace(
        go.Scatter(
            x=[tr_yoy],
            y=[np_yoy],
            mode="markers+text",
            marker=dict(size=20, color=color),
            text=["Current"],
            textposition="top center",
        )
    )
    
    # Add quadrant labels
    fig.add_annotation(x=30, y=60, text="利润增速>收入", showarrow=False, font=dict(size=10, color=COLORS["accent"]))
    fig.add_annotation(x=60, y=30, text="收入增速>利润", showarrow=False, font=dict(size=10, color=COLORS["danger"]))
    
    fig = _apply_style(fig, title="Growth Quality / 增长质量")
    fig.update_xaxes(title_text="Revenue YoY %", range=[-50, 100])
    fig.update_yaxes(title_text="Net Profit YoY %", range=[-50, 100])
    fig.update_layout(height=350, showlegend=False)
    return fig

