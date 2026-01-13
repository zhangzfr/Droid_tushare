"""
pledge_stat 数据补全脚本
采用迭代方式获取全部历史数据

使用方法: python scripts/backfill_pledge_stat.py
"""
import os
import sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tushare_duckdb.config import PRO_API, API_CONFIG
from src.tushare_duckdb.utils import get_connection, init_table, table_exists
from src.tushare_duckdb.storage import DuckDBStorage
from src.tushare_duckdb.logger import logger


def backfill_pledge_stat():
    """迭代获取 pledge_stat 全部数据"""
    
    config = API_CONFIG['reference']['tables']['pledge_stat']
    db_path = API_CONFIG['reference']['db_path']
    table_name = 'pledge_stat'
    fields = config['fields']
    unique_keys = config['unique_keys']
    limit = config.get('limit', 3000)
    
    total_fetched = 0
    total_stored = 0
    iteration = 0
    
    logger.info("=" * 60)
    logger.info("pledge_stat 数据补全脚本启动")
    logger.info(f"数据库: {db_path}")
    logger.info(f"单次限额: {limit}")
    logger.info("=" * 60)
    
    with get_connection(db_path) as conn:
        # 确保表存在
        if not table_exists(conn, table_name):
            init_table(conn, table_name, config)
        storage = DuckDBStorage(conn)
        
        while True:
            iteration += 1
            
            # 获取本地最小日期
            try:
                result = conn.execute(f"SELECT MIN(end_date) FROM {table_name}").fetchone()
                local_min_date = result[0] if result and result[0] else None
            except Exception:
                local_min_date = None
            
            logger.info(f"\n=== 第 {iteration} 轮 ===")
            logger.info(f"本地最小日期: {local_min_date or '无数据'}")
            
            # 构建 API 参数
            params = {'fields': ','.join(fields)}
            if local_min_date:
                # 关键修复：使用 min_date - 1 天作为下次查询的 end_date
                # 这样才能获取更早的数据，而不是重复获取相同数据
                prev_date = datetime.strptime(local_min_date, '%Y%m%d') - timedelta(days=1)
                query_end_date = prev_date.strftime('%Y%m%d')
                params['end_date'] = query_end_date
                logger.info(f"查询 end_date: {query_end_date} (本地最小日期 - 1 天)")
            
            # 分页获取
            offset = 0
            round_total = 0
            round_stored = 0
            
            while True:
                logger.info(f"获取中... offset={offset}")
                
                try:
                    df = PRO_API.pledge_stat(**params, limit=limit, offset=offset)
                except Exception as e:
                    logger.error(f"API 调用失败: {e}")
                    break
                
                if df is None or df.empty:
                    logger.info("本轮无更多数据")
                    break
                
                fetched = len(df)
                round_total += fetched
                
                # 存储数据
                stored = storage.store_data(
                    table_name, df, unique_keys,
                    date_column='end_date',
                    storage_mode='insert_new',
                    api_config_entry=config
                )
                round_stored += stored if stored > 0 else 0
                logger.info(f"获取 {fetched} 条, 新增存储 {stored} 条")
                
                if fetched < limit:
                    logger.info(f"数据行数 {fetched} < {limit}, 本批次结束")
                    break
                    
                offset += limit
                
                # Tushare offset 限制 100000
                if offset >= 100000:
                    logger.warning("达到 offset 上限 100000，切换到下一轮")
                    break
            
            total_fetched += round_total
            logger.info(f"第 {iteration} 轮完成: 获取 {round_total} 条, 新增 {round_stored} 条")
            
            # 终止条件: 本轮无新数据
            if round_total == 0:
                logger.info("\n获取到 0 行数据，补全完成！")
                break
            
            # 安全检查: 防止无限循环
            if iteration > 100:
                logger.warning("迭代次数超过 100，强制停止")
                break
        
        # 获取统计信息
        try:
            stats = conn.execute(f"""
                SELECT COUNT(*) as total, 
                       MIN(end_date) as earliest, 
                       MAX(end_date) as latest
                FROM {table_name}
            """).fetchone()
            
            logger.info("\n" + "=" * 60)
            logger.info("补全结束 - 数据统计")
            logger.info(f"总迭代: {iteration} 轮")
            logger.info(f"本次获取: {total_fetched} 条")
            logger.info(f"表总记录: {stats[0]} 条")
            logger.info(f"日期范围: {stats[1]} ~ {stats[2]}")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"统计查询失败: {e}")


if __name__ == '__main__':
    backfill_pledge_stat()
