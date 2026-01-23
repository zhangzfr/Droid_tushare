#!/usr/bin/env python3
"""
moneyflow_hsgt 沪深港通资金流向历史数据补全脚本

使用方法:
    # 补全全部历史数据 (从2014年11月17日开始)
    python scripts/backfill_moneyflow_hsgt.py
    
    # 补全指定日期范围
    python scripts/backfill_moneyflow_hsgt.py --start 20240101 --end 20240131
    
    # 仅显示计划(不实际获取)
    python scripts/backfill_moneyflow_hsgt.py --dry-run
"""
import os
import sys
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.tushare_duckdb.config import PRO_API, API_CONFIG
from src.tushare_duckdb.utils import get_connection, init_table, table_exists
from src.tushare_duckdb.storage import DuckDBStorage
from src.tushare_duckdb.logger import logger


def get_trade_dates_from_calendar(basic_db_path, start_date, end_date):
    """从交易日历获取交易日列表"""
    with get_connection(basic_db_path, read_only=True) as conn:
        query = """
            SELECT cal_date 
            FROM trade_cal 
            WHERE cal_date >= ? 
              AND cal_date <= ?
              AND exchange = 'SSE'
              AND is_open = '1'
            ORDER BY cal_date
        """
        result = conn.execute(query, [start_date, end_date]).fetchall()
        return [r[0] for r in result]


def fetch_data_for_range(start_date, end_date, fields):
    """获取指定日期范围的数据"""
    try:
        df = PRO_API.moneyflow_hsgt(
            start_date=start_date,
            end_date=end_date,
            fields=fields
        )
        if df is not None and not df.empty:
            return df
    except Exception as e:
        logger.error(f"API 请求失败 ({start_date} ~ {end_date}): {e}")
    return pd.DataFrame()


def backfill_moneyflow_hsgt(start_date=None, end_date=None, dry_run=False):
    """补全 moneyflow_hsgt 数据"""
    
    config = API_CONFIG['moneyflow']['tables']['moneyflow_hsgt']
    db_path = API_CONFIG['moneyflow']['db_path']
    basic_db_path = API_CONFIG['stock']['db_path']  # trade_cal 在 stock db 中
    table_name = 'moneyflow_hsgt'
    fields = ','.join(config['fields'])
    unique_keys = config['unique_keys']
    earliest_date = config.get('earliest_date', '20141117')
    
    # 设置日期范围
    if not start_date:
        start_date = earliest_date
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
    
    logger.info("=" * 60)
    logger.info("moneyflow_hsgt 沪深港通资金流向数据补全脚本")
    logger.info(f"数据库: {db_path}")
    logger.info(f"日期范围: {start_date} ~ {end_date}")
    if dry_run:
        logger.info("模式: DRY RUN (仅显示计划)")
    logger.info("=" * 60)
    
    with get_connection(db_path) as conn:
        # 初始化表结构
        if not table_exists(conn, table_name):
            logger.info(f"表 {table_name} 不存在，正在创建...")
            init_table(conn, table_name, config)
        
        storage = DuckDBStorage(conn)
        
        # 获取本地已有日期
        try:
            result = conn.execute(f"SELECT DISTINCT trade_date FROM {table_name} ORDER BY trade_date").fetchall()
            local_dates = set(r[0] for r in result)
            logger.info(f"本地已有 {len(local_dates)} 个交易日的数据")
        except:
            local_dates = set()
            logger.info("本地无数据")
        
        # 获取所有交易日
        all_trade_dates = get_trade_dates_from_calendar(basic_db_path, start_date, end_date)
        logger.info(f"交易日历中共 {len(all_trade_dates)} 个交易日")
        
        # 找出缺失的日期
        missing_dates = [d for d in all_trade_dates if d not in local_dates]
        logger.info(f"缺失 {len(missing_dates)} 个交易日的数据")
        
        if not missing_dates:
            logger.info("无缺失数据，补全完成！")
            return
        
        if dry_run:
            logger.info(f"\n[DRY RUN] 将获取以下日期范围:")
            logger.info(f"  开始: {missing_dates[0]}")
            logger.info(f"  结束: {missing_dates[-1]}")
            logger.info(f"  共 {len(missing_dates)} 个交易日")
            return
        
        # 分批获取数据 (每批30天，约22个交易日，低于300条限制)
        batch_size_days = 30
        total_stored = 0
        failed_ranges = []
        
        # 按时间顺序处理
        missing_dates.sort()
        
        i = 0
        while i < len(missing_dates):
            batch_start = missing_dates[i]
            
            # 找到该批次的结束日期 (最多batch_size_days天内的日期)
            batch_start_dt = datetime.strptime(batch_start, '%Y%m%d')
            batch_end_dt = batch_start_dt + timedelta(days=batch_size_days)
            batch_end = batch_end_dt.strftime('%Y%m%d')
            
            # 找到实际批次范围内的最后一个缺失日期
            batch_dates = []
            j = i
            while j < len(missing_dates) and missing_dates[j] <= batch_end:
                batch_dates.append(missing_dates[j])
                j += 1
            
            if not batch_dates:
                i += 1
                continue
            
            actual_start = batch_dates[0]
            actual_end = batch_dates[-1]
            
            logger.info(f"[{i+1}/{len(missing_dates)}] 获取 {actual_start} ~ {actual_end} ({len(batch_dates)} 日)...")
            
            df = fetch_data_for_range(actual_start, actual_end, fields)
            
            if df.empty:
                logger.warning(f"  {actual_start} ~ {actual_end}: 无数据")
                failed_ranges.append((actual_start, actual_end))
            else:
                df = df.drop_duplicates(subset=['trade_date'])
                
                stored = storage.store_data(
                    table_name, df, unique_keys,
                    date_column='trade_date',
                    storage_mode='insert_new',
                    api_config_entry=config
                )
                
                new_stored = stored if stored > 0 else 0
                total_stored += new_stored
                logger.info(f"  获取 {len(df)} 条, 新增 {new_stored} 条")
            
            i = j  # 跳到下一个未处理的日期
        
        # 最终统计
        try:
            stats = conn.execute(f"""
                SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
                FROM {table_name}
            """).fetchone()
            
            logger.info("\n" + "=" * 60)
            logger.info("补全结束")
            logger.info(f"新增记录: {total_stored} 条")
            logger.info(f"表总记录: {stats[0]} 条")
            logger.info(f"日期范围: {stats[1]} ~ {stats[2]}")
            if failed_ranges:
                logger.warning(f"无数据的范围: {len(failed_ranges)} 个")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='moneyflow_hsgt 沪深港通资金流向历史数据补全脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--start', '-s',
        type=str,
        default=None,
        help='开始日期 (YYYYMMDD)，默认从2014年11月17日开始'
    )
    
    parser.add_argument(
        '--end', '-e',
        type=str,
        default=None,
        help='结束日期 (YYYYMMDD)，默认为今天'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅显示计划，不实际获取数据'
    )
    
    args = parser.parse_args()
    
    backfill_moneyflow_hsgt(
        start_date=args.start,
        end_date=args.end,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
