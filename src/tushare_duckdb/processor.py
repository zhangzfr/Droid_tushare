import pandas as pd
from .utils import generate_param_grid, build_api_params
from .metadata import update_metadata
from .fetcher import TushareFetcher
from .storage import DuckDBStorage
from .config import PRO_API
from .logger import logger

class DataProcessor:
    def __init__(self, conn, api=None):
        self.conn = conn
        self.fetcher = TushareFetcher(api)
        self.storage = DuckDBStorage(conn)

    def process_dates(self, table_name, api_config_entry, unique_keys, date_list, batch_size,
                      date_column_in_db='trade_date', ts_codes=None, force_fetch=False, overwrite=False,
                      fetch_type='range', ts_code=None):
        """处理日期批次，支持 required_params 自动遍历"""
        api_table = api_config_entry.get('api_table', table_name) or table_name
        total_stored = 0

        required_params = api_config_entry.get('required_params', {})
        # 统一通过 date_param_mode 控制获取策略（废弃 is_daily 参数）
        # date_param_mode: 'single'(默认，逐日) | 'range'(范围) | 'full_paging'(智能分页)

        param_grid = []
        if ts_codes and any(ts_codes):
            param_grid = [{'ts_code': code} for code in ts_codes if code]
        elif required_params:
            param_grid = generate_param_grid(required_params)
            logger.info(f"{table_name}: 生成参数组合，共 {len(param_grid)} 种")
        else:
            param_grid = [{}]

        current_date_display = "未开始"
        try:
            for grid_params in param_grid:
                logger.info(f"{table_name}: 处理参数组合 {grid_params}")
                current_ts_code = grid_params.get('ts_code') or ts_code
                param_str = ', '.join(f"{k}={v}" for k, v in grid_params.items())
                logger.debug(f"{table_name}: 参数组合 [{param_str or '无'}]")

                extra = {**api_config_entry.get('fixed_params', {}), **grid_params, 'config': api_config_entry}
                mode = api_config_entry.get('date_param_mode', 'single')

                if mode == 'full_paging':
                    total_stored += self._process_full_paging(table_name, api_table, api_config_entry, unique_keys, grid_params)
                elif mode == 'range':
                    # 针对 Overwrite 模式 + 多个参数组合（如多交易所）的特殊优化：
                    # 不能在循环中直接 replace，否则后一个参数会把前一个参数的数据删掉。
                    # 必须收集所有参数的数据，统一去重，然后一次性 replace。
                    if overwrite and len(param_grid) > 1:
                        # 延迟处理，先收集
                        if 'range_dfs' not in locals(): range_dfs = []
                        df = self._fetch_only_range(table_name, api_table, api_config_entry, date_list, current_ts_code, extra)
                        if df is not None and not df.empty:
                            range_dfs.append(df)
                    else:
                        # 标准流程：单次处理
                        total_stored += self._process_range(table_name, api_table, api_config_entry, unique_keys,
                                                            date_list, current_ts_code, extra, date_column_in_db, overwrite, ts_code)
                else:
                    total_stored += self._process_daily(table_name, api_table, api_config_entry, unique_keys,
                                                        date_list, current_ts_code, extra, date_column_in_db, overwrite, ts_code,
                                                        param_grid, fetch_type)

            # === Loop 结束后的批量处理 (Range + Overwrite) ===
            if mode == 'range' and overwrite and len(param_grid) > 1 and 'range_dfs' in locals() and range_dfs:
                logger.info(f"{table_name}: 检测到多参数 Range 覆盖模式，开始统一存储合并后的 {len(range_dfs)} 个数据集")
                final_df = pd.concat(range_dfs, ignore_index=True)
                # 统一调用存储（触发一次性删除 + 插入）
                # 统一调用存储（触发一次性删除 + 插入）
                request_start = date_list[0]
                request_end = date_list[-1]

                # === 针对快照表的覆盖优化 ===
                overwrite_start = request_start
                overwrite_end = request_end
                if not api_config_entry.get('requires_date', True):
                     logger.info(f"{table_name}: 检测到快照表覆盖模式 (Batch)，将执行全表删除")
                     overwrite_start = None
                     overwrite_end = None
                
                total_stored = self.storage.store_data(
                    table_name, final_df, unique_keys,
                    date_column=date_column_in_db,
                    storage_mode='replace',
                    overwrite_start_date=overwrite_start,
                    overwrite_end_date=overwrite_end,
                    ts_code=ts_code,
                    api_config_entry=api_config_entry
                )

            logger.info(f"{table_name}: 日期处理完成。本轮总共存储 {total_stored} 条。")
            return total_stored

        except Exception as e:
            logger.error(f"{table_name}: 处理失败（最后尝试日期: {current_date_display}）: {e}")
            raise
        finally:
            logger.info(f"{table_name}: 本轮处理结束")

    def _process_full_paging(self, table_name, api_table, api_config_entry, unique_keys, grid_params):
        logger.info(f"{table_name}: date_param_mode=full_paging，执行智能增量分页")
        date_col = api_config_entry.get('date_column', 'trade_date')
        
        # 获取本地最新日期
        try:
            result = self.conn.execute(f"SELECT MAX(\"{date_col}\") FROM \"{table_name}\"").fetchone()
            local_max_date = result[0] if result and result[0] else '19000101'
        except Exception:
             local_max_date = '19000101'
        
        logger.info(f"{table_name}: 本地最新 {date_col} = {local_max_date}")

        offset = 0
        limit = api_config_entry.get('limit', 12000)
        total_new = 0

        while True:
            logger.debug(f"{table_name}: 拉取 offset={offset}")
            api_params = {'limit': limit, 'offset': offset}
            api_params.update(grid_params)

            # Use fetcher logic directly here or simpler call? 
            # Generic fetcher handles retries which is good.
            # But generic fetcher consumes all pages. Here we want page by page check.
            # So we use standard API call here or modify fetcher to support this.
            # For simplicity, I'll use PRO_API directly here as in original code, 
            # OR better, use fetcher's retry logic if possible.
            # The original code did manual paging here.
            
            # Let's use the fetcher for a single page fetch if we can, but fetcher loops.
            # So we stick to direct call with simple retry logic or just direct call.
            # Original code used pro.query directly.
            
            try:
                df_page = PRO_API.query(api_table, **api_params)
            except Exception as e:
                logger.error(f"API调用失败: {e}")
                break

            if df_page is None or df_page.empty:
                logger.debug(f"{table_name}: 已到最后一页，停止")
                break

            if date_col not in df_page.columns:
                logger.error(f"{table_name}: 返回数据缺少 {date_col}，停止")
                break

            df_page[date_col] = pd.to_datetime(df_page[date_col], format='%Y%m%d', errors='coerce')
            has_new = df_page[date_col].max() > pd.to_datetime(local_max_date, format='%Y%m%d')

            if not has_new:
                logger.info(f"{table_name}: 本页数据已存在，停止拉取")
                break

            logger.info(f"{table_name}: 本页包含新数据，正在存储...")
            stored = self.storage.store_data(
                table_name, df_page, unique_keys,
                date_column=date_col,
                storage_mode='insert_new',
                api_config_entry=api_config_entry
            )
            total_new += stored
            
            # Update local_max_date to avoid re-checking strictly if we wanted, 
            # but the logic relies on max date of page.
            
            offset += limit

        update_metadata(self.conn, table_name, date_col)
        logger.info(f"{table_name}: 智能增量完成，共新增 {total_new} 条")
        return total_new

    def _fetch_only_range(self, table_name, api_table, api_config_entry, date_list, current_ts_code, extra):
        """仅执行 Range 拉取，返回 DataFrame，不存储"""
        request_start = date_list[0]
        request_end = date_list[-1]
        api_params = build_api_params(table_name, request_start, request_end, current_ts_code, extra)
        return self.fetcher.fetch_data(api_table, api_params, api_config_entry)

    def _process_range(self, table_name, api_table, api_config_entry, unique_keys, date_list, current_ts_code, extra, date_column_in_db, overwrite, ts_code):
        request_start = date_list[0]
        request_end = date_list[-1]
        logger.info(f"{table_name}: date_param_mode=range，使用范围拉取 {request_start}~{request_end}")
        
        api_params = build_api_params(table_name, request_start, request_end, current_ts_code, extra)
        df = self.fetcher.fetch_data(api_table, api_params, api_config_entry)
        
        if df is not None and not df.empty:
            storage_mode = 'replace' if overwrite else 'insert_new'
            
            # === User Requested Logic: 针对快照表的覆盖优化 ===
            overwrite_start = request_start
            overwrite_end = request_end
            if overwrite and not api_config_entry.get('requires_date', True):
                 logger.info(f"{table_name}: 检测到快照表覆盖模式 (Single)，将执行全表删除")
                 overwrite_start = None
                 overwrite_end = None
            
            return self.storage.store_data(
                table_name, df, unique_keys,
                date_column=date_column_in_db,
                storage_mode=storage_mode,
                overwrite_start_date=overwrite_start,
                overwrite_end_date=overwrite_end,
                ts_code=ts_code,
                api_config_entry=api_config_entry
            )
        return 0

    def _process_daily(self, table_name, api_table, api_config_entry, unique_keys, date_list, current_ts_code, extra, 
                       date_column_in_db, overwrite, ts_code, param_grid, fetch_type):
        logger.info(f"{table_name}: date_param_mode=single，强制逐日拉取（共 {len(date_list)} 天）")
        total_stored = 0
        
        # Batch optimization logic for overwrite
        skip_batch_delete_tables = {
            'fut_index_daily', 'index_daily', 'index_dailybasic',
            'daily', 'daily_basic', 'adj_factor',
             'opt_daily', 'cb_daily', 'fund_daily'
        }
        
        multi_code_tables = {
             'fut_index_daily', 'index_daily', 'index_dailybasic',
             'daily', 'daily_basic', 'adj_factor',
             'opt_daily', 'cb_daily', 'fund_daily'
        }

        # Case 1: Batch delete safe tables
        if param_grid and len(param_grid) > 1 and overwrite and table_name not in skip_batch_delete_tables:
            return self._batch_fetch_and_store(table_name, api_table, api_config_entry, unique_keys, date_list, 
                                               param_grid, ts_code, date_column_in_db)

        # Case 2: Multi-code tables with overwrite (Specific optimization)
        elif param_grid and len(param_grid) > 1 and overwrite and table_name in multi_code_tables:
             return self._batch_fetch_and_store_multicode(table_name, api_table, api_config_entry, unique_keys, date_list, 
                                               param_grid, ts_code, date_column_in_db)
        
        # Case 3: Standard Daily Loop
        else:
            # 判断是否需要每日打印（Snapshot 表不需要）
            needs_daily_log = api_config_entry.get('requires_date', True)
            
            for current_date in date_list:
                if needs_daily_log:
                    logger.info(f"  → 正在拉取: {current_date}")
                else:
                    logger.debug(f"  → 正在拉取(静默): {current_date}")
                    
                api_params = build_api_params(table_name, current_date, current_date, current_ts_code, extra)
                
                df = self.fetcher.fetch_data(api_table, api_params, api_config_entry)
                if df is not None and not df.empty:
                    storage_mode = 'replace' if overwrite else 'insert_new'
                    stored = self.storage.store_data(
                        table_name, df, unique_keys,
                        date_column=date_column_in_db,
                        storage_mode=storage_mode,
                        overwrite_start_date=current_date,
                        overwrite_end_date=current_date,
                        ts_code=current_ts_code,
                        api_config_entry=api_config_entry
                    )
                    if stored >= 0:
                        total_stored += stored
            return total_stored

    def _batch_fetch_and_store(self, table_name, api_table, api_config_entry, unique_keys, date_list, param_grid, ts_code, date_column_in_db):
        logger.info(f"{table_name}: 检测到多参数组合 + 覆盖模式，使用优化：全量拉取后统一删除并插入（安全表）")
        all_dfs = []
        for grid_params in param_grid:
            current_ts_code = grid_params.get('ts_code') or ts_code
            extra = {**grid_params, 'config': api_config_entry}
            
            # Fetch daily for each date (standard loop capture)
            dfs_for_grid = []
            for current_date in date_list:
                api_params = build_api_params(table_name, current_date, current_date, current_ts_code, extra)
                df = self.fetcher.fetch_data(api_table, api_params, api_config_entry)
                if df is not None and not df.empty:
                    dfs_for_grid.append(df)
            
            if dfs_for_grid:
                all_dfs.append(pd.concat(dfs_for_grid, ignore_index=True))

        if all_dfs:
            df_combined = pd.concat(all_dfs, ignore_index=True)
            # Unified delete
            delete_sql = f'DELETE FROM "{table_name}" WHERE "{date_column_in_db}" >= ? AND "{date_column_in_db}" <= ?'
            self.conn.execute(delete_sql, (date_list[0], date_list[-1]))
            logger.info(f"{table_name}: 已统一删除日期范围 {date_list[0]}~{date_list[-1]} 的记录（覆盖模式优化）")
            
            return self.storage.store_data(
                table_name, df_combined, unique_keys,
                date_column=date_column_in_db,
                storage_mode='insert_new',
                api_config_entry=api_config_entry
            )
        return 0

    def _batch_fetch_and_store_multicode(self, table_name, api_table, api_config_entry, unique_keys, date_list, param_grid, ts_code, date_column_in_db):
         logger.info(f"{table_name}: 多 ts_code 日线表 + 覆盖模式，强制执行全量拉取 → 统一删除 → 统一插入")
         all_dfs = []
         request_start, request_end = date_list[0], date_list[-1]
         
         for grid_params in param_grid:
             current_ts_code = grid_params.get('ts_code') or ts_code
             extra_grid = {**grid_params, 'config': api_config_entry}
             api_params_grid = build_api_params(table_name, request_start, request_end,current_ts_code, extra_grid)
             
             df = self.fetcher.fetch_data(api_table, api_params_grid, api_config_entry)
             if df is not None and not df.empty:
                 all_dfs.append(df)
                 
         if all_dfs:
             df_combined = pd.concat(all_dfs, ignore_index=True)
             logger.info(f"{table_name}: 全量拉取完成，共 {len(df_combined)} 条，准备统一覆盖")
             
             delete_sql = f'DELETE FROM "{table_name}" WHERE "{date_column_in_db}" >= ? AND "{date_column_in_db}" <= ?'
             self.conn.execute(delete_sql, (request_start, request_end))
             
             return self.storage.store_data(
                 table_name, df_combined, unique_keys,
                 date_column=date_column_in_db,
                 storage_mode='insert_new',
                 api_config_entry=api_config_entry
             )
         return 0
