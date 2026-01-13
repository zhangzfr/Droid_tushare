# Tushare 2 DuckDB

这是一个高性能、模块化的 Tushare 金融数据本地化工程。利用 DuckDB 的卓越性能，为量化研究和数据工程提供稳定、高效的数据持久化解决方案。

## 🚀 核心特性

- **高性能存储**: 使用 DuckDB 作为存储引擎，支持超快的数据分析查询和高效的数据压缩。
- **模块化设计**:
  - `Fetcher`: 稳健的 Tushare API 集成，支持自动重试和频率限制（Rate Limiting）。
  - `Processor`: 数据清洗与转换逻辑封装。
  - `Storage`: 自动建表、增量更新及主键去重逻辑。
- **统一配置中心**: 通过 `settings.yaml` 集中管理 API 字段、调用限额、数据库路径及各类参数。
- **多库管理**: 智能数据分类存储（如：股票库 `stock.db`、指数库 `index.db`、宏观库 `macro.db`、参考库 `ref.db` 等）。
- **交互式菜单**: 提供全功能的 CLI 交互菜单，轻松管理数十类数据的更新、校验和探索。
- **专项补全脚本**: 针对质押数据（周频快照）及日线数据空隙，提供了专门的 Backfill 逻辑。
- **数据完整性监控**: 内置元数据追踪和数据验证报告，确保本地数据库与交易所同步。
- **数据库探索工具**: 内置交互式 SQL 查询工具，直接在命令行查看和分析本地金融数据。

## 🛠 项目结构

```text
├── src/tushare_duckdb/
│   ├── main.py             # 主入口 (交互式菜单)
│   ├── fetcher.py          # API 获取逻辑
│   ├── storage.py          # DuckDB 存储引擎
│   ├── schema.py           # 表结构定义
│   ├── data_validation.py  # 完整性校验工具
│   ├── db_explorer.py      # 数据库探索工具
│   └── config.py           # 配置加载器
├── scripts/                # 专项数据补全与迁移脚本
│   ├── backfill_pledge_stat.py
│   ├── backfill_pledge_detail.py
│   └── fix_daily_gaps.py
├── dashboard/              # 基于 Streamlit 的可视化仪表盘
├── settings.yaml           # 统一配置文件
└── requirements.txt        # 依赖清单
```

## 📋 环境要求

- Python 3.9+
- Tushare Pro Token (前往 [tushare.pro](https://tushare.pro/) 注册)
- DuckDB

## ⚙️ 快速开始

1. 克隆仓库:

   ```bash
   git clone <repository-url>
   cd Droid_tushare
   ```

2. 安装依赖:

   ```bash
   pip install -r requirements.txt
   ```

3. 配置 Token:
   编辑 `src/tushare_duckdb/config.py` 或设置环境变量 `TUSHARE_TOKEN`.

## 📖 使用指南

### 运行主程序

启动交互式菜单来管理各类数据：

```bash
python -m src.tushare_duckdb.main
```

### 补全质押数据

质押数据需要特定的迭代获取策略：

```bash
# 补全统计数据
python scripts/backfill_pledge_stat.py

# 补全明细数据 (支持 --smart 智能模式和 --force 强制模式)
python scripts/backfill_pledge_detail.py --smart
```

### 数据校验

检查本地数据库是否存在数据空缺或记录不一致：

- 使用主菜单的 `[14] 数据校验` 或 `scripts/` 下的专项脚本。

## 🤝 声明

本项目已排除 `utils/`、`extension/` 和 `quant-ml-qlib/` 等研究试用目录中的文件。
