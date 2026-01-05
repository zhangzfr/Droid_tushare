# 🗺️ Roadmap: From Data Storage to Quantitative Analysis (Qlib Integration)

This document outlines the strategic path from the current `Droid-Tushare` local database to a full-fledged Quantitative Research Environment powered by [Microsoft Qlib](https://github.com/microsoft/qlib).

## 1. 🔍 Codebase Review & Current Status

### System Health
*   **Core Architecture**: Strong. The `fetcher` -> `processor` -> `storage` pipeline is decoupled and robust.
*   **Storage**: DuckDB is performing well for column-oriented financial data.
*   **Data Coverage**: Extensive coverage of Stocks, Indexes, Funds, Options, and Macro data (Refactored "Marco" -> "Macro").
*   **Reliability**: built-in retry mechanisms, rate limiting, and data validation (coverage reports) are mature.

### Recent Improvements (Jan 2026)
*   **Macro Data**: Added `cn_m` (Money Supply), `sf_month` (Social Financing), `cn_pmi`, `us_tycr`.
*   **VIX Module**: Added independent VIX calculation module (`src/vix`) using local option data.
*   **Configuration**: Unified `date_param_mode` in `settings.yaml` to simplify fetching logic.
*   **Dashboard**: Streamlit dashboard provides visibility into data holdings.

### Technical Debt / Cleanup
*   ✅ **Fixed**: "Marco" typo in configuration and code refactored to "Macro".
*   **Pending**: Ensure all `settings.yaml` fields map 1:1 to Qlib requirements (specifically `vwap` or adjustments).

---

## 2. 🎯 Vision

The goal is to build a personal quantitative research platform where:
1.  **Data Source**: Tushare (synced to local DuckDB).
2.  **Data Management**: High-performance local querying via DuckDB.
3.  **Backtesting & AI**: **Qlib** for AI-driven factor mining and strategy backtesting.
4.  **Integration**: Use or adapt tools from `chenditc/investment_data` to bridge Tushare data to Qlib's binary format.

---

## 3. 🛣️ Implementation Path

### Phase 1: Data Preparation & Standardization
*Objective: Ensure local data is Qlib-ready.*

*   **Requirements**: Qlib requires Adjusted Prices (Pre-close or Adj Close) for backtesting to avoid dividend/split artifacts.
*   **Action Items**:
    *   Verify `stock_daily` and `adj_factor` tables are fully synced.
    *   Compute **Post-Adjusted Prices** (OHLC) dynamically or store a view.
        *   Formula: $P_{adj} = P_{raw} \times \frac{AdjFactor_{curr}}{AdjFactor_{base}}$
    *   Ensure `stk_limit` (Up/Down limits) and `suspend_d` (Suspensions) are available for filtering tradable universe.

### Phase 2: Building the Adapter (DuckDB -> CSV)
*Objective: Export data in Qlib-ingestible format.*

Qlib's default ingestion tool (`dump_bin`) typically reads CSV files where:
*   **File Organization**: One CSV per stock (e.g., `SH600000.csv`) OR a single large CSV.
*   **Columns**: `date, open, high, low, close, volume, factor, vwap` (optional but recommended).

**Proposed Script**: `utils/export_for_qlib.py`
1.  **Iterate** all stocks in `stock_basic`.
2.  **Query** `daily` join `adj_factor`.
3.  **Format** dates to `YYYY-MM-DD`.
4.  **Export** to a temporary directory `temp/qlib_source/`.

### Phase 3: Utilizing `investment_data` / Custom Ingestion
*Objective: Convert CSV to Qlib Binaries.*

We can reference `chenditc/investment_data` logic:
*   It likely standardizes the CSV format.
*   It uses `qlib.dump_bin` to create the provider database.

**Step-by-Step**:
1.  Install Qlib: `pip install pyqlib`.
2.  Run conversion:
    ```bash
    python -m qlib.run.dump_bin dump_all \
        --csv_path temp/qlib_source \
        --qlib_dir /Users/robert/.qlib/qlib_data/cn_data \
        --include_fields open,close,high,low,volume,factor
    ```
3.  **Validation**: Use `Qlib` data provider to load a dataframe and compare with DuckDB original.

### Phase 4: Factor Extension & Research
*Objective: Develop custom factors.*

*   **Base Factors**: Use Qlib's alpha101 or alpha158 libraries.
*   **Custom Factors**:
    *   Use DuckDB to compute complex SQL-based factors (e.g., Money Flow relative strength) and export as new columns.
    *   Or implement Formula Alpha in Qlib expressions (e.g., `Mean(Close, 5) / Close`).

---

## 4. 📝 Immediate Next Steps

1.  **Pilot Run**: Select a small universe (e.g., SSE 50) to test the pipeline.
2.  **Create Exporter**: Write `src/tools/qlib_exporter.py` to dump `daily` + `adj_factor` to `csv`.
3.  **Test Qlib Ingestion**: Attempt to generate Qlib binaries from these CSVs.

## 5. Guides Update
*   **README**: Updated to reflect Macro support.
*   **Guides**: This Roadmap serves as the master plan for the next development cycle.
