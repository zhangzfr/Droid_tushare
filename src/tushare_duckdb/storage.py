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

        # === Finance Pre-processing Hook ===
        # 针对财务数据的特殊清洗逻辑
        # 判断依据：config category='finance' (但这里没直接传 category)，或者根据 table_name 判断
        # 简单起见，如果 DataFrame 同时包含 ann_date 和 end_date，且 unique_keys 包含它们，就认为是财务表逻辑适用
        # 或者更明确：检查 api_config_entry
        if api_config_entry and 'ann_date' in unique_keys and 'end_date' in unique_keys:
             if 'ann_date' in processed_df.columns:
                 # 1. 尝试用 f_ann_date 填充
                 if 'f_ann_date' in processed_df.columns:
                     mask = processed_df['ann_date'].isna() | (processed_df['ann_date'] == '')
                     processed_df.loc[mask, 'ann_date'] = processed_df.loc[mask, 'f_ann_date']
                 
                 # 2. 尝试用 end_date 填充
                 if 'end_date' in processed_df.columns:
                     mask = processed_df['ann_date'].isna() | (processed_df['ann_date'] == '')
                     processed_df.loc[mask, 'ann_date'] = processed_df.loc[mask, 'end_date']
                 
                 # 3. 仍然为空则丢弃
                 mask = processed_df['ann_date'].isna() | (processed_df['ann_date'] == '')
                 if mask.any():
                     drop_count = mask.sum()
                     logger.warning(f"{table_name}: 发现 {drop_count} 条 ann_date 缺失且无法填充，已丢弃")
                     processed_df = processed_df[~mask]
                     
                 if processed_df.empty:
                     logger.warning(f"{table_name}: 清洗后为空，跳过存储")
                     return 0

             # 4. 确保 update_flag 存在
             if 'update_flag' in unique_keys:
                 if 'update_flag' not in processed_df.columns:
                     processed_df['update_flag'] = '0'
                 else:
                     processed_df['update_flag'] = processed_df['update_flag'].fillna('0').astype(str)
        # === End Finance Hook ===

        # === Moneyflow ts_code Fill Hook ===
        # Fix missing ts_code for moneyflow_cnt_ths based on name mapping
        if table_name == 'moneyflow_cnt_ths':
            # Known concept boards without ts_code in API response
            TS_CODE_MAPPING = {
                '蚂蚁集团概念': '885749.TI',
                '2025年报预增': '886107.TI',
            }
            
            if 'ts_code' in processed_df.columns and 'name' in processed_df.columns:
                # Find rows with missing ts_code
                mask = processed_df['ts_code'].isna() | (processed_df['ts_code'] == '')
                
                if mask.any():
                    missing_count = mask.sum()
                    # Fill from mapping
                    processed_df.loc[mask, 'ts_code'] = processed_df.loc[mask, 'name'].map(TS_CODE_MAPPING)
                    
                    # Check if still missing after mapping
                    still_missing = processed_df['ts_code'].isna() | (processed_df['ts_code'] == '')
                    filled_count = missing_count - still_missing.sum()
                    
                    if filled_count > 0:
                        logger.info(f"{table_name}: 通过 name 映射填充了 {filled_count} 条缺失的 ts_code")
                    
                    # Drop rows that still have missing ts_code after mapping
                    if still_missing.any():
                        unknown_names = processed_df.loc[still_missing, 'name'].unique().tolist()
                        logger.warning(f"{table_name}: 发现未知 name 的 ts_code 缺失: {unknown_names}, 已丢弃 {still_missing.sum()} 条")
                        processed_df = processed_df[~still_missing]
                
                if processed_df.empty:
                    logger.warning(f"{table_name}: 清洗后为空，跳过存储")
                    return 0
        # === End Moneyflow Hook ===

        # === 核心逻辑：日期格式归一化 (YYYY-MM-DD -> YYYYMMDD) ===
        # 根据 api_config_entry['date_columns'] 列表进行批量洗数
        date_cols_to_fix = api_config_entry.get('date_columns', [])
        # 兼容旧逻辑：如果只配了 date_column，也要处理
        if date_column and date_column not in date_cols_to_fix:
             date_cols_to_fix.append(date_column)
        
        for col in date_cols_to_fix:
            if col in processed_df.columns: # Use processed_df here
                try:
                    target_fmt = '%Y%m%d'
                    parse_fmt = None
                    if api_config_entry and api_config_entry.get('api_date_format') == 'YYYYMM':
                        target_fmt = '%Y%m'
                        parse_fmt = '%Y%m'
                    
                    # 统一转为 datetime 再转回目标格式字符串
                    # errors='coerce' 会将无法解析的变成 NaT，fillna('') 变为空字符串
                    processed_df[col] = pd.to_datetime(processed_df[col], format=parse_fmt, errors='coerce').dt.strftime(target_fmt).fillna('')
                except Exception as e:
                    logger.warning(f"列 {col} 日期格式化失败: {e}")

        # 确保日期列格式正确 (旧逻辑保留作为兜底)
        if date_column and date_column in processed_df.columns:
             # date_cols_to_fix 已经处理过了，这里可能是多余的，但为了安全保留或做最后的检查
             # 因为上面已经转成了 YYYYMMDD string，这里如果再 to_datetime 可能没必要，
             # 但 storage 后面如果依赖类型... DuckDB 插入时 string 'YYYYMMDD' 对应 date 类型是没问题的 (ISO format prefer YYYY-MM-DD but DuckDB handles YYYYMMDD usually if configured? No wait. DuckDB DATE type usually expects YYYY-MM-DD or strict ISO. 
             # Wait, Tushare standard here is YYYYMMDD strings in DB? 
             # Looking at other tables: earliest_date: '19900101', date_column: trade_date.
             # If the DB column is VARCHAR, YYYYMMDD is fine. If DATA, it might need casting.
             # In `utils.py` `get_all_dates` works with YYYYMMDD. 
             # Let's assume the project standard IS YYYYMMDD string for storage or at least consistency.
             # The user explicitly asked: "ensure入库数据全为 YYYYMMDD 字符串".
             pass

        # === 新增：过滤 NULL ===
        # This block should apply to the primary date_column after all formatting
        if date_column in processed_df.columns:
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
            
            before_count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]

            if storage_mode == 'insert_new':

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
                after_count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
                net_change = after_count - before_count
                inserted_count = len(processed_df)
                logger.info(f"{table_name}: 插入 {inserted_count} 条记录（覆盖模式，净新增 {net_change} 条）")

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
