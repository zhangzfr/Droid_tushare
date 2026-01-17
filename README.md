# Tushare 2 DuckDB

A high-performance, modular system for persisting Tushare financial data into DuckDB, designed for quantitative researchers and data engineers.

## 🚀 Key Features

-   **High-Performance Storage**: Leverages DuckDB for lightning-fast analytical queries and efficient data compression.
-   **Modular Architecture**:
    -   `Fetcher`: Robust Tushare API integration with automatic retries and rate limiting.
    -   `Processor`: Clean and transform raw data into optimized formats.
    -   `Storage`: Automated table creation, incremental updates, and deduplication.
-   **Unified Configuration**: Centralized management of API fields, limits, and database paths via `settings.yaml`.
-   **Multi-Database Management**: Smart data grouping into specialized DuckDB files (e.g., `stock.db`, `index.db`, `macro.db`, `ref.db`).
-   **Interactive CLI**: Comprehensive menu-driven interface for manual updates, validation, and exploration.
-   **Advanced Backfilling**: Specialized scripts for handling edge cases like pledge data (weekly snapshops) and filling historical gaps.
-   **Data Integrity & Metadata**: Built-in validation reports and metadata tracking for every table.
-   **Database Explorer**: Built-in interactive tool to query and inspect your local financial databases.

## 🛠 Project Structure

```text
├── src/tushare_duckdb/
│   ├── main.py             # Entry point (Menu-driven CLI)
│   ├── fetcher.py          # API fetching logic
│   ├── storage.py          # DuckDB storage engine
│   ├── schema.py           # Table definitions
│   ├── data_validation.py  # Integrity checking tools
│   ├── db_explorer.py      # Interactive SQL tool
│   └── config.py           # Settings loader
├── scripts/                # Specialized backfill & migration scripts
│   ├── backfill_pledge_stat.py
│   ├── backfill_pledge_detail.py
│   └── fix_daily_gaps.py
├── dashboard/              # Streamlit-based visualization
├── settings.yaml           # Unified configuration
└── requirements.txt        # Dependencies
```

## 📋 Prerequisites

-   Python 3.9+
-   Tushare Pro Token (Register at [tushare.pro](https://tushare.pro/))
-   DuckDB

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Droid_tushare
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your Tushare token:
   Edit `src/tushare_duckdb/config.py` or set an environment variable `TUSHARE_TOKEN`.

## 📖 Usage

### Main Interface
Launch the interactive menu to manage all data categories:
```bash
python -m src.tushare_duckdb.main
```

### Backfilling Pledge Data
Stock pledge data requires specific iterative fetching:
```bash
# Backfill statistical data
python scripts/backfill_pledge_stat.py

# Backfill detail data (Smart mode)
python scripts/backfill_pledge_detail.py --smart
```

> 推荐使用脚本更新 `pledge_detail`：该接口无日期过滤，使用主 CLI 会对每只股票全量拉取，易耗时和触发限频；脚本已按 `pledge_stat` 中的 ts_code 分批拉取并支持智能/强制模式。

### Data Validation
Check for gaps or inconsistencies in your local database:
- Use the main menu (Option 14) or dedicated scripts in `scripts/`.

## 🤝 Contribution
Excluding `utils/`, `extension/`, and `quant-ml-qlib/` which are for internal or extended research purposes.
