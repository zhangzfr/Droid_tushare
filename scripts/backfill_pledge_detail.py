"""
pledge_detail 数据补全脚本
支持三种模式：
  默认模式：只获取新增股票的数据
  --force：强制重新获取所有股票数据
  --smart：智能模式，只获取质押次数有变化的股票

使用方法:
  python scripts/backfill_pledge_detail.py           # 默认：只获取新股票
  python scripts/backfill_pledge_detail.py --force   # 强制全量更新
  python scripts/backfill_pledge_detail.py --smart   # 智能更新（质押次数变化）
"""
import os
import sys
import time
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.tushare_duckdb.config import PRO_API, API_CONFIG
from src.tushare_duckdb.utils import get_connection, init_table, table_exists
from src.tushare_duckdb.storage import DuckDBStorage
from src.tushare_duckdb.logger import logger


def fetch_detail_for_stock(ts_code, fields, limit=1000):
    """获取单个股票的质押明细（分页）"""
    all_dfs = []
    offset = 0
    
    while True:
        try:
            df = PRO_API.pledge_detail(ts_code=ts_code, fields=fields, limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"API 失败 ({ts_code}, offset={offset}): {e}")
            return pd.DataFrame()
        
        if df is None or df.empty:
            break
        
        all_dfs.append(df)
        
        if len(df) < limit:
            break
        offset += limit
        
        if offset >= 10000:
            break
    
    if not all_dfs:
        return pd.DataFrame()
    
    return pd.concat(all_dfs, ignore_index=True)


def get_stocks_to_update(conn, mode='default'):
    """根据模式获取需要更新的股票列表"""
    
    # 从 pledge_stat 获取所有 ts_code 和最新的质押次数
    result = conn.execute("""
        SELECT ts_code, MAX(pledge_count) as latest_count 
        FROM pledge_stat 
        GROUP BY ts_code 
        ORDER BY ts_code
    """).fetchall()
    stat_data = {r[0]: r[1] for r in result}
    all_ts_codes = list(stat_data.keys())
    logger.info(f"pledge_stat 中共 {len(all_ts_codes)} 个股票")
    
    # 获取本地已有的 ts_code 和记录数
    try:
        existing = conn.execute("""
            SELECT ts_code, COUNT(*) as cnt 
            FROM pledge_detail 
            GROUP BY ts_code
        """).fetchall()
        detail_counts = {r[0]: r[1] for r in existing}
        logger.info(f"pledge_detail 中已有 {len(detail_counts)} 个股票")
    except Exception:
        detail_counts = {}
    
    if mode == 'force':
        # 强制模式：更新所有股票
        logger.info("强制模式：将更新所有股票")
        return all_ts_codes, 'replace'
    
    elif mode == 'smart':
        # 智能模式：只更新质押次数有变化的股票
        changed_codes = []
        for ts_code in all_ts_codes:
            stat_count = stat_data.get(ts_code, 0) or 0
            detail_count = detail_counts.get(ts_code, 0)
            # 如果质押次数 > 本地记录数，可能有新增
            if stat_count > detail_count:
                changed_codes.append(ts_code)
        logger.info(f"智能模式：{len(changed_codes)} 个股票的质押次数有变化")
        return changed_codes, 'insert_new'
    
    else:
        # 默认模式：只获取新股票
        missing_codes = [c for c in all_ts_codes if c not in detail_counts]
        logger.info(f"默认模式：{len(missing_codes)} 个新股票")
        return missing_codes, 'insert_new'


def backfill_pledge_detail(mode='default'):
    """补全 pledge_detail 数据"""
    
    config = API_CONFIG['reference']['tables']['pledge_detail']
    db_path = API_CONFIG['reference']['db_path']
    table_name = 'pledge_detail'
    fields = ','.join(config['fields'])
    unique_keys = config['unique_keys']
    limit = config.get('limit', 1000)
    
    mode_desc = {'default': '默认（新股票）', 'force': '强制全量', 'smart': '智能更新'}
    
    logger.info("=" * 60)
    logger.info(f"pledge_detail 数据补全脚本 - {mode_desc.get(mode, mode)}")
    logger.info(f"数据库: {db_path}")
    logger.info("=" * 60)
    
    with get_connection(db_path) as conn:
        if not table_exists(conn, table_name):
            init_table(conn, table_name, config)
        storage = DuckDBStorage(conn)
        
        # 根据模式获取需要更新的股票
        stocks_to_update, storage_mode = get_stocks_to_update(conn, mode)
        
        if not stocks_to_update:
            logger.info("无需更新，补全完成！")
            return
        
        # 强制模式下，先删除这些股票的旧数据
        if mode == 'force':
            logger.info("强制模式：清理旧数据...")
            # 分批删除避免 SQL 过长
            batch_size = 500
            for i in range(0, len(stocks_to_update), batch_size):
                batch = stocks_to_update[i:i+batch_size]
                placeholders = ','.join([f"'{c}'" for c in batch])
                conn.execute(f"DELETE FROM {table_name} WHERE ts_code IN ({placeholders})")
            logger.info("旧数据清理完成")
        
        total_stored = 0
        batch_size = 50
        batch_dfs = []
        api_call_count = 0
        
        for i, ts_code in enumerate(stocks_to_update):
            # API 限流控制
            api_call_count += 1
            if api_call_count >= 350:
                logger.info("=== API 限流：休息 60 秒 ===")
                time.sleep(60)
                api_call_count = 0
            
            df = fetch_detail_for_stock(ts_code, fields, limit)
            
            if not df.empty:
                batch_dfs.append(df)
                if (i + 1) % 100 == 0:
                    logger.info(f"[{i+1}/{len(stocks_to_update)}] {ts_code}: {len(df)} 条")
            
            # 批量存储
            if len(batch_dfs) >= batch_size or (i == len(stocks_to_update) - 1 and batch_dfs):
                combined = pd.concat(batch_dfs, ignore_index=True)
                combined = combined.drop_duplicates(subset=unique_keys)
                
                # 过滤掉主键字段为空的记录
                original_len = len(combined)
                combined = combined.dropna(subset=['ts_code', 'ann_date', 'holder_name', 'pledge_amount'])
                if len(combined) < original_len:
                    logger.warning(f"过滤掉 {original_len - len(combined)} 条主键字段为空的记录")
                
                if not combined.empty:
                    stored = storage.store_data(
                        table_name, combined, unique_keys,
                        date_column='ann_date',
                        storage_mode='insert_new',
                        api_config_entry=config
                    )
                    new_stored = stored if stored > 0 else 0
                    total_stored += new_stored
                    logger.info(f"=== 批量存储: {len(batch_dfs)} 股, {len(combined)} 条, 新增 {new_stored} 条 ===")
                
                batch_dfs = []
            
            # 进度
            if (i + 1) % 500 == 0:
                logger.info(f"--- 进度: {i+1}/{len(stocks_to_update)}, 累计新增 {total_stored} 条 ---")
        
        # 最终统计
        stats = conn.execute(f"""
            SELECT COUNT(*), MIN(ann_date), MAX(ann_date), COUNT(DISTINCT ts_code)
            FROM {table_name}
        """).fetchone()
        
        logger.info("\n" + "=" * 60)
        logger.info("补全结束")
        logger.info(f"处理股票: {len(stocks_to_update)} 个")
        logger.info(f"新增记录: {total_stored} 条")
        logger.info(f"表总记录: {stats[0]} 条")
        logger.info(f"覆盖股票: {stats[3]} 个")
        logger.info(f"日期范围: {stats[1]} ~ {stats[2]}")
        logger.info("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pledge_detail 数据补全脚本')
    parser.add_argument('--force', action='store_true', help='强制全量更新所有股票')
    parser.add_argument('--smart', action='store_true', help='智能更新质押次数变化的股票')
    args = parser.parse_args()
    
    if args.force:
        mode = 'force'
    elif args.smart:
        mode = 'smart'
    else:
        mode = 'default'
    
    backfill_pledge_detail(mode)
