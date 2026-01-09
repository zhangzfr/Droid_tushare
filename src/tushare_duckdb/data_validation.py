from pathlib import Path
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .utils import get_connection, table_exists, get_table_schema, show_table_statistics
from .utils import get_all_dates, get_trade_dates, get_quarterly_dates, get_monthly_dates
from .config import API_CONFIG
from .logger import logger


def get_database_status(db_path, basic_db_path=None, tables=None, start_date=None, end_date=None,
                        detailed=False, use_trade_dates=False, exchange='SSE', irregular=False,
                        calendar_db_path=None, calendar_type='stock', field_style='standard',
                        verbose=True, frequency='daily'):
    """
    获取数据库状态，返回 (table_status, daily_data) 元组。
    table_status: 表状态列表
    daily_data: 逐日/逐期数据量详情列表
    frequency: 'daily' (默认) 或 'quarterly'
    
    如果是 frequency='quarterly' (财务数据):
    table_status 将包含: 数据库名称, 表名, 报告期, 记录数, TS_CODE计数
    daily_data 结构会有所不同，以报告期为 key。
    """
    if not tables:
        logger.error("错误：未提供表列表")
        return [], []

    is_range_check = start_date is not None and end_date is not None
    db_name = Path(db_path).name

    table_status = []
    daily_data = []
    try:
        with get_connection(db_path, read_only=True) as conn:
            if not conn:
                return [], []

            # 获取自然日列表
            valid_days = []
            trade_days = set()
            if is_range_check:
                if frequency == 'quarterly':
                     if not start_date or not end_date:
                         # Default to last 8 quarters if no range specified
                         today = datetime.now()
                         check_start = (today - relativedelta(months=24)).strftime('%Y%m%d')
                         check_end = today.strftime('%Y%m%d')
                         all_qs = get_quarterly_dates(check_start, check_end)
                         valid_days = all_qs[-8:] if len(all_qs) > 8 else all_qs
                     else:
                        valid_days = get_quarterly_dates(start_date, end_date)
                
                elif frequency == 'monthly':
                    # 月度数据校验逻辑
                    valid_days = get_monthly_dates(start_date, end_date)
                    if not valid_days: 
                         # fallback if generation failed
                         valid_days = []

                elif detailed and not irregular:
                    valid_days = get_all_dates(start_date, end_date)
                    basic_db_path = basic_db_path or db_path
                    try:
                        trade_days = set(get_trade_dates(basic_db_path, start_date, end_date, exchange))
                    except ValueError as e:
                        logger.warning(f"警告：无法获取交易日 (exchange: {exchange}): {e}")
                        trade_days = set()
                elif use_trade_dates:
                    basic_db_path = basic_db_path or db_path
                    valid_days = get_trade_dates(basic_db_path, start_date, end_date, exchange)
                else:
                    valid_days = get_all_dates(start_date, end_date)

            if detailed and is_range_check and valid_days and not irregular:
                if frequency == 'quarterly':
                     daily_data = [{'报告期': date, '类型': 'Q'} for date in valid_days]
                elif frequency == 'monthly':
                     daily_data = [{'日期': date, '类型': 'M'} for date in valid_days]
                # Re-enable daily data logic for non-quarterly if range check is valid or frequency is quarterly (which implies range check fulfilled by default logic)
            
            # Special handling for quarterly default range enablement
            if frequency == 'quarterly' and daily_data:
                 # Ensure we have data container even if is_range_check was false initially
                 pass
            elif detailed and is_range_check and valid_days and not irregular:
                 daily_data = [{'日期': date, '是否交易日': 'Y' if date in trade_days else 'N'} for date in valid_days]

            expected_keys = ['数据库名称', '表名', '最早日期', '最晚日期', '记录数']
            if not irregular:
                expected_keys += ['覆盖率', '缺失范围', '异常日期']

            # 预先获取交易日列表（如果需要）
            if is_range_check and not trade_days:
                basic_db_path = basic_db_path or db_path
                try:
                    trade_days = set(get_trade_dates(basic_db_path, start_date, end_date, exchange))
                except ValueError as e:
                    logger.warning(f"警告：无法获取交易日 (exchange: {exchange}): {e}")
                    trade_days = set()

            for table_name, date_column in tables:
                # 获取表的 date_type 配置
                table_date_type = 'natural'  # 默认自然日
                for cat_key, cat_val in API_CONFIG.items():
                    tables_conf = cat_val.get('tables', {})
                    if table_name in tables_conf:
                        table_date_type = tables_conf[table_name].get('date_type', 'natural')
                        break
                try:
                    if not table_exists(conn, table_name):
                        logger.warning(f"警告：表 {table_name} 不存在")
                        status = {k: 'N/A' if k in ['最早日期', '最晚日期', '覆盖率', '缺失范围', '异常日期'] else (
                            db_name if k == '数据库名称' else table_name if k == '表名' else 0) for k in expected_keys}
                        table_status.append(status)
                        if daily_data:
                            for i in range(len(valid_days)):
                                daily_data[i][table_name] = 0
                        continue

                    # 获取表列名
                    target_columns = get_table_schema(conn, table_name)
                    if not target_columns:
                        logger.warning(f"警告：表 {table_name} 列信息为空")
                        status = {k: 'N/A' if k in ['最早日期', '最晚日期', '覆盖率', '缺失范围', '异常日期'] else (
                            db_name if k == '数据库名称' else table_name if k == '表名' else 0) for k in expected_keys}
                        table_status.append(status)
                        if daily_data:
                            for i in range(len(valid_days)):
                                daily_data[i][table_name] = 0
                        continue

                    # 验证 date_column 存在 (如果配置了 date_column)
                    if date_column and date_column.lower() not in target_columns:
                        logger.warning(f"警告：表 {table_name} 不包含日期列 {date_column}")
                        irregular = True
                    
                    # 只有当 date_column 为 None 且不属于 irregular 时，我们认为它是快照表
                    is_snapshot = (date_column is None) and not irregular

                    total_records = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
                    earliest_date = 'N/A'
                    latest_date = 'N/A'
                    coverage = 'N/A'
                    missing_ranges = 'N/A'
                    anomaly_dates = 'N/A'

                    if date_column and not irregular:
                        if frequency == 'quarterly':
                             # 财务模式：特殊的统计逻辑，不需要最早/最晚日期等常规指标
                             pass
                        else:
                            query = f"SELECT MIN(\"{date_column}\"), MAX(\"{date_column}\") FROM \"{table_name}\" WHERE \"{date_column}\" IS NOT NULL"
                            result = conn.execute(query).fetchone()
                            earliest_date = str(result[0]) if result and result[0] else 'N/A'
                            latest_date = str(result[1] if result and result[1] else 'N/A')
                            earliest_table_date = earliest_date if earliest_date != 'N/A' else '19900101'
                    elif is_snapshot:
                        # 快照表逻辑
                        coverage = 'SnapShot'
                        missing_ranges = '-'
                        anomaly_dates = '-'
                    else:
                        if date_column: # 只有配置了 date_column 但没找到列才报警告，如果这类本身就是 None 则不报
                             logger.warning(f"表 {table_name} 缺少日期列 {date_column}，标记为 N/A")
                        irregular = True
                    
                    # Finance specific logic
                    if frequency == 'quarterly' and not irregular:
                         # ... (Existing Quarterly Logic) ...
                         # We need a robust way to determine which date column to use for "Report Period" validation
                         # Default to 'end_date' for finance tables if it exists, otherwise use config date_column
                         
                         report_date_col = 'end_date' if 'end_date' in target_columns else date_column
                         
                         # Check columns
                         has_ts_code = 'ts_code' in target_columns
                         
                         query = f"""
                            SELECT "{report_date_col}", COUNT(*), COUNT(DISTINCT {'ts_code' if has_ts_code else '1'})
                            FROM "{table_name}"
                            WHERE "{report_date_col}" IN ({','.join([f"'{d}'" for d in valid_days])})
                            GROUP BY "{report_date_col}"
                            ORDER BY "{report_date_col}" DESC
                         """
                         try:
                             rows = conn.execute(query).fetchall()
                             # rows: [(date, count, distinct_ts_code_count), ...]
                             # 将结果填入 daily_data
                             row_map = {str(r[0]): {'count': r[1], 'distinct': r[2]} for r in rows}
                             
                             if daily_data:
                                 for i in range(len(valid_days)):
                                     d = valid_days[i]
                                     if d in row_map:
                                         daily_data[i][table_name] = f"{row_map[d]['distinct']}家/{row_map[d]['count']}条"
                                     else:
                                         daily_data[i][table_name] = "0/0"
                             
                             # 获取最早/最晚报告期
                             min_max_query = f"SELECT MIN(\"{report_date_col}\"), MAX(\"{report_date_col}\") FROM \"{table_name}\""
                             min_max_res = conn.execute(min_max_query).fetchone()
                             earliest_report = str(min_max_res[0]) if min_max_res and min_max_res[0] else 'N/A'
                             latest_report = str(min_max_res[1]) if min_max_res and min_max_res[1] else 'N/A'

                             # 更新 table_status
                             status = {
                                '数据库名称': db_name,
                                '表名': table_name,
                                '最早报告期': earliest_report,
                                '最晚报告期': latest_report,
                                '记录数': total_records
                             }
                             table_status.append(status)
                             continue # Skip standard logic
                             
                         except Exception as e:
                             logger.error(f"财务统计查询失败: {e}")
                             irregular = True # Fallback

                    # Monthly Macro Data Logic
                    if frequency == 'monthly' and not irregular:
                        # 宏观数据如 cn_pmi，date_column 往往是 'month' (YYYYMM)
                        # 但也有可能是 'trade_date' (YYYYMMDD) 如 shibor
                        # 我们需要根据 date_column 的值长度来匹配 valid_days (YYYYMM)
                        
                        # 检测 DB 中该列的格式样本 (取第一条非空)
                        try:
                            sample_q = f"SELECT CAST(\"{date_column}\" AS VARCHAR) FROM \"{table_name}\" WHERE \"{date_column}\" IS NOT NULL LIMIT 1"
                            sample_res = conn.execute(sample_q).fetchone()
                            sample_val = str(sample_res[0]) if sample_res else ''
                            
                            is_yyyymm = len(sample_val) == 6
                            is_yyyymmdd = len(sample_val) == 8
                            
                            # 构建查询
                            # 如果 DB 是 YYYYMM，直接匹配 valid_days
                            # 如果 DB 是 YYYYMMDD，匹配 valid_days (YYYYMM) 为前缀，或匹配该月内任意一天
                            
                            if is_yyyymm:
                                query = f"""
                                    SELECT "{date_column}", COUNT(*)
                                    FROM "{table_name}"
                                    WHERE "{date_column}" IN ({','.join([f"'{d}'" for d in valid_days])})
                                    GROUP BY "{date_column}"
                                """
                                rows = conn.execute(query).fetchall()
                                count_dict = {str(r[0]): r[1] for r in rows}
                            
                            elif is_yyyymmdd:
                                # 对于 shibor 这种日频数据，但在 monthly 模式下展示
                                # 我们统计每个月的数据条数
                                query_parts = []
                                for ym in valid_days:
                                    # valid_days are YYYYMM
                                    start_m = ym + '01'
                                    # calculate end of month
                                    # simple logic: look for date LIKE 'YYYYMM%'
                                    # DuckDB supports LIKE
                                    # But aggregate might be slow via looping?
                                    # Better: extract YYYYMM from date_column
                                    pass
                                
                                # Optimized query: Group by substr(date, 1, 6)
                                query = f"""
                                    SELECT substr(CAST("{date_column}" AS VARCHAR), 1, 6) as ym, COUNT(*)
                                    FROM "{table_name}"
                                    WHERE substr(CAST("{date_column}" AS VARCHAR), 1, 6) IN ({','.join([f"'{d}'" for d in valid_days])})
                                    GROUP BY ym
                                """
                                rows = conn.execute(query).fetchall()
                                count_dict = {str(r[0]): r[1] for r in rows}
                                
                            else:
                                count_dict = {}

                            # 填充 daily_data
                            if daily_data:
                                for i in range(len(valid_days)):
                                    d = valid_days[i]
                                    daily_data[i][table_name] = count_dict.get(d, 0)

                            # 计算覆盖率
                            existing = [d for d in valid_days if count_dict.get(d, 0) > 0]
                            coverage = f"{len(existing)}/{len(valid_days)}"
                            
                            status = {
                                '数据库名称': db_name,
                                '表名': table_name,
                                '最早日期': earliest_date,
                                '最晚日期': latest_date,
                                '记录数': total_records,
                                '覆盖率': coverage,
                                '缺失范围': '见详情',
                                '异常日期': 'N/A'
                            }
                            table_status.append(status)
                            continue # Skip standard logic

                        except Exception as e:
                            logger.error(f"月度统计查询失败 ({table_name}): {e}")
                            irregular = True # Fallback

                    if frequency == 'quarterly' and not irregular:
                         # We need a robust way to determine which date column to use for "Report Period" validation
                         # Default to 'end_date' for finance tables if it exists, otherwise use config date_column
                         
                         report_date_col = 'end_date' if 'end_date' in target_columns else date_column
                         
                         # Check columns
                         has_ts_code = 'ts_code' in target_columns
                         
                         query = f"""
                            SELECT "{report_date_col}", COUNT(*), COUNT(DISTINCT {'ts_code' if has_ts_code else '1'})
                            FROM "{table_name}"
                            WHERE "{report_date_col}" IN ({','.join([f"'{d}'" for d in valid_days])})
                            GROUP BY "{report_date_col}"
                            ORDER BY "{report_date_col}" DESC
                         """
                         try:
                             rows = conn.execute(query).fetchall()
                             # rows: [(date, count, distinct_ts_code_count), ...]
                             # 将结果填入 daily_data
                             row_map = {str(r[0]): {'count': r[1], 'distinct': r[2]} for r in rows}
                             
                             if daily_data:
                                 for i in range(len(valid_days)):
                                     d = valid_days[i]
                                     if d in row_map:
                                         daily_data[i][table_name] = f"{row_map[d]['distinct']}家/{row_map[d]['count']}条"
                                     else:
                                         daily_data[i][table_name] = "0/0"
                             
                             # 获取最早/最晚报告期
                             min_max_query = f"SELECT MIN(\"{report_date_col}\"), MAX(\"{report_date_col}\") FROM \"{table_name}\""
                             min_max_res = conn.execute(min_max_query).fetchone()
                             earliest_report = str(min_max_res[0]) if min_max_res and min_max_res[0] else 'N/A'
                             latest_report = str(min_max_res[1]) if min_max_res and min_max_res[1] else 'N/A'

                             # 更新 table_status
                             status = {
                                '数据库名称': db_name,
                                '表名': table_name,
                                '最早报告期': earliest_report,
                                '最晚报告期': latest_report,
                                '记录数': total_records
                             }
                             table_status.append(status)
                             continue # Skip standard logic
                             
                         except Exception as e:
                             logger.error(f"财务统计查询失败: {e}")
                             irregular = True # Fallback

                    earliest_table_date = earliest_date if earliest_date != 'N/A' else '19900101'
                    effective_start_date = max(start_date,
                                               earliest_table_date) if is_range_check and earliest_table_date != 'N/A' else start_date
                    effective_valid_days = [d for d in valid_days if
                                            d >= effective_start_date] if is_range_check else valid_days

                    if not irregular and date_column and is_range_check and effective_valid_days:
                        # 动态检查表是否含有 ts_code 字段
                        has_ts_code = 'ts_code' in target_columns
                        if table_name in ['yc_cb', 'daily', 'adj_factor', 'daily_basic', 'fut_daily', 'fut_index_daily',
                                          'index_daily', 'opt_daily', 'cb_daily', 'fund_daily']:
                            count_expr = "COUNT(*)"  # 日线行情：统计总记录数
                        else:
                            count_expr = "COUNT(DISTINCT ts_code)" if has_ts_code else "COUNT(*)"
                        query = f"""
                            SELECT \"{date_column}\", {count_expr} AS count
                            FROM \"{table_name}\" 
                            WHERE \"{date_column}\" BETWEEN '{effective_start_date}' AND '{end_date}' 
                            GROUP BY \"{date_column}\" 
                            ORDER BY \"{date_column}\"
                        """
                        try:
                            daily_counts = conn.execute(query).fetchall()
                            count_dict = {str(d[0]): d[1] for d in daily_counts if d[0]}
                        except Exception as e:
                            logger.error(f"错误：表 {table_name} 数据量查询失败: {e}")
                            count_dict = {}

                        existing_dates = set(count_dict.keys())
                        
                        # 根据 date_type 选择正确的日期列表来计算缺失
                        if table_date_type == 'trade':
                            # 交易日类型：使用交易日列表
                            expected_dates = [d for d in effective_valid_days if d in trade_days]
                            missing_dates = sorted([d for d in expected_dates if d not in existing_dates])
                            date_unit = '个交易日'
                        else:
                            # 自然日类型：使用全部自然日
                            missing_dates = sorted([d for d in effective_valid_days if d not in existing_dates])
                            expected_dates = effective_valid_days
                            date_unit = '天'
                        
                        coverage = f"{(len(expected_dates) - len(missing_dates)) / len(expected_dates) * 100:.1f}%" if expected_dates else 'N/A'
                        missing_ranges = f"{missing_dates[0]}{'...' + missing_dates[-1] if len(missing_dates) > 1 else ''} ({len(missing_dates)}{date_unit})" if missing_dates else '无缺失'

                        counts = [c[1] for c in daily_counts] if daily_counts else []
                        if counts:
                            mean_count = np.mean(counts)
                            std_count = np.std(counts) if len(counts) > 1 else 0
                            threshold = max(mean_count - 2 * std_count, 1)
                            anomaly_dates_list = [str(d[0]) for d in daily_counts if d[1] < threshold]
                            anomaly_dates = '; '.join(anomaly_dates_list) if anomaly_dates_list else '无异常日期'
                        else:
                            anomaly_dates = '无数据'

                        if daily_data:
                            for i, date in enumerate(valid_days):
                                daily_data[i][table_name] = count_dict.get(date,
                                                                           0) if date >= effective_start_date else 0

                    elif is_snapshot and daily_data:
                         # 快照数据逐日详情填充 '-'
                         for i in range(len(valid_days)):
                             daily_data[i][table_name] = '-'

                    status = {
                        '数据库名称': db_name,
                        '表名': table_name,
                        '最早日期': earliest_date,
                        '最晚日期': latest_date,
                        '记录数': total_records
                    }
                    if not irregular or is_snapshot:
                        status.update({
                            '覆盖率': coverage,
                            '缺失范围': missing_ranges,
                            '异常日期': anomaly_dates
                        })
                    table_status.append(status)

                    # === 新增：如果有业务统计查询，则显示 (Added for enhanced validation) ===
                    # 我们需要反查这个 table 属于哪个 category 才能找到 API_CONFIG
                    # 也可以简单遍历所有 API_CONFIG 找到它
                    # 这里做一个简单的查找逻辑
                    for cat_key, cat_val in API_CONFIG.items():
                        tables_conf = cat_val.get('tables', {})
                        if table_name in tables_conf and 'statistics_queries' in tables_conf[table_name]:
                            # 为了不打断 validation 的主流程表格输出，我们把 stats 收集起来或者直接打印
                            # 但 validation 函数返回的是 status 列表，打印最好在主流程外？
                            # 或者直接在这里打印，但由于 validation 可能被 UI 调用...
                            # 暂且直接打印到控制台，Validation Tool 也是 CLI 工具。
                            if verbose:
                                show_table_statistics(db_path, table_name, tables_conf[table_name]['statistics_queries'])
                            break

                except Exception as e:
                    logger.error(f"错误：校验表 {table_name} 失败: {e}")
                    status = {k: 'N/A' if k in ['最早日期', '最晚日期', '覆盖率', '缺失范围', '异常日期'] else (
                        db_name if k == '数据库名称' else table_name if k == '表名' else 0) for k in expected_keys}
                    table_status.append(status)
                    if daily_data:
                        for i in range(len(valid_days)):
                            daily_data[i][table_name] = 0

            if field_style == 'opt' and not irregular:
                key_map = {
                    '数据库名称': '数据库名称',
                    '表名': '表名',
                    '覆盖率': '覆盖率',
                    '缺失范围': '建议补充范围',
                    '异常日期': '非交易日日期'
                }
                for status in table_status:
                    status.update({key_map.get(k, k): v for k, v in status.items()})

            return table_status, daily_data

    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "Cannot open database" in error_msg:
             logger.warning(f"数据库 {db_name} 尚未创建 (需要执行数据获取操作)")
             # 返回一个虚拟的空状态，让表格显示 "DB 未创建"
             empty_status = []
             for table_name, _ in tables:
                 status = {
                     '数据库名称': db_name,
                     '表名': table_name,
                     '记录数': 0,
                     '最早日期': 'N/A',
                     '最晚日期': 'N/A',
                     '覆盖率': 'DB未创建',
                     '缺失范围': '未创建',
                     '异常日期': '未创建'
                 }
                 empty_status.append(status)
             return empty_status, []
        logger.error(f"错误：获取数据库状态失败: {e}")
        return table_status, daily_data
