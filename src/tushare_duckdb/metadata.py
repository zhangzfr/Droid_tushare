# 文件：/Users/robert/Developer/Quant/tushare/tushare_2_duckdb/Droid_tushare/ts_duckdb_metadata.py
from datetime import datetime
from .utils import table_exists, get_columns


def init_metadata(conn, db_type):
    """初始化 metadata 表 (如果不存在)"""
    if not table_exists(conn, 'metadata'):
        try:
            conn.execute('''
                CREATE TABLE metadata (
                    table_name VARCHAR PRIMARY KEY,
                    min_date VARCHAR,
                    max_date VARCHAR,
                    record_count BIGINT, -- Use BIGINT for potentially large counts
                    last_updated TIMESTAMP -- Use TIMESTAMP for better precision
                );
            ''')  # Added semicolon for clarity
            print(f"创建 {db_type} 数据库的 metadata 表")
        except Exception as e:
            print(f"错误: 创建 metadata 表失败: {e}")
            # It's critical that metadata table exists, so re-raise
            raise


def update_metadata(conn, table_name, date_column=None, filter_null_dates=False):
    """更新 metadata 表"""
    # Ensure the metadata table itself exists before trying to update it
    if not table_exists(conn, 'metadata'):
        print("错误: Metadata 表不存在，无法更新元数据。请先初始化。")
        return  # Exit the function if metadata table is missing

    # Proceed only if the target table exists
    if not table_exists(conn, table_name):
        print(f"警告: 目标表 '{table_name}' 不存在，无法更新其元数据。")
        return  # Exit if target table doesn't exist

    last_updated = datetime.now()  # Store as datetime object
    min_date_str, max_date_str, count = None, None, 0  # Initialize defaults

    try:
        if date_column:
            # Check if date_column actually exists in the target table
            table_columns, _, _ = get_columns(conn, table_name)
            if date_column and date_column not in table_columns:
                print(f"警告：日期列 '{date_column}' 在表 '{table_name}' 中不存在，只更新记录数。")

            if date_column not in table_columns:
                print(f"日期列 '{date_column}' 在表 '{table_name}' 中不存在，只更新记录数。")
                # Get only count if date column missing
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                count = count_result[0] if count_result else 0
            else:
                # Date column exists, proceed with query
                date_filter_clause = f"WHERE \"{date_column}\" IS NOT NULL" if filter_null_dates else ""
                # Use prepared statement placeholders and quote column names
                query = f'SELECT MIN("{date_column}"), MAX("{date_column}"), COUNT(*) FROM "{table_name}" {date_filter_clause}'
                result = conn.execute(query).fetchone()
                # Handle potential None result if table is empty after filtering
                if result:
                    min_date, max_date, count_val = result
                    # Convert dates to string safely
                    min_date_str = str(min_date) if min_date is not None else None
                    max_date_str = str(max_date) if max_date is not None else None
                    count = count_val if count_val is not None else 0
                else:
                    # If query returned None (e.g., empty table or only NULL dates when filtering)
                    min_date_str, max_date_str, count = None, None, 0

        else:  # No date column specified
            count_result = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()
            count = count_result[0] if count_result else 0

        # Use prepared statements for INSERT/UPDATE
        conn.execute('''
            INSERT INTO metadata (table_name, min_date, max_date, record_count, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(table_name) DO UPDATE SET
                min_date = excluded.min_date,
                max_date = excluded.max_date,
                record_count = excluded.record_count,
                last_updated = excluded.last_updated;
        ''', (table_name, min_date_str, max_date_str, count, last_updated))  # Use variables directly

        print(
            f"已更新表 '{table_name}' 的元数据: min={min_date_str or 'N/A'}, max={max_date_str or 'N/A'}, count={count}")

    except Exception as e:
        print(f"错误: 更新表 '{table_name}' 的元数据失败: {e}")
