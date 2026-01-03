from .schema import TABLE_SCHEMAS
from datetime import datetime, timedelta
import duckdb
import re  # 文件顶部添加
try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

from contextlib import contextmanager
from itertools import product
import calendar
from dateutil.relativedelta import relativedelta


# === 连接管理 ===
@contextmanager
def get_connection(db_path, read_only=False):
    conn = None
    try:
        conn = duckdb.connect(db_path, read_only=read_only)
        print(f"数据库连接成功: {db_path} {'(只读)' if read_only else ''}")
        yield conn
    except Exception as e:
        print(f"错误：连接数据库 {db_path} 失败: {e}")
        # 关键修复：异常时直接 re-raise，不 yield None！
        raise  # 让 with 块外层捕获，不继续执行 finally 中的问题代码
    finally:
        if conn:
            try:
                conn.close()
                print(f"数据库连接已关闭: {db_path}")
            except Exception as close_err:
                print(f"警告：关闭数据库连接时出错: {close_err}")


# === 日期工具函数 ===
def get_all_dates(start_date, end_date):
    try:
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        date_list = []
        current_dt = start_dt
        while current_dt <= end_dt:
            date_list.append(current_dt.strftime('%Y%m%d'))
            current_dt += timedelta(days=1)
        return date_list
    except ValueError as e:
        print(f"错误：日期格式错误: {start_date} 或 {end_date}, {e}")
        return []


def get_trade_dates(db_path, start_date, end_date, exchange='SSE', conn=None):
    if conn:
        return _query_trade_dates(conn, start_date, end_date, exchange)
    
    with get_connection(db_path, read_only=True) as conn:
        return _query_trade_dates(conn, start_date, end_date, exchange)

def _query_trade_dates(conn, start_date, end_date, exchange):
    if not table_exists(conn, 'trade_cal'):
        return []
    query = "SELECT cal_date FROM trade_cal WHERE cal_date >= ? AND cal_date <= ? AND exchange = ? AND is_open = 1 ORDER BY cal_date"
    trade_dates = conn.execute(query, (start_date, end_date, exchange)).fetchall()
    return [d[0] for d in trade_dates]


def get_quarterly_dates(start_date, end_date):
    """
    生成标准财务季度末日期列表 (0331, 0630, 0930, 1231)
    返回格式: ['20230331', '20230630', ...]
    """
    quarters = []
    try:
        current = datetime.strptime(str(start_date), '%Y%m%d')
        end_dt = datetime.strptime(str(end_date), '%Y%m%d')
    except ValueError as e:
        print(f"错误：日期格式无效 ({start_date}, {end_date}): {e}")
        return []

    while current <= end_dt:
        month = current.month
        # 确定下一个季度末月份
        if month <= 3:
            q_month = 3
        elif month <= 6:
            q_month = 6
        elif month <= 9:
            q_month = 9
        else:
            q_month = 12
            # 如果当前已是12月之后（实际上逻辑是 10,11,12 -> 12，但如果是 12月31日，loop update logic handles valid check）
            # 特殊情况：如果输入是 1231， current=1231 -> q_month=12.
            # 下面 logic 会生成 当年1231.
            # loop step: current = q_end + 1 day = Next Jan 1.

        q_year = current.year
        # Handle year rollover if December processing logic was tricky in loop, 
        # but here simple mapping 1..3->3, ... 10..12->12 works for "current or next quarter end".
        # Wait, if I am at Jan 1st 2023. q_month=3. q_end=20230331. Valid.
        # If I am at Dec 31st 2023. q_month=12. q_end=20231231. Valid.
        # If I am at Nov 15. q_month=12. q_end=20231231.

        # What if start_date is 20230401 (April 1st)?
        # q_month -> 6. q_end -> 20230630.
        
        _, last_day = calendar.monthrange(q_year, q_month)
        q_end_dt = datetime(q_year, q_month, last_day)

        # Check if calculated quarter end is within range [current, end_dt]?
        # No, within [start_dt, end_dt]. My loop 'current' advances.
        # The logic in interactive_finance_update.py:
        # if q_end_dt >= current and q_end_dt <= end_dt:
        # This ensures we don't add 20230331 if start_date was 20230401.

        if q_end_dt >= current and q_end_dt <= end_dt:
             quarters.append(q_end_dt.strftime('%Y%m%d'))
        
        # Advance to start of next quarter relative to the calculated quarter end
        current = q_end_dt + relativedelta(days=1)
        
    return quarters


def generate_param_grid(required_params):
    if not required_params:
        return [{}]
    keys = list(required_params.keys())
    values = [v if isinstance(v, list) else [v] for v in required_params.values()]
    return [dict(zip(keys, combo)) for combo in product(*values)]

def build_api_params(table_name, start_date, end_date, ts_code, extra_params):
    """
    终极版本：完全尊重 required_params 矩阵
    不再假设任何参数名，直接传 extra_params
    """
    print(f"DEBUG: build_api_params called, table_name={table_name}")
    params = {}

    # === 关键：直接使用 extra_params（包含 grid_params）===
    # 例如 {'ts_codes': 'NHAI.NH'} 会直接传给 API
    params.update(extra_params)

    # === 日期参数逻辑（基于 date_param_mode）===
    config = extra_params.get('config', {})
    
    # === 日期格式适配 (YYYY-MM-DD vs YYYYMMDD) ===
    # Tushare 一般使用 YYYYMMDD，但部分接口（如 cb_share）可能要求 YYYY-MM-DD
    # 我们统一在内部使用 YYYYMMDD，仅在请求参数构建时进行转换
    target_format = config.get('api_date_format')
    
    def format_date(d_str):
        if not target_format or not d_str: return d_str
        try:
            if target_format == 'YYYY-MM-DD' and '-' not in d_str and len(d_str) == 8:
                return f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:]}"
            return d_str
        except:
            return d_str

    if config.get('requires_date') is False:
        pass
    else:
        mode = config.get('date_param_mode', 'single')
        single_param = config.get('date_param') or config.get('param_name')

        if mode == 'range':
            params['start_date'] = format_date(start_date)
            params['end_date'] = format_date(end_date)
        else:
            key = single_param or 'trade_date'
            # 范围查询时，取 end_date（最常见需求）
            raw_date = end_date if start_date != end_date else start_date
            params[key] = format_date(raw_date)

    # === 特殊处理：fut_index_daily 需要 ts_code 参数名 ===
    if table_name in ['fut_index_daily', 'index_daily', 'index_dailybasic']:
        if 'ts_codes' in params:
            params['ts_code'] = params.pop('ts_codes')

    # === 兼容旧 ts_code 参数 ===
    if ts_code and 'ts_code' not in params:
        params['ts_code'] = ts_code

    # 清理临时字段
    params.pop('config', None)

    print(f"DEBUG: build_api_params → {params}")
    return params



# === 其余函数保持不变 ===
def get_existing_dates(conn, table_name, date_column, date_list):
    if not date_list:
        return set()
    placeholders = ','.join(['?'] * len(date_list))
    query = f"SELECT DISTINCT \"{date_column}\" FROM \"{table_name}\" WHERE \"{date_column}\" IN ({placeholders})"
    results = conn.execute(query, date_list).fetchall()
    return set(r[0] for r in results if r[0])


def init_table(conn, table_name):
    """通用表初始化：仅执行配置的 SQL + 创建索引"""
    if table_name not in TABLE_SCHEMAS:
        print(f"错误：表 {table_name} 的结构未定义在 TABLE_SCHEMAS 中")
        return False

    sql = TABLE_SCHEMAS[table_name].strip()

    try:
        # 1. 创建表
        conn.execute(sql)
        print(f"创建表 {table_name}")

        # 2. 自动创建索引（增强版：支持复合主键）
        sql_upper = sql.upper()
        if 'PRIMARY KEY' in sql_upper:
            # 提取 PRIMARY KEY (...) 部分
            pk_start = sql_upper.find('PRIMARY KEY (')
            if pk_start == -1:
                # 尝试单主键：PRIMARY KEY ts_code
                pk_match = re.search(r'PRIMARY KEY\s+\(?([^\s,\)]+)', sql_upper)
                if pk_match:
                    pk_cols = pk_match.group(1).strip()
                else:
                    pk_cols = None
            else:
                pk_start += len('PRIMARY KEY (')
                pk_end = sql_upper.find(')', pk_start)
                if pk_end == -1:
                    pk_end = len(sql_upper)
                pk_cols_str = sql[pk_start:pk_end]
                pk_cols = pk_cols_str.replace(' ', '')

            if pk_cols:
                idx_name = f"idx_{table_name}_pk"
                conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {idx_name} ON "{table_name}" ({pk_cols})')
                print(f"  创建唯一索引 {idx_name}")

        return True

    except Exception as e:
        print(f"错误：初始化表 {table_name} 失败: {e}")
        return False


def table_exists(conn, table_name):
    try:
        result = conn.execute(
            f"SELECT 1 FROM information_schema.tables WHERE table_schema = 'main' AND table_name = '{table_name}' LIMIT 1").fetchone()
        return result is not None
    except Exception as e:
        print(f"错误：检查表 {table_name} 是否存在失败: {e}")
        return False


def get_columns(conn, table_name):
    try:
        result = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        if not result:
            return [], [], {}
        columns = [col[1] for col in result]
        columns_lower = [c.lower() for c in columns]
        column_info = {col[1]: {'type': col[2], 'notnull': bool(col[3]), 'pk': bool(col[5])} for col in result}
        return columns, columns_lower, column_info
    except Exception as e:
        print(f"错误：获取表 {table_name} 列信息失败: {e}")
        return [], [], {}


def init_tables_for_category(conn, category_tables):
    for table_name in category_tables:
        if not table_exists(conn, table_name):
            init_table(conn, table_name)
        else:
            print(f"表 {table_name} 已存在，跳过创建")


def get_table_schema(conn, table_name):
    """获取表的小写列名列表（兼容旧接口）"""
    _, columns_lower, _ = get_columns(conn, table_name)
    _, columns_lower, _ = get_columns(conn, table_name)
    return columns_lower

def show_table_statistics(db_path, table_name, queries):
    """显示指定表的业务逻辑分析报告"""
    print(f"\n>>>> [{table_name}] 业务逻辑分析报告 <<<<")
    try:
        with get_connection(db_path, read_only=True) as conn:
            for q_cfg in queries:
                label = q_cfg.get('label', '统计项')
                sql = q_cfg.get('query')
                mapping = q_cfg.get('map', {})
                
                try:
                    df = conn.execute(sql).fetch_df()
                    if not df.empty:
                        # 尝试处理映射（如 L/D/P 映射为中文）
                        if mapping:
                            first_col = df.columns[0]
                            # DuckDB 可能会把某些列名转为大写或保持原样，通常 df.columns[0] 就是目标
                            df[first_col] = df[first_col].apply(lambda x: f"{x}({mapping.get(x, x)})" if x in mapping else x)
                        
                        print(f"\n* {label}:")
                        if tabulate:
                            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
                        else:
                            print(df.to_string(index=False))
                    else:
                        print(f"\n* {label}: (无数据)")
                except Exception as sql_err:
                    print(f"警告: 执行统计查询 [{label}] 失败: {sql_err}")
    except Exception as e:
        print(f"警告: 生成统计报告任务失败: {e}")
    print("-" * 50)
