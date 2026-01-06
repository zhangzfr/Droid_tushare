# 🚀 Droid-Tushare 运维部署与性能优化指南

本文档详细说明 Droid-Tushare 项目的生产环境部署、运维管理和性能优化策略。

---

## 📋 目录

- [1. 部署架构](#1-部署架构)
- [2. 环境准备](#2-环境准备)
- [3. 生产环境部署](#3-生产环境部署)
- [4. Docker 容器化](#4-docker-容器化)
- [5. 自动化任务](#5-自动化任务)
- [6. 监控与告警](#6-监控与告警)
- [7. 数据备份与恢复](#7-数据备份与恢复)
- [8. 性能优化](#8-性能优化)
- [9. 安全加固](#9-安全加固)
- [10. 常见运维任务](#10-常见运维任务)

---

## 1. 部署架构

### 1.1 推荐架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用服务器 (App Server)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Dashboard   │  │  Cron Jobs   │  │  API Server  │  │
│  │  (Streamlit) │  │  (定时任务)  │  │  (FastAPI)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层 (Storage)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  DuckDB DB   │  │  Backups     │  │  Logs        │  │
│  │  (14 files)  │  │  (rsync/S3)  │  │  (ELK)       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    监控与告警 (Monitoring)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Prometheus  │  │  Grafana     │  │  AlertMgr    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 部署方案对比

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **单机部署** | 个人研究、小团队 | 简单、成本低 | 扩展性差、单点故障 |
| **虚拟机部署** | 中小团队 | 隔离性好、灵活 | 需要运维经验 |
| **Docker 部署** | 中大型团队 | 可移植、易扩展 | 需要 Docker 知识 |
| **Kubernetes 部署** | 大型团队 | 高可用、自动扩缩容 | 复杂度高 |

### 1.3 推荐配置

#### 最小配置（个人使用）
- **CPU**: 2 核
- **内存**: 4 GB
- **存储**: 100 GB SSD
- **网络**: 10 Mbps

#### 标准配置（小团队）
- **CPU**: 4 核
- **内存**: 8 GB
- **存储**: 500 GB SSD
- **网络**: 100 Mbps

#### 生产配置（中大型团队）
- **CPU**: 8 核
- **内存**: 16 GB
- **存储**: 2 TB SSD + 5 TB HDD（备份）
- **网络**: 1 Gbps
- **备份**: 异地备份

---

## 2. 环境准备

### 2.1 操作系统要求

**推荐**：
- Ubuntu 20.04 LTS 或更高版本
- CentOS 7 或更高版本
- macOS 10.15 或更高版本（仅限开发）

**不推荐**：
- Windows（需要 WSL）

### 2.2 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.8 \
    python3-pip \
    git \
    curl \
    wget \
    vim \
    htop \
    tmux

# CentOS/RHEL
sudo yum update
sudo yum install -y \
    python38 \
    python38-pip \
    git \
    curl \
    wget \
    vim \
    htop \
    tmux
```

### 2.3 Python 环境

```bash
# 创建虚拟环境
python3 -m venv venv_droid

# 激活虚拟环境
source venv_droid/bin/activate  # Linux/macOS
# venv_droid\Scripts\activate  # Windows

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 2.4 环境变量配置

创建 `.env` 文件：

```bash
# Tushare API Token
TUSHARE_TOKEN=your_token_here

# 数据库根目录
DB_ROOT=/path/to/your/database

# 日志级别（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO

# 调试模式（true/false）
DEBUG=false

# 端口配置
DASHBOARD_PORT=8501
API_PORT=8000

# 备份配置
BACKUP_ENABLED=true
BACKUP_DIR=/path/to/backup
BACKUP_SCHEDULE="0 2 * * *"  # 每天凌晨 2 点

# 监控配置
MONITORING_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

加载环境变量：

```bash
# 方法 1：使用 python-dotenv
python -c "from dotenv import load_dotenv; load_dotenv()"

# 方法 2：手动 source
export $(cat .env | xargs)
```

---

## 3. 生产环境部署

### 3.1 目录结构

```
/opt/droid_tushare/
├── app/                    # 应用代码
│   ├── src/
│   ├── dashboard/
│   ├── utils/
│   └── docs/
├── data/                   # 数据库文件
│   ├── tushare_duck_stock.db
│   ├── tushare_duck_index.db
│   └── ...
├── logs/                   # 日志文件
│   ├── app.log
│   ├── sync.log
│   └── error.log
├── backups/                # 备份文件
│   ├── daily/
│   ├── weekly/
│   └── monthly/
├── cache/                  # 缓存文件
│   ├── vix/
│   └── dashboard/
├── scripts/                # 运维脚本
│   ├── start.sh
│   ├── stop.sh
│   ├── backup.sh
│   └── monitor.sh
├── config/                 # 配置文件
│   ├── settings.yaml
│   └── .env
└── venv/                   # Python 虚拟环境
```

创建目录结构：

```bash
#!/bin/bash

# 创建目录结构
BASE_DIR="/opt/droid_tushare"
mkdir -p ${BASE_DIR}/{data,logs,backups/{daily,weekly,monthly},cache/{vix,dashboard},scripts,config,venv}

# 设置权限
chmod 750 ${BASE_DIR}
chmod 750 ${BASE_DIR}/logs
chmod 750 ${BASE_DIR}/backups
chmod 755 ${BASE_DIR}/cache

echo "目录结构创建完成！"
```

### 3.2 应用部署

#### 3.2.1 部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash

set -e

# 配置
APP_DIR="/opt/droid_tushare"
VENV_DIR="${APP_DIR}/venv"
REPO_URL="https://github.com/robert/droid_tushare.git"
BRANCH="main"

echo "======================================"
echo "开始部署 Droid-Tushare"
echo "======================================"

# 1. 停止服务
echo "[1/6] 停止现有服务..."
./scripts/stop.sh || true

# 2. 备份当前版本
echo "[2/6] 备份当前版本..."
BACKUP_DIR="${APP_DIR}/backups/deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p ${BACKUP_DIR}
cp -r ${APP_DIR}/app ${BACKUP_DIR}/
cp -r ${APP_DIR}/config ${BACKUP_DIR}/
echo "备份完成: ${BACKUP_DIR}"

# 3. 拉取最新代码
echo "[3/6] 拉取最新代码..."
if [ ! -d "${APP_DIR}/app" ]; then
    git clone ${REPO_URL} -b ${BRANCH} ${APP_DIR}/app
else
    cd ${APP_DIR}/app
    git fetch origin
    git checkout ${BRANCH}
    git pull origin ${BRANCH}
fi

# 4. 更新依赖
echo "[4/6] 更新 Python 依赖..."
source ${VENV_DIR}/bin/activate
pip install --upgrade -r ${APP_DIR}/app/requirements.txt

# 5. 数据库迁移（如果需要）
echo "[5/6] 检查数据库结构..."
# python scripts/migrate_db.py

# 6. 启动服务
echo "[6/6] 启动服务..."
./scripts/start.sh

echo "======================================"
echo "部署完成！"
echo "======================================"
```

#### 3.2.2 启动脚本

创建 `scripts/start.sh`：

```bash
#!/bin/bash

set -e

APP_DIR="/opt/droid_tushare"
VENV_DIR="${APP_DIR}/venv"
PID_FILE="${APP_DIR}/app.pid"

# 检查是否已经运行
if [ -f "${PID_FILE}" ]; then
    PID=$(cat ${PID_FILE})
    if ps -p ${PID} > /dev/null; then
        echo "服务已经在运行 (PID: ${PID})"
        exit 1
    else
        rm ${PID_FILE}
    fi
fi

# 激活虚拟环境
source ${VENV_DIR}/bin/activate

# 启动 Dashboard
echo "启动 Dashboard..."
cd ${APP_DIR}/app
nohup streamlit run dashboard/app.py \
    --server.port=${DASHBOARD_PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    > ${APP_DIR}/logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!

# 启动数据同步任务（可选）
# echo "启动数据同步..."
# nohup python -m src.tushare_duckdb.main \
#     > ${APP_DIR}/logs/sync.log 2>&1 &
# SYNC_PID=$!

# 保存 PID
echo ${DASHBOARD_PID} > ${PID_FILE}

echo "服务启动成功！"
echo "Dashboard PID: ${DASHBOARD_PID}"
echo "Dashboard URL: http://localhost:${DASHBOARD_PORT:-8501}"
```

#### 3.2.3 停止脚本

创建 `scripts/stop.sh`：

```bash
#!/bin/bash

APP_DIR="/opt/droid_tushare"
PID_FILE="${APP_DIR}/app.pid"

if [ ! -f "${PID_FILE}" ]; then
    echo "服务未运行"
    exit 0
fi

PID=$(cat ${PID_FILE})

echo "停止服务 (PID: ${PID})..."
kill ${PID}

# 等待进程结束
for i in {1..30}; do
    if ! ps -p ${PID} > /dev/null; then
        echo "服务已停止"
        rm ${PID_FILE}
        exit 0
    fi
    sleep 1
done

# 强制杀死
echo "强制杀死服务..."
kill -9 ${PID}
rm ${PID_FILE}
echo "服务已强制停止"
```

### 3.3 服务注册（systemd）

创建 `/etc/systemd/system/droid-tushare.service`：

```ini
[Unit]
Description=Droid-Tushare Data Service
After=network.target

[Service]
Type=simple
User=robert
WorkingDirectory=/opt/droid_tushare/app
Environment="PATH=/opt/droid_tushare/venv/bin"
EnvironmentFile=/opt/droid_tushare/config/.env
ExecStart=/opt/droid_tushare/venv/bin/streamlit run dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

注册并启动服务：

```bash
# 注册服务
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable droid-tushare.service

# 启动服务
sudo systemctl start droid-tushare.service

# 查看状态
sudo systemctl status droid-tushare.service

# 查看日志
sudo journalctl -u droid-tushare.service -f
```

---

## 4. Docker 容器化

### 4.1 Dockerfile

创建 `Dockerfile`：

```dockerfile
# 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/logs /app/cache

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DB_ROOT=/app/data

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
```

### 4.2 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: droid-tushare
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./cache:/app/cache
      - ./config:/app/config
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  backup:
    image: alpine:latest
    container_name: droid-backup
    volumes:
      - ./data:/data:ro
      - ./backups:/backups
    environment:
      - CRON_SCHEDULE="0 2 * * *"
    command: >
      sh -c "
        apk add --no-cache rsync &&
        echo '$$CRON_SCHEDULE rsync -av --delete /data/ /backups/daily/$(date +%Y%m%d)/' | crontab - &&
        crond -f -l 2
      "
    restart: unless-stopped

  monitor:
    image: prom/prometheus:latest
    container_name: droid-monitor
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: droid-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

### 4.3 Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down

# 重启服务
docker-compose restart app
```

### 4.4 Docker 最佳实践

**镜像优化**：
```dockerfile
# 多阶段构建
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.9-slim
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["streamlit", "run", "dashboard/app.py"]
```

**安全加固**：
```dockerfile
# 使用非 root 用户
RUN useradd -m -u 1000 appuser
USER appuser
```

**资源限制**：
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 5. 自动化任务

### 5.1 Cron 任务配置

#### 5.1.1 数据同步任务

创建 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加任务
# 每天凌晨 2 点同步股票日线数据
0 2 * * * cd /opt/droid_tushare/app && /opt/droid_tushare/venv/bin/python -m src.tushare_duckdb.main >> /opt/droid_tushare/logs/sync_stock.log 2>&1

# 每天凌晨 3 点同步指数数据
0 3 * * * cd /opt/droid_tushare/app && /opt/droid_tushare/venv/bin/python -m src.tushare_duckdb.main >> /opt/droid_tushare/logs/sync_index.log 2>&1

# 每周日凌晨 4 点同步 VIX 数据
0 4 * * 0 cd /opt/droid_tushare/app && /opt/droid_tushare/venv/bin/python -m src.vix.run --start_date $(date -d '7 days ago' +\%Y\%m\%d) --end_date $(date +\%Y\%m\%d) >> /opt/droid_tushare/logs/sync_vix.log 2>&1
```

#### 5.1.2 使用 Python APScheduler

创建 `scripts/scheduler.py`：

```python
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import sys
import os

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/droid_tushare/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def sync_stock_data():
    """同步股票日线数据"""
    logger.info("开始同步股票数据...")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'src.tushare_duckdb.main'],
            cwd='/opt/droid_tushare/app',
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("股票数据同步成功")
        else:
            logger.error(f"股票数据同步失败: {result.stderr}")
    except Exception as e:
        logger.error(f"股票数据同步异常: {e}")

def sync_vix_data():
    """同步 VIX 数据"""
    logger.info("开始同步 VIX 数据...")
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'src.vix.run',
             '--start_date', start_date,
             '--end_date', end_date],
            cwd='/opt/droid_tushare/app',
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("VIX 数据同步成功")
        else:
            logger.error(f"VIX 数据同步失败: {result.stderr}")
    except Exception as e:
        logger.error(f"VIX 数据同步异常: {e}")

def cleanup_old_logs():
    """清理 30 天前的日志"""
    logger.info("开始清理旧日志...")
    try:
        import glob
        import time

        log_dir = '/opt/droid_tushare/logs'
        cutoff = time.time() - (30 * 86400)  # 30 天

        for log_file in glob.glob(f'{log_dir}/*.log'):
            if os.path.getmtime(log_file) < cutoff:
                os.remove(log_file)
                logger.info(f"删除旧日志: {log_file}")

        logger.info("日志清理完成")
    except Exception as e:
        logger.error(f"日志清理异常: {e}")

def main():
    scheduler = BlockingScheduler()

    # 每天凌晨 2 点同步股票数据
    scheduler.add_job(
        sync_stock_data,
        'cron',
        hour=2,
        minute=0,
        id='sync_stock'
    )

    # 每天凌晨 3 点同步指数数据
    scheduler.add_job(
        sync_index_data,
        'cron',
        hour=3,
        minute=0,
        id='sync_index'
    )

    # 每周日凌晨 4 点同步 VIX 数据
    scheduler.add_job(
        sync_vix_data,
        'cron',
        day_of_week='sun',
        hour=4,
        minute=0,
        id='sync_vix'
    )

    # 每天凌晨 5 点清理旧日志
    scheduler.add_job(
        cleanup_old_logs,
        'cron',
        hour=5,
        minute=0,
        id='cleanup_logs'
    )

    logger.info("调度器启动，等待任务...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器停止")

if __name__ == '__main__':
    main()
```

注册为 systemd 服务：

```ini
[Unit]
Description=Droid-Tushare Scheduler
After=network.target

[Service]
Type=simple
User=robert
WorkingDirectory=/opt/droid_tushare/app
Environment="PATH=/opt/droid_tushare/venv/bin"
EnvironmentFile=/opt/droid_tushare/config/.env
ExecStart=/opt/droid_tushare/venv/bin/python scripts/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 6. 监控与告警

### 6.1 Prometheus 监控

创建 `config/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'droid-tushare'
    static_configs:
      - targets: ['localhost:8501']
    metrics_path: '/_stcore/health'
```

### 6.2 自定义指标

创建 `metrics.py`：

```python
from prometheus_client import start_http_server, Gauge, Counter
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

# 定义指标
db_size = Gauge('duckdb_size_bytes', 'DuckDB database size')
record_count = Gauge('duckdb_record_count', 'DuckDB record count', ['table'])
sync_duration = Gauge('sync_duration_seconds', 'Sync duration', ['category'])
sync_errors = Counter('sync_errors_total', 'Sync errors', ['category', 'table'])

def update_metrics():
    """更新监控指标"""
    DB_ROOT = os.getenv('DB_ROOT', '/opt/droid_tushare/data')

    # 更新数据库大小
    for db_file in os.listdir(DB_ROOT):
        if db_file.endswith('.db'):
            db_path = os.path.join(DB_ROOT, db_file)
            db_size.set(os.path.getsize(db_path))

    # 更新记录数
    conn = duckdb.connect(db_path)
    tables = conn.execute("SHOW TABLES").fetchdf()
    for table in tables['name']:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        record_count.labels(table=table).set(count)
    conn.close()

if __name__ == '__main__':
    # 启动 metrics HTTP 服务器
    start_http_server(9091)

    # 定期更新指标
    import time
    while True:
        update_metrics()
        time.sleep(60)
```

### 6.3 Grafana 仪表盘

创建 `config/grafana/dashboards/dashboard.yml`：

```yaml
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

### 6.4 告警规则

创建 `config/prometheus/alerts.yml`：

```yaml
groups:
  - name: droid_tushare
    rules:
      - alert: DatabaseSizeHigh
        expr: duckdb_size_bytes > 100 * 1024 * 1024 * 1024  # 100 GB
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database size is high"
          description: "Database {{ $labels.instance }} is {{ $value }} bytes"

      - alert: SyncErrorRateHigh
        expr: rate(sync_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Sync error rate is high"
          description: "Sync error rate is {{ $value }}/s"

      - alert: SyncDurationHigh
        expr: sync_duration_seconds > 3600  # 1 小时
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Sync duration is high"
          description: "Sync took {{ $value }} seconds"
```

### 6.5 日志管理

#### 6.5.1 日志轮转

创建 `/etc/logrotate.d/droid-tushare`：

```
/opt/droid_tushare/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 robert robert
    sharedscripts
    postrotate
        # 可选：重启应用
        # systemctl restart droid-tushare
    endscript
}
```

#### 6.5.2 ELK Stack 集成

创建 `config/filebeat.yml`：

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/droid_tushare/logs/*.log
  fields:
    app: droid-tushare
  fields_under_root: true
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

output.elasticsearch:
  hosts: ["localhost:9200"]
  indices:
    - index: "droid-tushare-%{+yyyy.MM.dd}"

setup.kibana:
  host: "localhost:5601"
```

---

## 7. 数据备份与恢复

### 7.1 备份策略

#### 7.1.1 全量备份脚本

创建 `scripts/backup_full.sh`：

```bash
#!/bin/bash

set -e

# 配置
APP_DIR="/opt/droid_tushare"
BACKUP_DIR="${APP_DIR}/backups/full"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="droid_tushare_full_${DATE}.tar.gz"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

echo "开始全量备份..."

# 打包所有数据
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} \
    -C ${APP_DIR} \
    data \
    config \
    --exclude='data/*.db-wal' \
    --exclude='data/*.db-shm'

echo "全量备份完成: ${BACKUP_DIR}/${BACKUP_FILE}"

# 清理 30 天前的备份
find ${BACKUP_DIR} -name "droid_tushare_full_*.tar.gz" -mtime +30 -delete

echo "旧备份清理完成"
```

#### 7.1.2 增量备份脚本

创建 `scripts/backup_incremental.sh`：

```bash
#!/bin/bash

set -e

APP_DIR="/opt/droid_tushare"
BACKUP_DIR="${APP_DIR}/backups/incremental"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p ${BACKUP_DIR}

echo "开始增量备份..."

# 使用 rsync 增量备份
rsync -av --delete \
    ${APP_DIR}/data/ \
    ${BACKUP_DIR}/${DATE}/

echo "增量备份完成: ${BACKUP_DIR}/${DATE}"

# 创建快照清单
ls -la ${BACKUP_DIR}/${DATE}/ > ${BACKUP_DIR}/snapshot_${DATE}.txt

# 清理 7 天前的增量备份
find ${BACKUP_DIR} -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```

#### 7.1.3 云端备份脚本

创建 `scripts/backup_s3.sh`：

```bash
#!/bin/bash

set -e

# 配置
APP_DIR="/opt/droid_tushare"
S3_BUCKET="s3://your-bucket/droid-tushare"
DATE=$(date +%Y%m%d_%H%M%S)

# 全量备份
echo "开始云端备份..."
tar -czf - ${APP_DIR}/data | aws s3 cp - ${S3_BUCKET}/full_${DATE}.tar.gz

# 元数据备份
aws s3 cp ${APP_DIR}/config/.env ${S3_BUCKET}/config/.env
aws s3 cp ${APP_DIR}/config/settings.yaml ${S3_BUCKET}/config/settings.yaml

echo "云端备份完成"
```

### 7.2 恢复策略

#### 7.2.1 全量恢复

```bash
#!/bin/bash

set -e

APP_DIR="/opt/droid_tushare"
BACKUP_FILE=$1

if [ -z "${BACKUP_FILE}" ]; then
    echo "用法: $0 <backup_file>"
    exit 1
fi

echo "开始恢复备份: ${BACKUP_FILE}"

# 停止服务
./scripts/stop.sh

# 解压备份
tar -xzf ${BACKUP_FILE} -C ${APP_DIR}

# 恢复数据库
# duckdb 连接时会自动恢复 WAL 文件

# 重启服务
./scripts/start.sh

echo "恢复完成"
```

#### 7.2.2 单表恢复

```python
import duckdb
import os

def restore_table_from_backup(
    db_path: str,
    table_name: str,
    backup_path: str
):
    """
    从备份恢复单个表

    Args:
        db_path: 数据库路径
        table_name: 表名
        backup_path: 备份文件路径
    """
    # 连接备份数据库
    backup_conn = duckdb.connect(backup_path)
    df = backup_conn.execute(f"SELECT * FROM {table_name}").fetchdf()
    backup_conn.close()

    # 连接目标数据库
    conn = duckdb.connect(db_path)

    # 删除旧表
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    # 创建新表并插入数据
    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

    conn.close()
    print(f"表 {table_name} 恢复完成")

# 使用
restore_table_from_backup(
    db_path='/opt/droid_tushare/data/tushare_duck_stock.db',
    table_name='daily',
    backup_path='/opt/droid_tushare/backups/20240101_120000/tushare_duck_stock.db'
)
```

### 7.3 备份计划

| 类型 | 频率 | 保留期 | 存储位置 |
|------|------|--------|---------|
| **增量备份** | 每天凌晨 3 点 | 7 天 | 本地 |
| **全量备份** | 每周日凌晨 4 点 | 30 天 | 本地 |
| **云端备份** | 每天凌晨 5 点 | 90 天 | S3/OSS |

---

## 8. 性能优化

### 8.1 数据库优化

#### 8.1.1 DuckDB 优化

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# 设置优化参数
conn.execute("PRAGMA threads=8")  # 使用 8 个线程
conn.execute("PRAGMA memory_limit='4GB'")  # 设置内存限制
conn.execute("PRAGMA enable_progress_bar=false")  # 关闭进度条

# 创建索引（对查询频繁的列）
conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_trade_date ON daily(trade_date)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_ts_code ON daily(ts_code)")

# 检查查询计划
plan = conn.explain("SELECT * FROM daily WHERE ts_code='000001.SZ'")
print(plan)

conn.close()
```

#### 8.1.2 分区策略

虽然 DuckDB 不支持传统的分区，但可以通过以下方式优化：

```python
# 按年度分表
for year in range(2010, 2025):
    conn.execute(f"""
        CREATE TABLE daily_{year} AS
        SELECT * FROM daily
        WHERE trade_date BETWEEN '{year}0101' AND '{year}1231'
    """)

# 查询时自动路由
year = date_str[:4]
result = conn.execute(f"SELECT * FROM daily_{year} WHERE ...").fetchdf()
```

### 8.2 应用层优化

#### 8.2.1 连接池

```python
import duckdb
from contextlib import contextmanager

class DuckDBConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = []
        self.used_connections = 0

    def get_connection(self):
        if len(self.connections) < self.pool_size:
            conn = duckdb.connect(self.db_path)
            self.connections.append(conn)
            return conn
        else:
            # 轮询使用
            conn = self.connections[self.used_connections % self.pool_size]
            self.used_connections += 1
            return conn

    def close_all(self):
        for conn in self.connections:
            conn.close()
        self.connections = []

# 使用
pool = DuckDBConnectionPool('tushare_duck_stock.db', pool_size=5)

with pool.get_connection() as conn:
    result = conn.execute("SELECT * FROM daily").fetchdf()
```

#### 8.2.2 批量查询优化

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# ❌ 不好：循环查询
for ts_code in ts_codes:
    result = conn.execute(f"""
        SELECT * FROM daily
        WHERE ts_code='{ts_code}'
        AND trade_date='{date}'
    """).fetchdf()

# ✅ 好：批量查询
ts_code_list = "','".join(ts_codes)
result = conn.execute(f"""
    SELECT * FROM daily
    WHERE ts_code IN ('{ts_code_list}')
    AND trade_date='{date}'
""").fetchdf()
```

### 8.3 Dashboard 优化

#### 8.3.1 数据预加载

```python
import streamlit as st
from functools import lru_cache

@st.cache_data(ttl=3600)  # 缓存 1 小时
def load_data():
    # 数据加载逻辑
    pass

# 在页面顶部加载数据
if 'data' not in st.session_state:
    st.session_state.data = load_data()
```

#### 8.3.2 懒加载

```python
import streamlit as st

# 只在需要时加载数据
if st.button('加载数据'):
    data = load_expensive_data()
    st.dataframe(data)
```

#### 8.3.3 使用列式格式

```python
import pandas as pd

# 读取数据时使用更高效的格式
df = pd.read_parquet('data.parquet')  # 比 CSV 快 10-100 倍

# 写入数据
df.to_parquet('data.parquet')
```

### 8.4 系统级优化

#### 8.4.1 CPU 绑定

```bash
# 绑定进程到特定 CPU 核心
taskset -c 0-3 streamlit run dashboard/app.py
```

#### 8.4.2 内存锁定

```python
import duckdb

# 锁定内存，防止被 swap
conn = duckdb.connect('tushare_duck_stock.db', read_only=False)
conn.execute("PRAGMA lock_memory=true")
```

#### 8.4.3 I/O 优化

```bash
# 调整 I/O 调度器
ionice -c 2 -n 7 python -m src.tushare_duckdb.main
```

---

## 9. 安全加固

### 9.1 文件权限

```bash
# 设置正确的文件权限
chmod 750 /opt/droid_tushare
chmod 600 /opt/droid_tushare/config/.env
chmod 644 /opt/droid_tushare/config/settings.yaml
chmod 755 /opt/droid_tushare/logs
chmod 640 /opt/droid_tushare/logs/*.log
chmod 700 /opt/droid_tushare/backups
```

### 9.2 网络安全

#### 9.2.1 防火墙配置

```bash
# 使用 ufw
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8501/tcp  # Dashboard
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw allow 3000/tcp  # Grafana
sudo ufw enable
```

#### 9.2.2 SSL/TLS

使用 Nginx 反向代理并启用 HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 9.3 访问控制

#### 9.3.1 基本认证

```nginx
# Nginx 基本认证
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://localhost:8501;
}
```

创建密码文件：

```bash
sudo htpasswd -c /etc/nginx/.htpasswd username
```

#### 9.3.2 IP 白名单

```nginx
# 只允许特定 IP 访问
location / {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;

    proxy_pass http://localhost:8501;
}
```

### 9.4 审计日志

```python
import logging
from functools import wraps

# 配置审计日志
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('/opt/droid_tushare/logs/audit.log')
audit_handler.setLevel(logging.INFO)
audit_logger.addHandler(audit_handler)

def audit_log(func):
    """审计日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        audit_logger.info(f"Function {func.__name__} called with args={args}, kwargs={kwargs}")
        return func(*args, **kwargs)
    return wrapper

# 使用
@audit_log
def sync_data(category, table):
    # 业务逻辑
    pass
```

---

## 10. 常见运维任务

### 10.1 数据库维护

#### 10.1.1 VACUUM 操作

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# VACUUM 回收空间
conn.execute("VACUUM")

# ANALYZE 更新统计信息
conn.execute("ANALYZE")

conn.close()
```

#### 10.1.2 检查数据库完整性

```python
import duckdb

conn = duckdb.connect('tushare_duck_stock.db')

# 检查数据库
result = conn.execute("PRAGMA database_size").fetchdf()
print(result)

# 检查表
tables = conn.execute("SHOW TABLES").fetchdf()
print(tables)

# 检查列
for table in tables['name']:
    columns = conn.execute(f"PRAGMA table_info({table})").fetchdf()
    print(f"\n{table}:\n{columns}")

conn.close()
```

### 10.2 性能诊断

#### 10.2.1 慢查询分析

```python
import duckdb
import time

conn = duckdb.connect('tushare_duck_stock.db')

# 记录查询时间
start = time.time()
result = conn.execute("""
    SELECT * FROM daily
    WHERE trade_date BETWEEN '20240101' AND '20241231'
""").fetchdf()
elapsed = time.time() - start

print(f"查询耗时: {elapsed:.2f} 秒")
print(f"返回记录数: {len(result)}")

# 使用 EXPLAIN ANALYZE
plan = conn.execute("EXPLAIN ANALYZE SELECT * FROM daily WHERE ts_code='000001.SZ'").fetchdf()
print(plan)

conn.close()
```

#### 10.2.2 资源使用监控

```bash
# CPU 使用
top -p $(pgrep streamlit)

# 内存使用
ps aux | grep streamlit

# 磁盘使用
df -h /opt/droid_tushare/data

# 网络使用
iftop -i eth0
```

### 10.3 故障恢复

#### 10.3.1 数据库损坏恢复

```bash
# 1. 停止服务
./scripts/stop.sh

# 2. 备份损坏的文件
cp tushare_duck_stock.db tushare_duck_stock.db.corrupted

# 3. 从 WAL 文件恢复
duckdb tushare_duck_stock.db -readonly -c "PRAGMA integrity_check;"

# 4. 如果无法恢复，从备份恢复
./scripts/restore_backup.sh backups/full/20240101_120000.tar.gz

# 5. 重启服务
./scripts/start.sh
```

#### 10.3.2 服务重启策略

```bash
# 优雅重启（平滑切换）
./scripts/restart_smooth.sh

# 快速重启（会中断连接）
./scripts/restart_fast.sh

# 滚动重启（多实例）
./scripts/restart_rolling.sh
```

创建 `scripts/restart_smooth.sh`：

```bash
#!/bin/bash

# 先启动新实例
nohup streamlit run dashboard/app.py --server.port=8502 > /dev/null 2>&1 &
NEW_PID=$!

# 等待新实例启动
sleep 10

# 切换流量（使用 Nginx）
# nginx -s reload

# 停止旧实例
./scripts/stop.sh

echo "平滑重启完成"
```

### 10.4 容量规划

#### 10.4.1 存储容量评估

```python
import duckdb
import os

def estimate_storage_growth():
    """评估存储增长趋势"""
    db_dir = '/opt/droid_tushare/data'

    total_size = 0
    for db_file in os.listdir(db_dir):
        if db_file.endswith('.db'):
            path = os.path.join(db_dir, db_file)
            size = os.path.getsize(path)
            total_size += size
            print(f"{db_file}: {size / (1024**3):.2f} GB")

    print(f"\n总大小: {total_size / (1024**3):.2f} GB")

    # 预估未来 3 个月增长
    daily_growth = 100 * 1024 * 1024  # 假设每天增长 100 MB
    days = 90
    estimated_growth = daily_growth * days
    future_size = total_size + estimated_growth

    print(f"\n预估 90 天后大小: {future_size / (1024**3):.2f} GB")
    print(f"需要额外空间: {estimated_growth / (1024**3):.2f} GB")

estimate_storage_growth()
```

---

## 📚 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构深度解析
- [VIX_GUIDE.md](VIX_GUIDE.md) - VIX 计算模块详解
- [README.md](README.md) - 用户使用指南
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除百科

---

**文档版本**: v1.0.0
**最后更新**: 2026-01-06
**维护者**: Robert
