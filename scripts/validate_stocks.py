#!/usr/bin/env python3
"""
股票数据验证脚本

交叉验证股票相关表，检查：
1. 基础信息：stock_basic 与 daily 代码一致性
2. 数据完整性：daily 数据在 list_date ~ today 期间的覆盖率（扣除停牌）
3. 表间一致性：daily vs daily_basic vs stk_limit 的记录对齐

使用方法：
    python -m scripts.validate_stocks
    python -m scripts.validate_stocks --sample 100
    python -m scripts.validate_stocks --detail
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.tushare_duckdb.config import API_CONFIG
from src.tushare_duckdb.utils import get_connection
from src.tushare_duckdb.logger import logger

# 今天日期
TODAY = datetime.now().strftime('%Y%m%d')

def get_db_paths():
    """获取股票相关的数据库路径"""
    # stock_basic, daily, daily_basic, stk_limit 在 stock 库
    stock_config = API_CONFIG.get('stock', {})
    stock_db = stock_config.get('db_path', '')
    
    # suspend_d 在 stock_events 库
    events_config = API_CONFIG.get('stock_events', {})
    events_db = events_config.get('db_path', '')
    
    return stock_db, events_db


def check_basic_consistency(stock_db: str) -> dict:
    """
    检查 stock_basic 与 daily 的一致性。
    """
    result = {
        'total_basic': 0,
        'total_daily': 0,
        'missing_in_basic': [],
        'extra_in_basic': [],
    }
    
    try:
        with get_connection(stock_db, read_only=True) as conn:
            # 获取 stock_basic 合约
            basic_codes = conn.execute("SELECT DISTINCT ts_code FROM stock_basic").fetchall()
            basic_set = {row[0] for row in basic_codes}
            result['total_basic'] = len(basic_set)
            
            # 获取 daily 合约
            daily_codes = conn.execute("SELECT DISTINCT ts_code FROM daily").fetchall()
            daily_set = {row[0] for row in daily_codes}
            result['total_daily'] = len(daily_set)
            
            # 找出差异
            result['missing_in_basic'] = sorted(daily_set - basic_set)
            result['extra_in_basic'] = sorted(basic_set - daily_set)
            
    except Exception as e:
        logger.error(f"检查基础信息一致性时出错: {e}")
        
    return result


def check_table_alignment(stock_db: str, sample_date: str = None) -> dict:
    """
    检查 daily, daily_basic, stk_limit 的记录数量一致性。
    如果指定 sample_date，则检查该日的对齐情况。
    """
    result = {}
    
    try:
        with get_connection(stock_db, read_only=True) as conn:
            tables = ['daily', 'daily_basic', 'stk_limit']
            
            # 1. 总量检查
            for table in tables:
                cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                date_range = conn.execute(f"SELECT MIN(trade_date), MAX(trade_date) FROM {table}").fetchone()
                result[table] = {
                    'count': cnt,
                    'min_date': date_range[0],
                    'max_date': date_range[1]
                }
            
            # 2. 抽样日期检查
            if not sample_date:
                # 默认取最近一个交易日
                sample_date = result['daily']['max_date']
            
            result['sample_date'] = sample_date
            alignment = {}
            for table in tables:
                day_cnt = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE trade_date = '{sample_date}'").fetchone()[0]
                alignment[table] = day_cnt
            result['alignment'] = alignment
            
    except Exception as e:
        logger.error(f"检查表间一致性时出错: {e}")
        
    return result


def check_data_gaps(stock_db: str, events_db: str, sample_size: int = 100) -> dict:
    """
    检查数据缺口（Data Gaps）。
    逻辑：
    1. 预期交易日 = 交易日历 (list_date ~ min(delist_date, today))
    2. 扣除停牌日 (suspend_d)
    3. 对比 actual_days (daily)
    """
    result = {
        'checked_count': 0,
        'complete_count': 0,
        'incomplete_contracts': [],
    }
    
    try:
        # 1. 获取交易日历 (只取SSE作为标准A股日历)
        with get_connection(events_db, read_only=True) as conn:
            cal = conn.execute(f"""
                SELECT cal_date FROM trade_cal 
                WHERE is_open = '1' AND exchange = 'SSE' AND cal_date <= '{TODAY}'
                ORDER BY cal_date
            """).fetchall()
            trade_days = [r[0] for r in cal]
            trade_days_set = set(trade_days)
            
            # 获取停牌数据
            # 由于停牌数据可能很大，我们稍后只针对抽样的股票查询
        
        # 2. 获取股票列表和实际交易天数
        with get_connection(stock_db, read_only=True) as conn:
            query = f"""
                SELECT 
                    b.ts_code, b.name, b.list_date, b.delist_date,
                    COUNT(d.trade_date) as actual_days
                FROM stock_basic b
                LEFT JOIN daily d ON b.ts_code = d.ts_code
                WHERE b.list_date IS NOT NULL
                GROUP BY b.ts_code, b.name, b.list_date, b.delist_date
                ORDER BY b.ts_code
            """
            if sample_size > 0:
                query += f" LIMIT {sample_size}"
                
            contracts = conn.execute(query).fetchall()
            result['checked_count'] = len(contracts)
            
            for row in contracts:
                ts_code, name, list_date, delist_date, actual_days = row
                
                # 确定检查截止日期
                check_end = min(delist_date, TODAY) if delist_date else TODAY
                
                # 预期交易日
                expected_days_list = [d for d in trade_days if list_date <= d <= check_end]
                expected_count = len(expected_days_list)
                
                # 如果实际天数 == 预期天数，直接判定完整（无需查停牌，节省IO）
                if actual_days == expected_count:
                    result['complete_count'] += 1
                    continue
                
                # 如果不一致，检查是否因停牌导致
                with get_connection(events_db, read_only=True) as events_conn:
                    suspend_days = events_conn.execute(f"""
                        SELECT trade_date FROM suspend_d 
                        WHERE ts_code = '{ts_code}'
                    """).fetchall()
                    suspend_set = {r[0] for r in suspend_days}
                
                # 扣除停牌日后的预期天数
                # 注意：suspend_d 有时记录了非交易日的停牌，或者是区间的。这里简化处理：
                # 真正预期的 = 预期交易日 - (预期交易日 & 停牌日)
                valid_suspend = set(expected_days_list) & suspend_set
                adjusted_expected = expected_count - len(valid_suspend)
                
                if actual_days >= adjusted_expected * 0.99: # 允许1%的误差（可能是数据源导致的微小差异）
                    result['complete_count'] += 1
                else:
                    missing = adjusted_expected - actual_days
                    completeness = actual_days / adjusted_expected if adjusted_expected > 0 else 0
                    
                    result['incomplete_contracts'].append({
                        'ts_code': ts_code,
                        'name': name,
                        'list_date': list_date,
                        'expected': adjusted_expected,
                        'actual': actual_days,
                        'suspend': len(valid_suspend),
                        'missing': missing,
                        'rate': f"{completeness*100:.1f}%"
                    })
                    
    except Exception as e:
        logger.error(f"检查数据缺口时出错: {e}")
        import traceback
        traceback.print_exc()
        
    return result


def generate_report(basic_res: dict, align_res: dict, gap_res: dict, show_detail: bool = False):
    """生成报告"""
    print("\n" + "=" * 70)
    print("  股票数据验证报告")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 基础一致性
    print("\n【1. 基础信息一致性 (stock_basic vs daily)】")
    print(f"   stock_basic 合约: {basic_res['total_basic']:,}")
    print(f"   daily 合约:      {basic_res['total_daily']:,}")
    
    missing = len(basic_res['missing_in_basic'])
    if missing > 0:
        print(f"   ⚠ 缺失合约: {missing} (daily有但basic无)")
        if show_detail:
            print(f"      示例: {basic_res['missing_in_basic'][:10]}")
    else:
        print("   ✓ 无缺失合约")
        
    extra = len(basic_res['extra_in_basic'])
    if extra > 0:
        print(f"   ℹ 无行情合约: {extra} (basic有但daily无)")
    
    # 2. 表间一致性
    print("\n【2. 表间一致性 (Daily / Daily_Basic / Stk_Limit)】")
    print(f"   {'Table':12} | {'Count':>12} | {'Date Range':20}")
    print("   " + "-" * 50)
    for table, info in align_res.items():
        if table in ['sample_date', 'alignment']: continue
        print(f"   {table:12} | {info['count']:>12,} | {info['min_date']}~{info['max_date']}")
    
    print(f"\n   抽样日期对齐检查 ({align_res.get('sample_date', 'N/A')}):")
    align = align_res.get('alignment', {})
    base_cnt = align.get('daily', 0)
    for table, cnt in align.items():
        diff = cnt - base_cnt
        mark = "✓" if diff == 0 else f"⚠ ({diff:+})" 
        print(f"      {table:12}: {cnt:>6} {mark}")

    # 3. 数据完整性
    print("\n【3. 数据完整性 (扣除停牌后)】")
    checked = gap_res['checked_count']
    if checked > 0:
        complete = gap_res['complete_count']
        rate = complete / checked * 100
        print(f"   检查样本: {checked}")
        print(f"   完整合约: {complete} ({rate:.1f}%)")
        print(f"   不完整数: {len(gap_res['incomplete_contracts'])}")
        
        if gap_res['incomplete_contracts']:
            print("\n   不完整合约示例 (Top 10):")
            # 按缺失天数排序
            sorted_incomplete = sorted(gap_res['incomplete_contracts'], 
                                     key=lambda x: x['missing'], reverse=True)
            for c in sorted_incomplete[:10]:
                print(f"      - {c['ts_code']} ({c['name']}): 缺 {c['missing']} 天 "
                      f"(实有{c['actual']}/应有{c['expected']}, 停牌{c['suspend']})")
    else:
        print("   未执行完整性检查")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description='股票数据验证脚本')
    parser.add_argument('--sample', '-s', type=int, default=100, help='完整性检查样本数')
    parser.add_argument('--detail', '-d', action='store_true', help='显示详细信息')
    args = parser.parse_args()
    
    stock_db, events_db = get_db_paths()
    if not stock_db:
        logger.error("未找到股票数据库配置")
        sys.exit(1)
        
    print(f"正在验证股票数据库: {stock_db}")
    
    # 1. 基础一致性
    print("检查基础信息一致性...")
    basic_res = check_basic_consistency(stock_db)
    
    # 2. 表间一致性
    print("检查表间对齐情况...")
    align_res = check_table_alignment(stock_db)
    
    # 3. 数据完整性
    print(f"检查数据缺口 (样本 {args.sample})...")
    gap_res = check_data_gaps(stock_db, events_db, args.sample)
    
    generate_report(basic_res, align_res, gap_res, args.detail)


if __name__ == '__main__':
    main()
