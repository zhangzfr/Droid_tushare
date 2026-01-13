# 🛠️ Droid-Tushare Scripts Guide

The `scripts/` directory contains specialized tools for data backfilling, historical remediation, and database maintenance. These scripts augment the core synchronization engine (`main.py`) by handling complex edge cases and heavy historical tasks.

---

## 📋 Directory Overview

| Script Name | Purpose | Key Logic |
| :---------- | :------ | :-------- |
| `backfill_pledge_stat.py` | Pledge Stats Backfill | Fetches data for every Friday based on the trade calendar. |
| `backfill_pledge_detail.py` | Pledge Details Backfill | Iterates through TS codes; supports Smart and Force modes. |
| `fix_daily_gaps.py` | Repair Daily Gaps | Scans the database for missing trading days and refills them. |
| `migrate_basic_to_stock.py` | Table Migration | Safely migrates tables between different DuckDB files. |
| `validate_stocks.py` | Stock Validation | Compares local records with Tushare for integrity audits. |

---

## 🔍 Detailed Script Breakdown

### 1. Pledge Statistics Backfill (`backfill_pledge_stat.py`)

**Context**: This API provides weekly snapshots. The core engine is inefficient for this as it fetches day-by-day, leading to massive duplicates.

**Features**:

- Automated retrieval of all historical Fridays via `trade_cal`.
- Compares with local DB to fetch only missing weeks.
- **Batching**: Merges 20 individual Fridays into a single batch write to optimize I/O.

**Usage**:

```bash
python scripts/backfill_pledge_stat.py
```

---

### 2. Pledge Details Backfill (`backfill_pledge_detail.py`)

**Context**: The `pledge_detail` interface requires a `ts_code` parameter and has no date filter; it returns the entire history for that stock.

**Execution Modes**:

- **Default**: Fetches only for new stocks not present in the local database.
- **Smart (`--smart`)**: Compares record counts between Stat and Detail tables; updates only stocks with new pledge activity.
- **Force (`--force`)**: Deletes existing local data for selected stocks and performs a full refresh.

**Rate Limiting**:

- Proactively throttles requests to stay within Tushare's 400 calls/minute limit. It pauses for 60 seconds every 350 requests.

**Usage**:

```bash
# Intelligent update based on change detection
python scripts/backfill_pledge_detail.py --smart
```

---

### 3. Repair Daily Gaps (`fix_daily_gaps.py`)

**Features**:

- Automatically identifies non-contiguous sequences in the `daily` table.
- Orchestrates targeted API calls to fill specific historical voids.

---

## ⚙️ General Patterns & Design

These scripts follow standardized design principles:

1. **Atomic Connections**: DB connections are opened globally for the script and safely closed on exit.
2. **Batching Strategy**: Avoids "chatty" DB writes by merging multiple stocks/days into a single transaction.
3. **Metadata Updates**: Automatically triggers `update_table_metadata` upon completion to refresh min/max date ranges.
4. **Comprehensive Logging**: Fully integrated with the project's logger to output detailed execution statistics.

---

## ⚠️ Safety & Best Practices

- **Backups**: Always backup your `.db` files before running migration or `--force` scripts.
- **Locking**: Scripts hold an exclusive write lock on the DuckDB file; Dashboards or queries may experience latency during execution.
- **API Quotas**: Backfill operations can consume significant Tushare points. Ensure your account balance is sufficient.
