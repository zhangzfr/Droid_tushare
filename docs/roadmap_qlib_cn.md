# 🗺️ 路线图：从数据存储到量化分析（Qlib 集成）

本文档概述了从当前的 `Droid-Tushare` 本地数据库到由 [Microsoft Qlib](https://github.com/microsoft/qlib) 驱动的成熟量化研究环境的战略路径。

## 1. 🔍 代码库审查与当前状态

### 系统健康状况
*   **核心架构**：强大。`fetcher` -> `processor` -> `storage` 流水线已解耦且稳健。
*   **存储**：DuckDB 在面向列的金融数据处理方面表现良好。
*   **数据覆盖**：广泛覆盖股票、指数、基金、期权和宏观数据（已将 "Marco" 重构为 "Macro"）。
*   **可靠性**：内置重试机制、速率限制和数据验证（覆盖率报告）已成熟。

### 近期改进 (2026 年 1 月)
*   **宏观数据**：新增 `cn_m`（货币供应量）、`sf_month`（社会融资）、`cn_pmi`、`us_tycr`。
*   **VIX 模块**：新增使用本地期权数据的独立 VIX 计算模块 (`src/vix`)。
*   **配置**：在 `settings.yaml` 中统一了 `date_param_mode`，以简化获取逻辑。
*   **仪表板**：Streamlit 仪表板提供对数据资产的可见性。

### 技术债务 / 清理
*   ✅ **已修复**：配置中的 "Marco" 拼写错误已更正为 "Macro"，并重构了代码。
*   **待处理**：确保所有 `settings.yaml` 字段与 Qlib 要求一一对应（特别是 `vwap` 或调整项）。

---

## 2. 🎯 愿景

目标是构建一个个人量化研究平台，其中：
1.  **数据源**：Tushare（同步至本地 DuckDB）。
2.  **数据管理**：通过 DuckDB 实现高性能本地查询。
3.  **回测与 AI**：使用 **Qlib** 进行 AI 驱动的因子挖掘和策略回测。
4.  **集成**：使用或适配 `chenditc/investment_data` 中的工具，将 Tushare 数据转换为 Qlib 的二进制格式。

---

## 3. 🛣️ 实施路径

### 阶段 1：数据准备与标准化
*目标：确保本地数据符合 Qlib 的要求。*

*   **要求**：Qlib 需要复权价格（Pre-close 或 Adj Close）进行回测，以避免分红/拆股带来的干扰。
*   **行动事项**：
    *   验证 `stock_daily` 和 `adj_factor` 表是否已完全同步。
    *   动态计算 **复权价格**（OHLC）或存储视图。
        *   公式：$P_{adj} = P_{raw} \times \frac{AdjFactor_{curr}}{AdjFactor_{base}}$
*   确保 `stk_limit`（涨跌停限制）和 `suspend_d`（停牌）可用于筛选可交易标的。

### 第二阶段：构建适配器 (DuckDB -> CSV)
*目标：以 Qlib 可导入的格式导出数据。*

Qlib 的默认导入工具 (`dump_bin`) 通常读取 CSV 文件，其中：
*   **文件组织**：每只股票一个 CSV 文件（例如 `SH600000.csv`）或者一个大型 CSV 文件。
*   **列**：`date, open, high, low, close, volume, factor, vwap`（可选但推荐）。

**建议脚本**：`utils/export_for_qlib.py`
1.  **遍历** `stock_basic` 中的所有股票。
2.  **查询** `daily` 并连接 `adj_factor`。
3.  将日期**格式化**为 `YYYY-MM-DD`。
4.  **导出**到临时目录 `temp/qlib_source/`。

### 阶段 3：使用 `investment_data` / 自定义数据摄取
*目标：将 CSV 转换为 Qlib 二进制文件。*

我们可以参考 `chenditc/investment_data` 的逻辑：
*   它可能对 CSV 格式进行了标准化。
*   它使用 `qlib.dump_bin` 来创建提供者数据库。

**分步指南**：
1.  安装 Qlib：`pip install pyqlib`。
2.  运行转换：
    ```bash
    python -m qlib.run.dump_bin dump_all \
            --csv_path temp/qlib_source \
            --qlib_dir /Users/robert/.qlib/qlib_data/cn_data \
            --include_fields open,close,high,low,volume,factor
    ```
3.  **验证**：使用 `Qlib` 数据提供器加载数据框，并与 DuckDB 原始数据进行比较。

### 阶段 4：因子扩展与研究
*目标：开发自定义因子。*

*   **基础因子**：使用 Qlib 的 alpha101 或 alpha158 库。
*   **自定义因子**：
    *   使用 DuckDB 计算复杂的基于 SQL 的因子（例如：资金流向相对强弱），并导出为新列。
    *   或者在 Qlib 表达式中实现公式 Alpha（例如：`Mean(Close, 5) / Close`）。

---

## 4. 📝 紧接着的步骤

1.  **试点运行**：选择一个小范围（例如 SSE 50）来测试流程。
2.  **创建导出器**：编写 `src/tools/qlib_exporter.py`，将 `daily` + `adj_factor` 导出为 `csv`。
3.  **测试 Qlib 数据摄取**：尝试从这些 CSV 文件生成 Qlib 二进制文件。

## 5. 指南更新
*   **README**：已更新以反映对 Macro 的支持。
*   **指南**：本路线图作为下一个开发周期的总体规划。
