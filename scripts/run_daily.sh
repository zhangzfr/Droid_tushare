#!/bin/bash
# ============================================================================
# Tushare 日频数据自动更新脚本 (Shell Wrapper)
# ============================================================================
#
# 用法:
#   ./run_daily.sh                      # 获取最近交易日的所有日频数据
#   ./run_daily.sh --date 20260110      # 获取指定日期
#   ./run_daily.sh --dry-run            # 模拟运行
#   ./run_daily.sh --list-categories    # 显示可用类别
#
# 定时任务示例 (crontab -e):
#   # 每个工作日18:00运行
#   0 18 * * 1-5 /path/to/run_daily.sh >> /path/to/logs/daily_fetch.log 2>&1
#
# ============================================================================

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 日志文件 (按日期)
LOG_FILE="$LOG_DIR/daily_fetch_$(date +%Y%m%d_%H%M%S).log"

# 切换到项目目录
cd "$PROJECT_ROOT" || exit 1

echo "============================================================" | tee -a "$LOG_FILE"
echo "  Tushare 日频数据更新开始" | tee -a "$LOG_FILE"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "  日志: $LOG_FILE" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3" | tee -a "$LOG_FILE"
    exit 1
fi

# 执行 Python 脚本，传递所有参数
python3 -m scripts.daily_fetcher "$@" 2>&1 | tee -a "$LOG_FILE"
STATUS=$?

echo "" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "  执行完成, 退出码: $STATUS" | tee -a "$LOG_FILE"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

exit $STATUS
