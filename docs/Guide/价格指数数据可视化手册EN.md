# Handbook for Visualizing Price Index Data

This handbook is designed to provide a comprehensive guide on how to visualize price index data, such as Consumer Price Index (CPI), Producer Price Index (PPI), and related metrics like GDP deflators. It is based on a detailed analysis of the visualizations provided in the document "212255228854541.pdf" and the accompanying images. The analysis covers the structure, content, design elements, and purpose of each visualization, drawing lessons to create effective, insightful charts for economic data.

The handbook is structured as follows:
- **Section 1: Introduction**
- **Section 2: Key Visualization Types and Examples**
- **Section 3: Best Practices**
- **Section 4: Tools and Implementation Tips**
- **Section 5: Common Pitfalls and Solutions**

Price index data typically involves time-series metrics (e.g., year-on-year or month-on-month changes), sub-categories (e.g., food vs. non-food), and comparisons (e.g., vs. commodities or money supply). Visualizations help reveal trends, seasonality, contributions, and anomalies. The examples analyzed here focus on Chinese economic data from 1997 to 2025, including CPI, PPI, and related indices, sourced from tools like Wind and MacroMargin.

## Section 1: Introduction

Price index visualization aims to make complex economic data accessible, highlighting inflation/deflation trends, sectoral breakdowns, and correlations. Effective visualizations should:
- Use time as the x-axis for trends.
- Employ colors to differentiate categories (e.g., positive/negative values with green/red).
- Include legends, labels, and sources for clarity.
- Balance detail with simplicity to avoid overwhelming the viewer.

From the document's tables (pages 9-10) and images, key themes include:
- Long-term cycles (e.g., multi-year trends).
- Breakdowns (e.g., CPI sub-items like food, services).
- Comparisons (e.g., CPI vs. PPI, core vs. overall).
- Seasonality and recent performance.

The document's tables provide raw data (e.g., monthly CPI/PPI values from 2024-2025), while the images visualize them dynamically.

## Section 2: Key Visualization Types and Examples

Based on the 10 provided images, I've categorized them into types. Each example includes:
- **Description**: Structure and content.
- **Purpose**: What insights it provides.
- **How to Create**: Step-by-step guidance.
- **Variations**: Adaptations for similar data.

### 2.1 Line Charts for Long-Term Trends
Line charts are ideal for showing continuous changes over time, such as inflation rates.

**Example from Image 1: "中国通胀长期周期观察" (China Inflation Long-Term Cycle Observation)**
- **Structure**: Multi-line chart with 4 lines (GDP deflator year-on-year in cyan, CPI in blue, PPI in yellow, GDP deflator quarter-on-quarter in red). X-axis: Years from 1997 to 2025. Y-axis: Percentage change (-9% to 15%). Shaded vertical bands highlight economic cycles (e.g., "7Q", "20Q", "10Q" for quarters or periods). Right y-axis for secondary scale (230Q-?). Source label at bottom (Wind, MacroMargin).
- **Content**: Shows historical inflation fluctuations, with peaks (e.g., 2008 crisis) and recent declines (2020s deflationary pressures). Lines overlap to compare indices.
- **Purpose**: Illustrates cyclical patterns and correlations between CPI, PPI, and GDP deflators over decades.
- **How to Create**:
  1. Gather time-series data (e.g., monthly/quarterly percentages).
  2. Plot x-axis as time (years/months); y-axis as % change.
  3. Use distinct colors for each line; add legend at top.
  4. Add shaded regions for events (e.g., recessions) using area fills.
  5. Include dual y-axes if scales differ.
- **Variations**: Smooth lines for noisy data; add markers for key events.

**Example from Image 5: CPI vs. Commodities (e.g., Gold Prices)**
- **Structure**: Dual-line chart (CPI in red, COMEX gold monthly in blue). X-axis: Dates from 2016-08 to 2025-12. Y-axis left: Gold price (500-4500); right: CPI % (-6% to 1.5%). Annotation for "CPI: Common Month-on-Month".
- **Content**: Contrasts CPI stability with commodity volatility, showing inverse correlations in some periods.
- **Purpose**: Highlights external influences on inflation.
- **How to Create**: Similar to above, but normalize scales or use dual axes for different units.

**Example from Image 6: PPI vs. M1 (Money Supply) Month-on-Month**
- **Structure**: Two lines (PPI in blue, M1 in red). X-axis: Dates from 2005/12 to 2025/12. Y-axis: % change (-10% to 16%).
- **Content**: Shows PPI leading M1 in cycles, with peaks around 2008 and 2022.
- **Purpose**: Demonstrates monetary policy impacts on producer prices.
- **How to Create**: Focus on synchronized x-axis; use thick lines for emphasis.

**Example from Image 7: CPI Food vs. Pork Prices**
- **Structure**: Two lines (CPI food in blue, pork prices in red). X-axis: Dates from 2016-03 to 2025-03. Y-axis: % change (-60% to 140%).
- **Content**: Pork as a driver of food CPI volatility in China.
- **Purpose**: Identifies key sub-drivers (e.g., supply shocks).
- **How to Create**: Emphasize one line (e.g., thicker for primary index).

### 2.2 Stacked Bar Charts for Category Contributions
These show how sub-components contribute to the total index.

**Example from Image 2: "CPI 同比:八大分项贡献" (CPI Year-on-Year: Eight Major Category Contributions)**
- **Structure**: Top: Stacked bar chart with 5 colored bars per month (e.g., black for food/tobacco, blue for clothing). Red line overlays total CPI. X-axis: Dates from 2020-10 to 2025-10. Y-axis: % ( -1.5% to 3%). Bottom: Line chart for cumulative contributions (lines for food, non-food, etc.).
- **Content**: Breaks down CPI into categories like food, clothing, housing; shows food's negative pull in 2025.
- **Purpose**: Reveals drivers of overall inflation (e.g., food volatility).
- **How to Create**:
  1. Calculate contributions (e.g., weighted % change).
  2. Stack bars by category; add total line.
  3. Use color legend; label x-axis densely for recent data.
  4. Add sub-chart for cumulative trends.
- **Variations**: Use 100% stacked for proportions.

**Example from Image 3 (Bottom Part): "CPI 主要分项贡献率" (CPI Main Sub-Item Contributions)**
- **Structure**: Multi-line chart (5 lines: food/tobacco in green, clothing in blue, etc.). X-axis: Dates from 2021-05 to 2025-12. Y-axis: % (-5% to 17%).
- **Content**: Cumulative lines showing rising contributions from services.
- **Purpose**: Tracks long-term shifts in inflation sources.
- **How to Create**: Plot as cumulative lines; use arrows for trends.

### 2.3 Line Charts for Comparisons and Seasonality
For side-by-side metrics or seasonal patterns.

**Example from Image 3 (Top): "CPI vs. 核心CPI, 食品 vs. 非食品" (CPI vs. Core CPI, Food vs. Non-Food)**
- **Structure**: Top: Four lines (CPI in blue/red, core in cyan/pink). X-axis: Dates from 2021-05 to 2025-12. Y-axis: % (-8% to 5%). Bottom: Similar for sub-divisions.
- **Content**: Core CPI steadier than overall; food drags down totals.
- **Purpose**: Distinguishes volatile vs. stable components.
- **How to Create**: Group related lines; use dashed for secondary.

**Example from Image 4: "CPI 环比季节" (CPI Month-on-Month Seasonality) and "核心CPI 环比季节"**
- **Structure**: Two sub-charts, each with 3 lines (recent years in red/blue/green). X-axis: Months (1-12). Y-axis: % (-1.5% to 1.5%). Shaded background for emphasis.
- **Content**: Shows seasonal peaks (e.g., January highs due to holidays).
- **Purpose**: Identifies predictable patterns for forecasting.
- **How to Create**:
  1. Segment data by year.
  2. Plot lines per year; label endpoints.
  3. Use neutral background; add annotations for averages.

### 2.4 Heatmaps for Sub-Item Analysis
Color-coded tables for multi-dimensional data.

**Example from Image 8: CPI Sub-Items Heatmap**
- **Structure**: Table with rows for sub-items (e.g., CPI overall, food), columns for months (2024-12 to 2025-12). Cells colored red (positive), green (negative), intensity by magnitude. Left column: Recent change arrow.
- **Content**: Monthly % changes; e.g., food negative in mid-2025.
- **Purpose**: Quick scan of trends across categories.
- **How to Create**:
  1. Use spreadsheet/table; apply conditional formatting (red>0, green<0).
  2. Add sparkline column for mini-trends.
  3. Sort rows by importance.

**Example from Image 9: China CPI Sub-Divisions Heatmap**
- **Structure**: Similar table, more rows (e.g., rural, services). Columns: Months from 2024-11 to 2025-12.
- **Content**: Detailed breakdowns; e.g., services positive.
- **Purpose**: Granular analysis.
- **How to Create**: Expand rows; ensure color scale consistency.

**Example from Image 10: PPI Sub-Items Heatmap**
- **Structure**: Rows for PPI sub-sectors (e.g., coal mining), columns for months. Colors as above.
- **Content**: Upstream sectors like metals volatile.
- **Purpose**: Industry-specific insights.
- **How to Create**: Similar to above; group by upstream/midstream.

## Section 3: Best Practices

- **Color Usage**: Red/green for positive/negative; consistent palettes (e.g., blue for CPI, yellow for PPI).
- **Labels and Legends**: Clear titles (e.g., "CPI vs. Core CPI"); date formats like YYYY-MM.
- **Scales**: Use % for rates; dual axes sparingly.
- **Interactivity**: If digital, add tooltips for values.
- **Sources**: Always include (e.g., Wind, MacroMargin).
- **Accessibility**: High contrast; alt text for images.
- **Data Preparation**: Clean data from tables like document pages 9-10; handle #N/A as gaps.

## Section 4: Tools and Implementation Tips

### Recommended Tool Stack

- **Data Acquisition**: Tushare Pro API → Local DuckDB Storage
- **Data Processing**: Python pandas/numpy → Data cleaning and preprocessing
- **Visualization Framework**: Streamlit + Plotly → Interactive web applications
- **Chart Library**: Plotly Express/Graph Objects → Professional financial charts
- **Styling Framework**: Custom CSS + Anthropic design language → Modern interfaces

### Droid-Tushare Integration Solution

Based on the project's dashboard module best practices:

```python
# 1. Data Loading (dashboard/data_loader.py)
@st.cache_data(ttl=3600)
def load_pmi_data():
    conn = duckdb.connect('data/tushare_duck_macro.db')
    df = conn.execute("SELECT * FROM cn_pmi").fetchdf()
    conn.close()
    return df

# 2. Chart Generation (dashboard/charts.py)
def plot_pmi_trend(df):
    fig = px.line(df, x='month', y=['pmi', 'pmi_production'],
                  title='PMI Trend Analysis')
    fig.update_layout(template='plotly_white')
    return fig

# 3. Page Rendering (dashboard/pages/macro_page.py)
def render_macro_page():
    df = load_pmi_data()
    fig = plot_pmi_trend(df)
    st.plotly_chart(fig, use_container_width=True)
```

### Project Implementation Steps

1. **Data Preparation**:
   - Use `src/tushare_duckdb` to sync macroeconomic data to DuckDB
   - Verify data completeness and quality

2. **Visualization Design**:
   - Select appropriate chart types based on this guide
   - Use existing components from the dashboard module
   - Follow the project's design standards

3. **Interaction Optimization**:
   - Add date range selectors
   - Implement data filtering functionality
   - Ensure responsive layout

4. **Deployment and Publishing**:
   - Use Streamlit Cloud or self-hosting
   - Configure appropriate caching strategies
   - Monitor performance and user experience

## Section 5: Common Pitfalls and Solutions

- **Pitfall**: Overcrowded charts. **Solution**: Limit lines to 4-5; use sub-charts.
- **Pitfall**: Misleading scales. **Solution**: Start y-axis at 0 for % changes.
- **Pitfall**: Ignoring context. **Solution**: Add annotations for events (e.g., COVID impacts).
- **Pitfall**: Static data. **Solution**: Update with recent dates (e.g., up to 2025-12 as in examples).

