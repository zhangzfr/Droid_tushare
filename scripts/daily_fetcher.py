#!/usr/bin/env python3
"""
Daily Tushare Data Fetcher (每日数据自动更新脚本)

用于自动获取所有日频更新的 Tushare 数据表。
- 仅包含日频数据，排除月频、季频、快照类数据
- 支持命令行参数控制
- 连续服务器错误时中断，单表失败时继续

Usage:
    python -m scripts.daily_fetcher [--date YYYYMMDD] [--categories cat1,cat2] [--dry-run]

Examples:
    # 获取最近交易日的所有日频数据
    python -m scripts.daily_fetcher

    # 获取指定日期的数据
    python -m scripts.daily_fetcher --date 20260110

    # 仅获取股票和指数数据
    python -m scripts.daily_fetcher --categories stock,index

    # 模拟运行（不实际获取）
    python -m scripts.daily_fetcher --dry-run
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tushare_duckdb.config import API_CONFIG, BASIC_DB_PATH
from src.tushare_duckdb.utils import get_connection
from src.tushare_duckdb.main import fetch_and_store_data
from src.tushare_duckdb.logger import logger

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


def get_daily_counts(db_path: str, table_name: str, date_column: str, 
                     days: int = 30) -> dict:
    """
    获取表中过去N天的每日数据量统计。
    
    Args:
        db_path: 数据库路径
        table_name: 表名
        date_column: 日期列名
        days: 统计天数
        
    Returns:
        dict: {日期: 数量} 的有序字典
    """
    try:
        with get_connection(db_path, read_only=True) as conn:
            # 检查表是否存在
            result = conn.execute("""
                SELECT count(*) FROM information_schema.tables 
                WHERE table_name = ?
            """, [table_name]).fetchone()
            
            if not result or result[0] == 0:
                return {}
            
            # 获取表中最大日期
            max_date_result = conn.execute(f"""
                SELECT MAX({date_column}) FROM {table_name}
            """).fetchone()
            
            if not max_date_result or not max_date_result[0]:
                return {}
            
            max_date = str(max_date_result[0])
            
            # 计算开始日期
            max_dt = datetime.strptime(max_date, '%Y%m%d')
            start_dt = max_dt - timedelta(days=days)
            start_date = start_dt.strftime('%Y%m%d')
            
            # 获取日期范围内的每日数据量
            result = conn.execute(f"""
                SELECT {date_column} as date, COUNT(*) as cnt
                FROM {table_name}
                WHERE {date_column} >= '{start_date}'
                GROUP BY {date_column}
                ORDER BY {date_column} DESC
            """).fetchall()
            
            return {str(row[0]): row[1] for row in result}
    except Exception as e:
        logger.debug(f"获取 {table_name} 每日统计失败: {e}")
        return {}


def print_comparison_table(before: dict, after: dict, table_name: str, date_column: str):
    """
    打印前后对比表格
    
    Args:
        before: 获取前的每日统计
        after: 获取后的每日统计
        table_name: 表名
        date_column: 日期列
    """
    # 合并所有日期
    all_dates = sorted(set(before.keys()) | set(after.keys()), reverse=True)
    
    if not all_dates:
        logger.info(f"    {table_name}: 无数据")
        return
    
    # 构建对比数据
    rows = []
    total_diff = 0
    for date in all_dates[:15]:  # 最多显示15天
        before_cnt = before.get(date, 0)
        after_cnt = after.get(date, 0)
        diff = after_cnt - before_cnt
        total_diff += diff
        
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "-"
        rows.append([date, before_cnt, after_cnt, diff_str])
    
    if HAS_TABULATE:
        headers = ['日期', '获取前', '获取后', '变化']
        table_str = tabulate(rows, headers=headers, tablefmt='simple', numalign='right')
        for line in table_str.split('\n'):
            logger.info(f"    {line}")
    else:
        logger.info(f"    {'日期':<12} {'获取前':>8} {'获取后':>8} {'变化':>6}")
        for row in rows:
            logger.info(f"    {row[0]:<12} {row[1]:>8} {row[2]:>8} {row[3]:>6}")
    
    if total_diff != 0:
        logger.info(f"    总计变化: +{total_diff}" if total_diff > 0 else f"    总计变化: {total_diff}")


# ==================== 日频数据表配置 ====================
# 根据 settings.yaml 分析，排除以下非日频表：
# - 快照表 (requires_date: false)
# - 月频表 (api_date_format: YYYYMM): cn_pmi, cn_m, sf_month, cn_cpi, cn_ppi
# - 季频表 (api_date_format: YYYYQN): cn_gdp
# - 财务数据 (finance category): 全部为季度报告
# - 用户指定排除: trade_cal, slb_*, index_weight

DAILY_TABLES = {
    'stock': [
        'daily',              # 股票日线行情
        'adj_factor',         # 复权因子
        'daily_basic',        # 每日指标
        'stk_limit',          # 涨跌停价格
        'suspend_d',          # 停复牌信息
        'bak_basic',          # 股票历史列表
        'bak_daily'           # 备用行情
    ],
    
    'margin': [
        'margin',             # 融资融券交易汇总
        'margin_detail',      # 融资融券交易明细
        'margin_secs',        # 融资融券标的
        # 排除: slb_len, slb_len_mm, slb_sec, slb_sec_detail (已停止更新)
    ],
    
    'moneyflow': [
        'moneyflow',          # 个股资金流向
        'moneyflow_ths',      # 同花顺个股资金流
        'moneyflow_dc',       # 东财个股资金流
        'moneyflow_ind_ths',  # 同花顺行业资金流
        'moneyflow_ind_dc',   # 东财行业资金流
        'moneyflow_mkt_dc',   # 东财大盘资金流
        'moneyflow_cnt_ths',  # 同花顺概念资金流
        'moneyflow_hsgt',     # 沪深港通资金流向
    ],
    
    'index': [
        'index_daily',        # 指数日线行情
        'index_dailybasic',   # 指数每日指标
        'daily_info',         # 上交所每日统计
        'sz_daily_info',      # 深交所每日统计
        'ths_daily',          # 同花顺概念指数日线
        'dc_daily',           # 东财概念指数日线
        'ci_daily',           # 中信行业指数日线
        'sw_daily',           # 申万行业指数日线
        'tdx_daily',          # 通达信行业指数日线
        'index_global',       # 国际指数日线
        'dc_index',
        'tdx_index',
        'dc_member',
        'tdx_member',
    ],
    
    # 排除: index_member (index_weight 改为月度维护)
    
    'fund': [
        'fund_nav',           # 公募基金净值
        'fund_daily',         # 场内基金日线行情
        'fund_adj',           # 基金复权因子
        'etf_share_size',     # ETF份额规模
        # 排除: fund_portfolio (季度持仓数据)
    ],
    
    'bond': [
        'cb_share',           # 可转债转股结果
        'cb_daily',           # 可转债日线行情
        'bond_blk',           # 债券大宗交易
        'bond_blk_detail',    # 债券大宗明细
        'repo_daily',         # 回购日报
        'yc_cb',              # 可转债收益率曲线
    ],
    
    'option': [
        'opt_basic',          # 期权基础信息
        'opt_daily',          # 期权日线行情
    ],
    
    'future': [
        'fut_daily',          # 期货日线行情
        'fut_wsr',            # 仓单日报
        'fut_settle',         # 结算参数
        'fut_holding',        # 持仓排名
        'fut_index_daily',    # 南华期货指数日线
    ],
    
    'reference': [
        'block_trade',        # 大宗交易
    ],
    
    'macro': [
        'shibor',             # 上海银行间同业拆放利率
        'shibor_quote',       # SHIBOR报价数据
        'us_tycr',            # 美国国债收益率
        'us_trycr',           # 美国实际利率
        'us_tltr',            # 美国长期利率
        'us_trltr',           # 美国实际长期利率
        'us_tbr',             # 美国短期利率
    ],
    
    'fx': [
        'fx_daily',           # 外汇日线行情
    ],
    
    'commodity': [
        'sge_daily',          # 上金所日线行情
    ],
}

# 排除的类别 (全部为非日频数据)
EXCLUDED_CATEGORIES = [
    'finance',        # 财务数据全部为季频
    'stock_events',   # trade_cal 年度更新, 其他为快照
    'index_basic',    # 快照/成员表
    'index_member',   # index_weight 改为月度维护
]

# 数据延迟发布的表（需要额外回溯几天确保完整性）
# 这些表的数据可能分多天发布，单纯查询 max_date 可能数据不完整
DELAYED_TABLES = {
    'index_global': 5,     # 国际指数，延迟发布
    'margin': 5,           # 融资融券汇总
    'margin_detail': 5,    # 融资融券明细
    'shibor_quote': 3,     # SHIBOR报价
    'fund_nav': 5,         # 基金净值（延迟公布较多）
    'bond_blk': 5,
    'bond_blk_detail': 5,
}

# 默认回溯天数（用于普通增量更新，用户可通过 --lookback 覆盖）
DEFAULT_LOOKBACK_DAYS = 1

# 全局回溯天数覆盖（用于长时间未更新的情况）
_GLOBAL_LOOKBACK_OVERRIDE = None


def set_global_lookback(days: int):
    """设置全局回溯天数覆盖"""
    global _GLOBAL_LOOKBACK_OVERRIDE
    _GLOBAL_LOOKBACK_OVERRIDE = days


def get_table_last_date(db_path: str, table_name: str, date_column: str = 'trade_date') -> str:
    """
    查询表中实际数据的最大日期。
    直接查询数据表而非 metadata，确保准确性。
    
    Returns:
        最大日期 (YYYYMMDD) 或 None（表不存在/无数据）
    """
    try:
        with get_connection(db_path, read_only=True) as conn:
            # 检查表是否存在
            result = conn.execute("""
                SELECT count(*) FROM information_schema.tables 
                WHERE table_name = ?
            """, [table_name]).fetchone()
            
            if not result or result[0] == 0:
                return None
            
            # 查询最大日期
            result = conn.execute(f"""
                SELECT MAX({date_column}) FROM {table_name}
            """).fetchone()
            
            if result and result[0]:
                return str(result[0])
    except Exception as e:
        logger.warning(f"查询表 {table_name} 最大日期失败: {e}")
    
    return None


def get_lookback_days(table_name: str) -> int:
    """
    获取表的回溯天数。
    如果设置了全局覆盖，则使用全局值（适用于长时间未更新的场景）。
    否则使用表特定的配置或默认值。
    """
    if _GLOBAL_LOOKBACK_OVERRIDE is not None:
        return max(_GLOBAL_LOOKBACK_OVERRIDE, DELAYED_TABLES.get(table_name, DEFAULT_LOOKBACK_DAYS))
    return DELAYED_TABLES.get(table_name, DEFAULT_LOOKBACK_DAYS)


def get_last_trade_date(target_date: str = None) -> str:
    """
    获取最近的交易日。
    如果指定了 target_date，返回该日期；否则：
    - 若当前时间 >= 18:00，以今天为基准查找最近交易日（可获取当日数据）
    - 若当前时间 < 18:00，以昨天为基准查找最近交易日（当日数据可能未更新完）
    """
    if target_date:
        return target_date
    
    now = datetime.now()
    
    # 18:00后可以获取当日数据（收盘后约3小时，数据应已更新）
    # 18:00前使用昨天作为基准
    if now.hour >= 18:
        reference_date = now.strftime('%Y%m%d')
    else:
        reference_date = (now - timedelta(days=1)).strftime('%Y%m%d')
    
    # 查询交易日历确认是否为交易日
    try:
        with get_connection(BASIC_DB_PATH, read_only=True) as conn:
            result = conn.execute("""
                SELECT cal_date FROM trade_cal 
                WHERE exchange = 'SSE' 
                  AND is_open = 1 
                  AND cal_date <= ? 
                ORDER BY cal_date DESC 
                LIMIT 1
            """, [reference_date]).fetchone()
            
            if result:
                return result[0]
    except Exception as e:
        logger.warning(f"查询交易日历失败: {e}，使用参考日期")
    
    return reference_date


def validate_categories(categories: list) -> list:
    """验证并返回有效的类别列表"""
    valid_categories = [c for c in categories if c in DAILY_TABLES]
    invalid = [c for c in categories if c not in DAILY_TABLES]
    
    if invalid:
        logger.warning(f"以下类别无效或不在日频数据范围内，已忽略: {invalid}")
    
    return valid_categories


def calculate_start_date(last_date: str, lookback_days: int, end_date: str) -> str:
    """
    根据表的最后日期和回溯天数计算开始日期。
    
    Args:
        last_date: 表中数据的最大日期
        lookback_days: 需要回溯的天数
        end_date: 目标结束日期
        
    Returns:
        开始日期 (YYYYMMDD)
    """
    if not last_date:
        # 表为空或不存在，使用默认起始日期（最近30天）
        start = datetime.strptime(end_date, '%Y%m%d') - timedelta(days=30)
        return start.strftime('%Y%m%d')
    
    # 从最后日期回溯指定天数
    last_dt = datetime.strptime(last_date, '%Y%m%d')
    start_dt = last_dt - timedelta(days=lookback_days)
    
    return start_dt.strftime('%Y%m%d')


def run_daily_fetch(end_date: str, categories: list = None, dry_run: bool = False, 
                    auto_range: bool = True, show_comparison: bool = True) -> dict:
    """
    执行日频数据获取。
    
    Args:
        end_date: 目标结束日期 (YYYYMMDD)
        categories: 要获取的类别列表，None 表示全部
        dry_run: 是否仅模拟运行
        auto_range: 是否自动根据表数据确定开始日期
        show_comparison: 是否显示前后数据对比
        
    Returns:
        dict: 各类别的获取结果统计
    """
    results = {}
    consecutive_server_errors = 0
    max_consecutive_errors = 3  # 连续服务器错误阈值
    
    target_categories = categories or list(DAILY_TABLES.keys())
    target_categories = validate_categories(target_categories)
    
    if not target_categories:
        logger.error("没有有效的类别可供获取")
        return results
    
    mode_desc = '模拟运行 (DRY RUN)' if dry_run else ('自动增量' if auto_range else '指定日期')
    
    logger.info("=" * 70)
    logger.info(f"  Tushare 日频数据自动更新")
    logger.info(f"  目标日期: {end_date}")
    logger.info(f"  目标类别: {', '.join(target_categories)}")
    logger.info(f"  模式: {mode_desc}")
    logger.info("=" * 70)
    
    total_tables = sum(len(DAILY_TABLES[c]) for c in target_categories)
    processed = 0
    total_stored = 0
    
    # ==================== 阶段1: 收集获取前的数据统计 ====================
    if not dry_run and show_comparison:
        logger.info("\n" + "─" * 70)
        logger.info("  [阶段1] 收集获取前的数据统计...")
        logger.info("─" * 70)
    
    before_counts = {}  # {category: {table_name: {date: count}}}
    
    for category in target_categories:
        tables = DAILY_TABLES[category]
        config_group = API_CONFIG.get(category, {})
        db_path = config_group.get('db_path', '')
        
        before_counts[category] = {}
        
        if not dry_run and show_comparison:
            logger.info(f"\n  {category.upper()}:")
            for table_name in tables:
                table_config = config_group.get('tables', {}).get(table_name, {})
                date_column = table_config.get('date_column', 'trade_date')
                counts = get_daily_counts(db_path, table_name, date_column, days=30)
                before_counts[category][table_name] = counts
                
                if counts:
                    recent_dates = sorted(counts.keys(), reverse=True)[:3]
                    recent_info = ", ".join([f"{d}:{counts[d]}" for d in recent_dates])
                    logger.info(f"    {table_name}: 最近3日 [{recent_info}]")
                else:
                    logger.info(f"    {table_name}: 无数据")
    
    # ==================== 阶段2: 执行数据获取 ====================
    if not dry_run:
        logger.info("\n" + "─" * 70)
        logger.info("  [阶段2] 执行数据获取...")
        logger.info("─" * 70)
    
    for category in target_categories:
        tables = DAILY_TABLES[category]
        config_group = API_CONFIG.get(category, {})
        db_path = config_group.get('db_path', '')
        
        logger.info(f"\n{'─' * 50}")
        logger.info(f"类别: {category.upper()} ({len(tables)} 个表)")
        logger.info(f"{'─' * 50}")
        
        category_result = {
            'tables': tables,
            'success': [],
            'failed': [],
            'skipped': [],
            'stored_count': 0,
            'date_ranges': {},
        }
        
        if dry_run:
            # Dry run 模式：显示每个表的预计日期范围
            for table_name in tables:
                table_config = config_group.get('tables', {}).get(table_name, {})
                date_column = table_config.get('date_column', 'trade_date')
                lookback = get_lookback_days(table_name)
                
                last_date = get_table_last_date(db_path, table_name, date_column) if auto_range else None
                start_date = calculate_start_date(last_date, lookback, end_date) if auto_range else end_date
                
                category_result['date_ranges'][table_name] = {
                    'last_date': last_date,
                    'start_date': start_date,
                    'end_date': end_date,
                    'lookback': lookback,
                }
                
                range_info = f"({start_date}~{end_date})" if auto_range else f"({end_date})"
                lookback_hint = f" [回溯{lookback}天]" if lookback > 1 else ""
                logger.info(f"  [DRY RUN] {table_name}{lookback_hint}: {range_info}, 本地最新: {last_date or '无数据'}")
            
            category_result['skipped'] = tables
            results[category] = category_result
            continue
        
        # 正式获取：逐表处理
        for table_name in tables:
            table_config = config_group.get('tables', {}).get(table_name, {})
            date_column = table_config.get('date_column', 'trade_date')
            lookback = get_lookback_days(table_name)
            
            # 获取表的最新日期
            if auto_range:
                last_date = get_table_last_date(db_path, table_name, date_column)
                start_date = calculate_start_date(last_date, lookback, end_date)
            else:
                last_date = None
                start_date = end_date
            
            category_result['date_ranges'][table_name] = {
                'last_date': last_date,
                'start_date': start_date,
                'end_date': end_date,
            }
            
            range_info = f"{start_date}~{end_date}" if start_date != end_date else end_date
            lookback_hint = f" [回溯{lookback}天]" if lookback > 1 else ""
            logger.info(f"  → {table_name}{lookback_hint}: {range_info} (本地最新: {last_date or '无'})")
            
            try:
                stored = fetch_and_store_data(
                    category=category,
                    start_date=start_date,
                    end_date=end_date,
                    selected_tables=table_name,
                    batch_size=50,
                    force_fetch=False,
                    overwrite=False
                )
                
                category_result['success'].append(table_name)
                category_result['stored_count'] += stored
                total_stored += stored
                consecutive_server_errors = 0
                
            except ConnectionError as e:
                consecutive_server_errors += 1
                category_result['failed'].append(table_name)
                category_result['error'] = str(e)
                logger.error(f"    ✗ {table_name} 服务器错误: {e}")
                
                if consecutive_server_errors >= max_consecutive_errors:
                    logger.error(f"\n连续 {max_consecutive_errors} 次服务器错误，中断执行")
                    results[category] = category_result
                    print_summary(results, end_date, dry_run, auto_range)
                    return results
                    
            except Exception as e:
                category_result['failed'].append(table_name)
                logger.error(f"    ✗ {table_name} 获取失败: {e}")
            
            processed += 1
        
        # 类别完成汇总
        success_count = len(category_result['success'])
        failed_count = len(category_result['failed'])
        logger.info(f"  ✓ {category} 完成: {success_count}个成功, {failed_count}个失败, 存储{category_result['stored_count']}条")
        logger.info(f"  总进度: {processed}/{total_tables} 表")
        
        results[category] = category_result
    
    # ==================== 阶段3: 显示前后对比 ====================
    if not dry_run and show_comparison:
        logger.info("\n" + "=" * 70)
        logger.info("  [阶段3] 数据变化对比 (过去15日)")
        logger.info("=" * 70)
        
        for category in target_categories:
            tables = DAILY_TABLES[category]
            config_group = API_CONFIG.get(category, {})
            db_path = config_group.get('db_path', '')
            
            logger.info(f"\n  {category.upper()}:")
            
            for table_name in tables:
                table_config = config_group.get('tables', {}).get(table_name, {})
                date_column = table_config.get('date_column', 'trade_date')
                
                before = before_counts.get(category, {}).get(table_name, {})
                after = get_daily_counts(db_path, table_name, date_column, days=30)
                
                # 计算变化汇总
                all_dates = sorted(set(before.keys()) | set(after.keys()), reverse=True)[:15]
                changes = []
                for date in all_dates:
                    diff = after.get(date, 0) - before.get(date, 0)
                    if diff != 0:
                        changes.append(f"{date}:+{diff}" if diff > 0 else f"{date}:{diff}")
                
                if changes:
                    logger.info(f"    {table_name}: {', '.join(changes[:5])}" + 
                               (f" (还有{len(changes)-5}天有变化)" if len(changes) > 5 else ""))
                else:
                    logger.info(f"    {table_name}: 无变化")
    
    # 输出汇总
    print_summary(results, end_date, dry_run, auto_range)
    
    return results


def print_summary(results: dict, target_date: str, dry_run: bool, auto_range: bool = True):
    """打印执行汇总"""
    logger.info("\n" + "=" * 70)
    logger.info("  执行汇总")
    logger.info("=" * 70)
    
    total_success = sum(len(r.get('success', [])) for r in results.values())
    total_failed = sum(len(r.get('failed', [])) for r in results.values())
    total_skipped = sum(len(r.get('skipped', [])) for r in results.values())
    total_stored = sum(r.get('stored_count', 0) for r in results.values())
    
    mode_str = '自动增量' if auto_range else '指定日期'
    logger.info(f"  结束日期: {target_date}")
    logger.info(f"  模式: {mode_str}")
    logger.info(f"  类别数: {len(results)}")
    logger.info(f"  成功表数: {total_success}")
    logger.info(f"  失败表数: {total_failed}")
    if dry_run:
        logger.info(f"  跳过表数 (DRY RUN): {total_skipped}")
    logger.info(f"  总存储记录: {total_stored}")
    
    if total_failed > 0:
        logger.info("\n  失败详情:")
        for cat, result in results.items():
            if result.get('failed'):
                logger.info(f"    - {cat}: {result.get('error', 'Unknown error')}")
    
    logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Tushare 日频数据自动更新脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          # 自动增量获取（根据每表最新日期）
  %(prog)s --date 20260110          # 指定结束日期（仍然自动计算开始日期）
  %(prog)s --lookback 14            # 强制回溯14天（适合长时间未更新）
  %(prog)s --no-auto-range          # 仅获取最近交易日当天数据
  %(prog)s --categories stock,index # 仅获取股票和指数数据
  %(prog)s --dry-run                # 模拟运行（显示每表日期范围）
  %(prog)s --list-categories        # 显示所有可用类别
        """
    )
    
    parser.add_argument(
        '--date', '-d',
        type=str,
        default=None,
        help='目标结束日期 (YYYYMMDD)，默认为最近交易日'
    )
    
    parser.add_argument(
        '--categories', '-c',
        type=str,
        default=None,
        help='要获取的类别，逗号分隔 (如: stock,index,fund)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，只显示将要获取的数据，不实际执行'
    )
    
    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='显示所有可用的日频数据类别和表'
    )
    
    parser.add_argument(
        '--no-auto-range',
        action='store_true',
        help='禁用自动日期范围检测，仅获取指定日期当天的数据'
    )
    
    parser.add_argument(
        '--lookback', '-l',
        type=int,
        default=None,
        help='强制设置回溯天数（覆盖默认值）。适用于长时间未更新的情况，如 --lookback 14 会回溯14天'
    )
    
    args = parser.parse_args()
    
    # 显示类别列表
    if args.list_categories:
        print("\n可用的日频数据类别及表:")
        print("=" * 60)
        for cat, tables in DAILY_TABLES.items():
            delayed = [t for t in tables if t in DELAYED_TABLES]
            print(f"\n{cat.upper()} ({len(tables)} 个表):")
            for t in tables:
                suffix = f" [回溯{DELAYED_TABLES[t]}天]" if t in DELAYED_TABLES else ""
                print(f"  - {t}{suffix}")
        print("\n" + "=" * 60)
        print(f"总计: {len(DAILY_TABLES)} 个类别, {sum(len(t) for t in DAILY_TABLES.values())} 个表")
        print(f"默认回溯: {DEFAULT_LOOKBACK_DAYS} 天（可用 --lookback N 覆盖）")
        return
    
    # 设置全局回溯覆盖
    if args.lookback is not None:
        set_global_lookback(args.lookback)
        logger.info(f"已设置全局回溯天数: {args.lookback} 天")
    
    # 解析参数
    target_date = get_last_trade_date(args.date)
    categories = args.categories.split(',') if args.categories else None
    auto_range = not args.no_auto_range
    
    # 执行获取
    results = run_daily_fetch(target_date, categories, args.dry_run, auto_range)
    
    # 返回状态码
    total_failed = sum(len(r.get('failed', [])) for r in results.values())
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == '__main__':
    main()
