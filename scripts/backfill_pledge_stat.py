"""
pledge_stat 数据补全脚本
1. 填补中间缺失的周五
2. 补全更早的历史数据

使用方法: python scripts/backfill_pledge_stat.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.tushare_duckdb.config import PRO_API, API_CONFIG
from src.tushare_duckdb.utils import get_connection, init_table, table_exists
from src.tushare_duckdb.storage import DuckDBStorage
from src.tushare_duckdb.logger import logger


def get_all_fridays_from_calendar(basic_db_path, start_date='20180101', end_date=None):
    """从交易日历获取所有周五交易日"""
    from datetime import datetime
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    with get_connection(basic_db_path, read_only=True) as conn:
        query = """
            SELECT cal_date 
            FROM trade_cal 
            WHERE cal_date >= ? 
              AND cal_date <= ?
              AND exchange = 'SSE'
              AND is_open = '1'
              AND dayofweek(strptime(cal_date, '%Y%m%d')) = 5
            ORDER BY cal_date
        """
        result = conn.execute(query, [start_date, end_date]).fetchall()
        return [r[0] for r in result]


def fetch_for_date(end_date, fields, limit=3000):
    """获取指定日期的完整数据（分页）"""
    all_dfs = []
    offset = 0
    
    while True:
        try:
            df = PRO_API.pledge_stat(end_date=end_date, fields=fields, limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"API 失败 ({end_date}, offset={offset}): {e}")
            break
        
        if df is None or df.empty:
            break
        
        # 只保留该日期的数据
        df_date = df[df['end_date'] == end_date]
        if not df_date.empty:
            all_dfs.append(df_date)
        
        if len(df) < limit:
            break
        offset += limit
        
        if offset >= 100000:
            break
    
    if not all_dfs:
        return pd.DataFrame()
    
    return pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=['ts_code', 'end_date'])


def backfill_pledge_stat():
    """补全 pledge_stat 数据：填补缺失 + 补全历史"""
    
    config = API_CONFIG['reference']['tables']['pledge_stat']
    db_path = API_CONFIG['reference']['db_path']
    basic_db_path = API_CONFIG['stock_events']['db_path']
    table_name = 'pledge_stat'
    fields = ','.join(config['fields'])
    unique_keys = config['unique_keys']
    limit = config.get('limit', 3000)
    earliest_date = config.get('earliest_date', '20180101')
    
    logger.info("=" * 60)
    logger.info("pledge_stat 数据补全脚本")
    logger.info(f"数据库: {db_path}")
    logger.info("=" * 60)
    
    # 获取所有周五
    all_fridays = get_all_fridays_from_calendar(basic_db_path, earliest_date)
    logger.info(f"交易日历中共 {len(all_fridays)} 个周五 ({earliest_date} ~ 今)")
    
    with get_connection(db_path) as conn:
        if not table_exists(conn, table_name):
            init_table(conn, table_name, config)
        storage = DuckDBStorage(conn)
        
        # 获取本地已有的周五
        result = conn.execute(f"SELECT DISTINCT end_date FROM {table_name} ORDER BY end_date").fetchall()
        local_dates = set(r[0] for r in result)
        logger.info(f"本地已有 {len(local_dates)} 个周五的数据")
        
        # 找出缺失的周五
        missing_fridays = [f for f in all_fridays if f not in local_dates]
        logger.info(f"缺失 {len(missing_fridays)} 个周五")
        
        if not missing_fridays:
            logger.info("无缺失数据，补全完成！")
            return
        
        # 按日期倒序获取（从最新到最早）
        missing_fridays.sort(reverse=True)
        
        total_stored = 0
        failed_dates = []
        batch_size = 20  # 每 20 个周五批量存储一次
        batch_dfs = []
        
        for i, friday in enumerate(missing_fridays):
            logger.info(f"[{i+1}/{len(missing_fridays)}] 获取 {friday} ...")
            
            df = fetch_for_date(friday, fields, limit)
            
            if df.empty:
                logger.warning(f"{friday}: 无数据")
                failed_dates.append(friday)
            else:
                batch_dfs.append(df)
                logger.info(f"{friday}: 获取 {len(df)} 条")
            
            # 批量存储
            if len(batch_dfs) >= batch_size or (i == len(missing_fridays) - 1 and batch_dfs):
                combined = pd.concat(batch_dfs, ignore_index=True)
                combined = combined.drop_duplicates(subset=['ts_code', 'end_date'])
                
                stored = storage.store_data(
                    table_name, combined, unique_keys,
                    date_column='end_date',
                    storage_mode='insert_new',
                    api_config_entry=config
                )
                
                new_stored = stored if stored > 0 else 0
                total_stored += new_stored
                logger.info(f"=== 批量存储: {len(batch_dfs)} 周, {len(combined)} 条, 新增 {new_stored} 条 ===")
                batch_dfs = []
        
        # 最终统计
        stats = conn.execute(f"""
            SELECT COUNT(*), MIN(end_date), MAX(end_date), COUNT(DISTINCT end_date)
            FROM {table_name}
        """).fetchone()
        
        logger.info("\n" + "=" * 60)
        logger.info("补全结束")
        logger.info(f"处理周五: {len(missing_fridays)} 个")
        logger.info(f"新增记录: {total_stored} 条")
        logger.info(f"表总记录: {stats[0]} 条, {stats[3]} 周")
        logger.info(f"日期范围: {stats[1]} ~ {stats[2]}")
        if failed_dates:
            logger.warning(f"无数据的日期: {len(failed_dates)} 个")
        logger.info("=" * 60)


if __name__ == '__main__':
    backfill_pledge_stat()
