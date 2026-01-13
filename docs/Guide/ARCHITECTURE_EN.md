# 🏗️ Droid-Tushare System Architecture

This document provides a deep dive into the system architecture, module responsibilities, data flow, and technology stack of the Droid-Tushare project.

---

## 📋 Table of Contents

- [1. System Overview](#1-system-overview)
- [2. Architecture Diagram](#2-architecture-diagram)
- [3. Core Modules](#3-core-modules)
- [4. Data Flow](#4-data-flow)
- [5. Technology Stack](#5-technology-stack)
- [6. Design Principles](#6-design-principles)

---

## 1. System Overview

### 1.1 Project Positioning

Droid-Tushare is an **industrial-grade financial data localization and quantitative analysis platform**. It addresses:

- **API Constraints**: Rate limiting, network latency, and data instability of Tushare API.
- **Data Management**: Lack of persistent storage, difficulty in incremental updates, and historical data gaps.
- **Analysis Efficiency**: Inconsistent formats and slow calculation processing.

### 1.2 Core Capabilities

| Dimension | Feature | Implementation |
|:---|:---|:---|
| **Data Sync** | 50+ tables, smart incremental updates, pagination handling | Tushare API + Paging Algorithm + Retry Logic |
| **Storage** | Analytical queries, columnar storage, atomic operations | DuckDB + Multi-DB Architecture |
| **Quality** | Auto-validation, anomaly detection, coverage analysis | Metadata Tracking + Validation Engine |
| **Backfilling** | Specialized iterative fetching for complex datasets | Custom scripts for Pledge & Daily gaps |

---

## 2. Architecture Diagram

The system follows a layered architecture:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          User Interface Layer                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  CLI Terminal│  │  Dashboard   │  │  Python API  │  │   Scripts    │ │
│  │  (main.py)   │  │  (app.py)    │  │  (processor) │  │  (backfill)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Business Logic Layer                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┐  ┌────────────────────────────────────┐  │
│  │  Data Sync Engine            │  │  Analysis & Visualization          │  │
│  │  (tushare_duckdb)            │  │  (dashboard/vix)                   │  │
│  │  ├─ TushareFetcher           │  │  ├─ Chart Creators                 │  │
│  │  ├─ DataProcessor            │  │  ├─ VIX Calculator                 │  │
│  │  ├─ DuckDBStorage            │  │  └─ Data Loaders                   │  │
│  │  └─ DataValidator            │  │                                    │  │
│  └──────────────────────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Data Storage Layer (DuckDB)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  Stock DB  │ │  Index DB  │ │  Fund DB   │ │  Macro DB  │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Modules

### 3.1 Data Sync Engine (`src/tushare_duckdb/`)

- **`TushareFetcher`**: Handles all API communications, including automatic pagination (offset/limit), retries with exponential backoff, and 60s cooldowns on rate limits.
- **`DataProcessor`**: Orchestrates the sync process using three modes: `single` (daily), `range` (date blocks), and `full_paging` (incremental snapshot).
- **`DuckDBStorage`**: Performs the heavy lifting of storage. It manages schema creation, field mapping, and atomic `INSERT ... ON CONFLICT` (implemented via `NOT EXISTS` in DuckDB).
- **`DataValidator`**: Monitors data health by checking coverage ratios and detecting anomalies in record counts.

### 3.2 Backfill Scripts (`scripts/`)

- **`backfill_pledge_stat.py`**: A specialized script for stock pledge statistics. It queries the local DB for the earliest weekly Friday and fetches historical data iteratively.
- **`backfill_pledge_detail.py`**: Fetches granular pledge details. Supports `--smart` mode (only updates stocks with changed pledge counts) and `--force` mode.

---

## 4. Technology Stack

- **DuckDB**: Fast OLAP database engine. Chosen for its columnar storage, vectorized execution, and zero-config deployment.
- **Tushare Pro**: Comprehensive source for Chinese financial market data.
- **Streamlit**: Framework for rapid delivery of interactive data dashboards.
- **Plotly**: Library for sophisticated financial charts and heatmaps.

---

## 5. Design Principles

- **Configuration Driven**: Table structures, API parameters, and storage paths are all defined in `settings.yaml`.
- **Atomic Operations**: Storage operations are designed to be idempotent and atomic to prevent database corruption.
- **Data Freshness**: Every record tracks its `last_updated` time and sync metadata.
