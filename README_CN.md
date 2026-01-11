# 🚀 Droid-Tushare: 工业级 Tushare 数据本地化同步引擎

> **让量化交易者告别网络延迟与频率限制，构建属于自己的高性能本地金融数据库。**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.8+-yellow.svg)](https://duckdb.org/)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.8+-yellow.svg)](https://duckdb.org/)

`Droid-Tushare` 是一个为专业量化交易者设计的本地化数据同步方案。它不仅是将 Tushare 数据存入数据库，更是通过 **DuckDB** 的列式存储优势、**智能分页算法** 以及 **自动化异常校验**，解决金融数据获取中的所有痛点。

---

## 📚 文档导航

- 📖 [本文档](#-快速开始) - 快速上手和使用说明
- 🏗️ [系统架构](ARCHITECTURE.md) - 深度技术解析（开发必读）
- 📊 [VIX计算指南](VIX_GUIDE.md) - 波动率指数详解（量化研究者必读）
- 🚀 [运维部署](DEPLOYMENT.md) - 生产环境部署（运维工程师必读）
- 🔧 [故障排除](TROUBLESHOOTING.md) - 问题诊断与解决（故障排查必读）

---

## ✨ 核心优势

### 1. ⚡ 极致性能：由 DuckDB 驱动

- **毫秒级查询**：利用 DuckDB 向量化执行引擎，即使是亿级行情数据，复杂聚合查询也能在毫秒内完成
- **轻量持久化**：无需安装庞大的数据库服务端，单文件存储，极致易读
- **高效压缩**：列式存储天然优势，大幅节省磁盘空间

### 2. 🧠 智能同步逻辑

- **全自动分页**：自动处理 Tushare 接口 2000/5000 行限制，通过 `limit` 与 `offset` 智能递归拉取
- **自适应频控**：内置限流监测，自动触发 65 秒冷却重试，确保 7x24 小时无人值守运行
- **增量优先**：支持 `full_paging` 模式，通过对比本地最大日期实现"秒级补录"，确保架构的可维护性与数据一致性

### 3. 🛡️ 工业级数据质量保障

- **异常日期检测**：内置 `Mean-2*Std` 算法自动识别数据缺失与异常天
- **多维校验报告**：交互式生成覆盖率报告、缺失范围定位以及非交易日异常记录提示
- **元数据追踪**：自动记录每张表的最早/最晚日期、记录数、最后更新时间

### 4. 🗂️ 全品种覆盖

项目内置 **50+ 张金融数据表**，涵盖股票、基金、期货、期权、债券、指数、宏观等全品种数据。所有表结构均基于 Tushare Pro API 标准，开箱即用。

---

## 🚀 快速开始

### 5 分钟快速上手

```bash
# 1. 克隆仓库
git clone https://github.com/robert/droid_tushare.git
cd droid_tushare

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cat > .env << EOF
TUSHARE_TOKEN=your_token_here
DB_ROOT=./data
LOG_LEVEL=INFO
EOF

# 4. 启动 Dashboard
streamlit run dashboard/app.py
```

### 实战案例 1：首次同步股票日线数据

```bash
# 启动交互式终端
python -m src.tushare_duckdb.main

# 按照提示操作：
# >>> 请选择数据类别 (输入数字):
#  [ 1] 股票列表         [ 2] 股票事件         [ 3] 股票行情
# >>> 3

# >>> 可用表（15个）: daily, adj_factor, daily_basic, stk_limit, suspend_d
# >>> 选择表（逗号分隔，all 为全部，默认 all）: daily,adj_factor

# >>> 开始日期（YYYYMMDD/YYYYMM，默认 20241001）: 20240101
# >>> 结束日期（YYYYMMDD/YYYYMM，默认 20241231）: 20241231

# >>> 模式: 1.增量插入 2.强制覆盖 3.强制去重插入 [默认1]: 1
```

### 实战案例 2：计算 VIX 波动率指数

```bash
# 计算上证 50ETF 的 VIX
python -m src.vix.run \
  --start_date 20240101 \
  --end_date 20240131 \
  --underlying 510050.SH

# 输出文件：
# - data/vix_result_510050.SH_20240101_20240131.csv
# - data/vix_details_near_510050.SH_20240101_20240131.csv
# - data/vix_details_next_510050.SH_20240101_20240131.csv
```

### 实战案例 3：程序化查询数据

```python
import duckdb
import pandas as pd

# 连接数据库
conn = duckdb.connect('data/tushare_duck_stock.db')

# 查询特定股票的日线数据
df = conn.execute("""
    SELECT trade_date, close, vol, amount
    FROM daily
    WHERE ts_code = '000001.SZ'
        AND trade_date BETWEEN '20240101' AND '20241231'
    ORDER BY trade_date
""").fetchdf()

# 计算收益率
df['return'] = df['close'].pct_change()
print(df.head())

conn.close()
```

---

## 📊 支持的数据表

### 📈 股票数据 (Stock)
- **基础信息**：`stock_basic` (股票列表), `stock_company` (公司信息)
- **行情数据**：`daily` (日线行情), `adj_factor` (复权因子), `daily_basic` (每日指标)
- **交易信息**：`stk_limit` (涨跌停), `suspend_d` (停复牌), `bak_basic` (备用行情)
- **事件数据**：`namechange` (更名), `hs_const` (沪深港通), `stk_managers` (高管), `stk_rewards` (分红)

### 📊 指数数据 (Index)
- **基础信息**：`index_basic` (指数列表), `sw_index_classify_2014/2021` (申万分类)
- **行情数据**：`index_daily` (日线), `index_dailybasic` (每日指标), `daily_info` (大盘统计)
- **成分股权重**：`index_weight` (权重), `ths_member` (同花顺成分), `sw_index_member_all` (申万成分)

### 💰 基金数据 (Fund)
- **基础信息**：`fund_basic` (基金列表), `fund_company` (基金公司)
- **净值数据**：`fund_nav` (净值), `fund_daily` (日线行情)
- **持仓分析**：`fund_portfolio` (持仓明细)

### 🛢️ 期货数据 (Future)
- **基础信息**：`fut_basic` (合约), `trade_cal_future` (交易日历)
- **行情数据**：`fut_daily` (日线), `fut_index_daily` (指数日线)
- **持仓结算**：`fut_wsr` (仓单), `fut_settle` (结算参数), `fut_holding` (持仓排名)

### 📋 期权数据 (Option)
- **基础信息**：`opt_basic` (期权合约)
- **行情数据**：`opt_daily` (日线行情)

### 🏦 债券数据 (Bond)
- **可转债**：`cb_basic` (基础), `cb_daily` (日线), `cb_issue` (发行), `cb_call` (赎回)
- **现券交易**：`bond_blk` (大宗交易), `repo_daily` (质押式回购)
- **收益率曲线**：`yc_cb` (可转债收益率)

### 💹 资金流向 (Moneyflow)
- **个股资金流**：`moneyflow` (资金流向)
- **同花顺数据**：`moneyflow_ths` (同花顺), `moneyflow_dc` (东财)
- **板块资金流**：`moneyflow_ind_ths` (行业), `moneyflow_mkt_dc` (市场)

### 💼 融资融券 (Margin)
- **融资融券**：`margin` (汇总), `margin_detail` (明细), `margin_secs` (标的券)
- **转融通**：`slb_len` (转融通余额), `slb_sec` (转融通明细)

### 🌐 宏观数据 (Macro)
- **国内宏观**：`shibor` (Shibor利率), `cn_m` (货币供应量), `sf_month` (社融数据), `cn_pmi` (采购经理人指数)
- **国际宏观**：`us_tycr` (美债收益率曲线) 等

---

## 🏗️ 系统架构概览

### 分层架构

```
用户交互层 (User Interface)
    ↓ CLI / Dashboard / Python API
业务逻辑层 (Business Logic)
    ├─ 数据同步引擎 (tushare_duckdb)
    ├─ 量化分析引擎 (vix)
    └─ 可视化引擎 (dashboard)
数据访问层 (Data Access)
    ├─ DuckDB 连接管理
    └─ 外部 API 管理 (Tushare Pro)
数据存储层 (Data Storage)
    └─ 14 个 DuckDB 数据库文件
```

### 核心模块

| 模块 | 职责 | 文件 |
|------|------|------|
| **API 客户端** | 与 Tushare API 通信、分页、重试 | `fetcher.py` |
| **数据处理** | 协调数据获取、处理和存储流程 | `processor.py` |
| **数据存储** | DuckDB 存储操作、字段映射 | `storage.py` |
| **数据校验** | 数据质量检查、覆盖率分析 | `data_validation.py` |
| **元数据管理** | 表结构信息、统计信息 | `metadata.py` |

**📖 深入了解**：查看 [ARCHITECTURE.md](ARCHITECTURE.md) 获取详细的架构设计、模块职责和数据流转说明。

---

## 📈 VIX 计算模块

本项目新增了 `src/vix` 子模块，用于计算中国市场的波动率指数（VIX）。该模块基于本地 DuckDB 中的期权数据和 Shibor 利率进行无模型（Model‑Free）计算。

### 关键特性

- **本地数据**：直接读取 `opt_basic`、`opt_daily` 与 `shibor` 表，无需网络请求
- **完整可追溯**：计算结果保存在 CSV 文件中，包含所有中间变量
- **多标的支持**：支持 9 个 ETF 期权和 3 个指数期权

### 支持的标的

| 标的代码 | 说明 | 对应指数 |
|----------|------|---------|
| `510050.SH` | 上证 50ETF | 000016.SH |
| `510300.SH` | 沪深 300ETF | 000300.SH |
| `510500.SH` | 中证 500ETF | 000905.SH |
| `588000.SH` | 科创 50ETF | 000688.SH |
| `159915.SZ` | 创业板ETF | 399102.SZ |
| ... | 更多标的 | [查看完整列表](VIX_GUIDE.md#-支持的标的) |

### 使用示例

```bash
# 计算上证50ETF波动率 (默认)
python -m src.vix.run --start_date 20230101 --end_date 20230110

# 计算沪深300ETF波动率
python -m src.vix.run --start_date 20230101 --end_date 20230110 --underlying 510300.SH
```

**📖 深入了解**：查看 [VIX_GUIDE.md](VIX_GUIDE.md) 获取详细的计算方法、数据源说明、结果解读和高级应用。

---

## 🚀 生产部署

### 部署方案

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **单机部署** | 个人研究、小团队 | 简单、成本低 | 扩展性差 |
| **Docker 部署** | 中大型团队 | 可移植、易扩展 | 需要 Docker 知识 |
| **Kubernetes** | 大型团队 | 高可用、自动扩缩容 | 复杂度高 |

### 推荐配置

| 规模 | CPU | 内存 | 存储 | 网络 |
|------|-----|------|------|------|
| **最小** | 2 核 | 4 GB | 100 GB SSD | 10 Mbps |
| **标准** | 4 核 | 8 GB | 500 GB SSD | 100 Mbps |
| **生产** | 8 核 | 16 GB | 2 TB SSD + 5 TB HDD | 1 Gbps |

### 备份策略

| 类型 | 频率 | 保留期 | 存储位置 |
|------|------|--------|---------|
| **增量备份** | 每天凌晨 3 点 | 7 天 | 本地 |
| **全量备份** | 每周日凌晨 4 点 | 30 天 | 本地 |
| **云端备份** | 每天凌晨 5 点 | 90 天 | S3/OSS |

**📖 深入了解**：查看 [DEPLOYMENT.md](DEPLOYMENT.md) 获取完整的部署流程、Docker配置、监控告警和性能优化指南。

---

## 🔧 配置与管理

### 环境变量配置

创建 `.env` 文件：

```bash
# 必需：Tushare API Token
TUSHARE_TOKEN=your_tushare_token_here

# 必需：数据库存储根目录
DB_ROOT=/path/to/your/database/directory

# 可选：日志级别
LOG_LEVEL=INFO

# 可选：调试模式
DEBUG=false
```

### settings.yaml 核心配置

项目核心配置位于 `settings.yaml` 文件，所有数据表定义、API 参数和同步逻辑均在此集中管理。

**关键配置项**：
- `db_path`：数据库文件路径
- `requires_paging`：是否需要分页处理
- `date_param_mode`：日期参数模式（`single`/`range`/`full_paging`）
- `unique_keys`：唯一键约束
- `fields`：API 返回的字段列表

---

## 🔧 故障排除

### 快速参考

| 命令 | 说明 |
|------|------|
| `python -m src.tushare_duckdb.main` | 启动数据同步终端 |
| `streamlit run dashboard/app.py` | 启动可视化仪表盘 |
| `python -m src.vix.run --start_date YYYYMMDD` | 计算 VIX |
| `./scripts/diagnose.sh` | 运行系统诊断 |

### 常见问题

#### 1. API 频率限制
**症状**：日志显示 "达到访问频率限制，等待重试"  
**解决方案**：系统自动等待 65 秒后重试，无需手动干预

#### 2. 数据库锁定错误
**症状**：`IO Error: Cannot open file ... because it is being used by another process`  
**解决方案**：确保没有其他程序（如 DBeaver）同时连接数据库

#### 3. VIX 计算结果异常
**症状**：VIX 为负数或 > 100  
**解决方案**：检查期权数据完整性，参考 [VIX_GUIDE.md](VIX_GUIDE.md) 的数据质量建议

**📖 深入了解**：查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 获取完整的故障排除百科，包含错误代码速查、11大类问题诊断和应急恢复手册。

---

## 📊 性能基准

### 数据同步性能

| 操作 | 数据量 | 耗时 | 吞吐量 |
|------|-------|------|--------|
| 股票日线 (单日) | ~5,000 条 | 2-5 秒 | 1,000-2,500 条/秒 |
| 指数日线 (单日) | ~15 条 | 1-2 秒 | 10-15 条/秒 |
| 期权日线 (单日) | ~50,000 条 | 30-60 秒 | 800-1,600 条/秒 |

### VIX 计算性能

| 范围 | 日期数 | 耗时 |
|------|-------|------|
| 1 周 | 5 | 2-5 秒 |
| 1 个月 | 20 | 8-15 秒 |
| 1 年 | 250 | 60-120 秒 |

---

## 📖 详细文档索引

### 根据用户角色

| 用户角色 | 推荐阅读 | 文档 |
|---------|---------|------|
| **新用户** | 快速开始 → 实战案例 | README.md |
| **开发者** | 系统架构 → 代码实现 | ARCHITECTURE.md |
| **量化研究者** | VIX计算 → 策略应用 | VIX_GUIDE.md |
| **运维工程师** | 部署流程 → 监控配置 | DEPLOYMENT.md |
| **故障排查** | 错误速查 → 诊断流程 | TROUBLESHOOTING.md |

### 根据使用场景

| 场景 | 推荐文档 |
|------|---------|
| **首次安装** | README.md → 环境准备 |
| **数据同步** | README.md → 使用指南 → TROUBLESHOOTING.md |
| **VIX分析** | VIX_GUIDE.md → 使用指南 → 结果解读 |
| **系统部署** | DEPLOYMENT.md → 部署架构 → Docker配置 |
| **性能优化** | DEPLOYMENT.md → 性能优化 |
| **问题排查** | TROUBLESHOOTING.md → 错误代码速查 |

---

## 🤝 贡献与反馈

### 开发哲学："Slow is Fast"

本项目秉承 **"慢即是快"** 的开发理念：
- **推理优先**：在编写代码前进行充分的思考和设计
- **质量至上**：注重代码的可读性、可维护性和长期稳定性
- **稳健第一**：优先确保系统的可靠性和数据一致性

### 贡献指南

欢迎各种形式的贡献！
- 报告 Bug：[创建 Issue](https://github.com/robert/droid_tushare/issues)
- 功能建议：[讨论](https://github.com/robert/droid_tushare/discussions)
- 代码贡献：[提交 Pull Request](https://github.com/robert/droid_tushare/pulls)

---

## 📄 许可证

本项目采用 **MIT License** 开源协议。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- **Tushare**：提供优质的金融数据 API 服务
- **DuckDB**：卓越的列式数据库引擎
- **Streamlit**：优雅的数据可视化框架
- **开源社区**：pandas、numpy 等优秀工具库的支持

---

**Droid-Tushare** - 让数据驱动投资决策 🚀

---

**文档版本**: v2.0.0  
**最后更新**: 2026-01-06  
**维护者**: Robert
