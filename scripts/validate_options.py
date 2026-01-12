#!/usr/bin/env python3
"""
期权数据验证脚本

交叉验证 opt_basic 和 opt_daily 表，检查：
1. 缺失合约：opt_daily 中有但 opt_basic 中没有的 ts_code
2. 数据完整性：每个合约的日期覆盖情况
3. 孤立数据：在合约生命周期外的数据

使用方法：
    python -m scripts.validate_options
    python -m scripts.validate_options --exchange SSE
    python -m scripts.validate_options --detail
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

# 今天日期（用于完整性检查的截止日期）
TODAY = datetime.now().strftime('%Y%m%d')


def get_db_paths():
    """获取期权相关的数据库路径"""
    opt_config = API_CONFIG.get('option', {})
    opt_db = opt_config.get('db_path', '')
    
    # trade_cal 在 basic 数据库
    basic_config = API_CONFIG.get('stock_events', {})
    basic_db = basic_config.get('db_path', '')
    
    return opt_db, basic_db


def check_missing_contracts(opt_db: str, exchange: str = None) -> dict:
    """
    检查 opt_daily 中有但 opt_basic 中没有的合约。
    
    Returns:
        dict: {
            'total_basic': int,           # opt_basic 合约数
            'total_daily': int,           # opt_daily 去重合约数
            'missing_in_basic': list,     # 缺失的 ts_code 列表
            'extra_in_basic': list,       # basic 中有但 daily 中没数据的
        }
    """
    result = {
        'total_basic': 0,
        'total_daily': 0,
        'missing_in_basic': [],
        'extra_in_basic': [],
    }
    
    try:
        with get_connection(opt_db, read_only=True) as conn:
            # 获取 opt_basic 中的所有合约
            where_clause = f"WHERE exchange = '{exchange}'" if exchange else ""
            basic_codes = conn.execute(f"""
                SELECT DISTINCT ts_code FROM opt_basic {where_clause}
            """).fetchall()
            basic_set = {row[0] for row in basic_codes}
            result['total_basic'] = len(basic_set)
            
            # 获取 opt_daily 中的所有合约
            if exchange:
                daily_codes = conn.execute(f"""
                    SELECT DISTINCT ts_code FROM opt_daily WHERE exchange = '{exchange}'
                """).fetchall()
            else:
                daily_codes = conn.execute("""
                    SELECT DISTINCT ts_code FROM opt_daily
                """).fetchall()
            daily_set = {row[0] for row in daily_codes}
            result['total_daily'] = len(daily_set)
            
            # 找出差异
            result['missing_in_basic'] = sorted(daily_set - basic_set)
            result['extra_in_basic'] = sorted(basic_set - daily_set)
            
            # 获取缺失合约的详细信息
            if result['missing_in_basic']:
                missing_details = conn.execute("""
                    SELECT 
                        d.ts_code, 
                        d.exchange,
                        MIN(d.trade_date) as first_trade,
                        MAX(d.trade_date) as last_trade,
                        COUNT(*) as record_count
                    FROM opt_daily d
                    LEFT JOIN opt_basic b ON d.ts_code = b.ts_code
                    WHERE b.ts_code IS NULL
                    GROUP BY d.ts_code, d.exchange
                    ORDER BY first_trade, d.ts_code
                """).fetchall()
                result['missing_details'] = [
                    {'ts_code': r[0], 'exchange': r[1], 'first_trade': r[2], 
                     'last_trade': r[3], 'record_count': r[4]}
                    for r in missing_details
                ]
            
    except Exception as e:
        logger.error(f"检查缺失合约时出错: {e}")
        
    return result


def check_data_completeness(opt_db: str, basic_db: str, exchange: str = None,
                           sample_size: int = 100) -> dict:
    """
    检查每个合约的数据完整性。
    
    对比每个合约的 list_date ~ delist_date 与实际行情日期：
    - 找出有数据缺口的合约
    - 统计缺口天数
    
    Args:
        sample_size: 抽样检查的合约数（0表示全部）
        
    Returns:
        dict: {
            'checked_count': int,
            'complete_count': int,
            'incomplete_contracts': list of dict,
        }
    """
    result = {
        'checked_count': 0,
        'complete_count': 0,
        'incomplete_contracts': [],
    }
    
    try:
        with get_connection(opt_db, read_only=True) as opt_conn:
            # 获取需要检查的合约（有行情数据且已退市的）
            where_clause = f"WHERE b.exchange = '{exchange}'" if exchange else ""
            
            query = f"""
                SELECT 
                    b.ts_code, 
                    b.list_date, 
                    b.delist_date,
                    b.exchange,
                    MIN(d.trade_date) as first_trade,
                    MAX(d.trade_date) as last_trade,
                    COUNT(DISTINCT d.trade_date) as trade_days
                FROM opt_basic b
                INNER JOIN opt_daily d ON b.ts_code = d.ts_code
                {where_clause}
                GROUP BY b.ts_code, b.list_date, b.delist_date, b.exchange
                ORDER BY b.ts_code
            """
            
            if sample_size > 0:
                query += f" LIMIT {sample_size}"
            
            contracts = opt_conn.execute(query).fetchall()
            result['checked_count'] = len(contracts)
            
            # 获取交易日历
            with get_connection(basic_db, read_only=True) as basic_conn:
                trade_cal = basic_conn.execute("""
                    SELECT cal_date FROM trade_cal 
                    WHERE exchange = 'SSE' AND is_open = '1'
                    ORDER BY cal_date
                """).fetchall()
                trade_days_set = {row[0] for row in trade_cal}
            
            for row in contracts:
                ts_code, list_date, delist_date, exch, first_trade, last_trade, actual_days = row
                
                # 跳过信息不完整的合约
                if not list_date or not delist_date:
                    continue
                
                # 使用 min(delist_date, today) 作为检查截止日期
                # 避免将未来日期误判为缺失
                check_end_date = min(delist_date, TODAY)
                
                # 计算应有的交易日数（到今天为止）
                expected_days = sum(
                    1 for d in trade_days_set 
                    if list_date <= d <= check_end_date
                )
                
                # 对比
                if expected_days > 0:
                    completeness = actual_days / expected_days
                    
                    if completeness >= 0.95:  # 95% 以上视为完整
                        result['complete_count'] += 1
                    else:
                        missing_days = expected_days - actual_days
                        result['incomplete_contracts'].append({
                            'ts_code': ts_code,
                            'exchange': exch,
                            'list_date': list_date,
                            'delist_date': delist_date,
                            'expected_days': expected_days,
                            'actual_days': actual_days,
                            'missing_days': missing_days,
                            'completeness': f"{completeness*100:.1f}%",
                        })
                        
    except Exception as e:
        logger.error(f"检查数据完整性时出错: {e}")
        import traceback
        traceback.print_exc()
        
    return result


def check_orphan_data(opt_db: str, exchange: str = None) -> dict:
    """
    检查在合约生命周期外的孤立数据。
    
    找出 opt_daily 中 trade_date 不在 list_date ~ delist_date 范围内的记录。
    
    Returns:
        dict: {
            'before_list': list,    # 在 list_date 之前的数据
            'after_delist': list,   # 在 delist_date 之后的数据
        }
    """
    result = {
        'before_list': [],
        'after_delist': [],
    }
    
    try:
        with get_connection(opt_db, read_only=True) as conn:
            where_clause = f"AND b.exchange = '{exchange}'" if exchange else ""
            
            # 检查 list_date 之前的数据
            before_list = conn.execute(f"""
                SELECT d.ts_code, d.trade_date, b.list_date, b.exchange
                FROM opt_daily d
                INNER JOIN opt_basic b ON d.ts_code = b.ts_code
                WHERE d.trade_date < b.list_date {where_clause}
                ORDER BY d.ts_code, d.trade_date
                LIMIT 50
            """).fetchall()
            
            result['before_list'] = [
                {'ts_code': r[0], 'trade_date': r[1], 'list_date': r[2], 'exchange': r[3]}
                for r in before_list
            ]
            
            # 检查 delist_date 之后的数据
            after_delist = conn.execute(f"""
                SELECT d.ts_code, d.trade_date, b.delist_date, b.exchange
                FROM opt_daily d
                INNER JOIN opt_basic b ON d.ts_code = b.ts_code
                WHERE b.delist_date IS NOT NULL 
                  AND d.trade_date > b.delist_date {where_clause}
                ORDER BY d.ts_code, d.trade_date
                LIMIT 50
            """).fetchall()
            
            result['after_delist'] = [
                {'ts_code': r[0], 'trade_date': r[1], 'delist_date': r[2], 'exchange': r[3]}
                for r in after_delist
            ]
            
    except Exception as e:
        logger.error(f"检查孤立数据时出错: {e}")
        
    return result


def get_data_coverage_by_exchange(opt_db: str) -> dict:
    """按交易所统计数据覆盖情况"""
    result = {}
    
    try:
        with get_connection(opt_db, read_only=True) as conn:
            # opt_basic 按交易所统计
            basic_stats = conn.execute("""
                SELECT exchange, COUNT(*) as cnt, 
                       MIN(list_date) as earliest, MAX(delist_date) as latest
                FROM opt_basic
                GROUP BY exchange
            """).fetchall()
            
            for row in basic_stats:
                exch = row[0]
                result[exch] = {
                    'basic_count': row[1],
                    'basic_earliest': row[2],
                    'basic_latest': row[3],
                }
            
            # opt_daily 按交易所统计
            daily_stats = conn.execute("""
                SELECT exchange, COUNT(DISTINCT ts_code) as contracts,
                       MIN(trade_date) as earliest, MAX(trade_date) as latest,
                       COUNT(*) as total_records
                FROM opt_daily
                GROUP BY exchange
            """).fetchall()
            
            for row in daily_stats:
                exch = row[0]
                if exch not in result:
                    result[exch] = {}
                result[exch].update({
                    'daily_contracts': row[1],
                    'daily_earliest': row[2],
                    'daily_latest': row[3],
                    'daily_records': row[4],
                })
                
    except Exception as e:
        logger.error(f"统计数据覆盖时出错: {e}")
        
    return result


def generate_report(missing: dict, completeness: dict, orphan: dict, 
                   coverage: dict, exchange: str = None, show_detail: bool = False):
    """生成验证报告"""
    print("\n" + "=" * 70)
    print("  期权数据验证报告")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if exchange:
        print(f"  交易所筛选: {exchange}")
    print("=" * 70)
    
    # 1. 合约数量对比
    print("\n【1. 合约基础信息检查】")
    print(f"   opt_basic 合约数: {missing['total_basic']:,}")
    print(f"   opt_daily 合约数: {missing['total_daily']:,}")
    
    missing_count = len(missing['missing_in_basic'])
    if missing_count > 0:
        print(f"   ⚠ 缺失合约: {missing_count} (opt_daily有但opt_basic无，需要更新opt_basic)")
        if show_detail:
            for code in missing['missing_in_basic'][:20]:
                print(f"      - {code}")
            if missing_count > 20:
                print(f"      ... 还有 {missing_count - 20} 个")
    else:
        print("   ✓ 无缺失合约")
    
    extra_count = len(missing['extra_in_basic'])
    if extra_count > 0:
        print(f"   ℹ 无行情合约: {extra_count} (opt_basic有但opt_daily无数据)")
    
    # 2. 数据完整性
    print("\n【2. 数据完整性检查】")
    checked = completeness['checked_count']
    complete = completeness['complete_count']
    incomplete = len(completeness['incomplete_contracts'])
    
    if checked > 0:
        rate = complete / checked * 100
        print(f"   检查合约数: {checked:,}")
        print(f"   完整合约数: {complete:,} ({rate:.1f}%)")
        print(f"   不完整合约: {incomplete:,}")
        
        if show_detail and incomplete > 0:
            print("\n   不完整合约详情 (前10个):")
            for c in completeness['incomplete_contracts'][:10]:
                print(f"      - {c['ts_code']}: 应有{c['expected_days']}天, "
                      f"实有{c['actual_days']}天, 缺失{c['missing_days']}天 "
                      f"({c['completeness']})")
    else:
        print("   未检查（无合约数据）")
    
    # 3. 孤立数据
    print("\n【3. 孤立数据检查】")
    before_count = len(orphan['before_list'])
    after_count = len(orphan['after_delist'])
    
    if before_count == 0 and after_count == 0:
        print("   ✓ 无孤立数据")
    else:
        if before_count > 0:
            print(f"   ⚠ list_date 之前的数据: {before_count} 条")
            if show_detail:
                for o in orphan['before_list'][:5]:
                    print(f"      - {o['ts_code']}: 行情{o['trade_date']} < list_date{o['list_date']}")
        if after_count > 0:
            print(f"   ⚠ delist_date 之后的数据: {after_count} 条")
            if show_detail:
                for o in orphan['after_delist'][:5]:
                    print(f"      - {o['ts_code']}: 行情{o['trade_date']} > delist_date{o['delist_date']}")
    
    # 4. 按交易所统计
    print("\n【4. 按交易所统计】")
    for exch, stats in sorted(coverage.items()):
        basic_count = stats.get('basic_count', 0)
        daily_contracts = stats.get('daily_contracts', 0)
        daily_records = stats.get('daily_records', 0)
        daily_earliest = stats.get('daily_earliest', '-')
        daily_latest = stats.get('daily_latest', '-')
        
        print(f"\n   {exch}:")
        print(f"      基础合约: {basic_count:,}")
        print(f"      有行情合约: {daily_contracts:,}")
        print(f"      行情记录数: {daily_records:,}")
        print(f"      行情日期范围: {daily_earliest} ~ {daily_latest}")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='期权数据验证脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 验证所有期权数据
  %(prog)s --exchange SSE     # 仅验证上交所期权
  %(prog)s --detail           # 显示详细信息
  %(prog)s --sample 50        # 完整性检查抽样50个合约
        """
    )
    
    parser.add_argument(
        '--exchange', '-e',
        type=str,
        default=None,
        help='交易所代码 (SSE, SZSE, DCE, CZCE, SHFE, CFFEX, INE)'
    )
    
    parser.add_argument(
        '--detail', '-d',
        action='store_true',
        help='显示详细信息'
    )
    
    parser.add_argument(
        '--sample', '-s',
        type=int,
        default=100,
        help='完整性检查抽样数量 (0=全部，默认100)'
    )
    
    parser.add_argument(
        '--export-missing',
        type=str,
        default=None,
        metavar='FILE',
        help='导出缺失合约列表到文件 (每行一个ts_code)'
    )
    
    args = parser.parse_args()
    
    opt_db, basic_db = get_db_paths()
    
    if not opt_db:
        logger.error("未找到期权数据库配置")
        sys.exit(1)
    
    print(f"正在验证期权数据库: {opt_db}")
    
    # 执行检查
    print("检查缺失合约...")
    missing = check_missing_contracts(opt_db, args.exchange)
    
    # 如果需要导出缺失合约
    if args.export_missing and missing['missing_in_basic']:
        export_file = args.export_missing
        with open(export_file, 'w') as f:
            for code in missing['missing_in_basic']:
                f.write(f"{code}\n")
        print(f"\n已导出 {len(missing['missing_in_basic'])} 个缺失合约到: {export_file}")
        
        # 按交易所分组显示
        if 'missing_details' in missing:
            print("\n按交易所分组:")
            by_exchange = {}
            for d in missing['missing_details']:
                exch = d['exchange']
                if exch not in by_exchange:
                    by_exchange[exch] = []
                by_exchange[exch].append(d)
            
            for exch in sorted(by_exchange.keys()):
                items = by_exchange[exch]
                print(f"  {exch}: {len(items)} 个")
        return
    
    print("检查数据完整性...")
    completeness = check_data_completeness(opt_db, basic_db, args.exchange, args.sample)
    
    print("检查孤立数据...")
    orphan = check_orphan_data(opt_db, args.exchange)
    
    print("统计数据覆盖...")
    coverage = get_data_coverage_by_exchange(opt_db)
    
    # 生成报告
    generate_report(missing, completeness, orphan, coverage, 
                   args.exchange, args.detail)


if __name__ == '__main__':
    main()
