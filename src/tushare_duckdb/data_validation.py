from pathlib import Path
import numpy as np
from .utils import get_connection, table_exists, get_table_schema, show_table_statistics
from .utils import get_all_dates, get_trade_dates, get_quarterly_dates
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
                if detailed and not irregular:
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
                elif frequency == 'quarterly':
                    valid_days = get_quarterly_dates(start_date, end_date)
                else:
                    valid_days = get_all_dates(start_date, end_date)

            if detailed and is_range_check and valid_days and not irregular:
                if frequency == 'quarterly':
                     daily_data = [{'日期': date, '类型': 'Q'} for date in valid_days]
                else:
                     daily_data = [{'日期': date, '是否交易日': 'Y' if date in trade_days else 'N'} for date in valid_days]

            expected_keys = ['数据库名称', '表名', '最早日期', '最晚日期', '记录数']
            if not irregular:
                expected_keys += ['覆盖率', '缺失范围', '异常日期']

            for table_name, date_column in tables:
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

                    # 验证 date_column 存在
                    if date_column.lower() not in target_columns:
                        logger.warning(f"警告：表 {table_name} 不包含日期列 {date_column}")
                        irregular = True

                    total_records = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
                    earliest_date = 'N/A'
                    latest_date = 'N/A'
                    coverage = 'N/A'
                    missing_ranges = 'N/A'
                    anomaly_dates = 'N/A'

                    if date_column and not irregular:
                        query = f"SELECT MIN(\"{date_column}\"), MAX(\"{date_column}\") FROM \"{table_name}\" WHERE \"{date_column}\" IS NOT NULL"
                        result = conn.execute(query).fetchone()
                        earliest_date = str(result[0]) if result and result[0] else 'N/A'
                        latest_date = str(result[1] if result and result[1] else 'N/A')
                        earliest_table_date = earliest_date if earliest_date != 'N/A' else '19900101'
                    else:
                        logger.warning(f"表 {table_name} 缺少日期列 {date_column}，标记为 N/A")
                        irregular = True

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
                        missing_dates = sorted([d for d in effective_valid_days if d not in existing_dates])
                        coverage = f"{(len(effective_valid_days) - len(missing_dates)) / len(effective_valid_days) * 100:.1f}%" if effective_valid_days else 'N/A'
                        missing_ranges = f"{missing_dates[0]}{'...' + missing_dates[-1] if len(missing_dates) > 1 else ''} ({len(missing_dates)}天)" if missing_dates else '无缺失'

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

                    status = {
                        '数据库名称': db_name,
                        '表名': table_name,
                        '最早日期': earliest_date,
                        '最晚日期': latest_date,
                        '记录数': total_records
                    }
                    if not irregular:
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
        logger.error(f"错误：获取数据库状态失败: {e}")
        return table_status, daily_data
