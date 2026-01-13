# 🚀 Droid-Tushare Deployment & Performance Guide

This document outlines the strategies for production deployment, operations management, and performance optimization for the Droid-Tushare project.

---

## 📋 Table of Contents

- [1. Deployment Architecture](#1-deployment-architecture)
- [2. Environment Preparation](#2-environment-preparation)
- [3. Automation & Scheduling](#3-automation--scheduling)
- [4. Performance Optimization](#4-performance-optimization)

---

## 1. Deployment Architecture

### 1.1 Recommended Setup

```text
┌─────────────────────────────────────────────────────────────┐
│                    Application Server                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Dashboard   │  │  Cron Jobs   │  │  Backfill    │  │
│  │  (Streamlit) │  │  (Daily)     │  │  Scripts     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  DuckDB Files │  │    Backups   │  │     Logs     │  │
│  │  (Analytics)  │  │  (snapshots) │  │  (Logging)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Environment Preparation

### 2.1 OS Requirements

- **Recommended**: Ubuntu 20.04+, CentOS 7+, macOS (for Dev).
- **Python**: 3.9 or higher.

### 2.2 Variables Configuration

Create a `.env` file or export variables:

```bash
# Tushare API Token
TUSHARE_TOKEN=your_token_here

# Database Root Directory
DB_ROOT=/absolute/path/to/databases

# Log Level
LOG_LEVEL=INFO
```

---

## 3. Operations & Scripts

### 3.1 Initial Setup

1. Install requirements: `pip install -r requirements.txt`
2. Initialize databases: Run `python -m src.tushare_duckdb.main` and choose a category to sync.

### 3.2 Backfilling Data

For datasets with complex historical requirements (like stock pledges):

```bash
# Step 1: Sync statistical snapshot
python scripts/backfill_pledge_stat.py

# Step 2: Sync exhaustive details (recommended using --smart)
python scripts/backfill_pledge_detail.py --smart
```

### 3.3 Fixing Gaps

If you identify missing days in `daily` price data:

```bash
python scripts/fix_daily_gaps.py
```

---

## 4. Performance Optimization

### 4.1 DuckDB Best Practices

- **Persistent Connections**: Reuse connections in scripts to avoid the overhead of reopening files.
- **Batch Insertion**: Use the `batch` logic in backfill scripts (e.g., merging 50 stocks before one commit) to drastically reduce I/O wait times.
- **Memory Management**: DuckDB automatically manages memory, but ensure at least 4GB RAM is available for large analytical aggregations.

### 4.2 API Rate Limiting

- The system includes a global rate limit detector that pauses for 60 seconds when a 403/Limit error is received.
- For high-frequency scripts like `pledge_detail`, a proactive counter is implemented to sleep every 350 calls.
