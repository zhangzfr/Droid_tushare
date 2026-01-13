#!/usr/bin/env python3
"""
股票行情数据缺口修复脚本

策略：
1. 优先：从 Tushare API 重新获取缺失日期的数据
2. 回退：若 API 无法获取，从 bak_daily 复制

使用方法：
    python -m scripts.fix_daily_gaps --export           # 导出缺失清单
    python -m scripts.fix_daily_gaps --mode api         # 从API获取
    python -m scripts.fix_daily_gaps --mode bak         # 从bak_daily补充
    python -m scripts.fix_daily_gaps --mode api --dates 20250901,20250902  # 指定日期
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.tushare_duckdb.config import API_CONFIG, TUSHARE_TOKEN
from src.tushare_duckdb.utils import get_connection
from src.tushare_duckdb.logger import logger

import tushare as ts

# 初始化 Tushare
pro = ts.pro_api(TUSHARE_TOKEN)

def get_db_path():
    """获取股票数据库路径"""
    return API_CONFIG.get('stock', {}).get('db_path', '')


def export_gaps(output_file: str = None) -> dict:
    """
    导出缺失数据清单
    返回: {'dates': [日期列表], 'records': [(ts_code, trade_date), ...]}
    """
    stock_db = get_db_path()
    
    with get_connection(stock_db, read_only=True) as conn:
        # 获取缺失的日期列表
        missing_dates = conn.execute("""
            SELECT DISTINCT b.trade_date
            FROM bak_daily b
            LEFT JOIN daily d ON b.ts_code = d.ts_code AND b.trade_date = d.trade_date
            WHERE d.ts_code IS NULL
            ORDER BY b.trade_date
        """).fetchall()
        dates = [r[0] for r in missing_dates]
        
        # 获取缺失记录详情
        missing_records = conn.execute("""
            SELECT b.ts_code, b.trade_date
            FROM bak_daily b
            LEFT JOIN daily d ON b.ts_code = d.ts_code AND b.trade_date = d.trade_date
            WHERE d.ts_code IS NULL
            ORDER BY b.trade_date, b.ts_code
        """).fetchall()
        records = [(r[0], r[1]) for r in missing_records]
    
    result = {
        'dates': dates,
        'records': records,
        'date_count': len(dates),
        'record_count': len(records)
    }
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"# 缺失数据清单 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"# 共 {result['date_count']} 个交易日，{result['record_count']} 条记录\n\n")
            f.write("# 日期列表\n")
            for d in dates:
                f.write(f"{d}\n")
        logger.info(f"缺失清单已导出到: {output_file}")
    
    return result


def fetch_from_api(dates: list, dry_run: bool = False) -> dict:
    """
    从 Tushare API 获取指定日期的数据并插入 daily 表
    
    Args:
        dates: 要获取的日期列表
        dry_run: 是否仅模拟
    
    Returns:
        统计结果
    """
    stock_db = get_db_path()
    stats = {'fetched': 0, 'inserted': 0, 'skipped': 0, 'errors': []}
    
    logger.info(f"开始从 API 获取 {len(dates)} 个交易日的数据")
    
    for i, trade_date in enumerate(dates):
        try:
            logger.info(f"[{i+1}/{len(dates)}] 获取 {trade_date}...")
            
            if dry_run:
                logger.info(f"  [DRY-RUN] 跳过实际获取")
                continue
            
            # 调用 API
            df = pro.daily(trade_date=trade_date)
            time.sleep(0.15)  # 防止频率限制
            
            if df is None or len(df) == 0:
                logger.warning(f"  API 返回空数据")
                stats['skipped'] += 1
                continue
            
            stats['fetched'] += len(df)
            
            # 插入数据库（使用 INSERT OR IGNORE 避免重复）
            with get_connection(stock_db) as conn:
                # 先检查已存在的记录
                existing = conn.execute(f"""
                    SELECT ts_code FROM daily WHERE trade_date = '{trade_date}'
                """).fetchall()
                existing_codes = {r[0] for r in existing}
                
                # 过滤出需要插入的
                new_df = df[~df['ts_code'].isin(existing_codes)]
                
                if len(new_df) > 0:
                    # 插入新数据
                    conn.execute("BEGIN TRANSACTION")
                    for _, row in new_df.iterrows():
                        conn.execute("""
                            INSERT INTO daily (ts_code, trade_date, open, high, low, close, 
                                             pre_close, change, pct_chg, vol, amount)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, [
                            row['ts_code'], row['trade_date'], 
                            row.get('open'), row.get('high'), row.get('low'), row.get('close'),
                            row.get('pre_close'), row.get('change'), row.get('pct_chg'), 
                            row.get('vol'), row.get('amount')
                        ])
                    conn.execute("COMMIT")
                    stats['inserted'] += len(new_df)
                    logger.info(f"  插入 {len(new_df)} 条新记录")
                else:
                    logger.info(f"  无新数据需要插入")
                    
        except Exception as e:
            logger.error(f"  错误: {e}")
            stats['errors'].append((trade_date, str(e)))
            time.sleep(1)  # 出错后等待
    
    return stats


def supplement_from_bak(dry_run: bool = False) -> dict:
    """
    从 bak_daily 补充缺失数据到 daily
    
    Returns:
        统计结果
    """
    stock_db = get_db_path()
    stats = {'inserted': 0}
    
    logger.info("从 bak_daily 补充缺失数据...")
    
    if dry_run:
        with get_connection(stock_db, read_only=True) as conn:
            count = conn.execute("""
                SELECT COUNT(*)
                FROM bak_daily b
                LEFT JOIN daily d ON b.ts_code = d.ts_code AND b.trade_date = d.trade_date
                WHERE d.ts_code IS NULL
            """).fetchone()[0]
        logger.info(f"[DRY-RUN] 将插入 {count} 条记录")
        stats['inserted'] = count
        return stats
    
    with get_connection(stock_db) as conn:
        # 执行插入
        result = conn.execute("""
            INSERT INTO daily (ts_code, trade_date, open, high, low, close, 
                             pre_close, change, pct_chg, vol, amount)
            SELECT b.ts_code, b.trade_date, b.open, b.high, b.low, b.close, 
                   b.pre_close, b.change, b.pct_chg, b.vol, b.amount
            FROM bak_daily b
            LEFT JOIN daily d ON b.ts_code = d.ts_code AND b.trade_date = d.trade_date
            WHERE d.ts_code IS NULL
        """)
        
        # 获取插入数量
        inserted = conn.execute("SELECT changes()").fetchone()[0]
        stats['inserted'] = inserted
        logger.info(f"成功插入 {inserted} 条记录")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='股票行情数据缺口修复')
    parser.add_argument('--export', action='store_true', help='导出缺失清单')
    parser.add_argument('--mode', choices=['api', 'bak', 'both'], 
                       help='补充模式: api=从API获取, bak=从bak_daily补充')
    parser.add_argument('--dates', type=str, help='指定日期（逗号分隔）')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不实际修改')
    parser.add_argument('--output', '-o', type=str, default='./tmp/daily_gaps.txt',
                       help='导出文件路径')
    args = parser.parse_args()
    
    stock_db = get_db_path()
    if not stock_db:
        logger.error("未找到股票数据库配置")
        sys.exit(1)
    
    print(f"数据库: {stock_db}")
    
    if args.export:
        gaps = export_gaps(args.output)
        print(f"\n缺失统计:")
        print(f"  交易日: {gaps['date_count']} 个")
        print(f"  记录数: {gaps['record_count']} 条")
        print(f"\n清单已导出到: {args.output}")
        return
    
    if args.mode == 'api':
        # 从 API 获取
        if args.dates:
            dates = args.dates.split(',')
        else:
            gaps = export_gaps()
            dates = gaps['dates']
        
        stats = fetch_from_api(dates, args.dry_run)
        print(f"\nAPI 获取结果:")
        print(f"  获取记录: {stats['fetched']}")
        print(f"  插入记录: {stats['inserted']}")
        print(f"  跳过日期: {stats['skipped']}")
        if stats['errors']:
            print(f"  错误数: {len(stats['errors'])}")
            
    elif args.mode == 'bak':
        # 从 bak_daily 补充
        stats = supplement_from_bak(args.dry_run)
        print(f"\nbak_daily 补充结果:")
        print(f"  插入记录: {stats['inserted']}")
        
    elif args.mode == 'both':
        # 先 API，再 bak
        gaps = export_gaps()
        
        print("步骤1: 从 API 获取...")
        api_stats = fetch_from_api(gaps['dates'], args.dry_run)
        
        print("\n步骤2: 从 bak_daily 补充剩余...")
        bak_stats = supplement_from_bak(args.dry_run)
        
        print(f"\n总结:")
        print(f"  API 插入: {api_stats['inserted']}")
        print(f"  BAK 补充: {bak_stats['inserted']}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
