# %% [markdown]
# # 沪深港通资金流向深度分析 (Plotly交互版)
# ## Stock Connect Money Flow Analysis (Interactive Plotly Version)
# 
# 本脚本从两个视角分析沪深港通资金流向数据:
# 1. **A股投资者视角** - 关注市场情绪、投资机会、风险预警
# 2. **量化投资者视角** - 关注统计因子、模型构建、回测信号
# 
# ⚡ **以924行情(2024-09-24)为分界点进行分段分析**

# %% [markdown]
# ## 第一部分: 环境配置与数据加载

# %%
# =============================================================================
# 导入必要的库
# =============================================================================
import duckdb                    # 用于连接DuckDB数据库
import pandas as pd              # 数据处理核心库
import numpy as np               # 数值计算库
import plotly.express as px      # Plotly快速绑图
import plotly.graph_objects as go  # Plotly图形对象
from plotly.subplots import make_subplots  # 子图支持
from scipy import stats          # 统计分析库
import warnings
warnings.filterwarnings('ignore')

print("✅ 库导入成功！Libraries imported successfully!")
print("📊 使用Plotly进行交互式可视化")

# %%
# =============================================================================
# 连接DuckDB数据库并加载数据
# =============================================================================

DB_PATH = '/Users/robert/Developer/DuckDB/tushare_duck_moneyflow.db'
conn = duckdb.connect(DB_PATH, read_only=True)
query = "SELECT * FROM moneyflow_hsgt"
df = conn.execute(query).fetchdf()
conn.close()

print(f"✅ 数据加载成功！共 {len(df)} 行数据")
print("\n📊 数据基本信息:")
df.info()

# %%
# =============================================================================
# 数据预处理
# =============================================================================

df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
df = df.sort_values('trade_date').reset_index(drop=True)
df_filled = df.fillna(0)

print("✅ 数据预处理完成！")
print(f"\n📅 数据时间范围: {df['trade_date'].min()} 至 {df['trade_date'].max()}")
display(df.head())

# %%
# =============================================================================
# ⚡ 关键分界点: 924行情 (2024-09-24)
# =============================================================================

BREAKPOINT_DATE = pd.Timestamp('2024-09-24')

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              ⚡ 关键分界点: 924行情 (2024-09-24)                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  2024年9月24日，央行、金融监管总局、证监会联合发布重磅利好政策!               ║
║  此后北向资金流入规模发生结构性变化，数据分析需以此为分界点!                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

df_before_924 = df[df['trade_date'] < BREAKPOINT_DATE].copy()
df_after_924 = df[df['trade_date'] >= BREAKPOINT_DATE].copy()

print(f"📊 数据分段: 924之前 {len(df_before_924)} 天, 924之后 {len(df_after_924)} 天")

# %% [markdown]
# ---
# # 第二部分: A股投资者视角分析 (Plotly交互图)

# %%
# =============================================================================
# 2.1 时间趋势维度 - 资金流向长期趋势 (4个子图)
# =============================================================================

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        '北向资金累计净流入 (North-bound)',
        '南向资金累计净流入 (South-bound)',
        '沪股通 vs 深股通',
        '南北向资金对比'
    ),
    vertical_spacing=0.12,
    horizontal_spacing=0.08
)

# 北向资金
fig.add_trace(
    go.Scatter(x=df['trade_date'], y=df['north_money'], 
               fill='tozeroy', fillcolor='rgba(231, 76, 60, 0.3)',
               line=dict(color='#E74C3C', width=1.5),
               name='北向资金(外资流入A股)',
               hovertemplate='日期: %{x}<br>累计: %{y:.0f}亿<extra></extra>'),
    row=1, col=1
)

# 南向资金
fig.add_trace(
    go.Scatter(x=df['trade_date'], y=df['south_money'],
               fill='tozeroy', fillcolor='rgba(52, 152, 219, 0.3)',
               line=dict(color='#3498DB', width=1.5),
               name='南向资金(内资流入港股)',
               hovertemplate='日期: %{x}<br>累计: %{y:.0f}亿<extra></extra>'),
    row=1, col=2
)

# 沪股通 vs 深股通
fig.add_trace(
    go.Scatter(x=df['trade_date'], y=df['hgt'],
               line=dict(color='#9B59B6', width=1.5),
               name='沪股通(HGT)',
               hovertemplate='日期: %{x}<br>沪股通: %{y:.0f}亿<extra></extra>'),
    row=2, col=1
)
fig.add_trace(
    go.Scatter(x=df['trade_date'], y=df['sgt'],
               line=dict(color='#1ABC9C', width=1.5),
               name='深股通(SGT)',
               hovertemplate='日期: %{x}<br>深股通: %{y:.0f}亿<extra></extra>'),
    row=2, col=1
)

# 南北向对比
fig.add_trace(
    go.Scatter(x=df['trade_date'], y=df['north_money'],
               line=dict(color='#E74C3C', width=1.5),
               name='北向(外资)',
               hovertemplate='北向: %{y:.0f}亿<extra></extra>'),
    row=2, col=2
)
fig.add_trace(
    go.Scatter(x=df['trade_date'], y=df['south_money'],
               line=dict(color='#3498DB', width=1.5),
               name='南向(内资)',
               hovertemplate='南向: %{y:.0f}亿<extra></extra>'),
    row=2, col=2
)

# 添加924分界线
for row in [1, 2]:
    for col in [1, 2]:
        fig.add_vline(x=BREAKPOINT_DATE, line_dash="dash", line_color="red", 
                      line_width=1, row=row, col=col)

fig.update_layout(
    title_text='沪深港通资金流向长期趋势 (Stock Connect Cumulative Money Flow)',
    title_font_size=16,
    height=700,
    showlegend=True,
    template='plotly_white',
    hovermode='x unified'
)
fig.show()

# %%
# =============================================================================
# 2.2 计算每日净流入
# =============================================================================

df['north_daily'] = df['north_money'].diff()
df['south_daily'] = df['south_money'].diff()
df['hgt_daily'] = df['hgt'].diff()
df['sgt_daily'] = df['sgt'].diff()

print("✅ 每日净流入计算完成！")
display(df[['north_daily', 'south_daily', 'hgt_daily', 'sgt_daily']].describe())

# %%
# =============================================================================
# 2.3 流入/流出极端值分析
# =============================================================================

north_top10_inflow = df.nlargest(10, 'north_daily')[['trade_date', 'north_daily']]
north_top10_outflow = df.nsmallest(10, 'north_daily')[['trade_date', 'north_daily']]

print("🚀 北向资金单日净流入TOP 10:")
display(north_top10_inflow)
print("\n⚠️ 北向资金单日净流出TOP 10:")
display(north_top10_outflow)

# 分布直方图
fig = make_subplots(rows=1, cols=2, subplot_titles=('北向资金每日净流入分布', '南向资金每日净流入分布'))

p5 = df['north_daily'].quantile(0.05)
p95 = df['north_daily'].quantile(0.95)

fig.add_trace(
    go.Histogram(x=df['north_daily'].dropna(), nbinsx=50, 
                 marker_color='#E74C3C', opacity=0.7,
                 name='北向资金',
                 hovertemplate='区间: %{x}<br>频次: %{y}<extra></extra>'),
    row=1, col=1
)
fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2, row=1, col=1)
fig.add_vline(x=p5, line_dash="dash", line_color="blue", annotation_text=f"5%: {p5:.0f}", row=1, col=1)
fig.add_vline(x=p95, line_dash="dash", line_color="green", annotation_text=f"95%: {p95:.0f}", row=1, col=1)

fig.add_trace(
    go.Histogram(x=df['south_daily'].dropna(), nbinsx=50,
                 marker_color='#3498DB', opacity=0.7,
                 name='南向资金'),
    row=1, col=2
)
fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2, row=1, col=2)

fig.update_layout(height=400, template='plotly_white', showlegend=False,
                  title_text='每日净流入分布直方图')
fig.show()

# %%
# =============================================================================
# 2.4 季节/周期维度分析
# =============================================================================

df['year'] = df['trade_date'].dt.year
df['month'] = df['trade_date'].dt.month
df['quarter'] = df['trade_date'].dt.quarter
df['weekday'] = df['trade_date'].dt.dayofweek

monthly_avg = df.groupby('month')[['north_daily', 'south_daily']].mean().reset_index()
weekday_avg = df.groupby('weekday')[['north_daily', 'south_daily']].mean().reset_index()

fig = make_subplots(rows=1, cols=2, subplot_titles=('各月份平均每日净流入', '星期几平均每日净流入'))

months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
weekdays = ['周一', '周二', '周三', '周四', '周五']

# 月度
fig.add_trace(go.Bar(x=months, y=monthly_avg['north_daily'], name='北向资金',
                     marker_color='#E74C3C', opacity=0.8), row=1, col=1)
fig.add_trace(go.Bar(x=months, y=monthly_avg['south_daily'], name='南向资金',
                     marker_color='#3498DB', opacity=0.8), row=1, col=1)

# 星期
fig.add_trace(go.Bar(x=weekdays, y=weekday_avg['north_daily'], name='北向资金',
                     marker_color='#E74C3C', opacity=0.8, showlegend=False), row=1, col=2)
fig.add_trace(go.Bar(x=weekdays, y=weekday_avg['south_daily'], name='南向资金',
                     marker_color='#3498DB', opacity=0.8, showlegend=False), row=1, col=2)

fig.add_hline(y=0, line_color="black", line_width=0.5, row=1, col=1)
fig.add_hline(y=0, line_color="black", line_width=0.5, row=1, col=2)

fig.update_layout(height=400, template='plotly_white', barmode='group',
                  title_text='季节性效应分析')
fig.show()

# %%
# =============================================================================
# 2.5 南北向资金比率分析
# =============================================================================

df['ns_ratio'] = df['north_money'] / df['south_money'].replace(0, np.nan)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['trade_date'], y=df['ns_ratio'],
    line=dict(color='#8E44AD', width=1),
    name='北向/南向比率',
    hovertemplate='日期: %{x}<br>比率: %{y:.2f}<extra></extra>'
))
fig.add_hline(y=1, line_dash="dash", line_color="black", annotation_text="比率=1")
fig.add_vline(x=BREAKPOINT_DATE, line_dash="dash", line_color="red", annotation_text="924分界点")

fig.update_layout(
    title='北向资金/南向资金 比率变化',
    xaxis_title='日期',
    yaxis_title='比率 (>1表示北向更强)',
    height=400,
    template='plotly_white'
)
fig.show()

print(f"📊 北向/南向比率: 最新 {df['ns_ratio'].iloc[-1]:.2f}, 均值 {df['ns_ratio'].mean():.2f}")

# %% [markdown]
# ---
# # 第三部分: 量化投资者视角分析

# %%
# =============================================================================
# 3.1 统计描述维度
# =============================================================================

quant_stats = pd.DataFrame({
    '均值': df[['north_daily', 'south_daily']].mean(),
    '标准差': df[['north_daily', 'south_daily']].std(),
    '偏度': df[['north_daily', 'south_daily']].skew(),
    '峰度': df[['north_daily', 'south_daily']].kurtosis(),
    '最小值': df[['north_daily', 'south_daily']].min(),
    '中位数': df[['north_daily', 'south_daily']].median(),
    '最大值': df[['north_daily', 'south_daily']].max(),
})
print("📊 量化统计指标:")
display(quant_stats.T.round(2))

# %%
# =============================================================================
# 3.2 移动平均分析
# =============================================================================

df['north_ma5'] = df['north_daily'].rolling(window=5).mean()
df['north_ma20'] = df['north_daily'].rolling(window=20).mean()
df['north_ma60'] = df['north_daily'].rolling(window=60).mean()

recent_df = df[df['trade_date'] >= '2025-01-01'].copy()

fig = go.Figure()
fig.add_trace(go.Bar(x=recent_df['trade_date'], y=recent_df['north_daily'],
                     marker_color='gray', opacity=0.3, name='每日净流入'))
fig.add_trace(go.Scatter(x=recent_df['trade_date'], y=recent_df['north_ma5'],
                         line=dict(color='#3498DB', width=1.5), name='5日均线'))
fig.add_trace(go.Scatter(x=recent_df['trade_date'], y=recent_df['north_ma20'],
                         line=dict(color='#E74C3C', width=2), name='20日均线'))
fig.add_trace(go.Scatter(x=recent_df['trade_date'], y=recent_df['north_ma60'],
                         line=dict(color='#2ECC71', width=2), name='60日均线'))
fig.add_hline(y=0, line_color="black", line_width=0.5)

fig.update_layout(
    title='北向资金每日净流入与移动平均 (2025年至今)',
    xaxis_title='日期',
    yaxis_title='净流入 (亿元)',
    height=500,
    template='plotly_white',
    hovermode='x unified'
)
fig.show()

# %%
# =============================================================================
# 3.3 因子构造
# =============================================================================

df['north_zscore'] = (df['north_daily'] - df['north_daily'].mean()) / df['north_daily'].std()
df['north_momentum_5d'] = df['north_daily'].rolling(5).sum()
df['north_momentum_20d'] = df['north_daily'].rolling(20).sum()
df['north_volatility_20d'] = df['north_daily'].rolling(20).std()

print("✅ 因子构造完成:")
display(df[['north_zscore', 'north_momentum_5d', 'north_momentum_20d', 'north_volatility_20d']].describe())

# %%
# =============================================================================
# 3.4 极端值阈值与交易信号
# =============================================================================

p10 = df['north_daily'].quantile(0.10)
p90 = df['north_daily'].quantile(0.90)

df['signal'] = 0
df.loc[df['north_daily'] >= p90, 'signal'] = 1
df.loc[df['north_daily'] <= p10, 'signal'] = -1

buy_signals = df[df['signal'] == 1]
sell_signals = df[df['signal'] == -1]

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['trade_date'], y=df['north_daily'],
                         line=dict(color='gray', width=0.5), opacity=0.5, name='每日净流入'))
fig.add_trace(go.Scatter(x=buy_signals['trade_date'], y=buy_signals['north_daily'],
                         mode='markers', marker=dict(color='green', size=6),
                         name=f'买入信号 (>{p90:.0f}亿)'))
fig.add_trace(go.Scatter(x=sell_signals['trade_date'], y=sell_signals['north_daily'],
                         mode='markers', marker=dict(color='red', size=6),
                         name=f'卖出信号 (<{p10:.0f}亿)'))
fig.add_hline(y=p90, line_dash="dash", line_color="green", opacity=0.5)
fig.add_hline(y=p10, line_dash="dash", line_color="red", opacity=0.5)
fig.add_hline(y=0, line_color="black", line_width=0.5)

fig.update_layout(
    title='基于北向资金的交易信号',
    height=500,
    template='plotly_white'
)
fig.show()

print(f"📊 信号统计: 买入{len(buy_signals)}次, 卖出{len(sell_signals)}次")

# %%
# =============================================================================
# 3.5 多渠道协方差分析 - 热力图
# =============================================================================

daily_cols = ['hgt_daily', 'sgt_daily', 'north_daily', 'south_daily']
corr_matrix = df[daily_cols].corr()
labels = ['沪股通', '深股通', '北向资金', '南向资金']

fig = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=labels,
    y=labels,
    colorscale='RdYlBu_r',
    zmin=-1, zmax=1,
    text=np.round(corr_matrix.values, 2),
    texttemplate='%{text}',
    textfont={"size": 14},
    hovertemplate='%{x} vs %{y}<br>相关系数: %{z:.2f}<extra></extra>'
))

fig.update_layout(
    title='资金流渠道相关性热力图',
    height=450,
    template='plotly_white'
)
fig.show()

# %%
# =============================================================================
# 3.6 累计流向与反转监控
# =============================================================================

windows = [5, 10, 20, 60]
for w in windows:
    df[f'north_cum_{w}d'] = df['north_daily'].rolling(w).sum()

recent = df[df['trade_date'] >= '2024-01-01']

fig = go.Figure()
fig.add_trace(go.Scatter(x=recent['trade_date'], y=recent['north_cum_5d'],
                         line=dict(width=1), name='5日累计'))
fig.add_trace(go.Scatter(x=recent['trade_date'], y=recent['north_cum_20d'],
                         line=dict(width=1.5), name='20日累计',
                         fill='tozeroy', fillcolor='rgba(0,128,0,0.1)'))
fig.add_trace(go.Scatter(x=recent['trade_date'], y=recent['north_cum_60d'],
                         line=dict(width=2), name='60日累计'))
fig.add_hline(y=0, line_color="black", line_width=0.5)
fig.add_vline(x=BREAKPOINT_DATE, line_dash="dash", line_color="red", annotation_text="924")

fig.update_layout(
    title='北向资金累计净流入 (不同期限)',
    xaxis_title='日期',
    yaxis_title='累计净流入 (亿元)',
    height=500,
    template='plotly_white',
    hovermode='x unified'
)
fig.show()

latest_5d = df['north_cum_5d'].iloc[-1]
latest_20d = df['north_cum_20d'].iloc[-1]
print(f"📈 最近5日累计: {latest_5d:.0f}亿, 最近20日累计: {latest_20d:.0f}亿")

# %% [markdown]
# ---
# # 第四部分: 分段对比分析 (924前后)

# %%
# =============================================================================
# 4.1 924前后统计对比
# =============================================================================

df_before_924['north_daily'] = df_before_924['north_money'].diff()
df_before_924['south_daily'] = df_before_924['south_money'].diff()
df_after_924['north_daily'] = df_after_924['north_money'].diff()
df_after_924['south_daily'] = df_after_924['south_money'].diff()

before_stats = df_before_924['north_daily'].dropna().agg(['mean', 'std', 'min', 'max', 'median'])
after_stats = df_after_924['north_daily'].dropna().agg(['mean', 'std', 'min', 'max', 'median'])

comparison_df = pd.DataFrame({
    '924之前': before_stats,
    '924之后': after_stats,
    '变化倍数': after_stats / before_stats.replace(0, np.nan)
})
comparison_df.index = ['均值(亿)', '标准差(亿)', '最小值(亿)', '最大值(亿)', '中位数(亿)']

print("📊 924前后北向资金统计对比:")
display(comparison_df.round(2))

# %%
# =============================================================================
# 4.2 分段可视化对比 (Plotly版)
# =============================================================================

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        '北向资金每日净流入分布对比 (箱线图)',
        '北向资金每日流入分布对比 (直方图)',
        '北向资金累计净流入 (标注924分界点)',
        '月度效应对比'
    ),
    vertical_spacing=0.12
)

# 1. 箱线图
fig.add_trace(go.Box(y=df_before_924['north_daily'].dropna(), name='924之前',
                     marker_color='#3498DB', boxmean=True), row=1, col=1)
fig.add_trace(go.Box(y=df_after_924['north_daily'].dropna(), name='924之后',
                     marker_color='#E74C3C', boxmean=True), row=1, col=1)

# 2. 直方图叠加
fig.add_trace(go.Histogram(x=df_before_924['north_daily'].dropna(), name='924之前',
                           marker_color='#3498DB', opacity=0.5, histnorm='probability density',
                           nbinsx=50), row=1, col=2)
fig.add_trace(go.Histogram(x=df_after_924['north_daily'].dropna(), name='924之后',
                           marker_color='#E74C3C', opacity=0.5, histnorm='probability density',
                           nbinsx=30), row=1, col=2)

# 3. 累计走势 + 分界点
fig.add_trace(go.Scatter(x=df['trade_date'], y=df['north_money'],
                         line=dict(color='#2C3E50', width=1), name='累计净流入',
                         showlegend=False), row=2, col=1)
fig.add_vline(x=BREAKPOINT_DATE, line_dash="dash", line_color="red", line_width=2,
              annotation_text="924分界点", row=2, col=1)

# 4. 月度效应对比
df_before_924['month'] = df_before_924['trade_date'].dt.month
df_after_924['month'] = df_after_924['trade_date'].dt.month
before_monthly = df_before_924.groupby('month')['north_daily'].mean()
after_monthly = df_after_924.groupby('month')['north_daily'].mean()

months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
fig.add_trace(go.Bar(x=months, y=before_monthly.reindex(range(1,13)).fillna(0),
                     name='924之前', marker_color='#3498DB', opacity=0.8, showlegend=False), row=2, col=2)
fig.add_trace(go.Bar(x=months, y=after_monthly.reindex(range(1,13)).fillna(0),
                     name='924之后', marker_color='#E74C3C', opacity=0.8, showlegend=False), row=2, col=2)

fig.update_layout(
    title_text='924行情前后资金流对比',
    height=800,
    template='plotly_white',
    barmode='group'
)
fig.show()

# %%
# =============================================================================
# 4.3 924前后量化指标对比
# =============================================================================

def calc_quant_metrics(data, col='north_daily'):
    daily = data[col].dropna()
    return {
        '均值': daily.mean(),
        '标准差': daily.std(),
        '偏度': daily.skew(),
        '峰度': daily.kurtosis(),
        '日胜率(%)': (daily > 0).mean() * 100,
        '90%阈值': daily.quantile(0.90),
        '10%阈值': daily.quantile(0.10),
    }

before_metrics = calc_quant_metrics(df_before_924)
after_metrics = calc_quant_metrics(df_after_924)

quant_comparison = pd.DataFrame({'924之前': before_metrics, '924之后': after_metrics})
print("📊 量化指标分段对比:")
display(quant_comparison.round(2))

# %% [markdown]
# ---
# # 第五部分: 综合总结

# %%
print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  沪深港通资金流向分析总结 (Plotly交互版)                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
""")

print("【A股投资者视角关键发现】")
print(f"  1. 累计净流入: {df['north_money'].iloc[-1]:.0f} 亿元")
print(f"  2. 最近5日: {'净流入' if latest_5d > 0 else '净流出'} {abs(latest_5d):.0f} 亿元")
print(f"  3. 最大单日: 流入 {df['north_daily'].max():.0f}亿, 流出 {df['north_daily'].min():.0f}亿")

print("\n【⚡924行情分段对比】")
print(f"  1. 日均流入: {before_stats['mean']:.0f}亿 → {after_stats['mean']:.0f}亿")
print(f"  2. 波动率: {before_stats['std']:.0f}亿 → {after_stats['std']:.0f}亿 (+{(after_stats['std']/before_stats['std']-1)*100:.0f}%)")

print("""
╚══════════════════════════════════════════════════════════════════════════════╝
✅ 分析完成！所有图表均支持交互操作（缩放、悬停、筛选）
""")
