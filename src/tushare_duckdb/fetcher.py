import pandas as pd
import time
from .config import PRO_API
from .logger import logger

class TushareFetcher:
    def __init__(self, api=None):
        self.api = api or PRO_API

    def fetch_data(self, table_name, api_params, api_config_entry, retries=3, initial_offset=0):
        expected_fields = api_config_entry.get('fields', [])
        requires_paging = api_config_entry.get('requires_paging', False)
        api_limit = api_config_entry.get('limit', 2000)
        unique_keys = api_config_entry.get('unique_keys', [])
        all_data_list = []
        current_offset = initial_offset
        total_fetched_raw = 0
        page_count = 0
        logger.info(f"开始获取 '{table_name}': 分页={requires_paging}, API参数={api_params}, 唯一键={unique_keys}")

        while True:
            page_count += 1
            current_api_call_params = api_params.copy()
            current_api_call_params['limit'] = api_limit
            current_api_call_params['offset'] = current_offset
            df_page = None
            page_rows = 0
            for attempt in range(retries):
                logger.info(
                    f"页 {page_count}, 尝试 {attempt + 1}/{retries}: 调用 API '{table_name}', 参数: {current_api_call_params}")
                try:
                    df_page = self.api.query(table_name, fields=expected_fields, **current_api_call_params)
                    page_rows = len(df_page) if df_page is not None else 0
                    total_fetched_raw += page_rows
                    logger.info(f"  API返回 {page_rows} 行. 总计: {total_fetched_raw} 行.")
                    if page_rows == 0:
                        logger.info(f"{table_name}: 分页结束")
                        break
                    df_page.dropna(how='all', inplace=True)
                    if not df_page.empty:
                        all_data_list.append(df_page)
                    current_offset += page_rows
                    break
                except Exception as e:
                    if "每_minute最多访问" in str(e):
                        logger.warning(f"检测到频率限制，等待 65 秒后重试...")
                        time.sleep(65)
                    elif attempt < retries - 1:
                        time.sleep(1.0 * (2 ** attempt))
                    else:
                        logger.error(f"  '{table_name}' 获取失败（ts_code={current_api_call_params.get('ts_code', '无')}）: {e}")
                        return pd.DataFrame()  # 关键：失败直接返回空，不卡死
            if page_rows < api_limit:
                break

        if all_data_list:
            df_combined = pd.concat(all_data_list, ignore_index=True)
            logger.info(f"{table_name}: 合并前总行数: {len(df_combined)}")
            df_combined = df_combined.drop_duplicates(subset=unique_keys, keep='last')
            logger.info(f"{table_name} 合并完成。总行数 (去重后): {len(df_combined)}")
            return df_combined
        return pd.DataFrame()
