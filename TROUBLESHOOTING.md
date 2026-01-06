# 🔧 Droid-Tushare 故障排除百科

本文档提供 Droid-Tushare 项目的常见问题诊断和解决方案，帮助您快速解决使用过程中遇到的各种问题。

---

## 📋 目录

- [1. 错误代码速查](#1-错误代码速查)
- [2. 安装与配置问题](#2-安装与配置问题)
- [3. 数据同步问题](#3-数据同步问题)
- [4. 数据库问题](#4-数据库问题)
- [5. VIX 计算问题](#5-vix-计算问题)
- [6. Dashboard 问题](#6-dashboard-问题)
- [7. 性能问题](#7-性能问题)
- [8. 数据质量问题](#8-数据质量问题)
- [9. 网络问题](#9-网络问题)
- [10. 系统资源问题](#10-系统资源问题)
- [11. 应急恢复手册](#11-应急恢复手册)

---

## 1. 错误代码速查

### 1.1 常见错误代码

| 错误代码 | 严重级别 | 可能原因 | 快速解决 |
|---------|---------|---------|---------|
| `TUSHARE_API_ERROR` | 高 | Tushare API 错误 | 检查 Token、网络连接 |
| `RATE_LIMIT_EXCEEDED` | 中 | API 频率限制 | 等待 65 秒后重试 |
| `DB_LOCK_ERROR` | 高 | 数据库被锁定 | 关闭其他连接，重启服务 |
| `TABLE_NOT_FOUND` | 中 | 表不存在 | 运行初始化脚本 |
| `DATA_VALIDATION_FAILED` | 中 | 数据校验失败 | 检查数据完整性 |
| `MISSING_DEPENDENCY` | 低 | 缺少依赖 | 安装缺少的包 |
| `CONFIG_ERROR` | 中 | 配置错误 | 检查 settings.yaml 和 .env |
| `MEMORY_ERROR` | 高 | 内存不足 | 增加内存或分批处理 |
| `PERMISSION_DENIED` | 中 | 权限不足 | 检查文件权限 |
| `TIMEOUT_ERROR` | 中 | 超时 | 增加超时时间或优化查询 |

### 1.2 日志级别说明

| 级别 | 说明 | 使用场景 |
|------|------|---------|
| `DEBUG` | 详细调试信息 | 开发环境、问题诊断 |
| `INFO` | 一般信息 | 正常运行 |
| `WARNING` | 警告信息 | 可能的问题但不影响运行 |
| `ERROR` | 错误信息 | 需要关注的错误 |
| `CRITICAL` | 严重错误 | 需要立即处理 |

---

## 2. 安装与配置问题

### 2.1 依赖安装失败

**错误信息**：
```
ERROR: Could not find a version that satisfies the requirement tushare
```

**原因分析**：
- Python 版本不兼容
- pip 版本过旧
- 网络问题

**解决方案**：

```bash
# 1. 检查 Python 版本
python --version  # 需要 3.8+

# 2. 升级 pip
pip install --upgrade pip

# 3. 使用清华镜像源（国内推荐）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 或使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 2.2 Tushare Token 错误

**错误信息**：
```
tushare.errors.TushareException: 您还没有权限或没有登录
```

**原因分析**：
- Token 无效或过期
- Token 权限不足
- 环境变量未设置

**解决方案**：

```bash
# 1. 获取有效的 Token
# 访问 https://tushare.pro/user/token

# 2. 检查 .env 文件
cat .env
# 应该包含：TUSHARE_TOKEN=your_actual_token_here

# 3. 手动设置环境变量
export TUSHARE_TOKEN=your_actual_token_here

# 4. 验证 Token
python -c "import tushare as ts; pro = ts.pro_api(); print(pro.query('trade_cal', exchange='SSE'))"
```

### 2.3 数据库路径错误

**错误信息**：
```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/database'
```

**原因分析**：
- `DB_ROOT` 环境变量未设置
- 目录不存在
- 权限不足

**解决方案**：

```bash
# 1. 创建数据库目录
mkdir -p /path/to/your/database

# 2. 检查 .env 文件
cat .env
# 应该包含：DB_ROOT=/path/to/your/database

# 3. 检查权限
ls -la /path/to/your/database

# 4. 设置正确权限
chmod 755 /path/to/your/database
```

### 2.4 YAML 配置错误

**错误信息**：
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**原因分析**：
- YAML 语法错误
- 缩进不正确
- 特殊字符未转义

**解决方案**：

```bash
# 1. 使用 YAML 验证工具
pip install yamllint
yamllint settings.yaml

# 2. 检查缩进（必须使用空格，不能用 Tab）

# 3. 检查特殊字符（如 $ 需要转义）

# 4. 恢复默认配置
git checkout settings.yaml
```

---

## 3. 数据同步问题

### 3.1 API 频率限制

**错误信息**：
```
达到访问频率限制，等待重试...
```

**原因分析**：
- 免费用户受 500 次/分钟限制
- 请求过于频繁

**解决方案**：

```python
# 方法 1：自动重试（系统已内置）
# 无需操作，系统会自动等待 65 秒后重试

# 方法 2：调整请求频率
# 在 settings.yaml 中增加 limit 参数
daily:
  limit: 3000  # 降低单次请求数量

# 方法 3：分批处理
# 不要一次性同步所有表，分多次运行
# 第一次：python -m src.tushare_duckdb.main
# 选择 stock，只同步 daily
# 第二次：再次运行，同步 adj_factor
```

### 3.2 数据同步卡住

**症状**：
- 进程无输出
- 日志无更新
- CPU 使用率低

**原因分析**：
- 网络问题
- API 响应慢
- 死锁

**解决方案**：

```bash
# 1. 检查网络连接
ping tushare.pro
curl -I https://tushare.pro

# 2. 检查进程状态
ps aux | grep python
top -p $(pgrep -f "python.*tushare")

# 3. 查看实时日志
tail -f logs/sync_*.log

# 4. 重启进程
./scripts/stop.sh
./scripts/start.sh

# 5. 增加超时时间
# 在 fetcher.py 中调整
```

### 3.3 数据同步中断

**错误信息**：
```
KeyboardInterrupt
或
ConnectionError
```

**原因分析**：
- 手动中断
- 网络中断
- 系统重启

**解决方案**：

```bash
# 1. 检查数据完整性
python -m src.tushare_duckdb.data_validation

# 2. 重新同步中断的日期范围
python -m src.tushare_duckdb.main
# 选择类别
# 输入开始日期（中断的那天）
# 选择增量插入模式

# 3. 或使用覆盖模式重新同步
python -m src.tushare_duckdb.main
# 选择类别
# 输入日期范围
# 选择覆盖模式（选项 2）
```

### 3.4 数据同步速度慢

**症状**：
- 同步耗时过长
- 每秒处理记录数少

**原因分析**：
- 网络带宽不足
- 批处理大小不合理
- 系统资源不足

**解决方案**：

```python
# 1. 调整批处理大小
# 在 settings.yaml 中调整 limit
daily:
  limit: 3000  # 减小到 3000

# 2. 并行处理（实验性）
# 修改 processor.py，使用多线程

# 3. 优化网络
# 使用更快的网络
# 使用 CDN 加速

# 4. 增加系统资源
# 升级 CPU、内存
```

---

## 4. 数据库问题

### 4.1 数据库锁定错误

**错误信息**：
```
IO Error: Cannot open file ... because it is being used by another process
```

**原因分析**：
- DuckDB 单进程写锁
- 另一个进程正在写入
- 可视化工具（如 DBeaver）正在连接

**解决方案**：

```bash
# 1. 查找占用进程
lsof | grep tushare_duck

# 2. 停止所有相关进程
killall python
killall streamlit

# 3. 关闭数据库连接工具
# 关闭 DBeaver、DB Browser 等工具

# 4. 检查并清理锁文件
find /opt/droid_tushare/data -name "*.lock" -delete
```

### 4.2 数据库损坏

**错误信息**：
```
IO Error: Database file is corrupted
```

**原因分析**：
- 磁盘空间不足
- 异常断电
- 文件系统错误

**解决方案**：

```bash
# 1. 备份损坏的文件
cp tushare_duck_stock.db tushare_duck_stock.db.corrupted

# 2. 检查磁盘空间
df -h

# 3. 尝试恢复
python -c "
import duckdb
conn = duckdb.connect('tushare_duck_stock.db')
conn.execute('PRAGMA integrity_check')
conn.close()
"

# 4. 如果无法恢复，从备份恢复
./scripts/restore_backup.sh backups/full/20240101_120000.tar.gz
```

### 4.3 表不存在错误

**错误信息**：
```
Catalog Error: Table with name daily does not exist!
```

**原因分析**：
- 表未初始化
- 数据库文件路径错误

**解决方案**：

```python
# 1. 初始化表
python -c "
from src.tushare_duckdb.utils import init_tables_for_category, get_connection
from src.tushare_duckdb.config import API_CONFIG

conn = get_connection('/path/to/database')
init_tables_for_category(conn, ['daily', 'adj_factor'])
conn.close()
"

# 2. 或通过主程序初始化
python -m src.tushare_duckdb.main
# 选择类别
# 系统会自动初始化表

# 3. 检查数据库路径
ls -la /path/to/database
```

### 4.4 查询性能差

**症状**：
- 查询耗时过长
- Dashboard 加载慢

**原因分析**：
- 缺少索引
- 数据量过大
- 查询不优化

**解决方案**：

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# 1. 创建索引
conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_trade_date ON daily(trade_date)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_ts_code ON daily(ts_code)")

# 2. 检查查询计划
plan = conn.explain("SELECT * FROM daily WHERE ts_code='000001.SZ' AND trade_date='20240101'")
print(plan)

# 3. 优化查询
# ❌ 不好：使用 LIKE
# conn.execute("SELECT * FROM daily WHERE ts_code LIKE '000001.SZ%'")

# ✅ 好：使用精确匹配
conn.execute("SELECT * FROM daily WHERE ts_code='000001.SZ'")

# 4. 分区查询（按年度）
conn.execute("SELECT * FROM daily WHERE trade_date BETWEEN '20240101' AND '20241231'")

conn.close()
```

---

## 5. VIX 计算问题

### 5.1 VIX 计算结果异常

**症状**：
- VIX 为负数
- VIX > 100
- VIX 突然跳变

**原因分析**：
- 期权数据错误
- Shibor 数据缺失
- 合约选择逻辑错误

**解决方案**：

```python
import pandas as pd

# 1. 检查期权数据
details = pd.read_csv('data/vix_details_near_510050.SH_20240101_20240131.csv')

# 检查价格异常
abnormal = details[
    (details['call'] <= 0) |
    (details['put'] <= 0) |
    (details['call'] > 10) |
    (details['put'] > 10)
]
print(f"异常价格记录数: {len(abnormal)}")
print(abnormal.head())

# 2. 检查 Shibor 数据
shibor = pd.read_csv('data/shibor_interpolated.csv', index_col=0)
print(f"Shibor 缺失值: {shibor.isnull().sum().sum()}")

# 3. 重新计算（跳过异常日期）
python -m src.vix.run --start_date 20240101 --end_date 20240131
```

### 5.2 数据缺失错误

**错误信息**：
```
ValueError: No option data found for date 20240115
```

**原因分析**：
- 期权数据未同步
- 日期是非交易日
- 合约未上市

**解决方案**：

```bash
# 1. 同步期权数据
python -m src.tushare_duckdb.main
# 选择 option
# 同步 opt_basic 和 opt_daily

# 2. 检查交易日历
python -c "
import duckdb
conn = duckdb.connect('tushare_duck_basic.db')
result = conn.execute(\"SELECT * FROM trade_cal WHERE cal_date='20240115' AND exchange='SSE'\").fetchdf()
print(result)
conn.close()
"

# 3. 使用有效日期
python -m src.vix.run --start_date 20240101 --end_date 20240110
```

### 5.3 无风险利率错误

**错误信息**：
```
KeyError: '20240115' in shibor_interpolated
```

**原因分析**：
- Shibor 数据未同步
- 日期范围不匹配

**解决方案**：

```bash
# 1. 同步 Shibor 数据
python -m src.tushare_duckdb.main
# 选择 macro
# 同步 shibor 表

# 2. 检查 Shibor 数据范围
python -c "
import duckdb
conn = duckdb.connect('tushare_duck_macro.db')
result = conn.execute(\"SELECT MIN(date), MAX(date) FROM shibor\").fetchdf()
print(result)
conn.close()
"

# 3. 扩展日期范围
python -m src.vix.run --start_date 20231201 --end_date 20240131
```

---

## 6. Dashboard 问题

### 6.1 Dashboard 无法启动

**错误信息**：
```
Streamlit API Error: Failed to start server
```

**原因分析**：
- 端口被占用
- 依赖未安装
- 配置错误

**解决方案**：

```bash
# 1. 检查端口占用
lsof -i :8501
netstat -an | grep 8501

# 2. 停止占用端口的进程
kill -9 $(lsof -t -i:8501)

# 3. 使用其他端口
streamlit run dashboard/app.py --server.port 8502

# 4. 重新安装依赖
pip install --upgrade streamlit
pip install --upgrade plotly
```

### 6.2 Dashboard 加载慢

**症状**：
- 页面加载时间长
- 图表渲染慢

**原因分析**：
- 数据量过大
- 查询未优化
- 缓存失效

**解决方案**：

```python
import streamlit as st

# 1. 启用缓存
@st.cache_data(ttl=3600)  # 缓存 1 小时
def load_data():
    # 数据加载逻辑
    pass

# 2. 减少数据量
# 只加载最近 1 年数据
df = df[df['date'] > '20230101']

# 3. 使用分页
page_size = 100
page = st.number_input('Page', min_value=1)
start = (page - 1) * page_size
end = start + page_size
st.dataframe(df[start:end])

# 4. 使用更高效的图表
# st.dataframe 比 st.table 更快
st.dataframe(df)
```

### 6.3 图表显示错误

**错误信息**：
```
PlotlyError: Invalid value for type
```

**原因分析**：
- 数据类型错误
- 缺失值未处理
- 图表配置错误

**解决方案**：

```python
import pandas as pd
import plotly.express as px

# 1. 检查数据类型
print(df.dtypes)

# 2. 处理缺失值
df = df.dropna()
df = df.fillna(0)

# 3. 转换数据类型
df['date'] = pd.to_datetime(df['date'])
df['value'] = pd.to_numeric(df['value'])

# 4. 简化图表配置
fig = px.line(df, x='date', y='value')
st.plotly_chart(fig)
```

---

## 7. 性能问题

### 7.1 内存占用过高

**症状**：
- OOM (Out of Memory) 错误
- 系统卡顿
- 进程被杀死

**原因分析**：
- 数据量过大
- 批处理不合理
- 内存泄漏

**解决方案**：

```bash
# 1. 检查内存使用
free -h
ps aux --sort=-%mem | head -10

# 2. 增加 swap 空间
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 限制内存使用
ulimit -v 8388608  # 限制 8GB

# 4. 分批处理
# 不要一次性同步所有数据
python -m src.tushare_duckdb.main
# 按年份分批同步
```

### 7.2 CPU 占用过高

**症状**：
- CPU 使用率 100%
- 响应慢

**原因分析**：
- 并发查询过多
- 复杂计算
- 无限循环

**解决方案**：

```python
# 1. 限制并发
import concurrent.futures

with ThreadPoolExecutor(max_workers=4) as executor:  # 限制 4 个线程
    results = list(executor.map(process_data, data_list))

# 2. 优化算法
# 避免嵌套循环
# ❌ 不好
for i in range(1000):
    for j in range(1000):
        # 复杂计算

# ✅ 好
import numpy as np
matrix = np.zeros((1000, 1000))
# 使用向量化操作

# 3. 使用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(x):
    # 复杂计算
    pass
```

### 7.3 磁盘 I/O 瓶颈

**症状**：
- 读写速度慢
- 系统卡顿

**原因分析**：
- 磁盘性能差
- 频繁的小文件读写
- 日志文件过大

**解决方案**：

```bash
# 1. 检查磁盘 I/O
iostat -x 1
iotop

# 2. 使用 SSD
# 将数据迁移到 SSD

# 3. 减少小文件写入
# 使用批量插入

# 4. 清理日志
find /opt/droid_tushare/logs -name "*.log" -mtime +30 -delete

# 5. 压缩旧数据
gzip old_data.db
```

---

## 8. 数据质量问题

### 8.1 数据缺失

**症状**：
- 某些日期没有数据
- 记录数少于预期

**原因分析**：
- 非交易日
- API 数据缺失
- 同步失败

**解决方案**：

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# 1. 检查日期范围
result = conn.execute("""
    SELECT
        MIN(trade_date) as min_date,
        MAX(trade_date) as max_date,
        COUNT(*) as record_count
    FROM daily
""").fetchdf()
print(result)

# 2. 检查缺失的交易日
result = conn.execute("""
    WITH trade_dates AS (
        SELECT DISTINCT cal_date
        FROM trade_cal
        WHERE exchange='SSE' AND is_open=1
    ),
    existing_dates AS (
        SELECT DISTINCT trade_date
        FROM daily
    )
    SELECT cal_date
    FROM trade_dates
    LEFT JOIN existing_dates ON trade_dates.cal_date = existing_dates.trade_date
    WHERE existing_dates.trade_date IS NULL
    ORDER BY cal_date
    LIMIT 10
""").fetchdf()
print("缺失的交易日：")
print(result)

# 3. 重新同步缺失日期
python -m src.tushare_duckdb.main
# 选择覆盖模式
# 输入缺失日期范围

conn.close()
```

### 8.2 数据重复

**症状**：
- 记录数异常多
- 查询结果重复

**原因分析**：
- 重复插入
- 唯一键配置错误
- 去重逻辑失败

**解决方案**：

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# 1. 检查重复记录
result = conn.execute("""
    SELECT ts_code, trade_date, COUNT(*) as count
    FROM daily
    GROUP BY ts_code, trade_date
    HAVING count > 1
    LIMIT 10
""").fetchdf()
print("重复记录：")
print(result)

# 2. 删除重复记录（保留最新一条）
conn.execute("""
    DELETE FROM daily
    WHERE (ts_code, trade_date) NOT IN (
        SELECT ts_code, trade_date
        FROM daily
        ORDER BY trade_date DESC
        LIMIT 1
    )
""")

# 3. 或重新同步（覆盖模式）
# python -m src.tushare_duckdb.main
# 选择覆盖模式

conn.close()
```

### 8.3 数据异常值

**症状**：
- 价格为 0 或负数
- 成交量异常
- 百分比超过 100

**原因分析**：
- 数据源错误
- 数据解析错误
- 单位错误

**解决方案**：

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# 1. 检查异常价格
result = conn.execute("""
    SELECT ts_code, trade_date, open, high, low, close
    FROM daily
    WHERE close <= 0
       OR open < 0
       OR high < 0
       OR low < 0
       OR high < low
    LIMIT 10
""").fetchdf()
print("异常价格记录：")
print(result)

# 2. 检查异常成交量
result = conn.execute("""
    SELECT ts_code, trade_date, vol, amount
    FROM daily
    WHERE vol < 0
       OR vol > 1000000000  # 超过 100 亿
    LIMIT 10
""").fetchdf()
print("异常成交量记录：")
print(result)

# 3. 删除或标记异常记录
conn.execute("""
    DELETE FROM daily
    WHERE close <= 0
""")

conn.close()
```

---

## 9. 网络问题

### 9.1 无法连接 Tushare API

**错误信息**：
```
ConnectionError: Failed to establish a new connection
```

**原因分析**：
- 网络不可达
- DNS 解析失败
- 防火墙阻止

**解决方案**：

```bash
# 1. 检查网络连接
ping tushare.pro
curl -I https://tushare.pro

# 2. 检查 DNS 解析
nslookup tushare.pro
dig tushare.pro

# 3. 检查防火墙
sudo ufw status
sudo iptables -L

# 4. 使用代理
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# 5. 修改 hosts 文件（临时）
sudo echo "127.0.0.1 tushare.pro" >> /etc/hosts
```

### 9.2 超时错误

**错误信息**：
```
TimeoutError: Request timed out after 30 seconds
```

**原因分析**：
- 网络延迟高
- 服务器响应慢
- 超时时间设置过短

**解决方案**：

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. 增加超时时间
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

response = session.get(
    "https://api.tushare.pro",
    timeout=60  # 增加到 60 秒
)

# 2. 在 fetcher.py 中调整超时
# 查找 timeout 参数并增加
```

---

## 10. 系统资源问题

### 10.1 磁盘空间不足

**错误信息**：
```
OSError: [Errno 28] No space left on device
```

**原因分析**：
- 磁盘已满
- 日志文件过大
- 备份文件过多

**解决方案**：

```bash
# 1. 检查磁盘空间
df -h

# 2. 查找大文件
find /opt/droid_tushare -type f -size +100M -exec ls -lh {} \;

# 3. 清理日志
find /opt/droid_tushare/logs -name "*.log" -mtime +30 -delete

# 4. 清理备份
find /opt/droid_tushare/backups -name "*.tar.gz" -mtime +90 -delete

# 5. 压缩数据库
gzip tushare_duck_stock.db

# 6. 扩展磁盘空间
# 使用云存储或添加新硬盘
```

### 10.2 文件句柄耗尽

**错误信息**：
```
OSError: [Errno 24] Too many open files
```

**原因分析**：
- 打开文件过多
- 文件句柄限制过低

**解决方案**：

```bash
# 1. 检查当前限制
ulimit -n

# 2. 临时增加限制
ulimit -n 4096

# 3. 永久增加限制
# 编辑 /etc/security/limits.conf
# 添加：
# robert soft nofile 4096
# robert hard nofile 8192

# 4. 重启生效
```

---

## 11. 应急恢复手册

### 11.1 完全恢复流程

当系统完全崩溃时的恢复步骤：

```bash
#!/bin/bash

echo "========================================"
echo "Droid-Tushare 应急恢复流程"
echo "========================================"

# 步骤 1：停止所有服务
echo "[1/8] 停止所有服务..."
./scripts/stop.sh

# 步骤 2：备份当前状态（即使损坏）
echo "[2/8] 备份当前状态..."
BACKUP_DIR="/opt/droid_tushare/backups/emergency_$(date +%Y%m%d_%H%M%S)"
mkdir -p ${BACKUP_DIR}
cp -r /opt/droid_tushare/data ${BACKUP_DIR}/
cp -r /opt/droid_tushare/config ${BACKUP_DIR}/

# 步骤 3：检查磁盘空间
echo "[3/8] 检查磁盘空间..."
df -h

# 步骤 4：从最近的全量备份恢复
echo "[4/8] 从备份恢复..."
LATEST_BACKUP=$(ls -t /opt/droid_tushare/backups/full/*.tar.gz | head -1)
./scripts/restore_backup.sh ${LATEST_BACKUP}

# 步骤 5：验证数据库完整性
echo "[5/8] 验证数据库完整性..."
python -c "
import duckdb
import os

for db_file in os.listdir('/opt/droid_tushare/data'):
    if db_file.endswith('.db'):
        try:
            conn = duckdb.connect(f'/opt/droid_tushare/data/{db_file}')
            conn.execute('PRAGMA integrity_check')
            conn.close()
            print(f'✓ {db_file} 完整')
        except Exception as e:
            print(f'✗ {db_file} 错误: {e}')
"

# 步骤 6：重新同步最新数据
echo "[6/8] 重新同步最新数据..."
python -m src.tushare_duckdb.main
# 选择需要的类别
# 输入最近缺失的日期范围

# 步骤 7：重新计算 VIX
echo "[7/8] 重新计算 VIX..."
python -m src.vix.run --start_date $(date -d '7 days ago' +\%Y\%m\%d) --end_date $(date +\%Y\%m\%d)

# 步骤 8：启动服务
echo "[8/8] 启动服务..."
./scripts/start.sh

# 验证服务状态
sleep 10
curl -f http://localhost:8501/_stcore/health
if [ $? -eq 0 ]; then
    echo "✓ 服务启动成功"
else
    echo "✗ 服务启动失败，请检查日志"
    tail -50 /opt/droid_tushare/logs/*.log
fi

echo "========================================"
echo "恢复流程完成"
echo "========================================"
```

### 11.2 快速诊断脚本

创建 `scripts/diagnose.sh`：

```bash
#!/bin/bash

echo "========================================"
echo "Droid-Tushare 系统诊断"
echo "========================================"

# 1. 系统信息
echo "[1] 系统信息"
echo "操作系统: $(uname -a)"
echo "内存: $(free -h | grep Mem | awk '{print $2}')"
echo "磁盘: $(df -h / | tail -1 | awk '{print $2}')"

# 2. 进程状态
echo "[2] 进程状态"
ps aux | grep -E "python|streamlit" | grep -v grep

# 3. 端口监听
echo "[3] 端口监听"
netstat -tlnp | grep -E "8501|8000|9090"

# 4. 数据库文件
echo "[4] 数据库文件"
ls -lh /opt/droid_tushare/data/*.db 2>/dev/null || echo "无数据库文件"

# 5. 日志错误
echo "[5] 最近错误日志"
grep -i "error\|exception" /opt/droid_tushare/logs/*.log | tail -20

# 6. 磁盘使用
echo "[6] 磁盘使用"
df -h /opt/droid_tushare

# 7. 网络连接
echo "[7] 网络连接"
ping -c 1 tushare.pro > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Tushare API 连接正常"
else
    echo "✗ Tushare API 连接失败"
fi

echo "========================================"
echo "诊断完成"
echo "========================================"
```

### 11.3 一键修复脚本

创建 `scripts/quick_fix.sh`：

```bash
#!/bin/bash

case "$1" in
    "reset_db")
        echo "重置数据库..."
        ./scripts/stop.sh
        rm -rf /opt/droid_tushare/data/*.db
        rm -rf /opt/droid_tushare/data/*.wal
        ./scripts/start.sh
        ;;
    "clear_cache")
        echo "清理缓存..."
        rm -rf /opt/droid_tushare/cache/*
        ;;
    "restart_services")
        echo "重启服务..."
        ./scripts/stop.sh
        sleep 5
        ./scripts/start.sh
        ;;
    "check_permissions")
        echo "修复权限..."
        chmod 750 /opt/droid_tushare
        chmod 600 /opt/droid_tushare/config/.env
        chmod 755 /opt/droid_tushare/logs
        ;;
    *)
        echo "用法: $0 {reset_db|clear_cache|restart_services|check_permissions}"
        exit 1
        ;;
esac
```

---

## 📚 获取帮助

### 社区支持

- **GitHub Issues**: https://github.com/robert/droid_tushare/issues
- **文档**: https://github.com/robert/droid_tushare/wiki
- **Discussions**: https://github.com/robert/droid_tushare/discussions

### 日志文件位置

所有日志文件位于 `/opt/droid_tushare/logs/` 目录：

- `sync_*.log` - 数据同步日志
- `vix_*.log` - VIX 计算日志
- `dashboard.log` - Dashboard 日志
- `scheduler.log` - 定时任务日志
- `error.log` - 错误日志

### 提交 Issue 时请包含

1. 错误信息和堆栈跟踪
2. 操作系统和 Python 版本
3. 相关配置文件（脱敏后）
4. 日志文件（相关部分）
5. 复现步骤

---

## 📚 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构深度解析
- [VIX_GUIDE.md](VIX_GUIDE.md) - VIX 计算模块详解
- [DEPLOYMENT.md](DEPLOYMENT.md) - 运维部署与性能优化
- [README.md](README.md) - 用户使用指南

---

**文档版本**: v1.0.0
**最后更新**: 2026-01-06
**维护者**: Robert
