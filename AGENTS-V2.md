# AGENTS-V2.md – 增强版智能体工作指南

> **版本**: v2.0.0  
> **最后更新**: 2026-01-15  
> **项目**: Droid-Tushare  
> **核心定位**: 工业级金融数据本地化同步与量化分析平台

---

## 目录

1. [项目总览](#1-项目总览)
2. [系统架构](#2-系统架构)
3. [核心模块详解](#3-核心模块详解)
4. [数据类别体系](#4-数据类别体系)
5. [配置驱动机制](#5-配置驱动机制)
6. [开发规范](#6-开发规范)
7. [API 交互规范](#7-api-交互规范)
8. [数据库架构](#8-数据库架构)
9. [可视化模块](#9-可视化模块)
10. [量化分析模块](#10-量化分析模块)
11. [运维与调试](#11-运维与调试)
12. [故障排查手册](#12-故障排查手册)
13. [扩展开发指南](#13-扩展开发指南)
14. [智能体任务清单](#14-智能体任务清单)

---

## 1. 项目总览

### 1.1 项目定位

Droid-Tushare 是一个**工业级的金融数据本地化同步与量化分析平台**，专为量化研究者、数据工程师和金融科技开发者设计。系统解决以下核心问题：

| 痛点领域 | 问题描述 | 解决方案 |
|---------|---------|---------|
| **数据获取** | Tushare API 频率限制、网络延迟、数据质量不稳定 | 智能分页、自动重试、增量同步 |
| **数据管理** | 缺乏本地化数据仓库、历史数据追溯困难 | DuckDB 列式存储、元数据追踪 |
| **量化分析** | 数据格式不统一、计算效率低 | CBOE VIX 方法论、回测框架 |
| **运维监控** | 数据更新状态不透明、故障难以定位 | 完整日志系统、覆盖率分析 |

### 1.2 系统规模

- **代码量**: ~10,000 行 Python 代码
- **数据表**: 50+ 张金融数据表
- **数据类别**: 14 个主要类别
- **数据库文件**: 14 个独立的 DuckDB 文件
- **支持的 ETF 期权**: 9 个标的
- **支持的指数期权**: 3 个标的

### 1.3 核心能力矩阵

| 能力维度 | 核心功能 | 技术实现 |
|---------|---------|---------|
| **数据同步** | 50+ 表自动同步、智能增量更新、分页处理 | Tushare API + 分页算法 + 重试机制 |
| **数据存储** | 高性能查询、列式存储、原子操作 | DuckDB + 多数据库架构 |
| **数据质量** | 自动校验、异常检测、覆盖率分析 | 统计学算法 + 元数据追踪 |
| **量化分析** | VIX 计算、回测框架、策略分析 | CBOE 方法论 + Backtrader |
| **数据可视化** | 交互式仪表盘、热力图、趋势分析 | Streamlit + Plotly |
| **运维监控** | 日志追踪、性能监控、故障恢复 | 日志系统 + 元数据管理 |

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          用户交互层 (User Interface)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  CLI Terminal│  │  Dashboard   │  │  Python API  │  │   专项脚本    │   │
│  │  (main.py)   │  │  (app.py)    │  │  (processor) │  │  (backfill)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          业务逻辑层 (Business Logic)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┐  ┌────────────────────────────────────┐   │
│  │  数据同步引擎                 │  │  量化分析与可视化                  │   │
│  │  (tushare_duckdb)            │  │  (dashboard/vix)                   │   │
│  │  ├─ TushareFetcher           │  │  ├─ 图表生成引擎                   │   │
│  │  ├─ DataProcessor            │  │  ├─ VIX 计算引擎                   │   │
│  │  ├─ DuckDBStorage            │  │  └─ 数据加载器                     │   │
│  │  ├─ DataValidator            │  │                                    │   │
│  │  └─ 专项补全 (backfill)       │  │                                    │   │
│  └──────────────────────────────┘  └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          数据访问层 (Data Access)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┐  ┌────────────────────────────────────┐   │
│  │  DuckDB 连接管理              │  │  外部 API 管理                     │   │
│  │  ├─ 连接池                   │  │  ├─ Tushare Pro API              │   │
│  │  ├─ 事务管理                 │  │  ├─ 限流控制                      │   │
│  │  └─ 错误处理                 │  │  └─ 重试机制                      │   │
│  └──────────────────────────────┘  └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          数据存储层 (Data Storage)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  Stock DB  │ │  Index DB  │ │  Fund DB   │ │  Option DB │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Future DB  │ │  Bond DB   │ │ Macro DB   │ │  Margin DB │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流转全景

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Tushare API  │ ──▶ │TushareFetcher│ ──▶ │DataProcessor │ ──▶ │DuckDBStorage │
│ (Data Source)│     │ (fetcher.py) │     │ (processor.py)│     │ (storage.py) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                      │
       ┌───────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DuckDB DB   │ ──▶ │DataValidator │ ──▶ │  Dashboard   │
│  (14个文件)  │     │ (validation) │     │  / VIX Module│
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 3. 核心模块详解

### 3.1 数据同步引擎 (`src/tushare_duckdb/`)

| 组件 | 文件 | 职责 | 代码行数 |
|------|------|------|---------|
| **API 客户端** | `fetcher.py` | 与 Tushare API 通信、分页、重试、限流 | ~60 |
| **数据处理** | `processor.py` | 协调数据获取、处理和存储流程 | ~400 |
| **数据存储** | `storage.py` | DuckDB 存储操作、字段映射、日期标准化 | ~240 |
| **数据校验** | `data_validation.py` | 数据质量检查、覆盖率分析、异常检测 | ~300 |
| **元数据管理** | `metadata.py` | 表结构信息、统计信息、更新追踪 | ~150 |
| **配置管理** | `config.py` | 加载 settings.yaml、环境变量 | ~80 |
| **日志系统** | `logger.py` | 统一的日志记录 | ~50 |
| **工具函数** | `utils.py` | 日期处理、连接管理、通用函数 | ~200 |

### 3.2 TushareFetcher 核心逻辑

```python
class TushareFetcher:
    def fetch_data(self, table_name, api_params, api_config_entry, 
                   retries=3, initial_offset=0):
        """
        从 Tushare API 获取数据，支持分页和自动重试
        
        处理流程:
        1. 构建 API 调用参数 (limit/offset)
        2. 发起 API 请求，捕获异常
        3. 检测频率限制 ("每_minute最多访问") → 等待 65s
        4. 网络错误 → 指数退避重试
        5. 数据去重 (基于 unique_keys)
        6. 返回合并的 DataFrame
        """
```

**关键机制**:

- **分页处理**: 自动根据 `limit` 和 `offset` 遍历数据
- **限流检测**: 识别 "每_minute最多访问" 错误，触发 65 秒等待
- **指数退避**: 网络错误时按 2^n 秒重试
- **去重处理**: 基于配置的唯一键 (`unique_keys`) 自动去重

### 3.3 DataProcessor 三种处理模式

| 模式 | `date_param_mode` | 适用场景 | API 调用次数 |
|------|-------------------|---------|-------------|
| **逐日处理** | `single` | 日频数据 (daily, adj_factor) | N 次 (N = 天数) |
| **范围处理** | `range` | 支持日期范围查询 (shibor, index_weight) | 1 次 |
| **智能分页** | `full_paging` | 基础信息表 (opt_basic, stock_basic) | 动态 |

**full_paging 智能增量同步原理**:

```
1. 查询本地数据库，获取最大日期（或最大 ID）
2. 从该日期之后开始分页拉取数据
3. 使用 offset 逐步遍历，直到无数据返回
4. 全量数据通过分页递归获取
5. 去重后存储（基于唯一键）
```

### 3.4 DuckDBStorage 核心方法

```python
class DuckDBStorage:
    def store_data(self, table_name, df, unique_keys,
                   date_column='trade_date',
                   storage_mode='insert_new',
                   overwrite_start_date=None,
                   overwrite_end_date=None,
                   ts_code=None,
                   api_config_entry=None):
        """
        存储数据到 DuckDB
        
        处理流程:
        1. 字段映射 (API 字段 → DB 字段)
        2. 日期标准化 (YYYY-MM-DD → YYYYMMDD)
        3. 金融数据预处理 (ann_date/end_date 填充)
        4. NULL 日期过滤
        5. 创建临时视图
        6. 执行 DELETE (如果是 replace 模式)
        7. 执行 INSERT (带 NOT EXISTS 检查)
        8. 更新元数据
        """
```

**存储模式**:

| 模式 | `storage_mode` | 行为 | 适用场景 |
|------|---------------|------|---------|
| **增量插入** | `insert_new` | 检查唯一键，不存在则插入 | 日常增量更新 |
| **覆盖模式** | `replace` | 删除指定范围数据，重新插入 | 修复历史数据 |

---

## 4. 数据类别体系

系统支持 **14 个数据类别**，每个类别对应独立的 DuckDB 数据库文件：

| 类别 | 数据库文件 | 表数量 | 主要用途 |
|------|-----------|-------|---------|
| **stock** | `tushare_duck_stock.db` | 10+ | 股票基础数据、日线、财务数据 |
| **index** | `tushare_duck_index.db` | 15+ | 指数行情、成分股、行业指数 |
| **fund** | `tushare_duck_fund.db` | 10+ | 基金信息、净值、持仓 |
| **option** | `tushare_duck_opt.db` | 2 | 期权合约、日线行情 |
| **future** | `tushare_duck_future.db` | 4 | 期货合约、仓单、日线 |
| **bond** | `tushare_duck_bond.db` | 10+ | 可转债、债券行情、回购 |
| **macro** | `tushare_duck_macro.db` | 15+ | 宏观经济指标 (PMI、社融、M2) |
| **margin** | `tushare_duck_margin.db` | 7 | 融资融券、证券借贷 |
| **moneyflow** | `tushare_duck_moneyflow.db` | 8 | 资金流向、龙虎榜 |
| **reference** | `tushare_duck_ref.db` | 3 | 大宗交易、股权质押 |
| **fx** | `tushare_duck_fx.db` | 2 | 外汇基础、日线行情 |
| **commodity** | `tushare_duck_commodity.db` | 2 | 上海黄金交易所数据 |
| **stock_events** | `tushare_duck_stock.db` | 5 | 股票事件 (高管变更、ST 等) |
| **index_member** | `tushare_duck_index_weight.db` | 1 | 指数成分股权重 |

---

## 5. 配置驱动机制

### 5.1 settings.yaml 核心结构

```yaml
# 数据类别定义
category_name:
  db_path: ${DB_ROOT}/tushare_duck_xxx.db  # 数据库路径
  list_exchange: SSE                         # 交易所筛选
  tables:
    table_name:                              # 表名
      fields:                                # API 返回字段
      - field1
      - field2
      unique_keys:                           # 唯一键（去重用）
      - ts_code
      - trade_date
      earliest_date: '19900101'              # 最早日期
      latest_date: null                      # 最晚日期 (null=至今)
      date_column: trade_date                # 数据库日期列
      date_type: trade                       # trade/natural
      date_param_mode: single                # single/range/full_paging
      requires_paging: true                  # 是否需要分页
      limit: 6000                            # API 分页大小
      api_date_format: 'YYYYMMDD'            # API 日期格式
      field_mappings:                        # 字段映射
        api_field: db_field
```

### 5.2 核心配置参数详解

| 参数 | 必填 | 说明 |
|------|------|------|
| `date_param_mode` | 是 | `single`(逐日)/`range`(范围)/`full_paging`(智能分页) |
| `requires_date` | 是 | 是否需要日期参数 |
| `date_column` | 是 | 数据库中的日期列名 |
| `date_type` | 是 | `trade`(交易日) 或 `natural`(自然日) |
| `unique_keys` | 是 | 复合唯一键列表，用于去重 |
| `fields` | 是 | API 返回的字段列表 |
| `limit` | 否 | API 分页大小，默认 2000 |

### 5.3 废弃参数（禁止使用）

以下参数已废弃，请勿在配置中添加：

- `is_daily` → 使用 `date_param_mode='single'`
- `force_daily` → 使用 `date_param_mode='single'`
- `fetch_by_date_range` → 使用 `date_param_mode='range'`
- `param_name` → 使用 `date_param`
- `display_as_daily` → 已废弃

---

## 6. 开发规范

### 6.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| **类名** | CamelCase | `TushareFetcher`, `DuckDBStorage` |
| **函数/方法** | snake_case | `fetch_data`, `store_data` |
| **变量** | snake_case | `date_list`, `api_params` |
| **常量** | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_LIMIT` |
| **私有方法** | `_snake_case` | `_process_daily()` |

### 6.2 代码风格

- **缩进**: 4 空格（禁止 Tab）
- **行长度**: ~100 字符
- **类型提示**: 必须使用（Google Style）
- **文档字符串**: Google Style + 中文说明

### 6.3 文档字符串模板

```python
def fetch_data(self, table_name: str, api_params: dict, 
               api_config_entry: dict, retries: int = 3) -> pd.DataFrame:
    """
    从 Tushare API 获取数据（支持分页和自动重试）

    Args:
        table_name: API 接口名称
        api_params: API 调用参数
        api_config_entry: 表的配置信息
        retries: 重试次数，默认 3

    Returns:
        去重后的 DataFrame，失败返回空 DataFrame

    Raises:
        APIRateLimitError: 达到 API 频率限制
        NetworkError: 网络连接失败
    """
```

### 6.4 日志使用规范

```python
from .logger import logger

# 信息日志
logger.info(f"开始获取 '{table_name}': 分页={requires_paging}")

# 警告日志
logger.warning(f"检测到频率限制，等待 65 秒后重试...")

# 错误日志
logger.error(f"'{table_name}' 获取失败: {e}")

# 结构化日志（带额外字段）
logger.info(
    f"{table_name}: 处理参数组合 {grid_params}",
    extra={
        'table': table_name,
        'params': grid_params,
        'action': 'process'
    }
)
```

---

## 7. API 交互规范

### 7.1 Tushare API 限制

| 限制类型 | 阈值 | 处理策略 |
|---------|------|---------|
| **调用频率** | 400 次/分钟 | 检测 "每_minute最多访问" 错误，等待 65 秒 |
| **单页行数** | 2000-15000 行 | 根据 `limit` 配置自动分页 |
| **Token** | 必需 | 必须设置 `TUSHARE_TOKEN` 环境变量 |

### 7.2 重试机制

```python
for attempt in range(retries):
    try:
        df_page = self.api.query(table_name, fields=fields, **params)
        # 成功处理
        break
    except Exception as e:
        if "每_minute最多访问" in str(e):
            logger.warning(f"检测到频率限制，等待 65 秒后重试...")
            time.sleep(65)
        elif attempt < retries - 1:
            # 指数退避: 1s, 2s, 4s, 8s...
            time.sleep(1.0 * (2 ** attempt))
        else:
            logger.error(f"获取失败: {e}")
            return pd.DataFrame()
```

### 7.3 分页处理流程

```
开始
  │
  ▼
构建分页参数 (limit/offset)
  │
  ▼
循环直到返回数据 < limit
  │
  ├── 返回数据 = 0 ──▶ 结束
  │
  └── 返回数据 > 0 ──▶ 合并到结果集 ──▶ offset += page_rows
                              │
                              ▼
                          返回合并后的 DataFrame
```

---

## 8. 数据库架构

### 8.1 多数据库设计

系统采用 **14 个独立的 DuckDB 文件**，按数据类别划分：

```
${DB_ROOT}/
├── tushare_duck_stock.db      # 股票数据
├── tushare_duck_index.db      # 指数数据
├── tushare_duck_fund.db       # 基金数据
├── tushare_duck_opt.db        # 期权数据
├── tushare_duck_future.db     # 期货数据
├── tushare_duck_bond.db       # 债券数据
├── tushare_duck_macro.db      # 宏观经济数据
├── tushare_duck_margin.db     # 融资融券数据
├── tushare_duck_moneyflow.db  # 资金流向数据
├── tushare_duck_ref.db        # 参考数据
├── tushare_duck_fx.db         # 外汇数据
├── tushare_duck_commodity.db  # 商品数据
└── tushare_duck_index_weight.db # 指数权重数据
```

### 8.2 元数据表

每个数据表都有一个对应的 `_metadata` 表：

| 字段 | 说明 |
|------|------|
| `table_name` | 表名 |
| `min_date` | 最早日期 |
| `max_date` | 最新日期 |
| `row_count` | 记录数 |
| `last_update` | 最后更新时间 |

### 8.3 DuckDB 连接管理

```python
from .utils import get_connection

# 使用上下文管理器（推荐）
with get_connection(db_path) as conn:
    result = conn.execute("SELECT * FROM table").fetchdf()

# 禁止：共享连接或跨线程使用
# DuckDB 连接不是线程安全的
```

---

## 9. 可视化模块

### 9.1 Dashboard 架构 (`dashboard/`)

| 组件 | 文件 | 职责 |
|------|------|------|
| **主应用** | `app.py` | 统一入口、导航、页面路由 |
| **数据加载器** | `*_data_loader.py` | 从 DuckDB 加载数据（带缓存） |
| **图表生成** | `*_charts.py` | 生成 Plotly 图表 |

### 9.2 页面结构

```
app.py (统一入口)
    ├─ 导航系统 (URL-based routing)
    │   └─ Query params: ?page=macro&sub=pmi
    ├─ 首页 (数据概览)
    ├─ 宏观数据 (PMI、社融、货币供应)
    ├─ 指数数据 (日线、权重、成分股)
    ├─ 市场数据 (股票统计)
    └─ VIX 页面 (波动率分析)
```

### 9.3 缓存策略

```python
import streamlit as st

@st.cache_data(ttl=3600)  # 缓存 1 小时
def load_pmi_data():
    """从 DuckDB 加载 PMI 数据"""
    conn = get_db_connection()
    try:
        df = conn.execute("SELECT * FROM cn_pmi").fetchdf()
        return df
    finally:
        conn.close()
```

---

## 10. 量化分析模块

### 10.1 VIX 计算引擎 (`src/vix/`)

| 组件 | 文件 | 职责 |
|------|------|------|
| **数据加载** | `data_loader.py` | 从 DuckDB 加载期权和 Shibor 数据 |
| **VIX 计算** | `calculator.py` | 实现 CBOE VIX 计算方法 |
| **配置管理** | `config.py` | VIX 相关配置 |
| **CLI 入口** | `run.py` | 命令行入口 |

### 10.2 支持的标的

| 类型 | 代码 | 说明 | 对应指数 |
|------|------|------|---------|
| **ETF 期权** | 510050.SH | 上证 50ETF | 000016.SH |
| | 510300.SH | 沪深 300ETF | 000300.SH |
| | 510500.SH | 中证 500ETF | 000905.SH |
| | 588000.SH | 科创 50ETF | 000688.SH |
| | 159922.SZ | 中证 500ETF | 399905.SZ |
| | 159919.SZ | 沪深 300ETF | 399300.SZ |
| **指数期权** | 000016.SH | 上证 50指数 | - |
| | 000300.SH | 沪深 300指数 | - |
| | 000852.SH | 中证 1000指数 | - |

### 10.3 VIX 计算流程

```
用户输入 (start_date, end_date, underlying)
    │
    ▼
1. 加载期权数据 (opt_basic + opt_daily)
    │
    ▼
2. 加载 Shibor 数据 (无风险利率)
    │
    ▼
3. 选择近月和次近月合约 (到期时间 >= 7 天)
    │
    ▼
4. 计算方差贡献
    ├─ 计算远期价格 F
    ├─ 确定 K0 (平值执行价)
    └─ 求和方差贡献
    │
    ▼
5. 加权插值到 30 天
    └─ VIX = 100 × √(V² × 365/30)
    │
    ▼
输出结果 (CSV 文件)
```

---

## 11. 运维与调试

### 11.1 常用命令速查

| 命令 | 说明 |
|------|------|
| `python -m src.tushare_duckdb.main` | 启动交互式 CLI |
| `streamlit run dashboard/app.py` | 启动 Dashboard |
| `python -m src.vix.run --start_date 20250101 --end_date 20250115 --underlying 510050.SH` | 计算 VIX |
| `./scripts/run_daily.sh` | 运行每日同步脚本 |
| `python src/test_import.py` | 模块导入测试 |

### 11.2 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `TUSHARE_TOKEN` | 是 | Tushare Pro API Token |
| `DB_ROOT` | 否 | 数据库根目录 (默认: `/Users/robert/Developer/DuckDB`) |
| `ENV_PATH` | 否 | .env 文件路径 (默认: `/Users/robert/.env`) |

### 11.3 日志级别

```python
import logging

# 设置日志级别
logger.setLevel(logging.DEBUG)   # 调试信息
logger.setLevel(logging.INFO)    # 默认
logger.setLevel(logging.WARNING) # 警告
logger.setLevel(logging.ERROR)   # 错误
```

---

## 12. 故障排查手册

### 12.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| API 返回空数据 | Token 无效/过期 | 检查 `TUSHARE_TOKEN` |
| 频率限制错误 | 调用过于频繁 | 增加 65 秒等待 |
| 数据缺失 | 日期范围错误 | 检查 `earliest_date`/`latest_date` |
| 数据库连接失败 | 文件被锁定 | 关闭其他进程 |
| 字段不存在 | 配置错误 | 检查 `fields` 和 `unique_keys` |

### 12.2 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 打印 API 参数
logger.debug(f"API 参数: {api_params}")

# 检查分页状态
logger.info(f"页 {page_count}, 返回 {page_rows} 行")

# 验证去重结果
logger.info(f"去重前行数: {len(df)}, 去重后行数: {len(df.drop_duplicates())}")
```

---

## 13. 扩展开发指南

### 13.1 新增数据类别

1. 在 `settings.yaml` 中添加类别配置
2. 在 `INIT_TABLES_MAP` 中添加初始化函数
3. 在主菜单中添加选项

```yaml
new_category:
  db_path: ${DB_ROOT}/tushare_duck_new.db
  tables:
    new_table:
      fields:
      - field1
      - field2
      unique_keys:
      - id
      date_column: date
      date_param_mode: single
```

### 13.2 新增 Dashboard 页面

1. 创建 `new_data_loader.py`
2. 创建 `new_charts.py`
3. 在 `app.py` 中添加路由

### 13.3 新增计算模块

1. 创建 `src/new_module/` 目录
2. 实现 `data_loader.py`、`calculator.py`、`run.py`
3. 添加配置文件 `config.py`

---

## 14. 智能体任务清单

### 14.1 修改前检查

- [ ] 阅读目标文件的完整内容
- [ ] 确认代码风格和缩进
- [ ] 检查相关配置文件

### 14.2 代码修改规范

- [ ] 使用正确的命名规范
- [ ] 添加类型提示和文档字符串
- [ ] 添加中文注释（关键逻辑）
- [ ] 使用 `logger` 替代 `print`

### 14.3 测试验证

- [ ] 运行 `python src/test_import.py`
- [ ] 测试小数据集
- [ ] 验证日志输出

### 14.4 文档更新

- [ ] 更新相关文档
- [ ] 更新配置说明（如有必要）

---

## 附录

### A. 文件路径速查

| 文件 | 路径 |
|------|------|
| 主配置 | `settings.yaml` |
| 核心模块 | `src/tushare_duckdb/` |
| VIX 模块 | `src/vix/` |
| Dashboard | `dashboard/` |
| 脚本 | `scripts/` |
| 文档 | `docs/` |

### B. 核心类索引

| 类名 | 文件 | 主要方法 |
|------|------|---------|
| `TushareFetcher` | `fetcher.py` | `fetch_data()` |
| `DataProcessor` | `processor.py` | `process_dates()`, `_process_daily()`, `_process_range()`, `_process_full_paging()` |
| `DuckDBStorage` | `storage.py` | `store_data()` |
| `DataValidator` | `data_validation.py` | `check_coverage()`, `find_missing_dates()`, `detect_anomalies()` |
| `VIXCalculator` | `vix/calculator.py` | `calculate_vix_for_date()` |

### C. 相关文档链接

- [README.md](README.md) - 用户使用指南
- [ARCHITECTURE.md](docs/Guide/ARCHITECTURE.md) - 系统架构详解
- [SCRIPTS_GUIDE.md](docs/Guide/SCRIPTS_GUIDE.md) - 脚本使用指南
- [DEPLOYMENT.md](docs/Guide/DEPLOYMENT.md) - 运维部署指南
- [TROUBLESHOOTING.md](docs/Guide/TROUBLESHOOTING.md) - 故障排除百科

---

*本指南由智能体维护，发现新模式或命令时请及时更新。*
