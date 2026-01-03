import time
import pandas as pd
from .utils import get_columns
from .metadata import update_metadata
from .logger import logger

class DuckDBStorage:
    def __init__(self, conn):
        self.conn = conn

    def store_data(self, table_name, df, unique_keys, date_column='trade_date', storage_mode='insert_new',
                           overwrite_start_date=None, overwrite_end_date=None, ts_code=None, api_config_entry=None):
        if df.empty:
            logger.info(f"{table_name}: 空数据，无需存储")
            return 0
        logger.debug(
            f"{table_name}: 接收参数: date_column={date_column}, overwrite_start_date={overwrite_start_date}, overwrite_end_date={overwrite_end_date}, storage_mode={storage_mode}")

        target_columns, _, _ = get_columns(self.conn, table_name)
        if not target_columns:
            return -1
        # logger.debug(f"{table_name}: 数据库表列: {target_columns}")

        processed_df = df.copy()
        
        # === 新增：字段映射支持（解决 dc_index.leading → leading_stock）===
        if api_config_entry:
            field_mappings = api_config_entry.get('field_mappings', {})
            if field_mappings:
                logger.info(f"{table_name}: 应用字段映射: {field_mappings}")
                target_columns, _, _ = get_columns(self.conn, table_name)
                # 安全检查
                missing = [v for k, v in field_mappings.items() if v not in target_columns]
                if missing:
                    logger.error(f"{table_name}: 错误！映射目标列不存在: {missing}")
                    return -1
                rename_dict = {k: v for k, v in field_mappings.items() if k in df.columns}
                if rename_dict:
                    processed_df = processed_df.rename(columns=rename_dict)
                    logger.info(f"{table_name}: 字段重命名成功: {rename_dict}")
        # === 映射结束 ===

        if date_column in processed_df.columns:
            # 统一日期格式化，增强健壮性
            processed_df[date_column] = pd.to_datetime(processed_df[date_column], errors='coerce').dt.strftime('%Y%m%d')
            # === 新增：过滤 NULL ===
            null_count = processed_df[date_column].isnull().sum()
            if null_count > 0:
                logger.warning(f"{table_name}: 发现 {null_count} 条日期为 NULL，自动丢弃")
                processed_df = processed_df.dropna(subset=[date_column])
            if processed_df.empty:
                logger.warning(f"{table_name}: 过滤后为空，跳过存储")
                return 0

        temp_view_name = f"temp_view_{table_name}_{int(time.time() * 1000)}"
        try:
            self.conn.register(temp_view_name, processed_df)
            logger.debug(f"{table_name}: 注册 {len(processed_df)} 行到临时视图 '{temp_view_name}'。")
        except Exception as e:
            logger.error(f"{table_name}: 注册临时视图失败: {e}")
            return -1

        try:
            # === 1. replace 模式：先删除范围内的数据 ===
            if storage_mode == 'replace' and overwrite_start_date and overwrite_end_date:
                delete_query = f"DELETE FROM \"{table_name}\" WHERE \"{date_column}\" BETWEEN '{overwrite_start_date}' AND '{overwrite_end_date}'"
                current_count_query = f"SELECT COUNT(*) FROM \"{table_name}\" WHERE \"{date_column}\" BETWEEN '{overwrite_start_date}' AND '{overwrite_end_date}'"

                if ts_code:
                    delete_query += f" AND ts_code = '{ts_code}'"
                    current_count_query += f" AND ts_code = '{ts_code}'"

                current_count = self.conn.execute(current_count_query).fetchone()[0]
                logger.info(
                    f"{table_name}: 准备删除日期范围 {overwrite_start_date} - {overwrite_end_date} 的记录，当前记录数: {current_count}")
                if ts_code:
                    logger.info(f"  (限定 ts_code={ts_code})")
                self.conn.execute(delete_query)
                logger.info(f"{table_name}: 删除日期范围记录执行完成")

            elif storage_mode == 'replace':
                current_count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
                logger.info(f"{table_name}: 准备删除所有记录，当前记录数: {current_count}")
                self.conn.execute(f"DELETE FROM \"{table_name}\"")
                logger.info(f"{table_name}: 删除所有记录执行完成")

            # === 2. 插入数据 ===
            columns_str = ", ".join([f'"{col}"' for col in processed_df.columns])

            if storage_mode == 'insert_new':
                before_count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]

                # 构建主键去重条件
                unique_conditions = " AND ".join(
                    f"m.\"{k}\" = t.\"{k}\"" for k in unique_keys
                )
                insert_query = f"""
                    INSERT INTO "{table_name}" ({columns_str})
                    SELECT {columns_str} FROM "{temp_view_name}" t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM "{table_name}" m
                        WHERE {unique_conditions}
                    )
                """
                self.conn.execute(insert_query)
                after_count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
                inserted_count = after_count - before_count
                logger.info(f"{table_name}: 实际插入 {inserted_count} 条新记录（NOT EXISTS 去重后）")
            else:
                # replace 模式：直接插入
                insert_query = f"""
                    INSERT INTO "{table_name}" ({columns_str})
                    SELECT {columns_str} FROM "{temp_view_name}"
                """
                self.conn.execute(insert_query)
                inserted_count = len(processed_df)
                logger.info(f"{table_name}: 插入 {inserted_count} 条记录（覆盖模式）")

            # === 3. 更新元数据 ===
            update_metadata(self.conn, table_name, date_column)
            logger.info(f"{table_name}: 元数据更新完成")
            return inserted_count

        except Exception as e:
            logger.error(f"{table_name}: 数据存储失败: {e}")
            return -1
        finally:
            try:
                self.conn.execute(f"UNREGISTER {temp_view_name}")
                logger.debug(f"{table_name}: 临时视图 {temp_view_name} 已注销")
            except Exception:
                pass
